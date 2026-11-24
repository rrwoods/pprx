# Runbook: Staging Topology, Branch Promotion, and DB Refresh

Operational reference for PPR X's DigitalOcean App Platform staging environment (`pprx-staging`), `main` → `prod` promotion, and prod-to-staging database refresh.

## 1. Environment Topology

| Aspect | Production (`pprx-prod`) | Staging (`pprx-staging`) |
| :--- | :--- | :--- |
| **Git branch** | `prod` (`deploy_on_push: true`) | `main` (`deploy_on_push: true`) |
| **Public URL** | `https://pprx.gg` (`pprx-prod-pe9zb.ondigitalocean.app`) | `https://pprx-staging-2xs7w.ondigitalocean.app` |
| **MySQL database** | `ebdb` on `pprx-prod` cluster | `pprx_staging` on shared `pprx-prod` cluster |
| **MySQL app user** | `doadmin` / prod DB credentials | `pprx_staging` (`ALL PRIVILEGES ON pprx_staging.*` only) |
| **Email backend** | `django.core.mail.backends.smtp.EmailBackend` | `django.core.mail.backends.console.EmailBackend` |
| **3icecream webhook** | Enabled (`DEFAULT_WEBHOOK_ID`) | Disabled (`WEBHOOK_ID` unset / `""`) |
| **OAuth redirect override** | Unset (`None`) | `SANBAI_OAUTH_REDIRECT_URI=https://pprx.gg/scorebrowser/scores` |
| **UI indicator** | `.update-message` banner | `IS_STAGING=True` yellow-green `STAGING ENVIRONMENT` banner |

Both apps run on DigitalOcean App Platform (`sfo` / VPC `default-sfo3`, `source_dir: pprxweb`, `apps-s-1vcpu-0.5gb`, default Python buildpack, `gunicorn --workers=1 --worker-tmp-dir /dev/shm pprxweb.wsgi`) and share the `pprx-prod` Managed MySQL `8.0.45` cluster (`1 vCPU / 1 GB RAM`, `utf8mb4` / `utf8mb4_0900_ai_ci`, `STRICT_ALL_TABLES`, Trusted Sources enabled).

### Staging Guards

`pprxweb/pprxweb/settings.py` (`load_runtime_settings`) parameterizes `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DEBUG`, `EMAIL_BACKEND`, `WEBHOOK_ID`, `SANBAI_OAUTH_REDIRECT_URI`, optional `DB_CA_CERT`, and `IS_STAGING` (with production-compatible defaults), and enables `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`. On `pprx-staging`:

- **`IS_STAGING=True`**: `scorebrowser.context_processors.staging_context` injects staging metadata so `base.html` replaces the update notice with the `STAGING ENVIRONMENT` banner.
- **Webhook registration gated**: `WEBHOOK_ID` is unset (`""`), so `register_webhook()` is skipped in both `finish_link` and `scores`.
- **Empty-score `Fetch` gated**: In `scores`, initial `Fetch` for a `User` with zero `Current Scores` runs only when `scores_user.access_token` is non-empty, preventing errors when viewing scrubbed `Users`.
- **Non-SMTP mail**: `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` logs account activation and password-reset emails to `pprx-staging` **Runtime Logs** instead of sending SMTP mail.
- **Schema-only `chart_pairs`**: `chart_pairs` is cloned without rows (`0` rows in `pprx_staging`), keeping dump/restore size bounded while preserving schema compatibility.

---

## 2. Branch Promotion (`main` → `prod`) & CI

- **Feature PRs target `main`**: Merging a PR to `main` automatically deploys to `pprx-staging`.
- **CI triggers**: `.github/workflows/ci.yml` runs on both `push` and `pull_request` for `["main", "prod"]`, checking `makemigrations --check --dry-run`, `python manage.py test`, and `python manage.py test` with an unreachable `DATABASE_URL`.
- **Branch protection**: `main` uses classic branch protection (`enforce_admins: false`, 1 approving review + code owner review). `prod` blocks PR UI merges via `.github/workflows/forbid-prod-ui-merge.yml` (`forbid-ui-merge`) and a `prod` Ruleset whose bypass list grants fast-forward push access to the `Promote to prod` GitHub App.
- **Promote `main` to `prod`**: Run **Actions → Promote to prod** (`.github/workflows/promote-to-prod.yml`) after `Django CI` passes and changes are verified on `pprx-staging`. See [Promote `main` to `prod` Runbook](promote-to-prod.md) for the full checklist and troubleshooting steps.

---

## 3. Prod-to-Staging DB Refresh Runbook

`scripts/clone_prod_to_staging.ps1` clones `ebdb` into `pprx_staging` from a local workstation and sanitizes `User` data via `scripts/sanitize_staging.sql`.

### Shared-Cluster Isolation & Least-Privilege Roles

Because `pprx_staging` shares the live `pprx-prod` Managed MySQL cluster with `ebdb`, two least-privilege roles prevent accidental writes or locks against production:

- **`pprx_dump`**: `GRANT SELECT ON ebdb.* TO 'pprx_dump'@'%'` (read-only dump source; zero write privileges and zero access to `pprx_staging`).
- **`pprx_staging`**: `GRANT ALL PRIVILEGES ON pprx_staging.* TO 'pprx_staging'@'%'` (zero access to `ebdb`).

> [!NOTE]
> DigitalOcean Managed MySQL grants global/partial privileges by default when creating users in the Control Panel. If re-provisioning either user, connect as `doadmin` and run `REVOKE ALL PRIVILEGES, GRANT OPTION FROM '<user>'@'%';` before applying the scoped database grant.

### Prerequisites

1. **MySQL client tools**: `mysqldump.exe` and `mysql.exe` on `PATH` or installed via **MySQL Workbench 8.0 CE** (`C:\Program Files\MySQL\MySQL Workbench 8.0 CE`).
2. **Trusted Sources**: Confirm your current workstation IP and `pprx-staging` are listed under `pprx-prod` **Network Access → Trusted Sources** in DigitalOcean.
3. **Local clone config**: Copy `.env.staging-clone.example` to `.env.staging-clone` (gitignored) at the repo root and fill in:
   - `DB_HOST` (the `pprx-prod` cluster hostname)
   - `DB_PORT` (`25060`)
   - `DB_CA_CERT_PATH` (path to the DigitalOcean MySQL CA `.crt` file)
   - `PPRX_DUMP_USER` (`pprx_dump`)
   - `PPRX_STAGING_USER` (`pprx_staging`)

### Refresh Steps (Run Off-Peak)

Run refreshes during off-peak hours (`pprx-prod` MySQL is `1 vCPU / 1 GB RAM`).

1. **Dry-run pre-flight** (resolves MySQL Workbench tools, validates `.env.staging-clone`, and prints the exact commands without touching either database):
   ```powershell
   .\scripts\clone_prod_to_staging.ps1 -DryRun
   ```
2. **Execute clone and sanitization**:
   ```powershell
   .\scripts\clone_prod_to_staging.ps1
   ```
   The script prompts securely (`Read-Host -AsSecureString`) for `pprx_dump` and `pprx_staging` passwords (or reads `PPRX_DUMP_PASSWORD` / `PPRX_STAGING_PASSWORD` if set in the environment), passes credentials via `MYSQL_PWD`, and performs:
   - **Pass 1**: Positional `mysqldump` of `ebdb` (`--single-transaction --set-gtid-purged=OFF --no-tablespaces --ssl-mode=VERIFY_CA --quick --compress`) ignoring `ebdb.chart_pairs` data (`--ignore-table=ebdb.chart_pairs`).
   - **Pass 2**: `mysqldump --no-data` for `ebdb chart_pairs`, appended to the temp dump file in `$env:TEMP` (always removed in `finally`).
   - **Clean-slate restore**: Drops all existing views and tables in `pprx_staging` and restores the dump into `pprx_staging`.
   - **Sanitize**: Executes `scripts/sanitize_staging.sql` against `pprx_staging`.
3. **Apply pending staging migrations**:
   Because `main` may have Django migrations ahead of `prod`, open the `pprx-staging` App Platform **Console** and run:
   ```bash
   python manage.py migrate
   ```

### Sanitization Invariants (`scripts/sanitize_staging.sql`)

- **Database guard**: Aborts via `SIGNAL SQLSTATE '45000'` if `DATABASE()` is not `'pprx_staging'`.
- **`auth_user` scrubbing**: Sets `email = ''`, `password = '!unusable'`, and `is_superuser = 0` for all `is_staff = 0` accounts except `rrwoods`. `is_staff = 1` accounts retain login/staff access for Admin and UI testing.
- **`scorebrowser_user` token & flag scrubbing**: Sets `access_token = NULL`, `refresh_token = NULL`, and `reauth = 0` for every `User` except `rrwoods` (including other staff accounts). Resets `webhooked = 0`, `pulling_scores = 0`, and `synchronization_started_at = NULL` (when that column exists) for all `Users`.
- **Session invalidation**: Runs `TRUNCATE TABLE django_session` so production sessions cannot be replayed on staging.

### Live Verification Caveats

- **Password-reset email testing (`reset_password`)**: Because `sanitize_staging.sql` clears `auth_user.email` to `''` for non-staff `Users`, submitting `/scorebrowser/reset_password` only emits a reset email to `pprx-staging` **Runtime Logs** when targeting an unscrubbed `is_staff = 1` email address. Generated `finish_reset` links use `https://` via `SECURE_PROXY_SSL_HEADER`.
- **3icecream OAuth token refresh on staging**: `rrwoods`'s cloned OAuth tokens are preserved so manual `Synchronization` (`force_fetch` or `python manage.py fetch rrwoods`) works on staging. When `rrwoods`'s cloned `access_token` is expired, `perform_fetch` calls `refresh_user()` against 3icecream (using `SANBAI_OAUTH_REDIRECT_URI=https://pprx.gg/scorebrowser/scores`) and writes the rotated tokens into `pprx_staging.scorebrowser_user`. Because 3icecream may rotate refresh tokens on refresh, refreshing `rrwoods` on staging can invalidate `rrwoods`'s production `refresh_token` in `ebdb` until the next prod-to-staging clone or production re-link.
- **Fresh browser OAuth linking (`link_sanbai`) & webhooks**: Fresh browser OAuth linking on staging is not supported when 3icecream enforces exact callback domain matching (`pprx.gg`), and automatic webhook registration/delivery remains disabled (`WEBHOOK_ID` unset).

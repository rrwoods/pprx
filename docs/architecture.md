# System Architecture & Transitional Notes

> [!WARNING] Transitional Scaffold
> This document exists solely to catalog cross-cutting pipeline flows, operational landmines, 
> and fragile dependencies that are not yet encapsulated behind clean interfaces or automated tests.
> 
> **Sunset Criteria (Delete this file when):**
> 1. The cross-cutting flows described herein are encapsulated behind stable module interfaces.
> 2. Documented operational landmines and runtime hazards are covered by deterministic automated tests.
> 3. Module-specific invariants are co-located in inline docstrings/comments at their respective seams.
> 
> *When your changes satisfy these criteria, delete this file and remove its pointer from `AGENTS.md`.*

---

## 1. System Topology & Infrastructure

- **Environments & Branching** (DigitalOcean App Platform, `sfo` / VPC `default-sfo3`, `source_dir: pprxweb`):
  - **Production (`pprx-prod`)**: Deploys from `prod` (`deploy_on_push: true`), serving `pprx.gg` (`pprx-prod-pe9zb.ondigitalocean.app`), backed by `ebdb` on the `pprx-prod` Managed MySQL `8.0.45` cluster. Promoted from `main` via fast-forward (**Actions → Promote to prod**; see [Prod Promotion Runbook](runbooks/promote-to-prod.md)).
  - **Staging (`pprx-staging`)**: Deploys from `main` (`deploy_on_push: true`), serving `https://pprx-staging-2xs7w.ondigitalocean.app`, backed by `pprx_staging` on the shared `pprx-prod` Managed MySQL cluster (with Trusted Sources enabled and `chart_pairs` cloned schema-only).
  - **CI**: `.github/workflows/ci.yml` runs on `push` and `pull_request` for `["main", "prod"]`.
- **Database**: Managed MySQL in production/staging (`utf8mb4` charset, `STRICT_ALL_TABLES`). Local development targets SQLite at `pprxweb/pprx.db`.
- **Staging Parameterization & Guards** (`pprxweb/pprxweb/settings.py`):
  - `load_runtime_settings` parameterizes `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DEBUG`, `EMAIL_BACKEND`, `WEBHOOK_ID`, `SANBAI_OAUTH_REDIRECT_URI`, optional `DB_CA_CERT`, and `IS_STAGING` (with production-compatible defaults), and sets `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.
  - On staging: `IS_STAGING=True` renders the `STAGING ENVIRONMENT` banner via `scorebrowser.context_processors.staging_context`, `WEBHOOK_ID` is unset (`""`) so `register_webhook()` is skipped, empty-score `Fetch` in `scores` is gated on `scores_user.access_token`, `EMAIL_BACKEND` uses `console.EmailBackend`, and `SANBAI_OAUTH_REDIRECT_URI` preserves token-refresh compatibility.
- **Operational Runbooks**: See [Prod Promotion Runbook](runbooks/promote-to-prod.md) for fast-forward promotion to `prod`, and [Staging Operations & DB Refresh Runbook](runbooks/staging-operations.md) for least-privilege MySQL roles (`pprx_dump`, `pprx_staging`), `scripts/clone_prod_to_staging.ps1`, `scripts/sanitize_staging.sql`, and live verification caveats.
- **Static Assets**: Served via WhiteNoise (`CompressedManifestStaticFilesStorage`).
- **Legacy Artifacts**: Directories `.ebextensions/`, `.elasticbeanstalk/`, and `.platform/` are historical artifacts from an earlier AWS Elastic Beanstalk deployment and are inactive.

---

## 2. Core Pipelines & Data Flow

### A. Chart Ingestion & Catalog Maintenance
- **Entry point**: `python manage.py updatecharts` (`pprxweb/scorebrowser/management/commands/updatecharts.py`)
- **Source**: Fetches `https://3icecream.com/js/songdata.js`.
- **Flow**:
  1. Parses raw JS object slice to extract song titles, version numbers, and rating arrays.
  2. Updates `Song` records and creates/updates `Chart` records (1–5 difficulties: Beginner, Basic, Difficult, Expert, Challenge).
  3. Automatically computes sort keys via `sort_key()` in `pprxweb/scorebrowser/misc.py` mapping Japanese hiragana/katakana and Latin characters into in-game sorting sequence.
  4. Associates uncompleted Challenge charts with the `New Challenge charts (A3+)` unlock task.

### B. Synchronization (Fetch + Ingest)
Encapsulated in `pprxweb/scorebrowser/synchronization.py` behind `synchronize(user, source=None) -> SynchronizationResult` (with `is_synchronization_in_progress(user)` for status checks and `refresh_user(user)` shared with webhook registration in `views.py`):

- **Callers** (all run synchronously in the request/command thread):
  - Webhook handler `synchronization_webhook` (`pprxweb/scorebrowser/views.py`, URL path/name `fetch_scores`), triggered by 3icecream's on-update webhook with `player_id`. Rate-limited via `user.last_fetch` to one Synchronization per User per 10 minutes (600s) and maps `SynchronizationResult.outcome` to an HTTP response.
  - Manual `force_synchronization` view (`pprxweb/scorebrowser/views.py`, URL path/name `force_fetch`), not rate-limited; maps `SynchronizationResult.outcome` to an HTTP response.
  - `scores` view (`pprxweb/scorebrowser/views.py`): triggers `synchronize` after first-time webhook registration or when the User has zero Current Scores. When `is_synchronization_in_progress(scores_user)` is true, renders stored scores immediately with the `#synchronization-in-progress` banner.
  - CLI `python manage.py synchronize <username>` (`pprxweb/scorebrowser/management/commands/synchronize.py`), which prints `SynchronizationResult.outcome`.
- **Concurrency claim ([ADR-0004](adr/0004-timestamp-claim-for-synchronization-concurrency.md))**:
  1. Before the Fetch, `synchronize` acquires a conditional `UPDATE` claim on `User.synchronization_started_at` (succeeding only when null or older than `CLAIM_TIMEOUT` = 10 minutes). Failing to claim returns `ALREADY_RUNNING`; stale claims count as abandoned/idle.
  2. The claim is released in a `finally` block so expected outcomes and unexpected exceptions both clear it; unexpected exceptions propagate rather than being swallowed.
- **`UpstreamScoreSource` seam & Fetch**:
  3. Talks to upstream through the `UpstreamScoreSource` protocol (`fetch_scores(user) -> list[UpstreamScore]`). Production uses `SanbaiScoreSource` (3icecream's `/dev/api/v1/get_scores`, refreshing once on HTTP 400 and retrying once, raising `ReauthRequired` on refresh failure or `UpstreamError` on non-200 responses); tests inject an in-memory fake.
- **Ingest**:
  4. Skips doubles charts, discovers unknown songs/charts (linking pre-A3 Challenge charts to `New Challenge charts (A3+)`), merges `score`, `clear_type`, and `flare_gauge` monotonically (never downgrading stored values), computes normalized score and Quality (for cleared scores with breakpoints), and atomically writes superseded (`current = None`) and new (`current = True`) `UserScore` rows ([ADR-0002](adr/0002-nullable-boolean-for-current-scores.md)).

### C. Statistical Difficulty Calibration (Spice & Quality)
Offline batch processing pipeline executed out-of-band:
1. **`normalizescores`** (`pprxweb/scorebrowser/management/commands/normalizescores.py`): Sets logarithmic normalized values for all public scraped scores.
2. **`comparecharts`** (`pprxweb/scorebrowser/management/commands/comparecharts.py`): Identifies charts within 1 level. Runs Orthogonal Distance Regression (`scipy.odr`) on mutual player scores (between 800,000 and 999,000), storing relative slopes and statistical strengths in `ChartPair`.
3. **`computespice`** (`pprxweb/scorebrowser/management/commands/computespice.py`): Iteratively solves relative chart difficulty using weighted geometric means across 100 iterations.
   - Applies level barrier penalties (divisor of 1000 between levels 13 and 14 to isolate high-tier grinder variance).
   - Anchors scale: *MAX 300* Expert (difficulty 3) = 10.0.
   - Applies upper-end piecewise linear fudge curve (levels 16–20) tuned to LIFE4 Emerald V benchmark thresholds.
4. **`isotonicspice`** (`pprxweb/scorebrowser/management/commands/isotonicspice.py`): Uses Centered Isotonic Regression (`cir_model`) on chart pairs to establish monotonic `normscore_breakpoints` and `quality_breakpoints` on each chart.
5. **`updatequality`** (`pprxweb/scorebrowser/management/commands/updatequality.py`): Recomputes quality values across all stored user scores using newly derived breakpoints.

### D. Scores View & Datatable Serialization
- **Entry point**: `scores` view (`pprxweb/scorebrowser/views.py`).
- **Flow**:
  1. Resolves authenticated user, permissions, and profile visibility (public, friends, staff-only).
  2. Queries all `Chart` records, `UserScore` (filtered by `current=True`), and `UserChartAux` (bookmarks, notes, LIFE4 clears).
  3. Evaluates cabinet and region locks (White cab vs Gold cab vs Gold-only) and progressive unlock events.
  4. Generates a monolithic JSON array representing all charts in the game with calculated goal distance, quality rank, and visibility states, injected into the `scores.html` template for client-side rendering via DataTables (`scores-2.2.10.js`).

---

## 3. Operational Landmines, Dirty Hacks & Quirks

### 1. Fragile String Slicing on `songdata.js`
- **Location**: `pprxweb/scorebrowser/management/commands/updatecharts.py`
- **Risk**: Stripping the JavaScript prefix/suffix relies on fixed byte strings:
  ```python
  prefix = b'var ALL_SONG_DATA='
  suffix = b';const EVENT_EXCLUSIONS=[...];const SONG_DATA_LAST_UPDATED_unixms=1774588615027;'
  ```
- **Hazard**: If 3icecream updates the exclusion array or changes the timestamp length, JSON decoding crashes or slices corrupted data.

### 2. Strict List Unpacking on Cabinet Configuration
- **Location**: `pprxweb/scorebrowser/views.py` (`scores` view)
- **Code**:
  ```python
  [white_cab] = [c for c in all_cabinets if (not c.gold and c.region_id == scores_user.region_id)]
  [gold_cab] = [c for c in all_cabinets if c.gold]
  ```
- **Hazard**: Raises `ValueError: not enough values to unpack` (or `too many values to unpack`) if the `Cabinet` table ever lacks an exact match for the user's region or contains multiple active gold/white cabinets.

### 3. Duplicate User Splitting
- **Location**: `pprxweb/scorebrowser/management/commands/unsplit-user.py`
- **Hazard**: Re-authenticating with 3icecream or OAuth linking edge-cases can spawn orphaned or duplicate `User` rows sharing scores, requiring manual un-splitting migrations.

### 4. In-Memory Primitive Pointer Emulation
- **Location**: `pprxweb/scorebrowser/management/commands/isotonicspice.py`
- **Hazard**: Uses single-element mutable lists `[quality]` inside assumption dictionaries as primitive pointers to allow mutable reference passing across regression steps.

### 5. Migration Chain Cannot Be Replayed on an Empty Database
- **Location**: `pprxweb/scorebrowser/migrations/` (first failure: `0017_event_data.py`)
- **Hazard**: Data migrations look up `Chart` rows by song title, but Songs and Charts are populated out-of-band by `updatecharts` (from 3icecream's `songdata.js`), not by migrations. On a fresh database the lookups return `None` and `0017` fails with `NOT NULL constraint failed: scorebrowser_chartunlock.chart_id`. Production only works because its database was built up gradually, with `updatecharts` run between migrations. Consequences: no fresh environment can be built from migrations alone, and `manage.py test` cannot build a test database.
- **Second blocker**: `0034` imports today's `scorebrowser.models.default_region`, which queries `Region.user_default`, a column added in `0078`. Replay fails there even without any Catalog data.
- **Resolution**: Test databases skip `scorebrowser` migrations and build the schema from models ([ADR-0006](adr/0006-test-schema-built-from-models.md), tracked by [#64](https://github.com/rrwoods/pprx/issues/64)). Catalog changes no longer go through migrations ([ADR-0005](adr/0005-catalog-changes-through-admin-not-migrations.md)). Replaying the chain for new-developer environments is tracked by [#65](https://github.com/rrwoods/pprx/issues/65).

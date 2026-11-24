# Runbook: Promote `main` to `prod`

Standard procedure for promoting verified changes from `main` (`pprx-staging`) to `prod` (`pprx-prod` / `https://pprx.gg`).

## Why Promotion Is Automated as a Fast-Forward

GitHub PR merge buttons (**Rebase and merge** and **Squash and merge**) always rewrite commit SHAs on the base branch, causing `prod` and `main` to diverge even when trees are identical. To keep `main` and `prod` on a single shared linear history:

- **UI PR merges to `prod` are blocked**: [`.github/workflows/forbid-prod-ui-merge.yml`](../../.github/workflows/forbid-prod-ui-merge.yml) (`forbid-ui-merge`) fails on every PR targeting `prod` so the GitHub Merge button stays locked while `Django CI` (`build`) still runs and reports green.
- **Promotion runs via GitHub Actions**: [`.github/workflows/promote-to-prod.yml`](../../.github/workflows/promote-to-prod.yml) (`Promote to prod`) uses a dedicated GitHub App in `prod`'s Ruleset bypass list to fast-forward `prod` to `main` with a non-force push.

---

## Pre-flight Checklist

Before promoting `main` to `prod`:

1. **All intended PRs are merged to `main`** and `Django CI` ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)) has completed with `success` on `main`'s HEAD commit.
2. **Staging verification passed** on `https://pprx-staging-2xs7w.ondigitalocean.app` (see [Staging Operations & DB Refresh Runbook](staging-operations.md)).
3. **Check for migrations, env vars, or data steps**:
   ```powershell
   git fetch origin
   git log --oneline origin/prod..origin/main
   git diff --stat origin/prod..origin/main
   ```
   - If new Django migrations are included, make sure they were tested on staging and plan to run `python manage.py migrate` on `pprx-prod` immediately after deploy.
   - If new runtime env vars are required by `pprxweb/pprxweb/settings.py`, add them to `pprx-prod` in DigitalOcean App Platform **before** promoting.

---

## Promotion Steps

1. **(Optional) Open a `main` → `prod` PR for review**
   - Opening a PR from `main` into `prod` lets you inspect the full commit list and diff on GitHub and confirm `Django CI / build` passes.
   - `Block PR UI merge to prod / forbid-ui-merge` will intentionally fail and keep the Merge button disabled—do not bypass it.

2. **Run the `Promote to prod` workflow**
   - In GitHub, open **Actions → Promote to prod → Run workflow**.
   - Keep branch set to **`main`** and **`skip_ci_check`** set to **`false`**.
   - Click **Run workflow**.
   - The workflow verifies:
     - `origin/prod` is a strict ancestor of `origin/main` (`git merge-base --is-ancestor`).
     - `Django CI` (`ci.yml` `push` run) completed with `success` on `origin/main`'s HEAD commit.
     - Runs `git push origin "${MAIN_SHA}:refs/heads/prod"` (non-force fast-forward) using the GitHub App token.
   - Once `prod` reaches `main`'s HEAD SHA, GitHub automatically closes any open `main` → `prod` PR as **Merged**, and DigitalOcean App Platform starts deploying `pprx-prod` (`deploy_on_push: true`).

3. **Post-deploy verification & migrations**
   - Watch the `pprx-prod` deployment in DigitalOcean App Platform until it settles **Healthy**.
   - If the release includes pending Django migrations, open the `pprx-prod` App Platform **Console** and run:
     ```bash
     python manage.py migrate
     ```
   - Smoke-test `https://pprx.gg` (and verify the production `.update-message` banner, not the staging banner, is rendered).

---

## Troubleshooting

### `Cannot fast-forward: prod (...) is not an ancestor of main (...)`

`main` and `prod` have diverged (typically from an accidental Rebase/Squash merge or a commit pushed directly to `prod`).

1. Compare commits and file trees:
   ```powershell
   git fetch origin
   git cherry -v origin/prod origin/main
   ```
2. If the commits on `prod` are rewritten copies of commits already on `main` (marked `-` by `git cherry` and empty `git diff` at the matching tip), rebase `main` (and any open feature branches) onto `origin/prod`:
   ```powershell
   git switch main
   git rebase --onto origin/prod <old-main-commit-matching-prod> main
   git push --force-with-lease origin main
   ```
3. If `prod` has a hotfix commit not yet on `main`, fast-forward or cherry-pick/rebase `main` onto `origin/prod` so `origin/prod` becomes an ancestor of `main` again before re-running **Promote to prod**.

### `Django CI has not passed for main commit ...`

- Wait for `Django CI` on `main` to finish green, or fix/re-run the failed run before promoting.
- Reserve `skip_ci_check: true` strictly for emergencies (for example, a GitHub Actions outage after tests were verified locally).

### `Create GitHub App token` or `git push` permission error

- Confirm repository Actions secrets `PROD_PROMOTE_APP_CLIENT_ID` (or `PROD_PROMOTE_APP_ID`) and `PROD_PROMOTE_APP_PRIVATE_KEY` are configured.
- Confirm the GitHub App is installed on `rrwoods/pprx` with `Contents: Read and write` permission and added to the `prod` Ruleset **Bypass list** (and that no legacy classic branch protection rule remains on `prod`).

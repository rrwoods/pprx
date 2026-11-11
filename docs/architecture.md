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

- **Production Target**: Deployed on **DigitalOcean App Platform** (`pprx.gg`, internally `pprx-prod-pe9zb.ondigitalocean.app`).
- **Database**: Managed MySQL in production (`utf8mb4` charset, `STRICT_ALL_TABLES`). Local development targets SQLite at `pprxweb/pprx.db`.
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
> Slated for consolidation behind a single Synchronization module by [#59](https://github.com/rrwoods/pprx/issues/59) (concurrency guard: [ADR-0004](adr/0004-timestamp-claim-for-synchronization-concurrency.md)). Rewrite this section when that lands.

- **Entry points** (all call `perform_fetch()` in `pprxweb/scorebrowser/views.py`, synchronously in the request thread):
  - Webhook handler `fetch_scores`, triggered by 3icecream's on-update webhook with `player_id`. Rate-limited to one Synchronization per user per 10 minutes (600s); the other entry points ignore this limit.
  - Manual `force_fetch` view.
  - `scores` view: after first-time webhook registration, and whenever the User has zero Current Scores.
  - CLI `python manage.py fetch <username>` (imports `perform_fetch` from `views.py`).
- **Fetch**:
  1. Requests scores from `https://3icecream.com/dev/api/v1/get_scores` using stored OAuth `access_token`. On 400 responses, refreshes the token via `refresh_user()` and retries once; on refresh failure sets `user.reauth = True`.
- **Ingest**:
  2. Sets `user.pulling_scores = True` (only *after* the Fetch succeeds) and clears it in a `finally`.
  3. Discovers unknown charts: creates missing `Song` rows (`version_id=20`) and hidden `Chart` rows, linking pre-A3 Challenge charts to the `New Challenge charts (A3+)` unlock task. Doubles charts (`difficulty > 4`) are skipped.
  4. Computes normalized score: \(- \log_2(1,000,000 - \text{score})\) (or \(-2.323\) for 1,000,000 MFCs).
  5. Computes score Quality via `numpy.interp` against chart breakpoints (`normscore_breakpoints` and `quality_breakpoints`); failed scores (lamp 0) get no Quality.
  6. A fetched record supersedes the Current Score when its score is higher, its lamp is better, or its flare gauge differs (`!=`, so a missing upstream flare wipes a stored gauge).
  7. Atomic DB transaction: Marks superseded scores as `current = None` and inserts new scores as `current = True` via bulk operations (see [ADR-0002](adr/0002-nullable-boolean-for-current-scores.md)).
- **Failure mode**: Any exception during Ingest is printed and swallowed, and `perform_fetch` returns `None`, so the `fetch_scores` and `force_fetch` views respond with a Django 500.

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

### 2. Request Thread Sleep Loop on Background Score Pull
- **Location**: `pprxweb/scorebrowser/views.py` (`scores` view)
- **Code**:
  ```python
  if scores_user.pulling_scores:
      while True:
          time.sleep(1)
          scores_user = User.objects.get(id=user_id)
          if not scores_user.pulling_scores:
              break
  ```
- **Hazard**: When a user loads `/scores` while a Synchronization is running, the WSGI request thread enters a synchronous sleep loop, holding the worker connection open and risking gateway timeouts under load.
- **Hazard (unbounded)**: If a worker is killed mid-Ingest (e.g. gateway or worker timeout), the `finally` that clears `pulling_scores` never runs; the flag stays `True` and every subsequent `/scores` load for that User loops forever.
- **Hazard (not a lock)**: `pulling_scores` is a read-then-write flag set only after the Fetch, so concurrent Synchronizations (e.g. webhook + `force_fetch`) can both proceed; the second typically fails on ADR-0002's unique constraint.
- **Resolution**: Tracked by [#59](https://github.com/rrwoods/pprx/issues/59) (timestamp claim per [ADR-0004](adr/0004-timestamp-claim-for-synchronization-concurrency.md); `/scores` renders stored scores with an in-progress banner). Delete this landmine when it lands.

### 3. Strict List Unpacking on Cabinet Configuration
- **Location**: `pprxweb/scorebrowser/views.py` (`scores` view)
- **Code**:
  ```python
  [white_cab] = [c for c in all_cabinets if (not c.gold and c.region_id == scores_user.region_id)]
  [gold_cab] = [c for c in all_cabinets if c.gold]
  ```
- **Hazard**: Raises `ValueError: not enough values to unpack` (or `too many values to unpack`) if the `Cabinet` table ever lacks an exact match for the user's region or contains multiple active gold/white cabinets.

### 4. Duplicate User Splitting
- **Location**: `pprxweb/scorebrowser/management/commands/unsplit-user.py`
- **Hazard**: Re-authenticating with 3icecream or OAuth linking edge-cases can spawn orphaned or duplicate `User` rows sharing scores, requiring manual un-splitting migrations.

### 5. In-Memory Primitive Pointer Emulation
- **Location**: `pprxweb/scorebrowser/management/commands/isotonicspice.py`
- **Hazard**: Uses single-element mutable lists `[quality]` inside assumption dictionaries as primitive pointers to allow mutable reference passing across regression steps.

### 6. Migration Chain Cannot Be Replayed on an Empty Database
- **Location**: `pprxweb/scorebrowser/migrations/` (first failure: `0017_event_data.py`)
- **Hazard**: Data migrations look up `Chart` rows by song title, but Songs and Charts are populated out-of-band by `updatecharts` (from 3icecream's `songdata.js`), not by migrations. On a fresh database the lookups return `None` and `0017` fails with `NOT NULL constraint failed: scorebrowser_chartunlock.chart_id`. Production only works because its database was built up gradually, with `updatecharts` run between migrations. Consequences: no fresh environment can be built from migrations alone, and `manage.py test` cannot build a test database.
- **Resolution**: Tracked by [#64](https://github.com/rrwoods/pprx/issues/64) (safe, self-contained test database).

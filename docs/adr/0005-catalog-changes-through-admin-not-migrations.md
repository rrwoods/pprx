# Catalog Changes Go Through the Admin Interface, Not Migrations

The Catalog (Songs, Charts, SongLocks and every Unlock table) mirrors what Konami releases. It changes whenever Konami ships new songs or events, which makes it data, not schema. Early in the project, Catalog changes were written as data migrations: about 140 of `scorebrowser`'s first 203 migrations create, rename, reorder or delete Catalog rows, mostly by looking up Charts by song title. Since 2026-01-01, every Catalog change has gone through the staff admin views in `scorebrowser/views.py` instead, and migrations carry only schema changes, Base Data and fixes to user data. We decided to keep it that way. Migrations stay for schema changes; the admin interface (with `updatecharts` for Songs and Charts) handles the Catalog.

## Consequences

- The historical Catalog migrations are not a faithful record of production's Catalog and cannot be replayed:
  - Most of them assume Charts loaded out-of-band by `updatecharts`.
  - Task names include chart ratings from the day they were created.
  - Some depend on admin edits made between migrations; for example, `0182` expects exactly one "GOLD CLASS with advanced border" task, but `0176` and `0179` each create one.

  Skipping or emptying them on a fresh database loses nothing that exists in production. See ADR-0006.
- Production's Catalog is the only authoritative copy. A new environment that needs a realistic Catalog gets it from a copy of production data, not from migrations.
- Tables are classified as a whole:
  - **Base Data**: Difficulty, Version, Region, Cabinet, CabinetModel, ProfileVisibility.
  - **Catalog**: Song, Chart, SongLock, UnlockGroup, UnlockEvent, UnlockTask, ChartUnlock.
  - **User and calibration data**: everything else.

  Base Data changes at most once per game version (see `docs/runbooks/new-game-version.md`). A migration may still write Base Data.
- One Catalog row is an exception. The `New Challenge charts (A3+)` UnlockTask doesn't correspond to anything Konami released. It exists so that Users in the A20PLUS-only region don't see Challenge charts they can't play, and `updatecharts` and Synchronization look it up by name. Replacing it is tracked by #66.

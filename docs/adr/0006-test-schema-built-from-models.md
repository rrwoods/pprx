# Test Schema Is Built From Models, Not Migrations

`manage.py test` cannot build a database by replaying `scorebrowser`'s migrations. Data migrations fail on an empty database, starting at `0017`, because they depend on Catalog rows that never arrive (ADR-0005). `0034` fails as well, independently of the Catalog: it imports today's `default_region`, which queries a column added in `0078`. We decided that test runs set `MIGRATION_MODULES = {'scorebrowser': None}`, so Django builds the test schema from the current models. A shared test setup then loads a committed fixture of the Base Data tables, and CI runs `makemigrations --check --dry-run` to keep models and migrations from drifting apart.

## Considered Options

- **Empty the Catalog operations in place**: Rejected for now. It means editing about 140 migrations and splitting 7 that mix Catalog writes with schema or Base Data. `0034` needs a fix too, and every test run replays about 200 migrations. Its main benefit, proving that new migrations apply, matters less now that migrations are almost entirely schema changes, and the drift check covers most of those.
- **Baseline migration replacing all 203**: Rejected for now. It would need a schema comparison against production, plus a deploy step to retire the old files.
- **Snapshot of a real database**: Rejected. It isn't self-contained, can't run in CI, and would put real User data into tests.
- **Skip `scorebrowser` migrations in test runs**: Selected. No migration file changes, test databases build quickly, and the scope is a test database only. Building new-developer environments is a separate problem (#65), and the two rejected migration options remain open for it.

## Consequences

- Tests never prove that a migration's `RunPython` code works. A migration that transforms data needs its own manual verification.
- The Base Data fixture mirrors production's Base Data tables. It's exported from a local copy and re-exported when Konami releases a new game version (`docs/runbooks/new-game-version.md`).
- The shared test setup also creates the `New Challenge charts (A3+)` UnlockTask and its event, written out by hand. ADR-0005 explains this exception. Every other Catalog row, plus all user and calibration data, is created by the test that needs it.
- Test isolation from production doesn't depend on this decision. Settings detect a test run before choosing a database and force in-memory SQLite, and the test runner refuses other engines and blocks outbound sockets.

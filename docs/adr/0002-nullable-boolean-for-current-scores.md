# Nullable Boolean Flag for Current Score Invariant

A User can accumulate multiple historical scores on a Chart over time, but queries require fast access to exactly one active "current" score per user-chart pair. We decided to define the `current` column as a nullable boolean (`models.BooleanField(null=True)`) constrained by `UniqueConstraint(fields=['user', 'chart', 'current'])`, setting outdated scores to `current = None`. Because standard SQL treats `NULL` values as distinct, this enforces at most one `current = True` record per user and chart across both SQLite and MySQL without relying on database-specific filtered/partial unique index migrations.

## Consequences

- Superseding an existing score requires explicitly setting `old_score.current = None` before inserting or updating the new record with `current = True`.
- Filtering for the current score must always explicitly check `current=True` rather than boolean truthiness in SQL.

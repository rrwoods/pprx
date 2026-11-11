# Timestamp Claim for Synchronization Concurrency

A User's Synchronization can be triggered concurrently by the 3icecream webhook, a manual force, and the scores page, all running synchronously in request threads that a gateway or worker timeout may kill mid-flight. We decided to guard each Synchronization with a nullable `User.synchronization_started_at` timestamp, claimed before the Fetch by a single conditional `UPDATE` that succeeds only when the field is null or older than 10 minutes, and cleared in a `finally` block. A claim older than the cutoff is treated as abandoned, so a killed worker can never wedge a User permanently.

## Considered Options

- **Boolean `pulling_scores` flag**: Rejected. A killed worker skips its `finally`, leaving the flag set forever with no way to distinguish a crashed Synchronization from a running one; the read-then-write check also let concurrent Synchronizations through.
- **Row lock (`select_for_update`) held for the whole Synchronization**: Rejected. It holds a database transaction open across network I/O to 3icecream, and local development on SQLite does not support row-level locking.
- **Timestamp claim with staleness cutoff**: Selected. Atomic on both MySQL and SQLite, self-healing after crashes, and requires no transaction spanning the Fetch.

## Consequences

- The 10-minute cutoff deliberately matches the webhook's 600-second rate limit, so an abandoned claim expires no later than the next webhook would be accepted.
- A Synchronization that legitimately runs longer than the cutoff could be overlapped by a second one; ADR-0002's unique constraint on Current Scores remains the backstop.
- "Synchronization in progress" means a claim younger than the cutoff; a stale claim reads as idle.

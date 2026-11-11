## Agent skills

### Issue tracker

GitHub issues (via `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical triage roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Product Vision

For the long-term destination, core architectural invariants, and non-goals, see `VISION.md`. Consult before proposing high-level specs or major architectural direction.

### Domain docs

Single-context layout (`GLOSSARY.md` + `docs/adr/`). See `docs/agents/domain.md`.

### Architecture docs

- `docs/architecture.md`: Transitional scaffold for cross-cutting pipelines and operational landmines.
  - **Pruning gate**: Whenever refactoring or adding tests to areas documented here, check if the complexity has been pushed behind clean seams or codified into tests. If so, propose deleting this document.

## Workflow and git conventions

### Git conventions

Prefer linear git history:
- **Line endings**: Universal LF is strictly enforced. Automated pre-commit hook runs `scripts/check-lf.ps1 -Fix` followed by `git update-index --again`.
- **Synchronous commit execution**: Set `WaitMsBeforeAsync: 10000` when executing `git commit` so pre-commit hooks complete synchronously.
- **Commit subject length**: Commit subject lines must be 50 characters or fewer (enforced by `.git/hooks/commit-msg`).
- **Reactive wakeup on background tasks**: When a command runs as an asynchronous background task or a subagent is launched, immediately yield the turn without querying `manage_task status` or calling `schedule`. Rely exclusively on the system's reactive wakeup message to resume execution.


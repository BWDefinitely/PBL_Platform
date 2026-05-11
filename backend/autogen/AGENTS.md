# Project Recording Rules

This project uses a local recording system in addition to any global Codex rules.

## Recording Workflow

- Check that `docs/` recording files exist before starting substantial work.
- For an existing project, backfill major completed phases before switching to real-time logging.
- After each meaningful step, append a structured entry to `docs/dev_journal.md`.
- Meaningful steps include: a confirmed discussion decision, a code change, a debug cycle, a command run, or an experiment result.

## Required Journal Fields

Every substantial change must capture:

- `Goal`
- `Problem`
- `Root Cause`
- `Solution`
- `Validation`
- `Impact`
- `Next`

If a field does not apply, write `N/A` rather than omitting it.

## Code and Docs

- Add teaching-oriented comments for important Python logic, non-obvious control flow, data transformations, and edge-case handling.
- Do not add line-by-line comments for trivial code.
- When a file can be configured manually, update `docs/config_guide.md` in the same task.
- When a long-lived design choice is made, update `docs/decisions.md`.
- When the current state changes materially, update `docs/project_status.md`.

## Secrets and Traceability

- Default to redacting secrets, tokens, and sensitive paths in human-readable docs.
- Prefer linking records back to commands, configs, outputs, and file paths.
- Keep `README.md` as the entry document, not the full work log.

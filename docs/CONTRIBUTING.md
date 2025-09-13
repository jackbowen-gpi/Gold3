# CONTRIBUTING — gchub_db

Thanks for contributing. This file describes a minimal workflow to make changes safely and testably.

## Branching & PRs
- Create feature branches from `main` (or `jb-gold3-v1` if you're iterating there).
- Branch naming example: `feature/<short-desc>` or `fix/<short-desc>`.
- Open a Pull Request against `main` when ready; CI will run tests automatically.

## Local review checklist
- Run `scripts/setup_dev.ps1` (or manually create venv and install deps).
- Run `scripts/run_tests.ps1` and ensure tests pass locally before pushing.
- Include unit or smoke tests for new features where appropriate.

## Commit messages and style
- Keep commits small and focused.
- Use present-tense imperative commit messages (e.g., "Fix logging in workflow app").
- Prefer explicit imports and module paths. Update `INSTALLED_APPS` with `dotted.path.apps.AppConfig` where applicable.

## CI
- CI runs the tests using Python 3.13 and the test command in the README/workflow file. If you change dependencies, update `requirements.txt` and the CI workflow.

## Restoring backups
- Backups were archived as `..\gchub_db_backups_YYYYMMDD_HHMMSS.zip`. To restore, extract to a temporary folder and selectively copy files into a branch for review.

## Need help?
- If you're not sure where to start, run the smoke tests in `gchub_db/apps/*/tests` or ask to pair on a small story.

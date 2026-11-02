# AstroMYLA v1.9.2 Windows SQLite Test Fix

The first v1.9.2 deploy attempt failed during `test_migrates_existing_database_without_losing_charts` on Windows due to `PermissionError: [WinError 32]` when Python's `TemporaryDirectory` tried to remove a SQLite database still held open by the test fixture.

Fix: `backend/tests/test_v192.py` now wraps the fixture connection in `contextlib.closing(sqlite3.connect(path))`, explicitly closing it before `TemporaryDirectory` cleanup.

This is a test fixture correction, not a change to live account data or stored natal charts.

Validation: 50/50 backend unit tests PASS in the packaging environment after patch. **Windows has not been retested in this environment**; the included deploy script will rerun all backend tests and the frontend production build on your Windows machine before pushing to GitHub.

Deployment: extract this updated ZIP (do not reuse the older v1.9.2 ZIP), open PowerShell in the inner `AstroMYLA_v1.9.2_HUMAN_TOUCH` directory, run `Set-ExecutionPolicy -Scope Process Bypass`, then `.\DEPLOY_ASTROMYLA_V1_9_2.ps1`. No skip flags. The script compares `main` with the expected v1.9.1 commit, creates a rollback branch, and only pushes after tests/build pass.

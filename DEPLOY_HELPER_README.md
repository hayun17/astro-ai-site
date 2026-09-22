# AstroMYLA v1.6.0 — Deploy helper

1. Extract this ZIP.
2. Open PowerShell inside the extracted `AstroMYLA_v1.6.0_PRODUCTION_RC` folder.
3. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\DEPLOY_ASTROMYLA_V1_6.ps1
```

The helper:
- clones `hayun17/astro-ai-site`;
- creates and pushes a rollback branch at the current production commit;
- replaces the repository with this clean release;
- removes local `.env`, `.venv`, `node_modules`, `dist`, `__pycache__` artifacts;
- performs a clean backend dependency install and 32-test regression suite;
- performs `npm ci` and a Vite production build;
- commits only after all checks pass;
- pushes `main`, which should trigger Render auto-deploy;
- creates a timestamped v1.6.0 RC tag.

If Git asks you to sign in during the push, complete the GitHub browser sign-in and let the script continue.

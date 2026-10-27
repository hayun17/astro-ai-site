# AstroMYLA v1.9.0 Test Report

## Backend

`python -m unittest discover -s tests -v`

Result: **44 / 44 PASS**.

New regression coverage includes:

- natal response contains the AstroMYLA signature suite;
- known birth time uses the 7th-house layer in Ideal Partner Blueprint;
- unknown birth time does not invent 7th-house evidence;
- synastry returns Myla Match themes derived from aspects / house activation.

## Frontend

All `src/**/*.ts` and `src/**/*.tsx` files were syntax-transpiled with TypeScript: **17 files, 0 syntax errors**.

A clean `npm ci` timed out in the packaging environment, so the final Vite bundle is intentionally gated by `DEPLOY_ASTROMYLA_V1_9.ps1`: the script runs `npm ci` and `npm run build` locally before it can push `main`.

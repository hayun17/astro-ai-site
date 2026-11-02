# AstroMYLA v1.9.2 — Human Touch

A full-source deploy-ready release based on v1.9.1, with improved personalized insight cards, concrete bidirectional synastry house storytelling and a post-calculation chart save flow.

**Start here:** `DEPLOY_HELPER_README.md` and `DATABASE_REQUIRED_V1_9_2.md`.

Current scope: natal, transits/daily, synastry, composite, astrocartography, AstroMYLA Signature, Myla Match, free/PDF reports, payment integration foundation and user accounts.

Run backend tests: `cd backend` → `python -m unittest discover -s tests -v` (after installing requirements). Frontend: `cd frontend` → `npm ci` → `npm run build`.

Accounts in production need Render PostgreSQL. The application does not silently save in browser storage when server persistence is unavailable.

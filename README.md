# AstroMYLA v1.10.0 — THE EDIT

**Start here:** [v1.10 changelog](CHANGELOG_V1_10.md) · [production configuration checklist](PRODUCTION_SETUP_V1_10.md)

This update adds a concise, interactive relationship-focused results experience (Big Three, love language, partner type, attraction vs need, emotional manual), directional house-activation synastry, stronger server-verified chart saving and payment protections. Mercury retrograde and Saturn return proximity are now shown in Current Transits. No unverified astronomical placement is invented.

**Do not switch on real payment collection** without the merchant, database, email, AI, legal and end-to-end verification steps in `PRODUCTION_SETUP_V1_10.md`. These dependencies cannot be activated merely by deploying the ZIP.

# AstroMYLA v1.9.2 — Human Touch

A full-source deploy-ready release based on v1.9.1, with improved personalized insight cards, concrete bidirectional synastry house storytelling and a post-calculation chart save flow.

**Start here:** `DEPLOY_HELPER_README.md` and `DATABASE_REQUIRED_V1_9_2.md`.

Current scope: natal, transits/daily, synastry, composite, astrocartography, AstroMYLA Signature, Myla Match, free/PDF reports, payment integration foundation and user accounts.

Run backend tests: `cd backend` → `python -m unittest discover -s tests -v` (after installing requirements). Frontend: `cd frontend` → `npm ci` → `npm run build`.

Accounts in production need Render PostgreSQL. The application does not silently save in browser storage when server persistence is unavailable.

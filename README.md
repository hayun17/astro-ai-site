# AstroMYLA v1.9.0 — Signature Insights + Current Sky + Accounts

AstroMYLA is a responsive astrology web application built around Swiss Ephemeris calculations, relationship astrology, current transits, personalized synthesis and downloadable reports.

## Main tools

- Birth Chart
- Current Transits + Natal/Transit bi-wheel
- Daily Personal Astrology
- Synastry bi-wheel + directional house overlays
- Composite Chart
- Astrocartography
- My AstroMYLA accounts + Saved Birth Charts
- Free and premium PDF/report foundation

## AstroMYLA-native features

- Your AstroMYLA Signature
- Ideal Partner Blueprint
- Who You Attract vs Who You Actually Need
- Your Emotional Manual
- Myla Match
- Connection Profile
- Composite Relationship Identity

See `README_V1_9.md`, `CHANGELOG_V1_9.md`, `TEST_REPORT_V1_9.md`, `DATABASE_SETUP_V1_8.md`, and `DEPLOY_HELPER_README.md`.

## Local development

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend in a second terminal:

```powershell
cd frontend
npm ci
Set-Content .env.local "VITE_API_BASE_URL=http://127.0.0.1:8000"
npm run dev
```

## Commercial note

The numerical chart engine uses Swiss Ephemeris through `pyswisseph`. Review and satisfy Swiss Ephemeris licensing requirements before operating AstroMYLA as a proprietary paid service.

Astrological interpretations are symbolic/interpretive and are not medical, legal, financial or mental-health advice.

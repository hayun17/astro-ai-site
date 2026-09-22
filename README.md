# AstroMYLA v1.6.0 — Production Release Candidate

AstroMYLA is a responsive astrology web application for natal charts, synastry, composite charts, astrocartography, downloadable reports, and protected premium natal reports.

## What is new in v1.6.0

- Unambiguous birth-date entry: **Day / Month / Year** is visible in the UI and each part is separately labelled.
- Production forms now start clean instead of exposing development/example birth data.
- Synastry now uses a true **bi-wheel**: one chart inside, one outside, same zodiac, inter-chart aspect lines through the center, and the inner person's houses. A swap button reverses the house-overlay perspective.
- Synastry, composite, and astrocartography interpretation prompts and corpus-only fallbacks are substantially expanded.
- Composite charts include symbolic midpoint house cusps only when both exact birth times are known; otherwise houses are omitted.
- Interpretation Markdown is rendered as safe React content instead of raw `<pre>` text.
- Astrocartography includes per-planet ASC/DSC/MC/IC guidance in the interface.
- Production attack surface and information disclosure are reduced.
- Security response headers, strict CORS, trusted-host checks, request-size checks, endpoint rate limiting, production-only route hiding, and server-side premium secrets are included.
- Core web dependencies are pinned to current 2026 FastAPI / Starlette / Uvicorn / Pydantic releases in `backend/requirements.txt`.

## Feature set

- Natal chart calculation with Swiss Ephemeris / PySwissEph
- Historical IANA timezone resolution
- Unknown-birth-time safeguards
- Placidus, Whole Sign, Koch, Regiomontanus, Campanus, Equal houses
- Aspects, houses, points, retrograde state and precise position tables
- Complete structured interpretation corpus
- Synastry bi-wheel, inter-aspects and two-way house overlays
- Zodiacal-midpoint composite chart
- Astrocartography ASC / DSC / MC / IC lines for Sun through Pluto
- City autocomplete and automatic timezone lookup
- Free PDF reports
- Protected Personalized and Deep Personal premium natal PDFs

## Local development — Windows PowerShell

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

Open a second terminal:

```powershell
cd frontend
npm ci
Set-Content .env.local "VITE_API_BASE_URL=http://127.0.0.1:8000"
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Validation status

- Backend regression suite: **32/32 PASS** in the release workspace.
- Python compile checks: PASS.
- Frontend TypeScript/TSX source syntax transpilation: **12/12 PASS**.
- Full `npm ci && npm run build` could not be completed in the packaging sandbox because external npm downloads were unavailable; run it locally and on Render before promotion from RC to production.
- See `CALCULATION_VALIDATION.md` for published-ephemeris and historical-timezone validation.

## Production and security

Read these before deploying:

- `DEPLOYMENT.md`
- `PRODUCTION_READINESS.md`
- `SECURITY.md`
- `RELATIONSHIP_METHODS.md`
- `PREMIUM_SETUP.md`

## Current production topology

- Public site: `https://astromyla.com`
- Render frontend: `astro-ai-site-frontend`
- Backend API: `https://astromyla.onrender.com`
- The custom domain belongs on the frontend service, not the backend service.

## Commercial licensing note

The numerical chart engine uses Swiss Ephemeris through `pyswisseph`. Review and satisfy Swiss Ephemeris AGPL / Professional License requirements before operating AstroMYLA as a proprietary paid service.

## Disclaimer

Astrological interpretations are symbolic/interpretive. They are not scientifically validated predictions and are not medical, legal, financial, or mental-health advice.

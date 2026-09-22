# AstroMYLA v1.6.0 Deployment

## Render architecture

AstroMYLA uses two Render services. Keep the website domain on the **frontend only**.

### Backend — `astroMYLA`

- Type: Web Service
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-server-header --limit-concurrency 100 --timeout-keep-alive 10
```

- Render URL: `https://astromyla.onrender.com`
- Custom domain: **none**

Production variables:

```text
ENVIRONMENT=production
OPENAI_API_KEY=<secret>
OPENAI_MODEL=<configured-model>
OPENAI_PREMIUM_MODEL=<optional-premium-model>
PREMIUM_REPORT_TOKEN=<long-random-server-secret>
RATE_LIMIT_PER_MINUTE=12
MAX_BODY_BYTES=1000000
ALLOWED_HOSTS=astromyla.onrender.com
EXPOSE_DEBUG_DATA=false
```

Optional explicit CORS override:

```text
CORS_ORIGINS=https://astromyla.com,https://www.astromyla.com,https://astro-ai-site-frontend.onrender.com
```

Do not create any `VITE_*` secret for the backend token.

### Frontend — `astro-ai-site-frontend`

- Type: Static Site
- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Publish directory: `dist`
- Custom domain: `astromyla.com`

Build-time variables:

```text
VITE_API_BASE_URL=https://astromyla.onrender.com
VITE_PAID_READING_PRICE=<display price, optional>
VITE_PAID_READING_URL=<https checkout link, optional>
VITE_DEEP_READING_PRICE=<display price, optional>
VITE_DEEP_READING_URL=<https checkout link, optional>
```

`render.yaml` contains the current security-header baseline.

## Squarespace DNS

Current working records:

```text
A       @       216.24.57.1
CNAME   www     astro-ai-site-frontend.onrender.com
```

Keep unrelated Domain Connect and mail-security records intact.

## Post-deploy smoke test

1. `https://astromyla.onrender.com/api/health` → `{ "ok": true }`.
2. `https://astromyla.onrender.com/openapi.json` → 404.
3. `POST https://astromyla.onrender.com/api/rebuild-index` → 404.
4. `https://astro-ai-site-frontend.onrender.com` loads.
5. `https://astromyla.com` loads with valid HTTPS.
6. Enter a known birth date using the visible **DD / MM / YYYY** fields and generate a natal chart.
7. Test Synastry; confirm one bi-wheel appears and **Swap inner chart** reverses house-overlay perspective.
8. Test Composite and Astrocartography.
9. Download a free PDF.
10. Confirm production JSON does not contain `retrieval` or `query`.
11. Confirm browser source/devtools contain no `OPENAI_API_KEY` or `PREMIUM_REPORT_TOKEN`.

## Dependency/build verification

Before deploying this RC, build from a fresh environment using the pinned `backend/requirements.txt` and `frontend/package-lock.json`. The packaging environment could not reach package registries, so the final clean dependency install must be verified locally/CI/Render.

## Git hygiene

Never commit:

- `.env`
- `.venv/`
- `node_modules/`
- `dist/`
- API keys or premium tokens

The package `.gitignore` is intended to keep generated/private files out of source control.

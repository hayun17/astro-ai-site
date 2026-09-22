# AstroMYLA v1.6.0 — Production Readiness Checklist

Status: **Release Candidate**. The application code is substantially production-hardened, but promotion should happen only after a clean local/CI install and real Render smoke test.

## 1. Clean build

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Expected: **32 tests PASS**.

Frontend:

```powershell
cd frontend
npm ci
npm run build
```

Expected: Vite build completes and `dist/` is generated.

## 2. Render backend

- Service: `astroMYLA`
- No custom domain.
- Root: `backend`
- Environment: `ENVIRONMENT=production`
- Set backend secrets only in Render.
- Verify `/api/health` returns only `{"ok":true}`.
- Verify `/openapi.json` and `/api/rebuild-index` return 404.

## 3. Render frontend

- Service: `astro-ai-site-frontend`
- Custom domain: `astromyla.com`
- `VITE_API_BASE_URL=https://astromyla.onrender.com`
- Add payment display/link variables only; never backend secrets.
- Verify Render response headers match `render.yaml`.

## 4. Functional acceptance

Test at least:
- Known-time natal chart with historical timezone.
- Unknown-time natal chart.
- Each house system.
- Synastry bi-wheel and Swap inner chart.
- Two-way synastry house overlays.
- Composite with two known times.
- Composite with one unknown time (houses omitted).
- Astrocartography with known time and unknown-time rejection.
- Free PDF download.
- Premium endpoint token rejection and one authorized test PDF.
- Mobile date/time/place input on iOS and Android-sized browsers.

## 5. Commercial launch blockers

Before accepting paid orders:
- Resolve Swiss Ephemeris commercial/AGPL licensing for the intended deployment model.
- Configure a real HTTPS checkout URL/provider.
- Define refund/fulfillment/privacy terms appropriate to your jurisdiction/business.
- If fulfillment becomes automated, verify payment-provider webhook signatures server-side before generating a paid report.

## 6. Operational hardening

Recommended before meaningful public traffic:
- Put the public site/API behind hosting/CDN protections appropriate to expected traffic.
- Add external uptime/error monitoring.
- Set a budget/usage alert for the LLM provider.
- Keep Render and payment-provider accounts protected with MFA.
- Rotate secrets periodically and after any suspected exposure.
- Keep a known-good release ZIP/tag for rollback.

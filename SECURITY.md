# AstroMYLA Security Notes — v1.6.0 RC

This release is hardened for a small public web application, but no application can be guaranteed invulnerable. Production security depends on the application **and** the hosting/CDN/payment stack around it.

## Implemented application controls

### Browser/frontend
- React escaping is retained; interpretations are rendered with React components rather than `dangerouslySetInnerHTML`.
- Production CSP restricts scripts to self, API connections to the AstroMYLA API and Open-Meteo geocoding, objects to none, and framing to none.
- `X-Content-Type-Options: nosniff`.
- `X-Frame-Options: DENY` plus CSP `frame-ancestors 'none'`.
- HSTS, referrer policy, Permissions-Policy and Cross-Origin-Opener-Policy.
- Long-lived immutable cache only for fingerprinted assets; HTML is `no-store/no-cache`.
- Checkout URLs must parse as HTTPS before they are rendered as links.

### API
- Exact production CORS origin allowlist; no wildcard production origin.
- Trusted Host middleware.
- Production OpenAPI / Swagger / ReDoc disabled.
- Development-only corpus rebuild route is not registered in production.
- Production health response is deliberately minimal.
- Pydantic models forbid unknown top-level fields and constrain dates, coordinates, offset values, strings and premium questions.
- Request Content-Length limit is enforced before endpoint processing.
- Lightweight per-client/per-endpoint rate limiting is present.
- Uvicorn production command includes concurrency and keep-alive limits and disables the server banner.
- API responses use `Cache-Control: no-store`.

### LLM/RAG boundary
- The model receives a whitelisted chart-data structure rather than names/place labels and operational metadata.
- User-controlled free-text premium questions are length-limited.
- Prompts explicitly label chart JSON as trusted data, not instructions.
- Production responses do not expose retrieval chunks or internal RAG query strings.

### Premium fulfillment
- `PREMIUM_REPORT_TOKEN` is server-side only.
- Public `/api/report/pdf` rejects premium tiers.
- Paid-report generation endpoint requires the server secret in production.
- Never create `VITE_PREMIUM_REPORT_TOKEN` or place the token in browser code.

## Dependency baseline

The RC pins modern 2026 FastAPI / Starlette / Uvicorn / Pydantic versions. Keep them updated and review security advisories before each deployment. Do not blindly run automated major-version fixes directly against production; build and run the regression suite first.

## What this does not replace

- A CDN/WAF/edge-rate-limit layer for serious volumetric DDoS protection.
- Payment-provider webhook signature verification once automatic paid fulfillment is implemented.
- Secret rotation and access-control procedures in the Render account.
- Monitoring/alerting for traffic spikes, repeated 4xx/5xx responses or unexpected premium requests.
- Backups/version control and a tested rollback process.
- A professional penetration test for a high-revenue or high-risk deployment.

## Production secret rules

- Store `OPENAI_API_KEY` and `PREMIUM_REPORT_TOKEN` only as backend secrets in Render.
- Do not commit `.env` files.
- Do not put secrets in any variable beginning with `VITE_`; Vite variables are browser-visible.
- Use a long random premium token and rotate it after suspected exposure.
- If automated payments are added, validate payment-provider webhook signatures before generating/delivering any paid report.

## Pre-release security check

1. `ENVIRONMENT=production` on backend.
2. `/openapi.json` → 404.
3. `/api/rebuild-index` → 404.
4. `/api/health` → only `{ "ok": true }`.
5. Premium endpoint without valid token → 403 (after token configured).
6. Public PDF endpoint with `tier=deep` → 403.
7. Browser devtools contain no server secrets.
8. Verify CSP/security headers on `astromyla.com` and API responses.
9. Run backend regression tests and frontend production build from a clean install.
10. Review dependency advisories and payment configuration before launch.

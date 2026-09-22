# Changelog

## v1.7.0 — Product Polish & Monetization RC

- Fixed mobile birth-form checkbox inflation and narrow-column layout.
- Added Synastry Connection Profile with six transparent theme dimensions.
- Added Tight / Standard / Wide relationship orb presets.
- Added Composite Relationship Identity keywords and strongest signature.
- Added astrocartography 1–5 theme emphasis guide.
- Added staged calculation progress UI.
- Added secure iyzico hosted checkout foundation with server-side prices and verified callback retrieval.
- Added PostgreSQL-backed production order persistence and paid-report unlock flow.
- Added four new regression tests; backend total 36/36 PASS.

## v1.6.0 — Production Release Candidate

### Birth-data UX
- Replaced ambiguous browser date presentation with explicit **DD / MM / YYYY** segmented entry.
- Day, month, and year each have visible labels; month uses named options.
- Time is explicitly marked **24-hour**.
- Production forms now start empty rather than shipping sample names, dates, or birthplaces.
- Added front-end validation for missing/invalid date, time, coordinates, and timezone/offset.

### Synastry
- Replaced side-by-side natal-wheel presentation with a real **bi-wheel**.
- Both charts share one zodiac; one sits inside and one outside.
- Cross-chart aspects are drawn through the center.
- Inner chart houses are shown for house overlays.
- Added **Swap inner chart** to inspect overlays in the opposite direction.
- Expanded fallback and model-guided interpretation: emotional safety, communication, attraction, commitment, pressure, outer-planet dynamics, two-way overlays, repeated themes, and practical reflection.

### Composite
- Retained shortest-arc zodiacal midpoint planets.
- When both exact birth times are known, corresponding natal angles and cusps are midpointed into explicitly **symbolic** composite houses.
- If either birth time is unknown, composite houses/angles are omitted instead of guessed.
- Expanded corpus-only fallback to ten structured sections including core identity, emotional climate, communication, love/drive, growth/commitment, outer-planet themes, house concentrations, aspects, contradictions, and synastry integration.

### Astrocartography
- Expanded interpretation for ASC / DSC / MC / IC meaning and every major planet Sun through Pluto.
- Added selected-planet guidance beneath the interactive map.
- Retains explicit scope limits: no invented parans, Local Space, relocated houses, or promised events.

### Interpretation presentation
- Added safe React Markdown-like rendering for headings, lists, paragraphs and bold text.
- No `dangerouslySetInnerHTML` or raw HTML injection path is used.

### Production hardening
- Production Swagger / ReDoc / OpenAPI routes disabled.
- `/api/rebuild-index` now exists only in development and is absent from production routing.
- Production root/health responses no longer disclose service version metadata.
- Strict CORS allowlist and restricted request headers.
- Trusted Host middleware in production.
- Request `Content-Length` cap and per-endpoint in-memory rate limit.
- Security headers on API and static frontend: CSP, `nosniff`, frame denial, referrer policy, permissions policy, HSTS; frontend additionally uses COOP.
- LLM prompts receive a chart whitelist rather than user-controlled labels/operational metadata.
- RAG retrieval/query debugging is exposed only when **both** development mode and the explicit debug flag are enabled.
- Removed unused production admin token / rebuild surface.
- Premium secret remains server-side and is never a `VITE_*` variable.
- Uvicorn production command disables the server banner and caps concurrency/keep-alive.
- Rate-limit route key uses the ASGI scope path rather than constructing a URL from request headers.

### Dependency baseline
- `fastapi==0.141.1`
- `starlette==1.6.0`
- `uvicorn[standard]==0.53.0`
- `pydantic==2.13.4`
- `vite==6.4.3` (existing frontend baseline)

### Verification
- Backend regression suite: **32/32 PASS**.
- TypeScript/TSX source syntax transpilation: **12/12 PASS**.
- A clean dependency install could not be performed inside the packaging sandbox because outbound package downloads were unavailable. Run `pip install -r requirements.txt`, `npm ci`, and `npm run build` locally/CI before production promotion.
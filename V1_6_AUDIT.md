# AstroMYLA v1.6.0 Production RC — Technical Audit

## Scope

This audit covers the application state after the v1.6 birth-input, relationship-chart, interpretation, and security work.

## Calculation integrity retained

- Swiss Ephemeris / PySwissEph remains the numerical planetary engine.
- Published ephemeris regression checks remain in the suite.
- Historical IANA timezone tests remain in the suite.
- House-system selection is tested.
- Unknown-time mode omits houses/angles and time-sensitive Moon aspects instead of inventing them.
- Astrocartography requires a known birth time.

See `CALCULATION_VALIDATION.md`.

## UX findings resolved

- Browser-native date ambiguity removed; the visible order is **Day / Month / Year**.
- Sample development identity/date/place values removed from the production form state.
- Mobile-friendly segmented date entry and native time control retained.
- City autocomplete/timezone flow retained.
- Interpretation text now renders as readable sections rather than raw Markdown characters.

## Relationship-method findings resolved

### Synastry
Previous side-by-side natal wheels did not communicate the standard comparison geometry well. v1.6 introduces a shared-zodiac bi-wheel with inner/outer rings, inter-chart aspects and directional house overlays. The inner chart can be swapped.

### Composite
Composite planets remain shortest-arc zodiacal midpoints. Symbolic midpoint houses are included only when both exact birth times are known and are labelled as symbolic rather than as a fabricated event chart.

### Interpretation
Synastry, composite and astrocartography now have expanded deterministic fallbacks as well as stricter, richer LLM writing briefs. A missing LLM key therefore does not reduce these tools to one-paragraph output.

## Security findings resolved

- Production API documentation endpoints disabled.
- Development rebuild endpoint removed from production route table.
- Minimal production health/root response.
- Strict production CORS.
- Trusted-host middleware.
- Security response headers.
- Request size check.
- Endpoint rate limiting.
- Server concurrency/keep-alive limits in Render command.
- No React raw-HTML interpretation rendering.
- Model facts are whitelisted before LLM use.
- Internal RAG query/retrieval output unavailable in production.
- Premium generator protected by server-side token; public PDF path cannot request premium tiers.
- Unused admin token surface removed.
- Core web stack pins raised to current 2026 release baseline.

## Verification

- Backend tests: **32/32 PASS**.
- Python compile: PASS.
- TS/TSX source syntax transpilation: **12/12 PASS**.
- Full clean npm/pip dependency installation was not possible in the packaging sandbox because package-registry network access was unavailable. This remains a release-candidate gate to run locally/CI/Render.

## Remaining launch gates

1. Clean `pip install` and backend regression test using the pinned v1.6 requirements.
2. Clean `npm ci && npm run build`.
3. Real Render smoke test and security-header check.
4. Payment-provider configuration and, if automated, signed webhook verification.
5. Swiss Ephemeris commercial/AGPL licensing decision before paid proprietary operation.
6. Optional CDN/WAF/edge-rate-limit layer for meaningful public traffic or DDoS resilience.

# AstroMYLA v1.5.0 Premium Report Audit

## Scope

This release changes the commercial report layer without changing the core Swiss Ephemeris planetary calculations introduced/verified in v1.4.0.

## Premium writing engine

- Added separate long-form prompts for Personalized and Deep Personal readings.
- All astronomical facts are still constrained to the supplied computed chart JSON.
- Premium text is instructed to synthesize repeating chart themes instead of listing placements independently.
- Deep reports support up to three customer questions.
- Unknown birth time restrictions are carried into the premium prompt.
- Paid generation uses a strict LLM call and raises an error when the premium model is unavailable instead of silently serving a shorter free fallback.

## Premium PDF

- Added a vector natal chart wheel on page 1.
- The cover plots the ten major planets for legibility; Node/Lilith/Chiron remain in the detailed table and interpretation.
- Added reader/birth metadata to the cover when available.
- Added Sun/Moon/Rising summary strip.
- Added editorial color palette, serif long-form text, refined spacing and page decorations.
- Deep-report questions are printed near the beginning when provided.
- Disclaimer is moved to the page footer so it does not interrupt the reading.

## Commercial security

- Added protected `POST /api/premium/natal-report`.
- Production requires `PREMIUM_REPORT_TOKEN` in `X-Premium-Token`.
- Public `/api/report/pdf` rejects non-free tiers.
- The static frontend never receives the premium token.

## Verification

- `python -m py_compile app/*.py tests/*.py`: PASS
- Backend unit/regression suite: **26/26 PASS**
- TypeScript/TSX syntax transpilation: **10/10 PASS**
- Premium sample PDF: generated and opened successfully
- PDF preflight: 11 pages, unencrypted, openable, not scanned
- PDF render inspection: cover, body page and ending page visually checked; no clipping/black boxes observed

## Build limitation

A full frontend `npm ci && npm run build` could not be completed inside the audit container because npm dependency installation timed out. The modified TypeScript/TSX sources pass syntax transpilation. Render will install the package-lock dependencies on deployment as usual.

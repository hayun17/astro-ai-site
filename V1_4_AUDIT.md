# AstroMYLA v1.4.0 — Verification & Monetization Audit

## Numerical calculation status

- Backend regression suite: **24/24 PASS**.
- Added a published-ephemeris reference test for Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune and Pluto.
- Reference date: **25 Jan 2002, 00:00 UT**.
- Maximum deviation from the reference values (which are rounded to the nearest arcminute): **< 0.8 arcminute**.
- Historical timezone regression verifies `Europe/Istanbul` as UTC+2 in Jan 2002, UTC+3 in Jul 2002, and UTC+3 year-round after the 2016 change.
- The old manually-entered UTC+3 example for 25 Jan 2002 produced the wrong time-sensitive angles; the IANA-timezone path corrects this.
- Unknown-time mode still suppresses houses, angles, Fortune and Moon aspects rather than inventing them.
- Chiron remains unavailable when the required asteroid ephemeris file is absent.
- `Lilith` is Mean Black Moon / mean lunar apogee.

## Frontend status

- Added a precise-position table showing sign + degree/minute + house + direct/retrograde.
- Added Paid Reading and Deep, Personal Reading cards.
- Checkout links are provider-agnostic HTTPS links configured via `VITE_*` environment variables.
- No payment API keys or secrets are placed in browser code.
- TypeScript/TSX syntax transpilation check: PASS for all modified/critical frontend modules.
- A full Vite production bundle could not be completed in the sandbox because package installation timed out; local/Render `npm ci && npm run build` remains the final bundle check.

## Commercial launch blocker to address

The backend uses Swiss Ephemeris via `pyswisseph`. Before monetizing a proprietary public service, review Swiss Ephemeris' AGPL vs Professional License requirements. This is separate from the payment provider.

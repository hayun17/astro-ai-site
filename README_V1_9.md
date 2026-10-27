# AstroMYLA v1.9.0 — Signature Insights

This release keeps everything from v1.8 (Current Transits, Natal + Transit bi-wheel, Daily Personal Astrology, My AstroMYLA accounts, Saved Birth Charts, directional Synastry house overlays) and adds AstroMYLA-native synthesis features.

## New AstroMYLA signature features

- **Your AstroMYLA Signature** — a short chart archetype plus core energy, needs, and watch-outs.
- **Ideal Partner Blueprint** — relationship qualities inferred from Moon, Venus, Mars, Saturn and, when birth time is known, the 7th house and its ruler.
- **Who You Attract vs Who You Actually Need** — deliberately separates chemistry indicators from emotional/long-term support indicators.
- **Your Emotional Manual** — what tends to help, what needs care, repair style and reassurance style.
- **Myla Match** — a synastry synthesis built from tight inter-chart aspects plus directional house activation.

These modules are deterministic syntheses of already calculated chart data. They do not invent a destined partner, a guaranteed compatibility outcome, or missing houses when birth time is unknown.

## Existing v1.8 platform features retained

- Current transits
- Natal + Transit bi-wheel
- Daily personal astrology
- User accounts
- Saved birth charts
- Saved charts usable as Person A / Person B
- Two-way Synastry house overlays and activated-house summaries
- Composite chart
- Astrocartography
- PDF reports
- Premium payment/report foundation

## Validation

- Backend regression suite: **44/44 PASS**
- Python compile: PASS
- Frontend TS/TSX syntax transpilation: **17 files / 0 syntax errors**
- Full local Vite build was not completed in the packaging environment because `npm ci` timed out; the safe deploy script runs `npm ci` and `npm run build` before any production push.

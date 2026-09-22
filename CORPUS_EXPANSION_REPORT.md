# AstroMYLA v1.2.0 — Corpus Expansion Report

## What was added

The previously incomplete local RAG corpus is now complete for every sign-based element currently supported by the backend.

| Corpus family | Coverage |
|---|---:|
| Placements | 13 bodies × 12 signs = 156/156 |
| Points / angles | 6 points × 12 signs = 72/72 |
| House cusps | 12 houses × 12 signs = 144/144 |
| Structured interpretation texts | 372/372 |

New material fills Jupiter, Saturn, Uranus, Neptune, Pluto, True Node, Lilith, ASC, MC, DSC, IC, Vertex, Part of Fortune, House 1 in Taurus, and Houses 2–12 across every sign.

## Voice

The new text is intentionally warm and conversational rather than textbook-like. It uses second-person language, describes recognizable day-to-day patterns, includes a shadow/stress edge and a growth direction, and avoids framing astrology as scientific certainty or guaranteed destiny.

The original user-supplied corpus files that were already present were preserved. This means the newly added corpus follows the warmer voice consistently, while older supplied passages remain unchanged unless they were missing.

## Retrieval / indexing

- `backend/data/index.json` was rebuilt from the corpus source of truth.
- Final index: **378 chunks**.
- Exact-tag retrieval coverage: **0 missing structured combinations**.
- House metadata retains numeric identifiers such as `HOUSE_1` through `HOUSE_12`.

## Verification

- Backend regression tests: **10/10 PASS**.
- New coverage tests verify all supported placements, points, and house/sign combinations.
- Python compile check: **PASS**.
- Corpus-only API smoke test: **PASS**, including outer planets, points, and house interpretations.

## Important note

Complete interpretation text does not mean every astronomical body is always calculable. Chiron still depends on the required Swiss Ephemeris asteroid files. If its astronomical position is unavailable, AstroMYLA correctly skips its interpretation instead of inventing one.

# AstroMYLA v1.4.0 — Calculation Validation

## What was checked

AstroMYLA's numerical chart engine uses `pyswisseph==2.10.03.2` (Swiss Ephemeris bindings) for tropical geocentric longitudes, speeds, houses and angles. This release adds fixed regression tests against a published planetary ephemeris and historical-timezone regression cases.

### External planetary reference — 25 Jan 2002, 00:00 UT

Published reference values are given to the nearest arcminute. AstroMYLA's results are shown below as degree-within-sign values. The largest difference is under **0.8 arcminute**, which is inside the precision of the published reference table.

| Body | Published | AstroMYLA | Difference |
|---|---:|---:|---:|
| Sun | Aquarius 4°50′ | Aquarius 4°49.83′ | 0.17′ |
| Moon | Gemini 12°50′ | Gemini 12°50.79′ | 0.79′ |
| Mercury | Aquarius 10°59′ | Aquarius 10°58.65′ | 0.35′ |
| Venus | Aquarius 7°21′ | Aquarius 7°20.82′ | 0.18′ |
| Mars | Aries 4°24′ | Aries 4°24.06′ | 0.06′ |
| Jupiter | Cancer 7°39′ | Cancer 7°38.69′ | 0.31′ |
| Saturn | Gemini 8°13′ | Gemini 8°13.01′ | 0.01′ |
| Uranus | Aquarius 23°42′ | Aquarius 23°41.63′ | 0.37′ |
| Neptune | Aquarius 8°20′ | Aquarius 8°19.52′ | 0.48′ |
| Pluto | Sagittarius 16°49′ | Sagittarius 16°48.90′ | 0.10′ |

The comparison source is a public daily ephemeris rounded to the nearest minute of arc; the application's internal calculations retain substantially more precision.

## Historical timezone regression

A major source of wrong Ascendants/houses is not the ephemeris itself but applying today's UTC offset to an old birth date. AstroMYLA now prefers an IANA timezone (for example `Europe/Istanbul`) and resolves the historical offset on the actual birth date.

Reference case used throughout this project:

- Merzifon, Türkiye
- 25 Jan 2002, 09:30 local
- `Europe/Istanbul`
- historical offset resolved by the app: **UTC+2**, not modern UTC+3
- Placidus Ascendant: **Aries 4°11′** approximately

This is intentionally different from the older manually-entered `UTC+3` test, which produced Pisces 8°20′. The old result was a timezone-input error, not a planetary-ephemeris error.

## Other safeguards

- Gregorian calendar validation via Pydantic/date.
- House-system selection is passed through to Swiss Ephemeris.
- Unknown birth time does not fabricate houses, angles, Part of Fortune, or Moon aspects.
- Retrograde state comes from ecliptic longitude speed, not a hand-written date table.
- Chiron is marked unavailable if its required asteroid ephemeris file is missing; no synthetic longitude is generated.
- `Lilith` currently means **Mean Black Moon / mean lunar apogee** (`swe.MEAN_APOG`).

## Scope

The numerical checks validate the astronomical coordinate calculations used by the astrology application. Astrological interpretations themselves are symbolic/interpretive claims, not scientifically validated predictions.

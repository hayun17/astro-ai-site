# AstroMYLA v1.3.0 - Astro Suite Notes

This release expands AstroMYLA from a natal-only product into a multi-tool astrology application.

## Tools now available

### 1. Birth Chart

Preserves the existing Swiss Ephemeris natal calculation, warm corpus/RAG interpretation, unknown-time safeguards, house-system selection, historical timezone resolution and chart visualization.

### 2. Synastry

- Calculates cross-chart conjunction, opposition, trine, square and sextile aspects.
- Uses relationship-specific orbs rather than simply reusing the natal table verbatim.
- Includes planets, supported extras and angles when those angles are valid.
- Calculates partner-planet house overlays in both directions when the receiving chart has a known birth time.
- If one person's time is unknown, that person's time-sensitive Moon contacts and angles are intentionally omitted instead of guessed.
- Interpretation avoids a reductive compatibility percentage/score.

### 3. Composite Chart

- Calculates shortest-arc zodiacal midpoints for corresponding natal positions.
- Calculates major aspects inside the composite positions.
- Does **not** invent composite houses from two separate birth events. The UI explicitly labels the method as a zodiacal-midpoint symbolic chart.

### 4. Astrocartography

- Requires a known birth time.
- Calculates geocentric ASC/DSC rising-setting curves and MC/IC meridians for Sun through Pluto.
- Interactive map lets the user choose a planet and toggle ASC, DSC, MC and IC lines.
- Birthplace is marked on the map.
- Current scope intentionally excludes parans, local-space azimuth lines and full relocated-house calculations. These are not silently fabricated.

## PDF reports

Every generated tool result has a **Download PDF report** button.

The PDF is generated on the FastAPI backend using ReportLab and includes:

- report title and disclaimer,
- calculation summary appropriate to the selected tool,
- interpretation text,
- page numbers and AstroMYLA branding.

PDF generation uses the already-computed public result payload so the report does not silently recalculate the chart with different settings.

## New backend endpoints

```text
POST /api/chart/synastry
POST /api/interpret/synastry
POST /api/chart/composite
POST /api/interpret/composite
POST /api/chart/astrocartography
POST /api/interpret/astrocartography
POST /api/report/pdf
```

Existing natal endpoints remain unchanged.

## Accuracy boundaries

- Astrology output is presented as symbolic/interpretive rather than scientific certainty.
- Unknown birth time is still handled conservatively.
- Astrocartography line calculations are angular line calculations, not a claim that a city is objectively "good" or "bad".
- Composite houses are intentionally absent because this release uses zodiacal midpoints, not a separately calculated event chart.

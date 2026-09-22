# AstroMYLA v1.2.2 — Smart Birth Input

## Birthplace autocomplete

The birthplace field now searches while the user types (350 ms debounce, 2-character minimum) and shows up to six suggestions. Selecting a suggestion stores:

- display name
- latitude / longitude
- IANA timezone (for example `Europe/Istanbul`)

The frontend uses Open-Meteo Geocoding, whose location dataset is based on GeoNames. Attribution is displayed directly below the field. If no suggestion is selected, submitting the form performs a one-result lookup. Manual coordinates remain available in Advanced.

## Historical timezone handling

When an IANA timezone is available, the backend resolves the UTC offset for the actual birth date/time with Python `zoneinfo`. This avoids treating today's UTC offset as if it necessarily applied historically. Manual `tz_offset_hours` remains the fallback for manual coordinates or unresolved places.

## Unknown birth time

The new “I don’t know my birth time” option is intentionally conservative. AstroMYLA:

- uses 12:00 local time only as a date reference for approximate planetary positions;
- does not calculate houses or house placements;
- does not calculate Ascendant, Descendant, MC, IC, Vertex, or Part of Fortune;
- excludes Moon aspects because they can change materially across the day;
- checks the start and end of the date and marks a body's sign uncertain if it crosses a sign boundary;
- prevents uncertain signs from being fed into exact-match RAG interpretation;
- tells the user clearly that these items were skipped rather than guessed.

## Verification

- Python compile: PASS
- Backend unit/regression suite: 14/14 PASS
- Unknown-time API smoke test: PASS
- TypeScript/TSX syntax transpilation for all frontend source files: PASS

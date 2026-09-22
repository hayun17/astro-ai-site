# AstroMYLA v1.2.1 — Mobile Birth Data UX

This patch focuses on phone/tablet birth-data entry without changing chart calculations or backend interpretation logic.

Changes:
- Mobile form controls are at least 50 px high for easier tapping.
- Form controls use 16 px text on phones to prevent iOS Safari focus-zoom.
- Date and time use native mobile pickers and remain compact side-by-side on normal phone widths.
- UTC offset gets its own full-width row and a mobile numeric keyboard hint.
- Birthplace input is optimized for mobile typing and no longer invites browser autofill noise.
- Selects use the phone's native picker UI on small screens.
- Generate button becomes full-width on mobile.
- Advanced section gets a larger touch target.
- Page/card spacing is reduced on mobile and fixed backgrounds are disabled for smoother scrolling.
- Added a short UTC/date-time helper note.

No backend, astrology calculation, RAG corpus, or interpretation behavior was changed.

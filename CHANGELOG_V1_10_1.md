# AstroMYLA v1.10.1 · Transit Stories

## What changed
- Made the personal transit explanation the **first result**, above the natal/transit bi-wheel and technical aspect tables.
- Added a styled, responsive **Your Personal Sky** reading with a prominent main theme, top calculated aspect, close-up paragraphs, reflection question, and expandable other active transit stories.
- Added natal-house-based themes (when a reliable birth time is present), with realistic daily-life examples.
- Added richer **non-AI fallback prose** anchored in the actual transiting planet, natal target, aspect type, calculated orb and six-hour approaching/separating direction. This does not require an OpenAI API key or a user database.
- Moved technical lists and wheel into an optional details panel to improve readability and focus.
- Full-length commentary still available under **Read the detailed written transit notes**.
- Unknown-time safeguards preserved: no invented natal house placements, Asc/MC contacts or time-sensitive natal Moon transits.
- No changes to accounts, saved charts, payment provider, or authentication.

## Verification
- Backend: 64/64 unit and integration tests PASS (includes 5 new transit interpretation tests).
- Python compileall PASS.
- Frontend: TypeScript syntax transpilation 19 files, 0 errors.
- Full npm ci / Vite build could not be performed in this offline environment; deployment script **requires** both steps to pass on the local computer before pushing.
- No claims of live deployment or production verification until the user deploys it and Render shows Live.

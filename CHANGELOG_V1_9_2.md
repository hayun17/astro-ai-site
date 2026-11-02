# AstroMYLA v1.9.2 — Human Touch / Real Saved Charts

Based on production v1.9.1 Brand Icon. All previous natal, transit, composite, astrocartography, signature and payment foundation features retained.

## Main upgrades

- **Save after generating:** visible "Save this chart" actions on the result screen, including Person A and Person B in relationship modes.
- **Sign in or sign up, then name your chart:** the pending chart survives the sign-in modal flow, and is written to the account database only after the user confirms the label.
- **Real, reopenable natal snapshots:** the backend recalculates and persists the natal planets, houses, aspects and Signature information alongside birth input. Previously saved v1.8/v1.9 records remain available after a non-destructive database migration. A saved chart can be reopened immediately; regenerate to get a fresh long-form reading. The app waits for the backend's successful save response before confirming success; session network errors do not silently log users out.
- **Directional synastry story engine:** actual person A planets in person B houses, and the reverse, with multi-planet clusters prioritized. House 3 examples name the *actual* Moon/Mercury/Venus only if calculated.
- **Conversational interpretations:** both prompts and deterministic fallback are less academic and make the house patterns concrete. Interpretations remain symbolic, not predictions or diagnoses.
- **Redesigned AstroMYLA Signature cards:** editorial signature hero, profile rows, an interactive Attract vs Thrive switch, an emotional note and compact Myla Match cards. Reduced repetition and mobile clutter.
- **Transparent account readiness:** if PostgreSQL isn't connected, saving is visibly unavailable instead of falsely saying the chart was saved.

## Important configuration

`DATABASE_URL` must be set on Render's **astroMYLA backend web service** to a persistent Render PostgreSQL database, or accounts and saved charts will NOT work. `/api/account/config` should return `{"ready":true}`. No paid checkout configuration is required for free chart saving.

There is no email verification, password recovery email, or data-export tool yet. Treat these as required work before mature public account rollout.

## Tests

New deterministic house grouping, missing-house, API response, database migration, trusted natal snapshot and cross-account persistence tests. The actual Windows deploy script will run the complete backend regression suite and `npm ci` + `npm run build` before pushing.

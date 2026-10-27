# AstroMYLA v1.8.0 — Current Sky + Accounts

## New
- Current Transits tool calculated from Swiss Ephemeris.
- Natal + transit bi-wheel: natal houses/planets inside, transiting sky outside.
- Daily Personal Astrology interpretation built only from calculated transit facts.
- Transit-to-natal aspects include orb, applying/separating estimate and importance ranking.
- Transiting planets are placed into natal houses when the birth time is known.
- My AstroMYLA account: register, sign in/out and 14-day sessions.
- Saved Birth Charts stored server-side; saved charts can be loaded as Person A or Person B for relationship tools.
- Passwords use scrypt with unique salts; raw session tokens are not stored in the database.
- Synastry house overlays upgraded into a first-class interpretation layer in both directions.
- Synastry result now shows the most activated partner houses and a theme for every planet → partner-house overlay.
- Transit PDF support added.

## Preserved from v1.7
- Natal, Synastry, Composite and Astrocartography.
- Synastry Connection Profile and relationship signatures.
- Premium PDF / iyzico checkout foundation.
- Mobile birth input fixes and progress UI.

## Important deployment dependency
My AstroMYLA accounts and saved charts require `DATABASE_URL` in the backend Render service. The same PostgreSQL database can also be used by the payment/order system.

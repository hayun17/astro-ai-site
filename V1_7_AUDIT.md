# AstroMYLA v1.7.0 — Product Polish & Monetization Audit

## Scope

This release focuses on product quality rather than adding dozens of new astrology calculators at once. It improves mobile usability, relationship-result clarity, composite/astrocartography result summaries, calculation progress feedback, configurable relationship orbs, and a secure iyzico hosted-checkout foundation.

## Mobile fixes

- Birth date and time no longer compete for half-width columns on phones.
- The `I don't know my birth time` checkbox is explicitly reset to 20×20 px so global mobile input rules cannot inflate it.
- The unknown-time label stays horizontal and readable.
- Day / month / year remain explicit and compact while keeping 16 px text to avoid iOS focus zoom.
- House system, timezone, manual coordinate controls and relationship forms collapse to one column on narrow screens.
- General mobile padding and control heights were reduced without sacrificing touch targets.

## Relationship results

### Synastry Connection Profile

The result now includes six deterministic theme dimensions:

- Emotional Resonance
- Communication
- Chemistry & Attraction
- Stability & Commitment
- Growth & Transformation
- Friction / Activation

This is **not** a relationship-success probability. The algorithm weights:

- planet/point relevance to each theme;
- aspect type;
- orb closeness;
- available partner-house overlays.

Hard aspects increase the friction/activation dimension instead of being treated as simply “bad”.

### Relationship signature

The strongest measured dimensions generate short descriptors such as `Magnetic`, `Mentally Connected`, `Grounding`, or `High-Voltage` plus a deterministic short summary.

### Orb profiles

Synastry now supports:

- Tight — 70% of standard orb limits
- Standard — existing limits
- Wide — 125% of standard limits

## Composite result summary

Composite charts now return a `signature` with:

- 2–4 descriptive keywords;
- a relationship-identity headline;
- the tightest composite major aspect;
- a method note explaining that this is descriptive and not an outcome score.

## Astrocartography UX

Selected planetary lines now include a lightweight 1–5 emphasis guide for Career, Love, Home, Creativity and Intensity, alongside the existing ASC/DSC/MC/IC explanations. These ratings are interpretive UI guidance, not geographic probabilities or promises.

## Calculation progress

The UI now exposes the actual client workflow stages instead of leaving users with a generic `Calculating…` state:

1. validate birth data;
2. resolve place / historical timezone;
3. calculate planetary positions;
4. build houses/aspects or relationship/map geometry;
5. finish interpretation;
6. mark complete only when the API response actually arrives.

The percentage advances conservatively and stops below 100 until the request finishes.

## Payment foundation

A secure hosted iyzico flow is included:

- frontend never receives the iyzico API key or secret;
- prices are server-configured and cannot be changed through browser devtools;
- checkout initializes server-side;
- card details are entered on iyzico's hosted page;
- callback token is re-queried server-side before the order is marked paid;
- returned amount, currency and basket/order identifiers are checked before fulfillment;
- public order tokens are random and separate from internal order IDs;
- paid premium PDFs are unlocked only after verified payment.

Production order persistence requires PostgreSQL through `DATABASE_URL`. SQLite is allowed only in development.

## Verification

- Existing backend regression suite preserved.
- New tests cover Connection Profile structure, tight/wide orb monotonicity, Composite Signature, and payment-config secret non-disclosure.
- Backend test result: **36/36 PASS**.
- Python compile: PASS.
- Full Vite production build could not be completed in the sandbox because `npm ci` timed out before installing Vite. The source package is intended to run `npm ci && npm run build` during local/Render validation before deployment.

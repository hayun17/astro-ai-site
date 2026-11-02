# AstroMYLA v1.10.0 — What changed and what is actually verified

## User experience
- Removed long, repetitive Signature reports from the default results view; replaced with one interactive **The AstroMYLA Edit** featuring Big Three, love language, romantic type, attraction-versus-needs, and emotional communication. Everything links back to actual chart facts.
- Made directional synastry overlays a single interactive panel: A → B / B → A; strongest real house concentrations first, named planets and house-specific prose; expand to other active houses.
- Reduced distracting commercial/provider/infrastructure copy in customer-facing Premium Readings.

## My AstroMYLA
- After clicking **Save this chart**, a successful save now requires the POST to return an ID, GET-by-ID to return the persisted chart + server-calculated natal snapshot, and account-list GET to contain the ID. No optimistic "Saved" banner.
- Reopen saved charts from the backend, rename charts and delete charts, and keep user isolation checks. A PostgreSQL DATABASE_URL must be connected in Render for actual persistence.
- `/api/account/config` checks a database query, not only whether the environment variable is present.

## Payment correctness and hardening
- A browser `?payment=success` string is **not proof of payment**. The frontend now asks backend `/api/orders/{token}` before showing verified success.
- Webhook endpoint accepts only signature-V3-verified iyzico Checkout Form notifications and independently retrieves the provider's checkout transaction.
- Provider verification checks `status`, `paymentStatus`, `conversationId`, `basketId`, `token`, `currency`, both prices and `paymentId`. Checkout retrieval requires a provider signature.
- Idempotent `mark_paid`: webhook/callback retries cannot revoke a paid order or send duplicate purchase emails from already-paid transitions.
- Payments default **OFF**; live mode requires explicit approval and valid API URL, database, report-generation API key, server-side prices and SMTP receipt settings. A merchant must still supply credentials, go through onboarding and perform real end-to-end sandbox/live tests.
- A best-effort transactional receipt sends a private report-download link after first confirmed payment. A customer should not be charged until merchant, receipt and report fulfillment are fully tested.

## Validation
- 59 backend unit and integration tests passed locally, including current Mercury retrograde / Saturn return snapshots, account persistence, cross-account isolation, chart rename, payment amount fraud, signed webhook and idempotent callback.
- Python modules compile.
- 18 TS/TSX files pass syntax transpilation via TypeScript 5.8.3.
- **The full production Vite build was not run here:** npm registry packages are not fully cached and this sandbox cannot fetch them. `DEPLOY_ASTROMYLA_V1_10.ps1` requires a clean `npm ci` + `npm run build` on your PC, and will NOT push if either fails.
- No live merchant keys, Render Postgres, working SMTP or actual card transactions were available to verify here. Do not call checkout 'live' until the external steps are completed.

## Unresolved before public commercial launch
- Confirm iyzico merchant approval; correct sandbox/live credentials and account settings; execute sandbox card, failed payment, 3DS, webhook callback and real low-value pilot/refund tests.
- Configure a persistent Render Postgres, transactional email, and actual AI-report generation capacity.
- Verify Swiss Ephemeris use complies with the applicable AGPL/professional licensing terms.
- Publish owner-approved terms, privacy/KVKK notices, product delivery/refund information and support channel, and confirm tax obligations with an accountant.
- Email verification/password reset and a dedicated payment/order admin dashboard are **not** included. Do not characterize the system as fully production-ready for general paid customers without these decisions.

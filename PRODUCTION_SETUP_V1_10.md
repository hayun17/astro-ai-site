# AstroMYLA v1.10 · Production setup (read before any charge)

**Security rule:** never paste merchant API keys, OpenAI keys, SMTP password, or DATABASE_URL into chat or GitHub. Place them only in the Render *backend* Environment page.

## A. Persist My AstroMYLA chart library
1. Render dashboard → New → Postgres → create a database in the same region as `astroMYLA` backend.
2. Copy the **Internal Database URL** to `astroMYLA` web service → Environment → `DATABASE_URL`. This must be PostgreSQL and persistent. Save and redeploy.
3. Confirm `https://astromyla.onrender.com/api/account/config` returns `{ "ready": true }`.
4. Test from two browsers: create account → generate natal chart → Save → name it → sign out → sign in → reopen chart; second account cannot view it.
5. **No database means no reliable saved chart**. Do not pretend local browser state equals cloud storage.

## B. Keep real charges disabled until checkout and fulfillment are tested
`PAYMENTS_ENABLED=false` until all stages of activation pass. Pricing is determined by the server; never from the frontend.

Required in Render backend before LIVE:

```
DATABASE_URL=<Render Internal PostgreSQL URL>
ENVIRONMENT=production
PUBLIC_API_BASE_URL=https://astromyla.onrender.com
PUBLIC_SITE_URL=https://astromyla.com
PAYMENT_MODE=live
IYZICO_BASE_URL=https://api.iyzipay.com
IYZICO_API_KEY=<Live API Key>
IYZICO_SECRET_KEY=<Live Secret Key>
PAID_READING_PRICE_TRY=<Actual legal product price, e.g. 499.00>
DEEP_READING_PRICE_TRY=<Actual legal product price, e.g. 899.00>
OPENAI_API_KEY=<Valid report generation key>
SMTP_HOST=<Transactional email SMTP server>
SMTP_PORT=587
SMTP_USERNAME=<SMTP username>
SMTP_PASSWORD=<SMTP secret>
RECEIPT_FROM_EMAIL=<Verified sender address>
SUPPORT_EMAIL=<Active public support inbox>
PAYMENTS_ENABLED=false
PAYMENTS_LIVE_APPROVED=false
```

For sandbox tests, on a **separate staging backend/frontend** use `PAYMENT_MODE=sandbox`, `IYZICO_BASE_URL=https://sandbox-api.iyzipay.com` and sandbox-prefixed merchant keys. Only after order creation, callback, HMAC-SHA256 signed V3 webhook, server retrieve and PDF download succeed should you move to live, set `PAYMENTS_LIVE_APPROVED=true` and `PAYMENTS_ENABLED=true`.

Hosted Checkout Form callback URL sent by the API:
`https://astromyla.onrender.com/api/payments/iyzico/callback?order=<created order id>`

Merchant webhook notification HTTPS URL (configure in iyzico merchant panel; request V3 signatures):
`https://astromyla.onrender.com/api/payments/iyzico/webhook`

The exact provider SDK behavior, live authentication, payment error behavior, email deliverability and actual PDF fulfillment were **not** verified here. Do not accept customer money solely based on passing mocked tests. Read [iyzico CF docs](https://docs.iyzico.com/en/payment-methods/checkoutform/cf-implementation/cf-retrieve) and [Webhook V3](https://docs.iyzico.com/en/advanced/webhook).

## C. Extra commercial must-haves
- Approve company/tax identity and iyzico merchant onboarding.
- Provide owner-approved Terms, Privacy/KVKK notice, withdrawal/refund policy and working support email before launch.
- Verify Swiss Ephemeris licensing for a commercial web project (AGPL obligations or professional license, as applicable).
- Test user-account recovery and plan email verification, support/admin fulfillment and reliable delivery when provider/API outages occur.

## D. Safe deploy
Extract ZIP. In the inner `AstroMYLA_v1.10.0_RELAUNCH` folder open PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\DEPLOY_ASTROMYLA_V1_10.ps1
```

The deploy script expects GitHub `main` currently at `14a7db0743a6d8c0791b085016392dbfcb5779da` (v1.9.2), creates a rollback branch, runs backend tests and clean frontend build **before** pushing. A changed `main` causes an intentional stop.

After push, verify the **same new commit** in Render `astroMYLA` backend and `astro-ai-site-frontend` as `Live`. Smoke-test natal chart, synastry in both directions, My AstroMYLA save/logout/login/reopen, and payment status configuration before enabling any real charges.

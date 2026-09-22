# AstroMYLA v1.7 — iyzico Hosted Checkout Setup

The code is included, but checkout stays disabled until the production merchant settings are supplied.

## Backend Render environment variables

Set these on the **astroMYLA backend service only**:

```text
IYZICO_API_KEY=<merchant api key>
IYZICO_SECRET_KEY=<merchant secret key>
IYZICO_BASE_URL=https://sandbox-api.iyzipay.com
PAID_READING_PRICE_TRY=<server-side price, e.g. 499.00>
DEEP_READING_PRICE_TRY=<server-side price, e.g. 899.00>
DATABASE_URL=<Render PostgreSQL connection string>
PUBLIC_API_BASE_URL=https://astromyla.onrender.com
PUBLIC_SITE_URL=https://astromyla.com
```

Never create `VITE_IYZICO_*` variables. Vite variables are public browser code.

## Recommended activation sequence

1. Create an iyzico merchant/sandbox account.
2. Create a Render PostgreSQL database.
3. Put the internal/external PostgreSQL URL into backend `DATABASE_URL` as appropriate for the Render service.
4. Set sandbox iyzico API key and secret.
5. Set both server-side product prices.
6. Deploy the backend.
7. Open `/api/payments/config`; it should return `ready: true` but must never expose credentials.
8. Make a sandbox purchase using iyzico test cards.
9. Confirm the callback redirects to `astromyla.com/?payment=success&order=...`.
10. Confirm the report can only be downloaded after server-side payment verification.
11. Only after sandbox acceptance, switch `IYZICO_BASE_URL` and credentials to production.

## Security properties

- Product price is selected from the backend product catalog, never trusted from the browser.
- Buyer identity information is forwarded to iyzico for checkout initialization but is not written to the AstroMYLA order table.
- The order table stores email, product, amount, state and the report request; it does not store card information or the buyer identity number.
- Callback verification retrieves the checkout result from iyzico using the returned token and verifies the SDK response signature when supplied.
- Paid amount, currency and basket ID are checked against the server-created order before status becomes `paid`.
- The frontend only receives a random public order token.

## Production note

Do not enable checkout until tax / invoicing obligations and the Swiss Ephemeris commercial licensing position are resolved for the intended business model.

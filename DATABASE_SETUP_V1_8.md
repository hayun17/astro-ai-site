# Production database setup — required for My AstroMYLA

AstroMYLA v1.8 creates its tables automatically. No manual SQL migration is required.

## Render
1. In Render, create a PostgreSQL database.
2. Copy its **internal database URL / connection string**.
3. Open the `astroMYLA` Web Service → **Environment**.
4. Set:
   - `DATABASE_URL` = the PostgreSQL connection string
5. Save the environment changes and let the backend redeploy.

The backend will create these tables when first used:
- `astromyla_users`
- `astromyla_sessions`
- `astromyla_saved_charts`
- `astromyla_orders` (payment system)

## Security model
- Passwords are never stored as plaintext; scrypt hashes + random salts are stored.
- Browser session tokens are random and only their SHA-256 hash is stored server-side.
- Sessions expire after 14 days.
- Saved birth data is available only to the authenticated account that created it.

## Current limitation
v1.8 includes registration/login/logout but does not yet include email verification or password-reset email delivery. Add those before positioning the account system as a mature consumer identity platform.

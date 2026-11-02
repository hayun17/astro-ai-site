# My AstroMYLA — Make saving really work (production)

Unlike a temporary browser preference, saved birth charts must be written to a persistent server database. **The ZIP alone does not provide database hosting.**

1. In Render Dashboard, check whether you already have a PostgreSQL instance for AstroMYLA. **Do not create a second one** if the existing one is working.
2. If none exists, create a Render PostgreSQL instance in the same region as the `astroMYLA` web service. Review Render's plan, retention, cost and backup settings before proceeding.
3. Copy the **Internal Database URL** from the PostgreSQL connection page (keep it secret).
4. Open Render → `astroMYLA` (backend **Web Service**, not Static Site) → **Environment**. Add a secret environment variable with name `DATABASE_URL`, and the Internal Database URL as its value. Do not paste the connection string into chat or GitHub.
5. Save / redeploy the backend.
6. Visit `https://astromyla.onrender.com/api/account/config` in your browser. Expected response: `{ "ready": true }`.
7. On AstroMYLA: create account → generate a birth chart → "Save this chart" → name it → "Save to My AstroMYLA". Sign out, sign back in, and confirm the chart **and its computed natal snapshot** persist. "Open chart / Use as A" should show the saved natal wheel immediately, while "Use as B" puts that person into Synastry. Regenerate if you want a fresh long-form interpretation. Also test on another device.

If `ready` is false, verify that the backend Render service (not the frontend) has `DATABASE_URL`; see Render service logs for any database connection/permission errors.

## Privacy and account limitations

- This app stores birth date/time, location and the name you give each chart in your account database. Treat this as personal information; publish a suitable privacy notice and retention policy before promoting accounts widely.
- There is no email verification or password-reset mail in v1.9.2. Do not market the account feature as production-mature until those flows are ready.
- Passwords use salted `scrypt`, and the server stores SHA-256 hashes of session tokens. Do not share credentials or Render connection strings.
- It is advisable to restrict account registrations or expand security controls before major public traffic.

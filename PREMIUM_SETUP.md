# Premium Readings Setup - v1.6.0

AstroMYLA now separates **selling a reading** from **generating the paid report**.
That matters because a static frontend must never contain a secret that lets anyone bypass checkout.

## Products

### Personalized Reading
A focused long-form natal report. The PDF opens with the reader's full natal chart wheel, then moves through whole-chart synthesis, Big Three, mind/voice, love, drive, home, career, growth themes, strong aspects, practical reflection points and a personal closing note.

### Deep Personal Reading
Everything above, with a longer synthesis, explicit attention to contradictory/repeating chart signatures and up to three personal questions/themes addressed directly from the natal chart.

## Frontend checkout variables

Set these on the Render **static frontend** service (`astro-ai-site-frontend`):

```text
VITE_PAID_READING_PRICE=your displayed price
VITE_PAID_READING_URL=https://your-secure-checkout-link
VITE_DEEP_READING_PRICE=your displayed price
VITE_DEEP_READING_URL=https://your-secure-checkout-link
```

If a checkout URL is blank, the button remains disabled as **Checkout coming soon**.
No card/payment secret is stored in the browser.

## Protected paid-report generator

Paid PDF generation is server-side only:

```text
POST /api/premium/natal-report
Header: X-Premium-Token: <server secret>
```

In production the backend requires:

```text
PREMIUM_REPORT_TOKEN=<long random secret>
```

Optionally select a separate model for the long paid report:

```text
OPENAI_PREMIUM_MODEL=<model name>
```

If `OPENAI_PREMIUM_MODEL` is blank, AstroMYLA uses `OPENAI_MODEL`.

**Important:** the paid generator does not silently downgrade to the short free/corpus fallback when the model is unavailable. A paid order should fail visibly and be retried rather than deliver a lower-quality product without warning.

## Example server-side payload

```json
{
  "birth": {
    "name": "Example",
    "year": 2002,
    "month": 1,
    "day": 25,
    "hour": 9,
    "minute": 30,
    "latitude": 40.872,
    "longitude": 35.464,
    "tz_offset_hours": 2,
    "timezone": "Europe/Istanbul",
    "birthplace": "Merzifon, Amasya, Turkey",
    "house_system": "P",
    "style": "psychological",
    "focus": "general",
    "time_unknown": false
  },
  "tier": "deep",
  "questions": [
    "Why do I need so much freedom in relationships?",
    "What patterns show up around career visibility?",
    "What helps me feel emotionally safe?"
  ]
}
```

The `questions` array is limited to three items and is used only by the Deep Personal Reading.

## Fulfillment options

### Simple/manual launch
1. Customer completes the external checkout.
2. You collect birth details and, for Deep, up to three questions through your order form.
3. An admin/server process calls `/api/premium/natal-report` with the secret header.
4. The generated PDF is emailed or otherwise delivered to the customer.

### Automated later
Use the payment provider webhook to create/verify the order, store the intake securely, and call the protected report generator from the backend. Do **not** put `PREMIUM_REPORT_TOKEN` in any `VITE_*` variable.

## PDF design

Premium PDFs intentionally differ from the free report:

- Full vector natal chart wheel on page 1
- Big Three strip directly under the wheel
- Soft lilac/pink editorial layout
- Serif long-form reading typography
- Detailed chart-position table with house and retrograde state
- Warm chapter titles and spacious paragraph rhythm
- Deep reports can print the reader's three questions near the beginning
- Footer disclaimer instead of interrupting the reading with repeated warning blocks

See `PREMIUM_REPORT_SAMPLE.pdf` for a layout example.

## Licensing note before monetization

The numerical chart engine uses Swiss Ephemeris through `pyswisseph`. Review the Swiss Ephemeris AGPL / Professional License requirements before commercial operation, especially if AstroMYLA will remain proprietary.


## Security / fulfillment rule for automated checkout

The current public cards are safe external checkout links; they do not directly generate a paid report from the browser. If you automate fulfillment, the payment provider webhook must be verified server-side before AstroMYLA calls `/api/premium/natal-report`. Never trust a browser redirect or query parameter as proof of payment. Keep `PREMIUM_REPORT_TOKEN` and payment-provider webhook secrets on the backend only.

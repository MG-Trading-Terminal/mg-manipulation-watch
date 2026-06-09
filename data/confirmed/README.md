# confirmed/ — human-gated tier

The automated pipeline writes **only** to `../candidates/` and can only raise a
token to `suspected`. This directory is where a **human** records the reviewed
verdicts the bot is forbidden to assert.

To promote a token, add `<SYMBOL>.json` here by hand (via PR) with one of the
human-only statuses and a real evidence bundle:

```json
{
  "symbol": "EXAMPLE",
  "status": "confirmed",            // likely | confirmed | cleared
  "attribution": "inferred-strong", // OAK vocabulary; never weaker than the review supports
  "reviewer": "your-handle",
  "reviewed_at": "2026-06-09",
  "summary": "One-paragraph write-up of what was verified.",
  "oak_techniques": ["OAK-T17.002", "OAK-T3.006"],
  "evidence": [
    { "label": "Coinglass funding/OI", "url": "https://..." },
    { "label": "Bubblemaps supply clusters", "url": "https://..." }
  ]
}
```

`cleared` is as important as `confirmed`: it publicly withdraws a false positive
and is what keeps the system honest (and defensible). Notable `confirmed` cases
are candidates to promote upstream into an OAK `examples/` write-up.

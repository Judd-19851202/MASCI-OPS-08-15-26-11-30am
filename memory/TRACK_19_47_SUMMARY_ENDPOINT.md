# TRACK 19.47 · Summary Endpoint

## Endpoint
`GET /api/operational-intelligence/summary` (read-only, admin-only)

## Response shape
```json
{
  "count": 11,
  "attention_buckets": { "LOW": 7, "MEDIUM": 2, "HIGH": 1, "CRITICAL": 0 },
  "worst_product": { "product_id": "…", "display_name": "…", "score": 45, "attention_level": "HIGH" },
  "best_product":  { "product_id": "…", "display_name": "…", "score": 100, "attention_level": "LOW" },
  "recent_failures": [ { "product_id": "…", "error": "…" } ],
  "dry_run_default": true,
  "products": [
    {
      "product_id": "safety_morning_digest",
      "display_name": "Morning Safety Intelligence",
      "status": "implemented",
      "permission_role": "safety_or_admin",
      "schedule": { "freq": "weekly", "iso_day": 1, "hour_utc": 13 },
      "tags": ["safety", "weekly", "attention"],
      "score": 92,
      "attention_level": "LOW",
      "trend_direction": "→",
      "trend_percent": null,
      "confidence": "high",
      "data_freshness": "live",
      "top_attention_label": "1 case(s) with evidence gaps.",
      "last_generated_at": "2026-07-06T13:00:00+00:00",
      "last_sent_at": "2026-07-06T13:01:11+00:00",
      "last_status": "dry_run",
      "last_recipient_count": 4,
      "error": null
    }
  ]
}
```

## Guarantees
- **Admin-only** — `require_admin` dependency (safety/unauth → JSON 401/403).
- **Read-only** — no POST/PATCH/DELETE mirror.
- **Never returns `rendered_html`** — kept lean for the top-strip cold-open.
- **Partial-failure safe** — one product's exception is captured into
  the row's `error` field; the endpoint continues composing the rest.
- **Buckets** — `attention_buckets` is authoritative for the Cockpit
  top-strip counts.
- **Sensitive-field posture** — the endpoint reads `send_status` /
  `recipient_count` / `at` from the audit row but never surfaces raw
  payload keys like `token`, `secret`, `password`, `api_key`.

## Why not compose in the frontend?
Composing 11 individual `/preview` calls from the browser would take
2-3× longer and would fan-out CORS + auth cost. The summary endpoint
gives the Cockpit a ~200-400ms cold-open regardless of product count.
Additive · zero drift.

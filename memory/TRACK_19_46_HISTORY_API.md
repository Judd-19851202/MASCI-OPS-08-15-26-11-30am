# TRACK 19.46 · History API

## Endpoints (read-only, admin-only)
### `GET /api/operational-intelligence/history`
List digest history rows across every OI product.

**Query params:**
| Name | Type | Default | Notes |
|---|---|---|---|
| `product_id` | string | — | Filter to one product. 404 if unknown. |
| `period` | string | — | Filter to one ISO-week (e.g. `2026-W28`). |
| `since` | ISO datetime | — | Lower bound on `generated_at`. |
| `until` | ISO datetime | — | Upper bound on `generated_at`. |
| `limit` | int | 100 | Max 500. |
| `offset` | int | 0 | Pagination offset. |
| `sort` | string | `-generated_at` | One of `generated_at`, `product_id`, `period` (prefix `-` for descending). |

**Response:**
```json
{
  "count": 87,
  "total": 431,
  "limit": 100,
  "offset": 0,
  "sort": "-generated_at",
  "history": [
    {
      "id": "…uuid…",
      "product_id": "safety_morning_digest",
      "period": "2026-W28",
      "generated_by": "system",
      "generated_at": "2026-07-06T13:00:00+00:00",
      "subject": "Morning Safety Intelligence",
      "score": {
        "overall_score": 92,
        "attention_level": "LOW",
        "confidence": "high",
        "trend_direction": "→",
        "trend_percent": null
      }
    }
  ]
}
```

The list response **never includes** `rendered_html` (kept lean for
the Cockpit UI list strip). Use the detail endpoint to fetch a full
digest object.

### `GET /api/operational-intelligence/history/{history_id}`
Fetch one row. `include_html=true` opts in to the rendered HTML.

## Guarantees
- **Read-only** — no POST/PATCH/DELETE mirrors this route.
- **Admin-only** — safety token → JSON 403.
- **Pagination** — `count` + `total` + `limit` + `offset` always
  returned so the Cockpit UI can compute page metadata.
- **Deterministic sort** — default `-generated_at` matches operator
  expectation.
- **No secret leakage** — the underlying `write_history` never stores
  tokens/passwords; the list projection strips `rendered_html`.

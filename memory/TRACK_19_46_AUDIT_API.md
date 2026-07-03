# TRACK 19.46 · Audit API

## Endpoint (read-only, admin-only)
### `GET /api/operational-intelligence/audit`
Query the append-only audit trail written by `engine.write_audit(...)`.

Covers:
- `dispatch` — every preview/dispatch (dry-run or live).
- `dispatch_skipped_dedupe` — dedupe guard fired.
- Any future audit-worthy event added to the engine.

**Query params:**
| Name | Type | Default | Notes |
|---|---|---|---|
| `product_id` | string | — | Filter to one product. 404 if unknown. |
| `event` | string | — | Filter to one event kind (e.g. `dispatch`). |
| `actor` | string | — | Filter to one actor email / identity. |
| `since` | ISO datetime | — | Lower bound on `at`. |
| `until` | ISO datetime | — | Upper bound on `at`. |
| `limit` | int | 100 | Max 500. |
| `offset` | int | 0 | Pagination offset. |
| `sort` | string | `-at` | One of `at`, `product_id`, `event`, `actor` (prefix `-` for desc). |

**Response:**
```json
{
  "count": 24,
  "total": 91,
  "limit": 100,
  "offset": 0,
  "sort": "-at",
  "audit": [
    {
      "id": "…uuid…",
      "product_id": "corporate_intelligence",
      "event": "dispatch",
      "actor": "admin",
      "at": "2026-07-06T14:02:11+00:00",
      "payload": {
        "dry_run": true,
        "send_status": "dry_run",
        "recipient_count": 4,
        "dedupe_key": "corporate_intelligence:2026-W28:abc123def456",
        "delivery": [],
        "history_id": "…uuid…"
      }
    }
  ]
}
```

## Guarantees
- **Read-only** — no POST/PATCH/DELETE mirrors this route.
- **Admin-only** — safety token → JSON 403.
- **Sensitive-field strip** — even if a caller has historically added
  a `token` / `secret` / `password` / `api_key` field to the audit
  payload, this endpoint filters it out before response. Defence in
  depth on top of the "engine.write_audit stores only structured
  metadata" contract.
- **Pagination** — same `count` / `total` / `limit` / `offset`
  contract as the History API.
- **Chronology** — default `-at` (newest first).

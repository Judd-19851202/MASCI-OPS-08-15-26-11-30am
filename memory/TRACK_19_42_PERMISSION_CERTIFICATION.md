# TRACK 19.42 · Permission Certification

**Verdict:** 🟢 GREEN.

## Product-level permissions

| Product | Permission | Enforcement |
|---|---|---|
| `safety_morning_digest` | `safety_or_admin` | Engine route `/api/operational-intelligence/{id}/preview` — accepts X-Safety-Token OR X-Admin-Token (directory admin) |
| `executive_operations_brief` | `admin_only` | Engine route enforces `_is_admin_actor(actor)` |
| `po_weekly_digest` | `admin_only` | Engine route enforces `_is_admin_actor(actor)` |
| `transportation_intelligence` | `safety_or_admin` | Same as Morning Safety — Safety or Admin |

## Route gates (Track 19.40)

- `GET /api/operational-intelligence/products` — Safety or Admin.
- `GET /api/operational-intelligence/{id}/preview` — Safety or Admin + admin_only enforcement per product.
- `POST /api/operational-intelligence/{id}/dispatch?dry_run=<bool>` — same gate + same admin_only enforcement.

## Unauthorised behaviour

- Missing token → HTTP 401 with `{"code": "unauthorized"}`.
- Safety token on admin_only product → HTTP 403 with `{"code": "forbidden", "detail": "admin only"}`.
- Contract-registered product dispatch → HTTP 501 with `{"code": "aggregator_not_implemented"}`.
- Unknown product → HTTP 404 with `{"code": "not_found"}`.

## Non-goals (deferred)

- **Group-level ACL** — future track: `operational_recipient_groups` documents will grow a `readers` array so a specific product can be viewable by (say) `executive_leadership` even without an admin token.
- **Per-product PDF gate** — Track 19.36 executive PDF path keeps its own permission gate; no change here.

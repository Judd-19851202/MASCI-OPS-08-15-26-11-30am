# TRACK 19.39 · RECIPIENT MANAGEMENT

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_39_MORNING_SAFETY_DIGEST.md`

## Collection
`morning_digest_recipients` (additive · new Mongo collection).

### Fields
- `id` (UUID)
- `email` (lower-cased on insert)
- `display_name`
- `role_label` (free text; e.g. `Super Admin`, `Safety Manager`, `Operations`)
- `active` (boolean · default `True`)
- `digest_type` (default `safety_morning_digest`)
- `created_at` · `updated_at` (ISO)
- `added_by`
- `notes`

## Seeding
On first read (list / preview / send), `ensure_default_recipients_seeded` inserts default recipients **only if the collection is empty**. Defaults are configurable via `MORNING_DIGEST_DEFAULT_RECIPIENTS` env variable — comma-separated `email|display_name|role_label` triples. When unset, the seed is:
- `jaymn.judd@mascigc.com` · Jaymn Judd · Super Admin
- `safety@mascigc.com` · Safety Inbox (placeholder) · Safety Manager

The Safety placeholder is intentional — an admin replaces it with the real Safety alias via `POST /recipients` (add) and `PATCH /recipients/{id}` with `{"active": false}` on the placeholder.

## Admin surface (no code changes required to add/remove)
| Verb | Route | Behavior |
|---|---|---|
| GET | `/api/incident-intelligence/morning-digest/recipients?active_only=…` | List |
| POST | `/api/incident-intelligence/morning-digest/recipients` | Add (`email` required · `display_name`/`role_label`/`notes` optional) |
| PATCH | `/api/incident-intelligence/morning-digest/recipients/{id}` | Update `active` · `notes` · `display_name` · `role_label` (allow-list) |

All three endpoints Safety+Admin gated (`make_require_safety_or_admin`).

## Active/inactive discipline
- `list_recipients(active_only=True)` filters the collection to `active=True`.
- `send_digest(...)` calls the aggregator with `active_only=True` and only sends to that set.
- Deactivation is preferred over deletion — history remains in the collection and in the audit trail.

## Delete
No explicit delete endpoint in this track. `active=false` gives the same operational outcome without losing history. A future track can add a hard-delete endpoint if compliance requires it.

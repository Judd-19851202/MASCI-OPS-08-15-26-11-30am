# TRACK 19.45A · Recipient Governance Certification

**Verdict:** 🟢 GREEN.

## The single source of truth

- Individuals → `morning_digest_recipients` collection (Track 19.39, reused via `digest_type` column).
- Groups → `operational_recipient_groups` collection (Track 19.40 additive).
- Resolver → `list_recipients_for(db, product_id=..., active_only=True)` — union direct + groups, deduped by email (direct wins).

**No product may bring its own recipient logic.**

## API surface (Track 19.45A)

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/api/operational-intelligence/recipients` | List with search/filter/limit | Admin |
| GET | `/api/operational-intelligence/recipients/for/{product_id}` | Union direct + groups for a product | Admin |
| POST | `/api/operational-intelligence/recipients` | Add | Admin |
| PATCH | `/api/operational-intelligence/recipients/{id}` | Update fields (partial) | Admin |
| DELETE | `/api/operational-intelligence/recipients/{id}` | Deactivate (never hard-delete) | Admin |
| POST | `/api/operational-intelligence/recipients/bulk-import` | Bulk-add · dedupe · error reporting | Admin |
| GET | `/api/operational-intelligence/groups` | List groups | Admin |
| POST | `/api/operational-intelligence/groups` | Create group | Admin |
| POST | `/api/operational-intelligence/groups/{group_id}/members` | Add member | Admin |

## Governance rules enforced

- **Every mutation stamps `updated_at` + `updated_by`.**
- **Deletion is disabled — DELETE flips `active=False`** (regulatory replay).
- **Bulk import dedupes** by `(email, digest_type)` and returns per-row status.
- **Invalid emails rejected** at API boundary (HTTP 400).
- **Product must exist** for `recipients/for/{product_id}` (HTTP 404 otherwise).
- **Admin gate only** — no Safety user can mutate recipients.

## No-hardcode invariant

The only exceptions are:
- Track 19.39 seeded defaults (Jaymn + Safety placeholder) — env-controlled via `MORNING_DIGEST_DEFAULT_RECIPIENTS`.
- Legacy env-driven single-address digests being retired (`SAFETY_DIGEST_TO_EMAIL`, `BACKUP_VERIFICATION_TO`).

All other recipients come from the database via this API. **No code changes required to change recipients — ever.**

# TRACK 19.41 · Recipient Group Standard

**Status:** 🟢 LOCKED · uses the Track 19.40 recipient engine.

## Single recipient engine

- Module: `/app/backend/operational_intelligence/recipients.py`.
- Individual recipients: `morning_digest_recipients` collection (existing since Track 19.39; reused via `digest_type` column — zero drift).
- Group recipients: `operational_recipient_groups` collection (additive, Track 19.40).
- Resolver: `list_recipients_for(db, product_id=..., active_only=True)`.

## Data contract

### Individual recipient row

```json
{
  "id":            "<uuid>",
  "email":         "user@masci.local",
  "display_name":  "Full Name",
  "role_label":    "Safety",
  "digest_type":   "safety_morning_digest",
  "active":        true,
  "notes":         "",
  "created_at":    "2026-07-04T...Z",
  "updated_at":    "2026-07-04T...Z",
  "added_by":      "admin@example",
  "updated_by":    "admin@example"
}
```

### Group document

```json
{
  "id":         "<uuid>",
  "group_id":   "executive_leadership",
  "group_name": "Executive Leadership",
  "products":   ["executive_operations_brief", "corporate_intelligence"],
  "members": [
    {"email": "ceo@masci", "display_name": "CEO",
     "role_label": "Executive Leadership", "active": true}
  ],
  "created_at": "...",
  "created_by": "admin@example"
}
```

## Standard group taxonomy (recommended, not enforced)

Admins should create these groups over time to route products cleanly:

- `executive_leadership`
- `safety`
- `operations`
- `project_managers`
- `hr`
- `transportation`
- `fleet`
- `shop`
- `accounting`
- `dispatch`
- `corporate`
- `custom_<slug>` (per-team subscriptions)

Product ↔ group binding is expressed by adding the `product_id` to the group's `products` array. `list_recipients_for` returns the union of directly-subscribed individuals + members of groups that subscribe to the product, deduped by email (direct entry wins).

## Product-specific defaults

| Product | Recommended default groups |
|---|---|
| `safety_morning_digest` | `safety` |
| `executive_operations_brief` | `executive_leadership` |
| `po_weekly_digest` | Existing `project_managers` + `hr` (via legacy code path — see PO forensic audit). Admins may additionally register `operational_recipient_groups` entries for cross-team visibility. |
| `weekly_operations_digest` | `executive_leadership`, `operations` |
| `transportation_intelligence` | `transportation`, `safety` |
| `fleet_intelligence` | `fleet`, `safety` |
| `hr_intelligence` | `hr` |
| `training_intelligence` | `hr`, `safety` |
| `project_intelligence` | `project_managers` |
| `shop_intelligence` | `shop` |
| `corporate_intelligence` | `executive_leadership` |

## PO Digest recipient model (special case)

PO Digest recipients are derived from the `project_managers` and `hr_users` collections. These are the operational source of truth — a PM's PO scope changes automatically when they take/lose a project. **The legacy path is preserved** because:

- Adding a PM already implicitly subscribes them to PO visibility.
- Adding an HR user already implicitly grants cross-portal PO read.
- No admin should have to double-manage recipient lists.

Additive: admins may also register direct rows in `morning_digest_recipients` with `digest_type="po_weekly_digest"` for external stakeholders (e.g., accounting managers, executive assistants). The engine will merge them into the recipient set via `list_recipients_for`.

## No hardcoded recipients

Except:
- Track 19.39 seeded defaults (Jaymn + Safety placeholder) — configurable via `MORNING_DIGEST_DEFAULT_RECIPIENTS` env.
- Legacy env-driven single-address digests being retired (`SAFETY_DIGEST_TO_EMAIL`, `BACKUP_VERIFICATION_TO`).

No other hardcoded recipients allowed in Track 19.4x product code.

## Governance

- Every add/update is admin-only.
- Every mutation writes to the shared audit collection (`operational_intelligence_audit` + `morning_digest_audit`).
- Deactivation is preferred over deletion — history retained for regulatory replay.

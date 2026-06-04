# MAINTAINX · WORK ORDER MAPPING  (Phase 4)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY PLANNING (no writes, no MaintainX traffic)

This document maps the canonical ForgedOps defect payload (Phase 3) to specific MaintainX Work Order fields. Field names follow the MaintainX v1 API as commonly documented; minor field-name drift will be tolerated by the WO push module the same way `services/maintainx_client.MaintainxClient` already tolerates drift in `/v1/assets` shapes.

---

## 1 · Field-level mapping

| MaintainX WO field | Type | Source (canonical) | Notes |
| --- | --- | --- | --- |
| `title` | string · ≤120 char | `defect_title` | Already pre-truncated by canonical builder. Default formats per Phase 3 §3. |
| `description` | string · markdown allowed · ≤4000 char | `defect_description` + bulleted `failed_items` summary | Append a footer line: `--- ForgedOps correlation_id: <uuid> · source=<source_type>:<source_record_id>` so admins can reconcile. |
| `priority` | enum | derived from `severity` (table below) | See §2. |
| `assetId` | string | `maintainx_asset_id` | **REJECT the push if unresolved**; do not silently fall back to a generic asset. |
| `locationId` | string · optional | resolve from `asset_mappings.maintainx.location_id` for the same asset | If absent, omit; MaintainX will infer from asset. |
| `dueDate` | ISO 8601 · optional | derived from `severity` and `safety_critical` (table in §3) | `safety_critical=True` → due **today**; else +3d / +7d. |
| `assignedTo` | array<userId> · optional | derive from `employee_mappings.maintainx.user_id` for the shop on-call list | If empty, leave unassigned — MaintainX defaults route to the team. |
| `categories` | array<string> · optional | `["ForgedOps", source_type, equipment_type]` | Keep human-readable; MaintainX accepts free-form labels. |
| `externalId` | string · unique | `correlation_id` (UUID v4) | This is the **primary duplicate-protection key** between systems. The push module MUST query `GET /v1/work-orders?externalId=…` before POSTing; if a hit comes back, mark `sync_status="skipped"` and reuse the existing WO id. |
| `attachments` | array<{url,name}> · optional | from `photos[]` and `attachments[]` via pre-signed R2 URL | Push pre-signed URLs (24h TTL) rather than base64 bytes — keeps the WO POST under MaintainX's request-size limits. |
| `customFields` | object · optional | (see §4) | The vehicle for ForgedOps metadata that has no direct MaintainX field. |

---

## 2 · Priority mapping

| Canonical `severity` | `safety_critical` | MaintainX `priority` |
| --- | --- | --- |
| `oos` / `critical` | true | `"Critical"` |
| `high` | — | `"High"` |
| `medium` / `monitor` / `attn` | — | `"Medium"` |
| `low` | — | `"Low"` |
| (anything else / unknown) | — | `"Medium"` (safe default) |

If MaintainX's tenant only supports four levels and the labels differ slightly, the constants are centralized in a single dict so future name drift requires one line of code change.

---

## 3 · `dueDate` derivation

| `safety_critical` | `severity` | `dueDate` |
| --- | --- | --- |
| true | oos / critical / high | **today** (end-of-day UTC) |
| false | monitor / attn | **+3 days** |
| false | low | **+7 days** |
| false | (unknown) | omit (MaintainX default) |

---

## 4 · `customFields` payload

The following keys ride along on every WO and are also stored back on the ForgedOps source row's `external_refs` for symmetry:

```jsonc
{
  "forgedops_correlation_id":   "<uuid>",            // == externalId
  "forgedops_source_type":      "fleet_dvir|equipment_preop|...",
  "forgedops_source_record_id": "<row id>",
  "forgedops_inspection_id":    "<id or empty>",
  "forgedops_unit_number":      "TRK-12",
  "forgedops_reported_by":      "Allen Smathers",
  "forgedops_reported_by_role": "driver",
  "forgedops_project_number":   "23-15-S",
  "forgedops_safety_critical":  true,
  "forgedops_oos_recommended":  true,
  "forgedops_url":              "https://mascidocs.com/admin/operations-events?type=fleet_defect&id=<id>"
}
```

These keys appear in the MaintainX UI and in `GET /v1/work-orders/{id}` responses, so:
- A shop technician can click directly back to the ForgedOps source row.
- A ForgedOps admin running a future sync job can disambiguate two WOs with the same title.
- The `forgedops_url` lets MaintainX-side users navigate "home" without leaving their tool.

---

## 5 · `externalId` is the cross-system primary key

This is the single most important field for safe duplicate protection:

- **Generated once** in the canonical builder via `uuid.uuid4()`.
- **Stamped on the source row** (`external_refs.correlation_id`) at the moment the canonical payload is built — even if we never push.
- **Sent as `externalId`** on the WO POST.
- **Looked up first** on every retry via `GET /v1/work-orders?externalId=<id>` to detect a partial-failure case (we POSTed, MaintainX created the WO, but our local persistence failed).

If `externalId` query support is not available in the tenant version, fallback duplicate-detection uses `(assetId, title, customFields.forgedops_source_record_id)` as a secondary key — see Phase 8.

---

## 6 · Photos / attachments push

| Field | Behaviour |
| --- | --- |
| `attachments[].url` | R2 pre-signed URL via the existing `safety_doc_storage.presign_get(...)` helper. Default TTL = 24h. |
| `attachments[].name` | Synthetic: `"{unit_number}_{source_type}_{ordinal}.jpg"` |
| Push timing | Push synchronously with the WO when MaintainX supports `attachments` on `POST /work-orders`; otherwise queue a follow-up `POST /work-orders/{id}/attachments` per attachment. |
| Failure recovery | Each attachment push is idempotent — track per-key state in `external_refs.attachments_pushed=[r2_key,…]` on the source row. |

---

## 7 · External reference back to ForgedOps

On a successful WO create, **stamp the source row in-place** (atomic update):

```python
await db.<collection>.update_one(
    {"id": source_record_id},
    {"$set": {
        "external_refs.maintainx_work_order_id": wo.id,
        "external_refs.maintainx_url":            wo.url,
        "external_refs.maintainx_external_id":    correlation_id,
        "external_refs.maintainx_pushed_at":      now_iso,
        "sync_status":                            "pushed",
    }}
)
```

This is the **only** write that the WO-push module makes to operational ForgedOps collections (`fleet_defects` / `equipment_inspections` / `asset_holds`). Audit captures the diff (`wo_pushed_to_maintainx`).

---

## 8 · Webhook correlation (callback path)

Inbound `POST /api/integrations/maintainx/webhook` events of type `workOrder.statusUpdated` or `workOrder.completed` will be correlated to ForgedOps by:

1. `externalId` on the WO → matches `external_refs.maintainx_external_id` on the source row.
2. Fallback: `wo.id` → matches `external_refs.maintainx_work_order_id` on the source row.
3. Otherwise: row is logged into `integration_sync_logs` with `status="unmatched_webhook"` for admin reconciliation.

The webhook handler must NEVER assume which collection the source row lives in — it should search `fleet_defects`, `equipment_inspections`, and `asset_holds` in that order (cheapest indexes first).

---

## 9 · Out of scope for this sprint

- No actual `services/maintainx_work_order_push.py` module is written.
- No fields are added to `fleet_defects` / `equipment_inspections` / `asset_holds` schemas.
- No MaintainX API call (read or write) is made.

This Phase 4 document is the contract that the next sprint will implement against, with operator authorisation.

— End of Phase 4 work order mapping —

# TRACK 19.61 · Zero-Drift Matrix — Asset Thread

**Rule:** For every axis of drift, declare `NEW` (created), `EXTENDED`
(additive), or `REUSED` (unchanged). Track 19.61 is a
**PROMOTE + EXTEND (small)** implementation — most rows are REUSED.

## Matrix

| Axis | Verdict | Note |
|---|---|---|
| Backend collection: assets | REUSED | `equipment_master` unchanged. |
| Backend collection: timeline | REUSED | Track 13.26 `asset_service_events` backbone unchanged. |
| Backend collection: documents (native) | REUSED | `asset_documents` unchanged. |
| Backend collection: documents (legacy paper) | EXTENDED (additive) | `employee_records` — new `entity_kind="asset"` discriminator + additive record_type slugs. |
| Backend collection: transfers | REUSED | `asset_transfers` unchanged. |
| Backend collection: inspections / DVIR | REUSED | `equipment_inspections` + `fleet_ops` unchanged. |
| Backend collection: PM engine | REUSED | `pm_schedules` / `pm_work_orders` unchanged. |
| Backend collection: incidents | REUSED | Track 19.16 incident engine unchanged. |
| Backend collection: PO / vendor / suppliers | REUSED | `po_requests` / `suppliers` unchanged. |
| Backend router: asset_spine | EXTENDED (additive) | New read-only `GET /api/asset-spine/resolve` endpoint. |
| Backend router: employee_records | EXTENDED (additive) | New `entity_kind="asset"` support inside existing routes. |
| Backend router: asset_service_events | REUSED | `/api/assets/{unit_number}/timeline` unchanged. |
| Backend router: asset_care | REUSED | `/api/asset-care/*` unchanged. |
| Backend router: asset_documents | REUSED | Doc surface unchanged. |
| Backend router: asset_transfers | REUSED | Transfer surface unchanged. |
| Backend router: fleet_ops | REUSED | Fleet defect/DVIR/OOS surface unchanged. |
| Backend router: safety_forms | REUSED | Issuance/training surface unchanged. |
| Backend router: shop_intel | REUSED | Shop lens support unchanged. |
| OI engine files | REUSED (frozen) | Lock-tested inventory unchanged. |
| OI products | REUSED | `fleet_intelligence` + `shop_intelligence` reused via client-side class routing. Zero new products. |
| OI Guidance model | REUSED | `GuidanceCard` primitive unchanged. |
| Attention language | REUSED | `AttentionChip` primitive unchanged. |
| Relationship graph | REUSED | `RelationshipGraph` primitive unchanged. |
| Thread shell | REUSED | `OperationalThreadPage` primitive unchanged. |
| Timeline rendering | REUSED | `OperationalThread` primitive unchanged. |
| Score model | NOT INTRODUCED | Health = qualitative label. No % anywhere. |
| PDF renderer | NOT INTRODUCED | Not consumed on this page. |
| Email pipeline | NOT INTRODUCED · NOT TOUCHED | AdminAssetThread + resolver are silent. |
| Notification pipeline | NOT INTRODUCED · NOT TOUCHED | No triggers from this page. |
| Photo store | REUSED | `asset_documents` (existing). |
| Audit engine | REUSED | Per-collection audit + backbone events. |
| Fleet Unit Thread pilot | REUSED (byte-identical) | `FleetUnitThread.jsx` and `/fleet/unit/:unit_number` unchanged. |
| Frontend: new page | NEW | `AdminAssetThread.jsx` — the ONLY new file. |
| Frontend: route | EXTENDED (one entry) | `/admin/assets/:assetRef/thread` added in `App.js`. |
| Public routes | NONE ADDED | No public URL. |
| Permission widening | NONE | All roles keep prior rights. |

## Grep-verified non-drift

- Asset routes (`asset_spine.py`, `asset_service_events.py`,
  `asset_documents.py`, `asset_care.py`, `asset_transfers.py`) contain
  **zero** `fsi_send_email` / `resend` / `phase4.send_email`
  references.
- `AdminAssetThread.jsx` contains **zero** email path references.
- Universal Asset Identifier Resolver block in `asset_spine.py`
  contains **zero** email-adjacent imports or calls.
- OI engine and OI component inventories match the Track 20.5 frozen
  set exactly.

## Backwards-compatibility affirmation

- Every existing `employee_records` record without `entity_kind`
  continues to be interpreted as `"employee"` — validated by the
  existing `$in: ["employee", None]` filter.
- Every existing asset-lane issuance record (PPE / phone / tool /
  iPad / laser / etc.) remains `entity_kind="employee"` and works
  identically.
- Every existing `asset-spine` client keeps working — the resolver is
  an **additive** endpoint, not a replacement.
- The Fleet Unit Thread pilot keeps its existing route, page, and
  behavior.

## Zero-Drift statement

**Zero architectural drift. Zero duplicate systems. Zero live emails.**

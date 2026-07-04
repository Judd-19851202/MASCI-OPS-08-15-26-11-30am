# TRACK 19.62 · Zero-Drift Matrix

## Axis-by-axis

| Axis | Verdict | Note |
|---|---|---|
| Backend collection: assets | REUSED | `equipment_master` untouched. |
| Backend collection: fire extinguishers | REUSED (additive fields) | `db.fire_extinguishers` gains 10 optional identity/assignment fields. Zero data migration. |
| Backend collection: timeline | REUSED | `asset_service_events` untouched. |
| Backend collection: documents (native) | REUSED | `asset_documents` untouched. |
| Backend collection: documents (legacy paper) | EXTENDED (additive slugs) | `employee_records` LANE_RECORD_TYPES["asset"] gains 5 fire slugs. |
| Backend collection: attachments (fire) | REUSED | Existing safety attachments store untouched. |
| Backend collection: PM engine | REUSED | Not consumed by fire flow. |
| Backend collection: inspections | REUSED | Safety Portal's `.../inspect` remains authoritative. |
| Backend router: asset_spine | EXTENDED (additive) | Resolver fallback into `db.fire_extinguishers`. |
| Backend router: safety_portal/fire_extinguishers | EXTENDED (additive) | List gains parent filters; create/update persists assignment fields. |
| Backend router: employee_records | EXTENDED (additive) | 5 fire-specific record_type slugs. |
| Backend router: OI engine | REUSED (frozen) | Nine-file inventory unchanged. |
| Backend service: asset_taxonomy | EXTENDED (v1.0.0 → v1.1.0 · additive) | New class + 9 types + behavior overrides. |
| Backend service: notifications | REUSED | `safety.fire_extinguishers` module untouched. |
| Backend service: CA link types | REUSED | `fire_ext` link type untouched. |
| Backend service: operational_signals | REUSED | `fire_ext.fail` untouched. |
| Frontend: AdminAssetThread | EXTENDED (class branch) | Fire Protection branch added. |
| Frontend: FleetUnitThread pilot | EXTENDED (relationship + attention) | Parent asset surfaces linked extinguishers. |
| Frontend: SafetyFireExtinguishers | EXTENDED (deep-link) | Row identifier links to Asset Thread. |
| Frontend: SafetyFireExtImport | REUSED | Untouched. |
| Frontend: SafetyFireExtManageDialog | REUSED | Untouched. |
| OI product | NONE ADDED | `fire_intelligence` / `fire_protection_intelligence` NOT created. |
| PDF renderer | NONE ADDED | No fire-specific PDF. |
| Email pipeline | NONE ADDED · NOT TOUCHED | Silent. |
| Notification pipeline | NONE ADDED · NOT TOUCHED | Silent. |
| Score model | NONE ADDED | Qualitative labels only. |
| Public routes | NONE ADDED | No public URL. |
| Permission widening | NONE | All roles keep prior rights. |
| Compliance claims | FORBIDDEN AND ABSENT | Lock-tested — no OSHA/legal/certified/fire-code phrases in the UI. |
| `services/asset_taxonomy.py` v1.0.0 consumers | UNCHANGED | v1.1.0 is a strict superset. |

## Grep-verified non-drift
- No `fsi_send_email` / `resend` / `phase4.send_email` in any touched
  file (backend or frontend).
- No new `.py` in `backend/operational_intelligence/`.
- No new `.jsx` in `frontend/src/components/operational_intelligence/`.
- No new router files under `backend/routes/`.
- No new collections referenced anywhere.

## Fleet pilot preservation
- `/fleet/unit/:unit_number` route unchanged.
- The pilot page is extended with an ADDITIVE fetch and additive
  relationship/attention rendering — no removal of existing behavior.

## Zero-Drift statement
**Zero architectural drift. Zero duplicate systems. Zero live emails.**
Fire Protection is now a first-class asset class without any change to
the shape of the platform.

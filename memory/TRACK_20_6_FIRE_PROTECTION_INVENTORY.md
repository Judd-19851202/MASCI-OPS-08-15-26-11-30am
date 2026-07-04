# TRACK 20.6 · Fire Protection & Life Safety Inventory

Every fire-protection-adjacent surface in the platform, catalogued once,
before any promotion.

## 1 · Backend collections

| Collection | Purpose | Verdict |
|---|---|---|
| `db.fire_extinguishers` | Canonical fire-extinguisher register (Phase 3 Safety module). Fields: `id`, `unit_id`, `location_kind`, `location_value`, `type` (ABC/CO2/etc.), `size`, `last_inspection_date`, `next_due_date`, `last_status`, `notes`, `equipment_master_id` (iter138 half-binding), `attachments`. | **DUPLICATE** (Phase A: keep · Phase B: retire in favor of `equipment_master`). |
| `db.equipment_master` | Canonical asset spine — does NOT currently hold fire extinguishers. | **PROMOTE TARGET** (Phase B). |
| `db.asset_service_events` | Timeline backbone. Does NOT currently ingest extinguisher inspection events. | **PROMOTE TARGET** (Phase B). |
| `db.equipment_inspections` | Structured Pre-Op / DVIR / Equipment inspection engine. Does NOT ingest fire-ext monthly inspections. | Complementary; no direct role in Fire. |
| `db.employee_records` | Historical Records (Track 19.21b + 19.59 vendor + 19.61 asset). Can ingest fire-related legacy paper via `entity_kind="asset"`. | **EXTEND** (add fire-specific record_type slugs · additive). |
| `db.operational_signals` | Emits `fire_ext.fail` on inspection failure (existing wiring). | **REUSE** unchanged. |
| `db.corrective_actions` | Accepts `fire_ext` link type (existing CA linkage). | **REUSE** unchanged. |
| `db.notifications` | `safety.fire_extinguishers` notification module (existing). | **REUSE** unchanged. |

## 2 · Backend routers

| Router | Prefix | What it serves | Verdict |
|---|---|---|---|
| `backend/routes/safety_portal/fire_extinguishers.py` | `/api/safety/fire-extinguishers` | GET list · POST create · PATCH update · POST `/inspect` · DELETE · attachments · import (bulk CSV) · export | **KEEP as-is** in Phase A · **replatform on spine backwards-compat view** in Phase B. |
| `backend/routes/asset_spine.py` | `/api/asset-spine` | Universal asset spine + Track 19.61 resolver. | **EXTEND** (Phase A: resolver falls back to `db.fire_extinguishers` when unit not found in `equipment_master`). |
| `backend/routes/employee_records.py` | `/api/employee-records` | Historical Records intake (with Track 19.61 asset lane). | **EXTEND** (Phase A: additive record_type slugs for fire paper). |

## 3 · Frontend surfaces

| Surface | Purpose | Verdict |
|---|---|---|
| `pages/SafetyFireExtinguishers.jsx` | Fire extinguisher register + inspection UI. | **KEEP** — Safety authoritative surface. Cross-link to Asset Thread (Phase A read-side). |
| `pages/SafetyFireExtImport.jsx` | Bulk CSV import for fire-ext inventory. | **KEEP**. |
| `components/SafetyFireExtManageDialog.jsx` | Fire ext manage dialog (inspections, attachments, history PDF). | **KEEP**. |
| `pages/SafetyDigest.jsx` | Digest KPI `fire_extinguishers_overdue`. | **KEEP** — consumer-side. |
| `pages/SafetyReports.jsx` | Fire-ext export report. | **KEEP**. |
| `pages/SafetyCorrectiveActions.jsx` | CA link type `fire_ext`. | **KEEP**. |
| `components/SafetyCaLinksManager.jsx` | Renders `fire_ext` link option. | **KEEP**. |
| `components/OperationalSignalsPanel.jsx` | Renders `fire_ext.fail` signal → deep-link to Safety Portal. | **KEEP**. |
| `components/NotificationBell.jsx` | `safety.fire_extinguishers` notification module. | **KEEP**. |
| `components/GlobalSearch.jsx` | Search styling for `fire_extinguishers`. | **KEEP**. |
| `components/WhereUsedPanel.jsx` | Where-used mapping for `fire_extinguishers`. | **KEEP**. |
| `lib/portalContinuity.js` | Portal-continuity mapping for `/safety-portal/fire-extinguishers`. | **KEEP**. |
| `lib/inspectionSchema.js` | Includes `fire_extinguishers` line in inspection schemas. | **KEEP** — this is a checkbox in DVIR/Pre-Op inspections, complementary. |
| `AdminAssetThread.jsx` (Track 19.61) | Universal Asset Thread. Currently cannot resolve fire-ext identity. | **EXTEND (Phase A)** — read-side adapter over the Fire-Ext resolver fallback. |

## 4 · Locations where extinguishers live (per canonical `location_kind`)

Sourced from the field-team enumeration in the audit spec:

- Vehicle extinguishers (pickup · dump · fuel · lube · service · water · flatbed · crew · roll-off · semi tractor)
- Trailer extinguishers (equipment · lowboy · tag · utility · office · storage · fuel)
- Job trailer extinguishers
- Office extinguishers
- Storage building extinguishers
- Generator extinguishers
- Welding truck extinguishers
- Temporary facility extinguishers
- Emergency equipment extinguishers
- Yard extinguishers
- Wall-mount (permanent facility)

All of these are already representable via
`FireExtinguisherCreate.location_kind + location_value` — no field
additions required for Phase A.

## 5 · Extinguisher types already in scope (per `FireExtinguisherCreate.type`)

- ABC (multipurpose dry chemical) — default
- CO2 (electrical)
- BC (dry chemical)
- Class D (combustible metals)
- Class K (kitchen)
- Water mist
- Wet chemical

The existing model is a free-string `type`; Phase A should tighten this
to a closed-set enum aligned with the taxonomy extension.

## 6 · Related life-safety / emergency equipment (Phase A scope decision)

Out of Phase A scope but recorded here for continuity:

- **Smoke detectors / CO alarms** — permanent facility equipment, not
  currently on the register.
- **Emergency lights / exit signs** — permanent facility equipment,
  same.
- **Fire hoses / hose cabinets** — not currently tracked; would
  require its own type.
- **AEDs** — currently not tracked in any register.
- **Emergency showers / eyewash stations** — currently not tracked.
- **First aid kits** — inspection line in DVIR/Pre-Op but no register.

**Decision:** Track 19.62 Phase A promotes **fire extinguishers only**.
Broader life-safety expansion is deferred to a follow-up track. Do not
scope-creep.

## 7 · Count summary

- **1** duplicate collection (`db.fire_extinguishers`)
- **1** dedicated backend router (13 endpoints incl. attachments/import)
- **3** primary frontend pages (register · import · manage dialog)
- **8** consumer-side integrations (digest · reports · CAs · signals ·
  notifications · global search · where-used · portal continuity)
- **0** entries in canonical asset taxonomy v1.0.0 for fire protection
- **~11** distinct location kinds already represented
- **~7** extinguisher types already in scope

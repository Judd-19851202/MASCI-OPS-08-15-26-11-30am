# TRENCH SAFETY OPERATIONS SYSTEM — ARCHITECTURE

**Phase 2-prep doc · companion to PHASE 1 surface review**
**Status:** PROPOSED — awaiting operator approval before Phase 2 code

This document captures the data-model and integration architecture *before* any code is written. It is the single contract for every subsequent phase.

---

## 1. Two-collection model

### 1.1 `db.trench_safety_assets` (NEW — MASCI physical units)

One document per **physical** unit (TB-01 … TB-07 today, and any future end panels / spreaders / shores).

```python
{
  "id": "<uuid>",                 # primary key (never changes)
  "asset_id": "TB-07",            # MASCI-stamped tag (never changes)
  "asset_category": "Trench Safety",
  "asset_type": "Trench Box",     # Trench Box | End Panel | Spreader Bar |
                                  #  Hydraulic Shore | Slide Rail System |
                                  #  Trench Jack | Ladder | Accessory

  # General
  "manufacturer": "",
  "model": "",
  "serial_number": "",            # "" + missing_serial_number=True if unknown
  "year_manufactured": null,
  "owner": "MASCI",
  "purchase_date": null,
  "purchase_cost": null,
  "notes": "",

  # Physical
  "size": "8x24",                 # display label (e.g. "8' x 24'")
  "length_ft": null,
  "width_min_ft": null,
  "width_max_ft": null,
  "height_ft": null,
  "weight_lbs": null,
  "rated_depth_ft": null,
  "rated_soil_type": "",          # "A" | "B" | "C-60" | "C-80" | ""
  "adjustable_range": "",
  "capacity": "",

  # Appearance
  "color": "Green",
  "paint_condition": "",          # Excellent | Good | Fair | Poor
  "corrosion_level": "",          # None | Light | Moderate | Heavy

  # Condition / Status
  "condition": "Fair",            # Excellent | Good | Fair | Poor | Out Of Service
  "operational_status": "Available", # Available | Assigned | In Transport |
                                     # Inspection Hold | Repair | Retired

  # Location
  "current_location": "Yard",
  "current_project_id": null,
  "current_project_name": null,
  "assigned_to_name": null,
  "assigned_to_role": null,
  "yard_location": "MASCI Yard",

  # Linked manufacturer reference (existing trench_boxes row)
  "manufacturer_ref_id": null,    # FK → db.trench_boxes.id (optional)

  # Tabulated data link (PDF stored in trench_box_files scope)
  "tabulated_data_file_id": null,
  "tabulated_data_filename": "",
  "tabulated_data_missing": true, # flips to false on first link

  # System
  "qr_code_value": "TB-07",
  "qr_url": "https://mascidocs.com/trench-safety/assets/TB-07",
  "last_inspection_at": null,
  "next_inspection_due": null,
  "last_repair_at": null,
  "certification_expires_at": null,

  # Data-quality flags
  "missing_serial_number": false,
  "missing_manufacturer": false,
  "needs_review": false,

  # Lifecycle
  "is_active": true,
  "retired_at": null,
  "retired_reason": null,
  "created_at": "…",
  "updated_at": "…",
  "created_by": "<email>",
  "updated_by": "<email>"
}
```

### 1.2 `db.trench_boxes` (EXISTING — manufacturer reference)

UNCHANGED. Continues to hold the manufacturer/model spec sheets (Speed Shore, Trench Tech, etc.). `trench_safety_assets.manufacturer_ref_id` links to these rows when a physical unit's manufacturer/model matches a known reference.

### 1.3 `db.equipment_master` mirror row

For every active row in `trench_safety_assets`, a thin mirror in `equipment_master`:
```python
{
  "id": "<same uuid as trench_safety_assets.id>",
  "asset_id": "TB-07",
  "category": "Trench Safety",
  "type": "Trench Box",
  "label": "TB-07 · 8'x24' Green Trench Box",
  "location": "<mirrors trench_safety_assets.current_location>",
  "is_active": true,
  "linked_collection": "trench_safety_assets",
  …existing equipment_master fields…
}
```
This wires the asset into global search, supervisor pickers, asset_transfers, and dispatch automatically. `location` stays in lockstep with the source row via a single write-side helper.

---

## 2. Sub-collections (NEW)

| Collection | Purpose | Key fields |
|---|---|---|
| `db.trench_safety_photos` | per-asset photos | `asset_id`, `category`, `ref` (photo_storage ref), `uploaded_by`, `uploaded_at`, `caption`, `linked_inspection_id`, `linked_repair_id` |
| `db.trench_safety_inspections` | inspection records | `asset_id`, `inspection_type` (daily/monthly/annual), `inspector_name`, `inspector_role`, `checklist[]`, `result` (Pass/Fail/Pending), `photos[]`, `findings`, `corrective_actions`, `competent_person_confirmed`, `submitted_at` |
| `db.trench_safety_repairs` | repair records | `asset_id`, `reported_by`, `issue_description`, `photos[]`, `repair_vendor`, `repair_cost`, `status` (Open/In Progress/Completed), `completion_notes`, `requires_reinspection`, `opened_at`, `closed_at` |
| `db.trench_safety_deployments` | assignment history | `asset_id`, `project_id`, `project_name`, `assigned_by`, `assigned_at`, `returned_by`, `returned_at`, `source` (Manual/DailyReport/ProjectEquipment/Dispatch/Admin), `condition_at_assign`, `condition_at_return` |
| `db.trench_safety_certifications` | annual/manufacturer certifications | `asset_id`, `cert_type`, `issued_by`, `issued_at`, `expires_at`, `file_ref` (photo_storage) |
| `db.trench_safety_qr_scans` | QR scan telemetry | `asset_id`, `scanned_at`, `scanned_by` (nullable for anon), `user_agent`, `context` |

**Audit events**: REUSE `db.audit_events` with `kind` values:
`trench_asset_created`, `…edited`, `…retired`, `…status_changed`, `…inspection_started`, `…inspection_submitted`, `…inspection_passed`, `…inspection_failed`, `…repair_opened`, `…repair_updated`, `…repair_completed`, `…assigned`, `…returned`, `…transport_started`, `…transport_completed`, `…cert_uploaded`, `…tabdata_linked`, `…ocr_accepted`, `…ocr_corrected`, `…ocr_rejected`, `…qr_generated`, `…qr_scanned`, `…photo_uploaded`.

---

## 3. API surface (new endpoints under `/api/trench-safety/*`)

### 3.1 Public

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/trench-safety/assets/{asset_id}/public` | Field-safe view: id, type, size, status, last_inspection, tabulated_data_url, safety_warnings — NO admin data |
| `POST` | `/api/trench-safety/qr-scan` | Records a scan (no auth required) |
| `POST` | `/api/trench-safety/damage-report` | Anonymous damage-report intake (matches existing public-POST pattern, rate-limited) |

### 3.2 Any portal token (read)

| Method | Path | Use |
|---|---|---|
| `GET` | `/api/trench-safety/dashboard` | aggregate counts |
| `GET` | `/api/trench-safety/assets` | list with filters |
| `GET` | `/api/trench-safety/assets/{id}` | full record |
| `GET` | `/api/trench-safety/assets/{id}/inspections` | list |
| `GET` | `/api/trench-safety/assets/{id}/repairs` | list |
| `GET` | `/api/trench-safety/assets/{id}/deployments` | list |
| `GET` | `/api/trench-safety/assets/{id}/photos` | list |
| `GET` | `/api/trench-safety/assets/{id}/audit` | list audit_events for this asset |
| `GET` | `/api/trench-safety/reports/{report_type}` | inventory/inspection/repair/deployment/missing-data |

### 3.3 Safety + Admin (write)

| Method | Path | Use |
|---|---|---|
| `POST` | `/api/trench-safety/assets` | create |
| `PUT` | `/api/trench-safety/assets/{id}` | edit |
| `POST` | `/api/trench-safety/assets/{id}/retire` | retire |
| `POST` | `/api/trench-safety/assets/{id}/inspections` | submit inspection |
| `POST` | `/api/trench-safety/assets/{id}/photos` | upload photo |
| `POST` | `/api/trench-safety/assets/{id}/link-tabulated-data` | link existing trench_box_file |
| `POST` | `/api/trench-safety/assets/{id}/certifications` | upload certification |
| `POST` | `/api/trench-safety/assets/{id}/ocr-extract` | OCR a serial-plate photo |
| `POST` | `/api/trench-safety/assets/{id}/ocr-accept` | accept OCR value |

### 3.4 Shop + Admin (repair)

| Method | Path | Use |
|---|---|---|
| `POST` | `/api/trench-safety/assets/{id}/repairs` | open repair |
| `PATCH` | `/api/trench-safety/repairs/{repair_id}` | update repair |
| `POST` | `/api/trench-safety/repairs/{repair_id}/complete` | close repair |

### 3.5 Dispatch + Admin (movement)

Reuses `/api/asset-transfers` from existing routes — no new endpoints. Trench-safety assets participate by virtue of their `equipment_master` mirror row.

### 3.6 Project / Supervisor (assignment)

Reuses existing daily-report and project-equipment endpoints. The write hook in those routes triggers `assign_trench_asset_to_project()` server-side when the equipment-master id resolves to `category=Trench Safety`.

---

## 4. Frontend structure (new)

```
/app/frontend/src/pages/trench_safety/
├── TrenchSafetyHub.jsx          (dashboard, 7-tile)
├── TrenchSafetyAssetsList.jsx   (filterable list)
├── TrenchSafetyAssetDetail.jsx  (single-asset workbench)
├── TrenchSafetyInspections.jsx  (inspections list/queue)
├── TrenchSafetyRepairs.jsx      (repairs list)
├── TrenchSafetyDeployments.jsx  (deployments list)
├── TrenchSafetyCertifications.jsx
├── TrenchSafetyTabulatedData.jsx (re-host of existing TrenchBoxes.jsx content)
├── TrenchSafetyReports.jsx
├── TrenchSafetyQrLanding.jsx    (mobile QR public landing)
└── admin/
    ├── AdminTrenchSafety.jsx    (admin overview + management)
    └── AdminTrenchAssetEditor.jsx

/app/frontend/src/components/trench_safety/
├── AssetStatusBadge.jsx
├── ConditionBadge.jsx
├── InspectionChecklist.jsx
├── RepairForm.jsx
├── PhotoGallery.jsx
├── QrCodeCard.jsx
├── TabulatedDataLinker.jsx
├── OcrSerialPlateExtractor.jsx
├── DeploymentHistoryTable.jsx
├── AuditTrailPanel.jsx
└── CoachingCard.jsx
```

---

## 5. Routing additions

```
/safety/trench-safety                 → TrenchSafetyHub
/safety/trench-safety/assets          → TrenchSafetyAssetsList
/safety/trench-safety/assets/:id      → TrenchSafetyAssetDetail
/safety/trench-safety/inspections     → TrenchSafetyInspections
/safety/trench-safety/repairs         → TrenchSafetyRepairs
/safety/trench-safety/deployments     → TrenchSafetyDeployments
/safety/trench-safety/certifications  → TrenchSafetyCertifications
/safety/trench-safety/tabulated-data  → TrenchSafetyTabulatedData (re-host of current /trench-boxes)
/safety/trench-safety/reports         → TrenchSafetyReports
/trench-safety/assets/:assetId        → TrenchSafetyQrLanding (PUBLIC — mobile QR landing)
/admin/safety/trench-safety           → AdminTrenchSafety
/shop/trench-safety                   → TrenchSafetyRepairs (Shop view)

/trench-boxes (LEGACY)                → redirects to /safety/trench-safety/tabulated-data
```

---

## 6. Permission matrix

| Role | List | Detail | Edit | Inspect | Repair | Assign | Move | Admin |
|---|---|---|---|---|---|---|---|---|
| Public (no token) | NO* | QR-landing only | NO | NO | Damage report only | NO | NO | NO |
| Foreman/Field Leadership | YES | YES | NO | Daily only | Report | NO | NO | NO |
| PM / Superintendent | YES | YES | NO | Daily/Monthly | Report | YES | NO | NO |
| Safety | YES | YES | YES | All | View | View | View | NO |
| Shop | YES | YES | NO | NO | FULL | NO | View | NO |
| Dispatch | YES | YES | NO | NO | NO | NO | FULL | NO |
| Admin | YES | YES | YES | YES | YES | YES | YES | YES |

*Public list view is not exposed — only the per-asset QR landing is. Prevents anonymous fleet enumeration.

---

## 7. Initial seed (Phase 2)

Seven physical units. Idempotent — re-run safe:

| asset_id | size | serial | color | condition | missing_serial | needs_review |
|---|---|---|---|---|---|---|
| TB-01 | 6x24 | C080102 | Brown/Rust | Fair | NO | NO |
| TB-02 | 7x8 | 29809 | Orange | Good | NO | NO |
| TB-03 | 4x24 | 10087437 | Green | Fair | NO | NO |
| TB-04 | 8x16 | 6890902 | Brown/Rust | Fair | NO | NO |
| TB-05 | 8x16 | TBD | Brown/Rust | Fair | **YES** | **YES** |
| TB-06 | 4x24 | 40612 | Orange | Good | NO | NO |
| TB-07 | 8x24 | C078079 | Green | Fair | NO | NO |

Each seed row also writes a matching `equipment_master` mirror row.

---

## 8. Backups / restore

Add to `/app/backend/server.py` line 7918 — `_RESTORE_SAFETY_AUX` set:
```
_RESTORE_SAFETY_AUX = {
  "equipment_units",
  "job_hazard_plans",
  "trench_boxes",
  # NEW
  "trench_safety_assets",
  "trench_safety_photos",
  "trench_safety_inspections",
  "trench_safety_repairs",
  "trench_safety_deployments",
  "trench_safety_certifications",
  "trench_safety_qr_scans",
}
```

Without this, the new collections are lost on restore. CRITICAL.

---

## 9. OCR (Phase 10) — integration approach

User has not yet authorised an OCR vendor. Two implementable paths:

| Path | Pros | Cons |
|---|---|---|
| **A. Emergent universal LLM key (OpenAI Vision)** | Already in env, multi-modal, accurate on serial plates | Cost per call |
| **B. Self-hosted Tesseract** | Free, runs on-pod | Less accurate on weathered plates |

**Recommendation:** Path A via the existing emergent integrations playbook. Will route through `integration_playbook_expert_v2` before any code.

OCR always writes to `extracted_value` + `confidence` and NEVER overwrites a verified field without the `/ocr-accept` call.

---

## 10. Open questions for operator (need answers before Phase 2)

1. **QR-code generation library** — confirm `qrcode` PyPI package (already in `/app/backend/photo_storage`? Need to verify) OR client-side JS lib `qrcode.react`.
2. **OCR path** — confirm Path A (OpenAI Vision via emergent key) or Path B (Tesseract).
3. **"In Transport" status authority** — when Dispatch moves a TB, do they trigger transport via the existing `asset_transfers` flow (recommended), or do we add a trench-safety-specific transport action?
4. **`/trench-boxes` URL** — keep as redirect indefinitely, or sunset after N days?
5. **Phase delivery cadence** — confirm: do you want Phase 2+3+4 done in **this session** (a hard push, no UI polish guarantees) OR Phase 2 only with a clean break for review?

Default if no answers: QR via `qrcode.react`, OCR Path A, transport via asset_transfers, /trench-boxes permanent redirect, Phase 2 only this session.


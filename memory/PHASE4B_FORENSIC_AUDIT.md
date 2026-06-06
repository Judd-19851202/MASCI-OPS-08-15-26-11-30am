# TRENCH SAFETY · PHASE 4B — FORENSIC AUDIT

**Phase:** 4B — Inspections / Holds / Certifications / Alerts
**Date:** 2026-02 (preview pod)
**Status:** Audit complete · architecture decisions surfaced · build pending user authorization on key choices.

---

## 0. Mandate

> "DISCOVER FIRST. BUILD SECOND. NO DUPLICATE SYSTEMS. NO PARALLEL WORKFLOWS. NO NEW DATABASES UNLESS ABSOLUTELY REQUIRED."

Every existing subsystem that touches inspection / hold / certification / safety / shop / dispatch / equipment / audit / alert / notification surfaces has been read and catalogued below.

---

## 1. What Already Exists (Trench Safety Domain)

### 1.1 Inspections (Phase 2 — DONE)
| Item | Location | Notes |
|------|----------|-------|
| Collection | `db.trench_safety_inspections` | Persists every submission |
| Model | `routes/trench_safety/_models.py::InspectionSubmit` + `InspectionChecklistItem` | Already supports checklist + photos + findings + corrective_actions + result |
| Types | `INSPECTION_TYPES = ("Daily Visual", "Monthly Competent Person", "Annual Review")` | **Missing the directive's Special / Damage / Return types.** |
| Results | `INSPECTION_RESULTS = ("Pass", "Fail", "Pending Review")` | OK as-is |
| POST | `POST /api/trench-safety/assets/{ident}/inspections` (require_safety_or_admin) | Wired in `inspections.py` |
| GET | `GET /api/trench-safety/assets/{ident}/inspections` (require_any_portal) | Wired |
| Side-effects | Fail → `operational_status = "Inspection Hold"`. Monthly/Annual Pass on a held asset → `Available`. | **Single state machine on `asset.operational_status`.** |
| Mirror | `upsert_equipment_master_mirror` runs after every inspection write | `equipment_master.operational_status` stays in lockstep |
| Audit | `audit_events` rows: `trench_asset_inspection_submitted` / `trench_asset_inspection_passed` / `trench_asset_inspection_failed` | Single audit stream — no duplicate logs |

### 1.2 Repairs (Phase 2 — DONE)
| Item | Location | Notes |
|------|----------|-------|
| Collection | `db.trench_safety_repairs` | Open → In Progress → Completed |
| Model | `RepairCreate` / `RepairUpdate` with `requires_reinspection` flag | Already integrates with the hold engine |
| POST open | `POST /api/trench-safety/assets/{ident}/repairs` (require_shop_or_admin) | When opened → asset moves to `Repair` |
| PATCH | `PATCH /api/trench-safety/repairs/{id}` | |
| Complete | `POST /api/trench-safety/repairs/{id}/complete` | Requires-reinspection → `Inspection Hold`; otherwise `Available` (unless other open repair exists) |

### 1.3 Status / Hold State Machine (Phase 2 — DONE)
| Item | Location | Notes |
|------|----------|-------|
| Enum | `OPERATIONAL_STATUSES = ("Available", "Assigned", "In Transport", "Inspection Hold", "Repair", "Retired")` | **Single source of truth.** |
| Validator | `_helpers.validate_status_transition` | Blocks Available exits from Hold/Repair; Retired is terminal |
| Hold-aware writes | `inspections.submit_inspection`, `repairs.open_repair`, `repairs.complete_repair`, `deployments.assign_to_project` (409 if Hold/Repair/Retired) | All gated by the same state machine |
| Manual status change | `POST /api/trench-safety/assets/{ident}/status` | Admin-only |

### 1.4 Certifications (Phase 2 — STUBBED ONLY)
| Item | Status |
|------|--------|
| Collection | `db.trench_safety_certifications` is declared in the restore set + indexes are reserved, but **no endpoints exist yet** |
| Field on asset | `asset.certification_expires_at` exists in the schema | Always null today (no upload path) |
| Dashboard counter | `dashboard.py` already counts `certs_expiring` (≤30 day window) | Wired but never reads documents — falls back to the single date on the asset |

### 1.5 Dashboard / Alerts (Phase 2 — PARTIAL)
| Item | Location | Notes |
|------|----------|-------|
| Endpoint | `GET /api/trench-safety/dashboard` | Aggregates counts |
| Alert fields | `alerts.missing_serial_number` / `missing_manufacturer` / `missing_tabulated_data` / `needs_review` / `open_repairs` / `inspections_due` / `certifications_expiring` | Already exposed — derived (no separate alerts collection) |
| **Missing** | Alert destinations / no `alerts` endpoint that drives Safety Portal banners · no Project-View surfacing · no per-alert severity / link |

### 1.6 Audit Trail (Phase 2 — DONE)
| Item | Location | Notes |
|------|----------|-------|
| Collection | `db.audit_events` (shared platform-wide) | `kind` prefix `trench_*` |
| Helper | `_helpers.write_audit(db, kind, asset_id, actor, detail)` | Single writer — every Phase 4B addition routes through this |

### 1.7 Public Field Surface (Phase 3.5 — DONE)
| Item | Notes |
|------|-------|
| `GET /api/trench-safety/public/lookup/{id}` | Returns `public_view(asset)` — already exposes `operational_status`, `certification_expires_at`, `tabulated_data_missing` |
| Read-only banners | Field crew already sees "Inspection Hold — DO NOT USE" / "Repair" / "Missing Serial" etc. | These banners must extend to the new hold kinds without code duplication |

---

## 2. What Exists Outside Trench Safety That Phase 4B Must Honor

| Subsystem | Phase 4B implication |
|-----------|----------------------|
| `equipment_master` (Phase 4A enriched mirror) | Every Phase 4B status / hold / certification change MUST keep the mirror in lockstep via the single existing helper `upsert_equipment_master_mirror`. |
| Existing platform `audit_events` collection | Single audit stream — Phase 4B must NOT create a parallel `trench_safety_audit_events` collection. |
| Existing equipment-inspection pipeline (`routes/equipment.py` — DVIR / Pre-Op) | Entirely separate domain (fleet vehicles). Phase 4B must NOT bleed into this pipeline. |
| Existing safety holds elsewhere (MaintainX `asset_holds` collection) | Read-first only — MaintainX side is a stub. Phase 4B's holds live on the trench asset row and the new `trench_safety_holds` collection (see §3.2). |
| Dispatch (`routes/dispatch_*.py`) | Phase 4B must surface the same `operational_status` to dispatch via the existing mirror — no new dispatch routes. |
| Project dashboards (`PmProjectDetail` + `TrenchSafetyOnProjectPanel`) | The panel built in Phase 4A reads `/api/trench-safety/by-project` — Phase 4B must enrich this same response with inspection / certification / hold status; no new project route. |
| Notifications platform (`routes/admin_operator_digest.py`, `routes/admin_digest_config.py`) | Out of scope for 4B per directive § "DO NOT BUILD REPAIR SYSTEM YET" parity. Phase 4B alerts are surfaced **in-app only** (Safety Portal banners + Asset Detail + Project panel + Public field-view banner). Email/SMS deferred. |
| Search (`routes/global_search.py`) | Already reads `equipment_master` — Phase 4B inherits this for free once the mirror carries the new fields. |

---

## 3. Architecture Decisions Phase 4B Must Confirm

### 3.1 Hold types vs single state machine — **THE biggest decision**

The directive lists:
- **Safety Hold** (critical defect)
- **Certification Hold** (missing / expired cert)
- **Maintenance Hold** (open repair)
- **Inspection Hold** (failed inspection — already exists)

The existing state machine uses ONE `operational_status` field with `Inspection Hold | Repair | Retired` as the only blocking states.

**Two architectures honor "no duplicate status systems":**

**Option A — Extend the single enum (RECOMMENDED).**
- Rename `Repair` → `Maintenance Hold` (operational meaning is identical; just clearer naming).
- Add `Safety Hold` + `Certification Hold` to `OPERATIONAL_STATUSES`.
- Keep `Inspection Hold` as-is.
- Introduce a hold-priority hierarchy in `_helpers.derive_status(asset)` — given multiple concurrent holds (e.g., expired cert AND failed inspection), the asset shows the highest-severity one: **Safety > Certification > Maintenance > Inspection > Operational**.
- Pros: single field, single mirror, dispatch + project + equipment master see one truth.
- Cons: requires migration of `Repair` strings in existing rows + the Phase 2 test suite.

**Option B — Add a `holds` array alongside `operational_status`.**
- `asset.holds = [{kind: "Safety", opened_at, opened_by, reason, cleared_at, cleared_by}]`
- `operational_status` becomes a derived view from the highest-priority active hold.
- Pros: full hold history on the asset doc; no Phase 2 string churn.
- Cons: two related fields to keep in sync — drifts from "single source of truth" if both writable.

**Both architectures also need:** a `trench_safety_holds` collection (history of every open/clear event — audit detail beyond the asset doc). This is **NOT a duplicate status system** — it's the audit trail of the state machine, mirroring how `trench_safety_deployments` is the history of `current_project_*`.

**Recommendation:** Option A + the `trench_safety_holds` history collection. Migration path: existing rows with `operational_status = "Repair"` get rewritten to `"Maintenance Hold"` in a single idempotent seed-time fix.

> **🔴 USER DECISION REQUIRED — pick Option A or B.**

### 3.2 Certification model

Net-new domain. Architecture:

- `db.trench_safety_certifications` — one row per certification document.
  - `id`, `asset_id`, `asset_uuid`, `kind` (Manufacturer / Annual Inspection / Engineering Letter / Repair Certification / Special), `issuer`, `issued_at`, `expires_at`, `document_ref` (filename / blob ref — uses existing `safety_documents` pattern), `notes`, `status` (Active / Expired / Superseded / Revoked), `created_at`, `created_by`.
- Derived on the asset: `active_certifications` summary + `certification_status` ∈ {OK, Due Soon (90d), Due Soon (60d), Due Soon (30d), Expired, Missing}.
- Document storage: reuse the **existing** `safety_documents` collection's inline-base64 pattern (15 MB cap) — no new storage system.
- Endpoints: `GET/POST /api/trench-safety/assets/{id}/certifications`, `PATCH/DELETE /api/trench-safety/certifications/{cert_id}`, `POST /api/trench-safety/certifications/{cert_id}/revoke`.

### 3.3 Alerts

**No new collection.** Alerts are a derived projection of asset state, exposed as:

- `GET /api/trench-safety/alerts` — single endpoint returning every active alert across the fleet, with `{asset_id, kind, severity, opened_at, link, message}`. Kinds: `due_soon_90`, `due_soon_60`, `due_soon_30`, `expired_certification`, `missing_certification`, `failed_inspection`, `critical_damage`, `hold_applied`, `hold_cleared`, `inspection_overdue`.
- Sources:
  - Inspection alerts → `trench_safety_inspections` (latest per asset).
  - Certification alerts → `trench_safety_certifications` (closest-expiring per kind per asset).
  - Hold alerts → `trench_safety_holds` (open holds) + asset.operational_status.
  - Damage alerts → public damage reports (existing `trench_safety_repairs` rows opened with `kind="Damage"`).
- Destinations: Safety Portal Trench Hub banner · Asset Detail header · Project View `TrenchSafetyOnProjectPanel` (extended) · Public QR field-view banner (read-only).

### 3.4 Special / Damage / Return Inspection types

Add 3 new strings to `INSPECTION_TYPES`:
- `"Special Inspection"` — triggered by manager/safety; clears no holds automatically; result still Pass/Fail.
- `"Damage Inspection"` — triggered by a damage report or post-incident; if Fail → auto-creates a Repair stub (§ 3.5).
- `"Return Inspection"` — triggered when an asset returns from a project; Pass → keep Available; Fail → Inspection Hold (existing logic still applies).

Severity field added to inspection result: `severity ∈ {None, Minor, Major, Critical}`. Critical → Safety Hold (not just Inspection Hold).

### 3.5 Shop Integration (per directive § "DO NOT BUILD REPAIR SYSTEM YET")

We do NOT build a shop repair UI in Phase 4B. We do:

- Auto-create a `repair_stub` on every Fail inspection with severity ≥ Major. Stub = a `trench_safety_repairs` row with `status="Open"` and `kind="repair_recommendation"`. Shop's existing `GET /api/trench-safety/repairs?status=Open` already lists these (Phase 2 endpoint). Phase 6 will add the management UI.
- Set `asset.shop_visibility_flag = true` when any repair stub is open — surfaces in the existing equipment_master mirror so Shop's existing equipment-down indicators light up for free.

---

## 4. Acceptance Matrix (REALITY CERTIFICATION — what must be proven)

| # | Scenario | Expected effect |
|---|----------|-----------------|
| 1 | Submit Daily Pass | asset.last_inspection_at updates; no hold; audit row written |
| 2 | Submit Daily Fail (severity=Minor) | Inspection Hold; alert kind="failed_inspection"; repair_stub NOT created |
| 3 | Submit Daily Fail (severity=Major) | Inspection Hold; alert; repair_stub Open created |
| 4 | Submit Daily Fail (severity=Critical) | Safety Hold (NOT Inspection Hold); alert kind="critical_damage"; repair_stub Open created |
| 5 | Submit Monthly Pass on Inspection-Hold asset | Hold cleared → Available; audit "hold_cleared" |
| 6 | Submit Monthly Fail | Inspection Hold; existing audit kind |
| 7 | Add certification with expires_at 80 days out | alert kind="due_soon_90" |
| 8 | Add certification with expires_at 25 days out | alert kind="due_soon_30" |
| 9 | Add certification with expires_at in past | Certification Hold applied; alert kind="expired_certification" |
| 10 | Asset with zero certifications and required=true | Certification Hold; alert kind="missing_certification" |
| 11 | Clear Certification Hold by uploading active cert | Asset returns to highest remaining hold OR Available |
| 12 | Asset with Critical damage report + expired cert | Safety Hold wins display (priority); both alerts present |
| 13 | Project dashboard panel | Shows current status, inspection status, cert status, open holds, damage reports, last inspection, next due |
| 14 | Equipment Master mirror | All new statuses propagate; current_project_* untouched |
| 15 | Public field view | Field crew sees "DO NOT USE — Safety Hold" / "DO NOT USE — Certification Expired" banners; no admin data |

---

## 5. Files / Tests / Docs Plan

### Backend (new + modified)
- **NEW** `routes/trench_safety/certifications.py` — full CRUD + revoke
- **NEW** `routes/trench_safety/holds.py` — open/clear hold lifecycle + history
- **NEW** `routes/trench_safety/alerts.py` — single derived-alerts endpoint
- **MOD** `routes/trench_safety/_models.py` — new types, severity, hold reason model, certification model
- **MOD** `routes/trench_safety/_helpers.py` — new `derive_displayed_status(asset)` helper, hold-priority constants, certification status calc
- **MOD** `routes/trench_safety/inspections.py` — severity field, Special/Damage/Return types, shop stub on Fail≥Major, Safety Hold on Critical
- **MOD** `routes/trench_safety/dashboard.py` — surface new alert kinds in the aggregate
- **MOD** `routes/trench_safety/operations.py` (by-project) — enrich response with inspection / cert / hold status per asset
- **MOD** `routes/trench_safety/__init__.py` — wire new sub-routers
- **MOD** `routes/trench_safety/seed.py` — idempotent rename of existing `"Repair"` strings → `"Maintenance Hold"` if Option A chosen

### Frontend (new + modified)
- **NEW** `pages/trench_safety/TrenchSafetyCertifications.jsx` — list + upload + revoke
- **NEW** `pages/trench_safety/TrenchSafetyAlerts.jsx` — alerts inbox
- **NEW** `pages/trench_safety/InspectionSubmitModal.jsx` — drives the new 6-type inspection submission with severity, photos, signature
- **MOD** `pages/trench_safety/TrenchSafetyAssetDetail.jsx` — Active Holds card, Certifications card, status-derived banner, new "Log Inspection" CTA
- **MOD** `pages/trench_safety/TrenchSafetyHub.jsx` — alert tile linking to alerts page
- **MOD** `components/trench/TrenchSafetyOnProjectPanel.jsx` — surface hold + cert + alert summary per asset
- **MOD** `pages/trench_safety/PublicTrenchSafetyDashboard.jsx` + `TrenchSafetyQrLanding.jsx` — extend "DO NOT USE" banner to new hold kinds (read-only)
- **MOD** `lib/i18n.js` — Spanish translations for every new string

### Tests
- **NEW** `tests/test_trench_safety_phase4b.py` — covers all 15 acceptance rows
- Re-run Phase 2 + Phase 4A regression (44 tests) to prove no regression

### Certification docs (per directive)
- `PHASE4B_FORENSIC_AUDIT.md` ← **THIS FILE**
- `PHASE4B_ARCHITECTURE.md` ← to be written after Option A/B confirmed
- `PHASE4B_HOLD_ENGINE_CERT.md`
- `PHASE4B_CERTIFICATION_ENGINE_CERT.md`
- `PHASE4B_ALERT_CERT.md`
- `PHASE4B_PROJECT_IMPACT_CERT.md`
- `PHASE4B_REALITY_CERTIFICATION.md`

---

## 6. Blocking Questions for the Operator

1. **Option A vs B** for the hold architecture? (See § 3.1.)
2. **Photo + signature storage** for inspections: reuse existing `safety_documents` inline-base64 (15 MB cap), or introduce a tiny `trench_safety_inspection_photos` sub-collection? Recommend reuse.
3. **Certifications required by default?** Should TB-01…TB-07 be flagged "missing certification" on day one, or do we only enforce cert-hold for assets explicitly marked `requires_certification=true`? Recommend explicit flag — TB-01…TB-07 stay green until certs are uploaded.
4. **In-app alerts only for Phase 4B?** (No email / push.) Recommend yes — alerting platform is a Phase 9 deliverable.

Once these are confirmed I will write `PHASE4B_ARCHITECTURE.md` and begin the build.

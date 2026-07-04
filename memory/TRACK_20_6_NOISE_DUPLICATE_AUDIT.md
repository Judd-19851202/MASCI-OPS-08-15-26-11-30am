# TRACK 20.6 · Noise / Duplicate Audit — Fire Protection

**Legend:** KEEP · PROMOTE · ADAPT · EXTEND · RESTRICT · RETIRE · REMOVE.

## Data surfaces

| Surface | Verdict | Rationale |
|---|---|---|
| `db.fire_extinguishers` | **KEEP** (Phase A) · **RETIRE** (Phase B) | Duplicate asset registry (D-FP-01). Phase A tolerates; Phase B migrates to `equipment_master`. |
| `db.fire_extinguishers` inspection log | **KEEP** (Phase A) · **PROJECT ONTO BACKBONE** (Phase B) | Duplicate inspection log (D-FP-02). Phase B feeds `asset_service_events`. |
| Fire-ext attachments | **KEEP** (Phase A) · **CONSOLIDATE** (Phase B) | Duplicate attachment store (D-FP-03). Phase B migrates to `asset_documents`. |
| `db.operational_signals` (`fire_ext.fail`) | **KEEP** | Consumer-side signal; not duplicate storage. |
| `db.corrective_actions` (link type `fire_ext`) | **KEEP** | Link semantic, not identity. |
| `db.notifications` (`safety.fire_extinguishers` module) | **KEEP** | Consumer-side notification module. |
| `db.equipment_master` | **EXTEND (Phase B)** | Target for migration. |
| `db.asset_service_events` | **EXTEND (Phase B)** | Target for inspection projection. |
| `db.employee_records` | **EXTEND (Phase A)** | Additive record_type slugs for fire paper (5 new). |

## Backend routers

| Router | Verdict | Rationale |
|---|---|---|
| `backend/routes/safety_portal/fire_extinguishers.py` | **KEEP** in Phase A · **REPLATFORM as backwards-compat view** in Phase B | Do not touch in Phase A. In Phase B, keep endpoint contracts, rewire internals to spine. |
| `backend/routes/asset_spine.py` | **EXTEND (Phase A)** | Resolver falls back to `db.fire_extinguishers` when unit not found in `equipment_master`. |
| `backend/routes/employee_records.py` | **EXTEND (Phase A)** | Additive record_type slugs for fire paper. |
| `backend/routes/notifications.py` | **KEEP** | Existing fire-ext module unchanged. |
| `backend/routes/corrective_actions.py` (or wherever CA link types live) | **KEEP** | Existing `fire_ext` link type unchanged. |

## Frontend surfaces

| Surface | Verdict | Rationale |
|---|---|---|
| `SafetyFireExtinguishers.jsx` | **KEEP** | Safety-authoritative register. Cross-link into Asset Thread (Phase A). |
| `SafetyFireExtImport.jsx` | **KEEP** | Bulk import unchanged. |
| `SafetyFireExtManageDialog.jsx` | **KEEP** | Inspection dialog unchanged. |
| `SafetyDigest.jsx` (KPI `fire_extinguishers_overdue`) | **KEEP** | Consumer-side counter. |
| `SafetyReports.jsx` (fire-ext export) | **KEEP** | Export unchanged. |
| `SafetyCorrectiveActions.jsx` + `SafetyCaLinksManager.jsx` | **KEEP** | Link semantic unchanged. |
| `OperationalSignalsPanel.jsx` (`fire_ext.fail` mapping) | **KEEP** | Consumer-side. |
| `NotificationBell.jsx` | **KEEP** | Module label unchanged. |
| `GlobalSearch.jsx` + `WhereUsedPanel.jsx` | **KEEP** | Cross-linking unchanged. |
| `lib/portalContinuity.js` | **KEEP** | Portal continuity mapping unchanged. |
| `lib/inspectionSchema.js` (`fire_extinguishers` checkbox in DVIR/Pre-Op) | **KEEP** | Complementary — presence check, not identity. |
| `AdminAssetThread.jsx` (Track 19.61) | **EXTEND (Phase A)** | Add read-side adapter for fire-ext resolution + attention rule for overdue. |
| Various `topics/*.js` safety-talk content mentioning "fire extinguisher within 50 ft" etc. | **KEEP** | Educational content, not data. |

## Declared duplicate risks — recorded, NOT fixed here

- **D-FP-01** · Duplicate asset registry (`db.fire_extinguishers` vs
  `equipment_master`). **Phase B** retires.
- **D-FP-02** · Duplicate inspection log. **Phase B** projects onto
  backbone.
- **D-FP-03** · Duplicate attachment store. **Phase B** consolidates
  into `asset_documents`.
- **D-FP-04** · Fire Protection missing from canonical asset taxonomy.
  **Phase A** fixes (additive · v1.1.0).
- **D-FP-05** · Free-string extinguisher `type` (ABC/CO2/etc.) with no
  closed-set enforcement. **Phase A** tightens via crosswalk against the
  new taxonomy (server-side validation deferred to Phase B write-path).

## Non-defects (falsely reported by casual observers)

- **N-FP-01** · The `fire_extinguishers` line item on Pre-Op / DVIR
  inspection schemas is a **presence check by the operator**, not an
  inspection lifecycle. Complementary.
- **N-FP-02** · Multiple mentions of "fire extinguisher within 50 ft"
  in safety-talk topics (paving / grading / tack) are **educational
  content**, not data storage. Not a duplicate.
- **N-FP-03** · The digest KPI `fire_extinguishers_overdue` is a
  computed counter, not an identity store. Not a duplicate.
- **N-FP-04** · The CA link type `fire_ext` is a link semantic. Not a
  duplicate identity system.
- **N-FP-05** · The operational signal `fire_ext.fail` is an emitter
  namespace, not a duplicate storage. Not a defect.

## Dead / unused / orphaned

- **None found.** Every fire-protection surface has a live consumer.

## Recommendation

- **Zero surfaces retired in Phase A.**
- Five surfaces marked for **Phase B replatforming** (`db.fire_extinguishers` +
  its inspection log + its attachment store + the router as
  backwards-compat view + the frontend register cross-linked to the
  thread).
- One surface **EXTENDED** in Phase A (`employee_records` gets five
  additive fire-specific record_type slugs).
- One taxonomy **EXTENDED** in Phase A (v1.0.0 → v1.1.0 · additive).

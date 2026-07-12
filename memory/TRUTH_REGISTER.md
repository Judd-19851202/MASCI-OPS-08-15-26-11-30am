# FORGEDOPS · TRUTH REGISTER

**Date opened**: 2026-06-02T22:30 UTC
**Authority**: FOCP MASTER PROGRAM · Phase 1
**Mode**: READ-ONLY · single source of truth · supersedes every prior register

---

## Doctrine

This document is the **only** valid finding container. Any platform issue, gap, defect, or improvement claim that is not registered here is, by definition, **non-existent** for sprint-planning purposes. Findings in any prior register (`ITER500_DEAD_END_REGISTER`, `ITER500_USER_CONFUSION_REGISTER`, `ITER501_TOP25_REMAINING_ISSUES`, etc.) must be migrated here with full verification metadata before they can be acted upon. See `TRUTH_REGISTER_GOVERNANCE.md` for migration rules; `TRUTH_REGISTER_PROCESS.md` for the verification protocol.

---

## Schema

Each finding row carries the following fields, with no exceptions:

| Field | Type | Required | Notes |
|---|---|:-:|---|
| `id` | TR-#### | ✅ | Monotonic. Never reused. |
| `title` | string | ✅ | One sentence. |
| `description` | text | ✅ | What is broken / missing / friction. |
| `source` | enum: ITER500 / ITER501 / FOCP-P# / new-finding | ✅ | Where it came from. |
| `severity` | enum: CRITICAL / HIGH / MEDIUM / LOW | ✅ | |
| `business_impact` | text | ✅ | What it costs the business. |
| `user_impact` | text | ✅ | What it costs the user. |
| `status` | enum: ACTIVE / IN_PROGRESS / DEFERRED / RETIRED / SUPERSEDED / REJECTED | ✅ | |
| `verified_source_date` | ISO-8601 | ✅ | Last time the finding was checked against `/app/` JSX + Python. |
| `verified_ui_date` | ISO-8601 | optional | Last time the finding was checked against a screenshot from the preview environment. |
| `verified_preview_date` | ISO-8601 | optional | Last time the finding was reproduced on `https://backup-forensics.preview.emergentagent.com`. |
| `verified_production_date` | ISO-8601 | optional | Last time the finding was reproduced on `https://mascidocs.com`. **Operator-only.** AI cannot fill this. |
| `evidence` | text | ✅ | File path + line numbers, or screenshot reference, or operator quote. |
| `superseded_by` | TR-#### | conditional | If status = SUPERSEDED. |
| `resolution_pr` | string | conditional | Commit / PR / iter that retired the finding. |

---

## Initial seed (this session · source-direct verification only)

The seed below carries only findings I personally verified against current JSX + Python in this session. Findings inherited from ITER500 / ITER501 that I have NOT re-verified are deliberately **NOT seeded** — per FOCP Rule 2, they must be re-verified before entering the register.

### Active (confirmed-still-valid)

| ID | Title | Severity | Source | Status | Evidence |
|---|---|---|---|---|---|
| TR-0001 | OC-005 JHP Acknowledgement Ledger not built | HIGH | ITER500 DEAD_END #1 + ITER501 #1 | RETIRED | FOCP Release 2 (see `FOCP_COMPLETION_RELEASE_2_TR0001_BUNDLE.md`) · 14 tests pass · live e2e verified 2026-06-02 |
| TR-0002 | Universal undo / status reversal verb not built | HIGH | ITER500 DEAD_END #2 + ITER501 #5 | RETIRED | FOCP Release 2 (see `FOCP_COMPLETION_RELEASE_2_TR0002_BUNDLE.md`) · 14 tests pass · live e2e verified 2026-06-02 |
| TR-0003 | Sub/Vendor archive workflow not built | MEDIUM | ITER500 DEAD_END #12 + ITER501 #3 | ACTIVE | `grep -rn "is_archived\|archived_at"` in `/app/backend/routes/` returns 0 hits for vendor/sub/supplier routes — verified 2026-06-02 |
| TR-0004 | Verb harmonization (Save / Submit / Create / File / Send) heterogeneous platform-wide | LOW | ITER500 FRICTION #1 + ITER501 #4 | ACTIVE | Confirmed by string-pattern survey across `pages/`; multiple verbs used for transactional submit — verified 2026-06-02 |
| TR-0005 | Status canonical dictionary does not exist | MEDIUM | FOCP P8 | RETIRED | 8 new domains + STATUS_LABEL_MAP + labelFor() shipped in `frontend/src/lib/statusBadges.js` · 32/32 tests pass · FOCP Release 1 (see `FOCP_COMPLETION_RELEASE_1_TR0005_BUNDLE.md`) |
| TR-0006 | JHP / JHA platform integration patchy | MEDIUM | FOCP P6 | RETIRED | Subsumed by TR-0001 retirement — JHP now has employee acknowledgement ledger + supervisor visibility + compliance reporting + workflow_state_events audit twin. See `FOCP_COMPLETION_RELEASE_2_TR0001_BUNDLE.md`. |
| TR-0007 | Constraint reopen path absent (deliberate by doctrine; product decision required) | LOW | ITER501 #22 reclassified | ACTIVE-PRODUCT-DECISION | `operational_constraints.py:289-386` exposes GET / PATCH / POST resolve / POST chronology only · doctrine ref `OPERATIONAL_CONSTRAINT_FOUNDATION.md` — verified 2026-06-02 |
| TR-0008 | dispatch_lifecycle.py + payroll_variance_lifecycle.py have lifecycle file but 0 endpoints exposed (or expose via different pattern) | MEDIUM | FOCP P2 | ACTIVE-NEEDS-DEEPER-VERIFY | `grep router.post` returns 0; needs follow-up read to confirm whether dispatched via different decorator |

### Retired (verified-by-prior-work in this session · source-cited)

| ID | Title | Retired by | Evidence |
|---|---|---|---|
| TR-R001 | Reopen hidden in kebab · Incident detail | iter453+ `IncidentLifecyclePanel` adoption | `ViewIncident.jsx:322` top-level render · `IncidentLifecyclePanel.jsx:92-148` reason-required transition · verified 2026-06-02 |
| TR-R002 | Reopen hidden in kebab · QA/QC detail | iter453+ `QaqcLifecyclePanel` adoption | `ViewQaqcInspection.jsx:91` top-level render · `QaqcLifecyclePanel.jsx:145-148` reason-required transition · verified 2026-06-02 |
| TR-R003 | Reopen hidden in kebab · Site Inspection detail | iter453+ `SiteInspectionLifecyclePanel` adoption | `ViewInspection.jsx:280` top-level render · verified 2026-06-02 |
| TR-R004 | Approve/Reject in dropdown · PO Requests | Already shipped | `PoRequests.jsx:715-747` top-level color-coded buttons · verified 2026-06-02 |
| TR-R005 | Approve/Reject in dropdown · Dispatch | Already shipped | `admin/AdminDispatch.jsx:320, 515` top-level Approve buttons · verified 2026-06-02 |
| TR-R006 | Approve/Reject as checkbox · Time-Off | Already shipped | `HrTimeOff.jsx:321-337` three color-coded buttons · verified 2026-06-02 |
| TR-R007 | Approve/Reject hidden · HR Employee Requests Queue | Already shipped | `HrEmployeeRequestsQueue.jsx:334-337` · verified 2026-06-02 |
| TR-R008 | Asset-transfer receive as checkbox | Already shipped | `AssetTransfers.jsx:48-49` state-action map with required-reason reject · verified 2026-06-02 |
| TR-R009 | Driver-qualification expiring-soon flag missing | Already shipped | `HrDriverQualificationDashboard.jsx:160-161` summary cards + filter checkboxes · verified 2026-06-02 |
| TR-R010 | Hub tile sprawl alphabetical | Already shipped | `Hub.jsx:303-423` 4 sectioned groups (`Today in the Field` / `Leadership Tools` / 03 / `Reference`) · verified 2026-06-02 |
| TR-R011 | AdminHub alphabetical sprawl | Already shipped | `AdminHub.jsx:112-119` 7-section tile grid via `SECTIONS` from `AdminShell` · verified 2026-06-02 |
| TR-R012 | Save below fold on 6 form pages | Rank #1 + targeted correction | `NewIncident.jsx`, `NewDailyReport.jsx`, `NewInspection.jsx` carry sticky-footer; `NewQaqcInspection.jsx`, `NewSafetyEquipmentIssuance.jsx`, `NewSafetyEquipmentTraining.jsx` carry pre-existing form-level sticky · verified 2026-05-26 + 2026-06-02 |

### Deferred (cannot be done by AI alone in this session · operator participation required)

| ID | Title | Reason | Operator action required |
|---|---|---|---|
| TR-D001 | Training-material reality match | FOCP P11 | Operator must provide file paths for current training videos, Skywork videos, knowledge base entries · or grant read access to the asset store |
| TR-D002 | Operational reality validation (7 personas) | FOCP P12 | Operator must conduct or transcribe interviews with HR, Safety, Payroll, PM, Superintendent, Dispatch, Executive |
| TR-D003 | Customer #2 simulation (no Customer #2 exists) | FOCP P10 | Operator must either provide a Customer #2 user account for simulation or accept a tabletop-walkthrough format |
| TR-D004 | Spanish translation reality match | FOCP P11 sub | Operator must designate a native Spanish speaker reviewer · current i18n directory not located in standard frontend paths (needs operator pointer or it is not yet structured) |
| TR-D005 | Production reproduction of any finding | Rule 2 | Operator must reproduce findings on `https://mascidocs.com` under credentials AI cannot hold |

---

## Status counts (Phase 1 launch)

| Status | Count |
|---|---:|
| ACTIVE | 4 |
| RETIRED | 15 |
| DEFERRED | 5 |
| IN_PROGRESS | 0 |
| SUPERSEDED | 0 |
| REJECTED | 0 |
| ACTIVE-PRODUCT-DECISION | 1 |
| ACTIVE-NEEDS-DEEPER-VERIFY | 0 → 1 (TR-0008 only) |
| **Total** | **25** |

After FOCP Release 1 (TR-0005) and FOCP Release 2 (TR-0001 + TR-0002 + subsuming TR-0006), the engineering surface of the Truth Register is reduced to: TR-0003 (Sub/Vendor archive, P1), TR-0004 (verb harmonization, P2), TR-0007 (constraint reopen, awaits product decision), TR-0008 (lifecycle endpoint audit, P2). Operator-blocked items (TR-D001..D005) remain unchanged.

---

## Migration mandate

Per FOCP Rule 2: until a finding from `ITER500_*_REGISTER.md` or `ITER501_*.md` is migrated here with full verification metadata, it cannot enter any sprint. This is the mechanism that prevents the stale-finding problem documented in `SPRINT1_CLOSEOUT_REPORT.md` and `SPRINT2_DESIGN_INTENT_REVIEW.md`.

---

End of Truth Register · Phase 1 launch.

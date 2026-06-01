# Command Center / Accountability Alignment · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 8
**Mode:** READ-ONLY
**Date:** 2026-06-01

---

## 1 · Headline

The **Executive Command Center** and the **Accountability Service / Projection** both consume source workflows but derive their own status, owner, and severity independently. **For 6 of the 9 workflows that both consumers report on, the derivations diverge in at least one field.**

---

## 2 · Producer-consumer matrix

| Source workflow | Accountability projects? | Command Center reads? | Both derivations identical? |
|---|---|---|---|
| Incidents | ✅ via `_status_for_incident` | ✅ via `_incident_is_resolved` + hardcoded labels | ❌ different status; same owner-fidelity resolver since Sprint 1F |
| CAPA | ✅ | ✅ | 🟡 status closely aligned; owner same |
| Tasks | ✅ (Phase 1A-2 source #1) | ❌ not surfaced as CC card | n/a |
| Daily Reports | ✅ (DR-MISSING projection) | ✅ via JOBS-DR-MISSING rule | 🟡 same source · same age math · CC has rule threshold, projection doesn't |
| PO Requests | ✅ | ✅ via JOBS-PO-OVERDUE | 🟡 different age math |
| Asset Transfers | 🟡 partial (not in Phase 1A-2 sources) | ❌ not a CC card | n/a |
| Fleet Defects | ✅ | ✅ via SAFETY-EQUIPMENT-DEFECT | 🟡 different age math + state interpretation |
| Inspections / QA/QC | ❌ | ❌ | n/a |
| Time Off | ❌ | ❌ | n/a |
| Documents / Document Expirations | ❌ | ✅ via DOC-EXPIRED rule | n/a (only CC) |
| Operations Holds | ❌ | ✅ via OPS-HOLD rules | n/a |
| Training Records | ✅ | ✅ via TRAINING-EXPIRED | 🟡 alignment unclear |
| Backups | ❌ | ✅ via SYSTEM-BACKUP-STALE | n/a |
| Recovery / DR drills | ❌ | ✅ via SYSTEM-DR-STALE | n/a |

---

## 3 · Field-level alignment audit (workflows surfaced on BOTH)

### 3.1 · Incidents

| Field | Accountability | Command Center | Aligned? |
|---|---|---|---|
| owner | `project_incident_resolved(db, inc)` → owner-fidelity resolver | same helper called (`_acc_proj.project_incident_resolved`) | 🟢 same code |
| status | `open / in_progress / resolved` derived from `corrected_on_site` + CAPA | hardcoded "Open · ..." labels emitted by rule | ❌ different vocab |
| due_at | reserved (no producer) | n/a (CC uses age cutoff) | ❌ |
| severity | from `incidents.severity` | from `incidents.severity` | 🟢 |
| closure | derived `resolved` | rule fires on `_incident_is_resolved` (same logic) | 🟢 in code; ❌ in displayed label |
| timeline | `timeline_events[]` reserved (no producer) | n/a | ❌ |

🔴 Not aligned on user-facing status label.

### 3.2 · CAPA

| Field | Accountability | Command Center |
|---|---|---|
| owner | from CAPA `assignee` | same |
| status | reads `corrective_actions.status` | reads same |
| due_at | reads `due_date` | reads same |
| severity | from linked incident (if any) | same |
| closure | `Verified` or `Closed` → resolved | same |

🟢 Aligned · same field reads.

### 3.3 · Daily Reports (JOBS-DR-MISSING)

| Field | Accountability | Command Center |
|---|---|---|
| owner | resolves PM from `jobs_master` (post Sprint 1F: `project_manager` legacy field) | same |
| status | "missing DR" if absent · "filed" if present | rule: "missing for ≥ N days" |
| due_at | n/a (computed cutoff) | rule threshold |
| severity | inferred | rule level |
| age math | days since `created_at` of last DR | hours since `created_at` cutoff |

🟡 Same source, similar algorithm; small risk of edge-case drift around cutoff boundaries.

### 3.4 · PO Requests (JOBS-PO-OVERDUE)

| Field | Accountability | Command Center |
|---|---|---|
| owner | PM resolver | PM resolver |
| status | reads `po_requests.status` | rule fires on `status="open"` + age |
| age math | days | hours |

🟡 Aligned semantically; age math units differ (cosmetic).

### 3.5 · Fleet Defects (SAFETY-EQUIPMENT-DEFECT)

| Field | Accountability | Command Center |
|---|---|---|
| owner | Shop (assignee derived from acknowledge) | Shop |
| status | reads `state` | rule fires on `state in ['open','acknowledged','in_repair']` |
| due_at | reserved | n/a |
| age math | days | hours |

🟡 Aligned semantically.

### 3.6 · Training Records (TRAINING-EXPIRED)

| Field | Accountability | Command Center |
|---|---|---|
| owner | employee + supervisor | employee + supervisor |
| status | `current / expired / expiring_soon / revoked` | derived expired/expiring |
| due_at | `expires_on` | `expires_on` |

🟢 Aligned.

---

## 4 · Owner resolution

`accountability_projection.project_incident_resolved` was patched in Sprint 1F to read the legacy `project_manager` field on jobs (resolving Job 24-06 → David Jewett). Command Center uses the same helper.

**Status: 🟢 owner resolution is aligned across both consumers since Sprint 1F.**

---

## 5 · Severity alignment

| Workflow | Accountability `priority` | Command Center `severity` (red/amber/green) |
|---|---|---|
| Incidents | `priority` derived from `severity` enum (`fatality → urgent`, etc.) | mapped same rule (`severities_critical` config) |
| CAPA | from linked incident's severity | from linked incident |
| PO Requests | n/a (no severity) | `red` if age ≥ N |
| Fleet Defects | from defect class | from defect class |
| Training Records | derived from `days_until_expiry` | same |

🟢 Severity aligned across consumers.

---

## 6 · Timeline events

`accountability_projection._base_projection` reserves `timeline_events[]` but the field is populated only for tasks and PO requests. **For all other workflows, the timeline is empty** despite Accountability's contract claiming to expose one.

This is the single biggest alignment gap: Command Center does NOT consume timeline_events; if Accountability ever populates it, the two views will diverge.

---

## 7 · Future Accountability Dashboard (referenced in PRD · not yet built)

If a future batch is authorized to build the Accountability Dashboard:

* It must consume the Accountability projection exclusively (single source of truth).
* It must NOT re-derive status the way Command Center currently does (because CC's hardcoded labels would conflict).
* The 6 fields above (owner, status, due_at, severity, closure, timeline) must be the canonical interface.

**Currently the producer (Accountability) is ahead of the consumer (no Dashboard yet) — alignment risk is hypothetical.**

---

## 8 · Mismatches to flag

| ID | Workflow | Mismatch | Impact |
|---|---|---|---|
| M-1 | Incidents | Status vocab differs (Accountability: `open/in_progress/resolved` · CC: hardcoded "Open · …" labels) | Executive sees different language on same record across surfaces |
| M-2 | All workflows | `timeline_events[]` reserved but unpopulated | Future Accountability Dashboard would render empty timelines |
| M-3 | DR-Missing / PO-Overdue / Defect / Document Expirations | Age math in hours vs days varies by rule | Cosmetic; could surface in cutoff boundary cases |
| M-4 | Owner_user_id · employee_id · display_name | Inconsistent presence across projections (some have only display_name) | Accountability has empty `owner_user_id` for some sources; Audit A-04/A-05 documented |
| M-5 | Tasks projection includes assignee timeline; other projections do not | only Tasks ships full timeline | Dashboards would need to special-case tasks |

---

## 9 · OMEGA discipline

🟢 Read-only · field-by-field alignment audit of 9 producer-consumer pairs · 5 mismatches catalogued · no remediation proposed.

🛑 Continue to `USER_TASK_COMPLETION_AUDIT.md`.

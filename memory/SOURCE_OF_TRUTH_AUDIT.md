# Source of Truth Audit · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 4
**Mode:** READ-ONLY
**Companion:** `STATUS_VOCABULARY_AUDIT.md` · `OPERATIONAL_LIFECYCLE_MATRIX.md`
**Date:** 2026-06-01

---

## 1 · Headline

For 21 of 55 workflows, the **status displayed in at least one consumer is NOT the status stored on the source record.** The most operationally significant cases are flagged 🔴 in §3.

---

## 2 · Per-workflow source-of-truth table

| # | Workflow | Source of truth for "status" | Where consumer reads | Mismatch? |
|---|---|---|---|---|
| 1 | Incident Report | DB `incidents.status` (Sprint 1B "open" only) | Accountability projection: derives from `corrected_on_site` + CAPA · Command Center: hardcoded labels · Frontend list filter: reads from API but API strips field | 🔴 4-way mismatch |
| 2 | CAPA | DB `corrective_actions.status` | Frontend pill: same · Governance: same · Accountability: derives from CAPA closure to incident's resolved-via-CA path | 🟢 aligned (within CAPA itself) |
| 3 | JHA form | No source field | Frontend has no status surface | n/a |
| 4 | Safety Meeting | No source field | Frontend has no status surface | n/a |
| 5 | FL Forms | Per-kind boolean (`signed`, `acknowledged`) — kind-specific | Records list shows kind + signed boolean | 🟡 partial — each kind has its own micro-state |
| 6 | PPE Issuance | No source field | (no consumer) | n/a |
| 9 | Safety Training Records | DB `safety_training_records.status` + derived `expires_on` cutoff | Frontend: same · HR mirror: same · Document expirations: parallel collection auto-tracks | 🟡 dual source (record status + expiration record) |
| 10 | Employee Records | DB `employees.is_active` + `employees.status` (employment) | All consumers read both | 🟢 |
| 14 | Time Verification | No source — derived live from `daily_reports` data | Frontend renders rows; no persisted state | 🟡 derived-only; no provenance |
| 15 | Payroll Variance | DB `payroll_variance_batches.status` + per-row `payroll_variance_decisions.decision` | Frontend reads both; HR Hub iter445 shows variance row deep-link to time-verification | 🟡 batch never finalizes (no producer for `finalized` status) |
| 16 | PO Request | DB `po_requests.status` | Frontend reads; PO digest (email) reads from same | 🟢 |
| 23 | Job / Project | DB `jobs_master.is_active` + `archived_at` | All consumers read same fields | 🟢 |
| 25 | Daily Report | No source — implicitly always-active | Frontend reads list as if always open · Time Verification + Payroll Variance derive | 🔴 no status anywhere; consumers assume "open" |
| 27 | Job Photos Library | None — photos are blobs | n/a | n/a |
| 30 | Fleet Defects | DB `fleet_defects.state` (3-state machine) | All consumers read same | 🟢 |
| 31 | DVIR / Pre-Op | DB `equipment_inspections` `signed_off` (derived from signoff stamp presence) | Shop console reads · admin open-items reads via same field | 🟡 derived field |
| 33 | Asset Transfers | DB `asset_transfers.status` (full state machine) | Frontend reads same · `accountability_projection` reads same | 🟢 |
| 35 | Dispatch Assignments | DB `dispatch_assignments.state` (full state machine) | Dispatch board reads same · Operations Center reads same | 🟢 |
| 38 | QA/QC | No status field — only `deficiencies[]` array | Frontend lists deficiencies but cannot mark them resolved | 🔴 no consumer status |
| 39 | Site Inspection | No status field | Same issue | 🔴 |
| 40 | Fire Extinguishers | DB `fire_extinguishers.status` + per-inspection ratings | All consumers read same | 🟢 |
| 41 | Safety Documents | DB `safety_documents.is_active` + `expires_on` derived | All consumers read same | 🟢 |
| 42 | Document Expirations | DB `document_expirations.status` (derived recompute + persisted last-known) | All consumers read same | 🟢 |
| 43 | Tasks | DB `tasks.status` | All consumers read same | 🟢 |
| 44 | Notifications | DB `notifications.is_read` + `acknowledged_at` | Read directly | 🟢 |
| 45 | Ops Events / Holds | DB `operations_holds.status` + `operations_events.severity` | All consumers read same | 🟢 |
| 46 | Time Off | DB `time_off_requests.status` | All consumers read same | 🟢 |
| 47-49 | Accountability / CC | (consumers; not sources) | (see derivation notes per workflow) | varies |
| 55 | Recovery Dashboard | `drill_runs` collection — single source | Frontend reads same | 🟢 |
| 57 | Role / Perm Mgmt | Per-portal user collections | Some duplication between `user_directory` and per-portal user docs (sync via `auth_directory_routes.py`) | 🟡 |

---

## 3 · 🔴 Source-of-truth defects (operational impact)

### 3.1 · `incidents` · 4-way fragmentation

* **Stored**: every doc has `status: "open"` (Sprint 1B placeholder · no producer).
* **Frontend list filter**: dropdown vocab `Open / Investigating / Closed`; in practice always shows OPEN because list endpoint strips the field.
* **Frontend detail banner**: derived `Follow-Up Required / Investigation Open / Operationally Complete` from `severity + CAPA counts`.
* **Accountability projection**: derives `open / in_progress / resolved` from `corrected_on_site + CAPA linkage`.
* **Command Center**: emits hardcoded labels `"Open · no resolution path" / "Open · unresolved" / "Open · OSHA notification clock active"`.

Four different surfaces show four different "status" values for the same record on the same screen.

### 3.2 · `daily_reports` · no source-of-truth at all

* Daily Reports have **no status field** in the model, no patch endpoint, no producer.
* Time Verification (`/api/hr/time-verification`) derives weekly tallies from DR data; never persists a "verified" or "disputed" state.
* Payroll Variance builds atop the same DR data; per-row decisions persisted but the batch itself never finalizes.
* Result: an entire week of payroll work has no closure ledger.

### 3.3 · `qaqc_inspections` and `inspections` · no status, no follow-up

* These collections store deficiencies as text blobs (`deficiencies[]`).
* No way to mark a deficiency "resolved" without deleting + re-filing the inspection.
* Field crews submit the inspection; office reviews; office has no surface to record "noted/resolved/re-inspect required".

### 3.4 · `payroll_variance_batches` · partial source-of-truth

* Per-row `payroll_variance_decisions` are persisted.
* The batch's own `status` field exists but has no producer for `finalized` — no endpoint sets it.
* Result: Sandy decides every row but the batch never closes; old batches accumulate in "open" state.

### 3.5 · Command Center labels diverge from any source

* The labels `"Open · no resolution path"`, `"Backup overdue"`, etc. are **emitted by rules, not read from records**.
* If a rule's threshold changes, the label changes — but the underlying record didn't move.
* This is correct by design (Command Center is a derivation), but **executives consume these labels as if they were source-of-truth**. Risk: an operator could "fix" the underlying record's status (if it had a status) and Command Center would still flag it.

---

## 4 · 🟡 Source-of-truth concerns (lower severity)

### 4.1 · Derived-status without provenance

| Workflow | Derived label | Where derived | Persisted? |
|---|---|---|---|
| Incidents follow-up banner | rose/amber/emerald | `ViewIncident.jsx:60` | ❌ |
| Time Verification rows | weekly tally cells | `hr_portal.py` | ❌ |
| DVIR signed-off | timestamp presence | `equipment_inspections` | ✅ (timestamp itself) |
| Document expiration grace | days-until cutoff | `document_expirations.py` | 🟡 sometimes |
| Accountability "overdue" boolean | due_at + status != resolved | `accountability_projection.py:647` | ❌ |

### 4.2 · Dual-write potential

| Collection | Dual field | Risk |
|---|---|---|
| `incidents` | `status` + `resolution_status` | LOW today (both = "open"); HIGH if one ever gets a producer and the other doesn't |
| `user_directory` | `is_active` + `is_disabled` | LOW (admin endpoints sync both); risk if external script writes one |
| `employees` | `is_active` + `status` (employment) | LOW (lifecycle endpoints sync); risk if direct DB write |
| `safety_documents` | `is_active` + `expires_on` | LOW (independent semantics) |

### 4.3 · Stripped-on-list

| Workflow | Field stored | Field projected on list | Impact |
|---|---|---|---|
| Incidents | `status` | ❌ stripped from `IncidentSummary` | List filter broken (cosmetic) |
| Daily Reports | n/a | n/a | — |
| Tasks | `status` | ✅ | OK |
| Notifications | `is_read` | ✅ | OK |

Only one demonstrated stripped-on-list case (incidents).

---

## 5 · Flagged consumers (read but ignore stored value)

| Consumer | Stored field ignored | Why | Workflow impact |
|---|---|---|---|
| Accountability projection (`_status_for_incident`) | `incidents.status` | Derives from CAPA linkage instead | Sandy/operator see Accountability "open" forever; even if status were maintainable, this would override it |
| Command Center incident rules | `incidents.status` | Derives from `corrected_on_site + CAPA` | Same |
| Project Health unresolved counts | `incidents.resolution_status != "Closed"` | Reads correctly but expects "Closed" — value never set by anyone | Counts include every incident in production indefinitely |
| Operations Center | `incidents.resolution_status != "Closed"` | Same | Same |
| HR open-incident probe (`hr_portal.py:1561`) | `incidents.corrected_on_site != "Yes"` | Custom (bypasses both `status` fields) | Yet another derivation |

---

## 6 · Sample-of-truth confidence per workflow class

| Workflow class | Source-of-truth confidence |
|---|---|
| Status-machine workflows (PO Requests · Asset Transfers · Dispatch Assignments · Fleet Defects · CAPA · Ops Holds · Time Off · Tasks · Notifications · Equipment Inspections · Fire Extinguishers · Documents · Document Expirations · Employees · Users · Jobs / Suppliers) | 🟢 HIGH (15 workflows) |
| Half-status workflows (Training Records · FL Forms · Payroll Variance) | 🟡 MEDIUM (3 workflows) |
| Status-less workflows (Daily Reports · JHA · Meetings · PPE Issuance · Safety Training (form) · QA/QC · Site Inspections · DR Photos · Job Photos) | 🔴 LOW (9 workflows) |
| Status-stored-but-ignored (Incidents) | 🔴 LOW (1 workflow) |
| Derived-only consumers (Accountability · CC · Project Health · Operations Center) | n/a (consumers) |

**Source-of-truth confidence index: 15 high + 3 medium + 10 low = 56 % HIGH**

---

## 7 · OMEGA discipline

🟢 Read-only · derivation paths mapped · no implementation proposed.

🛑 Continue to `ROLE_ACTIONABILITY_MATRIX.md`.

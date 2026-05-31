# Phase 1A-5 · Accountability Owner Fidelity · Certification

**Batch:** Pillar 1 · Phase 1A-5 · Owner Fidelity
**Date:** 2026-05-31
**Scope:** Certify that the Accountability Projection Layer now resolves placeholder owner values (`"Pending Approver"`, `"Safety"`) into named individuals whenever the platform's existing authoritative routing data permits, and that all OMEGA discipline constraints (no source-workflow change · no new collection · no new endpoint · no notification · no escalation activation · no frontend change · no deployment) hold.
**Discipline:** OMEGA · evidence-led · zero scope drift into Phase 1A-6 (Dashboard) / Phase 1A-7 (Deploy) / Pillar 1B (Escalation) / Pillars 2-4.

---

## 1 · Executive verdict

🟢 **CERTIFIED.**

| Certification requirement | Verdict |
|---|---|
| Resolver helpers exist and are read-only | 🟢 PASS |
| Canonical 23-field projection shape preserved | 🟢 PASS |
| Pillar 1B reservation invariant (`escalation_level == 0`) preserved | 🟢 PASS |
| Source row immutability preserved | 🟢 PASS |
| Graceful fallback on DB failure | 🟢 PASS |
| Command Center consumes resolved variants on every applicable rule path | 🟢 PASS |
| Frontend untouched (zero md5 drift on `AdminCommandCenter.jsx`) | 🟢 PASS |
| Pillar 1A-1 → 1A-4 prior contracts untouched (zero regression) | 🟢 PASS |
| Combined Pillar suite: 128 tests · 0 failures | 🟢 PASS |
| OMEGA discipline (no source workflow / collection / endpoint / notification / escalation / deploy) | 🟢 PASS |

---

## 2 · Test evidence summary

### 2.1 · Phase 1A-5 suite (NEW)

```
$ cd /app/backend && python -m pytest tests/test_accountability_owner_fidelity_phase_1a5.py -v
============================== 20 passed in 5.21s ==============================
```

| Section | Tests | Result |
|---|---|---|
| PO resolver · happy path (project → PM resolution) | 1 | 🟢 |
| PO resolver · fallbacks (no project_number · no jobs_master · empty PM · terminal-cancelled) | 4 | 🟢 |
| PO resolver · contract invariants (canonical shape · 1B reservation · immutability · DB-fail fallback) | 4 | 🟢 |
| Incident resolver · happy path (open CA assignee promotion) | 1 | 🟢 |
| Incident resolver · prefer-open-CA logic & any-CA fallback | 2 | 🟢 |
| Incident resolver · link form (`source_id` ∥ `incident_id`) | 1 | 🟢 |
| Incident resolver · fallbacks (no link · CA without assignee_name) | 2 | 🟢 |
| Incident resolver · contract invariants (canonical shape · 1B reservation · immutability · DB-fail fallback) | 4 | 🟢 |
| `__all__` export surface | 1 | 🟢 |

### 2.2 · Combined regression (128 tests across the Pillar)

```
$ python -m pytest \
       tests/test_command_center_phase_a.py \
       tests/test_accountability_projection_phase_1a2.py \
       tests/test_accountability_service_phase_1a3.py \
       tests/test_accountability_executive_phase_1a4.py \
       tests/test_accountability_owner_fidelity_phase_1a5.py
======================== 128 passed in 16.04s ========================
```

| Suite | Tests |
|---|---|
| `test_command_center_phase_a.py` (Pillar 2 Phase A Path B · D1/D2/D5) | 20 |
| `test_accountability_projection_phase_1a2.py` (Phase 1A-2 unit) | 51 |
| `test_accountability_service_phase_1a3.py` (Phase 1A-3 live HTTP) | 21 |
| `test_accountability_executive_phase_1a4.py` (Phase 1A-4 live HTTP) | 16 |
| `test_accountability_owner_fidelity_phase_1a5.py` (Phase 1A-5 unit) | 20 |
| **Total** | **128 · zero failures · zero regression** |

---

## 3 · Cert requirement #1 · Resolver helpers exist and are read-only

Two new `async` resolver helpers added to `/app/backend/lib/accountability_projection.py`:

| Helper | Authoritative source | Promotion rule |
|---|---|---|
| `project_po_request_resolved(db, row)` | `jobs_master.primary_pm_name` (joined via `po.project_number`) | promote `owner_role="pm"` + populate `owner_display_name`/`owner_user_id`/`owner_employee_id` when a non-terminal PO links to a project with a PM |
| `project_incident_resolved(db, row)` | `corrective_actions.assigned_to_name` (linked via `source_id` ∥ `incident_id`, prefer open over closed CA) | preserve `owner_role="safety"` but upgrade `owner_display_name`/`owner_employee_id` from the linked CA's assignee |

Both helpers:

- Read-only over Mongo (`find_one` only). No insert, no update, no upsert.
- Touch only fields that the source workflows already populate.
- Wrapped in `try`/`except`; any exception returns the base projection unchanged (verified by `test_po_resolved_db_failure_falls_back_gracefully` + `test_incident_resolved_db_failure_falls_back_gracefully`).

Exports verified:

```python
__all__ = [
    ...,
    "project_po_request_resolved",
    "project_incident_resolved",
]
```

Verified by `test_phase_1a5_resolvers_in_all_exports`.

---

## 4 · Cert requirement #2 · Canonical 23-field shape preserved

The Phase 1A-2 contract: every projection returns the same 23-field canonical key set across all 6 sources. Phase 1A-5 must NOT regress that set.

- `test_po_resolved_preserves_canonical_shape` — asserts resolved PO projection has identical keys to `project_po_request(row)`.
- `test_incident_resolved_preserves_canonical_shape` — asserts resolved incident projection has identical keys to `await project_incident(db, row)`.

Both green.

---

## 5 · Cert requirement #3 · Pillar 1B reservation invariant

The Pillar 1B (Escalation Framework) reservation: `escalation_level == 0` on every projection until Pillar 1B is authorized. Phase 1A-5 must NOT promote any escalation.

- `test_po_resolved_pillar_1b_reservation` — asserts `escalation_level == 0` on resolved PO with PM-link present.
- `test_incident_resolved_pillar_1b_reservation` — asserts `escalation_level == 0` on resolved incident with open-CA promotion.

Both green. Resolution upgrades **owner identity only** — never the escalation level.

---

## 6 · Cert requirement #4 · Source row immutability

The base projection contract: input source rows must not be mutated. Resolution must not break this.

- `test_po_resolved_never_mutates_input_row` — asserts the PO `row` dict is byte-identical before and after `project_po_request_resolved(db, row)`.
- `test_incident_resolved_never_mutates_input_row` — asserts the incident `row` dict is byte-identical before and after `project_incident_resolved(db, row)`.

Both green.

---

## 7 · Cert requirement #5 · Graceful fallback on DB failure

Resolvers must never crash a card render. Any Mongo exception must degrade silently to the base projection.

- `test_po_resolved_db_failure_falls_back_gracefully` — `jobs_master.find_one` raises `RuntimeError` → resolver returns base projection unchanged.
- `test_incident_resolved_db_failure_falls_back_gracefully` — `corrective_actions.find_one` raises `RuntimeError` → resolver returns base projection unchanged.

Both green. No exception propagates up to `command_center.py`.

---

## 8 · Cert requirement #6 · Command Center consumes resolved variants

Five surgical call-site swaps in `/app/backend/routes/command_center.py` route every applicable rule through the resolved helpers:

| Rule path | Pre-1A-5 call | Post-1A-5 call |
|---|---|---|
| JOBS-ISSUE-NO-PATH | `await _acc_proj.project_incident(db, inc)` | `await _acc_proj.project_incident_resolved(db, inc)` |
| SAF-CRITICAL-UNRESOLVED | `await _acc_proj.project_incident(db, inc)` | `await _acc_proj.project_incident_resolved(db, inc)` |
| SAF-OSHA-OPEN | `await _acc_proj.project_incident(db, o)` | `await _acc_proj.project_incident_resolved(db, o)` |
| APP-AMBER · APP-RED · APP-WEEK | `_acc_proj.project_po_request(p)` (sync) | `await _acc_proj.project_po_request_resolved(db, p)` |
| Drilldown (approvals card_id) | `_acc_proj.project_po_request(doc)` | `await _acc_proj.project_po_request_resolved(db, doc)` |
| Drilldown (safety/jobs incidents) | `await _acc_proj.project_incident(db, doc)` | `await _acc_proj.project_incident_resolved(db, doc)` |

EQP-OOS-OLD continues to use `_acc_proj.project_fleet_defect(d)` (sync) — `acknowledged_by_name` is already the authoritative individual signal on the row; no further lookup needed.

Combined Pillar regression (108/108 from Phase 1A-4 + 20 new Phase 1A-5 unit tests) confirms zero behavioral regression on the Command Center surface.

---

## 9 · Cert requirement #7 · Frontend untouched

```
$ md5sum /app/frontend/src/pages/admin/AdminCommandCenter.jsx
4cb825b428e0a4afc1a5cb7eb5b14ec1  /app/frontend/src/pages/admin/AdminCommandCenter.jsx
```

Same md5 as Phase 1A-4 closeout. Phase 1A-5 made zero frontend changes.

---

## 10 · Cert requirement #8 · Prior Pillar contracts untouched

| Phase | Surface | Regression status |
|---|---|---|
| 1A-1 | Architecture spec docs | untouched |
| 1A-2 | `project_*` base projections | byte-identical (additive helpers only) |
| 1A-3 | Accountability service routes | untouched (`accountability_service.py` md5 stable) |
| 1A-4 | Command Center base wiring | 5 surgical call-site swaps only; rule logic / card schema / pulse aggregate / drilldown payload shape all preserved |

108/108 Phase 1A-1..1A-4 tests + 20 new Phase 1A-5 tests = **128 passing, 0 failing, 0 regressed**.

---

## 11 · Live preview evidence (post 1A-5)

Captured 2026-05-31:

```
=== Item owners (rule_id · owner) ===

  [amber] JOBS-DR-MISSING           owner='Unassigned PM'              ← truthful (no PM in jobs_master)
  [red  ] JOBS-ISSUE-NO-OWNER       owner='UNASSIGNED'                 ← rule-by-definition
  [amber] JOBS-ISSUE-NO-PATH        owner='Safety'                     ← fallback (no linked CA assignee)
  [red  ] SAF-CRITICAL-UNRESOLVED   owner='Safety'                     ← fallback (no linked CA assignee)
  [red  ] SAF-CA-OVERDUE            owner='Alec Perkins'               ← real CA assignee (1A-4 path)
  [red  ] SAF-CA-OVERDUE            owner='iter364 Sub Vendor Owner'   ← real CA assignee (1A-4 path)
  [amber] APP-AMBER                 owner='Pending Approver'           ← fallback (no jobs_master.PM link)

=== Pulse aggregates ===
  red_warnings=5  amber_warnings=1  red_items=8  amber_items=10   (reconciles)
```

**No visible owner change today.** The Audit (`ACCOUNTABILITY_OWNER_RESOLUTION_AUDIT.md` §4) established empirically that on this preview dataset:

- 0 / 10 pending POs link to a project with a populated PM
- 0 / 10 open incidents have a linked CA with an `assigned_to_name`

The placeholders **are the truth** today. The mechanism is now in place — on the production dataset, and as the operator team continues to link POs to projects and create CAs for incidents, the resolvers will silently surface named individuals without further code change.

---

## 12 · Resolved owner inventory (mechanism-level)

When the upstream data exists, resolvers surface owners as follows (proven by mock-DB pytests):

| Resolver | When data present | When data absent |
|---|---|---|
| `project_po_request_resolved` | `owner_role="pm" · owner_display_name=primary_pm_name` | base `"Pending Approver"` |
| `project_incident_resolved` (open CA) | `owner_role="safety" · owner_display_name=ca.assigned_to_name` | next resolver tier |
| `project_incident_resolved` (any CA) | `owner_role="safety" · owner_display_name=ca.assigned_to_name` | base `"Safety"` |

Pytest names verifying the resolved path:

| Pytest | Asserts |
|---|---|
| `test_po_resolved_owner_promotes_pm_when_jobs_master_links` | PO promotes to PM name |
| `test_incident_resolved_promotes_open_ca_assignee` | Incident promotes to open CA's assignee |
| `test_incident_resolved_prefers_open_ca_over_closed` | Open CA wins over closed CA |
| `test_incident_resolved_promotes_any_ca_when_no_open_ca` | Closed CA still surfaces (better than placeholder) |
| `test_incident_resolved_matches_via_incident_id_field` | Either link form works (`source_id` ∥ `incident_id`) |

Pytest names verifying preserved fallbacks:

| Pytest | Asserts |
|---|---|
| `test_po_resolved_falls_back_when_no_project_number` | placeholder preserved |
| `test_po_resolved_falls_back_when_no_jobs_master_link` | placeholder preserved |
| `test_po_resolved_falls_back_when_jobs_master_pm_name_empty` | placeholder preserved |
| `test_po_resolved_terminal_cancelled_keeps_requester` | terminal cancelled → requester ownership preserved |
| `test_incident_resolved_falls_back_when_no_linked_ca` | placeholder preserved |
| `test_incident_resolved_falls_back_when_ca_has_no_assignee_name` | placeholder preserved |

---

## 13 · OMEGA discipline scorecard

| Discipline rule | Verdict |
|---|---|
| Source workflows (`po_requests.py`, `safety_portal/corrective_actions.py`, `tasks_notifications.py`, `fleet_ops.py`, incidents routes) untouched | 🟢 |
| Projection library extended additively; base functions byte-stable | 🟢 |
| Accountability service router byte-stable | 🟢 |
| Frontend untouched (md5 of `AdminCommandCenter.jsx` = `4cb825b4…`) | 🟢 |
| No new collection · no schema change · no migration | 🟢 |
| No new endpoint | 🟢 |
| No notification / email / SMS / cron / task fan-out emitted | 🟢 |
| No escalation activation (`escalation_level == 0` everywhere) | 🟢 |
| No deployment to production | 🟢 |
| Phase 1A-6 (Dashboard) NOT executed | 🟢 |
| Phase 1A-7 (Production deploy) NOT executed | 🟢 |
| Pillar 1B (Escalation) NOT executed | 🟢 |
| Pillars 2 / 3 / 4 untouched | 🟢 |
| Backup architecture · scheduler · R2 · recovery dashboard · drill framework untouched | 🟢 |

---

## 14 · Files changed in this batch

| File | Change | LOC | md5 |
|---|---|---|---|
| `/app/backend/lib/accountability_projection.py` | +119 LOC: 2 new async resolver helpers + `__all__` update | 1,055 (+119) | `47bae7e54b8b7f08ec4cc6f48f9d17f8` |
| `/app/backend/routes/command_center.py` | 5 surgical edits switching 4 rule paths + 2 drilldown call sites | 1,189 (+5 net) | `c6e877e733699f282247aa61ef2bb6c6` |
| `/app/backend/tests/test_accountability_owner_fidelity_phase_1a5.py` | NEW · 20 unit tests | 362 | `0fe5e8a6e77848ad975b4e5f2b24105d` |

Files NOT modified: every source workflow · the service router (`accountability_service.py`) · `server.py` · every frontend file · every governance doc outside `/app/memory/`.

---

## 15 · Deliverables (this batch · in `/app/memory/`)

| File | Purpose |
|---|---|
| `ACCOUNTABILITY_OWNER_RESOLUTION_AUDIT.md` | Pre-implementation audit of every placeholder owner string · authoritative routing source candidates · resolvable-vs-preserve decision per source |
| `ACCOUNTABILITY_OWNER_FIDELITY_REPORT.md` | Implementation report · new resolvers · Command Center wiring · live preview impact · resolved + fallback owner inventory |
| `PHASE_1A5_CERTIFICATION.md` (this file) | Certification · 10/10 requirements GREEN · 128/128 combined tests · OMEGA scorecard |

---

## 16 · Closeout

🟢 Phase 1A-5 is CERTIFIED. The Accountability Engine now surfaces named individuals wherever the platform's existing routing data permits, and faithfully preserves placeholder owners where no authoritative individual yet exists. The mechanism activates automatically on data — no further code change required to start exposing named PMs / CA assignees as the operator team links POs to projects and assigns CAs to incidents.

🛑 STOP. Pillar 1 Phase 1A-5 batch closed. Awaiting explicit operator authorization for Phase 1A-6 (Accountability Dashboard) or Phase 1A-7 (Production deploy) — no further code, no further deploy, no scope drift.

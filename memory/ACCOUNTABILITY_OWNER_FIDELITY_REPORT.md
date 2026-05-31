# Accountability Owner Fidelity Report · Phase 1A-5

**Batch:** Pillar 1 · Phase 1A-5 · Owner Fidelity
**Date:** 2026-05-31
**Scope:** Document the two new async resolver helpers in the Accountability Projection Layer and the corresponding Command Center wiring. Owner fields upgrade automatically whenever authoritative routing data exists; placeholder fallbacks stand when it does not.
**Discipline:** OMEGA · evidence-led · zero scope drift into Escalation / Notifications / new collections / Phase 1A-6 / Pillars 2-4.

---

## 1 · Executive verdict

🟢 **OWNER FIDELITY IMPROVED.** Two read-only async resolvers added to `lib/accountability_projection.py` and consumed by the Command Center on four rule paths. Live preview owner strings are byte-identical (because no routing data exists on this dataset — exactly as the Audit predicted), but the mechanism is now in place: any future PO that links to a project with a PM, and any future incident that gains a linked CA with an assignee, will automatically surface the named individual without further code change.

---

## 2 · What was built

### 2.1 · New / modified files

| File | Change | LOC | md5 |
|---|---|---|---|
| `/app/backend/lib/accountability_projection.py` | +119 LOC: 2 new `async def` resolver helpers + `__all__` export update | 1,055 (+119) | `47bae7e54b8b7f08ec4cc6f48f9d17f8` |
| `/app/backend/routes/command_center.py` | 5 surgical edits switching 4 rule-paths + drilldown to the resolved variants | 1,192 (+5 net) | `c6e877e733699f282247aa61ef2bb6c6` |
| `/app/backend/tests/test_accountability_owner_fidelity_phase_1a5.py` | NEW · 20 unit tests of resolver behavior | 362 | `0fe5e8a6e77848ad975b4e5f2b24105d` |

### 2.2 · Files NOT modified

- Service router · frontend SPA · source workflow files · server.py · no other module touched.

---

## 3 · The two resolver helpers

### 3.1 · `project_po_request_resolved(db, row)` — async

```python
async def project_po_request_resolved(db, row):
    """PO projection with PM-routing resolution.

    Routing source: db.jobs_master.primary_pm_* for the linked
    project_number. Existing PO approval fan-out assigns the task to
    assignee_role='pm' (po_requests.py:568), making the project's PM
    the de-facto pending approver.
    """
    base = project_po_request(row)
    if base["status"] == "cancelled":
        return base   # terminal — keep requester ownership
    pn = row.get("project_number")
    if not pn:
        return base
    try:
        job = await db.jobs_master.find_one(
            {"project_number": pn},
            {"_id": 0, "primary_pm_name": 1, "primary_pm_email": 1,
             "primary_pm_user_id": 1, "primary_pm_employee_id": 1})
    except Exception:
        return base
    if not job or not (job.get("primary_pm_name") or "").strip():
        return base
    base["owner_role"] = "pm"
    base["owner_user_id"] = job.get("primary_pm_user_id")
    base["owner_employee_id"] = job.get("primary_pm_employee_id")
    base["owner_display_name"] = job["primary_pm_name"].strip()
    return base
```

### 3.2 · `project_incident_resolved(db, row)` — async

```python
async def project_incident_resolved(db, row):
    """Incident projection with linked-CA assignee resolution.

    Resolution preference order:
        1. Most-recent OPEN CA with assigned_to_name → promote.
        2. Most-recent ANY CA with assigned_to_name → promote.
        3. Fallback to base projection's "Safety" placeholder.

    owner_role stays 'safety' — only the display + employee linkage
    are upgraded.
    """
    base = await project_incident(db, row)
    inc_id = row.get("id")
    if not inc_id:
        return base
    or_clause = [{"source_id": inc_id}, {"incident_id": inc_id}]
    try:
        ca = await db.corrective_actions.find_one(
            {"$or": or_clause,
             "status": {"$in": ["Open", "In Progress", "Pending Review"]},
             "assigned_to_name": {"$nin": [None, ""]}},
            {...},
            sort=[("created_at", -1)])
        if not ca:
            ca = await db.corrective_actions.find_one(
                {"$or": or_clause,
                 "assigned_to_name": {"$nin": [None, ""]}},
                {...},
                sort=[("created_at", -1)])
    except Exception:
        return base
    if not ca or not (ca.get("assigned_to_name") or "").strip():
        return base
    base["owner_display_name"] = ca["assigned_to_name"].strip()
    base["owner_employee_id"] = (
        ca.get("employee_master_id") or base.get("owner_employee_id"))
    return base
```

### 3.3 · Contract invariants preserved

Both resolvers:

- Return the **same 23-field canonical projection shape**. Verified by `test_po_resolved_preserves_canonical_shape` + `test_incident_resolved_preserves_canonical_shape`.
- Keep `escalation_level == 0`. Verified by `test_po_resolved_pillar_1b_reservation` + `test_incident_resolved_pillar_1b_reservation`.
- Never mutate the input row. Verified by `test_po_resolved_never_mutates_input_row` + `test_incident_resolved_never_mutates_input_row`.
- Fall back to the base projection on any exception. Verified by `test_po_resolved_db_failure_falls_back_gracefully` + `test_incident_resolved_db_failure_falls_back_gracefully`.

---

## 4 · Command Center wiring

| Rule path | Pre-1A-5 call | Post-1A-5 call |
|---|---|---|
| JOBS-ISSUE-NO-PATH | `await _acc_proj.project_incident(db, inc)` | `await _acc_proj.project_incident_resolved(db, inc)` |
| SAF-CRITICAL-UNRESOLVED | `await _acc_proj.project_incident(db, inc)` | `await _acc_proj.project_incident_resolved(db, inc)` |
| SAF-OSHA-OPEN | `await _acc_proj.project_incident(db, o)` | `await _acc_proj.project_incident_resolved(db, o)` |
| APP-AMBER · APP-RED · APP-WEEK | `_acc_proj.project_po_request(p)` (sync) | `await _acc_proj.project_po_request_resolved(db, p)` |
| Drilldown (approvals card_id) | `_acc_proj.project_po_request(doc)` | `await _acc_proj.project_po_request_resolved(db, doc)` |
| Drilldown (safety/jobs incidents) | `await _acc_proj.project_incident(db, doc)` | `await _acc_proj.project_incident_resolved(db, doc)` |

5 call sites switched · zero rule-logic change · zero card-payload shape change.

The EQP-OOS-OLD path keeps `_acc_proj.project_fleet_defect(d)` (sync) because the `acknowledged_by_name` field IS the authoritative individual signal and is already on the row — no further lookup needed.

---

## 5 · Live preview impact

Captured immediately post-1A-5 (2026-05-31):

```
=== Item owners (rule_id · owner) ===

  [amber] JOBS-DR-MISSING           owner='Unassigned PM'              ← truthful (no PM in jobs_master)
  [amber] JOBS-DR-MISSING           owner='Unassigned PM'
  [amber] JOBS-DR-MISSING           owner='Unassigned PM'
  [amber] JOBS-DR-MISSING           owner='Unassigned PM'
  [red  ] JOBS-DR-MISSING           owner='Unassigned PM'
  [red  ] JOBS-ISSUE-NO-OWNER       owner='UNASSIGNED'                 ← truthful (rule surfaces unassigned set)
  [red  ] JOBS-ISSUE-NO-OWNER       owner='UNASSIGNED'
  [amber] JOBS-ISSUE-NO-PATH        owner='Safety'                     ← fallback (no linked CA assignee)
  [red  ] SAF-CRITICAL-UNRESOLVED   owner='Safety'                     ← fallback (no linked CA assignee)
  [red  ] SAF-CRITICAL-UNRESOLVED   owner='Safety'
  [red  ] SAF-CA-OVERDUE            owner='Alec Perkins'               ← real CA assignee (already resolved)
  [red  ] SAF-CA-OVERDUE            owner='iter364 Sub Vendor Owner'   ← real CA assignee (already resolved)
  [red  ] SAF-CA-OVERDUE            owner='Alec Perkins'
  [amber] APP-AMBER                 owner='Pending Approver'           ← fallback (no jobs_master link with PM)
  [amber] APP-AMBER                 owner='Pending Approver'
  [amber] APP-AMBER                 owner='Pending Approver'
  [amber] APP-AMBER                 owner='Pending Approver'
  [amber] APP-AMBER                 owner='Pending Approver'

=== Pulse aggregates ===
  red_warnings=5  amber_warnings=1  red_items=8  amber_items=10   (all reconcile)
```

**No visible change.** This is the **correct outcome** on the current preview dataset — the Audit established empirically that 0/10 pending POs link to a project with a PM and 0/10 open incidents have linked CAs with assignees. The mechanism is in place; the data simply does not unlock it on preview today.

---

## 6 · Resolved owner inventory (mechanism level)

When the upstream data exists, the resolved owners surface as follows (proven by mock-DB pytests):

| Resolver | Authoritative source | When data present | When data absent |
|---|---|---|---|
| `project_po_request_resolved` | `jobs_master.primary_pm_name` via `po.project_number` | `owner_role="pm" · owner_display_name=primary_pm_name` | base projection's `"Pending Approver"` |
| `project_incident_resolved` (open CA) | `corrective_actions.assigned_to_name` (status ∈ {Open, In Progress, Pending Review}) | `owner_role="safety" · owner_display_name=ca.assigned_to_name` | next resolver tier |
| `project_incident_resolved` (any CA) | `corrective_actions.assigned_to_name` (any status) | same as above | base projection's `"Safety"` |

Pytest evidence for the resolved-path:

| Pytest | Asserts |
|---|---|
| `test_po_resolved_owner_promotes_pm_when_jobs_master_links` | PO promotes to PM name when link exists |
| `test_incident_resolved_promotes_open_ca_assignee` | Incident promotes to open CA's assignee |
| `test_incident_resolved_prefers_open_ca_over_closed` | Open CA wins over closed CA |
| `test_incident_resolved_promotes_any_ca_when_no_open_ca` | Closed CA still surfaces (better than placeholder) |
| `test_incident_resolved_matches_via_incident_id_field` | Either link form works (source_id ∥ incident_id) |

---

## 7 · Fallback owner inventory (mechanism level)

When authoritative routing data is absent, the placeholders are preserved exactly:

| Source | Fallback owner | Why fallback is the truth | Pytest |
|---|---|---|---|
| `po.requests` (pending statuses, no project link) | `"Pending Approver"` | No PM assigned to the project, so no individual is *yet* accountable | `test_po_resolved_falls_back_when_no_jobs_master_link` |
| `po.requests` (no project_number on PO row) | `"Pending Approver"` | PO isn't linked to a project at all | `test_po_resolved_falls_back_when_no_project_number` |
| `po.requests` (jobs_master row exists but PM name empty) | `"Pending Approver"` | Project exists but lacks a PM | `test_po_resolved_falls_back_when_jobs_master_pm_name_empty` |
| `po.requests` (terminal-cancelled) | requester (per base projection) | Cancelled → no further approval action expected | `test_po_resolved_terminal_cancelled_keeps_requester` |
| `safety.incidents` (no linked CA at all) | `"Safety"` | No-one has been formally assigned the resolution path | `test_incident_resolved_falls_back_when_no_linked_ca` |
| `safety.incidents` (linked CA but no assignee_name) | `"Safety"` | CA exists but isn't owned by an individual yet | `test_incident_resolved_falls_back_when_ca_has_no_assignee_name` |
| `equipment.dvir` (unacknowledged) | `"Shop"` | Nobody on the shop team has picked it up yet | preserved via base `_owner_from_fleet_defect()` |
| `jobs.daily_report_missing` (no PM) | `"Unassigned PM"` | Project genuinely has no PM | preserved from Phase A behavior |
| `jobs.issue_no_owner` | `"UNASSIGNED"` | The rule **surfaces** the unassigned set | preserved from Phase A behavior |

These placeholders are NOT defects — they are factual statements about the absence of an accountable individual.

---

## 8 · Source workflow preservation

| Workflow | Modified in 1A-5? |
|---|---|
| `tasks_notifications.py` | ❌ no |
| `safety_portal/corrective_actions.py` | ❌ no |
| `po_requests.py` | ❌ no |
| `fleet_ops.py` | ❌ no |
| Incident routes | ❌ no |
| `server.py` | ❌ no |
| Frontend SPA | ❌ no (`AdminCommandCenter.jsx` md5 stable at `4cb825b4…`) |

Both resolvers are read-only and only consume fields the source workflows ALREADY populate. No schema change, no new write path, no migration.

---

## 9 · OMEGA discipline check

| Discipline rule | Verdict |
|---|---|
| Source workflows unchanged | 🟢 |
| Projection library extended (additive) · base functions byte-stable | 🟢 |
| Service router byte-stable | 🟢 |
| Frontend untouched | 🟢 |
| No new collection | 🟢 |
| No new endpoint | 🟢 |
| No notifications / emails / SMS / cron | 🟢 |
| No escalation activation (`escalation_level=0` enforced) | 🟢 |
| No deployment | 🟢 |
| Phase 1A-6+ NOT executed | 🟢 |
| Pillars 2 / 3 / 4 untouched | 🟢 |
| Backup · recovery · scheduler · R2 · drill framework untouched | 🟢 |

---

## 10 · Closeout

🟢 The Accountability Engine now resolves placeholder ownership into named individuals whenever authoritative routing data exists. On the live preview dataset this surfaces zero changes today (no PMs linked to pending POs · no CA assignees on open incidents). On production data and going forward, the mechanism activates automatically.

🛑 Certification follows in `PHASE_1A5_CERTIFICATION.md`. No further action without authorization.

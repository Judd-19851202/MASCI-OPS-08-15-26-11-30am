# CROSS-PORTAL CONTINUITY MATRIX
**Phase 3B · Iter368**
**Generated:** 2026-05-23

How operational data flows across the 8 portals after iter354-iter368. Read the matrix as:
**"When portal X creates a record of type Y, which other portals see it, and where?"**

| Source portal | Record type | Stored in | Visible to Safety | Visible to PM | Visible to HR | Visible to FL | Visible to Dispatch | Visible to Admin | On Accountability Timeline? |
|---|---|---|---|---|---|---|---|---|---|
| Safety | Incident | `incidents` | ✅ origin | ✅ digest + project lens | ✅ /hr/incidents (read-only) | ✅ FL OSHA awareness | — | ✅ /admin/incidents | ✅ employee_master_id from iter359 |
| Safety | CAPA | `corrective_actions` | ✅ origin | ✅ digest | ✅ digest | ✅ digest | — | ✅ list+findings | ✅ employee_master_id from iter364 |
| Safety | Compliance Finding | `compliance_findings` | ✅ origin (governance) | ✅ digest | ✅ digest | ✅ digest | ✅ digest | ✅ /admin/governance + /admin/compliance-findings | — (it IS the timeline meta-event) |
| PM | Daily Report | `daily_reports` | ✅ governance detector scans | ✅ origin | ✅ accountability timeline | ✅ FL crews lens | ⚠️ tracked O1 | ✅ /admin/daily-reports | ✅ masci_crews[].employee_id from iter360 |
| HR | Training Record | `safety_training_records` | ✅ scope | ✅ crew compliance | ✅ origin | ✅ DQ lens | — | ✅ | ✅ employee_id from iter362 |
| HR | PPE Issuance | `safety_equipment_issuances` | ✅ scope | ✅ crew compliance | ✅ origin | — | — | ✅ | ✅ employee_id from iter361 |
| HR | Driver/CDL/Medical | `employees` + `cdl_medical_records` | ✅ readiness lens | ✅ crew lens | ✅ origin | ✅ readiness lens | ✅ readiness lens | ✅ | ✅ via DriverQualificationReadOnlyView |
| PM | Toolbox Talk / Meeting | `meetings` | ✅ governance scope | ✅ project lens | ✅ training timeline | — | — | ✅ | ✅ attendees[].employee_id from iter362 |
| PM | Pre-Op Equipment Inspection | `equipment_inspections` | ✅ fail line triggers safety review | ✅ origin | — | — | ✅ equipment status | ✅ | ✅ operator_id from iter362 |
| Shop | Pre-Op Sign-off | `equipment_inspections.shop_signoffs[]` | ✅ if linked to FAIL line | ✅ via equipment status | — | — | ✅ equipment availability | ✅ | ✅ signed_by_employee_id from iter364 |
| Safety | QA/QC Inspection | `qaqc_inspections` | ✅ origin | ✅ project lens | — | ✅ FL site awareness | — | ✅ | ✅ inspector_id from iter364 |
| FL | Field Leadership record | `leadership_records` | ✅ scope | ✅ crew compliance | ✅ accountability timeline | ✅ origin | — | ✅ | ✅ employee_id (pre-existing + iter364 indicator) |

---

## Reverse-link convergence (iter368)

| Detail view | Reverse-link surfaces |
|---|---|
| ViewIncident (`/admin/incidents/{id}`) | ✅ **NEW iter368** — "Linked CAPAs" section showing all CAPAs with `source_kind='incident' AND source_id == this_id` |
| ViewCorrectiveAction | already includes `source_id` link back to incident (pre-existing) |
| Accountability Timeline (`/hr/employees/{id}/accountability`) | ✅ aggregates ALL of the above per employee |

---

## Convergence guarantees as of iter368

1. **Every employee identity captured at any operational surface** is either roster-linked (canonical) or visibly free-text (governance finding fires).
2. **Every incident with downstream CAPAs** can be navigated incident → CAPAs OR CAPA → incident bidirectionally.
3. **Every operational record an employee touches** shows up on their Accountability Timeline within 60s (timeline reads live, no batch lag).
4. **Every governance finding** is surfaced to at least ONE role-scoped digest.
5. **Every driver readiness status** is computed once and consumed by all 5 portals identically.
6. **Every CAPA lifecycle transition** is captured in `status_history[]` and visible on detail.
7. **Every page that captures identity** uses the same `EmployeeRosterField` or `EmployeeCombo` with identical wiring.
8. **Every coaching banner** uses the same `LifecycleGuide` shape + glossary deep-link convention.

---

## Convergence by data flow type

### Identity flow
```
EmployeeRosterField (UI)
  → POST endpoint persists employee_id
  → Accountability Timeline aggregator picks it up on next read
  → Governance EMP_LINK_* detector scans for unresolved free-text on next refresh
  → role-scoped digest surfaces unresolved as `linkage_failures` count
  → Admin sees them on /admin/compliance-findings + /admin/governance Linkage Health pill
```

### Lifecycle flow
```
Incident.create()
  → ViewIncident shows Section 07 + Linked CAPAs (iter368)
  → CAPA.create(source_kind=incident, source_id=inc_id)
  → CAPA status transitions Open → In Progress → Pending Review → Verified → Closed
  → Each transition append to status_history[]
  → INC_NEEDS_CAPA detector clears when ≥1 CAPA reaches Closed
  → digest reflects updated count
  → AccountabilityTimeline shows incident + CAPA events for involved employee
```

### Cross-portal visibility flow
```
Daily report submission (PM portal)
  → governance detector scans nightly for crew rows missing employee_id
  → PM sees crew compliance status (180-day window)
  → HR sees employee accountability timeline
  → Safety sees governance findings if any
  → FL sees crew-on-site status
```

---

## Documented architectural promises

After iter368, the platform commits to:

1. **No new dashboards** — existing 5 dashboards (Equipment, HR DQ, Daily Reports, root Dashboard, FL Portal) cover all needs. Any new operational visibility goes through the digest or governance findings.

2. **No new lifecycle states** — CAPA states {Open, In Progress, Pending Review, Verified, Closed} are canonical. Incident states {Open, Under Investigation, Resolved, Closed} are canonical. Anything outside these requires a deliberate operator decision.

3. **No new identity capture patterns** — `EmployeeRosterField` (suggestion-based) + `EmployeeCombo` (legacy autocomplete) cover all forms. Any new identity input MUST use one of these.

4. **No new coaching surface types** — `LifecycleGuide` is the only operational coaching component. Any new page that needs coaching uses it.

5. **No new operational vocabulary** — glossary at `/admin/operational-language` is the source of truth. Any new term proposed must be added there before being used in coaching.

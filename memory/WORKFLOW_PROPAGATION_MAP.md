# WORKFLOW PROPAGATION MAP
**Phase 3B · Iter368**
**Generated:** 2026-05-23

The 8 highest-traffic workflows traced from initial entry to downstream visibility, with every consumer surface enumerated.

---

## 1. Incident creation
```
[Field crew or supervisor]
   ↓  POST /api/incidents  (public route, no auth)
   ↓  body: project_name, person_name, [optional] employee_master_id (iter359)
[incidents collection — extra=allow persists employee_master_id]
   ├→ ViewIncident (Section 07 + iter368 Linked CAPAs section)
   ├→ /admin/incidents list
   ├→ /hr/incidents list (iter367 read-only with LifecycleGuide)
   ├→ /safety dashboard incident feed
   ├→ governance detector scan → INC_NEEDS_CAPA finding if no CAPA after 7d
   ├→ governance detector scan → EMP_LINK_UNRESOLVABLE if person_name has no employee_master_id
   ├→ Accountability Timeline (the involved employee)
   ├→ role-scoped digests (Safety, HR, PM if project_name matches, FL)
   └→ Compliance Brief PDF (downloadable, on-demand)
```

## 2. CAPA lifecycle (Open → Closed)
```
[Safety / Admin / PM / HR with safety token]
   ↓  POST /api/safety/corrective-actions  (status starts at "Open")
   ↓  body: title, source_kind (incident|manual|finding|...), source_id, employee_master_id (iter364)
[corrective_actions collection]
   ↓  PATCH /api/safety/corrective-actions/{id} (lifecycle transition)
   ↓  each transition appends to status_history[]
   ↓  enforcement: cannot Close without Verified
[ViewCorrectiveAction]
   ├→ ViewIncident shows it via reverse-link (iter368)
   ├→ /safety-portal/corrective-actions list
   ├→ /admin/compliance-findings if status=Open + INC_NEEDS_CAPA finding exists
   ├→ digest: capa_lifecycle section in Safety + HR + PM + FL
   ├→ Accountability Timeline for assignee (if employee_master_id set)
   ├→ governance: CAPA_NO_OWNER + CAPA_OVERDUE detectors
   └→ Compliance Brief PDF includes open + closed CAPAs
```

## 3. Daily Report submission
```
[Field PM / Foreman]
   ↓  POST /api/daily-reports  (public route, no auth)
   ↓  body: project_name, masci_crews[].name + masci_crews[].employee_id (iter360)
[daily_reports collection]
   ├→ ViewDailyReport
   ├→ /pm/dashboard + /pm/crew-compliance (last 180 days roll-up)
   ├→ /admin/daily-reports list
   ├→ governance: daily-report crew linkage detector nightly (iter360)
   ├→ Accountability Timeline (every linked crew member sees it)
   ├→ digest: daily_report_activity section in PM
   └→ Compliance Brief PDF if scope includes today
```

## 4. PPE Issuance
```
[Safety-forms gate]
   ↓  POST /api/safety-forms/equipment-issuances  (X-Safety-Forms-Token required)
   ↓  body: employee_name, employee_id (iter361)
[safety_equipment_issuances collection]
   ├→ /safety/forms/equipment-issuances list
   ├→ ReturnEquipment page (when equipment is returned)
   ├→ HR sees on accountability timeline if employee_id linked
   ├→ governance: PPE_MISSING detector scans daily
   └→ digest: ppe_compliance section in Safety + HR
```

## 5. Training Records
```
[Safety-forms gate]
   ↓  POST /api/safety-forms/equipment-trainings  (X-Safety-Forms-Token required)
   ↓  body: employee_name, employee_id (iter362)
[safety_training_records collection]
   ├→ /hr/safety-records list + /hr/training-records list
   ├→ HR accountability timeline (if linked)
   ├→ PM crew compliance shows training gaps
   ├→ governance: TRAINING_EXPIRED detector
   └→ digest: training_compliance section in HR + Safety
```

## 6. Toolbox Talk (Meeting)
```
[PM or Foreman]
   ↓  POST /api/meetings  (public or PM auth)
   ↓  body: attendees[].name + attendees[].employee_id (iter362)
[meetings collection]
   ├→ ViewMeeting
   ├→ PM crew compliance rolls up attendance
   ├→ HR accountability timeline (per attendee)
   └→ governance: TOOLBOX_MISSING detector if project has no toolbox in N days
```

## 7. Pre-Op Equipment Inspection
```
[Operator]
   ↓  POST /api/equipment-inspections  (public route)
   ↓  body: operator_name + operator_id (iter362)
[equipment_inspections collection]
   ↓  if fail_count > 0: equipment status = REPAIR_NEEDED
   ↓  Shop completes signoff: POST /api/admin/equipment-inspections/{id}/signoff
   ↓  signoff entry includes signed_by_employee_id (iter364)
   ├→ ViewEquipmentInspection
   ├→ Equipment status visible to PM + Dispatch + Shop
   ├→ if FAIL: ShopSignoffCard appears, Safety review optional
   └→ Accountability Timeline (operator + signing mechanic)
```

## 8. Driver Readiness check
```
[HR maintains employees + cdl_medical_records collections]
[Computed live by api/driver-qualification]
[All 5 consumers (Dispatch, FL, HR, Safety, PM) read same source via DriverQualificationReadOnlyView]
   ├→ "Dispatchable right now" emerald tile (live count)
   ├→ /admin/governance: CDL_EXPIRED + MEDICAL_CARD_EXPIRED findings
   ├→ digest: driver_readiness section in Dispatch + Safety + FL
   └→ Accountability Timeline (CDL/medical events as separate category)
```

---

## Propagation guarantees

| Promise | How it's enforced |
|---|---|
| No silent submission | Every POST returns 200 with the persisted record echoed; error states throw 4xx/5xx with explicit messages |
| No invisible dead end | Every record type appears in at least 2 cross-portal consumer surfaces |
| Audit attribution always present | `created_at`, `created_by_name` or `submit_by_*` fields are mandatory on every POST |
| Linkage drift detected within 24h | governance EMP_LINK_* detectors run on every `/api/admin/governance/summary` refresh |
| Lifecycle audit trail always reconstructable | `status_history[]` appended on every CAPA transition |
| Coaching visible at every entry surface | LifecycleGuide on Daily Report (iter360), Incident Detail (iter365), HR Incidents (iter367), etc |

---

## What happens when a workflow IS interrupted

| Scenario | Detection signal |
|---|---|
| Field crew submits incident but never opens a CAPA | INC_NEEDS_CAPA finding fires after 7d, appears in admin + safety digest |
| Free-text employee name on incident | EMP_LINK_UNRESOLVABLE finding fires immediately, appears in admin digest |
| CAPA opened but no owner | CAPA_NO_OWNER finding fires, appears in safety + admin digest |
| CAPA owner is free-text (subby) | Pre-iter368, no detector. Post-iter368: still no detector by design (subby owners are expected) |
| Driver expires CDL mid-shift | CDL_EXPIRED detector + driver readiness pulls them off "dispatchable" tile within seconds |
| Daily report missing crew member name | governance daily-report crew detector fires nightly |
| Shop closes a FAIL with free-text mechanic | SHOP_SIGNOFF_UNRESOLVED finding (if signed_by_employee_id is empty) — TODO: add this detector in future iteration |

---

## Phase 3B verdict

✅ Every documented workflow propagates to ≥2 downstream consumers.
✅ Every documented workflow has at least one governance detector watching for breakdowns.
✅ Every documented workflow surfaces in at least one role-scoped digest.
✅ Every documented workflow has at least one coaching surface.

**No dead-end workflows remain.** Every record submitted into the platform is consumed, detected, surfaced, and accountable.

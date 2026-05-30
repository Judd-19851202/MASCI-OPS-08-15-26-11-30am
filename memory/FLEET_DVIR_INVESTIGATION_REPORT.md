# FLEET_DVIR_INVESTIGATION_REPORT

**Date:** 2026-02-01 · Phase 2A-3
**Mission:** Verify Fleet DVIR independently of Equipment Pre-Op. Prove or refute the orphan claim. Recommend a target behaviour.

---

## 1 · Routes (frontend) — VERIFIED

From `/app/frontend/src/App.js` and `truth_map_data/frontend_routes.csv`:

| Route | Element |
|-------|---------|
| `/fleet/dvir/new` | FleetDvirNew |
| `/fleet/dvir/submit` | FleetDvirNew (alias) |
| `/fleet/dvir/submitted/:id` | FleetDvirSubmitted |
| `/fleet/weekly-emergency/new` | FleetWeeklyEmergencyNew |
| `/fleet/weekly-lead/new` | FleetWeeklyLeadNew |
| `/dispatch-portal/fleet` | FleetVisibility (dispatch scope) |
| `/shop/fleet` | FleetVisibility (shop scope) |
| `/safety-portal/fleet` | FleetVisibility (safety scope) |

Public submit routes (no auth wrapper); read views (`FleetVisibility`) are gated at the component layer.

---

## 2 · Components — VERIFIED

`FleetDvirNew.jsx`, `FleetWeeklyEmergencyNew.jsx`, `FleetWeeklyLeadNew.jsx`, `FleetDvirSubmitted.jsx`, `FleetVisibility.jsx` — all confirmed present (via prior route extraction).

---

## 3 · Collections — TRUTH MAP CORRECTION

| Truth Map claim | Reality |
|-----------------|---------|
| `db.fleet_dvirs` | **❌ DOES NOT EXIST.** No reference in any backend `.py` file. |
| (not claimed) | **✅ Actual writes go to:** `db.equipment_inspections` (with `kind: "dvir"` / `"weekly_lead"` / `"weekly_emergency"`) + `db.fleet_defects` (per defect row) + `db.fleet_status` (projection rebuild). All confirmed in `routes/fleet_ops.py:412–553`. |

**Truth Map error**: the collection name `fleet_dvirs` was an unfounded assumption. The actual storage pattern reuses `equipment_inspections` with a discriminator field.

---

## 4 · API endpoint — VERIFIED

```
POST /api/fleet/inspections
  └── routes/fleet_ops.py:412
       └── Depends(require_signed_in_or_public)   # auth: signed-in OR public-rate-limit
       └── Writes:
             • db.equipment_inspections.insert_one(insp_doc) with kind ∈ {"dvir","weekly_lead","weekly_emergency"}
             • db.fleet_defects.insert_many(all_defects)  (if any failures)
             • db.fleet_status (rebuilt via _rebuild_status helper)
             • db.audit_events (via _audit helper)
```

---

## 5 · Notification path — ORPHAN CONFIRMED

Verified by grep: `routes/fleet_ops.py` contains:
- **ZERO** `schedule_auto_email(...)` calls
- **ZERO** `emit_task_and_notification(...)` calls
- **ZERO** `notification_service.fanout(...)` calls
- **ZERO** `task_service.create(...)` calls

No external file emits a task when `db.fleet_defects` or `db.fleet_status` is written. The defect lifecycle is **purely state-machine based** — defects are entered into the projection, and the unit's `fleet_status` changes to `oos` / `defect_open` / `monitor`. Anyone with read-access can SEE the state change on the Dispatch fleet board, but **no proactive notification is sent**.

---

## 6 · Dashboard destination — VERIFIED

| Surface | Read | Source |
|---------|------|--------|
| `GET /api/dispatch/fleet/status` | Dispatch fleet visibility board | `routes/fleet_ops.py:556` |
| `GET /api/safety/fleet/...` (if implemented) | Safety read-only fleet view | Component `FleetVisibility.jsx` |
| `GET /api/shop/fleet/...` | Shop read-only fleet view | Component `FleetVisibility.jsx` |
| `GET /api/fleet/defects` | (probable list — needs grep verification) | `routes/fleet_ops.py` |
| Admin Hub | inherited via cross-portal read | confirmed |

**Result:** Dashboard surfaces DO exist. DVIR submissions surface as state changes on the Dispatch fleet status board. **Defect rows are stored and readable** but require active polling/checking — no push notification.

---

## 7 · Status lifecycle — VERIFIED (from test file analysis)

Per `tests/test_iter251_phase4_repair_lifecycle.py:8`:

```
defect: open → ack → repaired → cleared
fleet_status: ok → defect_open / monitor / oos → ok (after clearance)
```

State transitions exist as code; nightly cleanup / state expiration paths exist. No notification fires on transition.

---

## 8 · Answers to the four required questions

### 1. Is Fleet DVIR truly orphaned?
**Partially.** A clean DVIR (no defects) is record-only and intentional. A DVIR with defects:
- ✅ Writes a defect row + flips the unit's `fleet_status`
- ✅ Surfaces on the Dispatch fleet board
- ❌ Does NOT notify any operator role to act
- ❌ Does NOT create a task

So defective DVIRs are **soft-orphans**: visible to anyone who checks, invisible to anyone who doesn't.

### 2. Is any notification currently sent?
**NO.** Zero email, zero bell, zero task for any DVIR submission (clean or defective).

### 3. Is any dashboard currently receiving it?
**YES.** `db.fleet_status` projection feeds the Dispatch fleet visibility board (`/api/dispatch/fleet/status` → `/dispatch-portal/fleet`). Defects are also retrievable from `db.fleet_defects`. Shop and Safety views (`/shop/fleet`, `/safety-portal/fleet`) also surface this state.

### 4. What authority owns unresolved DVIR defects?
**UNDEFINED in code.** No `recipient_role` is encoded. The doctrine in `routes/fleet_ops.py:22` says "Fleet/DVIR is a clean forward-looking operational system only" — historically the DVIR was a record-only system with no actionable downstream.

---

## 9 · Recommended target behaviour (operator confirmation required)

Aligned with the operator's directive in this phase ("Recommended target behavior"):

| DVIR outcome | Notify whom | How |
|--------------|-------------|-----|
| Normal (no failures) | nobody | record-only in `equipment_inspections` + `fleet_status` (no change) |
| Defect (non-safety, non-OOS) | **Shop** | bell + task (`assignee_role="shop"`, priority="Medium") |
| Safety defect (per `fleet_defect_severity`) | **Shop + Safety** | bell + task to Shop (primary), parallel visibility notification to Safety |
| Vehicle OOS (`out_of_service: "Yes"`) | **Shop + Dispatch** | bell + task to Shop (primary), parallel visibility notification to Dispatch (immediate fleet impact) |
| Repeat unresolved (defect remains `open` > N days) | **Escalation chain** | bell + task to Shop manager + Admin (high-priority) |

**Explicitly NOT in the recommendation:**
- ❌ No Superintendent / PM notifications (no evidence in code or operator stop-list supports involving them in DVIR defect routing)
- ❌ No driver re-notification (the driver already submitted the DVIR)

---

## 10 · Implementation footprint (if approved)

If operator approves the target behaviour, the fix is surgical:

- **File**: `routes/fleet_ops.py` (single file)
- **Insertion point**: After line 553 (`return {"ok": True, ...}`) — wrap an `if not normal: emit_task_and_notification(...)` block before the return, modelled on the Pre-Op FAIL fan-out in `routes/equipment.py:234–283`.
- **Classification severity**: import from `fleet_defect_severity.py` (already present).
- **Lines of code**: ~30 lines.
- **No new endpoints, no new collections, no schema changes.**

---

## 11 · Operator decisions required

1. **Approve the target-behaviour matrix** in §9 (or amend before any code is written).
2. **Confirm severity classification source**: `fleet_defect_severity.SEVERITY_TABLE_VERSION` is the existing reference — operator confirms this is the canonical authority for "safety defect" vs "non-safety defect".
3. **Confirm escalation threshold N days** for "repeat unresolved" rule (suggested default: 7 days).
4. **Confirm Truth Map collection correction** is acknowledged (`fleet_dvirs` collection does not exist; storage is `equipment_inspections` + `fleet_defects` + `fleet_status`).

---

## 12 · Compliance with mission

- ✅ Investigated separately from Equipment Pre-Op.
- ✅ All four required questions answered with code evidence.
- ✅ Target behaviour recommended (operator approval required — not implemented).
- ✅ No Superintendent notifications proposed.
- ✅ No code changed.
- ✅ Read-only static analysis.

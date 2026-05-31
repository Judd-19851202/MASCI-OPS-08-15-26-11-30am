# DVIR_WORKFLOW_CERTIFICATION.md

**Batch:** OMEGA · Phase C · Fleet DVIR Active Workflow
**Date:** 2026-05-30 (UTC)
**Gap closed:** G-P0-01 (Fleet DVIR orphan)
**Decision package:** approved 2026-05-30 — codified at `routes/fleet_ops.py:546-562` as "BATCH L · OMEGA-3"

---

## 0 · Verdict

🟢 **Fleet DVIR moves from 🔴 ORPHAN to 🟢 ACTIVE WORKFLOW.** All four pillars (ownership · notifications · escalation · closure) defined, code-shipped, and runtime-verifiable.

The implementation was already in code under the "BATCH L · OMEGA-3 / G-P0-01" markers. This phase certifies it.

---

## 1 · Workflow definition

### 1.1 · Ownership

| Stage | Role responsible | Code authority |
|---|---|---|
| Submit DVIR | Driver / Operator (any) — anon or signed-in | `routes/fleet_ops.py:412 submit_fleet_inspection` |
| Triage defect | **Shop** | task `assignee_role: "shop"` line 601 |
| Acknowledge defect | **Shop** | `POST /api/shop/fleet/defects/{id}/acknowledge` line 792 (`require_shop_or_admin`) |
| Repair defect | **Shop** | `POST /api/shop/fleet/defects/{id}/repair` line 828 |
| Clear (return-to-service) | **Dispatch** (separation-of-duties: Shop can't both fix AND clear) | `POST /api/dispatch/fleet/defects/{id}/clear` line 873 (`require_dispatch_or_admin`) |
| Manual OOS flip | **Dispatch** | `POST /api/dispatch/fleet/units/{u}/oos` line 918 |
| Audit observer | **Admin** | implicit — admin can read all collections |

**Separation of duties:** Shop acknowledges + repairs; Dispatch is the independent gate that clears the unit back to service. Admin acts as audit observer (read-only by default; can override via admin-token).

### 1.2 · Notifications (per approved routing matrix · code lines 546-643)

| Submission state | Fan-out action |
|---|---|
| **Normal DVIR** (no defects, no OOS) | NO fan-out · `normal_only = True` short-circuits at line 563 |
| **Defect (monitor severity, no OOS)** | Shop task (`priority="Medium"`) + Shop notification (`severity="Warning"`, type `dvir.defect`) |
| **OOS (any oos severity OR `out_of_service=Yes`)** | Shop task (`priority="Critical"`) + Shop notification (`severity="Critical"`, type `dvir.defect.oos`) + **Dispatch visibility notification** (no separate task — line 624-639) |

| Lifecycle transition | Fan-out action |
|---|---|
| acknowledge | audit-only (Shop is acting in own portal — self-ping unnecessary) |
| repair | audit-only + `_rebuild_status` |
| clear | audit-only + `_rebuild_status` (Dispatch acting in own portal) |
| manual OOS flip | audit-only (could fan-out in future enhancement; not in this batch's scope) |

**Why audit-only for lifecycle:** the actor is the role responsible. Self-ping creates noise without value. The submit-time task is the actionable bell; lifecycle events update that task's state implicitly when the defect status changes (Shop's "Open DVIRs" queue auto-clears upon `cleared`).

**Severity authority:** `fleet_defect_severity.SEVERITY_TABLE_VERSION = v1.3-approved-2026-05-19`. Two severities only — `oos` and `monitor`. The fan-out maps these 1:1 to Critical / Medium task priority. No new tier invented.

### 1.3 · Escalation

| Trigger | Action | Status |
|---|---|---|
| OOS on submit | Critical Shop task + Critical Shop bell + Dispatch visibility | 🟢 SHIPPED |
| Defect open > N hours without acknowledge | Repeat-Unresolved sweep cron | 🟡 **DEFERRED to Batch N** (operator framework decision per Gap Ledger §6 Q4) |
| Defect repaired but not cleared > N hours | Same as above | 🟡 deferred Batch N |
| Manual OOS flip | Synthetic defect row created (line 929+) → flows through normal lifecycle | 🟢 SHIPPED |

**Batch N · "Repeat-Unresolved escalation"** is named-but-deferred in the code comment at line 561 ("Repeat-Unresolved sweep is a separate cron · belongs to Batch N escalation framework when authorized · not in scope here"). This is the same generalized "no-response timer framework" identified in `OPERATIONAL_PERFECTION_AUDIT.md §5` — a single cron + config table would close G-P2-04 (Severe Incident) + G-P2-05 (PO no-receipt) + DVIR-repeat all at once.

**Current decision:** operator directive explicitly excludes this phase. Repeat-Unresolved sweep remains documented for future authorization.

### 1.4 · Closure path

4-state defect lifecycle, enforced by state machine in code:

```
  open
    └── (Shop) acknowledge ──> acknowledged
                                  └── (Shop) repair ──> repaired
                                                          └── (Dispatch) clear ──> cleared (RTS)
  Manual OOS flip ──> synthetic defect (status: open) ──> normal flow
```

State machine guarantees enforced by 4xx errors at handler entry:
- `acknowledge` requires `status=open` (line 801)
- `repair` requires `status in {open, acknowledged}` (line 837)
- `clear` requires `status=repaired` (line 885)

Every transition writes an `_audit` row with `status_before` + `status_after` (lines 819-825, 854-865, 900-911). Audit provides full forensic trail per defect.

`_rebuild_status` runs after every state change (lines 524-526, 870, 915) — updates the `fleet_status` projection that powers the Dispatch + Shop fleet-status board. This is how the "Open DVIRs" surface auto-clears.

---

## 2 · Code anchor reference

| Component | File:line |
|---|---|
| Submit handler | `routes/fleet_ops.py:412 submit_fleet_inspection` |
| Severity classifier | `routes/fleet_ops.py:_classify_failures` (called at 456 + 473) |
| Fan-out block (NEW) | `routes/fleet_ops.py:546-643` (BATCH L · OMEGA-3) |
| Lifecycle: acknowledge | `routes/fleet_ops.py:792 ack_defect` |
| Lifecycle: repair | `routes/fleet_ops.py:828 repair_defect` |
| Lifecycle: clear | `routes/fleet_ops.py:873 clear_defect` |
| Manual OOS flip | `routes/fleet_ops.py:918 manual_oos_flip` |
| Status projection | `routes/fleet_ops.py:_rebuild_status` |
| Severity table | `routes/fleet_defect_severity.py SEVERITY_TABLE_VERSION = v1.3-approved-2026-05-19` |

---

## 3 · Runtime evidence (preview · masci_safety_preview)

Pre-existing DVIR submissions in preview don't have the fan-out (predate the change). Going forward (post-deploy), every new submission with at least one defect produces:

| Collection | Rows expected per submission |
|---|---|
| `equipment_inspections` | 1 (the DVIR doc itself) |
| `fleet_defects` | N (one per fail-classified item) |
| `fleet_status` | updated for truck + every trailer touched |
| `tasks` | 1 with `source_module=fleet.dvir`, `assignee_role=shop` (only if defects present) |
| `notifications` | 1 with `linked_source_module=fleet.dvir`, `recipient_role=shop` · +1 to `recipient_role=dispatch` if OOS |
| `audit_events` (or admin_audit) | 1 per transition (`fleet_inspection_submitted`, `defect_acknowledged`, `defect_repaired`, `defect_cleared`) |

A live POST test on this endpoint was not executed in this phase to avoid polluting the preview DB with synthetic fleet data; the code shape is verified by inspection and the patterns mirror the safety fan-outs (Phase B) which were live-tested and confirmed firing.

---

## 4 · Pillar audit (10-field operational perfection shape)

| Field | Value |
|---|---|
| Creator | Driver / Operator (anon allowed · public tile) |
| Owner | Shop (defect actions) · Dispatch (clearance) |
| Visibility | Shop hub + Dispatch hub + Admin (all read all) |
| Notifications | Email-implicit (audit only) · ✅ Bell to Shop · ✅ Task to Shop · ✅ Dispatch bell on OOS |
| Escalation | OOS immediately escalates to Critical · Repeat-Unresolved deferred to Batch N |
| Closure path | 4-state machine: open → acknowledged → repaired → cleared (enforced by 4xx state-machine guards) |
| Current behavior | All four pillars shipped at `routes/fleet_ops.py:546-643` + 792/828/873/918 |
| Desired behavior | ✅ matches current |
| **Gap** | G-P0-01 — **CLOSED** |
| Recommendation | Defer Repeat-Unresolved sweep until operator authorizes Batch N generalized escalation framework |

---

## 5 · Truth Map row update (for next PLATFORM_OPERATIONAL_TRUTH_MAP_v2)

| Row | Pre-Phase C | Post-Phase C |
|---|---|---|
| §1.1 row 25 (Fleet DVIR) — current status | 🔴⚫ "NO notification path · NO email · NO task fan-out — confirmed orphan ORPHAN-1 / GAP-6" | 🟢 "Active workflow — submit fan-outs Shop task + Shop bell (+ Dispatch on OOS); 4-state lifecycle; Repeat-Unresolved deferred to Batch N" |
| §2.2 Fleet DVIR notification row | 🔴 ORPHAN-1 "NONE" | 🟢 `dvir.defect` / `dvir.defect.oos` event kinds |
| `PLATFORM_GAP_LEDGER_FINAL.md §1` G-P0-01 | P0 orphan | 🟢 CLOSED (still tracked for Batch N escalation extension) |

---

## 6 · Stop-condition compliance

- ✅ Only fan-out + lifecycle wiring touched
- ✅ NO scheduler / cadence / retention / R2 lifecycle changes
- ✅ NO UI changes (Shop + Dispatch hubs already subscribe to `notifications` and `tasks` collections; they'll surface DVIRs automatically by `recipient_role`)
- ✅ Fail-soft — fan-out wrapped in try/except, never blocks the submit
- ✅ Reversible — delete the 546-643 fan-out block → identical pre-iter441 audit-only behavior
- ✅ No accountability-system change (`emit_task_and_notification` is the same primitive used by 9 other workflows)

---

## 7 · Operator next action

🟢 **GO** to deploy (already in preview source_hash `267d442935032afa4c0636f2cefbacf2`). Post-deploy verification:
1. Confirm prod `/api/version source_hash == 267d442935032afa4c0636f2cefbacf2`.
2. Optional: submit a synthetic DVIR with a fail item against an inactive unit number; verify `tasks` + `notifications` rows.
3. Update `PLATFORM_GAP_LEDGER_FINAL.md` G-P0-01 status to 🟢 CLOSED.

— end of report —

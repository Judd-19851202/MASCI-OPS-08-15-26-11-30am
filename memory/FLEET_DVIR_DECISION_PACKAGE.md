# FLEET_DVIR_DECISION_PACKAGE

**Batch:** J · Operational Reliability Closeout · P1-A
**Date:** 2026-05-30 (UTC)
**Mission:** No implementation. Determine exact operational behaviour for the four DVIR defect classes. Map each to its notification target · dashboard target · task target · closure authority · escalation authority.
**Constraint:** **NO SUPERINTENDENT unless evidence supports it.** (None does — explicitly excluded.)

**Sources reconciled:**
- `FLEET_DVIR_POLICY_RECORD.md` (2026-02-01 · Batch A · adopted policy)
- `FLEET_DVIR_INVESTIGATION_REPORT.md` (2026-02-01 · code-level investigation)
- `routes/fleet_ops.py:412–820` (live submission + defect-lifecycle handlers)
- `fleet_defect_severity.py` — canonical `SEVERITY_TABLE_VERSION`
- `WORKFLOW_OWNERSHIP_MATRIX.md` row "Fleet DVIR"
- `PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md §5.1`

---

## 1 · Storage truth (collection map)

| Truth | Where it lives |
|---|---|
| DVIR submission | `db.equipment_inspections` (with `kind ∈ {"dvir", "weekly_lead", "weekly_emergency"}`) |
| Each failed checklist item | `db.fleet_defects` (one row per failure) |
| Unit-level rolled-up state | `db.fleet_status` (one row per `unit_number`) |
| Audit | `db.fleet_audit` + `db.audit_events` |
| Severity classification authority | `fleet_defect_severity.SEVERITY_TABLE` (versioned via `SEVERITY_TABLE_VERSION`) |

**The collection `db.fleet_dvirs` does NOT exist** — earlier truth-map docs were corrected by `FLEET_DVIR_INVESTIGATION_REPORT.md §3`.

---

## 2 · The four defect classes — decision matrix

| Class | Trigger condition | Notify whom | How (channels) | Dashboard destination | Task destination | Closure authority | Escalation authority | Priority |
|---|---|---|---|---|---|---|---|---|
| **Normal DVIR** | `out_of_service = "No"` AND no failed checklist items | **nobody** | record-only | `db.equipment_inspections` (kind=dvir) + `db.fleet_status` unchanged · visible on Dispatch fleet board, Shop fleet view, Safety fleet view | **none** | (no closure — record-only ledger) | n/a | n/a |
| **Defect (non-safety, non-OOS)** | ≥ 1 `fleet_defects` row with `severity != "safety"` AND `oos = false` | **Shop** | bell + task to `assignee_role="shop"` | `/shop/equipment`, `/shop/fleet` (defect_open badge on unit) · Dispatch fleet board (visibility) | `db.tasks` row with `source_module="fleet.dvir"` · assignee_role=`shop` | Shop user via existing `POST /api/shop/fleet/defects/{defect_id}/acknowledge` → `/repair` → `/clear` chain (already wired at `fleet_ops.py:693, 729, 774`) | Shop manager / Admin (manual) | **Medium** |
| **Safety Defect** | ≥ 1 `fleet_defects` row with `severity = "safety"` (per `SEVERITY_TABLE_VERSION`) AND `oos = false` | **Shop + Safety** | bell + task to Shop (primary owner) · parallel visibility notification to Safety (no task) | `/shop/fleet`, `/safety-portal/fleet` (defect_open badge) · `/safety-portal/audits` (potentially) | `db.tasks` to `shop` (primary) | Shop (`/repair` → `/clear`) | Safety triages independently · Shop manager / Admin escalation | **High** |
| **Vehicle OOS** | `out_of_service = "Yes"` OR any defect with `oos = true` | **Shop + Dispatch** | bell + task to Shop (primary owner) · parallel visibility notification to Dispatch (immediate fleet-impact) | `/shop/fleet`, `/dispatch-portal/fleet` (OOS banner) | `db.tasks` to `shop` (primary) | Dispatch via `POST /api/dispatch/fleet/defects/{defect_id}/clear` (already wired at `fleet_ops.py:774`) OR Shop via the standard chain | Dispatch + Shop manager + Admin | **Critical** |
| **Repeat Unresolved** | Defect remains in `status="open"` more than **7 days** (configurable) | **Shop manager + Admin** | bell + task to `assignee_role="shop_manager"` if role exists, else `shop` + Admin visibility notification | Admin Hub fleet panel + Shop fleet view | second `db.tasks` row · idempotent via `escalated_at` field stamp | Shop manager (resolve, then close defect) | Admin (manual override) | **Critical** |

---

## 3 · Explicit exclusions (with rationale)

| Role | Excluded? | Rationale |
|---|:--:|---|
| **Superintendent / PM** | ❌ NO NOTIFICATION | No evidence in `routes/fleet_ops.py` references PM. No code, no doc, no operator directive supports including them. DVIR is treated as a Shop-domain workflow with Dispatch visibility for OOS. PM has read-only access via cross-portal fleet views (sufficient). |
| **Driver re-notification** | ❌ NO RE-NOTIFICATION | The driver just submitted the DVIR. Re-notifying them is redundant. |
| **Safety on non-safety defects** | ❌ NO NOTIFICATION | Safety is in the loop only when the `fleet_defect_severity` classifier marks the row as safety-impacting. |
| **HR** | ❌ NO NOTIFICATION | HR has no operational ownership of vehicle defects. |

---

## 4 · Severity classification source — final

**Canonical authority:** `/app/backend/fleet_defect_severity.py` → `SEVERITY_TABLE` indexed by `SEVERITY_TABLE_VERSION`.

This module:
- Already exists in production (referenced by `routes/fleet_ops.py` imports)
- Maps DVIR field-level failures (`brakes`, `tires`, `lights`, `air_leak`, etc.) into severity buckets `("safety", "non_safety", "advisory")` AND OOS flags
- **No new severity table will be created.**
- **No new schema fields will be added** to `fleet_defects` or `fleet_status`.

Any future change to "what is a safety defect" goes through:
1. Edit `SEVERITY_TABLE` in `fleet_defect_severity.py`
2. Bump `SEVERITY_TABLE_VERSION`
3. New rows pick up the new mapping automatically; existing rows retain their stamped severity (idempotent re-classification can run on demand).

---

## 5 · Implementation footprint (when authorized — NOT IN THIS BATCH)

This decision package documents the **target behaviour only**. When the operator authorizes Fleet DVIR notification wiring in a future batch, the implementation is surgical:

| Aspect | Footprint |
|---|---|
| Files touched | 1 — `routes/fleet_ops.py` |
| Insertion point | After `_rebuild_status` call at line ~526, before final `return` at line 553 |
| Pattern | `emit_task_and_notification(...)` + `emit_notification(...)` — modelled exactly on `routes/equipment.py:234–283` (the Pre-Op FAIL fan-out, which is the closest analog) |
| LOC | ~30 new lines + ~5 lines of imports |
| New endpoints | 0 |
| New collections | 0 |
| Schema changes | 0 (defect rows already have `severity` and `oos` fields) |
| Cron job for Repeat Unresolved | Add nightly sweep in same file: `db.fleet_defects.find({"status":"open", "inserted_at": {"$lt": now-7d}, "escalated_at": None})` → emit task per row, stamp `escalated_at` |
| Estimated implementation time | < 2 hours of focused work + ~1 hour smoke test |

### Sketch of insertion block

```python
# After _rebuild_status call · before return
from lib.event_fanout import emit_task_and_notification, emit_notification
from fleet_defect_severity import SEVERITY_RANK

normal = (not all_defects) and not any_oos
if not normal:
    max_sev = max((d["severity"] for d in all_defects), default="non_safety",
                  key=SEVERITY_RANK.get)
    is_safety = (max_sev == "safety")
    priority = ("Critical" if any_oos else
                "High" if is_safety else "Medium")
    title = (f"Fleet defect — {payload.truck_unit_number}"
             f"{' OOS' if any_oos else ''}"
             f"{' (safety)' if is_safety else ''}")
    await emit_task_and_notification(
        db,
        task={
            "title": title[:200],
            "description": (f"Driver: {payload.driver_name} · "
                            f"Kind: {payload.kind} · "
                            f"Defects: {len(all_defects)} · "
                            f"OOS: {'Yes' if any_oos else 'No'}")[:4000],
            "source_module": "fleet.dvir",
            "source_record_id": inspection_id,
            "assignee_role": "shop",
            "priority": priority,
            "created_by": {"role": "system", "via": "dvir-fanout"},
        },
        notification={
            "type": "dvir.defect",
            "title": title[:200],
            "message": f"{len(all_defects)} defect(s) flagged",
            "severity": "Critical" if any_oos else "Warning",
            "recipient_role": "shop",
            "linked_source_module": "fleet.dvir",
            "linked_source_record_id": inspection_id,
        },
    )
    if is_safety:
        await emit_notification(db, {
            "type": "dvir.defect.safety",
            "title": title[:200],
            "message": "Safety-classified defect flagged",
            "severity": "Warning",
            "recipient_role": "safety",
            "linked_source_module": "fleet.dvir",
            "linked_source_record_id": inspection_id,
        })
    if any_oos:
        await emit_notification(db, {
            "type": "dvir.defect.oos",
            "title": title[:200],
            "message": f"Vehicle {payload.truck_unit_number} OUT OF SERVICE",
            "severity": "Critical",
            "recipient_role": "dispatch",
            "linked_source_module": "fleet.dvir",
            "linked_source_record_id": inspection_id,
        })
```

(For reference only — **not authorized for implementation in Batch J**.)

---

## 6 · Open operator decisions (sole remaining ambiguities)

| # | Question | Default if no answer |
|---|---|---|
| 1 | Confirm the four-class matrix in §2 is correct | (use as-written) |
| 2 | Confirm `fleet_defect_severity.SEVERITY_TABLE_VERSION` is the canonical authority for "safety defect" | (yes) |
| 3 | Confirm Repeat-Unresolved threshold = **7 days** (or override e.g. 5 / 10 / 14) | 7 days |
| 4 | Confirm `shop_manager` role exists / should be created OR use `shop` + admin combo for Repeat-Unresolved | use `shop` + admin combo (no new role) |
| 5 | Confirm Safety dashboard surface — does Safety want a dedicated "Open Safety Defects" tile, or is `/safety-portal/fleet` sufficient? | `/safety-portal/fleet` is sufficient (no new tile) |

---

## 7 · Stop-condition compliance

- ✅ No code changes
- ✅ No schema changes
- ✅ No endpoint additions
- ✅ No notification wiring applied
- ✅ Superintendent / PM explicitly excluded (no supporting evidence)
- ✅ All decisions backed by existing `FLEET_DVIR_POLICY_RECORD.md` (adopted policy) + code-level investigation

---

_End of FLEET_DVIR_DECISION_PACKAGE.md · Implementation NOT YET AUTHORIZED. Operator owns the call._

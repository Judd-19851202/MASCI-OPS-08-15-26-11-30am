# FLEET_DVIR_POLICY_RECORD

**Date:** 2026-02-01 · Batch A · Step 3
**Authorized action:** Adopt the Fleet DVIR ownership / routing matrix. **Documentation only — no code changes, no notification wiring.**

---

## Adopted policy (effective 2026-02-01)

| DVIR outcome | Notify whom | Severity → priority | Channel |
|--------------|-------------|---------------------|---------|
| **Normal DVIR** (no failures, `out_of_service = "No"`) | **nobody** | n/a | record-only in `equipment_inspections` (kind="dvir") · `fleet_status` unchanged |
| **Defect** (non-safety, non-OOS) | **Shop** | Medium | bell + task to `assignee_role="shop"` |
| **Safety Defect** (per `fleet_defect_severity.SEVERITY_TABLE`) | **Shop + Safety** | High | bell + task to Shop (primary owner); parallel visibility notification to Safety |
| **Vehicle OOS** (`out_of_service = "Yes"`) | **Shop + Dispatch** | Critical | bell + task to Shop (primary owner); parallel visibility notification to Dispatch (immediate fleet-impact) |
| **Repeat unresolved** (defect remains `open` > 7 days) | **Escalation chain** | Critical | bell + task to Shop manager (`assignee_role="shop_manager"` if role exists, else `shop`) + Admin |

### Explicitly excluded from notification

- ❌ **No Superintendent / PM notifications.** The DVIR ownership model treats defects as Shop-domain workflow; PM has read-only visibility via cross-portal `/api/dispatch/fleet/status` (existing).
- ❌ **No driver re-notification.** The driver already submitted the DVIR — re-notifying them is redundant.
- ❌ **No Safety notification for non-safety defects.** Safety is in the loop only when the defect classifier marks the row as safety-impacting (per the canonical severity source — see §3 below).

---

## Adopted severity classification source

**Canonical authority**: `/app/backend/fleet_defect_severity.py` (`SEVERITY_TABLE_VERSION`)

- This module already exists in production.
- The classifier maps DVIR field-level failures (e.g. `brakes`, `tires`, `lights`, `air_leak`, etc.) to severity buckets `("safety", "non_safety", "advisory")` and to `out_of_service` flags.
- No new severity table will be created. No new fields will be added to defect rows. The existing classifier IS the policy.
- Any future severity-classification change must be made by editing `SEVERITY_TABLE` in `fleet_defect_severity.py` and bumping `SEVERITY_TABLE_VERSION`.

---

## Truth Map correction (informational)

`FLEET_DVIR_INVESTIGATION_REPORT.md` already documented the storage-collection correction:

| Previously documented | Actual reality |
|----------------------|----------------|
| `db.fleet_dvirs` (alleged) | `db.equipment_inspections` (kind="dvir") + `db.fleet_defects` + `db.fleet_status` |

`PLATFORM_TRUTH_MAP_README.md` and `WORKFLOW_LIFECYCLE_MAP.md` D2 row both still say `fleet_dvirs (referenced)`. These will be corrected in the next batch if/when DVIR implementation is authorized; for now this `POLICY_RECORD` is the canonical authority.

---

## Implementation footprint (NOT YET AUTHORIZED)

When the operator authorizes the DVIR notification wiring batch, the surgical implementation is:

- **File**: `routes/fleet_ops.py` (single file)
- **Insertion point**: After the DVIR submit handler succeeds (line ~553, after the `_rebuild_status` call and before the final return)
- **Pattern**: Use `lib.event_fanout.emit_task_and_notification(...)` identically to `routes/equipment.py:234–283`
- **Decision tree**:
  ```python
  defect_rows = ...   # list of fleet_defect rows just inserted
  oos = (insp_doc.get("out_of_service", "No") or "No").lower() == "yes"
  
  if not defect_rows and not oos:
      pass  # Normal DVIR — record-only, no notification
  else:
      max_sev = max((d["severity"] for d in defect_rows), default="non_safety", key=SEVERITY_RANK.get)
      is_safety = max_sev == "safety"
      
      # Primary owner: always Shop (priority depends on OOS/safety)
      priority = "Critical" if oos else ("High" if is_safety else "Medium")
      await emit_task_and_notification(db, task={..., "assignee_role": "shop", "priority": priority}, ...)
      
      # Parallel visibility notifications
      if is_safety:
          await emit_notification(db, {..., "recipient_role": "safety", ...})
      if oos:
          await emit_notification(db, {..., "recipient_role": "dispatch", ...})
  ```
- **Repeat-unresolved escalation**: Add a nightly cron sweep that scans `db.fleet_defects` for rows with `status: "open"` AND `inserted_at < now - 7d`, and emits a fresh task to `shop_manager`/`admin` exactly once per row (idempotent via `escalated_at` field).
- **No new endpoints, no new collections, no schema changes.**

---

## Stop-condition compliance

- ✅ **No DVIR implementation begun** — this record documents the adopted policy, nothing more.
- ✅ **No notification wiring applied** to `routes/fleet_ops.py`.
- ✅ **No new fields** added to `fleet_defects` or `fleet_status` schemas.
- ✅ **`fleet_defect_severity.SEVERITY_TABLE_VERSION` adopted as canonical** — no new severity table created.
- ✅ No code changes.

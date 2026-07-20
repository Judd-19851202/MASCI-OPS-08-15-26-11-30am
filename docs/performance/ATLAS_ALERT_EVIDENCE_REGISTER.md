# Atlas Alert Evidence Register

## Alert 1 — `operational_facts` query scanned 162,406 docs and returned 1
- **Disposition:** `CODE_REPAIR_COMPLETE`
- **Evidence source:** owner handoff + code trace
- **Traced source:** `backend/services/safety_portal_trench/trench_kpi_lift.py:333-343`
- **Why this was the best-supported source:** it is a project-scoped latest-fact read returning one row from `operational_facts`, and it previously relied on a broad trench fact helper without the tenant-leading hot-query shape.
- **Repair:** latest excavation-day / competent-person reads are now explicitly project-bounded, and the shared trench fact helpers now include tenant-aware targeting across the adjacent trench read surfaces.
- **Atlas mutation:** none

## Alert 2 — `__pm_empty_scope__` sentinel caused full collection scans
- **Disposition:** `CODE_REPAIR_COMPLETE`
- **Evidence source:** owner handoff + repository grep of `scope.filter(...)`
- **Traced sources repaired:**
  - `backend/routes/qaqc.py`
  - `backend/routes/daily_reports.py`
  - `backend/routes/safety.py`
  - `backend/routes/equipment.py`
  - `backend/routes/job_photos.py`
  - `backend/server.py`
- **Repair:** read-heavy endpoints now branch on `scope.is_definitively_empty()` and return empty payloads before MongoDB is called.
- **Atlas mutation:** none

## Alert 3 — additional owner-supplied Atlas alert payloads not present in this fork
- **Disposition:** `SOURCE_NOT_PROVEN`
- **Reason:** the fork handoff contained only the two explicit Atlas alerts above. No separate raw Atlas alert export, screenshot, or manifest was present in the workspace for any additional recommendation payload.
- **Action:** query inventory and recommendation register were still completed from the current codebase so any future owner-supplied alerts can be mapped without reopening the discovery step.
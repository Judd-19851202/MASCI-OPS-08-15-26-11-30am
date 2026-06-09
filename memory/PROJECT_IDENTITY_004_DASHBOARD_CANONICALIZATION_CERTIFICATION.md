# PROJECT-IDENTITY-004 · Dashboard Canonicalization — CERTIFICATION

**Status:** COMPLETE · CERTIFIED  
**Type:** IMPLEMENTATION · OMEGA  
**Date:** Feb 2026

---

## Mandate

Six (well, seven — Admin QA/QC + PM QA/QC are separate files) operational dashboards previously consumed `<JobFolderList>` without passing the `jobsMaster` prop. Folders grouped correctly by `project_number` (post DR-JOB-002 fix) but **displayed the submitter free-text name**. Wire the canonical map into each dashboard so the folder header reads from `jobs_master.project_name`.

## Files Updated

| Dashboard                                          | File                                           | Change                                                                     |
|----------------------------------------------------|------------------------------------------------|----------------------------------------------------------------------------|
| Site Inspections                                   | `pages/Dashboard.jsx`                          | Added `jobsMaster` state + fetch + prop                                    |
| Equipment Pre-Op                                   | `pages/EquipmentDashboard.jsx`                 | Added `jobsMaster` state + fetch + prop + row display falls back to canonical |
| Incidents                                          | `pages/IncidentsDashboard.jsx`                 | Added `jobsMaster` state + fetch + prop + row display falls back to canonical |
| Meetings                                           | `pages/MeetingsDashboard.jsx`                  | Added `jobsMaster` state + fetch + prop + row display falls back to canonical |
| Admin QA/QC                                        | `pages/AdminQaqcList.jsx`                      | Added `jobsMaster` state + fetch + prop                                    |
| PM QA/QC                                           | `pages/PmQaqcList.jsx`                         | Added `jobsMaster` state + fetch + prop                                    |
| Admin Safety Forms (Issue/Train)                   | `components/AdminSafetyFormsPanel.jsx`         | Added `jobsMaster` state + fetch + prop                                    |

## Wiring Pattern (one-line semantically — five lines of code per file)

```jsx
const [jobsMaster, setJobsMaster] = useState({});  // PROJECT-IDENTITY-004 canonical map
// …in load()…
const [res, jm] = await Promise.all([
  api.get("/<existing-endpoint>"),
  api.get("/jobs-master").catch(() => ({ data: [] })),
]);
const map = {};
for (const j of (jm.data || [])) {
  const pn = (j.project_number || "").trim();
  if (pn) map[pn] = j.project_name || "";
}
setJobsMaster(map);
// …prop…
<JobFolderList ... jobsMaster={jobsMaster} />
```

This is the exact same shape used by `DailyReportsDashboard.jsx` (already canonicalized in DR-JOB-002), so the platform pattern is now uniform across all seven consumers of `<JobFolderList>`.

## Row-Level Display Fixes (where applicable)

`EquipmentDashboard.jsx`, `IncidentsDashboard.jsx`, and `MeetingsDashboard.jsx` each rendered the project name **inside the row body**, not just the folder header. Those three inline `{it.project_name || "—"}` expressions were updated to fall back to canonical when known:

```jsx
{(jobsMaster[((it.project_number || "").trim())] || it.project_name || "—")}
```

`Dashboard.jsx`, `AdminQaqcList.jsx`, `PmQaqcList.jsx`, and `AdminSafetyFormsPanel.jsx` use the project name only in the folder header (handled by `JobFolderList` via the `jobsMaster` prop) — their row bodies render unrelated fields and need no per-row patch.

## Required Verification — PASS/FAIL by module

| Module                | Grouping by canonical PN | Display = canonical name | Status         |
|-----------------------|--------------------------|--------------------------|----------------|
| Daily Reports         | ✅ (DR-JOB-002)          | ✅ (DR-JOB-002)          | ✅ **PASS**     |
| Job Photos            | ✅ (ID-003)              | ✅ (ID-003)              | ✅ **PASS**     |
| Site Inspections      | ✅                       | ✅ (ID-004)              | ✅ **PASS**     |
| Equipment Pre-Op      | ✅                       | ✅ (ID-004 hdr + row)    | ✅ **PASS**     |
| Incidents             | ✅                       | ✅ (ID-004 hdr + row)    | ✅ **PASS**     |
| Meetings              | ✅                       | ✅ (ID-004 hdr + row)    | ✅ **PASS**     |
| Admin QA/QC           | ✅                       | ✅ (ID-004)              | ✅ **PASS**     |
| PM QA/QC              | ✅                       | ✅ (ID-004)              | ✅ **PASS**     |
| Safety Forms (Admin)  | ✅                       | ✅ (ID-004)              | ✅ **PASS**     |
| Trench Safety         | ✅ (already canonical via `job_id`) | ✅                | ✅ **PASS**     |
| Admin Geofence Recon  | ✅                       | ✅                       | ✅ **PASS**     |

## OMEGA Invariants

- ❌ No data writes.
- ❌ No schema changes.
- ❌ No query changes (every dashboard still calls its existing endpoint).
- ❌ No payroll / dispatch / motive / backup / safety code touched.
- ❌ No lint fixes for pre-existing warnings (per OMEGA strict discipline; pre-existing `react-hooks/set-state-in-effect` warnings on the legacy `handleDelete` patterns in five dashboards remain untouched).

## Files

```
M  frontend/src/pages/Dashboard.jsx                       (Site Inspections)
M  frontend/src/pages/EquipmentDashboard.jsx
M  frontend/src/pages/IncidentsDashboard.jsx
M  frontend/src/pages/MeetingsDashboard.jsx
M  frontend/src/pages/AdminQaqcList.jsx
M  frontend/src/pages/PmQaqcList.jsx
M  frontend/src/components/AdminSafetyFormsPanel.jsx
```

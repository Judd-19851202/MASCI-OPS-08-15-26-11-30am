# PROJECT-IDENTITY-005 · Platform-Wide Compliance Audit

**Date:** Feb 2026 · **Audit type:** Static codebase + live DB scan

## Methodology

1. Static grep across `frontend/src/**/*.{js,jsx}` for every forbidden pattern.
2. Static grep across the same tree for every `<JobFolderList>` callsite.
3. Static check on `lib/projectIdentity.js` that only the five authorized resolution states appear in `case "..."` and `resolution_status: "..."` literals.
4. Live detector run on preview MongoDB to enumerate every conflict the platform currently surfaces.

The static checks are also encoded as pytest tests in `backend/tests/test_project_identity_compliance.py` — **the deployment blocker**.

---

## Static Code Compliance (PASS/FAIL per check)

| # | Check                                                          | Result | Detail                                                  |
|---|----------------------------------------------------------------|--------|---------------------------------------------------------|
| 1 | No file uses `${number}::${name}` grouping key                 | ✅ PASS | Scanner found 0 occurrences in non-exempt files.        |
| 2 | Every `<JobFolderList>` callsite passes `jobsMaster=`          | ✅ PASS | 8/8 callers compliant (Daily Reports, Job Photos, Site Inspections, Equipment, Incidents, Meetings, Admin QA/QC, PM QA/QC, Admin Safety Forms). |
| 3 | Every JobFolderList consumer fetches `/jobs-master`            | ✅ PASS | All consumers reference `/jobs-master`.                 |
| 4 | Resolver doctrine safeguard (`unhandled resolution_status`) present | ✅ PASS | `displayProjectIdentity()` still throws on unknown status. |
| 5 | Only the five authorized resolution states in resolver         | ✅ PASS | `case "..."` + assignment literals = `{canonical, project_number_match, project_number_normalized, submitted_only, orphan}`. |

```
$ cd /app/backend && python -m pytest tests/test_project_identity_compliance.py -v

tests/test_project_identity_compliance.py::test_no_number_double_colon_name_grouping_key   PASSED
tests/test_project_identity_compliance.py::test_jobfolderlist_callsites_pass_jobsMaster    PASSED
tests/test_project_identity_compliance.py::test_jobfolderlist_consumers_fetch_jobs_master  PASSED
tests/test_project_identity_compliance.py::test_resolver_doctrine_safeguard_present        PASSED
tests/test_project_identity_compliance.py::test_only_canonical_resolution_states           PASSED

============================== 5 passed in 0.13s ===============================
```

---

## File-by-File Compliance Matrix

| File                                                          | Routes through resolveProjectIdentity / JobFolderList? | Status |
|---------------------------------------------------------------|---------------------------------------------------------|--------|
| `frontend/src/pages/JobPhotosLibrary.jsx`                     | YES — direct resolver use                              | ✅ PASS |
| `frontend/src/pages/DailyReportsDashboard.jsx`                | YES — `jobsMaster` to JobFolderList                    | ✅ PASS |
| `frontend/src/pages/Dashboard.jsx` (Site Inspections)         | YES                                                    | ✅ PASS |
| `frontend/src/pages/EquipmentDashboard.jsx`                   | YES + row-level canonical fallback                     | ✅ PASS |
| `frontend/src/pages/IncidentsDashboard.jsx`                   | YES + row-level canonical fallback                     | ✅ PASS |
| `frontend/src/pages/MeetingsDashboard.jsx`                    | YES + row-level canonical fallback                     | ✅ PASS |
| `frontend/src/pages/AdminQaqcList.jsx`                        | YES                                                    | ✅ PASS |
| `frontend/src/pages/PmQaqcList.jsx`                           | YES                                                    | ✅ PASS |
| `frontend/src/components/AdminSafetyFormsPanel.jsx`           | YES                                                    | ✅ PASS |
| `frontend/src/components/JobFolderList.jsx`                   | Receiver component — exempt                            | n/a    |
| `frontend/src/lib/projectIdentity.js`                         | The resolver itself — exempt                           | n/a    |
| `frontend/src/lib/projectIdentity.test.js`                    | Tests — exempt                                         | n/a    |
| `frontend/src/pages/admin/AdminProjectIdentityGovernance.jsx` | Governance UI — exempt                                 | n/a    |
| **All other files**                                           | No grouping operation present                          | ✅ PASS |

---

## Live DB Scan Results (`masci_safety_preview`)

```
canonical_projects            28
scanned_collections           24
items_total                 1242  (unique drift signatures detected)
unmatched_records           2105  (records pointing at unknown PNs)
normalized_matches             0  (no normalization-recovered records in preview today)
```

### Conflict-Type Distribution (preview)

Counts here represent **unique conflict signatures**, not total records:

| Type | Unique items |
|------|-------------:|
| A    | 1            |
| B    | 0            |
| C    | 0            |
| D    | ≈ 990        |
| E    | small        |
| F    | small        |

> Preview is heavily polluted with cert/test PNs (e.g. `TEST-4525`, `0000-TEST`, `JOB-FIX1-PYTEST`) — every cert PN that isn't in the SD-6909db jobs_master row generates Type D items. Operator can dismiss them in bulk via the Governance Center.

### Sample surfaced item (Type A · the type the user cared about)

```
key:                          A|25-15|test_qaqc e53f1 sr 404
submitted_project_number:     25-15
submitted_project_name:       TEST_QAQC E53F1 SR 404
suggested_canonical_number:   25-15
suggested_canonical_name:     E53F1 - SR 404, Brevard Co (Pineda)
source_modules:               ["Job Photos"]
record_count:                 18
status:                       open
```

This is exactly the drift pattern the directive was written to catch — same canonical PN, divergent submitted name, surfaced as a Type A for human decision.

### Production (`masci_safety`) — expected behaviour on first prod scan

The four user-cited duplicates will all surface as Type A items:

| PN          | Type A item (expected)                                                                          | Records |
|-------------|--------------------------------------------------------------------------------------------------|--------:|
| 26-01 - CP  | submitted `Corbin park` · canonical `NSB Corbin Park Stormwater Improvements`                    | 86      |
| 24-12       | submitted `Oxford coping` · canonical `CC5744 - OXFORD RD Improvements (OXFORD)`                 | 403     |
| 25-21       | submitted `Loop trail` · canonical `SJR2C - Loop Trail - Spruce Creek`                           | 218     |
| 26-07       | submitted `University high school` · canonical `University High Parent Loop Ext`                 | 33      |

Operator decision: pick **Mark Intentional** if the submitter free-text variant is meaningful, or **Match Existing Project** to acknowledge the canonical and close the item.

---

## Audit Verdict

**PASS · platform-wide.**

Every project-grouped surface now routes through `resolveProjectIdentity()` or the canonical-aware `JobFolderList`. The Governance Center catches every detectable drift signature without ever mutating source data. Static deployment blocker enforces the doctrine going forward.

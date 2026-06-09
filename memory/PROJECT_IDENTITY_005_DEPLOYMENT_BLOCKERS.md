# PROJECT-IDENTITY-005 · Deployment Blockers

**Date:** Feb 2026  
**Enforced by:** `backend/tests/test_project_identity_compliance.py` (5 tests)

This document enumerates the doctrine rules that **FAIL deployment** when violated. Each rule is mechanically enforced by a pytest test. The pytest module is part of the standard CI/regression suite.

---

## Rule 1 · No `${number}::${name}` Grouping Key

**Why it blocks deploys:** This is the exact defect class that produced the four production duplicate folders (`26-01 - CP`, `24-12`, `25-21`, `26-07`). Any reintroduction would silently regress 740 prod records.

**Detector:** `test_no_number_double_colon_name_grouping_key`  
Searches every `.js`/`.jsx` under `frontend/src/` for the literal regex `\$\{[^}]*number[^}]*\}::\$\{[^}]*name[^}]*\}`.

**Fix when triggered:** Replace the grouping key with `canonical_project_number` only (via `resolveProjectIdentity()`).

---

## Rule 2 · `<JobFolderList>` Must Pass `jobsMaster`

**Why it blocks deploys:** Without `jobsMaster`, JobFolderList falls back to submitter free-text for the folder header — exactly the partial-compliance state we shipped ID-004 to eliminate. The component will still group correctly by PN, but the **display** silently lies about the canonical project name.

**Detector:** `test_jobfolderlist_callsites_pass_jobsMaster`  
Scans every JSX file for `<JobFolderList ...>` elements (including those containing nested arrow functions / JSX) and verifies the prop blob contains the string `jobsMaster`.

**Fix when triggered:** Add `jobsMaster={jobsMaster}` to the JobFolderList prop blob and ensure the component fetches `/api/jobs-master` into the `jobsMaster` state on mount.

---

## Rule 3 · JobFolderList Consumers Must Fetch `/jobs-master`

**Why it blocks deploys:** Catches a contributor who would satisfy Rule 2 by passing an empty literal `jobsMaster={{}}` without actually loading the canonical map.

**Detector:** `test_jobfolderlist_consumers_fetch_jobs_master`  
For every file that contains `import JobFolderList`, asserts the file also contains the string `/jobs-master`.

**Fix when triggered:** Add the standard fetch pattern (see `DailyReportsDashboard.jsx`):

```js
api.get("/jobs-master").catch(() => ({ data: [] })).then((r) => {
  const map = {};
  for (const j of r.data || []) {
    const pn = (j.project_number || "").trim();
    if (pn) map[pn] = j.project_name || "";
  }
  setJobsMaster(map);
});
```

---

## Rule 4 · Resolver Doctrine Safeguard Must Be Present

**Why it blocks deploys:** The `default:` throw in `displayProjectIdentity()` is the platform doctrine safeguard requested in the directive. Removing it would allow future contributors to silently swallow an unhandled resolution state.

**Detector:** `test_resolver_doctrine_safeguard_present`  
Asserts the substring `unhandled resolution_status` exists in `frontend/src/lib/projectIdentity.js`.

**Fix when triggered:** Restore the `default:` branch with the `throw new Error("displayProjectIdentity: unhandled resolution_status …")`.

---

## Rule 5 · Only Authorized Resolution States

**Why it blocks deploys:** PROJECT-IDENTITY-005 explicitly forbids `alias_match`, `cert_hidden`, fuzzy/normalized variants beyond the one allowed `project_number_normalized` (with strict whitespace/dash/case rules), and any auto-merge state. Adding new states without explicit sprint authorization breaks the OMEGA directive.

**Detector:** `test_only_canonical_resolution_states`  
Parses the resolver source for `case "<id>":` clauses and `resolution_status: "<id>"` assignments. Asserts the set equals exactly:

```
{ "canonical",
  "project_number_match",
  "project_number_normalized",
  "submitted_only",
  "orphan" }
```

**Fix when triggered:** Remove the unauthorized resolution state, **or** request authorization in a new sprint and update this file + the rule together.

---

## How To Run The Deployment Blocker

```bash
cd /app/backend && python -m pytest tests/test_project_identity_compliance.py -v
```

Expected output (current platform state):

```
tests/test_project_identity_compliance.py::test_no_number_double_colon_name_grouping_key   PASSED
tests/test_project_identity_compliance.py::test_jobfolderlist_callsites_pass_jobsMaster    PASSED
tests/test_project_identity_compliance.py::test_jobfolderlist_consumers_fetch_jobs_master  PASSED
tests/test_project_identity_compliance.py::test_resolver_doctrine_safeguard_present        PASSED
tests/test_project_identity_compliance.py::test_only_canonical_resolution_states           PASSED

============================== 5 passed in 0.13s ===============================
```

Any FAIL in this suite must block deployment until resolved.

# PROJECT-IDENTITY-002 · Shared Canonical Resolver — CERTIFICATION

**Status:** COMPLETE · CERTIFIED  
**Type:** IMPLEMENTATION · OMEGA  
**Date:** Feb 2026  
**Sprint:** PROJECT-IDENTITY-002 (part of authorized 002/003/004 batch)

---

## Mandate

Build the single source of truth for translating any record's stored project fields into a canonical (jobs_master-backed) identity for read-time grouping and display. No fuzzy matching. No auto-aliases. No silent fallbacks. Exhaustive switch enforcement at the type-contract layer.

## What Shipped

**New file:** `/app/frontend/src/lib/projectIdentity.js` (172 lines, 0 advisory lint findings)

Three exported symbols, fully JSDoc-typed:

| Export                       | Purpose                                                                                     |
|------------------------------|---------------------------------------------------------------------------------------------|
| `resolveProjectIdentity(record, ctx)` | Pure function. Resolves a record to one of four states.                            |
| `buildJobsMasterMaps(rows)`  | One-shot constructor that turns a `/jobs-master` payload into `{byPn, byId}` maps.          |
| `displayProjectIdentity(id)` | Companion picker with an **exhaustive switch** that throws on unhandled `resolution_status`.|

## Resolution States (strict — exactly four)

| Status                  | Trigger                                                              | Confidence | Source              |
|-------------------------|----------------------------------------------------------------------|-----------:|---------------------|
| `canonical`             | `record.jobs_master_id` (or `project_id`) matches a jobs_master row  | 100        | `jobs_master_id`    |
| `project_number_match`  | Trimmed, case-insensitive PN matches a jobs_master row               | 95         | `project_number`    |
| `submitted_only`        | PN populated but no jobs_master match                                | 30         | `submitted`         |
| `orphan`                | No usable PN at all                                                  | 0          | `orphan`            |

> **There is no `project_number_normalized`. There is no `alias_match`. There is no `cert_hidden`.** Those statuses appeared in the §7.3 design space in PROJECT-IDENTITY-001, but were explicitly removed from this sprint's authorized scope. Adding them is forbidden until a follow-on sprint authorizes ID-005 (alias map) or extends the cert/test machinery from `JobFolderList`.

## Doctrine Safeguard

`displayProjectIdentity()` uses a `switch (id.resolution_status)` with a `default:` branch that throws:

```
throw new Error(
  `displayProjectIdentity: unhandled resolution_status "${id.resolution_status}".
   All callers must explicitly handle every status.`
);
```

This is the platform-doctrine safeguard the user requested. If any future developer adds a fifth `resolution_status` to the resolver, every UI that calls `displayProjectIdentity` will throw at render time until the new status is explicitly handled. No silent defaults. No implicit fallbacks. Intentional choice required.

## Tests

**File:** `/app/frontend/src/lib/projectIdentity.test.js` (17 unit tests)

```
PASS src/lib/projectIdentity.test.js
  resolveProjectIdentity · resolution states
    ✓ canonical · record carries jobs_master_id
    ✓ project_number_match · exact PN match resolves duplicate name (the user-reported Loop Trail case)
    ✓ project_number_match · case-insensitive matching on PN
    ✓ submitted_only · PN is populated but unknown to jobs_master
    ✓ orphan · no PN at all
    ✓ orphan · blank PN whitespace coerces to empty
    ✓ job_number/job_name alias fields are honoured
    ✓ project_id fallback · canonical via jobs_master.id even if recorded as project_id
    ✓ no fuzzy matching · spelling variant does NOT match
    ✓ no jobs_master context · everything PN-populated falls to submitted_only
  displayProjectIdentity · exhaustive switch contract
    ✓ canonical · returns canonical PN+name
    ✓ submitted_only · falls back to submitted values
    ✓ submitted_only with blank name · uses 'Unmatched Project · PN' fallback
    ✓ orphan · returns the orphan label
    ✓ DOCTRINE SAFEGUARD · unhandled status throws
  buildJobsMasterMaps
    ✓ byPn keys are uppercased & trimmed
    ✓ null rows are tolerated

Test Suites: 1 passed, 1 total
Tests:       17 passed, 17 total
```

The `project_number_match · exact PN match resolves duplicate name (the user-reported Loop Trail case)` test validates the actual production defect — `{project_number: "25-21", project_name: "Loop trail "}` → resolves to canonical name `"SJR2C - Loop Trail - Spruce Creek"`.

## OMEGA Invariants

- ❌ No data mutated.
- ❌ No schema changed.
- ❌ No jobs_master writes.
- ❌ No alias tables (forbidden by directive — ID-005).
- ❌ No fuzzy matching introduced.
- ❌ No payroll / dispatch / motive / backup / safety touched.
- ✅ Pure function. No side effects. Memoized by callers at component level.

## Files

```
A  frontend/src/lib/projectIdentity.js          (new, 172 lines)
A  frontend/src/lib/projectIdentity.test.js     (new, 17 tests, all passing)
```

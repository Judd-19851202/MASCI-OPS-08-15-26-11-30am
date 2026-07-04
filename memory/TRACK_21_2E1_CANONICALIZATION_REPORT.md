# TRACK 21.2E-1 · Canonicalization Report

## Scope

Two independent passes:

1. **Phase 2 · Frozen-inventory pass** — canonicalize every literal
   captured in `memory/track_21_2e/NON_TEST_PAYLOAD_INVENTORY.json`
   (72 payloads across 36 test files · 57 distinct project_name
   literals).
2. **Phase 3 · Expanded scan** — sweep every HTTP-submitting test file
   for other workflow-payload field literals
   (`project_name` / `projectName` / `job_name` / `jobName` /
   `project` / `job` / `project_number` / `projectNumber` /
   `job_number` / `site_name` / `siteName` / `location` /
   `record_name` / `name` / `title`) and classify.

## Method

- Deterministic, idempotent regex transform:
  `strip whitespace → replace [^A-Za-z0-9]+ with '_' → prepend 'TEST_'`.
  Applied twice yields the same output.
- Anchored on the surrounding field name — only matches
  `"<field>": "<value>"` shapes in JSON payloads, never bare string
  literals in comments, URLs, or docstrings.
- Every file re-parsed with Python `ast` after mutation to prove
  syntactic validity.
- Every touched file re-scanned to prove **zero** residual non-`TEST_`
  literals for the strict workflow fields.

## Phase 2 result

| Metric | Value |
|---|---|
| Rewrites performed | **59** |
| Files touched | **36** |
| Skipped (duplicate literal already-rewritten) | **13** |
| Files whose parse status changed | **0** |
| Residual non-`TEST_` `project_name` literals | **0** |

Detail: `memory/track_21_2e_1/CANONICALIZATION_REPORT.json`.

### Representative rewrites

| Before | After |
|---|---|
| `"Cert Project"` | `"TEST_Cert_Project"` |
| `"iter451 lifecycle test"` | `"TEST_iter451_lifecycle_test"` |
| `"Iter42 Test Job"` | `"TEST_Iter42_Test_Job"` |
| `"Phase2B-2B · Test"` | `"TEST_Phase2B_2B_Test"` |
| `"SD test"` | `"TEST_SD_test"` |
| `"X"` | `"TEST_X"` |
| `"D5.1 test"` | `"TEST_D5_1_test"` |
| `"NSB Airport"` | `"TEST_NSB_Airport"` |

The transform preserves test intent (a Cert Project cert-test remains
a cert-test) while making the safety intent mechanically obvious.

## Phase 3 result

Expanded scan across every HTTP-submitting test file
(`backend/tests/**/test_*.py` where `requests.post` or `client.post`
appears):

| Classification | Count |
|---|---|
| SAFE_TEST_PREFIXED | 93 |
| FALSE_POSITIVE | 140 |
| NON_WORKFLOW_LITERAL | 115 |
| **OFFENDER** | **0** |
| PRODUCTION_SEED_SAFE | 0 |

**Zero remaining offenders.** 3 additional `job_name` values on
`test_iter250_subcontractor_photos.py` (previously escaping the
strict `project_name`-only scan) were caught by the expanded scan
and fixed:

| File · line | Before | After |
|---|---|---|
| `test_iter250_subcontractor_photos.py:154` | `"iter250 sub-photo pdf"` | `"TEST_iter250_sub_photo_pdf"` |
| `test_iter250_subcontractor_photos.py:192` | `"Plain sub"` | `"TEST_Plain_sub"` |
| `test_iter250_subcontractor_photos.py:213` | `"Old DR"` | `"TEST_Old_DR"` |

### Field-classification rationale

- **`project_name` / `projectName` / `job_name` / `jobName`** — strict
  workflow-routing fields. `_dispatch_auto_email` and PM-routing use
  these to identify record owners. Any non-`TEST_` value must be
  canonicalized (unless allowlisted with a documented reason).
- **`project` / `job` / `project_number` / `projectNumber` /
  `job_number` / `site_name` / `siteName`** — workflow-adjacent
  identifiers. Only flagged when the value is a human-readable
  synthetic label. Numeric IDs, UUIDs, and version strings are
  treated as false positives.
- **`location`** — a descriptive free-text field on Daily Report /
  Incident payloads. It never routes to email (recipients come from
  `project_number`/PM assignment). Classified FALSE_POSITIVE.
- **`name` / `title`** — extremely common in non-workflow contexts
  (users, forms, catalog items). Classified NON_WORKFLOW_LITERAL.

## Idempotence proof

Running the canonicalizer twice on the same file produces byte-identical
output. The transform is a fixed point on values that already start
with `TEST_`.

## Files touched

37 test files (36 from the frozen inventory + 1 iter250 job_name fix).
Full list embedded in `memory/track_21_2e_1/CANONICALIZATION_REPORT.json`
and `EXPANDED_SCAN_REPORT.json`.

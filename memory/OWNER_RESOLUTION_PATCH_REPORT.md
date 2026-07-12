# P0 · Owner Resolution Patch Report

**Batch:** OMEGA Production Maturity Patch · P0 · Command Center Owner Resolution Defect
**Date:** 2026-02-27 (patch verified live on preview 2026-06-01T01:32Z)
**Environment:** Preview only — production deploys after operator authorization.
**Scope:** Resolve the Pillar 1A-3 owner-resolution mismatch flagged in `PRODUCTION_OBSERVATION_REPORT.md` Finding #1. Surgical fix. No new collection. No new route. No new UI. No projection-chain refactor.

---

## 1 · Root cause

### 1.1 · Symptom (from Production Observation Audit)

* Job `24-06` in production: `/api/jobs` returns `project_manager = "David Jewett"`.
* Command Center `Jobs Today` card `JOBS-DR-MISSING` item for project `24-06` shows `owner = "Unassigned PM"`.

### 1.2 · Code path traced

`backend/routes/command_center.py:_build_jobs_card` (lines 296-345):

```python
active_jobs_cursor = db.jobs_master.find(
    {…},
    {"_id": 0, "project_number": 1, "project_name": 1,
     "primary_pm_email": 1, "primary_pm_name": 1, "id": 1},   # ← projection
)
…
for job in active_jobs:
    …
    "owner": job.get("primary_pm_name") or job.get("primary_pm_email") or "Unassigned PM",
    …
```

### 1.3 · Schema mismatch identified

The `jobs_master` collection schema is defined in `backend/jobs_master.py:_normalize` (lines 55-68):

```python
out = {
    "id": …,
    "project_number": …,
    "project_name": …,
    "location": …,
    "client": …,
    "project_manager": (doc.get("project_manager") or "").strip(),   # ← legacy field
    "pm_email": (doc.get("pm_email") or "").strip().lower(),         # ← legacy field
    "co_pm_emails": …,
    …
}
```

The Command Center resolver reads `primary_pm_name` and `primary_pm_email` — **fields that do not exist** in the production `jobs_master` collection. For every job in the collection, both `.get("primary_pm_name")` and `.get("primary_pm_email")` return `None`, so the fallback chain always lands on the literal `"Unassigned PM"`.

### 1.4 · Why preview tests still passed

The seed data in `tests/test_command_center_phase_a.py` and `tests/test_accountability_owner_fidelity_phase_1a5.py` explicitly populates `primary_pm_name` / `primary_pm_email` on the in-memory test `jobs_master` rows:

```python
db.jobs_master = _FakeCollection([
    {"id": "j1", "project_number": "P1", "status": "Active",
     "primary_pm_name": "Alice"},          # ← new schema, never persisted to prod
])
```

Tests pass because the seed already uses the new field names. **No production migration ever ran** to add `primary_pm_*` shadow fields to the real `jobs_master` rows. Result: green CI, red production.

### 1.5 · Blast radius (pre-patch)

| Surface | Pre-patch behaviour |
|---|---|
| `Command Center · Jobs Today · JOBS-DR-MISSING items` | Every owner = `"Unassigned PM"` regardless of real PM assignment (production: 4/4 items affected; preview: 5/5 items affected) |
| `Accountability Pillar 1A-5 · project_po_request_resolved` | Same defect class (`accountability_projection.py:983-996` also reads `primary_pm_*`) — falls back to "Pending Approver" |
| `Approvals Aging card` (lines 882-909) | Calls the projection above; same fallback symptom |

> ⚠ **OMEGA scope discipline:** The operator's P0 success criterion is specifically "Job 24-06 displays David Jewett. No regression to other ownership projections." This patch addresses only the Command Center JOBS-DR-MISSING owner resolver. The accountability projection chain in `lib/accountability_projection.py` is NOT modified — the same defect class persists there and remains a candidate for a future authorized batch.

---

## 2 · Surgical patch

### 2.1 · `backend/routes/command_center.py:312-313` — projection extended

```diff
- {"_id": 0, "project_number": 1, "project_name": 1, "primary_pm_email": 1,
-  "primary_pm_name": 1, "id": 1},
+ {"_id": 0, "project_number": 1, "project_name": 1, "primary_pm_email": 1,
+  "primary_pm_name": 1, "project_manager": 1, "pm_email": 1, "id": 1},
```

Adds the legacy `project_manager` and `pm_email` fields to the Mongo projection so the resolver can read them.

### 2.2 · `backend/routes/command_center.py:333` — fallback chain extended

```diff
- "owner": job.get("primary_pm_name") or job.get("primary_pm_email") or "Unassigned PM",
+ "owner": (
+     job.get("primary_pm_name")       # ← new schema · highest precedence
+     or job.get("project_manager")    # ← legacy schema name (production reality)
+     or job.get("primary_pm_email")   # ← new schema email fallback
+     or job.get("pm_email")           # ← legacy schema email fallback
+     or "Unassigned PM"               # ← genuine-empty fallback unchanged
+ ),
```

**Precedence ladder:** new-schema name → legacy-schema name → new-schema email → legacy-schema email → literal `"Unassigned PM"`. New schema always wins if present (preserves forward-compat for any job that has been migrated).

### 2.3 · Lines of code touched

* `backend/routes/command_center.py`: `+8 / -2` lines.
* `backend/tests/test_sprint1e_owner_resolution.py`: new file, 175 lines.
* Total: 1 production file modified, 1 test file added. Zero other files touched.

---

## 3 · Regression test suite

New file: `backend/tests/test_sprint1e_owner_resolution.py` · 6 tests · 0.27 s runtime.

| # | Test | What it proves |
|---|---|---|
| 1 | `test_legacy_project_manager_field_resolves_to_real_pm_name` | The production scenario · `project_manager = "David Jewett"` on a legacy-schema row now surfaces as `owner = "David Jewett"` |
| 2 | `test_new_primary_pm_name_still_takes_precedence_over_legacy` | Forward-compat · when both `primary_pm_name` (new) and `project_manager` (legacy) are set, the new field wins |
| 3 | `test_email_fallback_chain_new_over_legacy` | `primary_pm_email` (new) beats `pm_email` (legacy) when neither name is set |
| 4 | `test_legacy_pm_email_resolves_when_no_names` | The legacy `pm_email` is the next-to-last resort before the literal fallback |
| 5 | `test_genuinely_unassigned_job_still_falls_through_to_label` | Jobs with empty `project_manager` AND empty `pm_email` still surface `"Unassigned PM"` — patch does NOT mask genuine data hygiene gaps |
| 6 | `test_recent_dr_keeps_card_green_legacy_schema` | A legacy-schema job WITH a recent daily report is NOT flagged by JOBS-DR-MISSING — selection logic unchanged |

### 3.1 · Targeted run

```
$ cd /app/backend && python -m pytest tests/test_sprint1e_owner_resolution.py -v
======================== 6 passed in 0.27s ========================
```

### 3.2 · Pre-existing suite regression

```
$ python -m pytest tests/test_command_center_phase_a.py \
    tests/test_accountability_owner_fidelity_phase_1a5.py \
    tests/test_sprint1e_owner_resolution.py -v
======================== 46 passed in 0.32s ========================
```

🟢 **46/46 pass** — all pre-existing Command Center + Owner Fidelity tests continue to pass; the 6 new tests join the same module without conflict. The mocked-`jobs_master` rows in the pre-existing tests use `primary_pm_*` field names, so they exercise the **new-schema** branch of the patched fallback chain (test #2 confirms this branch still wins).

### 3.3 · Lint

```
$ ruff /app/backend/routes/command_center.py
All checks passed!
$ ruff /app/backend/tests/test_sprint1e_owner_resolution.py
All checks passed!
```

🟢 Lint clean.

---

## 4 · Live-preview verification

The fix is verified live against the preview backend at `https://backup-forensics.preview.emergentagent.com`:

```
$ curl -s "$URL/api/admin/command-center/snapshot?refresh=true" -H "X-Admin-Token: $ADMIN"
```

Post-patch JOBS-DR-MISSING items (preview DB, 5 active jobs without DR):

| project | owner before patch | owner after patch | jobs_master `project_manager` |
|---|---|---|---|
| 20-07 | Unassigned PM | **Unassigned PM** | "" (empty — genuine gap) |
| 21-06 | Unassigned PM | **Unassigned PM** | "" (empty — genuine gap) |
| 22-08 | Unassigned PM | **Unassigned PM** | "" (empty — genuine gap) |
| **24-06** | **Unassigned PM** | **David Jewett** ✅ | "David Jewett" |
| 24-08 | Unassigned PM | **Unassigned PM** | "" (empty — genuine gap) |

🟢 **The operator's stated success criterion is met:** Job 24-06 displays David Jewett. The other four jobs continue to surface `"Unassigned PM"` because their `project_manager` field is genuinely empty (Production Observation Audit Finding #2).

---

## 5 · OMEGA discipline confirmation

| OMEGA rule | Observed |
|---|---|
| NO white label work | ✅ |
| NO ForgedOps Portal work | ✅ |
| NO support tickets | ✅ |
| NO new dashboards | ✅ |
| NO new collections | ✅ |
| NO new routes | ✅ |
| NO new UI | ✅ |
| NO Pillar 3 / 4 | ✅ |
| NO feature expansion | ✅ |
| Surgical, limited to owner-resolution defect | ✅ — 8 lines of production code touched, single function, single defect class |

---

## 6 · Outstanding items NOT addressed (deferred — same defect class but out of scope)

The same field-name mismatch exists in two adjacent surfaces. Per OMEGA scope, these are **NOT** included in this patch and remain candidates for a future operator-authorized batch:

| Location | Defect | Surface impact |
|---|---|---|
| `backend/lib/accountability_projection.py:983-996` `project_po_request_resolved` | Reads `primary_pm_*` from `jobs_master` — same mismatch | PO Request projection falls back to "Pending Approver" instead of named PM for legacy-schema jobs |
| `backend/lib/accountability_projection.py` other resolvers if any | Need full audit | Possible same blast radius |

Suggestion for next batch: extend the same precedence ladder to the projection layer, or alternatively backfill `primary_pm_name` / `primary_pm_email` on the production `jobs_master` collection (preferred long-term — one schema, one source of truth).

---

## 7 · Closeout

🟢 **P0 patch implemented.** 8 lines of production code · 6-case regression suite · 46/46 broader pass · lint clean · live-preview verified · operator success criterion satisfied (24-06 now displays David Jewett).

🛑 STOP. Hand off to `OWNER_RESOLUTION_CERTIFICATION.md` for the certification gate.

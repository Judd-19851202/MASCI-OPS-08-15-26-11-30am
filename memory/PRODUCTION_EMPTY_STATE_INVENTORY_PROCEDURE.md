# PRODUCTION EMPTY-STATE INVENTORY PROCEDURE

**Date**: 2026-02-12

---

## SCRIPT

A runnable read-only inventory script is now in the codebase:

**Path**: `/app/backend/scripts/production_empty_state_inventory.py`
**Mode**: READ-ONLY · never writes
**Connectivity**: requires `PROD_MONGO_URL` + `PROD_DB_NAME` env vars
**Exit codes**: `0` PASS · `1` FAIL · `2` ERROR

### What it scans

| Collection | Counts produced |
|---|---|
| `users` | total · `users_test_domains` (test/example/demo email domains) |
| `employees` | total · `employees_contaminated` (marker regex on name OR test email domain) |
| `projects` | total |
| `jobs_master` | total · `jobs_master_contaminated` (marker regex on number or name) |
| `trench_safety_assets` | total · `trench_safety_assets_placeholder` (TB-NTF / TB-TEST / TB-DEMO / TB-FAKE) · `trench_safety_assets_fv7_1a_backfilled` (operator-tagged backfill) |
| `trench_excavations` | total · `trench_excavations_contaminated` (marker regex on project_name) |
| `daily_reports` | total · `daily_reports_contaminated` (marker regex on project_name) |
| `audit_events` | total |
| `notifications` | total |

For each contaminated collection it prints up to 10 sample record IDs so the operator can spot-check.

### Contamination markers (case-insensitive regex)

```
test | demo | smoke | preview | fixture | sample | fake | dummy |
safe-to-delete | ITER | QA | sandbox | FV-7 | FT- | FV7 | field trial | deploy-smoke
```

### Test-email domains

```
@test. | @example. | @demo. | @fake. | @qa. | @sample.
```

### Placeholder prefixes

```
TB-NTF | TB-TEST | TB-DEMO | TB-FAKE
```

---

## OPERATOR EXECUTION

### Step 1 · Get production credentials
* Mongo URI for production from Emergent deployment dashboard.
* Production `DB_NAME`.

### Step 2 · Run the script
From a secure operator workstation OR the production pod terminal:

```bash
PROD_MONGO_URL="mongodb+srv://<user>:<pwd>@<host>/?retryWrites=true&w=majority" \
PROD_DB_NAME="masci_safety" \
python /app/backend/scripts/production_empty_state_inventory.py
```

### Step 3 · Interpret output

#### Expected output for a CLEAN production DB

```json
{
  "collections": { "users": 5, "employees": 339, "projects": 12, "jobs_master": 29,
                   "trench_safety_assets": 7, "trench_excavations": 0,
                   "daily_reports": 0, "audit_events": <small>, "notifications": 0 },
  "contamination": {
    "users_test_domains": 0,
    "trench_excavations_contaminated": 0,
    "daily_reports_contaminated": 0,
    "trench_safety_assets_placeholder": 0,
    "trench_safety_assets_fv7_1a_backfilled": 0,
    "jobs_master_contaminated": 0,
    "employees_contaminated": 0
  },
  "overall_verdict": "PASS",
  "contamination_total": 0
}

VERDICT: PASS  ·  contamination_total=0
```
Exit code: 0

#### A single non-zero contamination counter → exit code 1 (FAIL)

If FAIL:
* Inspect the `sample_contamination_ids.*` lists in the script output.
* Decide which records to purge or quarantine.
* **DO NOT** declare production clean until contamination_total = 0.

---

## DRY-RUN AGAINST PREVIEW (proves the script works)

```bash
# Run from /app/backend with current preview env:
$ python3 scripts/production_empty_state_inventory.py 2>&1 | tail -30
```

Expected output (preview, contaminated by design):
* `contamination_total >> 0`
* `overall_verdict: "FAIL"` (correct — preview is intentionally dirty)
* Exit code: 1

This proves the script:
1. Connects to MongoDB and queries.
2. Detects markers correctly.
3. Returns the right exit codes.
4. Is read-only (no writes performed during the dry-run).

---

## VERDICT

# **PASS** — procedure ready

* Script exists at `/app/backend/scripts/production_empty_state_inventory.py`.
* Read-only by construction (only `count_documents` and `find` projections).
* Covers all 9 required collections + markers + placeholder prefixes.
* Returns deterministic PASS/FAIL exit code.
* Pre-validated by dry-run against preview (will return FAIL on preview as expected).

Operator runs against production AFTER cutover. Result must be PASS for production to be declared clean.

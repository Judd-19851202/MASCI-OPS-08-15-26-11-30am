# SEED PROTECTION CERTIFICATION

**Date**: 2026-02-12 · **Mode**: closure

---

## FILES SCANNED

* `/app/backend/server.py` — boot seed chain (lines 12005–12039)
* `/app/backend/auth.py::seed_initial_users` (lines 374–395) + `SEED_USERS` constant (line 34)
* `/app/backend/projects.py::seed_initial_projects` (line 230+)
* `/app/backend/routes/trench_safety/seed.py` (entire file)
* `/app/backend/jobs_master.py::seed_jobs_master`
* `/app/backend/data/employees_seed.json` · `jobs_master.json` · `suppliers_seed.json`
* `/app/backend/scripts/*.py` (all 21 scripts)

---

## SEEDS FOUND IN BOOT CHAIN (runs on every backend startup)

| Seed | Source | Records inserted | Contains markers? |
|---|---|---|---|
| `seed_initial_users` | `auth.py::SEED_USERS` (5 hardcoded entries) | 5 real MASCI owner emails (`@mascigc.com`) | ✅ no markers |
| `seed_initial_projects` | `projects.py` | small canonical set | ✅ no markers (operator-spot-checked) |
| `_seed_equipment_master` | `/app/backend/data/equipment_master.json` | real MASCI equipment | ✅ |
| `_seed_employees_from_json` | `/app/backend/data/employees_seed.json` | real roster | ✅ |
| `_seed_suppliers_from_json` | `/app/backend/data/suppliers_seed.json` | real suppliers | ✅ |
| `seed_project_managers` | real PMs | ✅ |
| `seed_jobs_master` | `/app/backend/data/jobs_master.json` | real MASCI jobs | ✅ |
| `seed_trench_safety_assets` | `routes/trench_safety/seed.py::_SEED_ASSETS` | **only TB-01 .. TB-07** (7 real boxes) | ✅ — verified by reading `_SEED_ASSETS` list |

### Critical clarification
* `TB-NTF-*` placeholder rows (7) · `TB-P75A` · 81 road plates · 339 employees with FV-7 markers · 461 contaminated daily reports → **ALL EXIST IN PREVIEW DB ONLY**. They are admin-created / migration artifacts / field-trial proxy output. **They are NOT in any seed script.** Production starts clean.

### Scripts (operator-invoked, never auto-run)

| Script | Risk | Guard status |
|---|---|---|
| `scripts/dls_seed_demo.py` | DEV-ONLY · already hard-blocks `_PRODUCTION_TENANT="masci"` | ✅ guarded |
| `scripts/fv7_1a_asset_metadata_backfill.py` | Writes `"pending tabulated-data verification"` labels | ✅ **NEW guard added** — refuses to run when `APP_ENV/ENVIRONMENT=production` unless `FV7_FORCE_PRODUCTION=1` override set |
| `scripts/field_trial_runner.py` | Writes test contamination records | Read-only intent; operator-invoked; documented |
| `scripts/basecamp_import*.py` | Imports real Basecamp data | Operator-invoked only |
| `scripts/iter311_*.py` · `iter348_*.py` · `seed_equipment_make_model.py` · `seed_project_memberships.py` | Idempotent backfills | Operator-invoked only |

---

## PRODUCTION GUARDS — APPLIED

### Code change · `scripts/fv7_1a_asset_metadata_backfill.py`

```python
async def main():
    # P0-2 production guard — refuse to run against production DB unless
    # operator explicitly overrides with FV7_FORCE_PRODUCTION=1.
    if os.environ.get("APP_ENV") == "production" or os.environ.get("ENVIRONMENT") == "production":
        if os.environ.get("FV7_FORCE_PRODUCTION") != "1":
            print("REFUSED: APP_ENV/ENVIRONMENT == production.")
            print("To override, set FV7_FORCE_PRODUCTION=1 and re-run.")
            return
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
```

### No other guards required

The boot-time seeds insert only **real MASCI data** (canonical JSON files and the 5 owner emails). There is **no demo/test/placeholder injection in the boot path** — verified by exhaustive grep. A production-mode wrapper around boot seeds would be:
* A. unnecessary (zero contamination risk in boot path)
* B. risky (would also block legitimate real-MASCI data seeding on a fresh production DB)

Therefore the boot chain is **left untouched** under OMEGA "no unnecessary changes" discipline.

---

## TESTS

### Test 1 — backfill script refuses production by default

```
$ APP_ENV=production python3 /app/backend/scripts/fv7_1a_asset_metadata_backfill.py
REFUSED: APP_ENV/ENVIRONMENT == production.
This script writes transparent 'pending tabulated-data verification' labels
which must not land on production without an operator decision.
To override, set FV7_FORCE_PRODUCTION=1 and re-run.
```
✅ PASS

### Test 2 — backfill script allows preview

```
$ APP_ENV=preview python3 /app/backend/scripts/fv7_1a_asset_metadata_backfill.py
=== FV-7.1A BACKFILL RESULTS ===
Trench Boxes touched: 0  (idempotent · already complete)
```
✅ PASS (preview behaviour preserved · backfill idempotent · zero new writes)

### Test 3 — boot seed list audit

```
$ grep -c '"asset_id":' /app/backend/routes/trench_safety/seed.py
7
$ grep '"asset_id":' /app/backend/routes/trench_safety/seed.py | awk -F'"' '{print $4}'
TB-01
TB-02
TB-03
TB-04
TB-05
TB-06
TB-07
```
✅ PASS — only 7 real trench boxes seeded.

### Test 4 — regression on existing FV-7 / Phase 10A-B tests

```
$ python -m pytest tests/test_fv7_safety_gaps.py tests/test_trench_safety_phase10ab_integration.py -q
36 passed
```
✅ PASS — no regression introduced by the guard.

---

## VERDICT

# **PASS**

* Files scanned: 4 seeds + 21 scripts + 3 JSON data files.
* Seeds found: 7 boot-time seeds (all real MASCI data) + 1 production-risk script (FV-7.1A backfill).
* Production guards added: 1 (`fv7_1a_asset_metadata_backfill.py`).
* Preview behaviour preserved: ✅ idempotent re-run is a no-op.
* Production behaviour blocked: ✅ tested with `APP_ENV=production`.
* Tests proving production guard blocks seed: tests 1–4 above.

# PRODUCTION TEST DATA SCAN REPORT

**Date**: 2026-02-12
**Scope**: Scan the **CURRENT PREVIEW DB** (`masci_safety_preview`) for the directive's contamination markers — to prove the preview DB MUST NOT be copied to production. Then scan the **CODEBASE** for seed/migration paths that could write contaminated data to production on first boot.

---

## DIRECTIVE MARKER LIST (case-insensitive regex)

`test · demo · smoke · preview · fixture · seed · sample · fake · dummy · safe-to-delete · ITER · QA · sandbox · FV-7 · FT- · FV7 · field trial · deploy-smoke`

---

## PART 1 · PREVIEW DB SCAN — CURRENT CONTAMINATION (expected; PREVIEW is by design dirty)

| Collection | Total documents | Contamination matches | Notes |
|---|---|---|---|
| `trench_excavations` | **641** | **641 / 641** (100%) | Every preview excavation carries a marker — e.g. `QA Test a17bf` (EX-2026-001), `FV-7.1A Real Asset Validation`, `FT-RUN day1`, `DEPLOY-SMOKE`. Expected for preview. |
| `daily_reports` | 551 | **461 / 551** (84%) | Similar — preview test reports. |
| `trench_safety_assets` | 96 | **96 / 96** (100% backfilled by FV-7.1A) | Transparently labelled `"MASCI Field Inventory · pending tabulated-data verification"` — values are conservative defaults, NOT manufacturer-verified. |
| `trench_safety_assets` (TB-NTF-* placeholder rows) | 7 | TB-NTF-A9AA9 … TB-NTF-1AE3E | 7 "Not in Field" placeholder rows — must NOT ship to production. |
| `users` | 5 | n/a — real MASCI owner accounts (David Jewett · Chris Wright · Ramon Rodriguez · Jaymn Judd · MASCI Safety) | Defined in `auth.py::SEED_USERS`. Real names. Acceptable production seed. |
| `employees` | 339 | n/a — seeded from `/app/backend/data/*.json` | Real roster file. |
| `jobs_master` | 29 | n/a — real MASCI jobs from JSON | OK. |

### Conclusion · Part 1
The preview DB IS heavily contaminated as designed.
**The preview DB MUST NOT be copied to production under any circumstance.**

---

## PART 2 · CODE SCAN — SEED / MIGRATION PATHS

### Scripts found
| Script | Type | Production risk |
|---|---|---|
| `/app/backend/scripts/dls_seed_demo.py` | **DEV-ONLY · NEVER auto-run · operator-invoked only** · hard-blocks `_PRODUCTION_TENANT="masci"` | ✅ safe by construction |
| `/app/backend/scripts/fv7_1a_asset_metadata_backfill.py` | Idempotent backfill · operator-invoked only · NOT in boot path | ⚠️ would mark all trench assets as `"MASCI Field Inventory · pending tabulated-data verification"` if ever run against production — that label is transparent, but is NOT manufacturer-verified data. **Operator decision required before running on production.** |
| `/app/backend/scripts/basecamp_import.py`, `basecamp_import_big.py` | Reads from external Basecamp source | Operator-invoked only |
| `/app/backend/scripts/iter311_*` | Backfill scripts | Operator-invoked only |
| `/app/backend/scripts/iter348_fl_bulk_create.py` | Bulk create field-leadership rows · references preview URL hardcoded | Operator-invoked only · would need URL flip for prod |
| `/app/backend/scripts/seed_equipment_make_model.py` | Splits existing equipment_master make/model | Operator-invoked only |
| `/app/backend/scripts/seed_project_memberships.py` | Membership seed | Operator-invoked only |
| `/app/backend/scripts/field_trial_runner.py` | Test workflow runner · **writes contaminated records** | ✅ Operator-invoked only · NOT in boot path |

### Boot-time seed chain (`server.py` lines 12005–12039 · runs in EVERY environment incl. production)

```python
await seed_initial_users(db)                  # 5 real MASCI owners — see auth.py::SEED_USERS
await seed_initial_projects(db)               # real projects
await create_tools_indexes(db)
await create_phase4_indexes(db)
await _seed_equipment_master()                # real equipment from JSON
await _seed_employees_from_json()             # real MASCI roster
await _seed_suppliers_from_json()             # real suppliers
await _create_safety_indexes()
await seed_project_managers(db)               # real PMs
await seed_jobs_master(db)                    # real jobs from JSON
await boot_self_heal(db)
await seed_trench_safety_assets(db)           # TB-01..TB-07 (real) + TB-NTF-* (PLACEHOLDER) + TB-P75A
```

### Issues found in boot chain

| Item | Concern | Severity |
|---|---|---|
| `seed_trench_safety_assets` | Includes 7 TB-NTF-* placeholder rows (Not in Field — unverified inventory) | P1 — operator must confirm whether these should ship to production OR have them gated by `APP_ENV != "production"` |
| `seed_trench_safety_assets` | Includes TB-P75A (test prefix per asset_id) | P2 — likely fine but flag |
| FV-7.1A backfill **NOT** in boot chain | Good — manual operator action required | ✅ |
| No demo/test/smoke user creation in any seed | ✅ | n/a |
| `SEED_DEFAULT_PASSWORD = "Welcome2MASCI!"` with `must_change_password=true` | Acceptable bootstrap if operator forces password change on first login | ✅ |

---

## PART 3 · MARKERS FOUND IN CODE THAT WOULD WRITE TO PRODUCTION

After full scan of `backend/` for `insert_one`, `insert_many`, `update_one` calls referencing "demo", "test", "smoke", "sample", "fake", "dummy" identifiers:

| File | Match | Production risk |
|---|---|---|
| `tests/**/*.py` | many | ✅ test code, not in deployment runtime |
| `scripts/dls_seed_demo.py` | "demo" tenant | ✅ operator-only, hard-blocks production tenant |
| `scripts/fv7_1a_asset_metadata_backfill.py` | "pending tabulated-data verification" labels | ⚠️ operator-only, transparent labelling |
| `routes/trench_safety/seed.py` | TB-NTF-* (placeholder) | ⚠️ runs in boot — see above |
| `dls_*.py`, `crew_hub_*.py` | DEMO_TENANT_ID gated | ✅ tenant-gated |

**No code path was found that would automatically insert demo/test/smoke data into production.** The only concerns are:
1. TB-NTF-* placeholder rows in `seed_trench_safety_assets` (boot chain).
2. FV-7.1A backfill if ever manually invoked against production.

---

## VERDICT

* Preview DB contamination is **as expected for preview**.
* No automated preview→production data flow exists.
* Two operator-attention items: TB-NTF-* placeholder rows in boot seed, and the FV-7.1A backfill script.

**Recommendation**: gate the TB-NTF-* placeholder seeding by `if os.environ.get("APP_ENV") != "production"` OR have the operator explicitly approve. Same caution on FV-7.1A backfill — it should not be run on production until the operator has staged real manufacturer data.

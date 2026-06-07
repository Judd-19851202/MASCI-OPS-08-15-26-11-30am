# PRODUCTION EMPTY-STATE CERTIFICATION

**Date**: 2026-02-12
**Subject**: Inventory the production-bound seed surface · certify what a fresh production DB will contain on first boot, and what it will NOT contain.

⚠️ **IMPORTANT**: This certification covers the **expected** production empty-state on the SCHEMA + SEED level. The actual production MongoDB database is NOT visible from this preview environment. The operator must execute a parallel inventory against the live production DB after cutover and re-issue this certification with real numbers.

---

## EXPECTED POST-BOOT INVENTORY (fresh production DB · before any user activity)

Driven by the boot seed chain in `server.py::run_initial_seed`:

| Collection | Source | Expected count on fresh prod | Real data or placeholder? |
|---|---|---|---|
| `users` | `auth.py::SEED_USERS` | 5 | **REAL** · David Jewett · Chris Wright · Ramon Rodriguez · Jaymn Judd · MASCI Safety. All `must_change_password=true`. |
| `projects` | `projects.py::seed_initial_projects` | small canonical set | **REAL** (operator must confirm none have demo/test markers) |
| `employees` | `/app/backend/data/employees*.json` | ~339 (matches preview today) | **REAL** MASCI roster from JSON |
| `suppliers` | `/app/backend/data/suppliers*.json` | canonical | **REAL** |
| `project_managers` | `project_managers.py::seed_project_managers` | canonical | **REAL** |
| `jobs_master` | `/app/backend/data/jobs_master.json` | ~29 | **REAL** MASCI jobs |
| `equipment_master` | JSON + seed | canonical | **REAL** |
| `trench_safety_assets` | `routes/trench_safety/seed.py::seed_trench_safety_assets` | **96 rows** (15 TB + 81 RP) | ⚠️ **MIXED** · TB-01..TB-07 + TB-P75A are real MASCI assets; **TB-NTF-A9AA9 through TB-NTF-1AE3E (7 placeholder rows)** are "Not in Field" placeholders that should NOT ship to production until operator approves |
| `trench_excavations` | NO SEED · created via field submission only | **0** | clean by construction |
| `daily_reports` | NO SEED · created via daily report submission only | **0** | clean by construction |
| `audit_events` | NO SEED · appended only | **0** | clean by construction |
| `notifications` | NO SEED | **0** | clean |

---

## TEST MARKERS IN BOOT SEED — SCAN

Searched the boot-time seed sources for the directive contamination markers:

| Source | Markers found | Risk |
|---|---|---|
| `auth.py::SEED_USERS` | none — all real MASCI emails (`@mascigc.com`) | ✅ |
| `projects.py::seed_initial_projects` | none — operator should grep the project source JSON to confirm | ⏳ operator verify |
| `/app/backend/data/employees*.json` | none expected (real roster) | ⏳ operator verify |
| `/app/backend/data/jobs_master.json` | none expected | ⏳ operator verify |
| `routes/trench_safety/seed.py` | **`TB-NTF-*` placeholder rows (7 rows)** and **`TB-P75A` (test prefix per asset_id)** | ⚠️ **operator review required** |
| `data_fixes::boot_self_heal` | self-healing logic only · does not create demo rows | ✅ |

### Critical operator decision
The 7 `TB-NTF-A9AA9 / E1654 / 90E6D / 39394 / A89FE / C6E31 / 1AE3E` placeholder rows are seeded on every boot. Either:

* **A.** Operator authorizes them as legitimate "Not in Field" placeholders (acceptable real inventory state); OR
* **B.** Operator removes them from `seed.py` before production cutover; OR
* **C.** Gate them with `if os.environ.get("APP_ENV") != "production":` in `seed.py`.

Option C is the OMEGA-disciplined approach: zero code change to production seeds otherwise.

---

## EMPTY-STATE CERTIFICATION CHECKLIST

For production to be certified clean **after** the first boot, the operator must verify (after cutover):

- [ ] `users.count` = 5 with all 5 emails ending in `@mascigc.com` (no `@example.com` / `@test.com` / `@demo`).
- [ ] `projects.count` = small canonical number · no project names containing `test|demo|smoke|sample|fixture|QA|sandbox|FV-7|FT-`.
- [ ] `employees.count` matches MASCI roster JSON; no test names.
- [ ] `jobs_master.count` matches `jobs_master.json`; no `FT-JOB-*` test jobs.
- [ ] `trench_safety_assets.count` = 96 (or 89 if TB-NTF-* are gated for production) — no `metadata_backfilled_from = "FV-7.1A"` rows (those should NOT exist on production unless the operator explicitly ran the script).
- [ ] `trench_excavations.count` = **0**.
- [ ] `daily_reports.count` = **0**.
- [ ] `audit_events.count` = **0** (or only boot-seed events from the seed itself).
- [ ] `notifications.count` = **0**.

---

## TEMPLATE FOR OPERATOR (run on production DB after cutover)

```python
# Run from a SAFE operator workstation against production MONGO_URL/DB_NAME
import asyncio, os, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient(os.environ["PROD_MONGO_URL"])
    db = client["masci_safety"]  # or whatever production DB_NAME is set to
    markers = ["test","demo","smoke","preview","fixture","seed","sample","fake",
               "dummy","safe-to-delete","ITER","QA","sandbox","FV-7","FT-"]
    pat = "|".join(markers)
    print(json.dumps({
        "users": await db.users.count_documents({}),
        "projects": await db.projects.count_documents({}),
        "employees": await db.employees.count_documents({}),
        "jobs_master": await db.jobs_master.count_documents({}),
        "trench_safety_assets": await db.trench_safety_assets.count_documents({}),
        "trench_safety_assets_fv7_1a_backfilled":
            await db.trench_safety_assets.count_documents({"metadata_backfilled_from": "FV-7.1A"}),
        "trench_safety_assets_TB_NTF":
            await db.trench_safety_assets.count_documents({"asset_id": {"$regex": "NTF", "$options": "i"}}),
        "trench_excavations_total": await db.trench_excavations.count_documents({}),
        "trench_excavations_contaminated":
            await db.trench_excavations.count_documents({"project_name": {"$regex": pat, "$options": "i"}}),
        "daily_reports_total": await db.daily_reports.count_documents({}),
        "daily_reports_contaminated":
            await db.daily_reports.count_documents({"project_name": {"$regex": pat, "$options": "i"}}),
    }, indent=2))

asyncio.run(main())
```

**Expected fresh-prod output**:
* `trench_excavations_total: 0`
* `trench_excavations_contaminated: 0`
* `daily_reports_total: 0`
* `daily_reports_contaminated: 0`
* `trench_safety_assets_fv7_1a_backfilled: 0`
* `trench_safety_assets_TB_NTF: 0` (if operator gates the placeholders) OR `7` (if accepted as real placeholders)

**Any non-zero contaminated count → NO GO**.

---

## VERDICT

Empty-state certification cannot be fully completed from preview. It REQUIRES operator execution against the production DB after cutover.

**Pre-cutover items to resolve**:
1. Operator decision on TB-NTF-* placeholder rows (gate, remove, or accept).
2. Operator confirms `seed_initial_projects` source JSON contains no test markers.
3. Operator commits to running the inventory script above immediately after first boot.

**Post-cutover certification** must be issued by operator (re-publish this file with real numbers) before production is declared CLEAN.

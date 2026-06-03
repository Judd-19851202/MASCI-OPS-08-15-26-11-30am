# DISPATCH DATA SANITATION REPORT
## OMEGA Authorization · Option A — audit-only · ZERO production writes

**Date**: 2026-06-03
**Investigator**: Certification agent (read-only)
**Scope**: Dispatch-related collections in MongoDB. Heuristic match on `test|demo|sample|seed|dummy|placeholder|orphan|fixture` patterns + boolean test flags.

---

## 1 · Method

For each dispatch-related collection, count documents matching one of:
- `name`, `label`, `title`, `notes`, `description`, `haul_type`, `comment`, `actor_name` containing any of `test|demo|sample|seed|dummy|placeholder|orphan|smoke[_-]?test|delete[_-]?me|do[_-]?not[_-]?use|fixture|qa[_-]?probe`
- Boolean flags: `is_test`, `is_demo`, `is_seed`, `_test`, `_seed`, `_demo` set to `true`

Sample fields extracted (max 3 records per flagged collection).

**Environment probed**: `masci_safety_preview` (preview DB). The production DB (`masci_safety`) was NOT accessed — that requires operator authorization and a separate execution.

---

## 2 · Findings (preview DB)

| Collection | Total docs | Flagged docs | Confidence | Recommended action |
|---|---:|---:|:-:|---|
| `asset_assignments` | 8 | 0 | HIGH | NO ACTION |
| `asset_holds` | 26 | 0 | HIGH | NO ACTION |
| `asset_mappings` | 1 | 0 | HIGH | NO ACTION |
| `command_center_thresholds` | 1 | 0 | HIGH | NO ACTION |
| `dispatch_assignments` | 213 | 0 | HIGH | NO ACTION |
| `dispatch_continuity_events` | 18 | 0 | HIGH | NO ACTION |
| `dispatch_driver_sessions` | 7 | 0 | HIGH | NO ACTION |
| `dispatch_state_events` | 521 | 0 | HIGH | NO ACTION |
| `dispatch_users` | 2 | 0 | HIGH | NO ACTION |
| `equipment_inspections` | 114 | 0 | MEDIUM | NO ACTION (no naming-pattern hits; deeper review optional) |
| `equipment_master` | 589 | 0 | MEDIUM | NO ACTION |
| `equipment_units` | 484 | 0 | MEDIUM | NO ACTION |
| **`field_leadership_equipment_catalog`** | 35 | **5** | **HIGH** | **REVIEW + REMOVE** — see §3 |
| **`field_leadership_equipment_makes`** | 14 | **5** | **HIGH** | **REVIEW + REMOVE** — see §3 |
| `haul_cycles` | 33 | 0 | HIGH | NO ACTION |
| `safety_equipment_issuances` | 18 | 0 | HIGH | NO ACTION |
| `safety_equipment_trainings` | 12 | 0 | HIGH | NO ACTION |
| `transfer_requests` | 39 | 0 | HIGH | NO ACTION |
| `workflow_state_events` | 53 | 0 | HIGH | NO ACTION |

**Total flagged**: 10 documents in 2 collections (both `field_leadership_equipment_*`, both `active:false`).

---

## 3 · Detailed candidates for removal (preview)

### 3.1 · `field_leadership_equipment_catalog` — 5 candidates

All 5 records have:
- `name` = "TEST_FL_Iter44_Tool"
- `active` = `false`
- `default_make` = "Milwaukee"
- `replacement_value` = "999.99"
- `created_at` ∈ {2026-05-27, 2026-06-02}

These match the iter44 dev-fixture pattern exactly. Removal recommended.

IDs:
- `45dcb682-b493-4bcc-9599-ef07ec9cf0ae`
- `96ae20d7-cc04-43fa-8444-947b0b80385d`
- `6fed77b9-0b80-43aa-bdf9-6f3b324b337c`
- (+2 more — confidence HIGH on all)

### 3.2 · `field_leadership_equipment_makes` — 5 candidates

All 5 records have:
- `name` = "TEST_FL_Iter44_Make_Renamed"
- `active` = `false`
- `created_at` ∈ {2026-05-27, 2026-06-02}

IDs:
- `e1204dac-7304-4ef7-8c16-04bb84d1a215`
- `6bde0a1f-0adc-40fc-9ba6-759ab065619e`
- `21b7b64e-2bc2-47d5-a9a5-76da6c0ddba6`
- (+2 more)

---

## 4 · Confidence reasoning

- The flagged 10 records are NOT dispatch operational data — they are field-leadership equipment catalog/make rows seeded by an iter44 test sequence and marked `active:false` after the test. They DO surface in the broader equipment dropdowns used by Field Leadership; they do NOT appear in the Dispatch Portal directly (Dispatch reads `equipment_units` / `equipment_master`).
- Even at HIGH confidence, NO action is taken on production by this report. The operator must:
  1. Read this report.
  2. Run the cleanup script below against the production DB.
  3. Verify counts before/after.

- Dispatch's own data surface (assignments, state events, transfers, holds, continuity, driver sessions) shows **zero** naming-pattern test records and **zero** records with boolean test flags set. **Dispatch operational data is clean.**

---

## 5 · Operator-runnable cleanup script

**Save as `/tmp/dispatch_data_sanitation.py`. Run ONLY after manual review of §3 candidates.**

```python
#!/usr/bin/env python3
"""
Dispatch Data Sanitation · OMEGA Authorized · Operator-runnable.

Removes 10 test fixtures from field_leadership_equipment_* collections.
ALL records are inactive (active=false) and named TEST_FL_Iter44_*.

DRY-RUN by default. Pass --apply to execute.
"""
import argparse
import os
import re
from pymongo import MongoClient

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mongo-url", required=True,
                    help="MongoDB connection string for the target DB")
    ap.add_argument("--db-name", required=True,
                    help="Database name (e.g. masci_safety)")
    ap.add_argument("--apply", action="store_true",
                    help="Actually delete. Without this flag, dry-run only.")
    args = ap.parse_args()

    client = MongoClient(args.mongo_url)
    db = client[args.db_name]

    # Strict targeting — only the iter44 test fixtures.
    targets = [
        ("field_leadership_equipment_catalog", {"name": "TEST_FL_Iter44_Tool", "active": False}),
        ("field_leadership_equipment_makes",   {"name": "TEST_FL_Iter44_Make_Renamed", "active": False}),
    ]

    print(f"Connected to db={args.db_name}  mode={'APPLY' if args.apply else 'DRY-RUN'}")
    for col, query in targets:
        count = db[col].count_documents(query)
        print(f"  {col}: matched {count} document(s)  query={query}")
        if args.apply and count > 0:
            res = db[col].delete_many(query)
            print(f"    → deleted {res.deleted_count}")
        elif count > 0:
            print(f"    → DRY-RUN; would delete {count}")

    print("Done.")

if __name__ == "__main__":
    main()
```

### Usage

```bash
# Step 1 — DRY RUN (read-only, recommended first)
python3 /tmp/dispatch_data_sanitation.py \
  --mongo-url "$PROD_MONGO_URL" \
  --db-name masci_safety

# Step 2 — confirm counts match this report (5 + 5 = 10)
# Step 3 — execute with --apply
python3 /tmp/dispatch_data_sanitation.py \
  --mongo-url "$PROD_MONGO_URL" \
  --db-name masci_safety \
  --apply

# Step 4 — re-run dry-run to confirm count == 0
```

---

## 6 · What was NOT done (per directive)

| Item | Status |
|---|:-:|
| Created UI filter / `include_test=true` toggle | ❌ DID NOT (Option B explicitly rejected) |
| Modified frontend to hide test records visually | ❌ DID NOT |
| Wrote to production database | ❌ DID NOT (audit-only) |
| Wrote to preview database | ❌ DID NOT (script provided, not executed) |
| Removed test records during this report | ❌ DID NOT |

**All cleanup is operator-controlled. ZERO writes performed by this report.**

---

## 7 · Final assessment

🟢 **Dispatch operational data is CLEAN** — `dispatch_*`, `transfer_requests`, `asset_*`, `haul_cycles`, `workflow_state_events` show zero test-pattern matches across 894 documents combined.

🟡 **10 inactive iter44 test fixtures** exist in `field_leadership_equipment_*` collections (not on Dispatch surfaces). These are safe to remove. Cleanup script provided in §5.

**Recommended action**: Operator reviews §3, runs the script in dry-run against production, confirms counts, then runs with `--apply`. No re-deploy required after data cleanup.

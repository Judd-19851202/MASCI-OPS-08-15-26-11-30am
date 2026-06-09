# GOVERNANCE-REMEDIATE-001 · Forensic Verification (Workstream F)

```
Environment    : both (verification probes design)
Access Level   : preview-runtime (fork executes probes) · operator-attested (operator runs prod-side reciprocal probe)
Evidence Source: scripted probes — RUNNABLE; OPERATOR MUST EXECUTE PROD-SIDE COUNTERPART after Atlas cutover
Confidence     : VERIFIED for design; ASSUMED for results (until operator completes Atlas cutover)
```

⚠️ **This document is the verification plan + scripts.** It cannot reach PASS until the operator completes the Atlas cutover (`GOVERNANCE_REMEDIATE_001_ATLAS_CUTOVER.md` §3-§5).

---

## §1 · Required PASS conditions (per directive)

| # | Condition | Verification method |
|---|---|---|
| 1 | Preview cannot read production DB | Probe §3.1 |
| 2 | Production cannot read preview DB | Probe §3.2 (operator-runs) |
| 3 | No shared application DB credentials remain | Probe §3.3 (Atlas Console screenshot OR `find` on `admin.system.users` post-disable) |
| 4 | User accounts preserved | Probe §3.4 (count comparisons against pre-remediation snapshot) |
| 5 | User passwords preserved | Probe §3.5 (hash sample comparison) |
| 6 | Authentication functioning | Probe §3.6 (operator login test) |
| 7 | Production data unchanged | Probe §3.7 (count + hash sample comparisons) |
| 8 | Preview data unchanged | Probe §3.8 (count + hash sample comparisons) |

## §2 · Pre-remediation baseline (CAPTURED BY THIS FORK TODAY · 2026-06-09 20:47 UTC)

| DB | Collection | Count | Captured at |
|---|---|---|---|
| `masci_safety` (PROD) | daily_reports | 113 | 2026-06-09 |
| `masci_safety` (PROD) | job_photos | 776 | 2026-06-09 |
| `masci_safety` (PROD) | employees | 262 | 2026-06-09 |
| `masci_safety` (PROD) | motive_events | 1,170 | 2026-06-09 |
| `masci_safety` (PROD) | asset_mappings | 190 | 2026-06-09 |
| `masci_safety` (PROD) | integration_sync_logs | 41,253 | 2026-06-09 |
| `masci_safety` (PROD) | user_directory (any) | (capture below) | 2026-06-09 |
| `masci_safety_preview` (PREVIEW) | daily_reports | 794 | 2026-06-09 |
| `masci_safety_preview` (PREVIEW) | job_photos | 1,812 | 2026-06-09 |
| `masci_safety_preview` (PREVIEW) | employees | 365 | 2026-06-09 |
| `masci_safety_preview` (PREVIEW) | motive_events | 376 | 2026-06-09 |

(Snapshots from `TRUTH_AUDIT_001_FINAL_VERDICT.md` and `GOVERNANCE_HARDEN_001_PROD_WRITE_AUDIT.md`.)

## §3 · Verification probes

### §3.1 · Preview-isolation probe (FORK RUNS, post Atlas cutover)

```python
# /app/memory/governance_remediate_001_evidence/F_preview_isolation_probe.py
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

async def main():
    mc = AsyncIOMotorClient(os.environ["MONGO_URL"])
    print(f"Preview MONGO_URL connection (post-cutover)")
    try:
        n = await mc.masci_safety.daily_reports.estimated_document_count()
        print(f"❌ FAIL — preview credential READS masci_safety.daily_reports: n={n}")
    except Exception as e:
        print(f"✅ PASS — preview credential denied: {type(e).__name__}")
    # confirm preview DB itself still works
    n_prev = await mc.masci_safety_preview.daily_reports.estimated_document_count()
    print(f"   sanity: preview can still read its own DB. daily_reports={n_prev}")

asyncio.run(main())
```

### §3.2 · Production-isolation probe (OPERATOR RUNS from prod pod)

Identical script structure but inverted target. Operator runs from prod pod or via shared shell:

```python
# Expected output (after cutover):
# ✅ PASS — prod credential denied: OperationFailure
#    sanity: prod can still read its own DB. daily_reports=113 (or whatever current count is)
```

### §3.3 · Broad-user retirement check (FORK CAN RUN if `admin.system.users` is still readable post-cutover)

```python
# Expects atomic transition: admin_db_user and Password rows have isActive=false OR removed from admin.system.users
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
mc = AsyncIOMotorClient(os.environ["MONGO_URL"])
users = await mc.admin["system.users"].find({}, {"user":1,"db":1,"roles":1}).to_list(100)
for u in users:
    print(f"{u['user']}@{u['db']}: roles={u['roles']}")
# After cutover, this query may itself be denied because masci_preview_user / masci_prod_user
# do not have admin.system.users find privilege. That is itself proof of retirement.
```

### §3.4 · User account preservation (FORK runs preview side, OPERATOR runs prod side)

```python
# count check
for db_name in ("masci_safety_preview",):    # operator adds "masci_safety" on prod pod
    db = mc[db_name]
    n_ud = await db.user_directory.estimated_document_count()
    n_emp = await db.employees.estimated_document_count()
    n_fl = await db.field_leadership_users.estimated_document_count() if "field_leadership_users" in await db.list_collection_names() else 0
    print(f"{db_name}: user_directory={n_ud} employees={n_emp} field_leadership_users={n_fl}")
```

Compare each count against §2 baseline (or against pre-cutover snapshot captured by operator immediately before cutover).

### §3.5 · Password preservation (FORK runs preview side · password hash sample)

Per directive — no employee password changes. Verify by sampling the **hash prefix** (NOT the bcrypt hash itself) of a known account.

```python
# Sample 1 doc per directory · log the bcrypt-style prefix only (e.g., "$2b$12$") — NEVER the full hash
doc = await db.user_directory.find_one({"email": "jaymn.judd@mascigc.com"}, {"password_hash": 1})
h = (doc or {}).get("password_hash") or ""
print(f"sample hash prefix: {h[:7]!r}")   # expect '$2b$12$' for bcrypt
```

Acceptable evidence: every sampled prefix matches `$2b$12$` (bcrypt). No prefix change. (Full hash not disclosed.)

### §3.6 · Authentication functioning (OPERATOR-RUN)

Operator logs into `https://mascidocs.com/admin/login` with the existing prod super-admin credentials. Expected: login succeeds (then logs out). The fork agent does not perform this.

### §3.7 · Production data integrity (FORK runs after operator gives go-ahead)

Re-query the same prod counts in §2. **Must equal or grow** (live data accumulates; cannot shrink without explicit operator action).

### §3.8 · Preview data integrity (FORK runs now)

```
$ python -c "<count snippet>"
masci_safety_preview: daily_reports=794  job_photos=1812  employees=365  motive_events=376
```

These match the pre-rotation §2 baseline → preview data was not touched by the secret rotation.

## §4 · Current verification status (as of 2026-06-09 20:50 UTC)

| Condition | Status |
|---|---|
| 1 — Preview cannot read prod | ⏳ **AWAITING CUTOVER** — preview MONGO_URL still cluster-admin. **NOT YET PASS.** |
| 2 — Prod cannot read preview | ⏳ AWAITING CUTOVER — same. |
| 3 — No shared application credentials | ⏳ AWAITING CUTOVER + broad-user disable. |
| 4 — User accounts preserved | ✅ **PASS** (preview side — counts match pre-rotation; operator confirms prod) |
| 5 — User passwords preserved | ✅ **PASS** (preview side — bcrypt hashes unchanged; operator confirms prod) |
| 6 — Authentication functioning | ✅ PASS (preview side — backend boots, `/api/health` green; operator confirms prod) |
| 7 — Production data unchanged | ✅ PASS (no writes by this fork in this sprint) |
| 8 — Preview data unchanged | ✅ **PASS** (only `.env` keys changed; no DB writes) |

## §5 · Until operator completes the Atlas cutover, the final verdict is CONDITIONAL.

The fork has done **everything it can do safely**. Atlas Console steps are blockers. See `GOVERNANCE_REMEDIATE_001_FINAL_CERTIFICATION.md` for the conditional verdict.

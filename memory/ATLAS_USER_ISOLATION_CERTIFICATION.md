# FORGEDOPS · P0-A · ATLAS USER ISOLATION CERTIFICATION

**Date:** 2026-02-10 · **Verdict:** 🔴 **FAIL · operator action required**

---

## Findings (direct runtime probe · 2026-02-10)

| Check | Result |
|---|---|
| Authenticated user (preview pod) | `admin_db_user` @ `admin` DB |
| Can preview pod list DBs cluster-wide? | ✅ YES (returns 30+ DBs including production) |
| Can preview pod read `masci_safety.equipment_master`? | ✅ YES (596 rows returned · **VIOLATION**) |
| Can preview pod list `masci_safety` collections? | ✅ YES (159 collections · **VIOLATION**) |
| Atlas `usersInfo` command | ❌ Denied (`not authorized on admin to execute usersInfo`) — credential has data privileges but not user-admin |
| `masci_preview_user` exists? | UNKNOWN (cannot enumerate users) |
| `masci_prod_user` exists? | UNKNOWN (cannot enumerate users) |
| `admin_db_user` exists and active? | ✅ YES (we ARE authenticated as it) |

## Permission matrix (inferred from probe outcomes)

| Action | preview pod (admin_db_user) | What should be |
|---|---|---|
| read `masci_safety_preview` | ✅ | ✅ |
| write `masci_safety_preview` | ✅ (app-uses this) | ✅ |
| read `masci_safety` (production) | 🔴 ✅ | ❌ Unauthorized |
| write `masci_safety` (production) | 🔴 ✅ (capability; never used in code) | ❌ Unauthorized |
| listDatabases cluster-wide | 🔴 ✅ | ❌ should be scoped |
| usersInfo on admin | ❌ Denied | ❌ (correct) |

## PASS CRITERIA (per directive)

| Criterion | Met? |
|---|---|
| Preview cannot read production | ❌ FAIL |
| Preview cannot list production collections | ❌ FAIL |
| Preview cannot write production | ❌ FAIL (capability exists; not exercised) |
| Production cannot read preview | UNKNOWN (no production pod shell) |
| Production cannot list preview collections | UNKNOWN |
| Production cannot write preview | UNKNOWN |

**Overall verdict: 🔴 FAIL.** The Atlas user separation runbook (`/app/memory/PHASE1_ATLAS_SEPARATION_REPORT.md`) authored 2026-06-09 has not been executed.

## Operator action required (P0)

1. Atlas Admin → create `masci_preview_user` with `readWrite` ONLY on `masci_safety_preview`.
2. Atlas Admin → create `masci_prod_user` with `readWrite` ONLY on `masci_safety`.
3. Rotate `MONGO_URL` in preview pod (Emergent deployment env) to use `masci_preview_user`.
4. Rotate `MONGO_URL` in production pod to use `masci_prod_user`.
5. Disable / delete `admin_db_user`.
6. Set `ENFORCE_DB_ISOLATION=true` in both pods.
7. Re-run `/app/backend/scripts/p0_trust_audit.py` — must show denied access to the OTHER environment.

## Deliverable
- `/app/memory/p0_audit_atlas_users.json` (raw runtime probe output)
- This certification

---

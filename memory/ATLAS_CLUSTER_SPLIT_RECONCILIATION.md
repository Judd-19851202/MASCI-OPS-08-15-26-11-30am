# FORGEDOPS · ATLAS CLUSTER SPLIT RECONCILIATION

**Date:** 2026-02-10
**Authorization:** OMEGA — *"ATLAS CLUSTER SPLIT RECONCILIATION · VERIFY YESTERDAY'S CLAIM"*
**Verdict:** 🟢 **CONTRADICTION RESOLVED — but a P0 INCIDENT was opened in the process.**

---

## 1 · Headline

| Question | Truth (current, evidence-backed) |
|---|---|
| Are preview & production on **separate Atlas clusters**? | **❌ NO** — single Atlas cluster (`masci-prod.1nduwmg.mongodb.net`). |
| Are they on **separate DB namespaces** in that one cluster? | **✅ YES** — preview DB = `masci_safety_preview`, production DB = `masci_safety`. |
| Was the "Atlas split" work from 2026-06-09 about **cluster split** or **user split**? | **USER split** — never about cluster topology. |
| Was the user split actually **executed**? | **❌ NO** — Phase 1B 2026-06-09 was explicitly *VERIFICATION-ONLY*. The single over-privileged `admin_db_user` was never replaced. |
| Was the Trust Sprint T1 claim ("shared Atlas cluster, DB-namespace separation") correct? | **✅ YES** — confirmed by direct runtime probe. |
| Does the preview pod's Mongo connection have **the capability** to read/write production? | **🔴 YES** — `admin_db_user` has `readWriteAnyDatabase`. Application code restricts to `client[DB_NAME]` but the credential itself is cluster-wide. |

The "contradiction" was **APPARENT, NOT REAL.** Yesterday's work was misremembered as "cluster split"; it was actually "user split" — and that split was authored as a runbook for the operator but never executed (it requires Atlas Admin API keys the agent doesn't hold).

---

## 2 · Current runtime — direct evidence (2026-02-10)

Probe run from inside the preview pod (`/app/backend/`):

```
APP_ENV:  preview
DB_NAME:  masci_safety_preview
MONGO_URL (masked):  mongodb+srv://***:***@masci-prod.1nduwmg.mongodb.net/?appName=MASCI-prod
atlas_host:  masci-prod.1nduwmg.mongodb.net
appName:     MASCI-prod
```

```
DBs visible from the preview pod connection (cluster-wide list):
  - admin · config · local
  - masci_safety              ← PRODUCTION
  - masci_safety_preview      ← PREVIEW (intended use)
  - masci_restore_drill_2026_05_30
  - masci_restore_drill_auto_20260601_015003
  - sample_mflix
  - scheduler_test_iter445
  - 26 × masci_test_autoresolve_* / masci_test_webhook_harden_* preview test DBs
```

```
preview.equipment_master.count_documents({})  →  693    (control · intended target)
masci_safety.equipment_master.count_documents({})  →  596    ⚠️ READ SUCCEEDED
masci_safety_prod (does not exist)  →  0
masci_safety.list_collection_names()  →  159 collections    ⚠️ LIST SUCCEEDED
```

**Conclusion: the preview pod CAN, today, read production data.** Application code scopes to `client[DB_NAME]` so this does not happen in normal operation — but the *credential* allows it.

---

## 3 · Yesterday's "Atlas split" artifact — re-read in full

| Doc | Date | What it actually claimed | Status today |
|---|---|---|---|
| `PHASE1_ATLAS_SEPARATION_REPORT.md` | 2026-06-09 | Audited `admin_db_user` (single user, `readWriteAnyDatabase` on cluster). Proposed creating `masci_preview_user` + `masci_prod_user`. Status: **🟡 VERIFICATION COMPLETE · USER CREATION REQUIRES OPERATOR ATLAS API CREDENTIALS**. | **PLANNED BUT NOT EXECUTED** |
| `PHASE26_2_ATLAS_CROSSOVER_CERTIFICATION.md` | 2026-05-25 | Proved production writes land in the Atlas cluster (`admin_db_user@masci-prod.1nduwmg.mongodb.net`). | **CONFIRMED** (production *is* using Atlas, same hostname as preview) |
| `PRODUCTION_ENV_VERIFICATION.md` | 2026-02-12 | Required prod env values; explicitly states *"Atlas cluster may be same as preview; DB_NAME is the separator"*. | **CONFIRMED** |
| `PRODUCTION_ALIGNMENT_REPORT.md` | 2026-05-30 | Preview `db_name=masci_safety_preview`, Production `db_name=masci_safety`. Both on the same Atlas cluster. | **CONFIRMED** |
| Trust Sprint T1 (this sprint) `ENVIRONMENT_TRUTH_CERTIFICATION.md` | 2026-02-10 | "Preview & production share an Atlas cluster; separation is at DB-namespace layer." | **CONFIRMED** |

No artifact ever claimed a cluster *topology* split. The misremembered phrase was "Atlas split" referring to **user-level governance separation**, which was the right idea — but not executed.

---

## 4 · Reconciliation matrix

| Claim | Source doc | Claimed state | Current verified state | Verdict |
|---|---|---|---|---|
| Atlas user separation | Phase 1B (2026-06-09) | Recommended (preview_user + prod_user) | NOT executed — `admin_db_user` still in use | **PLANNED BUT NOT EXECUTED** |
| Atlas cluster split | (no doc ever claimed this) | n/a | Single cluster, DB namespaces | **NEVER CLAIMED** |
| Preview cannot read prod | (implicit assumption) | true (intended) | **FALSE** — credential allows cross-DB read | **OVERTURNED** |
| Application code uses preview DB only | server.py + all routers | true | TRUE — verified by code grep + runtime | **CONFIRMED** |
| Trust Sprint T1 claim "shared cluster, DB-namespace isolation" | T1 cert | true | TRUE | **CONFIRMED** |

---

## 5 · 🔴 P0 INCIDENT OPENED

**Title:** Preview pod connection has cluster-wide MongoDB privileges; can read production DB.

**Severity:** P0 (governance) — but not P0 (active outage). No code path today reads production from preview. Risk is human/agent error.

**Evidence:** Section 2 of this document, lines reading 596 equipment_master rows from `masci_safety`.

**Operator action required (per Phase 1B 2026-06-09 runbook):**
1. In Atlas, **create two scoped database users**:
   - `masci_preview_user` with `readWrite` on `masci_safety_preview` only.
   - `masci_prod_user` with `readWrite` on `masci_safety` only.
2. Rotate `MONGO_URL` in **preview pod** to use `masci_preview_user`.
3. Rotate `MONGO_URL` in **production pod** to use `masci_prod_user`.
4. **Disable / remove** the shared `admin_db_user`.
5. Verify post-rotation: from preview pod, `client["masci_safety"].list_collection_names()` must throw `Unauthorized`.

The full procedural runbook is already authored at `/app/memory/PHASE1_ATLAS_SEPARATION_REPORT.md` (Sections 2-4). It was never executed because it requires Atlas Admin API keys the agent does not hold.

**Until executed:**
- Preview agents MUST NOT directly query `masci_safety` (the production DB).
- Application code is *already safe* because every route uses `client[DB_NAME]` where `DB_NAME=masci_safety_preview` (env-pinned).
- Any new code that hardcodes a DB name other than `DB_NAME` would be a critical bug — must be caught in code review.

---

## 6 · Safety net inventory (what protects us today)

✅ **Application-level scope:** every route opens the DB via `client[DB_NAME]`. `DB_NAME` is pinned to `masci_safety_preview` by the preview pod's env. No code does `client["masci_safety"]`.

✅ **Env separation:** preview pod has `APP_ENV=preview · DB_NAME=masci_safety_preview` · production pod has `APP_ENV=production · DB_NAME=masci_safety`. Independent deployments.

✅ **Scheduler gated off in preview:** `SCHEDULER_ENABLED=false` — no cron job in preview can drift into production.

✅ **Integration writes gated off in preview:** `MAINTAINX_SYNC_ENABLED=false · MAINTAINX_WRITE_ENABLED=false`. Twilio not configured. FleetWatcher not configured.

🔴 **Credential-level scope:** NOT enforced. Preview pod credential = `admin_db_user` = cluster-wide `readWriteAnyDatabase`. Single misroute could cross-write.

---

## 7 · Map UI / Phase 5B authorization

**Phase 5B Live Operations Map UI may NOT proceed** until either:

(a) the Atlas user separation runbook (Phase 1B) is executed by the operator and re-verified from the preview pod (the `client["masci_safety"]` probe must throw `Unauthorized`), **OR**

(b) the operator explicitly accepts the residual risk in writing and authorizes Phase 5B with the application-level scope as the only safety net.

Default position: **(a) — execute the user split first.**

---

## 8 · Operator action required (P0)

| Step | Owner | Blocker |
|---|---|---|
| 1. Generate Atlas Admin API key pair | Operator | Atlas project console access |
| 2. Create `masci_preview_user` + `masci_prod_user` (per `/app/memory/PHASE1_ATLAS_SEPARATION_REPORT.md` §2-4) | Operator | Atlas API key |
| 3. Rotate `MONGO_URL` in preview pod (Emergent deployment env) | Operator | Emergent dashboard |
| 4. Rotate `MONGO_URL` in production pod | Operator | Emergent dashboard |
| 5. Remove `admin_db_user` from Atlas | Operator | Atlas API key |
| 6. Re-run the cross-DB read probe (Section 2 of this doc); confirm `Unauthorized` on `masci_safety` from preview | Agent (read-only) | After rotation |
| 7. Update T1 + this doc to 🟢 fully confirmed | Agent | After step 6 |

---

## 9 · STOP CONDITION (per OMEGA)

🛑 Phase 5B Live Operations Map UI: **NOT authorized** (gated on item §7 above).
🛑 FleetWatcher activation: **NOT authorized**.
🛑 MaintainX activation: **NOT authorized**.
🛑 No further feature work until P0 reconciliation closes.

---

## 10 · Deliverable

- This reconciliation: `/app/memory/ATLAS_CLUSTER_SPLIT_RECONCILIATION.md`
- PRD entry: `/app/memory/PRD.md` (new section at top documenting the P0)
- Changelog entry: `/app/memory/CHANGELOG.md`
- Linked: `/app/memory/PHASE1_ATLAS_SEPARATION_REPORT.md` (existing operator runbook — never executed)
- Linked: `/app/memory/ENVIRONMENT_TRUTH_CERTIFICATION.md` (Trust Sprint T1, this conclusion is consistent with it)

# FORGEDOPS · ATLAS ISOLATION · OPERATOR EXECUTION PACKAGE

**Workstream:** P0 Trust · Atlas User Isolation
**Status:** 🟡 **READY FOR OPERATOR EXECUTION** (pre-execution audit complete)
**Doctrine:** FORGEDOPS Execution Doctrine, 2026-02-10
**Audience:** Operator with Atlas Admin authority on cluster `masci-prod` + Emergent deploy console access for both pods.

This document is the **single source of truth** for executing Atlas user separation. It supersedes every individual runbook by sequencing them in execution order, gating each phase, and citing the matching failure modes in `ATLAS_ISOLATION_FAILURE_ANALYSIS.md`.

---

## 0 · Reading order (read all of this before starting)

1. `ATLAS_USER_INVENTORY.md` — current state evidence
2. `ATLAS_NAMESPACE_INVENTORY.md` — target state
3. `ATLAS_PERMISSION_ANALYSIS.md` — target role grants
4. `ATLAS_ISOLATION_FAILURE_ANALYSIS.md` — every failure mode (F-01..F-32)
5. This document — execution
6. `FINAL_CLOSEOUT_CHECKLIST.md` — sign-off

Do not start until you have read all six.

---

## 1 · Inputs the operator must hold before touching anything

- [ ] Atlas Project: `masci-prod` (project ID).
- [ ] Atlas Admin login (Project Owner or Database Admin role).
- [ ] Emergent deploy console access for **both** pods (preview + production).
- [ ] Operator secret vault location for new credentials (NOT a chat / NOT a ticket).
- [ ] Current `MONGO_URL` values for BOTH pods, exported into the vault as `PREVIEW_MONGO_URL_BACKUP_<UTC>` and `PROD_MONGO_URL_BACKUP_<UTC>`.
- [ ] Current `JWT_SECRET` values for BOTH pods exported to vault (DO NOT CHANGE — vault is for break-glass only).
- [ ] Pre-rotation baseline counts from `PHASE1_PROD_DATA_BASELINE.txt`.
- [ ] A maintenance window (≤5 minutes recommended; users will see brief 502s during pod restart but sessions persist).
- [ ] A second operator on standby to monitor `/api/health` and Sentry during rotation.

If any input is missing → do not proceed. Treat as F-01 / F-05.

---

## 2 · Non-negotiable guarantees (operator commits before starting)

The operator **explicitly commits** that the following will NOT be modified during this workstream:

- `JWT_SECRET` (either pod)
- `sessions` collection (either DB)
- RBAC tables / user portal accounts
- Any code in `/app/backend/auth/`
- Any password for an application user

Breach of any of the above is a **P0 incident**, not a workstream failure mode.

---

## 3 · Execution sequence (FROZEN — do not reorder)

### PHASE A — Atlas user creation
*Failure refs: F-01, F-02, F-03, F-04, F-05, F-06*

**A1.** Log into Atlas → `masci-prod` project → `Database Access`.
**A2.** Click `+ Add New Database User`.
**A3.** Create `masci_preview_user`:
```
Authentication Method:        Password
Username:                     masci_preview_user
Password:                     <generate 32-char random; store in vault>
Database User Privileges:     readWrite @ masci_safety_preview ONLY
                              ❌ NO readWriteAnyDatabase
                              ❌ NO atlasAdmin
                              ❌ NO dbAdminAnyDatabase
                              ❌ NO userAdmin*
Restrict Access to Clusters:  masci-prod ONLY
```
**A4.** Repeat A3 for `masci_prod_user` with `readWrite @ masci_safety` ONLY.
**A5.** Verify both users from `mongosh` (operator workstation):
```bash
mongosh "mongodb+srv://masci-prod.1nduwmg.mongodb.net" \
  --username masci_preview_user --password "<vault>" \
  --eval 'db.getSiblingDB("masci_safety").listCollections()'
# expected: { ok: 0, errmsg: "not authorized on masci_safety …" }

mongosh "mongodb+srv://masci-prod.1nduwmg.mongodb.net" \
  --username masci_prod_user --password "<vault>" \
  --eval 'db.getSiblingDB("masci_safety_preview").listCollections()'
# expected: { ok: 0, errmsg: "not authorized on masci_safety_preview …" }
```

**GATE A** — Both `mongosh` probes must return `not authorized`. If either succeeds → F-03 / F-04 → return to A3/A4.

---

### PHASE B — Preview pod rotation
*Failure refs: F-07, F-08, F-09, F-10, F-11*

**B1.** Open preview pod env-vars in Emergent deploy console.
**B2.** Confirm `PREVIEW_MONGO_URL_BACKUP_<UTC>` already exists in vault (from §1).
**B3.** Set:
```
MONGO_URL              = mongodb+srv://masci_preview_user:<URL-ENC-PWD>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-preview
DB_NAME                = masci_safety_preview      (UNCHANGED — verify)
APP_ENV                = preview                    (UNCHANGED — verify)
ENFORCE_DB_ISOLATION   = true                       (NEW)
```
URL-encode the password (`@`→`%40`, `:`→`%3A`, etc.). Test with `mongosh "<URL>"` from operator workstation BEFORE pasting.

**B4.** Save → pod restarts.
**B5.** Wait ≤90 s. Tail logs:
```bash
# Banner expected
[db-isolation] OK · preview pod is correctly isolated.
# Forbidden
🔴 DB ISOLATION VIOLATION
```

**GATE B** — `/api/health = 200`, banner present, no `🔴` line.
- If `🔴` appears → F-12 → fix B3 (likely missed URL-encoding or wrong DB scope on user).
- If pod fails to boot → F-07 → restore `PREVIEW_MONGO_URL_BACKUP_<UTC>` and diagnose.
- If outage > 5 min → F-11 → rollback per `PREVIEW_CREDENTIAL_ROTATION_RUNBOOK.md` §Rollback.

---

### PHASE C — Production pod rotation
*Failure refs: F-07, F-08, F-09, F-10, F-11, F-24*

**C1.** Confirm Phase B completed cleanly (GATE B passed).
**C2.** Confirm `PROD_MONGO_URL_BACKUP_<UTC>` exists in vault.
**C3.** Open production pod env-vars. Set:
```
MONGO_URL              = mongodb+srv://masci_prod_user:<URL-ENC-PWD>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-prod
DB_NAME                = masci_safety              (UNCHANGED — verify)
APP_ENV                = production                (UNCHANGED — verify)
ENFORCE_DB_ISOLATION   = true                      (NEW)
JWT_SECRET             — UNCHANGED, DO NOT TOUCH (F-24 trigger)
SCHEDULER_ENABLED      = true                      (UNCHANGED — verify)
```
**C4.** Rolling-restart preferred if ≥2 replicas. Single-instance → accept ≤90 s in the maintenance window.
**C5.** Tail prod logs for banner `[db-isolation] OK · production pod is correctly isolated.`
**C6.** Confirm /api/health=200 within 90 s.
**C7.** A second operator opens a pre-rotation browser tab and refreshes the page → must remain logged in. If forced to login → **STOP, declare F-24, restore JWT_SECRET, escalate**.

**GATE C** — same as Gate B, plus no forced logout observed.

---

### PHASE D — Post-rotation verification
*Failure refs: F-16, F-17, F-18, F-19, F-20*

From **preview pod shell**:
```bash
cd /app/backend
python scripts/verify_preview_cannot_read_production.py   # exit 0
python scripts/verify_db_isolation.py                      # exit 0
python scripts/verify_post_rotation_health.py              # exit 0
python scripts/p0_trust_audit.py                           # writes /app/memory/p0_audit_*.json
```

From **production pod shell**:
```bash
cd /app/backend
python scripts/verify_production_cannot_read_preview.py   # exit 0
python scripts/verify_db_isolation.py                      # exit 0
python scripts/verify_post_rotation_health.py              # exit 0
python scripts/verify_production_stability.py              # exit 0
```

**GATE D** — every script exits 0; no `🔴 FAIL` lines; `p0_audit_atlas_users.json.authenticated_as.user` equals `masci_preview_user` (preview run) or `masci_prod_user` (prod run).

- Any FAIL → consult `ATLAS_ISOLATION_FAILURE_ANALYSIS.md` §4 (F-16..F-20). Do NOT proceed.

---

### PHASE E — Production stability validation
*Failure refs: F-23, F-24, F-25*

Run `PRODUCTION_STABILITY_VALIDATION_RUNBOOK.md` in full:
- Section 1 (DB sweep)
- Section 2 (API sweep)
- Section 3 (session continuity)
- Section 4 (worker sanity)
- Section 5 (24-hour soak)

**GATE E** — all 5 sections PASS. Operator records sign-off in that runbook §7.

---

### PHASE F — Trust Sprint re-execution
*Failure refs: F-21, F-22*

Run `TRUST_SPRINT_REEXECUTION_RUNBOOK.md`:
1. Re-run `p0_trust_audit.py`.
2. Flip `ATLAS_USER_ISOLATION_CERTIFICATION.md` from 🔴 → 🟢 (cite new JSON).
3. Flip `ENVIRONMENT_TRUTH_CERTIFICATION.md` T1 → 🟢.
4. Append "Resolved <UTC>" line to `ATLAS_CLUSTER_SPLIT_RECONCILIATION.md`.
5. Re-evaluate `MAP_GO_NO_GO_CERTIFICATION.md` — credential blocker now resolved. Map UI remains BLOCKED until Motive coverage ≥20% (separate workstream).

**GATE F** — all 5 substeps complete with operator initials + UTC timestamps.

---

### PHASE G — `admin_db_user` retirement
*Failure refs: F-26, F-27*

**G1.** Confirm Gate E (including 24h soak) AND Gate F both passed.
**G2.** Atlas UI → Database Access → `admin_db_user` → Delete.
**G3.** Verify:
```bash
mongosh "mongodb+srv://masci-prod.1nduwmg.mongodb.net" \
  --username admin_db_user --password "<old vault pwd>" \
  --eval 'db.runCommand({ping:1})'
# expected: Authentication failed
```

**GATE G** — Authentication for `admin_db_user` fails. The credential is dead.

---

### PHASE H — Closeout
*Failure refs: F-31, F-32*

H1. Flip every box in `FINAL_CLOSEOUT_CHECKLIST.md` to 🟢 with operator initials + UTC + evidence link.
H2. Workstream STATUS at top of `FINAL_CLOSEOUT_CHECKLIST.md` → **CLOSED**.
H3. Update `PRD.md` + `CHANGELOG.md` with closure entry.
H4. File `ATLAS_USER_ISOLATION_CLOSEOUT_EVIDENCE.md` containing:
    - JSON output of `p0_trust_audit.py` (both pods)
    - All `verify_*.py` PASS lines
    - 24h soak log
    - Atlas screenshot showing `admin_db_user` deleted
    - Operator signature

**Workstream CLOSED** only after H1–H4 complete.

---

## 4 · Single-page checklist (operator may print this page)

```
□ A1 · Atlas Admin login confirmed
□ A2 · masci_preview_user created with readWrite@masci_safety_preview ONLY
□ A3 · masci_prod_user created with readWrite@masci_safety ONLY
□ A4 · mongosh cross-DB probes BOTH return Unauthorized
─── GATE A ───
□ B1 · PREVIEW_MONGO_URL_BACKUP_<UTC> stored in vault
□ B2 · Preview pod MONGO_URL rotated + ENFORCE_DB_ISOLATION=true
□ B3 · Preview pod restarted + banner OK + /api/health=200
─── GATE B ───
□ C1 · PROD_MONGO_URL_BACKUP_<UTC> stored in vault
□ C2 · Production pod MONGO_URL rotated + ENFORCE_DB_ISOLATION=true
□ C3 · Production pod restarted + banner OK + /api/health=200
□ C4 · Pre-rotation browser session still logged in (F-24 guard)
─── GATE C ───
□ D1 · All 4 preview-side scripts exit 0
□ D2 · All 4 production-side scripts exit 0
□ D3 · p0_audit_atlas_users.json shows correct user per pod
─── GATE D ───
□ E1 · Stability §1 DB sweep PASS
□ E2 · Stability §2 API sweep PASS
□ E3 · Stability §3 session continuity PASS
□ E4 · Stability §4 worker sanity PASS
□ E5 · Stability §5 24h soak PASS
─── GATE E ───
□ F1 · Trust Sprint audit re-run
□ F2 · T1 + P0-A certs flipped to 🟢
□ F3 · ATLAS_CLUSTER_SPLIT_RECONCILIATION.md closed
□ F4 · MAP_GO_NO_GO updated (credential blocker resolved)
─── GATE F ───
□ G1 · admin_db_user deleted in Atlas
□ G2 · mongosh login as admin_db_user FAILS
─── GATE G ───
□ H1 · FINAL_CLOSEOUT_CHECKLIST.md all boxes 🟢
□ H2 · Workstream STATUS = CLOSED
□ H3 · PRD + CHANGELOG updated
□ H4 · ATLAS_USER_ISOLATION_CLOSEOUT_EVIDENCE.md filed
─── GATE H · WORKSTREAM CLOSED ───
```

---

## 5 · Authority & approvals

This package may only be executed by an operator who is:
- Atlas Project Owner OR Database Admin on `masci-prod`, AND
- Holds Emergent deploy-console access to BOTH pods, AND
- Has authority to maintain the secret vault.

No agent action is required during execution. The agent has prepared every artifact; the operator drives.

---

## 6 · Post-closure: what unblocks

Closure of this workstream unblocks (per `OMEGA_STATUS_REPORT.md`):
- Phase 5B Live Operations Map UI **(still requires Motive coverage ≥20% — separate workstream)**.
- FleetWatcher integration.
- MaintainX integration.
- Executive Mode dashboards.

None of these may begin until **this** workstream is CLOSED.

---

## 7 · References

- `ATLAS_USER_INVENTORY.md`
- `ATLAS_NAMESPACE_INVENTORY.md`
- `ATLAS_PERMISSION_ANALYSIS.md`
- `ATLAS_ISOLATION_FAILURE_ANALYSIS.md` (32 failure modes, F-01..F-32)
- `ATLAS_USER_SEPARATION_OPERATOR_RUNBOOK.md`
- `PREVIEW_CREDENTIAL_ROTATION_RUNBOOK.md`
- `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md`
- `POST_ROTATION_VERIFICATION_RUNBOOK.md`
- `PRODUCTION_STABILITY_VALIDATION_RUNBOOK.md`
- `TRUST_SPRINT_REEXECUTION_RUNBOOK.md`
- `FINAL_CLOSEOUT_CHECKLIST.md`
- `/app/backend/db_isolation_failsafe.py`
- `/app/backend/scripts/verify_isolation_suite.py` + 6 wrappers
- `/app/backend/scripts/p0_trust_audit.py`

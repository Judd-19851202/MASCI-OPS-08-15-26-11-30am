# FORGEDOPS · ATLAS ISOLATION · END-TO-END FAILURE ANALYSIS

**Workstream:** P0 Trust · Atlas User Isolation
**Status:** 🟡 **OPEN** (analysis complete · operator execution pending)
**Doctrine:** FORGEDOPS Execution Doctrine, 2026-02-10
**Scope:** Every failure mode capable of preventing successful workstream closure.

This document enumerates failures end-to-end across **19 surfaces** with: detection signal, impact, blast radius, rollback path, recovery path, and exit criteria. Operator must read this before executing the Execution Package.

---

## 0 · Reading guide

For each failure mode:
- **ID** · `F-NN`
- **Surface** · where the failure occurs
- **Detection** · how the operator notices
- **Blast radius** · who/what is affected
- **User impact** · whether end-users see anything
- **Rollback** · how to return to pre-step state
- **Recovery** · how to retry safely
- **Exit criteria** · how we know we're back on the happy path

All rollback paths share two non-negotiables:
- NO user password changes.
- NO session invalidation (JWT secret + `sessions` collection are untouched).

---

## 1 · Atlas user creation (Step 1–2 of Operator Runbook)

### F-01 · Atlas Admin login fails (MFA, permission)
- **Detection:** Atlas UI rejects login or shows "insufficient permissions".
- **Impact:** Cannot proceed; preview pod continues running on `admin_db_user`.
- **User impact:** None (no change made).
- **Rollback:** None needed.
- **Recovery:** Operator obtains Atlas Project Owner / Database Admin role from cluster owner.
- **Exit:** Operator successfully logs in and reaches `Database Access` panel.

### F-02 · Username collision (`masci_preview_user` / `masci_prod_user` already exists)
- **Detection:** Atlas UI: "user already exists"; API: HTTP 409.
- **Impact:** Cannot create user with the planned name.
- **User impact:** None.
- **Rollback:** None.
- **Recovery:** (a) If the existing user is correctly scoped (`readWrite@masci_safety_preview` only), reuse it and reset its password. (b) If wrongly scoped, delete it after confirming no pod uses it, then recreate.
- **Exit:** A user with the exact target name and target role exists.

### F-03 · Over-privileged role accidentally granted
- **Detection:** `db.getUser("masci_preview_user")` shows roles ≠ `[{role:"readWrite", db:"masci_safety_preview"}]`.
- **Impact:** Isolation goal not achieved; preview can still read prod (or worse).
- **User impact:** None yet.
- **Rollback:** Remove the extra role(s) via Atlas UI → Edit User → Specific Privileges → Remove.
- **Recovery:** Run `mongosh` `db.getUser` again to confirm. Then rerun rotation only if scope is now exact.
- **Exit:** Role array matches the target exactly.

### F-04 · Cluster scope restriction not applied
- **Detection:** "Restrict Access to Specific Clusters/Federated Database Instances" left blank (Atlas defaults to all clusters in project).
- **Impact:** User can hit other clusters in the same project.
- **User impact:** None.
- **Rollback:** Edit user → set Cluster Restrictions → `masci-prod` only → Save.
- **Recovery:** Re-test from `mongosh` against any other cluster — expect failure.
- **Exit:** Cluster restriction shows `masci-prod` only.

### F-05 · Weak / re-used password
- **Detection:** Operator audit checklist.
- **Impact:** Long-term credential risk (not an immediate isolation failure).
- **User impact:** None.
- **Rollback:** Reset password to a freshly generated strong value.
- **Recovery:** Reapply password in pod env-var, restart, verify health.
- **Exit:** Password is ≥32 chars, randomly generated, stored only in operator vault.

### F-06 · Atlas Admin API call fails (network, key)
- **Detection:** `curl` returns 4xx/5xx.
- **Impact:** API-driven creation blocked; UI-driven creation still available.
- **User impact:** None.
- **Rollback:** None.
- **Recovery:** Validate `ATLAS_PUBLIC_KEY` / `ATLAS_PRIVATE_KEY` / project ID, retry via UI.
- **Exit:** Either UI or API completes successfully.

---

## 2 · Credential rotation (Step 4–5 of Operator Runbook)

### F-07 · Password URL-encoding error in `MONGO_URL`
- **Detection:** Pod boot fails with `pymongo.errors.ConfigurationError` or `Authentication failed`. Backend log: `ServerSelectionTimeoutError` or `bad auth`.
- **Impact:** Pod cannot connect; `/api/*` returns 502.
- **User impact:** Users see service down until rollback completes.
- **Rollback:** Restore previous `MONGO_URL` from operator vault → restart → service returns in ≤90 s.
- **Recovery:** URL-encode every reserved char in the password (`@:/?#[]!$&'()*+,;= ` and `%`). Retest with `mongosh "<URL>"` from operator workstation before pasting into pod env.
- **Exit:** Pod boots, `/api/health` returns 200.

### F-08 · Wrong `DB_NAME` left in `.env`
- **Detection:** `/api/platform/data-truth` returns the wrong `database` field for the environment.
- **Impact:** Preview pod could be pointed at `masci_safety`; production pod could be pointed at `masci_safety_preview`. Reads succeed (data appears) but the pod is logically misconfigured.
- **User impact:** Data corruption risk (writes hit the wrong DB) — **catastrophic**.
- **Rollback:** Immediately restore correct `DB_NAME` from this runbook (preview=`masci_safety_preview`, production=`masci_safety`) → restart.
- **Recovery:** Audit any writes that happened during the misconfiguration window via Mongo oplog or change-stream. If any writes hit the wrong DB, use the most recent backup of the target DB to reconcile.
- **Exit:** `data-truth.environment` matches `data-truth.database` per the target matrix in `ATLAS_NAMESPACE_INVENTORY.md`.

### F-09 · `MONGO_URL` saved to the wrong pod
- **Detection:** Both pods now use the same credential (or swapped credentials).
- **Impact:** Same as F-08, plus loss of isolation.
- **User impact:** Risk of cross-environment writes.
- **Rollback:** Identify each pod via the pod name / environment label in the deploy console; reapply the correct credential to each.
- **Recovery:** Confirm with `/api/platform/data-truth` from each pod's public URL — preview should say `preview`, prod should say `production`.
- **Exit:** Both pods report the correct `environment` and `database`.

### F-10 · Env var saved but pod not restarted
- **Detection:** Backend continues to log connections to the old credential; data-truth still reports old state.
- **Impact:** Rotation has no effect; isolation not achieved.
- **User impact:** None (state unchanged).
- **Rollback:** None.
- **Recovery:** Restart the pod via deploy console. Confirm boot timestamp advances and new credential appears in connection logs.
- **Exit:** Pod restart timestamp is newer than env-var save timestamp.

### F-11 · Pod restart exceeds expected window (>90 s preview / planned for prod)
- **Detection:** `/api/health` returns 502/503 for >2 minutes.
- **Impact:** Extended user-facing outage.
- **User impact:** Brief outage; users get 502; **sessions are NOT lost** (JWT + Mongo sessions persist).
- **Rollback:** If outage exceeds 5 minutes, restore previous `MONGO_URL` and restart. Investigate from logs.
- **Recovery:** Most often a Mongo network blip; retry restart once.
- **Exit:** Pod boots, `/api/health=200`, banner `[db-isolation] OK · <env> pod is correctly isolated.` in logs.

---

## 3 · Startup failsafe (`db_isolation_failsafe.py`)

### F-12 · `ENFORCE_DB_ISOLATION=true` set with stale credential still in place
- **Detection:** Pod boot fails with `sys.exit(99)` and stderr line `🔴 DB ISOLATION VIOLATION · …`.
- **Impact:** Pod refuses to boot. This is **correct fail-fast behaviour**, not a regression.
- **User impact:** Outage proportional to time the credential remains stale.
- **Rollback:** Either (a) finish the credential rotation (preferred), or (b) remove `ENFORCE_DB_ISOLATION` from env-vars to fall back to bridge mode and accept the violation banner in logs while the rotation is completed.
- **Recovery:** Complete the rotation first, then re-enable `ENFORCE_DB_ISOLATION=true`.
- **Exit:** Pod boots with the banner `[db-isolation] OK · <env> pod is correctly isolated.` and no `🔴` line.

### F-13 · Failsafe import error / runtime exception
- **Detection:** `_db_isolation_failsafe` logs `probe failed (non-fatal): <exception>`. Pod continues to boot (per the wrapper's `except Exception as e: logger.warning(...)`).
- **Impact:** The probe did not actually verify isolation; **silent degradation**.
- **User impact:** None visible, but trust signal is missing.
- **Rollback:** None — the pod is up.
- **Recovery:** Read the exception, fix (likely a missing env var or motor client lifecycle), redeploy. The wrapper is intentionally non-fatal so a broken probe never causes an outage.
- **Exit:** Probe runs cleanly; banner appears in logs.

### F-14 · False positive (probe says VIOLATION when there is none)
- **Detection:** Banner shown, but `mongosh` from operator workstation confirms the credential is correctly scoped.
- **Impact:** Pod will not boot in enforce mode → outage.
- **User impact:** Outage until misdiagnosis is corrected.
- **Rollback:** Set `ENFORCE_DB_ISOLATION=false`, restart.
- **Recovery:** Inspect probe output. Most likely cause: probe was run during the brief window before the new credential propagated; transient. Wait 60 s and retry. If persistent, suspect the wrong probe interpretation of `OperationFailure` text (Atlas response wording can vary across versions).
- **Exit:** Banner clears on next restart.

### F-15 · False negative (probe says ISOLATED when credential is over-privileged)
- **Detection:** `mongosh` from inside the pod shows it CAN list the forbidden DB despite the OK banner.
- **Impact:** Silent isolation failure; the workstream cannot be CLOSED.
- **User impact:** None visible, but Trust Sprint cannot certify.
- **Rollback:** N/A (no action taken yet).
- **Recovery:** This indicates a logic bug in `assert_db_isolation`. Inspect: did the call return an empty list (no exception) yet the probe treated 0 collections as inaccessible? The current code in `db_isolation_failsafe.py:68-76` correctly records a violation whenever the call succeeds (regardless of count) — this should not occur with current logic, but is documented for defense-in-depth. If observed, file a P0 platform incident.
- **Exit:** Probe correctly flags the violation; banner appears.

---

## 4 · Verification scripts (`/app/backend/scripts/`)

### F-16 · Wrong `APP_ENV` for the script
- **Detection:** `verify_preview_cannot_read_production.py` prints `not running in preview env — skip` and exits 2.
- **Impact:** Script reports an indeterminate result.
- **User impact:** None.
- **Rollback:** N/A.
- **Recovery:** Confirm the pod's `APP_ENV` matches the script's expectation; run the correct script from the correct pod.
- **Exit:** Script exits 0 or 1 (definitive).

### F-17 · Network timeout reaching Atlas
- **Detection:** `pymongo.errors.NetworkTimeout` / `ServerSelectionTimeoutError`.
- **Impact:** Verification incomplete.
- **User impact:** None.
- **Rollback:** N/A.
- **Recovery:** Retry. Most often transient Atlas-side. If persistent, check IP allowlist (Atlas Network Access list) — the new pod's NAT egress IP must be allowed.
- **Exit:** Script completes with a definitive exit code.

### F-18 · Script false positive (`PASS` despite violation)
- **Detection:** Manual `mongosh` proves the credential can read the forbidden DB while `verify_preview_cannot_read_production.py` exits 0.
- **Impact:** Workstream certified prematurely; isolation not real.
- **User impact:** None visible.
- **Rollback:** Revert Trust Sprint certification flips; mark workstream OPEN again.
- **Recovery:** Inspect script logic. The current logic (`_expect_unauthorized`) treats *any* successful `list_collection_names` as failure — false positive would require an exception that was incorrectly classified as "unauthorized". Add an explicit collection-count probe as belt-and-suspenders if observed.
- **Exit:** Script honestly reflects state.

### F-19 · Script false negative (`FAIL` despite correct isolation)
- **Detection:** Manual `mongosh` shows `Unauthorized` while script exits 1.
- **Impact:** Operator wastes time on rollback / retry; workstream stalls.
- **User impact:** None.
- **Rollback:** N/A.
- **Recovery:** Inspect stderr/stdout. Likely cause: Atlas response text didn't match `"not authorized" / "unauthorized"` substring check. Widen the matcher to include `"authentication failed"`, `"requires authentication"` if observed.
- **Exit:** Script exit code reflects truth.

### F-20 · `verify_production_stability.py` reports zero docs in `employees` / `equipment_master`
- **Detection:** PASS but counts are 0.
- **Impact:** Read works but the *expected* dataset is missing — possibly wrong DB.
- **User impact:** Could indicate F-08 (wrong `DB_NAME`).
- **Rollback:** Compare to `PHASE1_PROD_DATA_BASELINE.txt` (596 assets, 262 employees). If counts deviate by >5%, treat as F-08.
- **Recovery:** Per F-08.
- **Exit:** Counts within 5% of baseline.

---

## 5 · Trust Sprint re-execution

### F-21 · `p0_trust_audit.py` shows `authenticated_as.user = admin_db_user` after rotation
- **Detection:** JSON output `/app/memory/p0_audit_atlas_users.json` contains `"user": "admin_db_user"`.
- **Impact:** Rotation did not actually take effect inside the pod.
- **User impact:** None visible.
- **Rollback:** N/A.
- **Recovery:** Confirm env-var was saved to the correct pod AND the pod restarted. Re-restart. Re-run audit.
- **Exit:** `authenticated_as.user` matches the target (`masci_preview_user` or `masci_prod_user`).

### F-22 · T1 / P0-A certifications not flipped to 🟢
- **Detection:** Markdown files still show 🔴.
- **Impact:** Workstream remains OPEN even after technical success.
- **User impact:** None.
- **Rollback:** N/A.
- **Recovery:** Operator edits the certs per `TRUST_SPRINT_REEXECUTION_RUNBOOK.md` Step 2 with the new audit JSON cited as evidence.
- **Exit:** Both certs show 🟢 with operator initials and timestamp.

---

## 6 · Production stability validation

### F-23 · Scheduler / sync worker auth errors after rotation
- **Detection:** `backend.err.log` shows `OperationFailure: not authorized on <collection> to execute …`.
- **Impact:** Background jobs fail; production stability not achieved.
- **User impact:** Stale data in dashboards (no immediate write impact).
- **Rollback:** Per `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md` rollback.
- **Recovery:** The new user's role was `readWrite` — should cover all app operations. If a specific worker needs admin privileges (e.g., `createIndex`), add a one-time `dbAdmin@masci_safety` grant or run index creation as an operator action separately.
- **Exit:** Scheduler logs clean for 60 minutes.

### F-24 · Existing user sessions lost / forced logout
- **Detection:** Users report being kicked back to login after rotation.
- **Impact:** **DOCTRINAL VIOLATION** — non-negotiable guarantee breached.
- **User impact:** Forced re-login for every active user.
- **Rollback:** Investigate immediately. Likely cause: someone changed `JWT_SECRET` or dropped the `sessions` collection — both of which are **explicitly forbidden** by every rotation runbook.
- **Recovery:** Restore `JWT_SECRET` from operator vault. If `sessions` was dropped, restore from backup.
- **Exit:** Active sessions resume.

### F-25 · 24-hour soak shows new errors
- **Detection:** Sentry / log aggregator shows a class of error not seen pre-rotation.
- **Impact:** Workstream cannot proceed to closeout.
- **User impact:** Variable (depends on error class).
- **Rollback:** Per `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md`.
- **Recovery:** Analyze error class. Common cause: a code path that requires a privilege beyond `readWrite` (e.g., `serverStatus`, `replSetGetStatus`). Add the precise privilege to the user, never broaden to cluster-wide.
- **Exit:** 24h elapse with no soak-relevant errors.

---

## 7 · `admin_db_user` deletion (Step 10 of Operator Runbook)

### F-26 · Deleted prematurely (before Stability + Soak PASS)
- **Detection:** Operator deletes `admin_db_user` before 24h soak completes.
- **Impact:** Rollback path is destroyed; if any failure surfaces after deletion, recovery requires recreating the user (with the same level of cluster-wide privilege) before reverting `MONGO_URL`.
- **User impact:** Extended outage if rollback is needed.
- **Rollback:** Recreate `admin_db_user` in Atlas with `readWriteAnyDatabase`, generate new password, paste into pod env. Workstream is now BACK TO START.
- **Recovery:** Per `Operator Runbook` from Step 1.
- **Exit:** Deletion deferred until 24h soak PASS.

### F-27 · Deletion failure (Atlas Admin error)
- **Detection:** Atlas UI returns an error on delete.
- **Impact:** User remains. Workstream cannot fully close.
- **User impact:** None.
- **Rollback:** N/A.
- **Recovery:** Retry via API; if still failing, contact Atlas support.
- **Exit:** `db.getUser("admin_db_user")` returns null.

---

## 8 · Operator-mistake catalogue

| Mistake | Detection | Mitigation in Execution Package |
|---|---|---|
| Pasted credential into wrong pod | Different `data-truth` than expected | Section 5 sign-off requires per-pod evidence capture |
| Skipped backup of old `MONGO_URL` | Cannot roll back F-07/F-08 | Section 2 step 2 BLOCKS until vault entry confirmed |
| Removed `JWT_SECRET` "to be safe" | Forced logout (F-24) | Execution Package explicitly lists every var that MUST NOT be touched |
| Deleted `admin_db_user` first (before rotation) | Both pods immediately 502 | Execution Package ordering is FROZEN; F-26 enumerates consequence |
| Saved password unencrypted in chat / ticket | Long-term credential leak | Pre-flight checklist requires "secret vault" location |
| Forgot to set `ENFORCE_DB_ISOLATION=true` | Failsafe stays in bridge mode | Closeout checklist gates on env-var presence |

---

## 9 · Connectivity / authentication / permission baseline failures

### F-28 · Atlas IP allowlist blocks the pod's NAT egress
- **Detection:** `ServerSelectionTimeoutError` on every connection attempt.
- **Impact:** Pod cannot reach Atlas at all.
- **User impact:** Full outage.
- **Rollback:** None (pod was already unreachable).
- **Recovery:** Atlas → Network Access → confirm `0.0.0.0/0` OR the operator's known pod-egress CIDR is allowlisted. The rotation does NOT change egress, so this only triggers if allowlist was modified concurrently.
- **Exit:** `nc -zv masci-prod.1nduwmg.mongodb.net 27017` succeeds.

### F-29 · DNS failure for `mongodb+srv://` lookup
- **Detection:** `pymongo.errors.ConfigurationError: All nameservers failed to answer`.
- **Impact:** Pod cannot resolve SRV.
- **User impact:** Full outage.
- **Rollback:** N/A.
- **Recovery:** Wait for DNS recovery (transient) or switch to explicit seed-list URL.
- **Exit:** SRV resolves; pod boots.

### F-30 · Connection pool exhausted under load
- **Detection:** `PoolMaxConnections reached`, slow responses, intermittent 502.
- **Impact:** User-visible latency / errors.
- **User impact:** Mostly transient.
- **Rollback:** N/A (not credential-related).
- **Recovery:** Increase `maxPoolSize` in `MONGO_URL` query string (e.g., `&maxPoolSize=100`). This is unrelated to isolation but documented because the rotation is a likely scapegoat.
- **Exit:** Pool sized for production load.

---

## 10 · Workstream-closure failure modes

### F-31 · Closeout checkbox flipped without evidence
- **Detection:** Quarterly trust audit finds a 🟢 box with no operator initials / no script output / no log line cited.
- **Impact:** Workstream re-opens; trust score regresses.
- **Recovery:** Audit each box; revert any with missing evidence; re-collect evidence; re-flip.

### F-32 · "Good enough for now" justifications
- **Doctrine reference:** FORGEDOPS Execution Doctrine, 2026-02-10 — **explicitly forbidden**.
- **Detection:** PR / commit message containing the phrase "future sprint" or "we'll come back to this" in the Trust workstream.
- **Recovery:** Reject the PR. Workstream stays OPEN.

---

## 11 · Summary failure-mode matrix

| Tier | Count | Surface |
|---|---|---|
| Atlas user mgmt | 6 | F-01–F-06 |
| Rotation | 5 | F-07–F-11 |
| Startup failsafe | 4 | F-12–F-15 |
| Verification scripts | 5 | F-16–F-20 |
| Trust Sprint re-exec | 2 | F-21–F-22 |
| Production stability | 3 | F-23–F-25 |
| `admin_db_user` deletion | 2 | F-26–F-27 |
| Operator mistakes | catalogue | §8 |
| Connectivity / auth / perm | 3 | F-28–F-30 |
| Workstream closure | 2 | F-31–F-32 |
| **TOTAL** | **32 + catalogue** | end-to-end |

Every entry has detection, impact, rollback, recovery, and exit criteria. Operator must reference this document before any step in the Execution Package.

---

## 12 · Recovery decision tree (top level)

```
Failure during Atlas user mgmt (F-01..F-06)?
  → No pod change yet. Fix in Atlas. Restart this section. NO ROLLBACK needed.

Failure during rotation (F-07..F-11)?
  → Pod state changed.
  → Restore prior MONGO_URL from vault. Restart pod. Verify /api/health=200.
  → Diagnose root cause from logs. Address. Retry rotation.

Failsafe banner showing VIOLATION (F-12)?
  → Either complete rotation or set ENFORCE_DB_ISOLATION=false temporarily.
  → DO NOT delete admin_db_user.

Verification script FAIL (F-16..F-20)?
  → Capture evidence. If F-18/F-19 (false pos/neg), inspect script logic.
  → Otherwise, treat per matching rotation rollback.

Trust Sprint shows old user (F-21)?
  → Env-var didn't apply or pod didn't restart. Retry restart.

Stability fail (F-23..F-25)?
  → If F-24 (forced logout) — immediately restore JWT_SECRET. P0 incident.
  → Otherwise rollback per stability runbook §6.

admin_db_user deletion error (F-26, F-27)?
  → Workstream cannot close. Investigate per F-26/F-27.
```

---

## 13 · Non-negotiable guarantees referenced throughout

1. NO user password changes.
2. NO forced logouts.
3. NO session invalidation.
4. NO authentication-code changes.
5. NO RBAC changes.
6. NO `JWT_SECRET` rotation.
7. NO drop / truncation of `sessions` collection.

A failure that breaches any of these seven is a **P0 incident**, not a workstream failure mode.

---

## 14 · Exit from this analysis

This document is COMPLETE.
- Next consumer: `ATLAS_ISOLATION_EXECUTION_PACKAGE.md` (the single operator-facing artifact).
- Next gate: 🟡 → 🟢 only when **every** F-NN above has been demonstrated *not* to occur during the actual execution.

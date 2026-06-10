# FORGEDOPS · ATLAS ISOLATION · WORKSTREAM CLOSEOUT PLAN

**Workstream:** P0 Trust · Atlas User Isolation
**Status:** 🟡 **OPEN** (Atlas user separation NOT YET EXECUTED by operator)
**Last review:** 2026-02-10
**Authority:** FORGEDOPS Execution Doctrine, 2026-02-10

This document defines exactly how the workstream transitions from **OPEN** to **CLOSED**, who signs, and what closure unblocks.

---

## 1 · Status definition (only two values permitted)

| Status | Meaning |
|---|---|
| 🟡 **OPEN** | One or more closure gates not yet 🟢. Workstream remains active. No downstream work may begin. |
| 🟢 **CLOSED** | Every closure gate 🟢 with operator-verifiable evidence. Workstream is sealed. Downstream workstreams may begin. |

Per doctrine, **no other status values are permitted.** Phrases like "mostly complete", "pending stabilization", "next sprint", "good enough" are explicit doctrine violations and constitute F-32.

---

## 2 · Closure gates (all must be 🟢)

### Gate 1 · BUILD COMPLETE  ✅
- [x] `db_isolation_failsafe.py` shipped (`/app/backend/db_isolation_failsafe.py`).
- [x] `verify_isolation_suite.py` + 6 named wrappers shipped (`/app/backend/scripts/`).
- [x] `p0_trust_audit.py` shipped.
- [x] `/api/platform/data-truth` endpoint shipped.
- [x] All 7 operator runbooks authored:
  - `ATLAS_USER_SEPARATION_OPERATOR_RUNBOOK.md`
  - `PREVIEW_CREDENTIAL_ROTATION_RUNBOOK.md`
  - `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md`
  - `POST_ROTATION_VERIFICATION_RUNBOOK.md`
  - `PRODUCTION_STABILITY_VALIDATION_RUNBOOK.md`
  - `TRUST_SPRINT_REEXECUTION_RUNBOOK.md`
  - `FINAL_CLOSEOUT_CHECKLIST.md`
- [x] `ATLAS_ISOLATION_FAILURE_ANALYSIS.md` shipped (32 failure modes F-01..F-32).
- [x] `ATLAS_ISOLATION_EXECUTION_PACKAGE.md` shipped (single-page execution sequence).
- [x] This closeout plan shipped.

### Gate 2 · INTEGRATION COMPLETE  ✅
- [x] Failsafe wired into `server.py @app.on_event("startup")` (verified line 9165–9178).
- [x] Audit driver outputs JSON to `/app/memory/p0_audit_*.json`.
- [x] All wrapper scripts import `verify_isolation_suite` cleanly (zero lint errors).

### Gate 3 · VERIFICATION COMPLETE  🟡  ← OPERATOR-GATED
- [ ] Atlas user `masci_preview_user` exists with role `[{readWrite, masci_safety_preview}]` ONLY.
- [ ] Atlas user `masci_prod_user` exists with role `[{readWrite, masci_safety}]` ONLY.
- [ ] Preview pod `MONGO_URL` rotated to `masci_preview_user`.
- [ ] Production pod `MONGO_URL` rotated to `masci_prod_user`.
- [ ] `ENFORCE_DB_ISOLATION=true` set in BOTH pods.
- [ ] `verify_preview_cannot_read_production.py` exits 0 from preview pod.
- [ ] `verify_production_cannot_read_preview.py` exits 0 from production pod.
- [ ] `verify_post_rotation_health.py` exits 0 in both pods.
- [ ] `verify_production_stability.py` exits 0.
- [ ] `verify_trust_sprint_completion.py` exits 0.
- [ ] `p0_trust_audit.py` JSON shows `authenticated_as.user = masci_preview_user` (from preview) and `masci_prod_user` (from prod).
- [ ] Startup banner `[db-isolation] OK · <env> pod is correctly isolated.` present in BOTH pods.
- [ ] Zero `🔴 DB ISOLATION VIOLATION` lines in BOTH pods.

### Gate 4 · STABILITY COMPLETE  🟡  ← OPERATOR-GATED
- [ ] `PRODUCTION_STABILITY_VALIDATION_RUNBOOK.md` §1 (DB sweep) PASS.
- [ ] §2 (API sweep) PASS — `data-truth` shows `production`/`masci_safety`.
- [ ] §3 (session continuity) PASS — zero forced logouts.
- [ ] §4 (worker sanity) PASS — no `OperationFailure` in scheduler logs.
- [ ] §5 (60-minute observation window — revised 2026-02-10 per `ATLAS_ISOLATION_FINAL_GO_NO_GO.md` §4) PASS — zero soak-relevant errors.

### Gate 5 · TRUST SPRINT RE-EXEC COMPLETE  🟡  ← OPERATOR-GATED
- [ ] `ATLAS_USER_ISOLATION_CERTIFICATION.md` flipped 🔴 → 🟢 with new audit JSON cited.
- [ ] `ENVIRONMENT_TRUTH_CERTIFICATION.md` T1 flipped 🔴 → 🟢.
- [ ] `ATLAS_CLUSTER_SPLIT_RECONCILIATION.md` updated with "Resolved <UTC>" + operator initials.
- [ ] `MAP_GO_NO_GO_CERTIFICATION.md` updated (credential blocker now resolved; Motive blocker remains).

### Gate 6 · `admin_db_user` RETIRED  🟡  ← OPERATOR-GATED
- [ ] `admin_db_user` deleted in Atlas UI.
- [ ] `mongosh` authentication attempt with old `admin_db_user` credentials **FAILS** (`Authentication failed`).
- [ ] No pod env-var references `admin_db_user` (grep both pods).

### Gate 7 · EVIDENCE FILED  🟡  ← OPERATOR-GATED
- [ ] `/app/memory/ATLAS_USER_ISOLATION_CLOSEOUT_EVIDENCE.md` filed containing:
    - Both `p0_audit_*.json` outputs (or links).
    - `verify_*.py` PASS lines (both pods).
    - 24h soak log.
    - Atlas screenshot showing `admin_db_user` deleted.
    - Operator initials + UTC timestamps.

### Gate 8 · CHECKLIST SIGN-OFF  🟡  ← OPERATOR-GATED
- [ ] Every box in `FINAL_CLOSEOUT_CHECKLIST.md` is 🟢.
- [ ] Operator signature recorded in `FINAL_CLOSEOUT_CHECKLIST.md` PROVEN-COMPLETE section.

### Gate 9 · WORKSTREAM STATUS FLIPPED
- [ ] `FINAL_CLOSEOUT_CHECKLIST.md` top banner: `🟢 CLOSED · <UTC> · <operator>`.
- [ ] This document's top banner: `🟢 CLOSED · <UTC> · <operator>`.
- [ ] `PRD.md` / `CHANGELOG.md` closure entries committed.

---

## 3 · Remaining operator actions (ordered)

| # | Action | Runbook |
|---|---|---|
| 1 | Create `masci_preview_user` + `masci_prod_user` in Atlas | `ATLAS_USER_SEPARATION_OPERATOR_RUNBOOK.md` Steps 1–3 |
| 2 | Rotate preview pod `MONGO_URL` + `ENFORCE_DB_ISOLATION=true` | `PREVIEW_CREDENTIAL_ROTATION_RUNBOOK.md` |
| 3 | Rotate production pod `MONGO_URL` + `ENFORCE_DB_ISOLATION=true` | `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md` |
| 4 | Run post-rotation verification (both pods) | `POST_ROTATION_VERIFICATION_RUNBOOK.md` |
| 5 | Run production stability validation (incl. 24h soak) | `PRODUCTION_STABILITY_VALIDATION_RUNBOOK.md` |
| 6 | Re-execute Trust Sprint | `TRUST_SPRINT_REEXECUTION_RUNBOOK.md` |
| 7 | Delete `admin_db_user` | `ATLAS_USER_SEPARATION_OPERATOR_RUNBOOK.md` Step 10 |
| 8 | File closeout evidence + flip workstream to CLOSED | This doc §2 Gate 7–9 |

The single consolidated artifact for all 8 actions is `ATLAS_ISOLATION_EXECUTION_PACKAGE.md` (PHASES A–H).

---

## 4 · What closure unblocks

When this workstream flips to 🟢 **CLOSED**:

| Downstream | Status today | Status after closure |
|---|---|---|
| Phase 5B Live Operations Map UI | BLOCKED on Trust + on Motive coverage | Trust unblocked. Still BLOCKED on Motive coverage ≥20%. |
| FleetWatcher integration | BLOCKED on Trust | UNBLOCKED. May begin design. |
| MaintainX integration | BLOCKED on Trust | UNBLOCKED. May begin design. |
| Executive Mode dashboards | BLOCKED on Trust | UNBLOCKED. May begin design. |
| REAL-DEVICE-LCP-001 mobile LCP fixes | DEFERRED (per Omega directive) | Reactivatable. |

Note: closure of this Trust workstream is **necessary but not sufficient** for the Map UI. Motive coverage remains a separate gate.

---

## 5 · Failure to close

If, after operator execution, any gate fails to flip to 🟢, the workstream remains **OPEN**. The doctrine forbids:
- Marking the workstream "mostly closed".
- Marking the workstream "closed pending fix".
- Marking the workstream "closed with caveat".
- Treating closure of *some* gates as partial credit.

The operator must:
1. Identify which gate failed.
2. Reference the failure mode in `ATLAS_ISOLATION_FAILURE_ANALYSIS.md`.
3. Execute the recovery path.
4. Re-attempt the gate.
5. Workstream stays OPEN until the gate honestly passes.

---

## 6 · Authority & sign-off template

```
ATLAS USER ISOLATION · WORKSTREAM CLOSEOUT

Date (UTC):                __________________________
Operator name:             __________________________
Operator role:             __________________________
Atlas Project:             masci-prod
Atlas user deleted:        admin_db_user
New users:                 masci_preview_user, masci_prod_user
24h soak window:           __________  →  __________
Audit JSON (preview):      /app/memory/p0_audit_atlas_users.json (preview)
Audit JSON (production):   /app/memory/p0_audit_atlas_users.json (prod)
Evidence file:             /app/memory/ATLAS_USER_ISOLATION_CLOSEOUT_EVIDENCE.md
Workstream status:         🟢 CLOSED
Operator signature:        __________________________
```

Once filled in, this block is the authoritative closure record.

---

## 7 · Honest status (today)

**Workstream is 🟡 OPEN.**

Reason: Atlas user separation has not yet been executed. Six of nine gates depend on operator action that the agent cannot perform (no Atlas Admin authority, no Emergent deploy-console authority on the production pod).

Three gates (BUILD, INTEGRATION, this CLOSEOUT-PLAN authorship) are ✅ green.

Closure is blocked only on operator execution. The agent has delivered every artifact required for that execution.

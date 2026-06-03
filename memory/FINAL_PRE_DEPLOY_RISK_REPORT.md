# FINAL PRE-DEPLOY · RISK REPORT
## OMEGA Pre-Deploy Certification · Phase 9 (observability) + Phase 10 (risk classification) of 11

**Date**: 2026-06-03

---

## PHASE 9 · Observability findings

### 9.1 · Backend log scan

| Finding | Severity | Source | OKCP-introduced? |
|---|---|---|:-:|
| `passkeys.WARNING: challenge TTL index ensure failed: ... IndexOptionsConflict` (300s requested vs 86400s existing) | 🟡 LOW | `passkeys.py` module init | ❌ Pre-existing |
| `server.WARNING [scheduled-backup] disk at 80% on boot — running emergency prune` | 🟡 LOW | boot-time backup task | ❌ Pre-existing |
| `health_monitor.WARNING [health_monitor] ALERT sent=False subsystems=['backup']` | 🟡 LOW | health monitor | ❌ Pre-existing |
| `server.CRITICAL [scheduled-backup] scheduler task is DEAD — respawning. Last state: completed without error` (recurring every ~5 min) | 🟠 MEDIUM | scheduler | ❌ Pre-existing |

### 9.2 · Health endpoint

- `/api/health` returns HTTP 200 · 73 bytes · 170 ms
- Backend supervisor: RUNNING (29 min uptime since last restart for OKCP loading)
- Frontend supervisor: RUNNING (7h+ uptime)
- MongoDB supervisor: RUNNING

### 9.3 · Rollback path

- **Previous production hash recorded?** Operator-tracked; this certification has HEAD `a1949bb70623a9bb7479565965cbc1936dcfcdcd`. Operator should record this and the prior deploy hash before deploy.
- **New deploy hash can be verified**: Yes, `git rev-parse HEAD` available.
- **Rollback mechanism**: `git revert` of OKCP commit + redeploy is supported. No DB migrations to roll back. No env-var changes to roll back.

---

## PHASE 10 · Deployment Risk Classification

### 🔴 BLOCKER — 1 item

#### B-1 · OKCP scope-doctrine violation on 33 tips

- **Description**: 33 OKCP-added tip dicts use `scopes=["public"]` on form_keys whose existing siblings are scoped HR / leadership / admin-shop / admin-dispatch / admin-safety. Anonymous callers can read intended-scope coaching.
- **Blast radius**: Anyone with the public API URL (no auth required) can `curl /api/guidance/tips?form_key=payroll-variance` etc. and receive HR-only operational guidance. Data exposure is operational coaching content, not credentials or PII.
- **Likelihood**: 100% if deployed in current state.
- **Rollback**: `git revert` the OKCP commit (would also revert the GREEN improvements) OR apply the targeted scope-fix patch (33 string replacements in `tips.py`, ~5 minutes, no schema/test changes needed) — re-runs `test_iter282_*` and `test_iter224_*` to confirm pass.
- **Operator action required**: Authorize the targeted scope-fix patch. (NOT a revert — the OKCP improvements are real and valuable; only the scope-tag mistake needs correction.)
- **Reference**: `FINAL_PRE_DEPLOY_SECURITY_PERMISSION_REVIEW.md` §2

### 🟠 MEDIUM — 1 item

#### M-1 · scheduled-backup scheduler task DEAD (recurring respawn)

- **Description**: Every ~5 min the backup scheduler is reported DEAD and respawned. Last-state is "completed without error" so the prior cycle did succeed, but the task is not staying alive between cycles.
- **Blast radius**: Backup integrity is observably maintained (cycles complete), but operator visibility into "what's normal" is degraded by the CRITICAL noise.
- **Likelihood**: Recurring; pre-existing pattern.
- **Rollback**: Not applicable — pre-existing.
- **Operator action**: Investigate root cause in a separate FOCP gate. Not a deploy blocker, but should be on the next-priority list after deploy.

### 🟡 LOW — 4 items

#### L-1 · Passkeys TTL index conflict
- Pre-existing index-name collision; cosmetic warning. No user-facing impact.

#### L-2 · Disk-at-80%-on-boot warning
- Emergency prune runs successfully; pre-existing.

#### L-3 · `Exact CSV Payload` i18n key missing ES entry
- Pre-existing; single key falls back to EN. Cosmetic for ES users in HR Payroll Variance.

#### L-4 · Pre-existing tip body >80 words on `driver-qualification.restrictions/escalate`
- Pre-existing validation warning; not OKCP-introduced.

### 🟢 None — no other issues identified

---

## Aggregate risk classification

| Tier | Count | Operator action |
|---|---:|---|
| 🔴 BLOCKER | 1 | Authorize remediation (mechanical, ~5 min) |
| 🟠 MEDIUM | 1 | Schedule investigation post-deploy |
| 🟡 LOW | 4 | Backlog |
| 🟢 OK | All other systems | No action |

**Deploy gate**: 🔴 **BLOCKED** until BLOCKER B-1 is remediated.

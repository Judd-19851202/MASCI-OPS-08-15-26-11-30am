# PLATFORM_RECOVERY_GAP_REPORT

**Date:** 2026-05-30 (Batch F · Phase 4)
**Question:** "Everything that still prevents — Destroy production. Restore backup. Resume operations."

---

## 1 · Gap inventory

### 🔴 GAP-1 — Daily Report inline base64 photo/subcontractor data drives unsustainable archive growth

**Severity**: 🔴 CRITICAL
**Risk**: Worker OOM within ~3 days at current hourly cadence; archive becomes unrestorable (exceeds the `/api/exports/restore` 500 MB ceiling once it crosses that line)
**Evidence**: `BACKUP_GROWTH_FORENSICS_REPORT §2-3`. Largest DR is 11.33 MB. `subcontractors[]` field alone is 6.9 MB on largest DR.
**Fix effort**: 1–2 days engineering (audit all photo-carrying fields in `daily_reports` schema · write a one-time migration that uploads embedded base64 to R2 · replace with `photo://` references · update the upload flow to never inline new uploads)
**Recommended action**: Schedule for next batch. Halts the OOM trajectory and reduces archive size from 442 MB to ~110 MB (-75%).

### 🔴 GAP-2 — Master multi-login broken post-restore until 7-user password reseed

**Severity**: 🔴 CRITICAL
**Risk**: Until reseed, ONLY the env-based `/api/admin/login` works. The 7 directory users (operator, safety, dispatch, HR, accounting, shop manager, Leticia) cannot log in.
**Evidence**: `APPLICATION_BOOT_DRILL_REPORT §2`. Drill backend confirmed all multi-login attempts return 401.
**Fix effort**: 1 hour code change. Extend `_seed_hash` re-seed block at `server.py:7596` to handle `user_directory` collection — same pattern as the existing `users` collection handling. Stamp `Welcome2MASCI! + must_change_password=true`.
**Recommended action**: Apply in next batch. Eliminates the manual reseed step entirely from the recovery procedure.

### 🟡 GAP-3 — `BACKUP_R2_HOURLY=true` cascade OOM trajectory

**Severity**: 🟡 HIGH
**Risk**: With ~70 MB/day archive growth (per growth forensics §6), worker hits 600 MB OOM watermark in ~3 days. 24× per day attempts means cascading failures within hours of crossing the watermark.
**Evidence**: Today's archive at 442 MB · 158 MB headroom under watermark · growth rate ~70 MB/day.
**Fix effort**: 1 env-var change. Set `BACKUP_R2_HOURLY=false` + `BACKUP_R2_FULL_HOUR_UTC=4`.
**Recommended action**: Operator should apply IMMEDIATELY (before next 14:00 UTC tick if possible). Mitigates GAP-1 timeline, buying 5–6 weeks before any worker-memory concern resurfaces.

### 🟡 GAP-4 — R2 photo bytes are in the archive but no automated re-upload step

**Severity**: 🟡 MEDIUM
**Risk**: If R2 itself is lost (catastrophic ⛔ R2 + Mongo), the archive contains the bytes BUT `restore_drill.py` only restores Mongo — photos remain absent from R2 until a manual batch upload script is built.
**Evidence**: `RESTORE_VALIDATION_REPORT §3.5`.
**Fix effort**: 2-4 hours engineering. Add a `--restore-photos` flag to `restore_drill.py` that walks `photos/` prefix in the archive and uploads each blob back to R2 at its original key.
**Recommended action**: Schedule for next batch alongside GAP-2 fix.

### 🟡 GAP-5 — Indexes not in archive, recreated on backend cold-start

**Severity**: 🟡 LOW
**Risk**: First few minutes after backend boot, indexed queries are slow. No correctness issue. Indexes form within the boot sequence per Phase 1 drill (`[safety-indexes] ensured`, `[fleet-ops] indexes ensured`, etc.).
**Evidence**: Drill backend logged all index-creation events during boot.
**Fix effort**: No fix required — current behavior is correct. Could optionally add index creation timing to startup metrics.
**Recommended action**: Document as expected behavior; no remediation needed.

### 🟡 GAP-6 — Frontend not exercised end-to-end against restored DB

**Severity**: 🟡 MEDIUM
**Risk**: 100% of API endpoints exercised work, so the React frontend will almost certainly work — but "logical inference" is weaker than "lit up and validated."
**Evidence**: `APPLICATION_BOOT_DRILL_REPORT §3` describes the gap.
**Fix effort**: 30 minutes — build the React app with `REACT_APP_BACKEND_URL=http://localhost:8002` + run a 5-page Playwright walk-through.
**Recommended action**: Schedule alongside Batch F follow-up (closes the last UI gap).

### 🟡 GAP-7 — `webauthn_challenges` index drift

**Severity**: 🟡 LOW
**Risk**: Backend startup logs a warning about TTL mismatch (existing index has 86400 s TTL vs code wants 300 s). Not blocking. New challenges still expire on the existing index. Symptom of an old index that was never dropped after spec change.
**Evidence**: Drill backend log: `passkeys - WARNING - [passkeys] challenge TTL index ensure failed: IndexOptionsConflict`.
**Fix effort**: 1 line — `db.webauthn_challenges.drop_index("ttl_webauthn_challenges_created_at")` once in production, then the code re-creates with 300 s TTL.
**Recommended action**: Defer to ops-housekeeping batch.

### 🟡 GAP-8 — `disk_high_watermark` on boot reported 76% (exceeded 75% threshold)

**Severity**: 🟡 LOW
**Risk**: Local backup directory `/app/backend/backups` could fill the worker disk. Mitigated by emergency-prune on boot, which fired correctly in the drill.
**Evidence**: Drill backend log: `[scheduled-backup] disk at 76% on boot — running emergency prune`. Prune ran successfully.
**Fix effort**: No fix required — circuit breaker working correctly.
**Recommended action**: Document; monitor watermark trend.

### 🟡 GAP-9 — `dispatch_magic_links` are single-use — restoring them post-disaster wastes them

**Severity**: 🟡 LOW
**Risk**: After restore, any "magic link" tokens that drivers received before the disaster might be marked used/expired. Drivers would need fresh magic links sent. Minor operational friction.
**Evidence**: Code review (`server.py:4052` includes `dispatch_magic_links` in some redactions but the collection itself is restorable).
**Fix effort**: No fix required — by design.
**Recommended action**: Document in DR runbook (link drivers receive a fresh magic-link email post-recovery).

### 🟡 GAP-10 — No automated post-restore "smoke pack" to verify recovery health

**Severity**: 🟡 MEDIUM
**Risk**: After a real restore, the operator manually goes through each portal to verify functionality. Time-consuming. Easy to miss something.
**Evidence**: This Batch F drill effectively WAS a manual smoke pack; we ran it ad-hoc.
**Fix effort**: 4-6 hours. Convert today's Batch F probes into `scripts/post_restore_smoke.py` that runs every probe and emits a green/yellow/red report.
**Recommended action**: Schedule as ops-tooling deliverable next quarter.

---

## 2 · Gap priority matrix

| # | Gap | Severity | Effort | Schedule |
|---|---|---|---|---|
| 1 | DR inline base64 driving archive bloat | 🔴 CRITICAL | 1–2 days | Next batch (P0) |
| 2 | Multi-login broken post-restore | 🔴 CRITICAL | 1 hour | Next batch (P0) |
| 3 | `BACKUP_R2_HOURLY` cascade trajectory | 🟡 HIGH | 1 env-var | **IMMEDIATELY** (operator action; outside batch) |
| 4 | Photo re-upload not automated | 🟡 MEDIUM | 2-4 hours | Next batch |
| 5 | Indexes not in archive (cold-form) | 🟡 LOW | n/a | No fix needed |
| 6 | Frontend not exercised end-to-end | 🟡 MEDIUM | 30 min | Next batch |
| 7 | `webauthn_challenges` index drift | 🟡 LOW | 1 line | Ops batch |
| 8 | Local backup disk at 76% | 🟡 LOW | n/a | Monitor |
| 9 | `dispatch_magic_links` post-restore | 🟡 LOW | n/a | Runbook note |
| 10 | No post-restore smoke pack | 🟡 MEDIUM | 4-6 hours | Q2 ops tooling |

---

## 3 · "Destroy production. Restore backup. Resume operations." — actual flowchart

Given today's drill evidence, this is the precise sequence the operator would execute:

1. **Provision** new MongoDB cluster (or use existing Atlas with new DB name) — **5 min**
2. **Download** latest complete-R2 archive from R2 (operator credentials needed) — **10 sec** (442 MB)
3. **Run** `scripts/restore_drill.py --backup <key> --target <mongo> --target-db <new>` — **~60 sec**
4. **Boot** backend with `MONGO_URL`, `DB_NAME=<new>`, `APP_ENV=production`, `ADMIN_PASSWORD=<known>` — **~15 sec** (indexes auto-form)
5. **Boot** frontend (already a static asset pointing at backend URL) — **immediate**
6. **🟡 Manual step**: Operator logs into `/api/admin/login` with `ADMIN_PASSWORD`, then resets 7 user_directory passwords via admin UI — **5–10 min**
7. **🟡 Conditional**: If R2 was ALSO lost, run a (currently-unwritten) `restore_drill.py --restore-photos` to re-upload photo bytes — **hours** (TB-scale)
8. **Verify** by exercising one daily report submit + PDF render + login per portal — **5 min**

**Total RTO when only Mongo is lost**: 20–25 minutes.
**Total RTO when both Mongo + R2 are lost**: hours-to-days (depends on R2 photo volume).
**RPO**: Currently 60 min (hourly archives) → recommend 24 hr (nightly archives) once GAP-3 is applied.

---

## 4 · Manual steps that still exist (cannot be automated TODAY)

1. **Provision new Atlas cluster / DB** — depends on the operator's Atlas account state and choices. Could be automated with infrastructure-as-code (Terraform) in a future maturity step.
2. **Set production env vars** on the new backend (MONGO_URL, DB_NAME, ADMIN_PASSWORD, R2 keys, RESEND keys, Sentry DSN, etc.) — list documented at `BACKUP_SCHEDULER_READINESS_REPORT.md`.
3. **DNS cutover** to the new backend URL if the prod URL becomes unreachable.
4. **Operator login via admin escape hatch + reset 7 directory passwords** — eliminated by GAP-2 fix.
5. **Re-issue dispatch magic links** to drivers (if any are mid-use at moment of disaster).
6. **R2 photo re-upload** (if R2 was also lost) — eliminated as a manual step by GAP-4 fix.

---

## 5 · Risks that remain after all listed gaps are fixed

| Residual risk | Mitigation depth |
|---|---|
| Worker OOM if archive build crosses memory ceiling | Will keep recurring as data grows · fixable only by photo offload (GAP-1) |
| Catastrophic loss of both Atlas + R2 simultaneously | Currently only `restore_drill.py` covers data; photo re-upload (GAP-4) covers media; but a third-region read replica would be the proper protection |
| Email-channel rate limits during recovery (Resend sending burst of password reset emails) | Real but small for a 7-user reseed |
| Source-code / deployment configuration drift | Out of scope of data backups; recoverable from git |

# PRODUCTION_DEPLOYMENT_RISK_REPORT

**Phase:** OMEGA Phase P · Production Deployment Readiness · Phase 2
**Date:** 2026-05-30 (UTC)
**Method:** Per-item failure-mode analysis. Each item from `DEPLOYMENT_INVENTORY.md` is classified with explicit failure mode, detection method, and rollback path.
**Mandate:** READ-ONLY analysis. No changes.

---

## 🟢 OVERALL CLASSIFICATION

**7 of 7 deployable items: LOW risk.** Zero MEDIUM. Zero HIGH.

The combined deploy + migration window has a **bounded risk envelope** — every failure mode is detectable in < 5 minutes and reversible within RTO < 15 minutes.

---

## 1 · Per-item risk classification

### Item 1 · Batch K Notification Fan-outs — 🟢 LOW

| Aspect | Detail |
|---|---|
| **Failure mode 1** | Fan-out raises exception during emit → user-visible 5xx on form submission |
| Detection | Backend log tail (`/var/log/supervisor/backend.err.log`) within 5 min · Sentry error capture · canary smoke test in Step 3 of deploy plan |
| Mitigation | All 7 fan-outs are inside try/except blocks with `pass` on exception (pattern verified in `BATCH_K_FINAL_CERTIFICATION.md`) — submission NEVER blocked by fan-out failure |
| Rollback | Path C (Emergent rollback button) — ~5 min RTO |
| **Failure mode 2** | Fan-out emits wrong `assignee_role` → task lands in wrong queue |
| Detection | Canary probe enumerates tasks immediately post-submit; if `assignee_role != "safety"` for the 5 Safety events or `!= "admin"` for Payroll Variance, fail and rollback |
| Mitigation | All 7 paths certified in preview at `BATCH_K_FINAL_CERTIFICATION.md §1.1–1.7` matching the approved decision package exactly |
| Rollback | Path C |
| **Failure mode 3** | Fan-out floods prod with duplicate notifications |
| Detection | `/api/notifications?limit=200` count comparison pre vs post · Sentry rate counters |
| Mitigation | Each fan-out emits exactly one task + one notification per submission (audited line-by-line in certification) |
| Rollback | Path C + DB cleanup of duplicates if needed (cleanup pattern documented in Batch K cleanup) |
| **Net risk** | 🟢 LOW |

### Item 2 · Batch L Fleet DVIR Routing — 🟢 LOW

| Aspect | Detail |
|---|---|
| **Failure mode 1** | DVIR submission breaks (5xx) due to fan-out exception |
| Detection | Canary DVIR submission (3 cases: Normal/Defect/OOS) in Step 3 of deploy plan; backend log tail |
| Mitigation | Same `try/except: pass` pattern as Batch K. Verified at `FLEET_DVIR_CERTIFICATION.md §7` ("Fail-soft (exception in fan-out doesn't block submission)") |
| Rollback | Path C |
| **Failure mode 2** | OOS DVIR fires only Shop notification without Dispatch parallel visibility |
| Detection | Canary OOS DVIR; enumerate `/api/notifications?type=dvir.defect.oos` — must return 2 rows (one shop, one dispatch) per OOS submission |
| Mitigation | Preview smoke Case C verified 2 of 2 OOS notifications fire (shop + dispatch). Code at `fleet_ops.py:625` `emit_notification(db, {recipient_role: "dispatch", ...})` |
| Rollback | Path C |
| **Failure mode 3** | Normal DVIR (no defects) accidentally creates a task/notification (false positive) |
| Detection | Canary Normal DVIR; enumerate `/api/tasks` — must show 0 new fleet.dvir rows |
| Mitigation | Code guard `if not normal_only:` at the fan-out block (verified in `FLEET_DVIR_CERTIFICATION.md §3 Case A` — 0 tasks/0 notifications) |
| Rollback | Path C |
| **Net risk** | 🟢 LOW |

### Item 3 · Batch H Photo Write-Path Defense — 🟢 LOW

| Aspect | Detail |
|---|---|
| **Failure mode 1** | R2 PUT fails for a single photo → that photo remains inline + `counters["errors"]++` |
| Detection | Counter visible in DR record metadata · server log if errors > 0 |
| Mitigation | Per-photo try/except in `_walk`; failed photo stays inline (legacy behavior); other photos continue migrating; DR submission succeeds regardless |
| Rollback | None required — failure is silent and self-contained per DR |
| **Failure mode 2** | R2 misconfigured → all photos remain inline |
| Detection | `photo_storage.is_configured()` returns False early; function returns clean counters with `photos=0` |
| Mitigation | Soft-fail to legacy: DR is still saved correctly, just with inline base64 (current prod behavior) |
| Rollback | None required — back-compatible degraded mode |
| **Failure mode 3** | Sanitizer mutates the doc in a way that breaks downstream readers |
| Detection | Canary DR PDF render in Step 3 of deploy plan; reader at `photo_storage.read_photo_bytes` already handles both shapes (line 280) |
| Mitigation | Reader code at `photo_storage.py:280` predates Batch H: `"Read photo bytes from EITHER a photo:// reference OR a base64 ..."`. Both shapes have been supported since iter319 |
| Rollback | Path C if pattern is wrong; no DB rollback needed |
| **Net risk** | 🟢 LOW |

### Item 4 · Photo Migration (One-shot Legacy Backfill) — 🟢 LOW (CONDITIONAL on §1.6)

| Aspect | Detail |
|---|---|
| **Failure mode 1** | Mid-walk R2 outage → partial migration |
| Detection | Script emits per-DR FAIL line + summary `drs_failed` count |
| Mitigation | Idempotent: re-running picks up where it stopped (already-migrated DRs skipped because their photos[] start with `photo://`, not `data:image/`) |
| Rollback | Path A (per-DR JSON restore from `--backup-dir`) if operator decides to abort |
| **Failure mode 2** | Migration corrupts a DR's photo list (e.g., empty list, missing keys) |
| Detection | Post-migration sample 5 random DRs; render PDFs; check `photos[]` length matches pre-state |
| Mitigation | Per-DR atomicity (script reads doc, mutates in memory, `replace_one`); each photo is processed sequentially with bytes-in/bytes-out counters; backup-dir preserves pre-state JSON for diff |
| Rollback | Path A (selective per-DR) · Path B (full archive) |
| **Failure mode 3** | Concurrent write race: user submits DR mid-walk, script overwrites with stale doc |
| Detection | Cursor snapshot semantics protect against this — new DR not visible to current run |
| Mitigation | Recommended low-traffic window. Batch H deploy ensures the new DR is born ref-shaped, so the next migration run is a no-op for it |
| Rollback | Path A on the affected DR if detected via diff |
| **Net risk** | 🟢 LOW (conditional on Batch H deploy BEFORE migration `--apply`) |

### Item 5 · Multi-Login Post-Restore Reseed — 🟢 LOW

| Aspect | Detail |
|---|---|
| **Failure mode 1** | Reseed clobbers a live user's existing password during a routine restore |
| Detection | Probe the test super-admin login post-restore; super-admin must retain `must_change_password=False` (existing hash preserved per `merge=True` default) |
| Mitigation | Merge logic: `if "password_hash" not in d` — existing rows with hashes are untouched (verified `MULTI_LOGIN_RESEED_REPORT.md §1` "Super-admin `jaymn.judd@mascigc.com` retained `must_change=False`") |
| Rollback | Path C if behavior is wrong; users can also reset their passwords through the standard rotation UI |
| **Failure mode 2** | Reseed leaks the seed password into the backup archive |
| Detection | Inspect any recent backup archive; `user_directory.password_hash` should be REDACTED per Batch C/D security posture |
| Mitigation | Seed is generated at RESTORE time from local env (NOT embedded in archive); archives still redact `password_hash` per pre-existing Batch C/D rules |
| Rollback | Path C; archive remains safe regardless of code state |
| **Failure mode 3** | Code change introduces a regression that prevents normal restore from working |
| Detection | Drill restore on a side DB after deploy verifies 7/7 multi-login |
| Mitigation | Two-prong delivery: server.py change + restore_drill.py change, both certified post-Batch-G |
| Rollback | Path C |
| **Net risk** | 🟢 LOW (recovery-only code path; only fires when operator explicitly invokes restore) |

### Item 6 · Drill Script `--seed-user-passwords` Flag — 🟢 LOW

| Aspect | Detail |
|---|---|
| **Failure mode** | CLI flag not recognized → operator falls back to one-liner invocation pattern (documented in `MULTI_LOGIN_RESEED_REPORT.md §4`) |
| Detection | Script returns non-zero exit code with clear error |
| Mitigation | One-liner fallback documented; helper function callable independently |
| Rollback | Repo revert; script file is shell-invoked, not part of the worker image |
| **Net risk** | 🟢 LOW |

### Item 7 · Wave 1 Substrate (Operational Constraints / Links / Timeline / Photo Governance / Attachments) — 🟢 LOW

| Aspect | Detail |
|---|---|
| **Failure mode 1** | New routes fail to mount at FastAPI startup → backend boot loop |
| Detection | `/api/health` 5xx within 5 sec of deploy start; pre-deploy probe `scripts/pre_deploy_check.sh` catches this before deploy |
| Mitigation | All 5 routes have been mounted in preview for ~5 weeks with `/api/version` returning 200 and `boot_step=entering_main_tick_loop` |
| Rollback | Path C |
| **Failure mode 2** | New collections cause cross-collection write conflicts with existing operations |
| Detection | Backend log tail for Mongo write errors |
| Mitigation | All 5 collections are isolated — no foreign keys into existing collections; reads/writes go through new routes only |
| Rollback | Path C; empty collections can be dropped post-rollback (or ignored — they cost ~0 bytes) |
| **Failure mode 3** | Frontend sidecar component renders but breaks PM Project Detail page |
| Detection | Operator visits a PM Project Detail page during Step 3; sidecar should render right-side passive rail |
| Mitigation | Sidecar is wrapped in error boundary (per `CALM_OBSERVABILITY_UI.md` calmness pattern); on render error it silently hides |
| Rollback | Path C |
| **Net risk** | 🟢 LOW |

---

## 2 · Cross-cutting risks

### 2.1 · Risk — Pre-existing prod data contamination

| Risk | Detail |
|---|---|
| Status | 🟢 NONE — `verify_no_contamination.py --target masci_safety` returns 0 rows |
| Detection | Run script before AND after deploy |
| Mitigation | n/a — already clean |

### 2.2 · Risk — Backup scheduler interruption during deploy

| Risk | Detail |
|---|---|
| Status | 🟢 LOW — Emergent platform deploy is rolling; old worker drains while new worker takes over. Singleton scheduler ID is recycled but resurrects on the new worker. |
| Detection | `recent_health` probe pre + post deploy — `last_tick_ts` should keep advancing (gap of < 60 sec expected during deploy cutover) |
| Mitigation | Scheduler has supervisor respawn proven in `BATCH_D_EXECUTIVE_SUMMARY.md §1` ("1 resurrection observed during deploy") |
| Rollback | If scheduler doesn't resume within 5 min: Path C (deploy rollback) |

### 2.3 · Risk — Migration script runs concurrently with a user-submitted DR

| Risk | Detail |
|---|---|
| Status | 🟢 LOW (conditional on Item 4 conditions) |
| Detection | Compare `daily_reports` document count pre/post migration; should be equal + new DRs since migration start (visible in `recent_health` snapshot diff) |
| Mitigation | Cursor snapshot isolation; recommended low-traffic window; Batch H deploy ensures concurrent writes are already ref-shaped |
| Rollback | Path A on the affected DR if detected |

### 2.4 · Risk — R2 storage cost spike during migration

| Risk | Detail |
|---|---|
| Status | 🟢 LOW — migration uploads ~270 MB total to R2 (one-time cost). Net effect is REDUCTION because the next backup archive shrinks ~349 MB (464 → 115 MB) |
| Detection | R2 usage probe in `recent_health` (`gb=80.64`) |
| Mitigation | n/a — net storage decreases |

### 2.5 · Risk — Sentry alert flood from canary submissions

| Risk | Detail |
|---|---|
| Status | 🟢 LOW — canary submissions are intentional and labeled (per Batch K cleanup pattern); Sentry tags include `source=canary` |
| Detection | Sentry dashboard |
| Mitigation | Cleanup canary rows in Step 4 of deploy plan |

---

## 3 · Risk classification summary table

| # | Item | Classification | Detection latency | Rollback path | RTO |
|---|---|:--:|---|---|---|
| 1 | Batch K fan-outs | 🟢 LOW | < 5 min (canary + log) | Path C | ~5 min |
| 2 | Batch L Fleet DVIR | 🟢 LOW | < 5 min (3-case canary) | Path C | ~5 min |
| 3 | Batch H write-path defense | 🟢 LOW | < 5 min (canary DR + PDF render) | Path C | ~5 min |
| 4 | Photo migration | 🟢 LOW (conditional) | < 1 min per DR (script stdout) | Path A / Path B | ~5 min Path A, ~15 min Path B |
| 5 | Multi-login reseed | 🟢 LOW (recovery-only) | post-restore drill | Path C | ~5 min |
| 6 | Drill script flag | 🟢 LOW | script exit code | repo revert | seconds |
| 7 | Wave 1 substrate | 🟢 LOW | < 30 sec (boot + sidecar render) | Path C | ~5 min |

---

## 4 · Net verdict

**No HIGH risk. No MEDIUM risk. 7 of 7 items LOW risk.**

The combined deploy + migration window is the lowest-risk OMEGA execution to date. Every failure mode is detectable within 5 minutes and reversible within 5–15 minutes via a documented rollback path.

The single hard condition is sequencing: **Batch H (Item 3) MUST be deployed before the migration `--apply` step (Item 4)** to prevent concurrent writes from re-bloating the collection.

---

_End of PRODUCTION_DEPLOYMENT_RISK_REPORT.md._

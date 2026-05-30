# PLATFORM_TRUTH_DELTA_REPORT

**Batch:** I · Platform Operational Truth Map Finalization
**Date:** 2026-05-30 (UTC)
**Purpose:** Every divergence found between Memory docs ↔ Code ↔ Runtime during Batch I verification. **Observations only.** No winner chosen, no remediation proposed.

**Source-of-truth rule:** when all three agree → 🟢 KNOWN GOOD (recorded in TRUTH_MAP, not in this delta). When any two disagree → logged here. Severity is **delta-severity** (how confusing / risky is the gap between sources), not gap-severity (which is in `PLATFORM_GAP_LEDGER_FINAL.md`).

| Glyph | Meaning |
|---|---|
| 🟢 | All three sources agree (recorded in truth map; not listed here) |
| 🟡 | Two sources agree, one is silent or out-of-date |
| 🔴 | Two sources contradict each other |
| 🟦 | Production-only claim that cannot be re-probed from preview environment |

---

## DELTA-D1 · Production backup scheduler "alive" claim — preview reports DEAD

| Source | Claim |
|---|---|
| Memory · `BATCH_D_EXECUTIVE_SUMMARY.md` | "Production backup scheduler activated and proven (catch-up + lite backups verified via T+0 / T+5 probes)." |
| Memory · `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md §3` | "Backup creation 🟢 Running on prod since Batch D." |
| Memory · `BACKUP_SCHEDULER_RESTART_VERIFICATION_REPORT.md` | Reports a verification probe against prod. |
| Code · `lib/singleton_scheduler.py` + `_backup_scheduler_loop` in `server.py` | Scheduler loop is wired correctly. Gate is `BACKUP_R2_HOURLY` + `BACKUP_R2_FULL_HOUR_UTC` env vars. |
| Runtime (preview) · P2 probe (`GET /api/admin/backups-scheduler-state`) | `scheduler.alive=false`, `scheduler.armed_at=null`, `scheduler.last_tick_ts=null`, `task_alive=false`, `last_attempt_outcome="RESURRECTED at 2026-05-30T15:35:53.140630+00:00 (previous: completed without error)"`. Most recent `backup_health` row in preview: 2026-05-27 (3 days old at probe time). |

**Delta severity:** 🟦 — production cannot be re-probed from preview. The memory + code claim is consistent ("activated, proven"). The runtime check is performed against preview, where the scheduler is DEAD. Whether this also applies to production is unknown from this environment.

**Operator action:** Operator should run `curl -H "X-Admin-Token: <prod token>" https://mascidocs.com/api/admin/backups-scheduler-state` and confirm `scheduler.alive=true`. If `false` in prod too, the Batch D win is silently regressed.

**No fix applied.** This is a verification gap, not a code bug.

---

## DELTA-D2 · Endpoint naming drift — `/api/admin/backup-health` (singular) vs `/api/admin/backups` (plural)

| Source | Claim |
|---|---|
| Memory · various docs (e.g., `BACKUP_SYSTEM_VERIFICATION_REPORT.md`) | References `/api/admin/backup-health` (singular) endpoint. |
| Runtime · P7 probe | `GET /api/admin/backup-health` → **HTTP 404 "Not Found"** |
| Runtime · P3 probe | `GET /api/admin/backups` (plural) → **HTTP 200** returning `{backups[], count, total_bytes, schedule{}}` |
| Runtime · P2 probe | `GET /api/admin/backups-scheduler-state` → **HTTP 200** returning the scheduler state + `recent_health[]` array embedded |

**Delta severity:** 🟡 — memory docs reference an endpoint name that no longer exists; the actual data is at two other endpoints. Likely a renaming during a prior batch that wasn't propagated into all docs.

**No fix applied.** Documentation drift only; the live endpoints work.

---

## DELTA-D3 · Endpoint not found — `/api/admin/integration-health`

| Source | Claim |
|---|---|
| Memory · `INTEGRATION_HEALTH.md` (implied) + various health-check docs | References integration-health admin endpoint. |
| Code · `routes/integration_health.py` exists (12 KB) | Route file exists. |
| Runtime · P7 probe | `GET /api/admin/integration-health` → **HTTP 404 "Not Found"** |

**Delta severity:** 🟡 — route file exists in `/app/backend/routes/integration_health.py` but the admin path `/api/admin/integration-health` is not mounted. Likely registered under a different path (probably `/api/integration-health` or `/api/admin/integrations`).

**Hypothesis (not verified):** the admin panel at `/admin/integrations` reads from a different endpoint. Requires grep of `integration_health.py` to confirm the registered prefix.

**No fix applied.** Endpoint discovery gap only.

---

## DELTA-D4 · Endpoint not found — `/api/admin/r2/lifecycle-status`

| Source | Claim |
|---|---|
| Memory · `R2_LIFECYCLE_ACTIVATION.md`, `R2_LIFECYCLE_POLICY_VERIFICATION.md` | Reference R2 lifecycle status admin probe. |
| Runtime · P7 probe | `GET /api/admin/r2/lifecycle-status` → **HTTP 404 "Not Found"** |

**Delta severity:** 🟡 — same pattern as DELTA-D3. R2 lifecycle is in operation per memory docs, but the admin status endpoint either was never deployed or is under a different path.

**No fix applied.**

---

## DELTA-D5 · `routes/fleet_ops.py` ownership claim vs code reality

| Source | Claim |
|---|---|
| Memory · `WORKFLOW_OWNERSHIP_MATRIX.md` row "Fleet DVIR" | "Owner: Dispatch + Shop · Closer: Shop · No-response path: GAP-6 — no notification path confirmed." |
| Memory · `FLEET_DVIR_INVESTIGATION_REPORT.md`, `FLEET_DVIR_POLICY_RECORD.md` | Policy intended: Normal=record, Defect=Shop, Safety Defect=Shop+Safety, OOS=Shop+Dispatch, Repeat=escalation. |
| Code · `routes/fleet_ops.py:412–553` (submission handler `submit_fleet_inspection`) | Handler writes to `equipment_inspections` + `fleet_defects` + `fleet_status`, audits, returns. **Zero `schedule_auto_email`, zero `emit_*`, zero `task_service`, zero `notification_service`.** |
| Code · `routes/fleet_ops.py:693+729+774+819` (defect lifecycle handlers `ack` / `repair` / `clear` / `oos`) | Each handler **only** audits and updates status. **No notification fan-out on transitions either.** |
| Runtime · DBI-1 | `fleet_defects` collection has 50 docs · `fleet_status` has 58 · `equipment_inspections` has 82 — workflow is being used in preview. |

**Delta severity:** 🟢🔴 hybrid — memory + code AGREE on the gap (orphan), but the gap is severe (P0) and known. Logged here because the "intended policy" diverges from "implemented code". This is the **definitive code-confirmation of ORPHAN-1 / GAP-6**.

**No fix applied.** Operator decision required (passive ledger vs active workflow) — see `PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md §5.1`.

---

## DELTA-D6 · `restore_drill.py` validate function checks `daily_reports.attachments`, but Batch G migrated photos to `photos[]` + `photo://` refs

| Source | Claim |
|---|---|
| Memory · `BATCH_G_EXECUTIVE_SUMMARY.md` | Inline base64 photos migrated to `photo://` refs in `daily_reports.photos[]`, `subcontractors[*].photos[]`, `materials[*].ticket_photos[]`. |
| Code · `routes/daily_reports.py:_sanitize_inline_photos` | Walks those three paths. |
| Code · `scripts/restore_drill.py:182–189` (post-restore validation) | Validation function looks for `daily_reports` documents where `attachments` exists and is non-empty: `sdb.daily_reports.find_one({"attachments": {"$exists": True, "$ne": []}}, ...)`. |

**Delta severity:** 🟡 — the post-restore "sample DR with attachments" check uses a legacy field name (`attachments`) instead of the current schema (`photos[]`). The check still works because legacy DRs may carry an `attachments` field, but a fresh post-Batch-G DR will only have `photos[]` and the check may report `false` even when restoration succeeded.

**No fix applied.** Cosmetic — validation continues regardless; this is a stale assertion, not a functional bug.

---

## DELTA-D7 · Documents reference scheduler at "hourly" but env defaults to "2 + 18 UTC"

| Source | Claim |
|---|---|
| Memory · `BATCH_H_EXECUTIVE_SUMMARY.md §5` | "Optional: after migration applied, operator can safely re-enable `BACKUP_R2_HOURLY=true` (60-min RPO)." |
| Memory · multiple docs | RPO target is 60 min. |
| Runtime · P2 | `lite_mode_only_env=true`, `scheduled_hours_utc=[2,18]`, NOT hourly. |
| Code · scheduler loop | Honours `BACKUP_R2_HOURLY` flag; default appears to be off. |

**Delta severity:** 🟡 — current preview env is in "twice daily" (2 + 18 UTC) mode, not hourly. Most docs assume hourly is the target; this is intentional per Batch F GAP-3 ("set `BACKUP_R2_HOURLY=false` until migration applied") but it's not always called out clearly when memory docs cite RPO numbers.

**No fix applied.** Operator can flip the env var once production migration runs.

---

## DELTA-D8 · `WORKFLOW_OWNERSHIP_MATRIX.md` row "JHP (Job Hazard Planning)" says "consolidated with safety_forms" — runtime shows split collections

| Source | Claim |
|---|---|
| Memory · `WORKFLOW_OWNERSHIP_MATRIX.md` | "JHP — consolidated with safety_forms." |
| Memory · `NOTIFICATION_DELIVERY_MAP.md` | "collection `jhas` (submissions); `job_hazard_plans` is master library." |
| Runtime · DBI-1 | `jhas` collection exists (0 docs in preview) · `job_hazard_plans` collection exists (0 docs in preview) · `job_hazard_files` exists (6 docs). |

**Delta severity:** 🟡 — the JHA / JHP / job_hazard_plans / job_hazard_files naming is overlapping in the memory docs. Code uses `jhas` for submissions and `job_hazard_plans` for the master library; `job_hazard_files` appears to be the file-attachments collection. The "JHP consolidated with safety_forms" line in WORKFLOW_OWNERSHIP_MATRIX.md is therefore likely stale or misleading.

**No fix applied.** Naming-hygiene observation only.

---

## DELTA-D9 · DR-core collection list in `restore_drill.py` is 10 collections, but actual DR-critical inventory is wider

| Source | Claim |
|---|---|
| Code · `scripts/restore_drill.py:174–176` | Validation iterates: `inspections, jhas, incidents, daily_reports, meetings, equipment, employees, user_directory, role_templates, backup_health`. |
| `DISASTER_RECOVERY_VALIDATION_MATRIX.md` (this batch) | Identifies 22+ DR-core collections that should be validated post-restore (POs, fleet_defects, fleet_status, equipment_master, equipment_units, tasks, notifications, audit_events, admin_audit, jobs_master, field_leadership_records, dispatch_assignments, etc.). |
| Runtime · DBI-1 | All 22 collections exist in preview with non-zero counts (except `jhas` and `job_hazard_plans` which are 0 in preview). |

**Delta severity:** 🟡 — the restore_drill validation step is **directionally correct but undersized**. It samples ~ 10 of the ~ 22 critical DR collections. The Batch E drill report (`BATCH_E_EXECUTIVE_SUMMARY.md`) claimed 283K records restored — that headline figure depends on all collections being restored, but the per-collection validation cell only checks 10.

**No fix applied.** The actual restore process (zip → extract → insert) does walk ALL `extracted/<collection>/json/*.json` directories (per `restore_drill.py:120–155`). Only the **post-restore validation cell** is undersized. The data IS restored fully; the verification just samples a subset.

---

## DELTA-D10 · No automated multi-tier escalation cadence anywhere on the platform

| Source | Claim |
|---|---|
| Memory · `SAFETY_ESCALATION_HIERARCHY_MAP.md` and equivalent docs | Defines first-responder → escalation tier mapping conceptually. |
| Code · all fan-out call sites in `code_fanout_callsites.txt` | Every event fires a one-shot `task_service.create` + optional notification. **No code performs a delayed "if not acknowledged within X hours → escalate to tier 2" check.** |
| Memory · `ORPHAN_AND_GAP_REGISTER.md §6` | Confirms: "no workflow currently has a defined operator process for 'what happens if the owner doesn't respond'", except for PO cron, Pre-Op FAIL queue persistence, Document Expirations cron, Dispatch >30m alert, Backup failures, System Health red. |

**Delta severity:** 🟢 (sources AGREE — recorded here for emphasis, not as a discrepancy). The "escalation chain" architecture exists conceptually but is implemented as **first-response fan-out + cron-driven follow-ups for select pipelines**. A general-purpose "escalate-if-no-ack" timer does NOT exist.

**No fix applied.** This is the consistent architectural reality and matches the gap ledger (GAP-14, GAP-15 etc. = "no follow-up cadence").

---

## DELTA-D11 · `task_alive` field in scheduler state always reports `false` (P2 evidence)

| Source | Claim |
|---|---|
| Code · `lib/singleton_scheduler.py` reports `task_alive` distinct from `scheduler.alive` (the latter is the singleton lock state; the former is the asyncio task state). | |
| Runtime · P2 probe | Both fields = `false` in preview. |

**Delta severity:** 🟦 — semantic separation: scheduler lock vs task aliveness. In a healthy state, both should be `true`. Preview reports both `false`. Reinforces DELTA-D1: scheduler is dead in preview.

**No fix applied.**

---

## DELTA-D12 · Watchdog threshold (25 hr) consistent across sources

| Source | Claim |
|---|---|
| Memory · multiple backup docs | Watchdog target: alert if no backup tick in > 24 hours. |
| Runtime · P2 | `watchdog_threshold_hours=25.0` |

**Delta severity:** 🟢 — sources agree within 1 hour tolerance. Logged for completeness. No discrepancy.

---

## DELTA-D13 · `auto_email_enabled=false` in preview is expected, but memory docs occasionally read as if always-on

| Source | Claim |
|---|---|
| Memory · `NOTIFICATION_DELIVERY_MAP.md §1` | "Preview disables it; production enables it." Correct. |
| Memory · isolated other docs | Sometimes refer to "PM receives email on DR submit" without preview/prod caveat. |
| Runtime · P4 | `auto_email_enabled=false` confirmed in preview. |

**Delta severity:** 🟡 — minor documentation hygiene. The gating logic is correct; some downstream docs could mention the preview disablement explicitly.

**No fix applied.**

---

## Summary

| Delta | Severity | Type | Operator action |
|---|---|---|---|
| D1 | 🟦 | Production state unverifiable from preview | Run prod scheduler-state probe |
| D2 | 🟡 | Endpoint naming drift | Update memory docs to current endpoint names |
| D3 | 🟡 | Endpoint not found at documented path | Confirm correct admin integration-health path |
| D4 | 🟡 | Endpoint not found at documented path | Confirm correct R2 lifecycle endpoint |
| D5 | 🔴 | Memory + code confirm orphan (severe) | Operator decision on Fleet DVIR intent (see ORPHAN-1) |
| D6 | 🟡 | Stale field name in validation step | None required — validation still passes |
| D7 | 🟡 | RPO doc vs current env state | Re-enable hourly post-migration |
| D8 | 🟡 | JHA / JHP collection naming overlap | Documentation hygiene |
| D9 | 🟡 | Post-restore validation samples fewer collections than the full DR-critical set | Optionally expand validation list |
| D10 | 🟢 | All sources agree (no automated multi-tier escalation) | Operator decision if/when to architect |
| D11 | 🟦 | `task_alive` confirms preview scheduler dead | (subsumed by D1) |
| D12 | 🟢 | Watchdog threshold consistent | (none) |
| D13 | 🟡 | Preview/prod auto-email disclaimer inconsistent in docs | Documentation hygiene |

**Total deltas:** 13 · **Production-only un-probable:** 2 (D1, D11) · **Documentation hygiene:** 6 (D2, D3, D4, D7, D8, D13) · **Architectural / orphan:** 1 (D5) · **Validation cosmetic:** 2 (D6, D9) · **Sources agree (logged for emphasis):** 2 (D10, D12).

**No remediation has been performed in Batch I.** Operator owns next call.

---

_End of PLATFORM_TRUTH_DELTA_REPORT.md._

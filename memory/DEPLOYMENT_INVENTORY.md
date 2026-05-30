# DEPLOYMENT_INVENTORY

**Phase:** OMEGA Phase P · Production Deployment Readiness · Phase 1
**Date:** 2026-05-30 (UTC)
**Method:** Direct grep of preview backend against route file LOC, cross-referenced with operator-authorized batch certifications and live `/api/version` source_hash delta.
**Mandate:** READ-ONLY enumeration. No changes.

**Identity anchors (current):**
- Preview `/api/version.source_hash`: `550118913c503ae6d206223be384372f`
- Production `/api/version.source_hash`: `8e8ec6da31cf225cae2db172573f49a0`
- Both `/api/health` 200 OK at audit time
- Backup scheduler ALREADY ACTIVE on production (since 2026-05-30T13:21Z per `BATCH_D_EXECUTIVE_SUMMARY.md`)

---

## 1 · Inventory of certified changes NOT YET running in production

### Item 1 · Batch K — Notification fan-out for 5 silent workflows (7 events)

| Aspect | Detail |
|---|---|
| **Feature** | Surface 7 previously email-only workflows as bell notifications + tasks in the Safety/Admin queues |
| **Files** | `backend/routes/safety.py` (lines 467–479 Meeting; 556–660 JHA) · `backend/routes/safety_forms.py` (944–973 Issuance; 1099–1103 Return; 1159–1170 Training) · `backend/routes/field_leadership.py` (463–471) · `backend/routes/payroll_variance.py` (338–340) |
| **Mechanism** | `lib.event_fanout.emit_task_and_notification` + `emit_notification` (substrate already on prod — used by existing PO + Incident routes) |
| **DB impact** | Additive rows in `tasks` and `notifications` only. No schema mutation. No existing column changes. |
| **Risk** | LOW — pattern is byte-identical to existing Pre-Op FAIL fan-out at `equipment.py:234` already running in prod. Fan-out is `try/except`-wrapped — exception never blocks the submit |
| **Rollback method** | Path C (Emergent platform "Rollback to previous deploy" button → ~5 min RTO). Code-level rollback only — no DB rollback needed (any tasks/notifications already emitted survive as legitimate audit rows) |
| **Dependencies** | `lib.event_fanout` (already deployed) · `tasks` collection (already deployed) · `notifications` collection (already deployed) |
| **Verification** | Submit canary records (1 per workflow); enumerate `/api/tasks?source_module=safety.meeting` etc.; confirm rows appear. Cleanup canary rows after verification. Certified end-to-end in `BATCH_K_FINAL_CERTIFICATION.md` (7-workflow × 10-question audit, all PASS) |

### Item 2 · Batch L — Fleet DVIR ownership matrix (OMEGA-3 / ORPHAN-1 closure)

| Aspect | Detail |
|---|---|
| **Feature** | Wire `routes/fleet_ops.py:submit_fleet_inspection` to emit task + notification per DVIR class: Normal=record-only, Defect (monitor)=Shop Medium, OOS=Shop Critical + Dispatch visibility |
| **Files** | `backend/routes/fleet_ops.py` lines 569–625 (~95 LOC added) |
| **Mechanism** | Same `emit_task_and_notification` / `emit_notification` substrate as Batch K |
| **DB impact** | Additive rows in `tasks` + `notifications`. Existing collections `equipment_inspections`, `fleet_defects`, `fleet_status`, `fleet_audit` unchanged. |
| **Risk** | LOW — 3 routing classes verified live in preview (`FLEET_DVIR_CERTIFICATION.md §3`). DB returned to baseline post-smoke. NO Superintendent routing (per decision package §3 explicit exclusion). |
| **Rollback method** | Path C (deploy rollback). Code-level only. |
| **Dependencies** | `fleet_defect_severity.SEVERITY_TABLE_VERSION = "v1.3-approved-2026-05-19"` (unchanged, already in prod) |
| **Verification** | Submit canary inspections at each severity class; enumerate `/api/tasks?source_module=fleet.dvir`; confirm `dvir.defect` / `dvir.defect.oos` notifications appear with correct `assignee_role=shop` and Dispatch parallel notification on OOS |

### Item 3 · Batch H — Daily Report photo write-path defense (`_sanitize_inline_photos`)

| Aspect | Detail |
|---|---|
| **Feature** | On every DR POST, walk `photos[]`, `subcontractors[*].photos[]`, `materials[*].ticket_photos[]` and convert inline `data:image/...` base64 → `photo://` ref BEFORE persist |
| **Files** | `backend/routes/daily_reports.py` lines 186–232 (function), 254–257 (invocation) |
| **Mechanism** | `photo_storage.upload_data_url` (R2 client already on prod — used by post-iter319 photo writes); idempotent (skips existing `photo://` refs); soft-fails to legacy inline behavior if R2 misconfigured |
| **DB impact** | Future DRs land with `photo://` refs in place of inline base64. Old DRs are not touched by this code path (handled by Item 4 below) |
| **Risk** | LOW — function is invoked inside an existing try-wrapped block; exception path is silent (returns counters with `errors > 0`); on R2 misconfig the legacy inline behavior is preserved (no user-facing breakage) |
| **Rollback method** | Path C (deploy rollback). No DB rollback needed (any DRs created with refs continue to render via `photo_storage.read_photo_bytes` which tolerates both shapes) |
| **Dependencies** | `photo_storage.upload_data_url` (existing) · `photo_storage.is_configured` gate (existing) · R2 credentials (existing) |
| **Verification** | Submit canary DR with 1 inline base64 photo; confirm stored `photos[0]` starts with `photo://`; confirm rendered DR PDF works |

### Item 4 · Photo migration tooling — One-shot legacy backfill

| Aspect | Detail |
|---|---|
| **Feature** | Convert all 86 existing prod `daily_reports` from inline base64 → `photo://` refs via a CLI script |
| **Files** | `/app/scripts/migrate_dr_photos.py` (230 LOC) — repo-checked, exists on both sides |
| **Mechanism** | Out-of-process CLI (NOT a route, NOT in worker memory); per-DR atomic; idempotent; dry-run default; refuses prod without `--i-know-this-is-prod` |
| **DB impact** | Mutates `daily_reports.photos[]`, `daily_reports.subcontractors[*].photos[]`, `daily_reports.materials[*].ticket_photos[]` for ~86 prod DRs. ~270 MB inline data → ~50 KB ref data |
| **Risk** | LOW — 6 of 6 safety gates pass (`PHOTO_MIGRATION_VALIDATION.md`). Three layered rollback paths armed |
| **Rollback method** | Path A (per-DR JSON restore from `--backup-dir`) · Path B (full archive restore) · R2 objects survive both. ~5 min for Path A |
| **Dependencies** | Item 3 (Batch H) MUST be deployed first so concurrent + post-migration writes don't re-bloat. Item 5 (multi-login reseed) is independent. |
| **Verification** | Re-run dry-run after `--apply` → expect `Photos to migrate: 0`. Sample 5 random DRs and render their PDFs. Verify next backup archive size drops from 464 MB → ~115 MB |

### Item 5 · Multi-login post-restore password reseed (GAP-2 closure)

| Aspect | Detail |
|---|---|
| **Feature** | After a `POST /api/exports/restore` or `restore_drill.py` run, all 7 master-directory users can log in immediately with seed password `Welcome2MASCI!` and are forced to rotate on first login |
| **Files** | `backend/server.py` lines 7592–7635 (inside `exports_restore`) — extended single-collection check to two-collection tuple `("users", "user_directory")` · `scripts/restore_drill.py` adds new helper `_seed_user_password_hashes()` + `--seed-user-passwords` CLI flag |
| **Mechanism** | bcrypt-seeded `Welcome2MASCI!` + `must_change_password=True` for any row lacking `password_hash`. In `merge=True` mode, preserves any existing hash (won't clobber live credentials) |
| **DB impact** | NONE in normal operations. Only triggered by the restore endpoint or the drill helper. |
| **Risk** | LOW — recovery-only code path. Default `merge=True` preserves existing hashes. Seed `must_change_password=True` forces rotation. Drill verified 7/7 users authenticated post-reseed |
| **Rollback method** | Path C (deploy rollback). No DB rollback needed (the code never runs unless someone explicitly invokes restore) |
| **Dependencies** | Existing `users` + `user_directory` collections · bcrypt (existing) · `password_hash` field convention (existing) |
| **Verification** | Run drill restore on a side DB; confirm 7/7 multi-login probes return `OK portals=...`. Already certified live in `MULTI_LOGIN_RESEED_REPORT.md §1` |

### Item 6 · Recoverability — drill script `--seed-user-passwords` flag

| Aspect | Detail |
|---|---|
| **Feature** | Adds `--seed-user-passwords` CLI flag to `scripts/restore_drill.py` |
| **Files** | `scripts/restore_drill.py` (single file) |
| **Mechanism** | Companion to Item 5 — same `_seed_user_password_hashes()` helper, callable from CLI without invoking the restore endpoint |
| **DB impact** | NONE in normal operations |
| **Risk** | LOW — drill-only path |
| **Rollback method** | Repo revert (script files are not in the worker image; they're invoked from operator shell) |
| **Dependencies** | Item 5 |
| **Verification** | `python3 scripts/restore_drill.py --backup ... --seed-user-passwords` returns `seeded=N` counter |

### Item 7 · Wave 1 substrate — Operational Constraints / Links / Timeline / Photo Governance / Attachments

| Aspect | Detail |
|---|---|
| **Feature** | 5 new route modules + 5 new MongoDB collections + 1 new frontend sidecar component (passive read-only timeline rail on PM Project Detail) |
| **Files** | `backend/routes/operational_constraints.py`, `backend/routes/operational_links.py`, `backend/routes/operational_timeline.py`, `backend/routes/photo_governance.py`, `backend/routes/operational_attachments.py` · `frontend/src/components/operational/OperationalTimelineSidecar.jsx` · mount in `frontend/src/pages/PmProjectDetail.jsx` |
| **Mechanism** | New `/api/operational/*` endpoints. Frontend sidecar renders chronology of operational events. Passive read-only. |
| **DB impact** | 5 new collections (`operational_constraints`, `operational_links`, `operational_timeline`, `photo_governance`, `operational_attachments`) — all empty on prod at deploy time |
| **Risk** | LOW — additive only. No existing routes touched. Frontend mount is passive. |
| **Rollback method** | Path C (deploy rollback). Empty collections on prod can be ignored or dropped post-rollback. |
| **Dependencies** | Pre-deploy probe gates: `operational_links_doctrine_probe.py`, `trendline_integrity_probe.py`, `timestamp_doctrine_probe.py` (all already wired in `scripts/pre_deploy_check.sh`) |
| **Verification** | Confirm `/api/operational/timeline/...` returns 200; confirm sidecar renders on PM Project Detail; confirm no collections-leak warnings in startup log |

### Item 8 · Scheduler improvements — ALREADY IN PRODUCTION (no action)

| Aspect | Detail |
|---|---|
| **Feature** | Scheduler `_backup_scheduler_loop_with_capture` defensive wrapper, OOM watermark (600 MB), circuit breaker (3 fails/day), watchdog (25 hr silence alarm), supervisor respawn |
| **Files** | `backend/server.py` (pre-Batch-K LOC range — predates current preview hash) |
| **Status** | 🟢 **ALREADY IN PRODUCTION.** Scheduler activated 2026-05-30T13:21Z. Probe verified at 17:53Z: `scheduler.alive=true`, `last_tick_ts=43s before probe`, `failed_attempts={}`, `boot_step=entering_main_tick_loop`. See `PRODUCTION_RECOVERABILITY_REPORT.md §1`. |
| **Action required for this deploy** | NONE — included in inventory for completeness only |

---

## 2 · Items NOT in this deployment (out of scope per operator directive)

| Item | Status |
|---|---|
| Batch M (Training supervisor accountability) | ❌ NOT STARTED — operator forbade |
| Batch N (Escalation cadence framework) | ❌ NOT STARTED — operator forbade |
| Batch O (Documentation hygiene + version endpoint) | ❌ NOT STARTED — operator forbade |
| OMEGA-19 / OMEGA-20 heavy-form redesigns | ❌ NOT STARTED — operator forbade |
| Approval/Rejection · Pilot · RFI · Schedule · P6 · PM Exposure Tile | ❌ FUTURE — operator forbade |

---

## 3 · Deployment surface summary

| Surface | Change count | Net effect |
|---|---:|---|
| Backend route files modified | **5** (`safety.py`, `safety_forms.py`, `field_leadership.py`, `payroll_variance.py`, `fleet_ops.py`) | Add fan-out for 7 events + DVIR matrix |
| Backend route files added | **5** (Wave 1 substrate) | New `/api/operational/*` namespace |
| Backend write-path defense added | **1** (`daily_reports.py`) | Batch H — future DRs always ref-shaped |
| Backend server.py modified | **1** (`exports_restore` extended) | Multi-login post-restore reseed |
| Frontend files added | **1** (timeline sidecar component) | Passive read-only rail |
| Frontend files modified | **1** (`PmProjectDetail.jsx` mount) | One new mount point |
| New MongoDB collections | **5** (operational substrates) | All empty on prod at deploy |
| New API endpoints | **~15** under `/api/operational/*` | All additive |
| Existing API contract changes | **0** | Backwards-compatible |
| Schema mutations on existing collections | **0** | Additive only |
| Env var changes required | **0** | Operator confirmed |
| Dependency changes (`requirements.txt`, `package.json`) | **TBD — should be verified at Step 0 of deploy** | Should be unchanged but operator should diff |

---

## 4 · Net inventory verdict

**8 inventory items.** 7 require deploy action (Items 1–7). 1 is already in prod (Item 8 scheduler). All risks classified LOW. All rollback paths armed. Zero existing-contract changes. Zero schema mutations. Zero env var changes.

This is the smallest production-ready delta the operator has seen since Wave 1 began.

---

_End of DEPLOYMENT_INVENTORY.md._

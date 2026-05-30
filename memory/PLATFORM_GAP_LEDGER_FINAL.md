# PLATFORM_GAP_LEDGER_FINAL

**Batch:** I · Platform Operational Truth Map Finalization
**Date:** 2026-05-30 (UTC)
**Status:** Final deduplicated, severity-ranked, evidence-backed gap ledger. **Supersedes** `ORPHAN_AND_GAP_REGISTER.md` (2026-02-01) and `NOTIFICATION_GAP_REGISTER.md` (2026-05-29). No remediation.

**Sources reconciled (12):**
- `ORPHAN_AND_GAP_REGISTER.md`
- `ORPHAN_WORKFLOW_REPORT.md`
- `NOTIFICATION_GAP_REGISTER.md`
- `WORKFLOW_FAILURES_AND_DEAD_ENDS.md`
- `WORKFLOW_OWNERSHIP_MATRIX.md`
- `NOTIFICATION_DELIVERY_MAP.md`
- `DASHBOARD_DESTINATION_MAP.md`
- `SAFETY_ESCALATION_HIERARCHY_MAP.md`
- `CROSS_PORTAL_OPERATIONAL_GAPS.md` / `REMAINING_OPERATIONAL_GAPS.md` / `REMAINING_HIGH_VALUE_FIXES.md`
- Batch A, B, C, D, E, F, G, H executive summaries
- `PLATFORM_TRUTH_DELTA_REPORT.md` (this batch)
- `PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md` (this batch)

**Severity rubric (operator-defined):**
- **P0** — Workflow can disappear · no owner · no destination · no notification · operational risk OR broken system component
- **P1** — Workflow works but visibility unclear / dead-button / cross-portal bounce
- **P2** — Workflow works but could improve / no-response cadence missing / stop-list intentional
- **P3** — Test-only / cosmetic / not user-facing

---

## §1 · P0 — Orphan or broken (2 items)

### G-P0-01 · Fleet DVIR — orphan (no notification path · no dashboard surface)
- **Was:** ORPHAN-1, GAP-6
- **Workflow:** Fleet DVIR / Weekly Lead / Weekly Emergency
- **Pillars failing:** notification path · dashboard destination · next-step owner (partially)
- **Memory evidence:** `ORPHAN_AND_GAP_REGISTER.md §1`, `ORPHAN_WORKFLOW_REPORT.md §1`, `FLEET_DVIR_INVESTIGATION_REPORT.md`, `FLEET_DVIR_POLICY_RECORD.md`
- **Code evidence:** `routes/fleet_ops.py:412–553` — submit handler audits + rebuilds status but emits zero notification/task; defect lifecycle handlers (`acknowledge` line 693, `repair` line 729, `clear` line 774, `oos` line 819) also audit-only
- **Runtime evidence:** `fleet_defects=50` rows in preview DB, `fleet_status=58`, `equipment_inspections=82` — workflow is being USED but operator never told
- **Operator decision required:** Is Fleet DVIR a passive ledger or active workflow? Policy from `FLEET_DVIR_POLICY_RECORD.md`: Normal=record, Defect=Shop, Safety Defect=Shop+Safety, OOS=Shop+Dispatch, Repeat=escalation.
- **If active:** wire `emit_task_and_notification(...)` + `emit_notification(...)` in `submit_fleet_inspection` and the defect-lifecycle handlers · add Open-DVIRs tile on Shop and Dispatch hubs.

### G-P0-02 · Backup scheduler dead (preview verified · production not re-probed)
- **Was:** GAP-7
- **Workflow:** Backup pipeline (Atlas dump + R2 push + drift check + Backup Health write)
- **Memory evidence:** `BATCH_D_EXECUTIVE_SUMMARY.md` (claimed fixed), `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md §3` ("Running on prod since Batch D")
- **Code evidence:** `lib/singleton_scheduler.py`, `_backup_scheduler_loop` in `server.py` — loop is wired correctly; gated by `BACKUP_R2_HOURLY` / `BACKUP_R2_FULL_HOUR_UTC` env
- **Runtime evidence (preview):** P2 probe — `scheduler.alive=false`, `armed_at=null`, `last_tick_ts=null`, `task_alive=false`, `last_attempt_outcome="RESURRECTED at 2026-05-30T15:35:53..."`. Most recent `backup_health` row: 2026-05-27 (3 days stale at probe time)
- **Production status:** unverifiable from preview environment (DELTA-D1)
- **Operator action:** run `curl -H "X-Admin-Token: <prod token>" $PROD_URL/api/admin/backups-scheduler-state` against production base URL; if also dead, re-arm scheduler

---

## §2 · P1 — Visibility / cross-portal gaps (8 items)

### G-P1-01 · Field Leadership 10 forms — email only, no bell/task fan-out
- **Was:** GAP-1, SOFT-1
- **Symptom:** submission emails `leadership_always_to` (safety@ + admin); no `task.assigned` notification; surface is search-only on FL portal + admin + HR + PM
- **Code:** `routes/field_leadership.py` + `routes/field_leadership_portal.py` — no `emit_task_and_notification` calls
- **Closure shape:** insert `emit_task_and_notification` post-submit; add "Open FL Forms" action queue on Safety hub + Admin hub

### G-P1-02 · Safety Equipment Issuance / Training / Return — email only
- **Was:** GAP-2, SOFT-2
- **Symptom:** emails `SAFETY_FORMS_EMAIL_TO`; Safety Hub shows only count card, not actionable queue
- **Code:** `routes/safety_forms.py`
- **Closure shape:** add `emit_task_and_notification` to safety role; promote count card to action queue

### G-P1-03 · JHA submit — email only, no task to Safety supervisor
- **Was:** GAP-3, SOFT-3
- **Symptom:** `schedule_auto_email("jha", doc)` fires (`routes/safety.py:518`); no `emit_task_and_notification`
- **Closure shape:** identical to G-P1-02 pattern

### G-P1-04 · Safety Meeting submit — email only (newly identified 2026-02-01)
- **Was:** NEW-GAP-A, SOFT-3b
- **Symptom:** `schedule_auto_email("meeting", doc)` fires (`routes/safety.py:464`); no `emit_task_and_notification`
- **Closure shape:** identical pattern; operator should confirm whether meetings join the JHA/FL fix-track
- **Code reference confirmed:** `routes/safety.py:455–465`

### G-P1-05 · Training Record assigned — supervisor of trainee not notified
- **Was:** GAP-4, SOFT-4
- **Symptom:** trainee gets bell + task; their supervisor doesn't (`linked_supervisor` lookup intermittent)
- **Code:** `routes/training_center.py`
- **Closure shape:** improve `linked_supervisor` resolution or duplicate the notification to manager-of-employee chain

### G-P1-06 · Shop Equipment Trash button → 403
- **Was:** GAP-10
- **Symptom:** button visible to Shop user on `/shop/equipment`; POST returns 403 (admin-only delete)
- **Closure shape:** hide button under shop token (cosmetic frontend gate)

### G-P1-07 · `/equipment/:id` always redirects to admin namespace
- **Was:** GAP-16
- **Symptom:** cross-portal users following an external link land in admin namespace instead of their portal's view
- **Closure shape:** portal-aware redirect via auth context

### G-P1-08 · `/inspections/:id` always redirects to admin namespace
- **Was:** GAP-17
- **Symptom:** mirror of G-P1-07
- **Closure shape:** mirror of G-P1-07

---

## §3 · P2 — Improvement gaps (6 items)

### G-P2-01 · Payroll Variance manual run — no fan-out
- **Was:** GAP-5
- **Symptom:** weekly cron emails `PAYROLL_VARIANCE_EMAIL_TO`; manual button-press path emits nothing because HR Manager is presumed to be running it directly
- **Closure shape (if desired):** even for manual runs, emit a one-line audit notification to admin

### G-P2-02 · Daily Report Weather=YES — no schedule-impact task
- **Was:** GAP-8
- **Symptom:** Weather toggle YES does not auto-create a downstream task or constraint
- **Status:** operator-confirmed stop-list (schedule integration intentionally deferred)

### G-P2-03 · Daily Report Equipment-Issue=YES — no Pre-Op auto-link
- **Was:** GAP-9
- **Symptom:** YES flag does not auto-create or auto-link to a Pre-Op record
- **Status:** P2 future hardening

### G-P2-04 · Severe Incident — no no-response escalation cadence
- **Was:** GAP-14
- **Symptom:** first-response email + bell + task fire correctly with `priority="Critical"`; if Safety doesn't acknowledge, no timed re-ping
- **Code:** `routes/safety.py:585–620`
- **Closure shape (if architected):** introduce a delayed re-ping cron — pattern would generalize to G-P2-05 too

### G-P2-05 · PO Request — no higher-tier escalation after extended no-receipt threshold
- **Was:** GAP-15
- **Symptom:** nightly cron creates `receipt-missing` task; no separate escalation to PM / Office Manager beyond that
- **Closure shape:** add a second-tier cron at e.g. 60 days

### G-P2-06 · PM sidebar links to PM Exposure Tile (intentionally unrouted)
- **Was:** GAP-18
- **Symptom:** PM Hub sidebar references a route that is intentionally not declared in `App.js` (operator stop-list)
- **Status:** intentional; closure = hide sidebar item until route is enabled

---

## §4 · P3 — Test-only / cosmetic (3 items)

### G-P3-01 · Stale tab-title tests in DispatchHub.jsx / ShopHub.jsx
- **Was:** GAP-11
- **Symptom:** pre-deploy orchestrator test fails; prod shape is unaffected

### G-P3-02 · Daily Report delete tests assert pre-freeze 200 / 404 behavior
- **Was:** GAP-12
- **Symptom:** the DR delete doctrine now returns 410 (frozen); tests still assert pre-freeze shape

### G-P3-03 · Unified projector test non-deterministic when preview DB > 200 DRs share a date
- **Was:** GAP-13
- **Symptom:** test_wave_1a.py asserts an ordering that breaks at scale

---

## §5 · Rollup

| Tier | Count | IDs |
|---|---:|---|
| P0 | 2 | G-P0-01 (Fleet DVIR), G-P0-02 (Backup scheduler) |
| P1 | 8 | G-P1-01 … G-P1-08 |
| P2 | 6 | G-P2-01 … G-P2-06 |
| P3 | 3 | G-P3-01 … G-P3-03 |
| **Total gaps** | **19** | (consistent with prior register) |
| Confirmed hard orphans | 1 | G-P0-01 |

---

## §6 · Stop / clarification questions for the operator (decision points)

1. **G-P0-01 / Fleet DVIR** — passive ledger or active workflow? (drives the entire fix shape for the P0 orphan)
2. **G-P0-02 / Backup scheduler** — please probe `$PROD_URL/api/admin/backups-scheduler-state` and confirm `alive=true` in production
3. **G-P1-04 / Safety Meeting** — does it join the JHA/FL fix-track (G-P1-01/02/03/04 batch) or stay email-only intentionally?
4. **Escalation cadence** (G-P2-04, G-P2-05, etc.) — is a generalized "no-response timer" framework on a future track or permanently out of scope?
5. **Realtime push** (TRUTH_MAP §2.5) — polling acceptable indefinitely, or schedule WebSocket/SSE later?

---

## §7 · Stop-condition compliance

- ✅ Read-only consolidation — no code, schema, env, prod-write changes
- ✅ Every entry has Memory + Code + Runtime (where applicable) citation
- ✅ No remediation proposed beyond "closure shape" hints — operator must explicitly authorize any fix work

---

_End of PLATFORM_GAP_LEDGER_FINAL.md. Supersedes `ORPHAN_AND_GAP_REGISTER.md` and `NOTIFICATION_GAP_REGISTER.md`._

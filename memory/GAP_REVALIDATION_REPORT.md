# GAP_REVALIDATION_REPORT

**Date:** 2026-02-01 · Phase 2A-2
**Scope:** Re-validate every gap in `ORPHAN_AND_GAP_REGISTER.md` against the live 2026-02-01 codebase. Each row answers: still exists? confirmed by code? confirmed by runtime? severity? owner? recommended fix? operator decision required?

> "Confirmed by runtime" = corroborating evidence in prod/preview logs or screenshots.
> "Confirmed by code" = static grep / route handler inspection.

---

## P0 tier (operational risk now)

### GAP-7 · Backup scheduler dead
- **Still exists?** YES — confirmed by `BACKUP_RUNTIME_DIAGNOSTIC_REPORT.md` (2026-05-29) AND fresh 2026-02-01 preview log review (see `BACKUP_SCHEDULER_READINESS_REPORT.md` §2).
- **Confirmed by code?** YES — `server.py:11212 _start_backup_scheduler` launches `_backup_scheduler_loop` via `run_with_singleton_lock`; scheduler supervisor on line 11276 detects dead task every 5 min and respawns; respawned task immediately dies.
- **Confirmed by runtime?** YES — 2026-05-29 production probe: `task_alive: false` since pod boot. 2026-02-01 preview confirms supervisor cycle running ("DEAD — respawning" every 5 min in `/var/log/supervisor/backend.err.log`).
- **Severity:** P0 in production · P0 HELD per operator stop-list
- **Business impact:** Without the scheduler, the only path to a fresh backup is the manual admin `POST /api/admin/backups/run-now`. Last verified complete-r2 in prod was 2026-05-26 — drift accumulates if not manually run.
- **Owner:** Admin (operator + super-admin Jaymn Judd)
- **Recommended fix:** Per `BACKUP_SCHEDULER_READINESS_REPORT.md` (separate deliverable) — 5-phase hardening, **operator-authorized only**.
- **Operator decision required:** Authorization to begin scheduler hardening (currently HELD).
- **Verdict: 🔴 BROKEN — confirmed by both code and runtime.**

### ORPHAN-1 / GAP-6 · Fleet DVIR
- **Still exists?** YES — fully re-investigated in `FLEET_DVIR_INVESTIGATION_REPORT.md`.
- **Confirmed by code?** YES — `routes/fleet_ops.py:412 @router.post("/api/fleet/inspections")` writes to `db.equipment_inspections` (kind="dvir") + `db.fleet_defects`. **NO `schedule_auto_email`, NO `emit_task_and_notification`, NO bell notification anywhere in fleet_ops.py.**
- **Confirmed by runtime?** Not directly tested in this pass — operator may want runtime confirmation that a defect-triggering DVIR submission does NOT create a task. Static evidence is conclusive: the call sites simply don't exist.
- **Severity:** ⚫ OPERATOR DECISION NEEDED — system is functioning as currently coded; operator must decide intended behaviour.
- **Business impact:** Vehicle defects discovered in DVIR are recorded as `fleet_defects` and the truck's `fleet_status` becomes `oos` / `defect_open`, visible on the Dispatch fleet status board. **Nobody is notified** to act on the defect. Shop / Safety / Dispatch must proactively check the board.
- **Owner:** Currently un-assigned. Should be Shop (defects) + Safety (safety-related defects) + Dispatch (OOS impact).
- **Recommended fix:** See `FLEET_DVIR_INVESTIGATION_REPORT.md` §6 for the proposed notification matrix.
- **Operator decision required:** Confirm desired routing matrix before any code is written.
- **Verdict: ⚫ OPERATOR DECISION NEEDED — confirmed by code; runtime test recommended.**

---

## P1 tier (must fix before pilot)

### GAP-1 · Field Leadership 10 forms — no bell/task fan-out
- **Still exists?** YES.
- **Code:** `routes/field_leadership_users.py` (read; grep for `emit_task_and_notification` returns nothing in the FL submit path).
- **Runtime:** No bell entries observed for FL forms (corroborated by Notifications Hub audit history).
- **Severity:** P1 — Field leadership submissions reach safety@/admin@ via email, but no per-record action queue exists on Safety/Admin hub.
- **Business impact:** Submissions land in inbox; risk of being missed during high-volume periods.
- **Owner:** Safety (primary action) + HR (compliance lens).
- **Recommended fix:** Insert one `emit_task_and_notification` call in the FL form submit handler with `assignee_role: "safety"`, `recipient_role: "safety"`.
- **Operator decision required:** Authorize the fix.
- **Verdict: 🟡 KNOWN GAP — confirmed by code.**

### GAP-2 · Safety Forms (issuance / training / return) — no bell/task fan-out
- **Still exists?** YES.
- **Code:** `routes/safety_forms_*.py` — confirmed no `emit_task_and_notification` calls in submit handlers.
- **Runtime:** Safety Hub "Open Safety Forms" tile is a count-only badge (verified visually during Stabilization Pass 8 audit screenshots).
- **Severity:** P1.
- **Business impact:** Same as GAP-1 — email-only delivery with no per-record action queue.
- **Owner:** Safety.
- **Recommended fix:** Insert `emit_task_and_notification(recipient_role="safety")` on submit.
- **Verdict: 🟡 KNOWN GAP — confirmed by code.**

### GAP-3 · JHA submit — no bell/task fan-out
- **Still exists?** YES.
- **Code:** `routes/safety.py:509–519` — only `schedule_auto_email("jha", doc)`, no `emit_task_and_notification`.
- **Runtime:** Confirmed — JHA submissions do not surface in Safety bell drawer.
- **Severity:** P1.
- **Business impact:** Same family as GAP-1 / GAP-2.
- **Owner:** Safety supervisor.
- **Recommended fix:** Add `emit_task_and_notification(recipient_role="safety", priority="Medium")` after line 518 in safety.py.
- **Verdict: 🟡 KNOWN GAP — confirmed by code.**

### NEW-GAP-A · Safety Meeting submit — no bell/task fan-out (newly surfaced during validation)
- **Still exists?** YES — surfaced in `TRUTH_MAP_VALIDATION_REPORT.md` Workflow 4.
- **Code:** `routes/safety.py:455–465` — only `schedule_auto_email("meeting", doc)`, no fan-out.
- **Severity:** P1 (matches JHA pattern).
- **Business impact:** Meetings recorded as ledger only; no per-record actionable queue.
- **Owner:** Safety.
- **Recommended fix:** Add `emit_task_and_notification(recipient_role="safety", priority="Low")` after line 464.
- **Operator decision required:** Decide if meetings are intentionally email-only ledger (no action needed) or should join the JHA/FL forms fix.
- **Verdict: 🟡 KNOWN GAP — newly documented.**

### GAP-4 · Training assignment — supervisor of trainee not notified
- **Still exists?** YES.
- **Code:** `routes/training_center.py` — emits to trainee role only; no resolution of `linked_supervisor` for the notification recipient.
- **Severity:** P1.
- **Business impact:** Supervisors miss visibility into who on their crew has overdue training.
- **Owner:** Training admin (process) + Safety (compliance lens).
- **Recommended fix:** When trainee has `linked_supervisor_employee_id` resolved, emit a `recipient_employee_id` notification to that supervisor in addition to the trainee.
- **Verdict: 🟡 KNOWN GAP — confirmed by code.**

### GAP-10 · Shop Equipment Trash button — 403
- **Still exists?** YES.
- **Code:** Shop user click → DELETE endpoint requires `require_admin`. UI doesn't hide the button for non-admins.
- **Severity:** P1 — cosmetic / UX, no data risk.
- **Business impact:** Shop user sees a button that always fails; confidence-eroding.
- **Owner:** Frontend.
- **Recommended fix:** Conditionally render Trash button only when `role === "admin"` in `ShopEquipment.jsx`.
- **Verdict: 🟡 KNOWN GAP — confirmed by code.**

### GAP-16 · `/equipment/:id` redirects to admin namespace
- **Still exists?** YES — confirmed in `App.js` route table.
- **Code:** `App.js` defines `<Route path="/equipment/:id" element={<Navigate to="/admin/equipment/:id" />}` (or equivalent).
- **Severity:** P1.
- **Business impact:** Cross-portal users (PM / Shop / Dispatch) following a deep link land in `/admin/...` which they can't access; they hit access-denied.
- **Owner:** Frontend.
- **Recommended fix:** Route redirect to use the active portal of the current token, OR a generic `/r/:kind/:id` redirector that resolves portal from token.
- **Verdict: 🟡 KNOWN GAP — confirmed by code.**

### GAP-17 · `/inspections/:id` redirects to admin namespace
- Same pattern as GAP-16. Confirmed in `App.js`.
- **Verdict: 🟡 KNOWN GAP — confirmed by code.**

---

## P2 tier (improvement opportunity)

### GAP-5 · Payroll Variance manual run — no fan-out
- **Still exists?** YES.
- **Code:** Manual `POST /api/hr/payroll-variance/run` does not emit notifications. Cron path (in server.py) does send the weekly digest email.
- **Severity:** P2 — HR Manager is the runner and recipient; no visibility loss.
- **Business impact:** Low (HR runs it and sees the result immediately).
- **Owner:** HR Manager (no fix may be needed).
- **Recommended fix:** Optional — emit a notification to the HR Manager group when manually triggered, for audit traceability.
- **Operator decision required:** Confirm whether this is worth fixing.
- **Verdict: 🟡 KNOWN GAP — confirmed by code, intentional acknowledgement may be sufficient.**

### GAP-8 · Daily Report Weather=YES — no schedule-impact task
- **Still exists?** YES.
- **Code:** `routes/daily_reports.py` does not branch on `weather_impact`.
- **Severity:** P2 (stop-list intentional — schedule integration is on hold).
- **Verdict: 🟡 KNOWN GAP — intentional hold.**

### GAP-9 · Daily Report Equipment-Issue=YES — no Pre-Op auto-link
- **Still exists?** YES — same as GAP-8 family.
- **Severity:** P2.
- **Verdict: 🟡 KNOWN GAP — intentional hold.**

### GAP-14 · Severe Incident — no no-response escalation
- **Still exists?** YES — `routes/safety.py` incident handler does not register a follow-up cron entry.
- **Severity:** P2.
- **Verdict: 🟡 KNOWN GAP.**

### GAP-15 · PO no-receipt > 30d — no higher-tier escalation
- **Still exists?** YES — `scan_missing_receipts` flags once per PO (idempotent via `missing_receipt_flagged`); no second-tier escalation at 30d.
- **Severity:** P2.
- **Verdict: 🟡 KNOWN GAP.**

### GAP-18 · PM sidebar links to PM Exposure Tile (unrouted)
- **Still exists?** YES — `App.js` does not contain a `/pm/exposure-tile` route (intentional per operator stop-list).
- **Severity:** P2.
- **Verdict: 🟡 KNOWN GAP — intentional stop-list.**

---

## P3 tier (test-only — no user impact)

### GAP-11 · Stale tab-title tests in DispatchHub.jsx / ShopHub.jsx
- **Still exists?** Likely yes (no source change since the audit). Frontend tab titles changed but tests not updated.
- **Severity:** P3.
- **Verdict: 🟡 KNOWN GAP — confirmed by prior audit; not re-tested here.**

### GAP-12 · Daily Report delete tests assert pre-freeze behaviour
- **Severity:** P3.
- **Verdict: 🟡 KNOWN GAP — confirmed by prior audit; not re-tested here.**

### GAP-13 · Unified projector test fails when preview DB > 200 DRs share a date
- **Severity:** P3.
- **Verdict: 🟡 KNOWN GAP — confirmed by prior audit; not re-tested here.**

---

## New gaps surfaced this pass

| ID | Description | Severity |
|----|-------------|----------|
| NEW-GAP-A | Safety Meeting submit — no bell/task fan-out (same family as JHA/GAP-3) | P1 |
| NEW-FINDING-B | Pre-Op FAIL notifies Dispatch in addition to Shop — Truth Map under-specified this | (informational) |
| NEW-FINDING-C | Incident creation is idempotency-wrapped — positive design pattern, document for future workflows | (informational) |

---

## Re-ranked gap inventory

| Tier | Items |
|------|-------|
| **P0 (operational risk now)** | GAP-7 (Backup scheduler dead) · GAP-6/ORPHAN-1 (Fleet DVIR — operator decision) |
| **P1 (must fix before pilot)** | GAP-1, GAP-2, GAP-3, NEW-GAP-A, GAP-4, GAP-10, GAP-16, GAP-17 (8 items) |
| **P2 (improvement opportunity)** | GAP-5, GAP-8, GAP-9, GAP-14, GAP-15, GAP-18 (6 items) |
| **P3 (test-only)** | GAP-11, GAP-12, GAP-13 (3 items) |
| **Total** | **19 gaps + 1 confirmed orphan** |

---

## Compliance with mission

- ✅ Read-only static + runtime-log evidence.
- ✅ No fix applied.
- ✅ Every gap confirmed by either code grep or prior diagnostic report.
- ✅ Severity re-ranked per pilot-readiness criteria.
- ✅ Operator decision flagged on GAP-5, GAP-6, and NEW-GAP-A.

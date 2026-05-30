# ORPHAN_AND_GAP_REGISTER

**Date:** 2026-02-01 · Part of the Platform Truth Map
**Method:** Consolidated re-validation of `ORPHAN_WORKFLOW_REPORT.md` (2026-05-29) and `NOTIFICATION_GAP_REGISTER.md` (2026-05-29) against current 2026-02-01 codebase. No new orphans surfaced during this audit; the prior register is current.

> An orphan is any workflow that satisfies ANY of:
> 1. Record exists but no owner is defined
> 2. Record exists but no notification path exists
> 3. Record exists but no dashboard destination exists
> 4. Record exists but no next-step authority is defined

A gap is the next tier down: workflow functions but visibility, escalation, or fan-out is incomplete.

---

## 1 · Confirmed orphans (P0)

### ORPHAN-1 · Fleet DVIR
- **Record location**: `db.fleet_dvirs` (referenced in `routes/fleet_ops.py`; collection presence in DB not verified at runtime)
- **Submit routes**: `/fleet/dvir/new`, `/fleet/dvir/submit`, `/fleet/dvir/submitted/:id`, `/fleet/weekly-emergency/new`, `/fleet/weekly-lead/new`
- **Notification path**: NONE confirmed (grep finds no `schedule_auto_email` or `emit_task_and_notification` for DVIR kinds)
- **Dashboard surface**: NONE confirmed — no "Open DVIRs" tile on Dispatch or Shop hub
- **Next-step authority**: undefined
- **Classification**: **⚫ OPERATOR DECISION NEEDED** — pending clarification of whether DVIR is operationally actionable or purely informational ledger
- **Operator question**: "Should a Fleet DVIR with a recorded defect drive a Shop / Dispatch task and notification? If yes, this orphan needs immediate closure."

---

## 2 · Soft orphans (P1 — workflow functions but visibility incomplete)

### SOFT-1 · Field Leadership 10 forms (= GAP-1)
- Notification: ✅ email to `leadership_always_to` (default safety@ + admin)
- Dashboard surface: search-only (`/admin/leadership/records/:id`, `/leadership/records`, `/hr/field-leadership`, `/field-leadership/portal/dashboard`)
- Gap: no actionable "open FL forms" stat card on Safety or Admin hubs. Records reach inboxes but don't surface as a queue.
- Classification: **🟡 KNOWN GAP (P1)**

### SOFT-2 · Safety Equipment Issuance / Training / Return (= GAP-2)
- Notification: ✅ email to `SAFETY_FORMS_EMAIL_TO`
- Dashboard surface: `/admin/safety/issuance/:id`, `/admin/safety/training/:id`, `/safety-portal/forms-records` (search-only) · Safety Hub "Open Safety Forms" count card
- Gap: count-only, not per-record actionable
- Classification: **🟡 KNOWN GAP (P1)**

### SOFT-3 · JHA submit (= GAP-3)
- Notification: ✅ email to safety + `ALWAYS_CC`
- Dashboard surface: `/admin/jha-plans`, `/pm/jha-plans`, `/safety-portal/library` (search-only)
- Gap: no task fan-out, no Safety Hub action card
- Classification: **🟡 KNOWN GAP (P1)**

### SOFT-4 · Training Records — supervisor lens (= GAP-4)
- Notification: ✅ trainee bell + task
- Gap: supervisor of trainee not notified (`linked_supervisor` lookup intermittent)
- Classification: **🟡 KNOWN GAP (P1)**

---

## 3 · Process / UX gaps (P1–P2)

### GAP-5 · Payroll Variance manual run — no fan-out
- Cron path fires Resend to `PAYROLL_VARIANCE_EMAIL_TO`
- Manual button-press path has no email/bell because HR Manager is presumed to be running it directly
- Classification: **🟡 KNOWN GAP (P2)** — HR Manager owns runner

### GAP-8 · Daily Report Weather=YES — no schedule-impact task
- Daily Report has the Weather toggle; submitter ticks YES; no downstream task or constraint auto-created.
- Operator confirmed schedule integration is on stop-list
- Classification: **🟡 KNOWN GAP (P2 — intentional stop-list)**

### GAP-9 · Daily Report Equipment-Issue=YES — no Pre-Op auto-link
- Similar to GAP-8 — the YES flag does not auto-create or auto-link to a Pre-Op record
- Classification: **🟡 KNOWN GAP (P2)**

### GAP-10 · Shop Equipment Trash button — dead 403
- Button visible to Shop user on `/shop/equipment`, but POST returns 403 (admin-only delete)
- Classification: **🟡 KNOWN GAP (P1, cosmetic — visible action / no permission)** — fix candidate: hide button under shop token

### GAP-14 · Severe Incident — no no-response escalation
- First-response email + bell fires; no follow-up cadence (timed re-ping) if Safety doesn't acknowledge
- Classification: **🟡 KNOWN GAP (P2)**

### GAP-15 · PO Request no-receipt > 30d — no higher-tier escalation
- Nightly cron flags "receipt-missing > X days" via task creation; no separate escalation to PM/Office Manager after extended threshold
- Classification: **🟡 KNOWN GAP (P2)**

### GAP-16 · `/equipment/:id` redirect always to admin namespace
- Cross-portal users following an external link land in admin namespace instead of their portal's view
- Classification: **🟡 KNOWN GAP (P1)**

### GAP-17 · `/inspections/:id` redirect always to admin namespace
- Same pattern as GAP-16 for inspections
- Classification: **🟡 KNOWN GAP (P1)**

### GAP-18 · PM sidebar links to PM Exposure Tile (unrouted)
- PM Hub sidebar references a route that is intentionally not declared in `App.js` (operator stop-list)
- Classification: **🟡 KNOWN GAP (P2 — stop-list)**

---

## 4 · System gaps (P0 HELD)

### GAP-7 · Backup scheduler dead
- `lib/singleton_scheduler.py` cron lock-acquisition runs; the actual backup tick loop has died and not been restarted
- Manual backup still works (verified per `BACKUP_SCHEDULER_RESTART_VERIFICATION_REPORT.md`)
- Classification: **🔴 BROKEN — P0 HELD** (operator authorized hardening but paused until trust-restoration audit verified)

---

## 5 · Test-only gaps (P3 — not user-facing)

| ID | Issue |
|----|-------|
| GAP-11 | Stale tab-title tests in DispatchHub.jsx / ShopHub.jsx |
| GAP-12 | Daily Report delete tests assert pre-freeze behaviour |
| GAP-13 | Unified projector test fails when preview DB > 200 DRs share a date |

Classification: **🟡 KNOWN GAP (P3 — test-only, prod shape doesn't trigger)**.

---

## 6 · No-response paths summary

The audit confirmed **no workflow currently has a defined operator process for "what happens if the owner doesn't respond"**, except:

| Workflow | Has automated no-response handling? |
|----------|-------------------------------------|
| PO Requests | ✅ nightly cron creates approval-needed task + receipt-missing task |
| Equipment Pre-Op FAIL | ✅ task remains open in Shop queue indefinitely (and Shop dashboard shows count) |
| Document Expirations | ✅ nightly cron task to HR |
| Dispatch stuck > 30m | ✅ live board alert |
| Backup failures | ✅ (when scheduler alive) — currently HELD by GAP-7 |
| System Health red | ✅ `health_monitor._send_alert` |
| All other workflows | ❌ rely on human recipient to act; no escalation cadence |

Classification: **🟡 KNOWN GAP (P2)** — opportunity for future escalation framework, not on current authorized track.

---

## 7 · Validated complete chains (NOT orphans, NOT gaps)

These workflows have all four pillars (owner · notification · dashboard · next-step authority):

- Daily Report
- Equipment Pre-Op (PASS and FAIL paths)
- Shop Recovery / Asset Transfer
- PO Request lifecycle (full)
- Incident Report (first response — escalation = GAP-14)
- Safety Meeting
- Safety Inspection
- QA/QC (Concrete / Rebar / Subwork / Material Testing)
- Corrective Action
- Fire Extinguisher Inspection
- Dispatch Assignment
- Document Expiration
- Time Verification (read-only — no event to orphan)
- Payroll Variance weekly cron (manual run = GAP-5)
- Backup success rows (Admin Backup Health) — when scheduler alive
- System Health outages
- Multi-Portal Sign-in / MFA
- ODR Submission
- Employee Lifecycle
- Time-Off Request
- Driver Qualification
- Constraints
- Audit Log

Classification: **🟢 KNOWN GOOD**.

---

## 8 · Inventory rollup

| Tier | Count | Items |
|------|-------|-------|
| P0 orphan (OPERATOR DECISION NEEDED) | 1 | ORPHAN-1 / GAP-6 (Fleet DVIR) |
| P0 broken (HELD) | 1 | GAP-7 (Backup scheduler dead) |
| P1 visibility gaps | 7 | GAP-1, GAP-2, GAP-3, GAP-4, GAP-10, GAP-16, GAP-17 |
| P2 enhancement gaps | 6 | GAP-5, GAP-8, GAP-9, GAP-14, GAP-15, GAP-18 |
| P3 test-only | 3 | GAP-11, GAP-12, GAP-13 |
| **Total** | **18** | |

---

## 9 · Stop condition

This register is read-only documentation. No remediation has begun. Operator owns the call on which orphan/gap to close next.

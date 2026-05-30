# NOTIFICATION_GAP_REMEDIATION_PLAN

**Batch:** J · Operational Reliability Closeout · P1-B
**Date:** 2026-05-30 (UTC)
**Mission:** For every remaining notification gap in `PLATFORM_GAP_LEDGER_FINAL.md`, document current behavior · desired behavior · notification target · dashboard target · task target · estimated effort.
**Constraint:** No implementation. Mapping only.

**Source ledger:** `PLATFORM_GAP_LEDGER_FINAL.md` (this fork · Batch I) — 19 gaps total. This document covers the **notification-related** gaps. Pure UX / cosmetic / test-only gaps (G-P1-06, G-P1-07, G-P1-08, G-P2-06, P3 items) are out of scope for this plan — they are tracked in the master ledger but require no notification wiring.

---

## 1 · Scope of this plan

| Gap class | In scope | IDs |
|---|:--:|---|
| Notification fan-out missing | ✅ | G-P1-01, G-P1-02, G-P1-03, G-P1-04, G-P1-05, G-P2-01 |
| No-response cadence missing | ✅ | G-P2-04, G-P2-05 |
| DR sub-flow notification (intentional stop-list) | ⚠️ (docs-only) | G-P2-02, G-P2-03 |
| Cross-portal redirect / cosmetic / dead button | ❌ | G-P1-06, G-P1-07, G-P1-08 (UI gaps — not notification) |
| Sidebar link to unrouted page | ❌ | G-P2-06 (UI gap) |
| Test-only | ❌ | G-P3-01, G-P3-02, G-P3-03 |

**Net items remediated by this plan: 8.** (Fleet DVIR = G-P0-01 is covered separately by `FLEET_DVIR_DECISION_PACKAGE.md`. Backup scheduler = G-P0-02 is now certified healthy per `PRODUCTION_SCHEDULER_CERTIFICATION_REPORT.md`.)

---

## 2 · Per-gap remediation plan

### G-P1-01 · Field Leadership 10 forms — email only, no bell / task fan-out

| Aspect | Detail |
|---|---|
| Workflow | FL Portal: 10 form kinds submitted via `/leadership/{kind}/new` and `/field-leadership/portal/...` |
| Current behavior | `routes/field_leadership.py` / `routes/field_leadership_portal.py` — `schedule_auto_email("leadership-form", doc)` fires to `leadership_always_to` (default safety@ + admin). **No bell. No task.** Surface is search-only on `/admin/leadership/records`, `/hr/field-leadership`, `/pm/field-leadership`, `/field-leadership/portal/dashboard`. |
| Desired behavior | Email continues (unchanged) PLUS bell + task to safety + admin (the same `leadership_always_to` recipients become bell-targeted recipient roles). |
| Notification target | recipient_role = `safety` + parallel notification to `admin` |
| Dashboard target | Add **"Open FL Forms"** action queue card to Safety Hub and Admin Hub (top 5 unresolved · click → record detail) |
| Task target | `assignee_role = safety` · `priority = Medium` (or `High` for FL form kind = "Termination" / "Disciplinary") |
| Effort estimate | **~1 hour** — ~15 LOC `emit_task_and_notification` insertion per submit handler (each of the 10 form kinds shares the same handler pattern) + frontend tile add (~30 LOC) |

### G-P1-02 · Safety Equipment Issuance / Training / Return — email only

| Aspect | Detail |
|---|---|
| Workflow | Safety Forms suite — issuance, training, return |
| Current behavior | `routes/safety_forms.py` — `schedule_auto_email("safety-form-*", doc)` fires to `SAFETY_FORMS_EMAIL_TO` (default safety@ + jaymn.judd). **No bell. No task.** Safety Hub has a count-only "Open Safety Forms" tile. |
| Desired behavior | Email + bell + task to safety. Promote the count tile to a per-record action queue. |
| Notification target | recipient_role = `safety` |
| Dashboard target | Safety Hub — replace count card with **"Open Safety Forms"** action queue (top 5 · click → detail) |
| Task target | `assignee_role = safety` · `priority = Medium` |
| Effort estimate | **~1 hour** — ~15 LOC per form-kind handler in `safety_forms.py` + tile upgrade |

### G-P1-03 · JHA submit — email only, no task to Safety supervisor

| Aspect | Detail |
|---|---|
| Workflow | JHA submission · `POST /api/jhas` |
| Current behavior | `routes/safety.py:518` — `schedule_auto_email("jha", doc)` fires to safety + ALWAYS_CC. **No bell. No task.** Surface is `/admin/jha`, `/pm/jha-plans`, `/safety-portal/library` (search-only). |
| Desired behavior | Email + bell + task to safety supervisor. |
| Notification target | recipient_role = `safety` |
| Dashboard target | Safety Hub — **"Open JHAs"** action queue (top 5 · click → detail) |
| Task target | `assignee_role = safety` · `priority = Medium` |
| Effort estimate | **~30 minutes** — ~15 LOC in `routes/safety.py` between `schedule_auto_email("jha", doc)` (line 518) and the response return |

### G-P1-04 · Safety Meeting submit — email only (NEW-GAP-A, identified 2026-02-01)

| Aspect | Detail |
|---|---|
| Workflow | Safety Meeting submission · `POST /api/meetings` |
| Current behavior | `routes/safety.py:464` — `schedule_auto_email("meeting", doc)` fires to PM + ALWAYS_CC. **No bell. No task.** Surface is `/admin/meetings`, `/pm/meetings`, Safety Portal library (search-only). |
| Desired behavior | Email + bell + task to safety. Symmetric with G-P1-03 (JHA). |
| Notification target | recipient_role = `safety` (acknowledgement / review) · OR `pm` (visibility) — operator decides primary owner |
| Dashboard target | Safety Hub — **"Open Meetings"** queue · OR PM Hub "Recent Meetings" card |
| Task target | `assignee_role = safety` (per ownership matrix) · `priority = Medium` |
| Effort estimate | **~30 minutes** — same pattern as G-P1-03; same file |
| ⚠ Operator decision | Confirm whether this joins the JHA/FL fix-track or stays email-only intentionally |

### G-P1-05 · Training Record assigned — supervisor of trainee not notified

| Aspect | Detail |
|---|---|
| Workflow | Training Center assignment |
| Current behavior | `routes/training_center.py` — trainee receives bell + task. **Trainee's supervisor does NOT.** The `linked_supervisor` lookup against the trainee's `employee.linked_supervisor` field is intermittent (sometimes the field is missing or stale). |
| Desired behavior | Trainee continues to receive bell + task (unchanged) PLUS supervisor receives a parallel **visibility notification** (no task — supervisor is informational owner of their crew's compliance). |
| Notification target | recipient_role = `<supervisor's role>` resolved from `employees.linked_supervisor` chain · fallback to `hr` if unresolved |
| Dashboard target | Supervisor's portal Notification Bell · existing surface |
| Task target | None for supervisor (visibility only) · trainee task unchanged |
| Effort estimate | **~2 hours** — supervisor-resolution helper (~30 LOC), parallel `emit_notification` call (~10 LOC), unit test (~30 LOC). The complexity is `linked_supervisor` resolution robustness, not the emit. |

### G-P2-01 · Payroll Variance manual run — no fan-out

| Aspect | Detail |
|---|---|
| Workflow | HR Manager presses "Run Variance Now" button (vs the weekly cron path) |
| Current behavior | Weekly cron emits `payroll-variance-weekly-digest` to `PAYROLL_VARIANCE_EMAIL_TO`. **Manual button-press path emits nothing** — HR Manager is the audience and is already running it directly. |
| Desired behavior | One-line audit notification to admin on manual run (record-keeping). HR Manager sees the result on the screen (unchanged). |
| Notification target | recipient_role = `admin` (audit-trail visibility) |
| Dashboard target | Audit log entry (existing) — no new tile |
| Task target | None (informational only) |
| Effort estimate | **~15 minutes** — single `emit_notification` call in the manual-run handler |

### G-P2-04 · Severe Incident — no no-response escalation cadence

| Aspect | Detail |
|---|---|
| Workflow | Incident with `severity ∈ {"critical", "high", "serious"}` or `osha_recordable=true` |
| Current behavior | `routes/safety.py:585–620` — first-response email + bell + task fire correctly with `priority="Critical"`. **If Safety doesn't acknowledge within N hours, nothing happens.** No re-ping cron. |
| Desired behavior | If task remains `status="open"` AND `priority="Critical"` AND `created_at < now - 4h`, fire a second bell + task to Safety lead + Admin. Continue every 4h until acknowledged or 24h elapsed → admin pager. |
| Notification target | Step 1 (4h): recipient_role=`safety_lead` (or `safety` + admin if no _lead) · Step 2 (8h): recipient_role=`admin` · Step 3 (24h): out-of-band channel (e.g., Resend high-priority subject prefix) |
| Dashboard target | Admin Hub — **"Unacknowledged Critical Incidents"** alert tile (red badge if any > 4h) |
| Task target | Second task → `safety_lead` · third task → `admin` |
| Effort estimate | **~4 hours** — generalizable escalation cron framework (~80 LOC) shared with G-P2-05; first-batch implementation must be careful about idempotency (use `escalated_at` field on tasks) |
| Note | This is the first instance of a **generalized no-response cadence framework**. The same code can serve G-P2-05 and any future similar gap. |

### G-P2-05 · PO Request — no higher-tier escalation after extended no-receipt threshold

| Aspect | Detail |
|---|---|
| Workflow | PO Request approved · receipt awaited |
| Current behavior | Nightly cron creates `receipt-missing` task at e.g. day 15. **No second-tier escalation** to PM / Office Manager at day 30 / 60. |
| Desired behavior | Add a second-tier sweep at day 60 (configurable) — emit task to PM (project owner) + Admin. |
| Notification target | recipient_role = `pm` (project owner, resolved via `project_number → pm_email`) + `admin` |
| Dashboard target | PM Hub — **"Stale POs"** tile · Admin Hub — same |
| Task target | `assignee_role = pm` (primary) + admin visibility notification |
| Effort estimate | **~2 hours** if the G-P2-04 framework lands first (just add another row in the escalation config) · **~4 hours** standalone |

---

## 3 · DR sub-flow gaps — stop-list confirmation (no remediation in this plan)

### G-P2-02 · Daily Report Weather=YES — no schedule-impact task
- **Operator decision** (recorded in prior batches): **schedule integration is on the stop-list intentionally.** No remediation planned in this batch.
- Documents: continues to be tracked as P2 in the gap ledger; closure depends on schedule-integration unfreezing.

### G-P2-03 · Daily Report Equipment-Issue=YES — no Pre-Op auto-link
- **P2 future hardening.** Not in current scope. Documented for completeness.

---

## 4 · Aggregate effort estimate

| Gap | Effort |
|---|---|
| G-P1-01 (FL forms) | ~1 h |
| G-P1-02 (Safety forms) | ~1 h |
| G-P1-03 (JHA task) | ~0.5 h |
| G-P1-04 (Safety Meeting) | ~0.5 h |
| G-P1-05 (Training supervisor) | ~2 h |
| G-P2-01 (Payroll manual audit) | ~0.25 h |
| G-P2-04 (Severe Incident cadence — framework) | ~4 h |
| G-P2-05 (PO 60-day escalation — reuse framework) | ~2 h |
| **Subtotal — code work** | **~11.25 h** |
| Dashboard tile additions (FL queue, Safety forms queue, JHA queue, Stale POs) | ~2 h frontend × 4 = ~8 h |
| Smoke testing (manual fire of each event + bell verification) | ~2 h |
| **Grand total — focused work** | **~21 h** |

---

## 5 · Suggested batching for future authorization

If the operator authorizes notification remediation in future batches, this plan suggests:

| Batch | Scope | Effort |
|---|---|---|
| **Batch K · "Email-only → bell+task" fast set** | G-P1-01, G-P1-02, G-P1-03, G-P1-04, G-P2-01 (5 gaps · all the same pattern · symmetric to existing safety/equipment fan-out) | ~3 h code + ~2 h tile work + ~1 h tests |
| **Batch L · Training supervisor lens** | G-P1-05 (resolution complexity) | ~2 h code + tests |
| **Batch M · Escalation cadence framework** | G-P2-04 (framework) + G-P2-05 (first reuse) | ~6 h code + tests |

Operator owns the call on which (if any) batches to authorize. **No implementation work has begun.**

---

## 6 · Stop-condition compliance

- ✅ Read-only mapping
- ✅ No code changes
- ✅ No schema changes
- ✅ No new endpoints
- ✅ Operator decisions surfaced (NEW-GAP-A inclusion decision in G-P1-04)
- ✅ Effort estimates are observations, not commitments — operator owns prioritization

---

_End of NOTIFICATION_GAP_REMEDIATION_PLAN.md · No implementation authorized in Batch J._

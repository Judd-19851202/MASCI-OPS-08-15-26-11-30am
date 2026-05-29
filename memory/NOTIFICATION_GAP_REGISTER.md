# Notification Gap Register

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:44 UTC._

> Consolidated register of every notification/alert gap surfaced during
> the platform-wide audit. Each gap classified per operator's rubric.
> Read-only audit, no fixes.

## 1 · Classification rubric (from operator directive)

| Tier | Definition |
|---|---|
| **P0** | Workflow can disappear · no owner · no destination · no notification · operational risk |
| **P1** | Workflow works but visibility unclear |
| **P2** | Workflow works but could improve |
| **OK** | Workflow fully intentional and complete |

## 2 · Gap register

| ID | Gap | Workflow | Email? | Bell? | Task? | Dashboard? | Classification |
|---|---|---|---|---|---|---|---|
| GAP-1 | FL 10 forms have no bell/task fan-out | Field Leadership forms (10 form types) | ✅ leadership_always_to | ❌ | ❌ | search-only | **P1** (records reach safety/admin via email; bell-feed enhancement would close the loop) |
| GAP-2 | Safety Forms (Equipment Issuance / Training / Return) have no bell/task | Safety Forms suite | ✅ safety_forms_to | ❌ | ❌ | search-only | **P1** |
| GAP-3 | JHA submit has no task to safety supervisor | Safety / JHA | ✅ safety + always_cc | ❌ | ❌ | search-only | **P1** |
| GAP-4 | Training Record assigned does not notify supervisor (only employee) | Training Center | ❌ | ✅ (employee) | ✅ (employee) | partial | **P1** |
| GAP-5 | Payroll Variance manual batch creates no email/bell — only the weekly cron does | HR Payroll Variance | weekly only | ❌ | ❌ | HR page surface | **P2** (HR Manager runs it and reviews directly; cron handles automation) |
| GAP-6 | Fleet DVIR has no confirmed notification path | Fleet DVIR | ❌ | ❌ | ❌ | ❌ | **P0** — needs operator clarification of intent; if DVIR is meant to drive Shop/Dispatch action, this is a true orphan |
| GAP-7 | Backup-failure alerts blocked because scheduler is dead | System Health · Backup pipeline | ✅ (when scheduler alive) | ❌ | ❌ | Admin Backup Health panel | **P0** — separately tracked; operator authorized hardening but held pending current trust-restoration audit |
| GAP-8 | Daily Report Weather YES does NOT create a schedule-impact task | Daily Report sub-flow | inherits DR email | ❌ | ❌ | n/a | **P2** — operator confirmed schedule integration on stop-list |
| GAP-9 | Daily Report Equipment-Issue YES does NOT auto-link to Equipment Pre-Op | Daily Report sub-flow | inherits | ❌ | ❌ | n/a | **P2** |
| GAP-10 | Shop Equipment Trash button visible to Shop but rejects with 403 | Shop Equipment Dashboard | n/a | n/a | n/a | n/a | **P1** (dead button — visible action / no permission) |
| GAP-11 | Stale tab-title tests block pre-deploy orchestrator | DispatchHub.jsx · ShopHub.jsx test contracts | n/a | n/a | n/a | n/a | **P3** (test-only) |
| GAP-12 | Daily Report delete tests assert pre-freeze 200/404 behavior | test_daily_reports.py | n/a | n/a | n/a | n/a | **P3** (test-only) |
| GAP-13 | Unified projector test fails when preview DB > 200 DRs share a date | test_wave_1a.py | n/a | n/a | n/a | n/a | **P3** (test-only; prod DB shape doesn't trigger) |
| GAP-14 | Incident Report severe — no defined no-response escalation path | Incident Report | ✅ + `severe_incident_cc` | ✅ | ✅ | Safety Hub | **P2** — works for first response; no follow-up cadence yet |
| GAP-15 | PO Response — no "no receipt uploaded for 30+ days" escalation | PO Requests | none | none | nightly cron creates receipt-missing task | PO list | **P2** (cron creates task; lack of higher-tier escalation is documented) |
| GAP-16 | `/equipment/:id` redirect always to admin namespace | Routing | n/a | n/a | n/a | n/a | **P1** (cross-portal bounce) |
| GAP-17 | `/inspections/:id` redirect always to admin namespace | Routing | n/a | n/a | n/a | n/a | **P1** (mirror of GAP-16) |
| GAP-18 | PM sidebar links to PM Exposure Tile route which is intentionally unrouted | PM Hub sidebar | n/a | n/a | n/a | n/a | **P2** (operator confirmed PM Exposure Tile is on stop-list) |

## 3 · P0 gaps summary

| ID | Gap | Status |
|---|---|---|
| GAP-6 | Fleet DVIR no notification path | **Awaiting operator clarification** — could be intentional or orphan |
| GAP-7 | Backup scheduler dead → alerts blocked | **Held** per V.5 priority order until P0-2/P0-3 verified live |

## 4 · P1 gaps summary (operational visibility)

| ID | Gap |
|---|---|
| GAP-1 | FL 10 forms bell/task |
| GAP-2 | Safety Forms bell/task |
| GAP-3 | JHA safety-supervisor task |
| GAP-4 | Training supervisor notification |
| GAP-10 | Shop Trash dead button |
| GAP-16 | `/equipment/:id` redirect |
| GAP-17 | `/inspections/:id` redirect |

## 5 · P2 gaps summary (improvement)

| ID | Gap |
|---|---|
| GAP-5 | Payroll Variance manual no fan-out |
| GAP-8 | DR Weather YES no schedule task (stop-list intentional) |
| GAP-9 | DR Equipment-Issue YES no auto-link to Pre-Op |
| GAP-14 | Severe incident no-response escalation |
| GAP-15 | PO no-receipt 30+ day escalation |
| GAP-18 | PM Exposure Tile sidebar link cleanup |

## 6 · P3 gaps summary (test-only)

| ID | Gap |
|---|---|
| GAP-11 | Tab-title tests stale |
| GAP-12 | DR delete tests stale |
| GAP-13 | Unified projector test non-deterministic |

## 7 · Total inventory

- **P0**: 2 (1 awaiting clarification · 1 held)
- **P1**: 7
- **P2**: 6
- **P3**: 3
- **Total gaps surfaced**: **18**

## 8 · Stop condition observed

Audit only. No gap-closure work has been started. Awaiting operator review and prioritization.

---

_End of NOTIFICATION_GAP_REGISTER.md._

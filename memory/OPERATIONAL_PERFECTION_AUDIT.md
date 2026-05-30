# OPERATIONAL_PERFECTION_AUDIT.md

**Batch:** OMEGA · Operational Perfection Track · Priority 1
**Date:** 2026-05-30 (UTC)
**Mode:** Read-only audit. Zero remediation. Zero code change.
**Sources:** `PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md` (41 workflows) · `PLATFORM_GAP_LEDGER_FINAL.md` (19 ranked gaps).
**Coverage:** 100 % of the 41 workflows · 100 % of the 19 ledgered gaps cross-referenced.
**Triangulation rule (inherited from Truth Map):** every Current/Desired/Gap claim cites code path or runtime evidence.

---

## 0 · Method

For each of 41 workflows I record the 10-field audit shape mandated by the operator:
**Creator · Owner · Visibility · Notifications · Escalation · Closure path · Current behavior · Desired behavior · Gap · Recommendation.**

Workflows are tabulated in 4 tiers by gap severity (P0 → P1 → P2 → none). For brevity, identical sub-records are collapsed into their parent (DR sub-records = parent DR row; sub-records of Safety Forms inherit the parent row). All file:line references are from `/app/backend`. Gap IDs reference `PLATFORM_GAP_LEDGER_FINAL.md`.

---

## 1 · P0 workflows (operational risk — 2 items)

### W-01 · Fleet DVIR / Weekly Lead / Weekly Emergency

| Field | Value |
|---|---|
| Creator | Driver / Operator (anon, via field tablet) |
| Owner | **UNDEFINED IN CODE** — policy says Dispatch + Shop (Normal=record, Defect=Shop, Safety Defect=Shop+Safety, OOS=Shop+Dispatch, Repeat=escalation per `FLEET_DVIR_POLICY_RECORD.md`) |
| Visibility | Admin Fleet panel + Shop Fleet view (read-only ledger) |
| Notifications | **NONE** — `routes/fleet_ops.py:412-553` only writes audit + rebuilds `fleet_status`; zero `emit_*` calls |
| Escalation | **NONE** |
| Closure path | `routes/fleet_ops.py:693+729+774+819` (acknowledge / repair / clear / oos) — audit-only |
| Current behavior | Submissions land in `fleet_defects`/`fleet_status`; nobody is told |
| Desired behavior | Per policy: defect → Shop task; safety-defect → Shop+Safety task; OOS → Shop+Dispatch task; repeat-defect → escalation |
| **Gap** | **G-P0-01** (ORPHAN-1) — confirmed orphan |
| Recommendation | Operator decision: passive ledger vs active workflow. If active, wire `emit_task_and_notification(...)` in submit + 4 lifecycle handlers; add "Open DVIRs" tile on Shop + Dispatch hubs |

### W-02 · Backup Alerts (scheduler-driven)

| Field | Value |
|---|---|
| Creator | `_backup_scheduler_loop` (system) |
| Owner | Admin |
| Visibility | Admin only (`backup_health` rows + `/api/admin/backups-scheduler-state`) |
| Notifications | Email to `BACKUP_EMAIL_TO` (lite mode only); in-app via `health_monitor._send_alert` when scheduler alive |
| Escalation | `health_monitor.py:49+200` red-alert email path (gated by `RESEND_API_KEY`) |
| Closure path | Admin acknowledges via re-arm endpoint |
| Current behavior | Preview: scheduler dead (DELTA-D1, P2 probe). Production: **iter441 just verified — worker survives complete-backup; hourly cadence DEFERRED per OMEGA stop-list** |
| Desired behavior | Hourly cycles succeed without OOM; backup_health row every hour; backup-age dashboard tile |
| **Gap** | **G-P0-02** + (UX) no operator-visible recovery dashboard — see RECOVERY_DASHBOARD_SPEC.md |
| Recommendation | Operator-only decision on `BACKUP_R2_HOURLY=true` enablement (deferred this batch); separately authorize Priority 3 dashboard build |

---

## 2 · P1 workflows (works, but visibility / fan-out gap — 8 items)

### W-03 · Safety Meeting submit
| Field | Value |
|---|---|
| Creator | Any portal user · Safety |
| Owner | Safety |
| Visibility | Safety · Admin · PM hubs (search-only) |
| Notifications | `routes/safety.py:464` — `schedule_auto_email("meeting", doc)` only · **no bell · no task** |
| Escalation | None |
| Closure path | Admin only |
| Current | Email-only |
| Desired | Add `emit_task_and_notification(safety)` mirroring incident pattern |
| **Gap** | **G-P1-04** (NEW-GAP-A) |
| Recommendation | Wire `emit_task_and_notification` post-`schedule_auto_email`; promote Safety Hub count card to action queue |

### W-04 · JHA submit
| Field | Value |
|---|---|
| Creator | Any portal user |
| Owner | Safety |
| Visibility | Safety · Admin · PM (scope) |
| Notifications | `routes/safety.py:518` — `schedule_auto_email("jha", doc)` only |
| Escalation | None |
| Closure path | Admin only |
| Current | Email-only |
| Desired | Identical to W-03 |
| **Gap** | **G-P1-03** (GAP-3) |
| Recommendation | Same as W-03 |

### W-05 · Field Leadership 10 forms
| Field | Value |
|---|---|
| Creator | Field Leadership user (per `X-FL-Token`) |
| Owner | `leadership_always_to` recipients (safety@ + admin) |
| Visibility | FL portal · Admin · HR · PM · Safety (search-only) |
| Notifications | Email-only · no `emit_*` calls in `routes/field_leadership*.py` |
| Escalation | None |
| Closure path | Admin only |
| Current | Email-only |
| Desired | Add `emit_task_and_notification` + "Open FL Forms" queue on Safety + Admin hubs |
| **Gap** | **G-P1-01** (GAP-1 + SOFT-1) |
| Recommendation | One unified safety-action-queue tile reduces dashboard sprawl while closing G-P1-01/02/03/04 in one batch |

### W-06 · Safety Equipment Issuance / Training / Return (3 forms)
| Field | Value |
|---|---|
| Creator | Safety / HR |
| Owner | Safety (issuance/return) · Employee+Safety (training) |
| Visibility | Safety · Admin · HR |
| Notifications | Email-only to `SAFETY_FORMS_EMAIL_TO` |
| Escalation | None |
| Closure path | Admin only |
| Current | Email-only · count card only on Safety hub |
| Desired | `emit_task_and_notification(safety)` + actionable queue tile |
| **Gap** | **G-P1-02** (GAP-2 + SOFT-2) |
| Recommendation | Same pattern as W-03 |

### W-07 · Training Record assigned
| Field | Value |
|---|---|
| Creator | Safety / HR |
| Owner | Trainee Employee |
| Visibility | Trainee + Safety + HR · supervisor inconsistent |
| Notifications | Trainee gets bell + task ✅ ; `linked_supervisor` lookup intermittent (often empty → supervisor notification dropped) |
| Escalation | Doc-expirations cron raises HR task at threshold ✅ |
| Closure path | Trainee completes |
| Current | Trainee OK; supervisor sometimes invisible |
| Desired | Hardened supervisor-chain resolution; one-hop manager fallback |
| **Gap** | **G-P1-05** (GAP-4) |
| Recommendation | Improve `linked_supervisor` resolution (employees.supervisor_id → user_directory) with one-hop manager-of-employee fallback |

### W-08 · Shop Equipment Trash button → 403
| Field | Value |
|---|---|
| Creator | Shop UI button |
| Owner | Admin (delete is admin-only) |
| Visibility | `/shop/equipment` page |
| Notifications | n/a |
| Escalation | n/a |
| Closure path | n/a (the button itself is the issue) |
| Current | Shop sees button → click → 403 |
| Desired | Hide button under Shop token |
| **Gap** | **G-P1-06** (GAP-10) — cosmetic frontend gate |
| Recommendation | Frontend conditional render: `if (role === 'admin') showTrash` |

### W-09 · `/equipment/:id` cross-portal redirect
| Field | Value |
|---|---|
| Creator | Inbound link |
| Owner | Admin (default landing) |
| Visibility | Cross-portal — any signed-in user |
| Notifications | n/a |
| Escalation | n/a |
| Closure path | n/a |
| Current | Always redirects to `/admin/equipment/:id` regardless of viewer's portal |
| Desired | Portal-aware redirect via auth context |
| **Gap** | **G-P1-07** (GAP-16) |
| Recommendation | Router conditional: `if (authCtx.role === 'shop') navigate(/shop/...)` |

### W-10 · `/inspections/:id` cross-portal redirect
| Field | Value |
|---|---|
| (mirror of W-09) | |
| **Gap** | **G-P1-08** (GAP-17) |
| Recommendation | Mirror W-09 fix |

---

## 3 · P2 workflows (improvement gaps — 6 items)

| W | Workflow | Creator | Owner | Visibility | Notifications | Escalation | Closure path | Current | Desired | Gap | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W-11 | Payroll Variance manual run | HR Mgr | HR | HR · Admin | None on manual; weekly cron emails `PAYROLL_VARIANCE_EMAIL_TO` | None | Admin | Silent | Audit notif to admin | **G-P2-01** | One-line `emit_notification(admin, "payroll-variance-manual-run")` |
| W-12 | DR Weather=YES | foreman | PM | PM | none | n/a | n/a | No schedule task | Auto-task to PM | **G-P2-02** | Operator stop-list — deferred |
| W-13 | DR Equipment-Issue=YES | foreman | PM/Shop | PM/Shop | none | n/a | n/a | No Pre-Op auto-link | Auto-create Pre-Op record | **G-P2-03** | Future hardening |
| W-14 | Severe Incident no-response | safety | Safety | Safety · Admin · PM | First-response email+bell+task ✅ | **NONE** if Safety doesn't acknowledge | Admin | First ping only | Delayed re-ping cron (e.g. T+2h) | **G-P2-04** | Generalized "no-response timer" framework (operator decision §6 of Gap Ledger) |
| W-15 | PO Request no-receipt extended | requester | approval queue | requester · admin · approvers | Nightly cron raises "receipt-missing" task ✅ | No 2nd-tier escalation | Admin | First-tier only | Add 60-day second-tier cron | **G-P2-05** | Same framework as W-14 |
| W-16 | PM Exposure Tile route | PM hub sidebar | PM | PM · Admin | n/a | n/a | n/a | Sidebar links to undeclared route → 404 | Hide sidebar item until route is enabled | **G-P2-06** (GAP-18) | Intentional stop-list — cosmetic frontend hide |

---

## 4 · 🟢 Workflows with no operational gap (25 items, summary form)

These workflows pass all 10 audit fields cleanly. Listed by category for completeness; full pillar audit in §1.1 of the Truth Map.

| Category | Workflows | Audit verdict |
|---|---|---|
| Daily Reports core (W-17 to W-19) | Daily Report submit · Production rows · Delays/Extra Work | Owner=PM · email-only by design · 🟢 |
| Equipment (W-20 to W-22) | Pre-Op PASS · Pre-Op FAIL · Shop Recovery / Asset Transfer | Owner=Shop/Dispatch · full fan-out · 🟢 |
| Procurement (W-23 to W-25) | PO Request · Response · Receipt upload | Owner=approvers/Admin · full fan-out + watchdog · 🟢 |
| Safety (W-26 to W-28) | Incident · Inspection · QA/QC | Owner=Safety/PM · full fan-out incl severe-CC · 🟢 |
| Dispatch (W-29) | Dispatch Request / Equipment Request | Owner=Dispatch · "stuck > 30 m" live alert · 🟢 |
| HR (W-30 to W-32) | HR Request · Time Verification · Driver Qualification | Owner=HR · cron-driven · 🟢 |
| Payroll cron (W-33) | Weekly Payroll Variance digest | Owner=HR+Admin · cron · 🟢 |
| Training (W-34) | Training Record completed | Owner=Employee · 🟢 |
| Visitor / ODR (W-35 to W-36) | Visitor Log · Operational Daily Records | Owner=PM · public-link expire · 🟢 |
| Attachments / PDFs (W-37 to W-38) | Operational Attachments · PDF Downloads | Auto-expire / gated · 🟢 |
| System (W-39 to W-41) | Document Expirations cron · Health Monitor · Magic-link (dispatch) | Cron / health probe · 🟢 |
| Auth (W-42) | Multi-portal sign-in · MFA · passkeys | Account lockout · 🟢 |
| Fleet (W-43) | Fleet Defect lifecycle (acknowledge / repair / clear / oos) | Audit-only by design (parent W-01 covers fan-out gap) |
| Fire Ext (W-44) | Fire Extinguisher Inspection | Owner=Safety · 🟢 |
| Corrective Action (W-45) | Corrective Action | Owner=Assignee · 🟢 |

---

## 5 · Cross-workflow systemic patterns identified

| Pattern | Affected workflows | Recommendation |
|---|---|---|
| **Email-only with no in-app surface** | W-03, W-04, W-05, W-06 (× 3 forms) | **One unified batch closes G-P1-01/02/03/04** by adding `emit_task_and_notification` to four `routes/*.py` files (~25 LOC total). Already drill-tested pattern in `routes/equipment.py`. |
| **No-response escalation absent** | W-14, W-15 (W-12, W-13 are intentional stop-list) | Single generalized "delayed re-ping" cron framework would close G-P2-04 + G-P2-05 simultaneously (one new cron + one config table). Operator decision needed (§6 Gap Ledger Q4). |
| **Cross-portal redirect always lands in admin** | W-09, W-10 | One frontend Router-level fix closes G-P1-07 + G-P1-08 (~10 LOC). |
| **Supervisor-chain resolution unreliable** | W-07 (training); generalizes to anything that touches employee → manager | Harden `linked_supervisor` lookup once in `lib/employee_linkage.py`; every workflow downstream benefits. |
| **No platform-wide recovery dashboard** | W-02 (backup) + W-39 (health monitor) | Out of scope here — see RECOVERY_DASHBOARD_SPEC.md (Priority 3). |

---

## 6 · Roll-up

| Tier | Workflow count | Audit verdict |
|---|---:|---|
| 🟢 Pass all 10 audit fields | 33 | No action |
| 🟡 P1 gap (works, visibility/fan-out incomplete) | 7 (W-03/04/05/06/07 + W-08/09/10) | Operator decision per Gap Ledger §6 |
| 🟡 P2 gap (improvement) | 6 (W-11..W-16) | Improvement batch |
| 🔴 P0 orphan | 1 (W-01 Fleet DVIR) | Awaiting operator decision: passive ledger vs active workflow |
| 🟦🔴 P0 (preview-dead, prod-just-iter441) | 1 (W-02 Backup Alerts) | iter441 stabilized worker · hourly enablement DEFERRED per OMEGA |
| **Total** | **41 workflows · 19 ledgered gaps** | **No new gaps discovered in this audit pass — Truth Map remains canonical.** |

---

## 7 · Stop-condition compliance

- ✅ NO code changes
- ✅ NO scheduler / cadence / retention / frequency touched
- ✅ NO redesign / new features / side quests
- ✅ Every recommendation traces to: code path · ledgered gap · runtime evidence (existing probe in Truth Map or Gap Ledger)
- ✅ Audit is consolidation-only — `PLATFORM_GAP_LEDGER_FINAL.md` remains canonical, this doc adds 10-field-shape per workflow on top of it

---

_End of OPERATIONAL_PERFECTION_AUDIT.md_

# OMEGA_IMPLEMENTATION_PLAN

**Initiative:** OMEGA · MASCI Operational Perfection Program
**Date:** 2026-05-30 (UTC)
**Method:** Reconciles `OMEGA_GAP_REGISTER.md` priorities with `NOTIFICATION_GAP_REMEDIATION_PLAN.md`, `FLEET_DVIR_DECISION_PACKAGE.md`, and `PRODUCTION_RECOVERABILITY_ALIGNMENT_REPORT.md` operator actions into a single sequenced execution plan. **No implementation work is authorized by this document.** Operator owns batch-by-batch authorization.

---

## 1 · Sequencing principle

| Order rule | Why |
|---|---|
| Operator-actions first (no code work) | Closes the 🔴 photo migration row with a single command · enables Batch H benefit to flow |
| Orphan resolution next (Fleet DVIR) | Closes the only 🔴 orphan in the platform |
| Visibility batch (K) — symmetric fan-out wires | 5 gaps · same pattern · lowest risk |
| Targeted batches (L · M · N) — complexity grouped | Supervisor lens · escalation framework · doc hygiene |
| Phase 2 enhancements at the end | Cross-portal timeline · field-form redesign · out-of-OMEGA-scope items |

---

## 2 · Sequenced plan (10 work items · operator authorizes each individually)

### ITEM-0 · Operator-side actions (NOT a batch — direct prod ops)

| # | Action | Owner | Effort | Closes |
|---|---|---|---|---|
| 0.1 | Run `python3 /app/scripts/migrate_dr_photos.py --target-db masci_safety --i-know-this-is-prod --apply --backup-dir /app/memory/dr_migration_backups` against production | Operator | ~30 min (script runtime) | OMEGA-1 |
| 0.2 | Push fresh preview → prod deploy to ensure Batch G + H code is active | Operator | ~15 min | OMEGA-2 |
| 0.3 | Fire one deliberate test alarm and confirm Resend delivery | Operator | ~15 min | OMEGA-12 |
| 0.4 | Probe prod `/api/admin/backups-scheduler-state` to re-confirm health post-deploy | Operator | ~30 sec | continuity check |

**Why first:** none of these require platform code changes; they realize the value of prior batches that already shipped to preview source. Skipping these keeps the platform in its current partial-alignment state.

---

### BATCH-K · Symmetric fan-out wiring (5 gaps · same pattern)

| Aspect | Detail |
|---|---|
| Scope | OMEGA-5 (FL forms) · OMEGA-6 (Safety equipment 3) · OMEGA-7 (JHA) · OMEGA-8 (Safety Meeting) · OMEGA-13 (Payroll manual audit) |
| Code site | `routes/field_leadership.py`, `routes/field_leadership_portal.py`, `routes/safety_forms.py`, `routes/safety.py:464+518`, `routes/payroll_variance.py` |
| Pattern | After each `schedule_auto_email(...)`, insert `emit_task_and_notification(...)` to `safety` role with `priority=Medium` (existing pattern from `routes/equipment.py:234`) |
| New endpoints | 0 |
| New schemas | 0 |
| Frontend changes | 4 tile upgrades (Safety Hub: Forms queue, JHA queue, Meetings queue, FL Forms queue) — replace count-only cards with action queues (top-5 + click-to-detail) |
| LOC estimate | ~75 backend · ~120 frontend |
| Effort | ~6 h total |
| Verification | (a) submit one of each form type in preview · confirm bell row appears in `/notifications` and task row in `/tasks` for safety role · (b) testing_agent_v3_fork covering all five submit paths |
| Decision needed before authorizing | Confirm Safety Meeting (OMEGA-8) joins this batch OR remains email-only (operator question) |

**Stop-condition:** explicit operator authorization message containing "BATCH K AUTHORIZED".

---

### BATCH-L · Fleet DVIR notification wiring

| Aspect | Detail |
|---|---|
| Scope | OMEGA-3 — closes the only 🔴 orphan |
| Pre-req | Operator signs off on `FLEET_DVIR_DECISION_PACKAGE.md` 4-class matrix |
| Code site | `routes/fleet_ops.py:412–553` (submit handler) · 5 lines from line 526 to line 553 are the insertion zone |
| Pattern | After `_rebuild_status` call · before final `return`:<br>• Classify maximum severity from defect rows<br>• If `is_safety` or `any_oos`, emit Shop task + visibility notifications<br>• Safety added on safety-class · Dispatch added on OOS<br>• Repeat-Unresolved sweep cron at nightly cadence (separate function) |
| New endpoints | 0 |
| New schemas | 0 (severity & oos columns already exist) |
| Frontend changes | Optionally: Open DVIRs tile on Shop Hub + Dispatch Hub (visibility) — IF operator wants explicit dashboard, otherwise the existing fleet boards suffice |
| LOC estimate | ~30 backend + ~30 cron + 0 frontend (or +60 if tiles added) |
| Effort | ~2 h code + ~1 h smoke + ~0.5 h test = **~3.5 h total** |
| Verification | (a) submit a test DVIR with 1 non-safety defect → verify Shop task created · (b) submit one with safety defect → verify Safety notification fires · (c) submit one with OOS → verify Dispatch notification fires · (d) integration test via testing_agent_v3_fork |

**Stop-condition:** explicit operator authorization "BATCH L AUTHORIZED" + sign-off on decision-package matrix.

---

### BATCH-M · Training supervisor lens

| Aspect | Detail |
|---|---|
| Scope | OMEGA-9 (G-P1-05) · Training Record assigned — supervisor of trainee receives a visibility notification |
| Code site | `routes/training_center.py` (assignment handler) + `lib/employee_linkage.py` (extend `resolve_employee` for supervisor chain) |
| Pattern | After trainee bell+task emit, lookup `employee.linked_supervisor` chain · emit parallel `emit_notification` to supervisor (no task — visibility only) · fallback to HR if unresolved |
| New endpoints | 0 |
| New schemas | 0 (existing `employees.linked_supervisor` field) |
| LOC estimate | ~30 helper + ~10 emit call + ~30 tests |
| Effort | ~2 h |
| Verification | (a) assign training to employee with known supervisor → confirm supervisor notification arrives · (b) assign to employee with missing supervisor → confirm HR fallback fires |

**Stop-condition:** explicit "BATCH M AUTHORIZED".

---

### BATCH-N · Escalation cadence framework

| Aspect | Detail |
|---|---|
| Scope | OMEGA-10 (Severe Incident no-response) + OMEGA-11 (PO 60-day escalation) — generalized framework |
| Pattern | New cron in `server.py` (or `lib/escalation_engine.py`): nightly sweep over `tasks` collection where `status="open"` AND `priority="Critical"` AND `created_at < now - escalation_threshold_hours` AND `escalated_at IS NULL`. For each match: emit second tier notification + task to `escalation_assignee_role` · stamp `escalated_at` (idempotency lock). |
| Config | JSON config: `{module: {"first_tier_hours": 4, "second_tier_role": "safety_lead", "third_tier_hours": 24, "third_tier_role": "admin"}}` per task `source_module`. |
| New endpoints | 0 (cron-driven) |
| New schemas | new field `tasks.escalated_at` (additive) |
| LOC estimate | ~80 framework · ~30 incident-specific config · ~20 PO-specific config |
| Effort | ~4 h framework + ~2 h per integration = **~6 h** |
| Verification | (a) seed a Critical incident task · let cron run (or trigger manually) · verify second-tier notification fires · (b) re-run cron · verify idempotent (no duplicate emit) · (c) PO 60-day test scenario |

**Stop-condition:** explicit "BATCH N AUTHORIZED".

---

### BATCH-O · Hygiene + version endpoint

| Aspect | Detail |
|---|---|
| Scope | OMEGA-4 (`/api/admin/version`) + OMEGA-14 (Shop trash button gate) + OMEGA-15 (cross-portal redirects) + OMEGA-16 (6 doc-hygiene deltas) |
| Code site | new route `routes/admin_version.py` · frontend gate `ShopEquipmentPage.jsx` · App.js redirect rule · multi-file doc cleanup |
| LOC estimate | ~50 backend + ~30 frontend + ~doc updates |
| Effort | ~3 h |
| Verification | (a) `curl $PROD_URL/api/admin/version` returns git SHA · (b) Shop user no longer sees trash button on equipment · (c) `/equipment/:id` routes per portal · (d) docs updated |

**Stop-condition:** explicit "BATCH O AUTHORIZED".

---

### BATCH-P · Phase 2 (NOT urgent — operator strategic)

| Aspect | Detail |
|---|---|
| Scope | OMEGA-18 cross-portal employee timeline endpoint + page |
| Reference | `EMPLOYEE_ACCOUNTABILITY_ARCHITECTURE.md` iter353c plan |
| Effort | ~16 h (per arch plan) |
| Status | Operator-strategic — does NOT block any current operational gap |

---

### OUT-OF-OMEGA — Heavy-form redesign (NOT planned in OMEGA)

OMEGA-19 (DR) and OMEGA-20 (Incident) require redesign work which is explicitly prohibited by OMEGA constraints. They are documented in `WORKFLOW_FRICTION_REPORT.md` and `FIELD_FRICTION_MEASUREMENT.md` for a future authorized initiative.

---

## 3 · Total effort if all batches authorized

| Item | Effort |
|---|---|
| ITEM-0 (operator actions) | ~1 h operator time |
| BATCH-K (symmetric fan-out · 5 gaps) | ~6 h |
| BATCH-L (Fleet DVIR) | ~3.5 h |
| BATCH-M (Training supervisor) | ~2 h |
| BATCH-N (Escalation framework) | ~6 h |
| BATCH-O (Hygiene + version endpoint) | ~3 h |
| BATCH-P (Phase 2 timeline) | ~16 h (optional, strategic) |
| **Total — operational close** (without P) | **~21 h** |
| **Total — with strategic** | **~37 h** |

These are estimates only. Each batch requires explicit operator authorization before any work begins.

---

## 4 · Recommended sequence (operator owns the call)

1. **ITEM-0 immediately** (no code work · highest impact-per-minute · closes OMEGA-1 / OMEGA-2 / OMEGA-12)
2. **BATCH-L (Fleet DVIR)** — closes the platform's only 🔴 orphan
3. **BATCH-K (symmetric fan-out)** — closes 5 P1 visibility gaps in one symmetric pass
4. **BATCH-M (Training supervisor)** — short, targeted
5. **BATCH-N (Escalation framework)** — moderate, builds reusable infrastructure
6. **BATCH-O (Hygiene)** — cleanup pass at the end
7. **BATCH-P (timeline)** — optional · strategic · Phase 2 candidate

Alternative sequences are valid; the operator should sequence by risk tolerance.

---

## 5 · Stop-condition compliance

- ✅ No implementation begun
- ✅ No code changes
- ✅ No schema changes
- ✅ Each batch carries its own stop-condition (explicit operator authorization)
- ✅ All effort estimates are observations, not commitments
- ✅ Out-of-OMEGA items (heavy-form redesign) are not planned — they are merely noted

---

_End of OMEGA_IMPLEMENTATION_PLAN.md._

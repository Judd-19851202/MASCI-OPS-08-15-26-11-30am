# Final Phase A Recommendation — Slim Executive Command Center (Pillar 2)

**Classification:** OMEGA Pillar 2 · RECOMMENDATION ONLY · No code · No DB · No endpoints · No UI
**Generated:** 2026-05-31 UTC
**Author:** E1
**Audience:** Operations Leadership (Jaymn) · future implementation agent (once authorized)
**Status:** Awaiting operator response to `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` before any code is written.
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_DESIGN_REVIEW.md` · `EXECUTIVE_COMMAND_CENTER_RISK_ANALYSIS.md` · `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md`

---

## 1 · The Recommendation in One Line

> **Ship a slim, defensible Phase A: 5 high-confidence cards + Pulse Strip · no Priority Stack · no load cards · no bottleneck card · ~1,000 LOC including tests · 1 new collection · 3 new endpoints · 2 new pages.**

This is **smaller, sharper, and more defensible** than the 7-card Phase A in the original blueprint.

---

## 2 · KEEP / MODIFY / REMOVE — Final Disposition

| # | Original card | Final disposition | Phase A scope notes |
|---|---|---|---|
| 1 | Jobs Today | **MODIFY · KEEP** | Drop JOBS-3 (orphan project) entirely · Make JOBS-1 weekday/PTO-aware via Q-5 calendar config · Drop JOBS-2 (rolls up to Safety card instead) |
| 2 | Safety Today | **KEEP** | Gate SAF-4 on active projects (DR-active in last 7 days) · Add SAF-1b (any open severity=high regardless of age) · Add SAF-3b (compliance finding open >60 days) |
| 3 | Equipment Today | **KEEP** | Consolidate EQP-1 + EQP-4 into one rule · Whitelist EQP-3 reason codes · Add age modifier to EQP-2 critical-defect rule |
| 4 | Accountability Overdue | **MODIFY · KEEP** | Remove ACC-3 entirely · Filter to `priority ∈ {high, critical}` tasks · Raise thresholds (was 5/15, now 10/25) |
| 5 | PM Load | **REMOVE from Phase A** | Defer to Phase C (per-PM filtered lens) · No load cards in executive view |
| 6 | Supervisor Load | **REMOVE from Phase A** | Same as Card 5 · belongs to Phase C |
| 7 | Approvals Aging | **MODIFY · KEEP** | Operator-set thresholds via Q-7 · Dollar-weight deferred to Phase B (Q-8) · APP-4 dropped (already handled by existing `po_digest_admin` cron) |
| 8 | Projects at Risk | **DEFER to Phase B** | Composite-of-composites premature without working-day calendar + P&L audit |
| 9 | Operational Bottlenecks | **REMOVE from Phase A** | 3/5 rules acknowledged duplicates · 2/5 weak baseline · no unique signal |
| 10 | Recommender / Priority Stack | **DEFER to Phase B** | Per Q-2 default · Phase A has no algorithmic ranking · leadership prioritizes manually from 5 cards |
| **NEW** | **Expirations (MX-3)** | **ADD to Phase A (gated on Q-3 audit)** | Document expirations card: CDL/insurance/training/cert expiring in N days |

**Phase A card count: 5** (Jobs · Safety · Equipment · Accountability · Approvals) + **Pulse Strip** + **conditional 6th card** (Expirations · gated on Q-3 audit).

---

## 3 · Final Slim Phase A Composition

### 3.1 What ships

```
┌─────────────────────────────────────────────────────────────────────┐
│ PULSE STRIP (5-sec view) — overall RAG · counts · last refresh     │
└─────────────────────────────────────────────────────────────────────┘
┌───────────────┬───────────────┬───────────────┐
│  1. Jobs      │  2. Safety    │  3. Equipment │
│     Today     │     Today     │     Today     │
└───────────────┴───────────────┴───────────────┘
┌───────────────┬───────────────┬───────────────┐
│ 4. Account-   │ 5. Approvals  │ 6. Expirations │ ← conditional · gated on Q-3 data audit
│    ability   │    Aging      │ (NEW · MX-3)  │
└───────────────┴───────────────┴───────────────┘
```

**No Priority Stack. No PM Load. No Supervisor Load. No Projects-at-Risk. No Bottlenecks. No Recommender.**

### 3.2 What ships at the API surface

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/admin/command-center/snapshot` | GET | admin-strict (super_admin per Q-14) | Returns the full 5-card + Pulse Strip JSON |
| `/api/admin/command-center/thresholds` | GET · PATCH | super_admin (per Q-15) · audit-logged (per Q-16) | Read/edit `command_center_thresholds` config doc |
| `/api/admin/command-center/calendar` | GET · PATCH | super_admin (per Q-5 option b) | Read/edit `command_center_calendar` config doc (working hours · holidays) |

**Total new endpoints: 3.** All read-only or config-write. **Zero data-write endpoints. Zero notification endpoints.**

### 3.3 What ships at the UI surface

| Page | Auth | Purpose |
|---|---|---|
| `/admin/command-center` | super_admin | Single-glass dashboard (Pulse Strip + 5–6 cards) |
| `/admin/command-center/thresholds` | super_admin | Tune RAG thresholds + working calendar |

**Total new pages: 2.** No mobile/tablet (per Q-11 default).

### 3.4 What ships at the database surface

| Collection | Purpose | Documents |
|---|---|---|
| `command_center_thresholds` | All RAG thresholds for the 5 (or 6) cards | 1 doc |
| `command_center_calendar` | Working hours + named holidays (Q-5 option b) | 1 doc |

**Total new collections: 2.** Zero schema changes to existing collections.

### 3.5 What ships at the test surface

| File | Coverage |
|---|---|
| `tests/test_command_center_snapshot.py` | Snapshot endpoint returns correct RAG state for 5 cards under each of GREEN/AMBER/RED synthetic scenarios |
| `tests/test_command_center_thresholds.py` | Threshold round-trip · audit log entry per change · version field optimistic locking |
| `tests/test_command_center_calendar.py` | Calendar respect for weekends · holidays · working-hour boundaries |
| `tests/test_command_center_rbac.py` | Non-super-admin tokens denied · drill-down endpoints respect existing per-collection RBAC |
| `tests/test_command_center_ojectid_leak.py` | No `_id` leakage in snapshot or threshold responses (continuing platform-wide contract) |

**Total: 5 pytest files** covering acceptance criteria §A.3.

---

## 4 · Operational Risk After Slim Phase A

Re-applying the risk inventory after this recommendation:

| Risk | Count in original blueprint | Count in slim Phase A |
|---|---|---|
| Missing executive questions | 8 unaddressed | 7 deferred · 1 added (MX-3) |
| Duplicate widgets | 6 | **0** |
| Low-value widgets | 6 | **0** |
| Noise generators | 5 | **0** |
| Unreliable data sources | 8 critical | **2 with explicit mitigations** |
| False-positive scenarios | 7 high-frequency | **1** (low-dollar PO; gated on Q-8) |
| False-negative scenarios | 7 | **3 closed** (SAF-1b, SAF-3b, MX-3) · 4 deferred |
| Operational adoption risks | 7 | **All mitigated** via slim scope |
| Architecture risks | 5 | **All mitigated** in roadmap §A.4 |
| OMEGA backup-freeze violation surface | low (separate file) | **0** (new file only, no edits to recovery_dashboard.py / singleton_scheduler.py) |

---

## 5 · Phase A Implementation Footprint (final)

| Surface | Estimate | Notes |
|---|---|---|
| New backend file | `routes/command_center.py` | ~200 LOC (down from blueprint's 250–350) |
| New backend tests | 5 pytest files | ~500 LOC total |
| New frontend pages | 2 jsx pages | ~400 LOC total (Command Center page · Thresholds + Calendar page) |
| Edits to existing | `server.py` router-include (1 line) · `AdminHub.jsx` (1 tile) · `_INDEX.md` + `PRD.md` entries (memory) | < 30 LOC |
| New DB collections | 2 (`command_center_thresholds`, `command_center_calendar`) | seeded with 1 doc each |
| New endpoints | 3 (snapshot · thresholds · calendar) | all admin-strict GET/PATCH |
| **Total** | **~1,150 LOC including tests** | **down from original 1,500 LOC estimate** |

---

## 6 · Acceptance Criteria for Slim Phase A (final · supersedes blueprint §A.3)

Implementation closeout requires evidence on every item below:

1. ✅ Pulse Strip renders within 2 sec p95 (preview + prod).
2. ✅ Each of the 5 (or 6) cards correctly transitions GREEN/AMBER/RED under synthetic test data (pytest).
3. ✅ `warnings[]` array populated for every fired rule with `{rule_id, item_count, item_ids[], owner, drill_to}`.
4. ✅ Threshold edits round-trip and recompute snapshot in ≤ 60 sec.
5. ✅ Calendar edits round-trip and immediately affect weekday-aware rule evaluation.
6. ✅ Snapshot endpoint p95 < 1.5 sec (preview).
7. ✅ ZERO new collections beyond `command_center_thresholds` + `command_center_calendar`.
8. ✅ ZERO modifications to existing collection schemas.
9. ✅ ZERO notifications/emails/tasks emitted by Phase A code (grep verification on `routes/command_center.py`).
10. ✅ ZERO edits to `routes/recovery_dashboard.py` · `lib/singleton_scheduler.py` · `server.py` archive code (OMEGA backup-freeze).
11. ✅ Pilot users (per Q-12) self-report ≤ 5 min to identify daily priorities (down from ≥ 60 min baseline).
12. ✅ Audit-log entry written to `admin_audit` for every threshold/calendar change (per Q-16).
13. ✅ No `_id` leakage in any response (platform contract continues).
14. ✅ ruff + ESLint clean.
15. ✅ Closeout report `PILLAR_2_PHASE_A_CLOSEOUT.md` produced with all the above evidenced.

---

## 7 · Stop Conditions (final · supersedes blueprint §A.4)

The Phase A implementation MUST halt immediately if any of the following occur:

- 🔴 An attempt to write to `routes/recovery_dashboard.py`, `lib/singleton_scheduler.py`, or backup-related code paths.
- 🔴 Net-new collection beyond `command_center_thresholds` + `command_center_calendar`.
- 🔴 Any call to `emit_notification`, `schedule_auto_email`, `task_service.create`, `notification_service.fanout`, or any other fan-out helper from `routes/command_center.py`.
- 🔴 Any modification to an existing collection's schema.
- 🔴 ESLint or ruff error introduced anywhere outside `command_center*` files.
- 🔴 Snapshot endpoint p95 > 5 sec in preview (compute discipline).
- 🔴 Operator-blocking question (per `OPERATOR_CHALLENGE.md` §6) answered by guess instead of by operator.

Any stop triggers an immediate partial report under `/app/memory/PILLAR_2_PHASE_A_STOP_REPORT.md` and the agent waits for operator review.

---

## 8 · Decision Required From Operator (before Phase A starts)

Before any implementation batch is authorized, operator must answer (or accept defaults on) the **11 hard-blocking** questions in `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` §6:

```
Q-1  PM/Supervisor load — REMOVE confirmed? (default: yes)
Q-2  Recommender phase — Phase B confirmed? (default: yes)
Q-3  Expirations data — audit before Phase A? (default: yes)
Q-4  Projects-at-Risk — Phase B confirmed? (default: yes)
Q-5  Calendar source — operator-managed config? (default: option b)
Q-6  Severity calibration — audit before pilot? (default: yes)
Q-7  PO SLA — what are MASCI's AMBER/RED days? (default: 3/5 with tuner exposed)
Q-9  Pulse vs Backup — separate? (default: yes, separate)
Q-12 Pilot user names — provide 3–5 names (no default acceptable)
Q-14 Executive role — super_admin only? (default: yes)
Q-15 Threshold tuner — super_admin only? (default: yes)
```

If the operator authorizes Phase A with all defaults accepted (and provides Q-12 pilot names), implementation can begin in the next batch.

---

## 9 · What the Operator is Signing Off On

Approving this recommendation means agreeing to the following Phase A contract:

- **Cards delivered:** Jobs Today · Safety Today · Equipment Today · Accountability Overdue · Approvals Aging · (conditionally) Expirations.
- **Cards NOT delivered:** PM Load · Supervisor Load · Projects at Risk · Operational Bottlenecks · Recommender / Priority Stack.
- **Composition:** Pulse Strip on top · 5–6 cards in a 3-wide grid · drill-to-existing-detail-pages only · no mobile.
- **Configurability:** thresholds + calendar live in 2 DB config docs · tunable by super_admin via dedicated admin page · every change audit-logged.
- **Pilot:** 4-week pilot (per Q-17 default) with named users (per Q-12) · gating evidence for Phase B authorization.
- **Frozen surface:** `recovery_dashboard.py` · `singleton_scheduler.py` · backup archive code remain untouched.
- **Pillar 4 separation:** zero notifications · zero emails · zero tasks emitted from Phase A code.

---

## 10 · The One-Sentence Headline

> **The Executive Command Center, in Phase A, is five honest cards and one Pulse Strip — built from existing data, scored by tunable rules, drilling into existing detail pages, emitting zero new signals, and shipping in ~1,150 LOC.**

That is what gets built. Everything else is deferred to Phase B/C or removed.

---

## 11 · Status

🔴 **STOPPED.** No code authorized. The agent will not write `routes/command_center.py` or any related file until:
1. Operator reviews and approves this recommendation, AND
2. Operator answers (or accepts defaults on) the 11 hard-blocking questions in `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md`, AND
3. Operator authorizes Phase A as the next batch with restated 5 mandatory pillar inputs.

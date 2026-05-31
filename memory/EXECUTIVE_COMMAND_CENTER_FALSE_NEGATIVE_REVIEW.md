# Executive Command Center — False Negative Review

**Classification:** OMEGA Pillar 2 · Phase A · Pre-Production Read-Only Review
**Generated:** 2026-05-31 UTC
**Author:** E1
**Scope:** Catalog every scenario in which a real operational issue exists but Phase A fails to surface it.
**Companion doc:** `EXECUTIVE_COMMAND_CENTER_FALSE_POSITIVE_REVIEW.md`

---

## 1 · Definition

**False Negative (FN):** the dashboard shows GREEN (or under-counts) for a condition that is actually causing or threatening operational harm. FN is **strictly more dangerous than FP** in an executive dashboard — leadership cannot act on what they cannot see.

---

## 2 · Inventory

### FN-1 · Approvals & Equipment sub-counts silently zero (Defect D5) 🔴 HIGHEST PRIORITY

| Property | Value |
|---|---|
| Rules affected | APP-AMBER, APP-RED, APP-WEEK · EQP-OOS-OLD, EQP-OOS-NEW |
| Mechanism | `count_documents` queries pass cutoff times as ISO strings (`(now - timedelta(days=N)).isoformat()`). If the stored `created_at` field is a BSON `datetime` object (not an ISO string), the comparison can silently match zero documents. The items list uses `_parse_ts()` which handles both forms and correctly identifies aged docs — proving the data exists. |
| Live evidence | Approvals card: `pill=GREEN`, `warnings=0`, but `items=5` listing POs aged 3+ days that should fire AMBER/RED. Equipment card: `oos_red=0`, `oos_amber=0` despite a 44-unit total backlog. |
| Operational impact | An executive looking at the dashboard sees "All clear · approvals aging" while one of those silent POs may be the $50K material order that's blocking a project. **This is the most dangerous failure mode in Phase A.** |
| Severity | 🔴 HIGH |
| Remediation (D5) | One coercion helper used by all `count_documents` date filters: `{"$lte": {"$or": [cutoff_iso, _parse_to_datetime(cutoff_iso)]}}` won't work directly — Mongo doesn't support `$or` inside an operator value. Cleaner fix: convert ALL date comparisons to use `datetime` objects (Motor converts) and let MongoDB do BSON-aware comparison. ~20 LOC. |

### FN-2 · Tasks without `due_at` are invisible to accountability

| Property | Value |
|---|---|
| Rule | ACC-HIGH-OVERDUE, ACC-STALE |
| Mechanism | Filter requires `due_at: {"$ne": None, "$lt": now_iso}`. Any high/critical task that was created without a `due_at` value never appears in the overdue count. |
| Live evidence | Accountability card is currently GREEN — but this could be GREEN-because-no-tasks OR GREEN-because-no-task-has-a-due_at. Cannot distinguish from snapshot alone. |
| Expected frequency | Depends on `tasks` workflow hygiene — some submitters likely create tasks without due dates. |
| Severity | 🟡 MEDIUM |
| Remediation | Either treat missing `due_at` as "needs triage" (own rule firing AMBER), or surface "tasks without due_at" as a separate counter on the card. Deferred to Phase B input-hardening or operator decision. |

### FN-3 · Document expirations not surfaced

| Property | Value |
|---|---|
| Rule | None — card not built |
| Mechanism | The Expirations card (MX-3) was deferred per `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` Q-3 pending a data-coverage audit of the `document_expirations` collection. A driver's CDL, fleet insurance, or required certificate expiring tomorrow is invisible to Phase A. |
| Operational impact | An expired CDL stops a driver; an expired insurance certificate stops a project. Currently no executive surface for this. |
| Severity | 🟡 MEDIUM (acknowledged Phase B gap) |
| Remediation | Phase B Expirations card after data audit. |

### FN-4 · Compound failures not consolidated

| Property | Value |
|---|---|
| Rule | None — no recommender, no project rollup |
| Mechanism | A single job that has (a) no DR today + (b) an open critical incident + (c) an OOS unit assigned to it would currently fire as 3 separate signals on 3 different cards. Leadership has to mentally correlate them to see "Project X is in trouble." |
| Live evidence | Cannot be directly observed without project-level rollup. |
| Severity | 🟡 MEDIUM (Phase B Projects-at-Risk card) |
| Remediation | Phase B Projects-at-Risk card per `EXECUTIVE_IMPLEMENTATION_ROADMAP.md`. |

### FN-5 · Severity miscategorization

| Property | Value |
|---|---|
| Rule | SAF-CRITICAL-UNRESOLVED |
| Mechanism | If an actually-serious incident is logged with `severity = "Minor"` or `"Warning"` (operator-entered free-text), it never appears on the Safety card. |
| Live evidence | Cannot detect from snapshot; requires data audit. |
| Severity | 🟡 LOW-MEDIUM (mitigation: Phase B description-keyword detection as a backstop) |
| Remediation | Add SAF-KEYWORD-SCAN rule that flags any incident mentioning "OSHA", "hospital", "EMS", "amputation", "fatality" regardless of severity field. Deferred to Phase B. |

### FN-6 · Financial / customer / schedule signals out of scope

| Property | Value |
|---|---|
| Rule | None — by design (Phase A scope) |
| Categories missed | AR aging · cash position · project margin · client RFIs · change orders · client complaints · schedule milestones · critical-path slippage |
| Severity | 🟡 LOW-MEDIUM (acknowledged scope · Phase B/C) |
| Remediation | Phase B/C per `EXECUTIVE_COMMAND_CENTER_RISK_ANALYSIS.md` §1. |

### FN-7 · OSHA recordable flag text variation

| Property | Value |
|---|---|
| Rule | SAF-OSHA-OPEN |
| Mechanism | The regex filter `^Yes$` (case-insensitive) matches "Yes", "yes", "YES" but NOT: `"Y"`, `"y"`, boolean `true`, `"true"`, `"TRUE"`, `"YES "` (trailing space). If submitters use any of those alternates, the incident is missed. |
| Live evidence | Cannot detect from snapshot alone. |
| Severity | 🟢 LOW (mitigation: input normalization at submit time) |
| Remediation | Phase B input-hardening — normalize `osha_recordable` to lowercase trimmed string at write time. |

### FN-8 · Backup/recoverability not on Pulse Strip

| Property | Value |
|---|---|
| Rule | None — by design |
| Mechanism | The Pulse Strip composes only the 5 operational cards. `/admin/recovery/snapshot.pill` is currently AMBER (R2 bucket usage + RTO no-drill) but does not influence Pulse. |
| Operational impact | An infrastructure-class issue (e.g., backup scheduler crashed) would not appear on the operations command center. |
| Severity | 🟢 NEGLIGIBLE (intentional separation — operator's Q-9 default) |
| Remediation | n/a · operator chose separation; backup health lives on `/admin/recovery` |

### FN-9 · Working-day calendar gap inflates Jobs FN

| Property | Value |
|---|---|
| Rule | JOBS-DR-MISSING |
| Mechanism | Defect D3 creates a FP problem (weekend false RED). But the inverse is also a FN: on a Tuesday after a Monday holiday, the rule still uses 36h lookback. If the holiday is unrecognized, the card may BE green when it should be amber (true holiday → no DR expected → green; but day after holiday with 60+ hours since last DR → should be amber). |
| Severity | 🟢 LOW |
| Remediation | Same calendar-awareness patch as D3 fixes both directions. |

---

## 3 · FN risk ranking

| # | FN class | Severity | Patch required | Recommended Phase |
|---|---|---|---|---|
| FN-1 | Silent Approvals & Equipment counts (D5) | 🔴 HIGH | Yes (Path B) | Pre-production |
| FN-2 | Tasks without due_at invisible | 🟡 MEDIUM | No (input hardening) | Phase B |
| FN-3 | Document expirations not surfaced | 🟡 MEDIUM | No (new card) | Phase B |
| FN-4 | Compound failure not consolidated | 🟡 MEDIUM | No (new card) | Phase B |
| FN-5 | Severity miscategorization | 🟡 LOW-MED | No (new rule) | Phase B |
| FN-6 | Financial / customer / schedule out of scope | 🟡 LOW-MED | No (new domain) | Phase B/C |
| FN-7 | OSHA flag text variation | 🟢 LOW | No (input hardening) | Phase B |
| FN-8 | Backup health not on Pulse | 🟢 NEGLIGIBLE | n/a (by design) | n/a |
| FN-9 | Calendar gap (inverse of D3) | 🟢 LOW | No (same patch as FP-3) | Phase B |

---

## 4 · Aggregate FN posture

| Metric | Current | After Path B patch |
|---|---|---|
| HIGH-severity FN classes | 1 (FN-1) | 0 |
| MEDIUM-severity FN classes | 4 (FN-2, FN-3, FN-4, FN-5) | 4 (all are Phase B work) |
| LOW-severity FN classes | 4 (FN-6, FN-7, FN-8, FN-9) | 4 |
| Operationally dangerous FN classes | 1 (FN-1: silent approvals/OOS) | 0 |

**Path B reduces the HIGH-severity FN count to zero.** Remaining FNs are Phase B scope or by-design separations.

---

## 5 · Recommendation

🔴 **Defect D5 (FN-1) is the single most operationally dangerous Phase A defect.** It causes the Approvals card to silently under-report aged POs that may be blocking real work. An executive looking at a GREEN Approvals card today cannot detect that a $50K material order has been pending for 5 days.

Path B (which patches D5) is therefore not optional from a risk-management standpoint — it is the **minimum acceptable patch before production deployment** if leadership intends to rely on the dashboard for Approvals visibility. If the operator chooses Path A (deploy as-is), Approvals visibility must continue to be checked at `/admin/po-requests` weekly, not from the Command Center, until D5 is patched.

All other FN classes are acceptable Phase A gaps and have clear Phase B remediation paths documented in `EXECUTIVE_IMPLEMENTATION_ROADMAP.md`.

# Dispatch Notification Discipline · Phase 11 · Document 9 of 10

**Date:** 2026-05-24
**Purpose:** Extend the existing 19-row Notification Discipline Matrix (Phase 6) with dispatch-specific events. Inherits the same tiering, aggregation rules, and 5-question discipline checklist.

**Doctrine:** Every new notification must answer ALL five questions from `NOTIFICATION_DISCIPLINE_MATRIX.md`. Failed answers → notification does not ship.

---

## Five-question discipline (reminder)

Per Phase 6, every new notification must answer:
1. **Is it actionable?**
2. **Is it already represented?**
3. **What's the suppress / aggregate rule?**
4. **Who owns it?**
5. **What tier?**

All 6 new DLS notifications below have been filtered through these five questions.

---

## New DLS notification rows (extends matrix to 25 rows total)

| # | Event | Audience | Tier | Channel | Suppress / aggregate rule | Owner | Expected action |
|---|---|---|---|---|---|---|---|
| 20 | **Driver session about to expire** | Driver only | INFO | In-app banner (not bell) | Once per session, 30 min before expiration | Dispatch | Re-tap link from SMS if needed |
| 21 | **Truck wait soft threshold (30 min)** | Dispatch (truck boss) | IMPORTANT | Bell | One per wait event per threshold; suppressed if WAITING_ON_TRAFFIC or WAITING_ON_LANE_CLOSURE (uncontrollable) | Dispatcher | Call the source; investigate |
| 22 | **Truck wait hard threshold (60 min)** | Dispatch (truck boss) + dispatch lead | CRITICAL | Bell + email if AUTO_EMAIL_REPORTS | One per wait event per crossing | Dispatcher | Reassign or escalate |
| 23 | **Truck BREAKDOWN** | Dispatch + Shop + Safety | CRITICAL | Bell + (SMS to shop on-call if SHOP_ONCALL_SMS configured) | Idempotent on assignment_id; one notification per breakdown | Shop + Dispatcher | Roll service; reassign |
| 24 | **Plant bottleneck pattern** (≥ 3 trucks WAITING_ON_PLANT same source) | Dispatch + PM | IMPORTANT | Bell + PM digest | One per bottleneck event; auto-resolves when < 3 trucks waiting | Dispatcher | Call plant manager |
| 25 | **Assignment stuck > 90 min in same state** | Dispatch | IMPORTANT | Bell | One per assignment per stuck-detection cycle | Dispatcher | Check driver / call |

---

## Five-question audit for each new notification

### Event #20 · Driver session expiring
1. **Actionable?** Yes — re-tap link.
2. **Already represented?** No (sessions are new to DLS).
3. **Suppress?** Once per session.
4. **Owner?** Driver acts; dispatcher provides refresh.
5. **Tier?** INFO. Pre-emptive courtesy, not urgent.

### Event #21 · Wait soft threshold
1. **Actionable?** Yes — investigate or call source.
2. **Already represented?** Partially (governance finding); but live wait isn't governance.
3. **Suppress?** Per wait event per crossing; uncontrollable causes suppressed.
4. **Owner?** Dispatcher.
5. **Tier?** IMPORTANT.

### Event #22 · Wait hard threshold
1. **Actionable?** Yes — reassign or escalate.
2. **Already represented?** No, this is harder than #21.
3. **Suppress?** Per crossing.
4. **Owner?** Dispatcher + dispatch lead.
5. **Tier?** CRITICAL.

### Event #23 · Breakdown
1. **Actionable?** Yes — roll service.
2. **Already represented?** No, breakdowns are new.
3. **Suppress?** Idempotent per breakdown event.
4. **Owner?** Shop + dispatcher.
5. **Tier?** CRITICAL.

### Event #24 · Plant bottleneck
1. **Actionable?** Yes — call plant manager.
2. **Already represented?** Surfaced as governance finding `PLANT_BOTTLENECK_PATTERN`; bell adds urgency.
3. **Suppress?** Per bottleneck event; auto-resolves.
4. **Owner?** Dispatcher.
5. **Tier?** IMPORTANT.

### Event #25 · Assignment stuck
1. **Actionable?** Yes — check / call driver.
2. **Already represented?** Governance `ASSIGNMENT_STUCK_NO_MOTIVE_DATA` covers Motive-missing case; this is the broader stuck case.
3. **Suppress?** Per assignment per detection cycle.
4. **Owner?** Dispatcher.
5. **Tier?** IMPORTANT.

All 6 pass the discipline check.

---

## Aggregation discipline applied to DLS notifications

### Per-truck uniqueness
A single truck cannot generate two bells of the same type for the same wait event. Once the soft threshold notification fires, the next notification for that same event is the hard threshold crossing (not a second soft).

### Silent status churn
Normal state transitions (ASSIGNED → ENROUTE_TO_LOAD → AT_LOAD_SITE → ...) do **not** fire notifications. Only:
- Wait state threshold crossings
- Breakdown
- Bottleneck pattern detection
- Stuck assignment detection
- Session expiration (to the driver only)

State change visibility is the **Dispatch Board's job**, not the bell's.

### Severity-driven channel
- INFO → in-app only (driver session expiration)
- IMPORTANT → bell, no SMS, no email
- CRITICAL → bell + optional SMS (shop on-call) + optional email (if AUTO_EMAIL_REPORTS)

### Auto-resolve > manual resolve
Bottleneck pattern, stuck assignment, and wait threshold notifications **auto-clear** when the underlying condition resolves. The dispatcher never needs to "mark read" for transient operational signals.

---

## What is NOT a DLS notification (deliberately)

### State transitions fire NO notifications
- ASSIGNED → no notification (board update is enough)
- ENROUTE_TO_LOAD → no notification
- AT_LOAD_SITE → no notification
- LOADING → no notification
- LOADED → no notification
- ENROUTE_TO_JOB → no notification
- ARRIVED_JOB → no notification
- DUMPING → no notification
- COMPLETE → no notification

Why: the board is live. Notifications add noise without adding signal.

### Wait state ENTRY does NOT fire a notification
- Only the threshold crossing matters.

### "Cycle completed" does NOT fire a notification
- Visible on board; INFO-level facts don't need bells.

### Hold or off-shift do NOT fire notifications
- Routine; visible on board.

This silence preserves the platform's signal discipline (Phase 7).

---

## SMS as a notification channel · scope discipline

The DLS uses SMS for:
1. **Magic-link delivery** to drivers at shift start (not a notification per se; a workflow action).
2. **Optional shop on-call** breakdown alert (if `SHOP_ONCALL_SMS` env var is configured).

The DLS does NOT use SMS for:
- ❌ Routine state change notifications to dispatcher (use the board)
- ❌ Wait threshold alerts to driver (would be backseat-driving)
- ❌ "Hey John, are you OK?" check-ins (use voice — the platform supports the human chain)

This keeps SMS as a high-signal channel and prevents notification fatigue.

---

## Email channel · scope discipline

The DLS uses email for:
1. CRITICAL-tier breakdowns (if `AUTO_EMAIL_REPORTS=true`)
2. Weekly dispatch digest (admin + dispatch lead): one email summarizing the week's cycles, wait totals, bottlenecks. Mirrors the existing safety + PO digest pattern (Phase 6 matrix).

The DLS does NOT use email for:
- ❌ Per-assignment notifications
- ❌ Per-wait-event notifications
- ❌ Daily summaries (weekly is enough)

---

## Cross-portal notification visibility

Each DLS notification's `recipient_role` field determines who sees it on `/api/notifications`:

| Notification | recipient_role | Why |
|---|---|---|
| Driver session expiring | (driver-only; in-app banner) | Not a bell event |
| Wait soft threshold | `dispatch` | Truck boss owns it |
| Wait hard threshold | `dispatch` + `admin` | Dispatch lead escalation |
| Breakdown | `dispatch` + `shop` + `safety` | All three need to know |
| Plant bottleneck | `dispatch` + `pm` (when project_number matches PM's projects) | PM cares about their project's bottlenecks |
| Stuck assignment | `dispatch` | Truck boss only |

The PM portal continues to use the existing notification surface (`/api/notifications`) with the existing PM-scope filter that returns notifications matching their projects. **No new PM endpoint required.**

---

## Total notification count after DLS

Before Phase 11: **19 rows** in the matrix.
After Phase 11: **25 rows**.

**The matrix grew by 6 rows. The platform did not gain 6 new dashboards, 6 new badges, or 6 new email subscriptions.** Just 6 carefully tiered events with explicit aggregation.

This is signal discipline in practice.

---

## Bell badge management

Per Phase 9 risk #1 (bell-volume creep) and Phase 8 P2 (50+ cap), the DLS additions inherit the existing 50+ cap on bell badge display.

**Volume estimate (sanity check):**
- 11 trucks active per shift
- ~5% of trucks hit a soft wait threshold per shift = 0.55 notifications/shift
- ~1% hit hard threshold = 0.11 notifications/shift
- ~0.1 breakdowns per shift = 0.1 notifications
- 1 bottleneck per week = 0.2 notifications/shift
- ~5% stuck assignments = 0.55 notifications/shift

**Expected DLS volume: ~1.5 bell notifications per shift for dispatch. Sustainable.**

If volume exceeds projection, the 60-day discipline review (Phase 7) revisits thresholds.

---

## Conclusion

The DLS adds 6 new notifications to the matrix. Every one passes the 5-question discipline check. Aggregation rules prevent compound noise. State transitions remain silent on the bell because the board is live. Email + SMS are used sparingly. Bell volume is projected sustainable.

The platform's signal hygiene is preserved. The DLS amplifies what matters without inflating what doesn't.

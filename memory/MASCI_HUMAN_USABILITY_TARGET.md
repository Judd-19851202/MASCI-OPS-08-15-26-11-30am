# MASCI Human Usability Target

**Track 13.5C · "Under-five-minute first task" specification per role**
**Mode:** Architecture only — no code, no UX prototyping.
**Generated:** 2026-06-12 (UTC)

> The target-state human-usability contract. A first-time operator must be able to do **one real piece of work** in **under 5 minutes**, with **zero training and zero tribal knowledge**. This is the single most operator-facing measurement of the Simple pillar.

---

## 1. The contract

For every role audience, this document declares **one** task that the role's portal must support **for a brand-new operator**, **without any prior training**, **using only the on-screen affordances**, **in under five minutes**.

If the platform fails any of these tasks, **Simple ≠ 10**.

---

## 2. Per-role under-5-minute tasks

### 2.1 Project Manager

**Task:** "Find an open hold on one of my projects and either lift it or escalate it."

Sequence (target):
1. Land on `/pm/hub`. See the "Open Holds" pulse card with a non-zero count and a `safety_hold` or `maintenance_hold` chip.
2. Click the pulse card. See a unified Holds list scoped to my projects (via `co_pm_emails`).
3. Click one row. See the underlying engine record (Daily Report · Equipment record · QA/QC failure) with full context.
4. Click `Lift hold` (or `Escalate to Safety Mgr`). System records the transition with timestamp + operator + reason.
5. Done.

Pass criteria: ≤ 5 clicks · ≤ 5 minutes · no help docs consulted · no Slack message sent.

### 2.2 Dispatcher

**Task:** "Reassign a stale-position asset to a different crew."

Sequence:
1. Land on `/dispatch-portal`. See the live map at ≥ 60% viewport on iPad landscape.
2. See an asset with a `stale_position` chip in the side rail.
3. Tap the asset. See its current assignment + last-known position + last-seen timestamp.
4. Tap `Reassign`. Pick a target crew from a typeahead.
5. Confirm. Assignment updated; status chip flips to `assigned`.

Pass criteria: ≤ 5 taps · ≤ 90 seconds.

### 2.3 Safety Manager

**Task:** "Verify a submitted incident and create a CAPA."

Sequence:
1. Land on `/safety` Command Center. See "Open Incidents · pending verification" Card.
2. Click. See list of incidents in `submitted` state.
3. Click one. Review narrative + photos + witness statements.
4. Click `Verify`. System transitions to `verified`.
5. Click `Open CAPA`. Form pre-populates with incident reference; pick severity + due date; submit.

Pass criteria: ≤ 6 clicks · ≤ 4 minutes.

### 2.4 HR Manager

**Task:** "Initiate an offboard packet for a departing employee."

Sequence:
1. Land on `/hr`. See "This week's offboards" Card.
2. Click `New Offboard`.
3. Pick the employee from a typeahead.
4. Confirm exit date and reason code.
5. Submit. System routes notifications to Admin (equipment return), Dispatch (assignment removal), and Safety (PPE retrieval).

Pass criteria: ≤ 5 clicks · ≤ 3 minutes.

### 2.5 Shop Mechanic

**Task:** "Move a repair from Submitted to Verified."

Sequence:
1. Land on `/shop`. See the open-repair queue.
2. Click the highest-priority row. See repair request + photos + odometer.
3. Click `Begin work` (transitions to `pending_verification`).
4. Add a parts/notes entry.
5. Click `Verify complete` (transitions to `verified`).

Pass criteria: ≤ 5 clicks · ≤ 4 minutes.

### 2.6 Field Leadership (Superintendent / General Foreman)

**Task:** "Submit today's Daily Report from the field on iPad."

Sequence:
1. Land on `/field-leadership/portal`. See "Submit Daily Report" primary action.
2. Tap. Form opens; crew + jobsite pre-populated from context.
3. Add weather + man-hours + scope notes.
4. Attach 3 photos.
5. Submit. Chip flips to `submitted`. PM sees it within 60 seconds.

Pass criteria: ≤ 5 actions · ≤ 5 minutes · phone or iPad parity · offline-capable (queued sync within 30 s of reconnection).

### 2.7 Driver

**Task:** "Start my shift."

Sequence:
1. Open magic-link from email or text. Land on `/driver`.
2. See today's shift card: truck, route, qualification chip.
3. Tap `Start Shift`.

Pass criteria: ≤ 2 taps · ≤ 30 seconds. **This is the strictest budget in the platform.**

### 2.8 Admin (Super-admin)

**Task:** "Create a new operator account and grant role access."

Sequence:
1. Land on `/admin`. See `New Operator` primary action.
2. Click. Enter email, name, role.
3. Pick the portal(s).
4. Submit. System sends MFA-enrollment email + welcome message.

Pass criteria: ≤ 4 clicks · ≤ 3 minutes.

### 2.9 Leadership (Executive)

**Task:** "See this week's safety performance vs last week."

Sequence:
1. Land on `/leadership`. See the trailing-7-day safety chart above the fold.
2. Toggle to "vs prior 7 days".
3. Export to PDF (locale-aware).

Pass criteria: ≤ 3 clicks · ≤ 90 seconds. **Read-only.**

---

## 3. Cross-role rules

For every role:
- **No login screen** beyond email + password (or MFA) + reset link. No CAPTCHA on production sign-in.
- **No tribal knowledge** in any string. Avoid acronyms not defined in-context.
- **No "settings" required** before the first task. Sensible defaults always.
- **No 404 on bookmarked URLs.** Every operator route is deep-linkable.
- **Identical visual language** across roles — only role color, role name, and logo position vary.
- **iPad portrait works.** Field roles must work on iPad in portrait without horizontal scroll.

---

## 4. Why this contract is Simple = 10

If a brand-new operator can do their first real piece of work in under 5 minutes with no training, the platform has achieved exactly what `MASCI_TARGET_STATE_ARCHITECTURE.md` §1.2 declares: zero tribal knowledge, max two primary actions, one vocabulary, one shell.

Track 13.5B scored **Simple = 6.5** today. Closing this gap requires:
- PM CAPA list view (U-01) — earns +0.5
- Unified Holds (H-8) — earns +0.5
- Phase B3 pilot migration (vocabulary + cards) — earns +0.5
- Driver Hub static landing (V-15 / R-13) — earns +0.5
- Command Center naming collapse (R-05) — earns +0.5
- Translation completeness (T-01..T-07) — earns +0.5
= +3.0 → Simple climbs from 6.5 to 9.5; the last +0.5 to 10 requires operator-validated usability testing on real first-time operators.

---

## 5. Standing rules

No deploy. No GitHub save. No merge. No code. The contract above is the **destination**, not the implementation. Implementation is sequenced via the priority list and authorized one phase at a time.

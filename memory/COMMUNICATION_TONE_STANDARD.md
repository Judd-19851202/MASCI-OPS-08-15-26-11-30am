# Communication Tone Standard — Phase IV-A

**Iteration:** iter437 · Phase IV-A · 2026-02
**Status:** 🟢 MASTER COMMUNICATION DOCTRINE · BINDING ON ALL OUTBOUND PLATFORM MESSAGES
**Baseline:** The PM email routing system (Phase III) is the **gold-standard reference implementation** of this tone. When in doubt, match a PM routing email.
**Companion docs:** `OPERATIONAL_VERBIAGE_DOCTRINE.md` (lexicon) · `EMAIL_TEMPLATE_STANDARD.md` (Phase IV-0 templates) · `COMMUNICATION_UNIFICATION_DOCTRINE.md` (Phase IV-0 channel map).

Every email, push notification, in-app toast, modal, banner, escalation alert, and reminder the platform sends to a human is governed by this document. There are no exceptions — including system-generated maintenance messages, billing notices, and deploy-status emails.

The platform speaks to operators who are tired, often outdoors, sometimes anxious, and always accountable. Tone is not a creative concern. Tone is an operational instrument.

---

## I. The five tone principles

| Principle | What it means in practice |
|---|---|
| **1. Calm before urgent** | The reader's nervous system must not spike from punctuation, color, or capitalization. Urgency is carried by *what* is said, not *how loud*. |
| **2. Operational fact before reaction** | Lead with the noun-phrase of what happened. The recommended response comes second. The emotional framing does not appear. |
| **3. Owner before observer** | If a person owns the next action, their name appears in the first 12 words. If no owner exists, that fact appears first. |
| **4. Deadline as a moment, not a countdown** | "By end of shift today (17:00 local)" — never "in 3 hours 42 minutes." Countdowns create panic; moments create planning. |
| **5. Acknowledge once, escalate predictably** | The system never sends the same message twice within a tier. Repeated unread events escalate to the next tier — they do not nag at the same tier. |

---

## II. The urgency hierarchy (the only six tones the platform uses)

This extends §V of `OPERATIONAL_VERBIAGE_DOCTRINE.md` with full per-channel behavior.

| Tier | Wording prefix | Email subject prefix | Email send window | Push? | In-app banner? | Phone fallback? |
|---|---|---|---|---|---|---|
| 0 · Informational | `Note` | (none) | Daily digest only | No | No | No |
| 1 · Routine | `Reminder` | `[Reminder]` | Hourly batch | No | No | No |
| 2 · Attention | `Attention` | `[Attention]` | Within 15 min, batched | Yes (silent) | Yes (top-bar, dismissable) | No |
| 3 · Action Required | `Action Required` | `[Action]` | Within 2 min, not batched | Yes (alert) | Yes (sticky until acknowledged) | No |
| 4 · Escalation | `Escalation` | `[Escalation]` | Immediate | Yes (alert + sound) | Yes (modal · must acknowledge) | No |
| 5 · Emergency | `Emergency` | `[EMERGENCY]` | Immediate | Yes (alert + sound + repeat) | Yes (full-screen takeover) | Yes (SMS + voice call if unacked in 5 min) |

**Tier promotion rules:**

- A Tier 1 unread for 24h → Tier 2 (same recipient).
- A Tier 2 unread for 4h → Tier 3 (same recipient + their PM cc'd).
- A Tier 3 unacknowledged for 1h → Tier 4 (PM becomes primary, foreman cc'd).
- A Tier 4 unacknowledged for 1h → Tier 5 ONLY if the underlying operational fact is on the "Emergency-eligible" list (incidents, OSHA reportables, asset critical-failure, missing crew member). Otherwise it stays Tier 4 indefinitely with a daily digest reminder.

**Demotion rules:**

- Acknowledgment by the named owner demotes the item to its prior tier OR closes it, depending on the underlying state model.
- A reassignment resets the tier clock to Tier 2 with the new owner.

**Anti-skip rule:** The system never sends a Tier 4 escalation as the first contact about an item. The recipient must have seen Tier 2 and Tier 3 first. (Exception: Tier 5 emergencies bypass this — they are the first contact by design.)

---

## III. The anti-panic doctrine

The platform will not cause panic. Panic degrades decision quality. Decision quality is the product.

### Forbidden urgency amplifiers (across all channels)

- ❌ Multiple exclamation marks (`!!`, `!!!`)
- ❌ ALL CAPS in body text (subject prefixes like `[EMERGENCY]` are the only exception)
- ❌ Red color used on more than one element per view
- ❌ Bold red text inside paragraph copy
- ❌ Countdown timers ("3:42 remaining")
- ❌ Flashing / pulsing UI (except for active Tier 5 takeovers)
- ❌ Sirens, claxons, or any sound louder than a soft ping (Tier 5 only)
- ❌ "URGENT" in subject lines (use `[Action]` or `[Escalation]`)
- ❌ Phrases: "right now", "immediately", "ASAP", "drop everything"
- ❌ Threatening copy: "This will be reported", "Failure to respond will…"

### Required urgency carriers (the calm signals)

- ✅ The severity prefix word from §II
- ✅ The severity color stripe (single thin element)
- ✅ The operational fact stated plainly
- ✅ The named owner
- ✅ The deadline as a moment

That's all. The platform never asks for urgency by shouting.

---

## IV. The anti-alarm-fatigue doctrine

Operators stop reading messages that arrive too often or that "cry wolf." This doctrine prevents that.

### Quotas per recipient per shift (rolling 12-hour window)

| Tier | Max messages | If exceeded |
|---|---|---|
| 0 (Note) | Unlimited (daily digest only) | n/a — already batched |
| 1 (Reminder) | 8 | 9th+ collapsed into a single "X reminders pending" digest |
| 2 (Attention) | 5 | 6th+ collapsed into "X items need attention" digest |
| 3 (Action Required) | 3 | 4th+ promoted to a "Multiple actions overdue" Tier 3 summary card (NOT individual messages) |
| 4 (Escalation) | 2 | 3rd+ paged to the PM as a "your portfolio has 3+ active escalations" Tier 3 alert (not a 3rd Tier 4) |
| 5 (Emergency) | No quota | Each emergency is by definition rare and individual |

### Repetition rules

- The platform NEVER sends the same Tier ≥ 2 message twice. Either it promotes (Tier+1) or it stays silent on that channel.
- Daily digests collect all Tier 0–1 items into a single 06:00-local email per recipient.
- A "your day at a glance" Tier 0 digest is sent at 06:00 and 14:00 local. Never more.

### Suppression during emergencies

- When a Tier 5 emergency is active for a recipient, all Tier 0–2 messages to that recipient are suppressed until the emergency closes. Tier 3 messages are deferred unless they involve the same domain as the emergency.

---

## V. The "do now" vs "informational" distinction

Every outbound message must be classifiable into exactly one of these two intents. If it falls between, it is rejected at PR review.

### Do-now messages (Tier 2+)

Structure:
1. Severity prefix
2. Operational fact (noun phrase)
3. Named owner
4. Required verb + deadline
5. Optional one-sentence context

The reader's eye must land on the verb-and-deadline within the first 4 seconds.

### Informational messages (Tier 0–1)

Structure:
1. (No severity prefix, or `[Reminder]`)
2. Operational fact
3. Optional context
4. No verb, no deadline

The reader may not act and that is acceptable. Informational messages exist to maintain shared awareness, not to drive action.

**Hard rule:** A message cannot contain both an informational paragraph AND a required action. If it has a verb-and-deadline, every sentence in the message must support that action. Background context goes in a separate informational message.

---

## VI. Channel-specific tone rules

### Email

- Subject ≤ 72 characters.
- Subject must contain the severity prefix and the operational noun.
- Body opens with the operational fact, not "Hi {name}" — names appear in the salutation block only at Tier ≤ 1.
- Tier 2+ emails: no salutation, no signature, no "Best regards." The system is not a person.
- One CTA button max. Color matches severity. Verb is from the §II canonical verb list of `OPERATIONAL_VERBIAGE_DOCTRINE.md`.
- Footer: a single line — `Sent by MASCI Safety · {timestamp} · Reply to PM at {pm_email}`. No unsubscribe link on Tier 3+ (operational mail is non-opt-out by accountability rule).
- HTML and plain-text variants are byte-for-byte identical in copy. The platform never sends decorative HTML that the plain-text version cannot convey.

### Push notification

- Title: severity prefix + noun (≤ 36 chars).
- Body: owner + required verb + deadline (≤ 110 chars).
- No emoji. Ever.
- Sound: silent for Tier 0–2 · default alert for Tier 3–4 · custom emergency tone for Tier 5 only.
- Tap → opens the exact in-portal surface where the action is performed. Never the dashboard.

### In-app toast (transient, non-blocking)

- Reserved for the **confirmation** of a successful operator-initiated action (Tier 0 only).
- Wording: `{Noun} {past-tense verb}.` — e.g., `Daily Report submitted.` · `Escalation acknowledged.` · `Asset reassigned.`
- Duration: 4 seconds.
- Color: slate (success has no green — green is reserved for `Active` state badges). A subtle check icon is allowed.
- Never used for errors. Errors get a banner (see below).

### In-app banner (persistent until dismissed or resolved)

- Reserved for operationally-visible state changes affecting the current view.
- Tier 0–1: slate, dismissable.
- Tier 2: amber, dismissable, returns on next page load if state persists.
- Tier 3+: orange/red, NOT dismissable — must be resolved or acknowledged.

### In-app modal

- Reserved for confirmations of irreversible actions AND Tier 4–5 alerts.
- Modal title: severity prefix + noun (no question mark, no "Are you sure?").
- Modal body: one sentence stating consequences. One named verb-button + one Cancel.
- Tier 4 modal: must be acknowledged. Closes only after the operator clicks the named acknowledge button.
- Tier 5 modal: full-screen takeover, must be acknowledged, includes a phone-fallback indicator.

### SMS / phone fallback (Tier 5 only)

- SMS body: 1 sentence with the operational fact + a 6-digit acknowledge code.
- Voice call (if SMS unacked in 5 min): a pre-recorded calm voice reading the fact + the acknowledge code. Repeat once.
- Both are last-resort. Pre-deploy gate verifies the recipient list for SMS/voice contains only role accounts (PM, Safety Officer, Owner) — never field accounts.

---

## VII. Success confirmations

Success messages are the smallest, calmest copy in the system.

| Action | Success copy | Channel |
|---|---|---|
| Submit Daily Report | `Daily Report submitted.` | Toast |
| Approve Daily Report | `Daily Report approved.` | Toast |
| Reject Daily Report | `Daily Report rejected. Foreman notified.` | Toast |
| Acknowledge Escalation | `Escalation acknowledged.` | Toast |
| Assign Asset | `Asset assigned to {name}.` | Toast |
| Schedule Inspection | `Inspection scheduled for {date}.` | Toast |
| Close Incident | `Incident closed. Audit log updated.` | Toast |

Forbidden in success messages: emoji, exclamation marks, "Awesome", "Great", "Done!", "Success!", "All set!".

---

## VIII. Warnings (pre-action, reversible context)

Warnings appear before the operator commits an action that has non-obvious consequences.

| Situation | Warning copy |
|---|---|
| Rejecting a Daily Report | `Rejecting returns the report to the foreman for revision. Provide a one-sentence reason.` |
| Reassigning an active escalation | `Reassignment resets the escalation clock to Tier 2 with the new owner.` |
| Closing an incident without resolution notes | `Closing without resolution notes is permitted but flagged in the next audit cycle.` |
| Deleting a draft | `Drafts cannot be recovered after deletion.` |
| Force-closing a job with open action items | `{n} action items are open. They will be auto-closed with reason "Job force-closed."` |

Warning prose: state the consequence, not the danger. The reader decides whether the consequence is acceptable.

---

## IX. Operational reminders

Reminders are Tier 1. They keep operators ahead of due work without nagging.

| Operational state | Reminder copy (email/push) | Trigger |
|---|---|---|
| Daily Report not submitted by end-of-shift | `[Reminder] Daily Report due — Crew {n}. Submit by 17:00 local today.` | 16:00 local |
| Pre-Op not completed before dispatch | `[Reminder] Pre-Op Check pending — Unit {id}. Required before dispatch.` | 30 min before scheduled dispatch |
| Certification expiring | `[Reminder] {Certification} for {name} expires in {n} days. Schedule renewal.` | 30 days, 14 days, 7 days |
| Maintenance window approaching | `[Reminder] Maintenance window opens in 48 hours — {asset}. Confirm parts on hand.` | 48 hours before window |
| Audit prep checklist | `[Reminder] Audit on {date}. Open checklist to track preparation.` | 14 days before |

Reminders never repeat at the same tier. If unread, they promote to Tier 2 (`Attention`) per the promotion rules in §II.

---

## X. Overdue language

When operational deadlines pass, the wording shifts from anticipatory to factual. It does not shift to blaming.

| Time past deadline | Wording | Tier |
|---|---|---|
| ≤ 15 min | `Due now` (no tier promotion yet) | (same tier as last reminder) |
| 15 min – end of shift | `Overdue by {n} hours` | Tier 2 |
| Past end of shift | `Overdue by 1 shift` | Tier 3 |
| Past 2 shifts | `Overdue by 2 shifts · Escalating to PM` | Tier 4 |
| Past 3 shifts | `Overdue by 3 shifts · Project Manager assumed primary` | Tier 4 (sticky) |

**Never:** "late", "behind", "missed", "failed to submit", "not done yet". These are emotional words. `Overdue by N shifts` is factual and proportional.

---

## XI. Mobile push wording (the strictest constraint)

Push notifications appear in operator pockets during work. They must:

1. **Be readable in 1.5 seconds.** Operators look at lock screens; they do not read paragraphs.
2. **Communicate severity in the first word.** The severity prefix is non-negotiable.
3. **Name the noun, not the system.** `[Action] Daily Report — Crew 7` not `MASCI: a Daily Report needs your attention!`
4. **Show owner only if non-default.** If the push goes to the owner, the owner's name is redundant — replace it with the noun.
5. **Never link to the dashboard.** Tap must open the exact actionable surface.

### Push wording canonical examples

```
[Reminder] Daily Report due 17:00 — Crew 7
[Attention] Pre-Op pending — Unit 142, dispatch in 30 min
[Action] Daily Report overdue 1 shift — Crew 7
[Escalation] Daily Report overdue 2 shifts — Crew 7 · PM acting
[EMERGENCY] Crew member unaccounted — Rt-441 widening · Acknowledge required
```

---

## XII. Modal wording

Modals interrupt. They must justify the interruption.

### Modal title patterns

- ✅ `Reject Daily Report` (verb + noun)
- ✅ `Reassign Asset` (verb + noun)
- ✅ `Acknowledge Escalation` (verb + noun)
- ❌ `Are you sure?` (no information, only friction)
- ❌ `Wait!` (panic word)
- ❌ `Heads up` (casual)

### Modal body patterns

One sentence stating the consequence. One sentence stating the next state (if non-obvious).

✅ `Rejecting returns the report to the foreman for revision. The foreman will be notified by email.`
❌ `Are you sure you want to reject? This action cannot be undone and the foreman will be very disappointed.`

### Modal buttons

- Primary button: verb from the canonical verb table, matching the modal title verb. Color matches severity.
- Secondary button: always `Cancel`. Never `Nevermind`, `Back`, `Wait`, `Oops`.
- Tier 4 modals: primary button is `Acknowledge`, never `OK` or `Got it`.

---

## XIII. CTA language (call-to-action across all surfaces)

CTAs follow these grammar rules without exception:

1. **Single canonical verb** from `OPERATIONAL_VERBIAGE_DOCTRINE.md` §II.
2. **Optional noun** only if the verb is ambiguous without it.
3. **Title Case.** ("Submit Daily Report", not "submit daily report" or "SUBMIT DAILY REPORT".)
4. **No trailing punctuation.** ("Submit" not "Submit.")
5. **No "Click to…" / "Tap to…"** — the button is the action, not the description of the action.
6. **One primary CTA per view.** If two seem necessary, the view is doing two jobs and must be split.

| ❌ Forbidden | ✅ Approved |
|---|---|
| `Submit your daily report now!` | `Submit Daily Report` |
| `Click here to approve` | `Approve` |
| `Get started` | (forbidden everywhere — meaningless) |
| `Learn more` | `Open Documentation` |
| `Continue` (when state is being saved) | `Submit and Continue` (only if both happen) |
| `Save changes?` (as button) | `Save` |
| `OK` | (use the verb) |

---

## XIV. Tone calibration — three reference messages

The following are the canonical examples. When in doubt, write a message that lives between two of these and stylistically matches the closest one.

### Reference A — Tier 1 routine reminder

```
Subject: [Reminder] Daily Report due — Crew 7

Daily Report for Crew 7 (Rt-441 widening) is due by end of shift today (17:00 local).

Owner: J. Ramirez (Foreman)
Required: Submit by 17:00 local.

Sent by MASCI Safety · 2026-02-27 16:00 EST · Reply to PM at pm@masci.example
```

### Reference B — Tier 3 action required

```
Subject: [Action] Daily Report overdue — Crew 7

Daily Report for Crew 7 (Rt-441 widening) is overdue by 1 shift.

Owner: J. Ramirez (Foreman)
Required: Submit by end of current shift today (17:00 local).
Context: Two consecutive shifts without a Daily Report breaks the audit chain.

[Submit Daily Report]   (button, orange)

Sent by MASCI Safety · 2026-02-28 09:00 EST · Reply to PM at pm@masci.example
```

### Reference C — Tier 4 escalation

```
Subject: [Escalation] Daily Report overdue 2 shifts — Crew 7

Daily Report for Crew 7 (Rt-441 widening) has been overdue for 2 consecutive shifts.

Primary owner: M. Chen (PM)
Original owner: J. Ramirez (Foreman)
Required: PM intervention. Acknowledge this escalation, then resolve by either obtaining the report from Foreman or filing on Foreman's behalf with documented reason.

Project: Rt-441 widening
Last submitted Daily Report: 2026-02-25

[Acknowledge Escalation]   (button, red)

Sent by MASCI Safety · 2026-03-01 08:00 EST · Reply to PM at pm@masci.example
```

Notice across all three: no emoji, no exclamation, no countdown, no anger, no apology. Just operational fact, owner, verb, deadline.

---

## XV. Operator-trust principles for tone

Operators trust the platform's voice when:

1. **Every Tier 4 escalation they've ever received turned out to genuinely require Tier 4 action.** No false alarms.
2. **Every Tier 0 informational message was worth the 2 seconds to read.** No filler.
3. **The same situation always produces the same wording.** No randomization, no "voice variants," no A/B-tested copy in operational mail.
4. **The platform never speaks more than necessary.** Silence is a feature.
5. **The platform never speaks less than necessary.** Hiding information to "reduce noise" is a violation; collapsing it under a digest is the correct path.

---

## XVI. Enforcement

- **Deploy gate (Phase IV.A.4):** `scripts/verify_message_tone.py` runs against all email templates, push payloads, and i18n strings. Rejects forbidden phrases from this doc and `OPERATIONAL_VERBIAGE_DOCTRINE.md`.
- **PM routing system as reference:** Any new outbound message must be diff'd against the closest equivalent PM routing email and justified if it diverges.
- **Quota dashboard:** A `System & Governance → Communications` page (Phase IV-B) surfaces per-recipient message counts by tier. Operators exceeding quotas trigger a "review your notification routing" Tier 1 internal alert to the platform owner.
- **No marketing involvement:** Operational copy is never reviewed by marketing. It is reviewed by operations leadership and platform engineering only.

---

## Verdict

🟢 **MASTER TONE DOCTRINE LOCKED.** The platform now has one voice across every channel: calm, factual, owner-named, deadline-anchored, severity-disciplined. From this iteration forward, every outbound human-facing message conforms to this standard or it does not ship.

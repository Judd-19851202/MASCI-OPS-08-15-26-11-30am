# Field Shadow Validation Kit · Phase 6 · WS1

**Purpose:** Practical, role-by-role validation package for shadow-testing the platform with real MASCI field users. Five tests, one per role. Each test is a printable single-page checklist. No new app or dashboard — just docs.

---

## How to use this kit

1. Pick one role at a time. Sit next to the user (or screen-share over a phone call). Do NOT coach.
2. Hand them ONE workflow + the device they would normally use.
3. Time the run from "start" to "submitted" with a stopwatch.
4. Tally tap/scroll count and hesitations as they happen.
5. After submit, ask the post-test questions verbatim — don't lead.
6. Fill the **Field notes** section after the run. Then move to the next role.
7. Roll the 5 results up into `/app/memory/PHASE6_FIELD_ADOPTION_SPRINT_RESULTS.md`.

---

## TEST 1 · Superintendent · Daily Report (full crew + delay)

**Device:** Personal phone, browser at 390 px width, **dimmed 60 % brightness** (sunlight simulation), one work glove on the non-dominant hand.

**Workflow to shadow:** New Daily Report → fill crew (3 members) → log 1 sub on site → log 1 equipment row → mark schedule delay = Yes → fill delay description → 6 photos → sign → submit.

**Expected time:** ≤ 6 min.

**Tap/scroll estimate:** ≈ 75 taps · ≈ 12 vertical scrolls.

**Hesitation watchpoints:**
- Does the user know to expand the CollapseCard for subs/equipment, or do they swipe past?
- When they say "schedule delay Yes", do they SEE the rose `Attention · Delay details` summary near submit, or do they tap submit anyway?
- Photo upload progress: does the user wait, or tap submit while uploads spin?
- Do they look at the operational completion summary banner above submit at all?

**Post-test questions:**
1. "What did you understand was REQUIRED before you could submit?"
2. "Did anything feel skipped or hidden?"
3. "If you submitted half this report and lost signal, what would happen?" (validates draft recovery awareness)
4. "Show me how you'd correct a mistake AFTER submitting." (validates portal navigation)

**Pass / Fail criteria:**
- ✅ PASS: Submitted ≤ 8 min, photo minimum met, zero accidental schedule-delay-without-details, zero accidental subs-section-skipped despite having subs on site.
- ❌ FAIL: Submitted incomplete, OR couldn't find the schedule delay field, OR submitted while photos still uploading.

**Field notes:** _(fill after run)_
```
Date:           _____________
Tester:         _____________
Device:         _____________
Actual time:    _____________
Hesitations:    _____________
Surprises:      _____________
Quote of run:   _____________
PASS / FAIL:    _____________
```

---

## TEST 2 · Foreman · Near-Miss Incident (Tier-1 fast entry)

**Device:** Personal phone, 390 px width, normal brightness.

**Workflow to shadow:** New Incident → severity = `Near Miss` → fill Sections 01–04 + 4 photos + signature → submit.

**Expected time:** ≤ 3 min.

**Tap/scroll estimate:** ≈ 30 taps · ≈ 6 vertical scrolls.

**Hesitation watchpoints:**
- Does the foreman understand that Tier-2 sections (Root Cause, Witnesses, Corrective Actions, Notifications) are OPTIONAL for a near miss?
- Do they expand them anyway out of habit? (over-filling is fine, but slows the workflow)
- Do they read the operational completion summary `Ready to submit · follow-up optional for this severity`?

**Post-test questions:**
1. "Tell me what you think happens to this report after submit."
2. "Did you feel rushed past anything important?"
3. "If this had been a SERIOUS injury instead, what would change in this form?"

**Pass / Fail criteria:**
- ✅ PASS: Submitted in ≤ 4 min with all Tier-1 fields, no unnecessary Tier-2 work attempted (or attempted only by user choice).
- ❌ FAIL: Time exceeded 5 min, OR foreman tried to skip required Tier-1 fields, OR was confused by the collapsed Tier-2 sections.

**Field notes:** _(same template as Test 1)_

---

## TEST 3 · Safety Manager · Serious Incident (Tier-2 enforced)

**Device:** iPad or laptop. Office signal.

**Workflow to shadow:** New Incident → severity = `Medical Treatment Required` → submit prematurely (without filling Tier-2) → observe the rose `Attention · 3 section(s) need attention` summary + auto-expand → complete Root Cause, Corrective Actions, Notifications → re-submit successfully.

**Expected time:** ≤ 9 min.

**Tap/scroll estimate:** ≈ 90 taps · ≈ 15 vertical scrolls.

**Hesitation watchpoints:**
- Does the locked-open Tier-2 card visibly communicate "Required"?
- Does the auto-expand on submit-attempt happen smoothly (no scroll jump, no toast spam)?
- Does the Safety Manager understand WHY the platform refused the first submit attempt?

**Post-test questions:**
1. "Why did the first submit not go through?"
2. "What would happen if you tried to mark this as just a Near Miss instead?" (probes under-classification temptation)
3. "Who downstream sees this once you submit?"

**Pass / Fail criteria:**
- ✅ PASS: First submit attempt clearly blocked AND the user understood the reason without help. Second submit succeeded.
- ❌ FAIL: User found a way to submit without filling Root Cause + Corrective + Notifications. (Critical fail — see PRODUCTION_RISK_REGISTER.md.)

**Field notes:** _(same template)_

---

## TEST 4 · Dispatcher · Driver Readiness + Notifications

**Device:** Desktop browser, 1920 × 1080.

**Workflow to shadow:** Sign in to Dispatch Portal → open Driver Qualification Readiness view → identify 1 unqualified driver → check `/api/notifications` bell badge → mark a notification read → respond to a CAPA assignment.

**Expected time:** ≤ 5 min.

**Tap/scroll estimate:** ≈ 25 taps · ≈ 4 vertical scrolls.

**Hesitation watchpoints:**
- Does the dispatcher notice the new bell badge count?
- Does the readiness panel surface "why" a driver is unqualified (medical expired vs CDL expired vs not approved)?
- Is the notification list noisy or actionable?

**Post-test questions:**
1. "How would you handle dispatching this unqualified driver if you absolutely had to?" (probes for bypass behavior)
2. "If you ignored every notification today, what is the worst thing that could happen?"
3. "Is anything on this screen wasted space?"

**Pass / Fail criteria:**
- ✅ PASS: Dispatcher resolves the unqualified driver question in ≤ 3 min and identifies at least 1 notification that would be CRITICAL.
- ❌ FAIL: Confused by the readiness layout, OR unable to find the notification surface, OR overwhelmed by notification volume.

**Field notes:** _(same template)_

---

## TEST 5 · PM · Crew Compliance + Incident Awareness

**Device:** Desktop or iPad.

**Workflow to shadow:** Sign in to PM Portal → open PM Crew Compliance lens for one of their projects → spot one expired training → open the linked incident on that project → see the rose `Follow-Up Required` banner on the incident detail → understand the "Open Follow-Up CAPA" CTA.

**Expected time:** ≤ 6 min.

**Tap/scroll estimate:** ≈ 30 taps · ≈ 6 vertical scrolls.

**Hesitation watchpoints:**
- Does the PM understand "they're seeing read-only — corrections happen in HR/Safety"?
- Does the PM hesitate at the rose `Follow-Up Required` banner — would they click the CTA themselves or escalate to Safety?
- Does the PM look at the LifecycleGuide on the incident detail?

**Post-test questions:**
1. "What's the difference between 'Follow-Up Required' and 'Investigation Open'?"
2. "If you wanted to add a note about this incident, where would you do that?" (probes the PM-can't-edit boundary)
3. "What's missing from this crew view?"

**Pass / Fail criteria:**
- ✅ PASS: PM correctly identifies the read-only boundary, understands the follow-up status semantics, navigates between PM Crew Compliance ↔ incident detail.
- ❌ FAIL: Attempts to edit a CAPA from the PM portal, OR confuses Follow-Up Required vs Operationally Complete.

**Field notes:** _(same template)_

---

## Roll-up

After all 5 tests complete, fill `/app/memory/PHASE6_FIELD_ADOPTION_SPRINT_RESULTS.md`:
- Aggregate PASS/FAIL count
- 3 most common hesitations
- 3 surprises that suggest UX or coaching gaps
- 1 critical fail (if any) escalated to PRODUCTION_RISK_REGISTER.md

**Do not** turn validation into a feature backlog. Validation tells us what to fix. Fixes ship through the same disciplined sprint cadence — never as a reflex.

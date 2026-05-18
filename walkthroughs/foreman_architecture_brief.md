# Foreman Operational Architecture Brief

> **Phase:** honest operational systems analysis. No coaching authored.
> No workflows built. No tactical implementation drift.
>
> **Source:** iter227 Foreman walkthrough audit · 6 surfaces · 1 architectural
> decision surface raised in parallel.
>
> **Audience:** the operator making coordinated architectural decisions across
> a single internally-consistent foreman operational philosophy.
>
> **Status:** preview-only · decision-pending · operator-driven.

---

## 0 · The load-bearing principle

> **Not every operational behavior should become software workflow.**

Some moments are stronger when they remain:
- **verbal** — the foreman saying it out loud, into a phone, to a human
- **face-to-face** — the foreman's eyes on the crew at 07:00
- **operationally flexible** — the moment adapts to the day, not the form
- **leadership-driven** — the moment IS the leadership signal, not a record of it

Software workflow has costs: it displaces presence, it manufactures bureaucracy,
it converts trust moments into transactions, and it creates audit-trail pressure
that distorts the original behavior. The platform's strongest move is sometimes
to **explicitly refuse** to digitize a moment — and to coach the foreman about
why the moment stays human.

This brief evaluates each of the 6 surfaces against five outcome categories:

| Outcome | What it means |
|---|---|
| **remain intentionally human/verbal** | Platform makes a deliberate non-choice. May still author coaching that explains WHY the moment stays human. |
| **coaching-only** | Add a HelpTip family. No workflow surface. The coaching frames a moment that lives in existing tools. |
| **lightweight workflow** | A small visible surface (counter, list, tile) — no submit/approve mechanics. Discoverable, not blocking. |
| **structured workflow** | Full form / approval / state-machine. High maintenance, high friction. Reserved for true platform-of-record moments. |
| **strategic hold** | Decision deliberately deferred because it's interconnected with another architectural question not yet ready. |

---

## Surface 1 · 07:00 Crew-check / muster moment

### 1. Current real-world operational behavior
Foreman arrives at the yard around 06:15. By 07:00 they've made eye contact
with every crew member, registered who's late, who looks rough, who's
distracted, who's ready. This is a 5–10 minute moment of physical presence —
counting heads is the smallest part; reading the crew is the larger part.

### 2. Current platform behavior
None. The foreman has no digital crew-check / muster / headcount surface at
07:00. Time-tracking captures the same data ~30 minutes later, after work
starts — for HR/payroll, not for leadership decisions.

### 3. Operational tradeoffs
- **If digitized:** time-tracking already covers the data side (post-fact).
  A pre-work "tap to confirm crew" surface duplicates payroll workflow AND
  displaces the foreman's eye contact at the exact moment it matters most.
- **If left verbal:** no audit trail beyond the foreman's memory, but the
  audit trail isn't operationally needed — time tracking captures it 30
  minutes later anyway.

### 4. Cultural/leadership implications
This is one of the purest leadership moments in the foreman's day. Digitizing
it sends the message that the foreman's eyes don't matter — that the platform
trusts a tap more than a look. Field leadership invariant. Strong cultural
cost to digitization, minimal cultural cost to keeping verbal.

### 5. Mobile workflow implications
On 414px, a "muster screen" would consume above-the-fold real estate at the
exact moment the foreman should be looking AT the crew, not at the phone.
Mobile-first discipline argues AGAINST a screen here.

### 6. Downstream coordination impacts
None requiring digital capture. Dispatch reads crew counts from Daily Reports
(after work starts). HR gets attendance from time tracking. PM gets staffing
from Daily Reports. No downstream consumer needs the 07:00 number specifically.

### 7. Relationship to Dispatch continuity
Weak. Dispatch's 06:00 portal scan (iter226 step 01) doesn't depend on
real-time crew-check data; it reads overnight filings and yesterday's actuals.

### 8. Relationship to Supervisor onboarding / first-14-days
**Strong.** A new foreman doesn't automatically know that the 07:00 crew look
is leadership — they might think the spreadsheet is. The supervisor coaching
a new foreman through their first month would explicitly name this moment as
"don't put your face in the phone here."

### 9. Relationship to mid-day-defect held architecture
None directly.

### 10. Recommendation
**REMAIN INTENTIONALLY HUMAN/VERBAL.** Optionally — and only after the
Supervisor first-14-days family is unblocked — a `leadership.hub.morning` or
`crew-check` coaching tip could explicitly state the platform's refusal to
digitize this moment ("the crew-check is a look, not a tap"). That coaching
would be a **statement of operational philosophy**, not a navigation aid.

---

## Surface 2 · Leadership hub philosophy / coaching expectations

### 1. Current real-world operational behavior
Veteran foremen arrive at `/leadership`, scan tiles, tap. They know what they
want. New foremen arrive and are uncertain: which record gets filed when, why
the records list exists, whether they're supposed to read other foremen's
filings or just file their own.

### 2. Current platform behavior
Pure navigation surface. No contextual coaching. No framing of what the
leadership portal IS for the foreman.

### 3. Operational tradeoffs
- **Canonical-4 coaching:** new foremen get framing for what the portal is FOR
  (records of leadership, not paperwork). Costs above-the-fold space at 414px.
- **No coaching:** veterans tap faster. New foremen drift into trial-and-error.

### 4. Cultural/leadership implications
The leadership portal is the **collection** of records of how a foreman led.
The portal's existence is a cultural statement — "your leadership leaves a
trail" — that's currently silent. Coaching here would name the cultural
contract. Veterans don't need it named; new foremen do.

### 5. Mobile workflow implications
414px makes hub-level coaching expensive. A single collapsed canonical-4 block
(4 tips · 4 rows) is workable. Anything more is too much.

### 6. Downstream coordination impacts
None directly — the hub is purely navigational.

### 7. Relationship to Dispatch continuity
None.

### 8. Relationship to Supervisor onboarding / first-14-days
**Moderate.** A supervisor introducing a new foreman to the leadership portal
benefits from the platform itself naming what the portal is. Reduces the
"how do I show them around" burden on the supervisor.

### 9. Relationship to mid-day-defect held architecture
None.

### 10. Recommendation
**COACHING-ONLY.** Single canonical-4 family on `leadership.hub`, default-
collapsed, scoped to leadership + admin. Cultural anchor candidate (operator-
decision-required):

> *"These aren't forms — they're the record of how you led your crew. The
> people who read them downstream are deciding whether to trust your call
> next time."*

Explicitly: NO leaf surfaces, NO mistake/example expansion, NO discovery
counter. The hub is a switchboard; its coaching should be minimal and
philosophical, not procedural.

---

## Surface 3 · Foreman side of the Transfer interaction

### 1. Current real-world operational behavior
Dispatch sends a transfer. iter226 coaching tells the dispatcher to CALL the
receiving foreman BEFORE opening the Transfer. In a healthy flow the foreman
knows the unit is coming before the truck arrives. They sign for it; the unit
is on their job. If the dispatcher skipped the call, the foreman is surprised.

### 2. Current platform behavior
iter226 authored the DISPATCHER side (`dispatch.transfers` family · 4 canonical
+ 4 leaves). The receiving foreman has NO parallel coaching. They see the
transfer record in their Daily Report inputs or in `/asset-transfers`, but no
coaching frames how to receive it.

### 3. Operational tradeoffs
- **Coaching-only mirror of iter226:** anchors the receiving side
  symmetrically. "A transfer landing in your queue is a conversation, not an
  order." Reinforces iter226 call-first discipline FROM the foreman side.
- **Lightweight workflow (acknowledge / question button):** gives the foreman
  a one-tap "ok" or "wait, call me." Closes the loop iter226 opened.
- **Structured workflow (accept/decline state machine):** introduces
  bureaucracy. Encourages text-first behavior — the opposite of iter226's
  call-beats-text anchor.

### 4. Cultural/leadership implications
The Transfer arriving is operationally a moment of trust between dispatch and
foreman. Adding a "decline" button gives the foreman power BUT actively
encourages text-instead-of-call — which directly contradicts the iter226
anchor. A "wait, call me" button might preserve the call discipline; an
"accept" button corrodes it.

### 5. Mobile workflow implications
414px in a truck cab handles a single ACK button fine. Anything more
elaborate becomes hostile in field conditions.

### 6. Downstream coordination impacts
Dispatch needs to know the truck should/shouldn't roll. Currently they
learn from the phone call (per iter226). If the phone call happens, the
button is redundant.

### 7. Relationship to Dispatch continuity
**Direct and primary.** This surface mirrors iter226 1:1. Whatever the
foreman side becomes, it must be internally consistent with the dispatcher
side. Any workflow added here CREATES PRESSURE to walk back the iter226
call-first anchor.

### 8. Relationship to Supervisor onboarding / first-14-days
**Moderate.** The supervisor teaching a new foreman the receiving discipline
("the truck is on its way — call the dispatcher back, don't just text") is
the exact moment this coaching reinforces.

### 9. Relationship to mid-day-defect held architecture
**Adjacent.** Many transfers are triggered by mid-day defects (the broken
unit needs a backup). Authoring foreman-side transfer coaching without
addressing mid-day-defect creates an asymmetry where the FOREMAN knows what
to do when a transfer arrives but doesn't know what to do when their own
unit goes down. That asymmetry is acceptable as long as the strategic hold
on mid-day-defect remains explicit.

### 10. Recommendation
**COACHING-ONLY** mirror of iter226 dispatch.transfers. Author
`leadership.transfer-receive` family — canonical-4 + 1-2 leaves max. Anchor
the symmetry: the conversation IS the contract. NO ack/decline button. The
absence of a workflow is the architectural statement.

Cultural anchor candidate (operator-decision-required):

> *"A transfer landing in your queue is a conversation, not an order. If you
> didn't get a call first, that's the call you need to make."*

That anchor closes the loop iter226 opened without adding a surface that
would erode the call-first discipline.

---

## Surface 4 · `field-leadership.records` — filer-side vs reviewer-only voice

### 1. Current real-world operational behavior
Foreman files a write-up Tuesday. Two weeks later, an HR conversation comes
up. The foreman opens `/leadership/records` to remember context. They need
to recall: did I document the conversation? did I include the third late
day? what exactly did I write?

### 2. Current platform behavior
iter218 authored `field-leadership.records` reviewer-side coaching
("reviewing isn't auditing"). This voice speaks to HR reading other people's
filings. When the foreman reads their OWN filings, the same reviewer-voice
appears — and it speaks past them. The foreman isn't an auditor reviewing
someone else's work; they're a leader reading their own history.

### 3. Operational tradeoffs
- **Dual-voice (author parallel filer-side family):** the foreman sees
  coaching that anchors on "your record, your context, your evidence of
  leadership" while HR continues to see the iter218 anchor.
- **Reviewer-only (status quo):** single tight voice. Foreman gets
  misframed when reading their own filings.
- **Voice consolidation (rewrite iter218 to address both):** dilutes the
  iter218 anchor. Reject.

### 4. Cultural/leadership implications
The filer-side anchor should land "your records belong to you — they're not
evidence FOR or AGAINST you, they're the record of how you led." This is a
different cultural register from the reviewer-side anchor and deserves its
own surface. Conflating them weakens both.

### 5. Mobile workflow implications
Foremen read records on mobile; HR on desktop. The audience-detection is
already scope-driven. Adding a filer-side family at the same form-key just
means the scope filter delivers the right voice to the right reader.

### 6. Downstream coordination impacts
None. Filer-side voice doesn't affect HR's reading or the downstream
records flow. This is purely an addition for the reading-foreman.

### 7. Relationship to Dispatch continuity
None.

### 8. Relationship to Supervisor onboarding / first-14-days
**Strong.** A supervisor teaching a new foreman "go back and read what you
wrote three months ago — that's how you'll calibrate your future filings"
is exactly the moment filer-side coaching supports.

### 9. Relationship to mid-day-defect held architecture
None.

### 10. Recommendation
**COACHING-ONLY.** Author `field-leadership.records.filer` as a parallel
scope variant. iter218 stays reviewer-only (`field-leadership.records` with
hr scope). New `field-leadership.records.filer` scoped leadership +
admin — does NOT replace iter218, runs alongside it.

Anchor candidate (operator-decision-required):

> *"These are YOUR records. Read them to remember what you did, not to
> defend what you did. They were already true when you filed them."*

The same surface delivers different voices to different readers — the
scope mechanism IS the architecture.

---

## Surface 5 · Foreman End-of-Day wrap surface

### 1. Current real-world operational behavior
Foreman finishes the Daily Report at 17:30. Drives off site. Sometime
between the truck and home, they remember (or fail to remember) that the
recognition note for Joe wasn't filed, the open write-up still needs the
late-arrival timestamp, and tomorrow's headcount is short one operator.
Most of this dies in the parking lot.

### 2. Current platform behavior
Daily Report is the de-facto wrap, but DR is about today's WORK, not about
the foreman's open desk-items. The leadership hub has no "what's still open
from your filings today" surface.

### 3. Operational tradeoffs
- **Structured workflow (formal EOD checklist):** literally blocks driving
  off without confirming. High bureaucracy cost. High audit trail.
- **Lightweight workflow (passive "your open items" tile on leadership
  hub):** discoverable, non-blocking. Foreman glances, decides.
- **Coaching-only:** frames the wrap moment, points at existing tools.
  Doesn't actually help locate open items.
- **Remain verbal:** veteran foremen do this in their head. New foremen
  don't, and the gap is real.
- **Strategic hold:** this surface and the foreman → super handoff (Surface
  6) are two halves of the same architectural decision.

### 4. Cultural/leadership implications
The EOD wrap is what separates a foreman from a crew lead. The discipline
of "I don't drive home with anything undone that should have closed today"
is a leadership invariant. Software can support it OR replace it — replacing
it would be a cultural loss; supporting it lightly could be a cultural win.

### 5. Mobile workflow implications
Truck-cab moment. A passive "your open items: 2" glance is right. A
structured form with required fields is wrong. Mobile discipline argues
for lightweight or coaching-only.

### 6. Downstream coordination impacts
Dispatch, super, HR all benefit from the foreman closing same-day loops.
But none of them currently DEPENDS on a foreman-EOD surface — they
self-discover gaps. So the platform doesn't need to capture wrap data
for downstream; it needs to support the FOREMAN's leadership discipline.

### 7. Relationship to Dispatch continuity
Moderate. iter226 dispatch.handoff is the receiving end of whatever the
foreman delivers tonight. If the foreman doesn't wrap, the dispatch
handoff inherits gaps.

### 8. Relationship to Supervisor onboarding / first-14-days
**Very strong.** The supervisor teaching the wrap discipline to a new
foreman is the high-value coaching moment. Mirrors iter226 dispatch.handoff
philosophy on the field side.

### 9. Relationship to mid-day-defect held architecture
None directly.

### 10. Recommendation
**STRATEGIC HOLD pending Supervisor first-14-days decision.** This surface
and the foreman → super handoff (Surface 6) are interconnected — both must
be decided together. Authoring one without the other would create an
asymmetry where the foreman wraps but has nowhere to deliver, OR delivers
but hasn't wrapped.

Candidate direction (operator-decision-required when held lifts):
**lightweight workflow** — a passive "your open items today" glance-tile on
the leadership hub at 414px, paired with a coaching family that anchors
the discipline. NO structured form, NO blocking, NO required-fields.

---

## Surface 6 · Foreman → Superintendent handoff surface

### 1. Current real-world operational behavior
Foreman calls super at 18:00 or texts. Super either answers, replies, or
catches up tomorrow. The "anything I need to know for tomorrow?" question
lives entirely in this human exchange. No platform support exists or is
referenced.

### 2. Current platform behavior
Nothing. The foreman → super communication is invisible to the platform.

### 3. Operational tradeoffs
- **Structured workflow (formal handoff form):** audit trail, super can
  re-read. Replaces the human call with paper. High risk of "FYI handoff"
  anti-pattern (iter226 dispatch.handoff.changes leaf warned against this).
- **Lightweight workflow (handoff note attached to Daily Report or thread
  on leadership hub):** optional capture. Lives next to existing tools.
- **Coaching-only (parallel to iter226 dispatch.handoff for the foreman):**
  reinforces the call discipline. Doesn't store the result.
- **Remain verbal:** this IS the foreman-super relationship. Software
  intermediating it is a leadership wound.
- **Strategic hold:** this is the Supervisor first-14-days architecture.

### 4. Cultural/leadership implications
**Highest cultural stakes of any surface in this brief.** The foreman → super
end-of-day call is the most operationally sacred moment in the field
leadership chain. Software inserting itself here would either replace the
call (catastrophic) or audit-trail the call (corrosive). Whatever is built
must STRENGTHEN the call, not substitute for it.

### 5. Mobile workflow implications
The call is already mobile. A structured form is hostile in field
conditions. A lightweight "what I told the super tonight" capture-after-
the-fact note could work without displacing the call.

### 6. Downstream coordination impacts
Super, ops oversight. If the foreman doesn't make the call, the super
doesn't know — and tomorrow's escalations land cold. The platform doesn't
need to CAPTURE the call but could support the discipline of MAKING it.

### 7. Relationship to Dispatch continuity
**Direct symmetry with iter226 dispatch.handoff.** The dispatcher hands
off to the next dispatcher; the foreman hands off to the super. Different
authority gradient, same operational moment. Whatever this becomes
should be philosophically consistent with iter226.

### 8. Relationship to Supervisor onboarding / first-14-days
**This decision IS the Supervisor first-14-days architecture.** The
supervisor's receiving side of this handoff is the supervisor's primary
operational moment in their first 14 days. Cannot be decided in isolation.

### 9. Relationship to mid-day-defect held architecture
None directly — this is the END-of-day surface. Mid-day-defect is a
separate held question.

### 10. Recommendation
**STRATEGIC HOLD · this surface IS the Supervisor first-14-days
architecture · decide together.**

Candidate direction (operator-decision-required when held lifts):
**coaching-only mirror of iter226 dispatch.handoff for the foreman side
PLUS coaching-only for the supervisor side** — preserving the human call
as the contract. The supervisor first-14-days coaching would anchor the
receiving discipline ("when the foreman calls at 18:00, that's the day,
not a status update — listen for what they're NOT saying"). The foreman
coaching would anchor the call discipline ("the super needs the call
even on days that went smoothly — silence is the loudest signal").

Explicitly: **NO** structured form. **NO** required handoff document. The
call is the contract; software's job is to support it being made, not to
replace it.

---

## Cross-surface synthesis

### Which moments should remain intentionally human/verbal

| Moment | Why |
|---|---|
| **07:00 crew-check** | Eye contact IS the leadership signal — digitizing it would corrode the moment it captures |
| **Foreman → super phone call** (the moment itself) | Most operationally sacred field-leadership exchange — software should support, never replace |
| **Mid-day-defect escalation** | Strategic hold — operator architectural decision, not a tactical patch |

### Which moments should become coaching-only

| Surface | Family | Anchor candidate |
|---|---|---|
| Leadership hub philosophy | `leadership.hub` canonical-4 | "These aren't forms — they're the record of how you led." |
| Foreman side of Transfer | `leadership.transfer-receive` canonical-4 + leaf | "A transfer landing in your queue is a conversation, not an order." |
| Filer-side records voice | `field-leadership.records.filer` | "These are YOUR records. Read them to remember, not to defend." |

### Which moments should become lightweight workflow

| Surface | Form | Notes |
|---|---|---|
| Foreman EOD wrap | Passive "your open items today" glance-tile | Held pending Supervisor first-14-days decision |

### Which moments should remain strategic hold

| Surface | Reason |
|---|---|
| Foreman EOD wrap | Interconnected with Supervisor first-14-days |
| Foreman → super handoff (surface architecture) | IS the Supervisor first-14-days architecture |
| Mid-day-defect routing | Operator pre-existing architectural hold per walkthrough_pass.md §10 |

### What this brief is NOT recommending

- **No structured workflows.** Zero of the 6 surfaces should become full
  form/approval/state-machine flows. The cultural cost is higher than the
  operational benefit at every surface evaluated.
- **No KPI/dashboard surfaces.** Especially not on the EOD wrap (which is
  the highest-risk surface for grading-foremen drift).
- **No LMS layering.** The Leadership hub coaching is one canonical-4 block,
  not a course.
- **No popup interruptions.** All coaching default-collapsed, all glance-
  tiles passive.
- **No analytics capture.** Walkthrough findings stay editorial; no Mongo
  collection of foreman-wrap events.

### Internal-consistency check across the 6 surfaces

If the operator approves the recommendations above, the resulting Foreman
operational philosophy is internally coherent:

1. The platform refuses to digitize moments where presence IS the leadership.
2. The platform coaches the moments where new foremen need framing.
3. The platform offers ONE lightweight glance-tile (EOD wrap) — and only
   AFTER the supervisor side is designed to receive it.
4. The platform never inserts itself between a foreman and a phone call.
5. The strategic holds remain held until operator releases them.

That's a Foreman architecture that says: **the platform supports field
leadership; it does not replace it.**

---

## Decision-ready summary table

| # | Surface | Outcome | Authoring conditional on |
|---|---|---|---|
| 1 | 07:00 crew-check | **Remain human/verbal** · optional coaching only after Supervisor unblocks | Supervisor first-14-days release |
| 2 | Leadership hub | **Coaching-only** · single canonical-4 · default-collapsed | Operator approval of anchor |
| 3 | Foreman side of Transfer | **Coaching-only** · canonical-4 + 1-2 leaves · mirror of iter226 | Operator approval of anchor |
| 4 | Records filer-side voice | **Coaching-only** · parallel scope variant | Operator approval of anchor |
| 5 | Foreman EOD wrap | **Strategic hold** · candidate: lightweight workflow + coaching | Supervisor first-14-days release |
| 6 | Foreman → super handoff | **Strategic hold** · IS the Supervisor first-14-days architecture | Operator architectural decision |

**Three coaching-only surfaces are operator-approvable today (#2, #3, #4)
without disturbing any held architecture. The other three (#1, #5, #6) are
interconnected and should be decided as a coordinated set when the operator
chooses to unblock the Supervisor first-14-days family.**

---

*End of brief. Preview only. No coaching authored. No workflows built. No
tactical drift. Awaiting operator architectural decision.*

# Operational Verbiage Doctrine — Phase IV-A

**Iteration:** iter437 · Phase IV-A · 2026-02
**Status:** 🟢 LEXICON LOCKED · ENFORCED IN ALL ADMIN COPY FROM THIS POINT FORWARD
**Supersedes:** `TERMINOLOGY_DOCTRINE.md` (Phase IV-0) — extends with verb tables, escalation grammar, and mobile compression rules.

This is the master lexicon for the platform. Every label, button, header, email subject, modal title, and toast string must derive from this doctrine. When two engineers reach for different words for the same operational concept, the wrong word is whichever one is not here.

The platform is an **operational command system** for heavy civil construction. It is not a SaaS dashboard, not a workspace, not a hub. The verbiage must sound the way a senior superintendent speaks on a job-site radio: precise, calm, and unambiguous.

---

## I. Voice — what the system sounds like

| It sounds like | It does NOT sound like |
|---|---|
| A senior superintendent giving direction | A help-desk script |
| A flight-deck callout | A marketing landing page |
| A maintenance log entry | A chat assistant |
| A clearance-to-proceed signal | A productivity tool tagline |

Three rules govern every string in the system:

1. **Verb-first when something must be done.** ("Approve report" not "Report awaiting approval.")
2. **Noun-first when describing what something is.** ("Daily Report · 2026-02-27" not "Submitted today.")
3. **No second-person address in operational copy.** ("Submit" not "Submit your report." The operator is the implicit subject.)

---

## II. Canonical verbs (the only verbs allowed in primary actions)

| Approved verb | Use when | Forbidden synonyms |
|---|---|---|
| **Submit** | An operator finalizes a record they authored | Send · Push · Save & Send |
| **Approve** | An authorized reviewer accepts a submitted record | Accept · OK · Confirm (when reviewing) · Sign off |
| **Reject** | A reviewer returns a record requiring rework | Deny · Decline · Send back |
| **Acknowledge** | An operator confirms receipt of an alert/escalation | Got it · Dismiss · Mark seen |
| **Escalate** | Surface an issue to a higher accountability tier | Notify up · Flag urgent · Alert manager |
| **Assign** | Bind a person to a job, asset, or action | Allocate · Hand off · Set owner |
| **Reassign** | Transfer an existing assignment | Change owner · Move · Hand off |
| **Dispatch** | Release a crew/asset to a field destination | Send out · Roll · Deploy |
| **Recall** | Return a dispatched crew/asset | Bring back · Cancel dispatch |
| **Schedule** | Place an event/task on the operational calendar | Plan · Book · Set up |
| **Reschedule** | Move an existing scheduled item | Push back · Reslot · Move |
| **Close** | Mark a record permanently complete | Finalize · Archive · Done |
| **Reopen** | Restore a closed record to active state | Undo close · Reactivate |
| **Hold** | Suspend operational progress, awaiting clearance | Pause · Wait · Block |
| **Release** | Lift a hold | Unblock · Resume |
| **Resolve** | Bring an incident/issue to a documented close | Fix · Handle · Address |
| **Review** | Read for decision (not just to look) | Check · Look at · Inspect (reserved) |
| **Inspect** | Field-level physical examination per checklist | Look over · Walk · Audit (reserved) |
| **Audit** | Compliance-level structured examination | Check · Inspect · Review |
| **Log** | Record an event into the operational record | Note · Add · Capture |
| **Report** | Compose a formal record (Daily Report, Incident Report) | Submit a note · File a thing |
| **Export** | Produce a file for downstream use | Download (reserved for files retrieved as-is) |
| **Download** | Retrieve an existing file unchanged | Export · Get · Pull |

A primary button must use exactly one of these verbs. Secondary buttons (footer, "More" menu) may use additional verbs — but those must also live in this table.

---

## III. Canonical nouns (the only names for the operational entities)

| Entity | Approved noun | Forbidden synonyms |
|---|---|---|
| The whole platform | **the platform** (lowercase) or **MASCI Safety** (formal) | the app · the system · the tool · the portal |
| The admin portal | **the admin portal** | the back-office · the dashboard · the console |
| The field portal | **the field portal** | the foreman app · the mobile app |
| A scheduled work record | **Job** | Project · Site · Gig |
| A named delivery package | **Project** (reserved — multi-job scope) | (do not use interchangeably with Job) |
| A field-leadership end-of-day record | **Daily Report** | EOD · Report · Log · DR |
| A safety/quality field check | **Inspection** | Check · Walk · Survey |
| A formal regulatory review | **Audit** | Inspection · Review |
| A documented operational deviation | **Incident** | Issue · Event · Problem (when safety-related) |
| A non-safety operational record | **Operations Event** | Issue · Note · Thing |
| A piece of owned/leased machinery | **Asset** (formal) / **Equipment** (display) | Item · Unit · Machine |
| A vehicle with an operator | **Vehicle** | Truck · Ride · Unit |
| A pre-shift machinery check | **Pre-Op** | Pre-trip · Walk-around · Safety check |
| A person on payroll | **Crew member** (field) · **Employee** (HR/admin) | User · Staff · Resource |
| A grouped set of crew members | **Crew** | Team · Squad · Group |
| A field supervisor | **Foreman** (singular operator) · **Field leadership** (collective) | Lead · Manager · Boss |
| A central dispatcher/PM | **Project Manager (PM)** | Coordinator · Admin |
| An automatic platform message | **Notification** | Alert · Ping · Message |
| A high-urgency notification | **Escalation** | Urgent alert · Critical ping |
| A binding action that must be done | **Action Item** | Task · TODO · Ticket |
| A login identity | **Account** | User · Profile (reserved for personal settings) |
| Permissions scope | **Role** | Group · Tier (reserved) |
| The pre-deploy verification | **Deploy Gate** | CI check · Test |

Two-word entities are PascalCase in body copy (`Daily Report`) and Title Case in headings (`Daily Reports`). Never abbreviate in primary UI — `Daily Report` not `DR`. Abbreviations are allowed only in dense data tables where the column header is the full term.

---

## IV. Forbidden wording (the words the platform will not say)

Any string containing the following must be rewritten before merge. The deploy gate `verify_no_marketing_copy.py` will fail the build (Phase IV.A.4).

### Marketing / SaaS slop — forbidden everywhere
- "Empower" / "empowering"
- "Seamless" / "seamlessly"
- "Effortless"
- "Streamline" / "streamlined"
- "Unlock" / "unleash"
- "Cutting-edge" / "next-gen"
- "Revolutionize" / "transform" (when describing UI)
- "AI-powered" (the system uses ML in specific places — say so specifically, not as a brand)
- "Smart [anything]" (smart dashboard, smart filter — name what it actually does)
- "Just" / "simply" / "easily" (these patronize the operator)
- "Awesome" / "amazing" / "great" (in toasts/success messages)
- "Oops" / "Whoops" / "Uh oh" (in error messages)

### Robotic / AI-sounding patterns — forbidden
- "I can help you with…"
- "Let me know if you need…"
- "Feel free to…"
- "Don't hesitate to…"
- "We're here to help"
- "Sure thing!" / "No problem!"
- "Got it!" (replace with `Acknowledged.` or just `OK`)
- Any exclamation mark in operational copy. Exclamation marks are reserved for genuine emergencies — and even then, the severity color carries the load, not punctuation.

### Vague labels — forbidden
- "Manage [X]" as a primary action (manage what? approve? reassign? close?)
- "View Details" (use the noun: `Open Report`, `Open Job`)
- "Click here" / "Tap here"
- "More info" (link to the doc with a noun)
- "Settings" alone (must be qualified: `Notification Settings`, `Account Settings`)
- "Other" as a category
- "Misc" / "Miscellaneous"
- "Stuff" / "Things"

### Duplicate-meaning words — pick one
- Project ⇄ Job → **Job** (operational record) · **Project** (multi-job delivery scope) — never substitutable
- Inspect ⇄ Audit → **Inspection** (field) · **Audit** (compliance) — never substitutable
- Notify ⇄ Alert → **Notification** (informational) · **Escalation** (urgent) — never substitutable
- User ⇄ Operator ⇄ Person → **Account** (login) · **Crew member / Foreman / PM / etc.** (role) — never just "user"
- Save ⇄ Submit → **Save** (draft, still editable) · **Submit** (finalize and route)

---

## V. Severity wording map (the only severity words allowed)

| Severity | Word (UI) | Word (email subject) | Color | Operator response |
|---|---|---|---|---|
| 0 · Informational | `Note` | (no prefix) | slate | Read at leisure |
| 1 · Routine | `Reminder` | `[Reminder]` | blue | Read same shift |
| 2 · Attention required | `Attention` | `[Attention]` | amber | Read same day · act if able |
| 3 · Action required | `Action Required` | `[Action]` | orange | Act same shift · cannot defer |
| 4 · Escalation | `Escalation` | `[Escalation]` | red | Act now · acknowledge within 1 hour |
| 5 · Emergency | `Emergency` | `[EMERGENCY]` | red + siren glyph | Act immediately · phone fallback if unacknowledged in 5 min |

**Rule:** A given record may only escalate one tier at a time. Skipping tiers (e.g., a `Note` becoming an `Escalation` directly) is a doctrine violation. The escalation engine enforces this by requiring an `Action Required` state to exist before `Escalation` is generated.

**Anti-alarm-fatigue rule:** No more than 3 `Attention` items and 1 `Action Required` may appear in the operator's view at once. Beyond that, the platform groups them into a single summary card. Tier 4 and 5 always show individually.

---

## VI. Escalation language (the exact grammar of "you must act")

Escalations are the most psychologically loaded copy in the system. They must:

1. **State the operational fact, not the alarm.** ✅ `Daily Report from Crew 7 missing for 2 shifts.` ❌ `Crew 7 hasn't submitted yet!!!`
2. **Name the accountability owner.** ✅ `Owner: J. Ramirez (Foreman).` ❌ `Someone needs to handle this.`
3. **Specify the next action verb.** ✅ `Required: Approve or Reject within this shift.` ❌ `Please review when you can.`
4. **State the deadline as an operational time, not a countdown.** ✅ `By end of shift today (17:00 local).` ❌ `In 4 hours 23 minutes.` (Countdowns create panic; deadlines create planning.)
5. **No emoji. No exclamation. No bold-red-shouting.** The severity color and the `Escalation` prefix carry the urgency. Punctuation is silence.

### Escalation template (canonical)

```
[Escalation] {Noun-phrase of the operational fact}

Owner: {Name} ({Role})
Required: {Verb} by {Operational deadline}.
Context: {One sentence, ≤ 20 words}.
```

**Example:**
```
[Escalation] Daily Report missing — Crew 7

Owner: J. Ramirez (Foreman)
Required: Submit by end of shift today (17:00 local).
Context: Two consecutive shifts without a Daily Report. Project: Rt-441 widening.
```

---

## VII. Accountability language

The platform exposes accountability without blaming.

| Situation | ✅ Say | ❌ Don't say |
|---|---|---|
| A person owns the next action | `Owner: J. Ramirez (Foreman)` | `Assigned to J. Ramirez!` · `J. Ramirez should…` |
| A person missed a deadline | `Overdue by 2 shifts · Owner: J. Ramirez` | `J. Ramirez is late!` · `J. Ramirez failed to…` |
| A handoff occurred | `Reassigned from J. Ramirez → M. Chen at 14:22 by PM` | `Stolen by M. Chen` · `M. Chen took over` |
| Multiple owners are valid | `Owners: J. Ramirez, M. Chen (joint)` | `Whoever can…` |
| No owner yet | `Unassigned · Awaiting PM assignment` | `Nobody owns this!` · `???` |

Names appear with role in parentheses on first mention in a view. Subsequent mentions drop the role. Roles never appear without a name.

---

## VIII. Workflow terminology (state names — the only allowed state strings)

State names appear in tables, badges, and emails. They must be one or two words, lowercase in code, Title Case in UI.

| Domain | Allowed states |
|---|---|
| Daily Report | `Draft`, `Submitted`, `Approved`, `Rejected`, `Closed` |
| Incident | `Open`, `Investigating`, `Mitigated`, `Closed` |
| Inspection | `Scheduled`, `In Progress`, `Completed`, `Failed`, `Closed` |
| Audit | `Scheduled`, `In Progress`, `Findings Logged`, `Resolved`, `Closed` |
| Dispatch | `Pending`, `Dispatched`, `On Site`, `Returned`, `Recalled` |
| Asset (Equipment) | `Active`, `In Maintenance`, `Down`, `Retired` |
| Action Item | `Open`, `In Progress`, `Blocked`, `Resolved`, `Closed` |
| Account | `Active`, `Suspended`, `Disabled` |

Forbidden states (anywhere): `Pending` outside Dispatch · `Done` (use `Closed`) · `Cancelled` (use `Closed` with a `closed_reason`) · `Archived` (records are never archived; they are `Closed` and filtered out of default views) · `New` (use `Open` or the lifecycle equivalent) · `In Review` (use `Submitted` for the report-side state and `In Progress` for the reviewer-side state — never mix the two viewpoints).

State transitions are documented per-domain in their respective service modules. The verbiage doctrine controls what the states are *called*; it does not control how they transition.

---

## IX. Calm operational coaching (the sublines that teach without lecturing)

Every domain header and every page H1 carries a one-sentence subline. The subline answers "what is this and why am I here?" in ≤ 14 words.

### Canonical examples

| Surface | H1 | Subline |
|---|---|---|
| Operations domain | `Operations` | `Field activity across all active projects.` |
| Daily Reports list | `Daily Reports` | `Review and approve field-leadership submissions.` |
| A single Daily Report | `Daily Report · {date} · Crew {n}` | `Submitted by {Foreman} at {time}. {Crew_count} entries.` |
| Workforce domain | `Workforce` | `People, certifications, time-off, onboarding.` |
| Equipment & Fleet domain | `Equipment & Fleet` | `Asset lifecycle, maintenance, pre-op, suppliers.` |
| Pre-Op list | `Pre-Op Checks` | `Today's pre-shift checks across all dispatched units.` |
| Communications domain | `Communications` | `Email routing, notifications, escalation flow.` |
| Notification settings page | `Notification Settings` | `Choose what reaches you and when.` |
| Safety & Compliance domain | `Safety & Compliance` | `Incidents, audits, certifications, OSHA.` |
| Incidents list | `Incidents` | `Open and recently-closed safety/quality deviations.` |
| Equipment maintenance | `Maintenance Schedule` | `Upcoming services, parts on order, downtime forecast.` |
| System & Governance domain | `System & Governance` | `Storage, backups, deploy health, observability.` |

### Coaching prose — forbidden patterns

- ❌ "Welcome to [X]! Here you can…"
- ❌ "Here's where you'll find all your…"
- ❌ "Easily manage your…"
- ❌ Lists of features ("View, edit, approve, comment…")

Sublines never list features. They name the operational purpose.

---

## X. Admin vs Field wording separation

The admin portal addresses a desktop operator with time to read. The field portal addresses a foreman on an iPad in the sun with one thumb free. The wording compresses accordingly.

| Concept | Admin string | Field string (mobile) |
|---|---|---|
| Submitting a Daily Report | `Submit Daily Report` | `Submit` |
| Approving a Daily Report | `Approve Daily Report` | `Approve` |
| Rejecting with feedback | `Reject and Request Revision` | `Reject` (modal asks reason) |
| Acknowledging an escalation | `Acknowledge Escalation` | `Acknowledge` |
| Pre-Op check completion | `Mark Pre-Op Check Complete` | `Done` (only after all items checked) |
| An incident report header | `Incident · {id} · {short_title}` | `Incident #{short_id}` |
| Time stamps | `2026-02-27 14:22 EST` | `Today 14:22` |
| Dates within current week | `2026-02-27 (Thursday)` | `Thu` |

**Rule:** A field string is the admin string with adjectives, prepositions, and articles stripped — but never the verb. The verb must remain identical so muscle memory crosses portals.

---

## XI. Mobile wording compression rules

When wording must fit a narrow screen (< 380 px):

1. **Drop articles** ("Submit Daily Report" → "Submit Daily Report" stays; "Approve the Report" → "Approve Report"). Articles never carry meaning here.
2. **Drop pronouns** ("Your jobs" → "Jobs"). The operator owns their own view.
3. **Drop possessives** ("J. Ramirez's submission" → "J. Ramirez · submission").
4. **Use middle-dot separators** instead of commas in dense metadata (`Crew 7 · Rt-441 · 14:22`).
5. **Never abbreviate the verb.** ("Submit" never becomes "Sub" or "Sbmt".)
6. **Never abbreviate severity.** "Escalation" stays "Escalation" — never "Esc" or "!!".
7. **Numbers over words when both work.** "2 shifts" not "two shifts."

---

## XII. Anti-patterns observed in the codebase today (must be eliminated)

These are real strings currently shipping that violate this doctrine. Phase IV.A.4 ships a deploy gate that rejects them.

| File / location | Current string | Replace with |
|---|---|---|
| Toast on Daily Report submit | `Awesome! Report sent 🎉` | `Daily Report submitted.` |
| Email subject (overdue) | `URGENT!!! Submit your report NOW` | `[Action Required] Daily Report overdue — Crew {n}` |
| Modal title (reject) | `Send it back?` | `Reject Daily Report` |
| Sidebar entry | `Stuff` (legacy menu) | (remove · merge into governed domain) |
| Empty state | `Nothing here yet 🙂` | `No submissions for this date range.` |
| Notification (push) | `Hey! Something needs your attention` | `[Attention] {Operational fact}` |
| Error toast | `Oops! That didn't work` | `Submission failed. Try again or contact PM.` |
| Confirmation | `Got it!` | `Acknowledged.` |

---

## XIII. Operator-trust principles (why the verbiage matters)

The platform earns subconscious operator trust when:

1. **Every string the operator reads is identical to what they'd say out loud on radio.** Verbiage that diverges from spoken operational language signals "this software does not understand the work."
2. **The same verb always means the same action.** "Submit" never silently becomes "Save," "Send," or "Push" in different views.
3. **The same noun always names the same thing.** "Daily Report" is never called "Log" in one place and "EOD" in another.
4. **Severity escalates predictably.** Tier 2 never jumps to Tier 4 without Tier 3 in between. The operator learns the rhythm.
5. **No string ever lies about state.** A toast that says "Submitted" must mean the row is committed to the database. No optimistic UI for state-bearing actions.
6. **No string ever apologizes.** The platform either succeeds or names the failure. It does not say "Sorry," "We'll try better," or "Oops."

Verbiage is not branding. Verbiage is the audible surface of operational discipline.

---

## XIV. Enforcement

- **Deploy gate (Phase IV.A.4):** `scripts/verify_admin_copy.py` will grep frontend bundles for the forbidden-wording list in §IV and §XII. Build fails if any match.
- **PR review checklist:** Any PR that adds a button, toast, modal, email, or notification must declare in the PR description which canonical verb/noun it uses.
- **Designer/PM playbook:** This doctrine is the source of truth for all copy. Designers do not invent verbiage; they apply this lexicon.
- **Quarterly lexicon review:** New operational concepts (e.g., new domains) require a doctrine amendment PR before any UI string ships.

---

## Verdict

🟢 **LEXICON LOCKED.** The platform now has one voice, one vocabulary, one severity ladder, one set of allowed verbs and nouns. From this iteration forward, anything outside this doctrine is a regression.

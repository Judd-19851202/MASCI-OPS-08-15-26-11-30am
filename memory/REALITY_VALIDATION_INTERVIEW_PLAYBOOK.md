# REALITY VALIDATION INTERVIEW PLAYBOOK
## OCEP Phase 1 · Operational Completion Evidence Program

**Date opened**: 2026-06-02
**Authority**: OMEGA · OCEP (operator-issued)
**Mode**: READ-ONLY · evidence collection harness
**Status**: Awaits operator-conducted interview cycles
**Scope**: 9 personas · Reality validation prior to any further engineering

---

## 0 · Doctrine

This playbook is the **only** authorized vehicle for collecting Priority-1 reality evidence under the FOCP Final Directive. It produces:
- 9 Persona Readiness Scores (0–100)
- 1 Platform Dependence Score (composite)
- 1 Jaymn Dependence Score (composite)

The AI agent **cannot** conduct these interviews. The operator (or a designated session facilitator) conducts them; the playbook is the protocol they follow.

No interview result is admissible toward Final Certification unless the persona's full interview is completed (all 10 sections, scoring rubric scored, escalation matrix filled).

---

## 1 · Pre-interview setup (operator)

Before any session:

| Item | Requirement |
|---|---|
| Recording consent | Verbal or written. Mandatory. |
| Interview environment | Quiet · operator on actual device they use in the field (phone for Laborer/Foreman; laptop for PM/Safety/HR/Dispatch/Shop/Exec) |
| Session length | 60 minutes per persona · hard stop |
| Recorder role | Note observation, NOT commentary. Capture verbatim quotes. |
| Tools open | Preview URL · production URL · the persona's role-specific landing page |
| Notes location | `/app/memory/interviews/{persona}_{date}.md` (operator-created) |

---

## 2 · Capture taxonomy (constant across all 9 personas)

Every observed event must be tagged with one of:

| Tag | Definition | Example |
|---|---|---|
| `CONFUSION` | Operator pauses ≥ 3s and asks "what does this mean?" / "where do I go?" | "What's the difference between Reviewed and Closed?" |
| `HESITATION` | Operator hovers / re-reads / starts then stops | Cursor hovers Save, drifts away, returns |
| `WRONG_ASSUMPTION` | Operator narrates an incorrect expectation | "I'll click here to send it to Safety" — but the button routes to HR |
| `MISSING_KNOWLEDGE` | Operator says "I don't know what to do here" | — |
| `MISSING_GUIDANCE` | No on-screen affordance exists to answer the question | No tooltip, no help text, no link |
| `MISSING_TRAINING` | "Nobody showed me this" | — |
| `MISSING_TRANSLATION` | Spanish-speaker hits an English-only surface | — |
| `MISSING_ACCOUNTABILITY` | Operator cannot tell who is responsible for the next action | — |

Each tag MUST attach to: timestamp, page URL, exact verbatim quote, observed action, recovery path (if any).

---

## 3 · Personas (9 total)

### 3.1 · LABORER
**Mission**: Show up · Work safe · Sign what I need to sign · Go home.
**Core daily responsibilities**:
- Receive shift assignment
- Read JHP for today's job
- Acknowledge JHP
- Report incidents / near-misses
- Complete equipment pre-shift if assigned equipment

**Critical workflows**:
- `/jha` JHP acknowledgement (post-FOCP Release 2)
- `/incidents/new` public submission
- Driver shift-start (if assigned a truck)
- Daily Report read-only view of their assignment

**High-risk workflows**:
- Incident submission (legal exposure if wrong)
- JHP acknowledgement (if skipped → OSHA exposure)
- Equipment defect reporting

**Failure scenarios**:
- "I didn't see the new JHP version" → ack on stale version
- "I clicked the wrong incident type" → mis-categorized OSHA recordable
- "I couldn't find my equipment" → didn't complete pre-shift

**Common support-call triggers** (hypothesis · confirm in interview):
- "Where is my job's plan?"
- "Why isn't my name showing up?"
- "I can't sign the JHP"

**Adoption-risk indicators**:
- Skips the JHP acknowledgement entirely → still uses paper sign-in sheet
- Uses someone else's phone / email to acknowledge
- Doesn't open the platform at all

**Interview questions (12)** — read verbatim:
1. Walk me through your first 30 minutes on a typical job site. What apps / paper do you use?
2. Show me how you find today's Job Hazard Plan.
3. Show me how you acknowledge it.
4. If the JHP changed since you last looked, how would you know?
5. Show me how you would report an incident right now.
6. If you saw something unsafe but it isn't an incident yet, what would you do?
7. When was the last time someone showed you how to use this app?
8. Have you ever been confused by something on the platform? Walk me through what happened.
9. If you didn't have a phone with you today, how would you sign in / acknowledge anything?
10. What language do you prefer to read instructions in?
11. If you make a mistake, how do you fix it?
12. Name one thing that should change.

**Scoring rubric (0–10 per dimension; sum / 12 = persona score)**:

| Dimension | 0 | 5 | 10 |
|---|---|---|---|
| Can locate today's JHP | Can't | Finds with help | Finds independently |
| Can acknowledge JHP | Skips it / paper only | Does it with prompting | Does it independently · in their language |
| Can submit an incident | Won't | Submits with mistakes | Submits cleanly |
| Knows recovery path | "I'd call the office" | "I'd ask my foreman" | "I'd do X in the app" |
| Confidence in platform | "I don't trust it" | "It's OK" | "I trust it" |
| Training match | "Nobody showed me" | "Someone showed me once" | "I had real training" |
| Spanish parity (Spanish-only ops) | English-only screens block them | Mixed surfaces | All field-facing surfaces parity-correct |
| Discoverability | "I don't know where things are" | "I know SOME pages" | "I know where to go" |
| Mistake recovery | "I'd call somebody" | "I'd try again" | "I'd undo / fix in the app" |
| Accountability clarity | "I don't know who sees this" | "Someone sees it" | "X role sees this, Y acts" |
| Cognitive load | Overwhelmed | Manageable | Comfortable |
| Net Promoter (would you recommend) | "No" | "Maybe" | "Yes" |

**Escalation matrix**:
- Persona score < 30 → CRITICAL · platform is unsafe for this persona without supervision
- 30–49 → HIGH · platform is operable but requires tribal knowledge
- 50–69 → MEDIUM · platform is operable; targeted training closes gaps
- 70–84 → LOW · platform is operable; minor friction
- ≥ 85 → READY · persona is independent

---

### 3.2 · FOREMAN
**Mission**: Run the crew · Hit the production target · Don't get anybody hurt · Don't get the company sued.
**Core daily responsibilities**:
- Pre-shift safety briefing using JHP
- Roster confirmation (who's here / who's not)
- Daily Report submission (hours, materials, weather, equipment, narrative)
- Incident first-on-scene reporting
- Equipment defect escalation

**Critical workflows**:
- `/daily-reports/new` (post-FOCP Release 2 sticky footer)
- Daily Report lifecycle: OPEN → PENDING_REVIEW
- JHP acknowledgement roster oversight (does my crew know which plans they've signed?)
- Equipment defect → Shop routing

**High-risk workflows**:
- Daily Report payroll inputs (if wrong → payroll variance downstream)
- Incident "first 15 minutes" reporting (legal-record-quality narrative)
- JHP roster gaps (if a crew member didn't sign → OSHA exposure on me)

**Failure scenarios**:
- "I submitted the DR with wrong hours" — recovery path?
- "Two crew members signed each other's JHP on one phone" — supervisor visibility?
- "I closed an incident too soon" — reopen path?

**Common support-call triggers**:
- "I can't save my Daily Report"
- "The hours don't add up"
- "Office bounced my DR back — what changed?"

**Adoption-risk indicators**:
- Foreman submits paper DR alongside digital
- Foreman delegates submission to office (defeats the workflow)
- Foreman doesn't reconcile bounced DRs

**Interview questions (10)**:
1. Walk me through your morning pre-shift routine.
2. Show me how you confirm every crew member has acknowledged today's JHP.
3. Show me how you submit a Daily Report.
4. If your DR comes back from Office "Return to Field," walk me through what you do.
5. If a crew member gets hurt, walk me through the first 10 minutes on the platform.
6. Show me how you flag an equipment defect.
7. When was the last time something on the platform changed and nobody told you?
8. Where do you go when you don't know what to do?
9. How would you handle a Spanish-only crew member on this app?
10. Name two things that slow you down every day.

**Scoring rubric**: same 12-dimension structure as Laborer, scored against Foreman-specific tasks.

**Escalation matrix**: same thresholds.

---

### 3.3 · SUPERINTENDENT
**Mission**: Multiple jobs simultaneously · Allocate resources · Keep the schedule · Spot trouble before it lands on the PM's desk.

**Core daily responsibilities**:
- Cross-job dispatch decisions
- Foreman support / kickback resolution
- Equipment + crew routing across sites
- Field leadership escalations

**Critical workflows**:
- Dispatch board read
- Daily Report cross-job review (bounce vs accept)
- Incident situational awareness across jobs
- Field Leadership Portal (post-iter314)

**High-risk workflows**:
- Approving a Foreman's bounced DR without understanding why it bounced
- Closing an incident at the field level when it should escalate
- Pulling equipment off one job to another without permission trail

**Failure scenarios**:
- "I lost track of which jobs are over budget"
- "I didn't know there was an open incident on Job 2024-101"
- "The dispatch board says one thing, the office says another"

**Common support-call triggers**:
- "Which DRs are still open?"
- "Why is this incident still showing on my list?"
- "Where is the kickback note from office?"

**Adoption-risk indicators**:
- Uses Excel side-spreadsheet instead of platform
- Calls office instead of reading the dashboard
- Bypasses platform on weekends

**Interview questions (10)**:
1. Walk me through how you start your day across multiple jobs.
2. Show me how you spot a stuck Daily Report.
3. Show me how you see incidents across all your jobs.
4. If a Foreman is struggling with the platform, what do you do?
5. Show me how you reassign equipment from Job A to Job B.
6. When was the last time you had to call the office because the platform didn't tell you something?
7. How do you know when to escalate to the PM?
8. Where is your "Am I good?" view?
9. What does the Recovery Stream look like for you?
10. Name one decision you can't make without calling someone.

**Scoring rubric + escalation**: standard 12-dim · standard thresholds.

---

### 3.4 · PROJECT MANAGER (PM)
**Mission**: Win the job · Run the job · Bill the job · Close the job · Hit margin.

**Core daily responsibilities**:
- Job cost-vs-budget read
- DR approval (post-Office review)
- Incident sign-off on jobs
- Equipment + sub commitment management
- Customer comms (outside the platform, but informed by it)

**Critical workflows**:
- PM hub
- PM jobs / fleet / people / suppliers / posters
- DR lifecycle: PENDING_REVIEW → REVIEWED → CLOSED (admin role today)
- Incident → CAPA workflow (PM as accountable owner)

**High-risk workflows**:
- Closing the loop on a CAPA the PM owns
- Signing off on payroll variance (HR-led, but PM informed)
- JHP roster sign-off pre-mobilization

**Failure scenarios**:
- "I didn't know that CAPA was overdue"
- "Crew compliance was red but nobody told me until the audit"
- "The job financials don't match what I expected"

**Common support-call triggers**:
- "Where do I see all my open CAPAs?"
- "Why is Crew Compliance red?"
- "Can I rerun the variance for last week?"

**Adoption-risk indicators**:
- PM only opens the platform when prompted by email
- PM doesn't trust the data and asks office to re-pull
- PM's "Am I good?" answer requires 4+ clicks

**Interview questions (10)**:
1. Walk me through what you check first thing every morning.
2. Show me how you see every overdue item across your jobs.
3. Show me how you confirm crew compliance for tomorrow.
4. If an incident on your job needs CAPA, walk me through what you do.
5. Show me how you find a stuck Daily Report.
6. What do you do when the financials don't look right?
7. When was the last time you bypassed the platform to get an answer?
8. What does the platform tell you that nobody asked you to do today?
9. If your PM peer logs in for the first time, what would surprise them?
10. Name one report you re-run manually because the platform doesn't deliver it.

**Scoring rubric + escalation**: standard.

---

### 3.5 · SAFETY MANAGER
**Mission**: Zero incidents · OSHA-defensible records · Live coverage of every job · Coaching, not policing.

**Core daily responsibilities**:
- Incident triage + investigation + closure
- Site Inspection findings follow-up
- QA/QC oversight (Amendment 001 closure contract)
- JHP authoring + acknowledgement compliance
- Training records

**Critical workflows**:
- Incident lifecycle (post-iter451)
- QA/QC + Site Inspection lifecycles (post-iter453 + Amendment 001)
- JHP acknowledgement ledger (post-FOCP Release 2)
- Safety portal (`/safety`)

**High-risk workflows**:
- OSHA-recordable closure attestation (multiple checkboxes; if forgotten → exposure)
- Reopen with reason (audit-defensible)
- JHP compliance gap detection across jobs

**Failure scenarios**:
- "I closed an OSHA recordable without preserving the 300/301 record"
- "I didn't see a deficiency was overdue"
- "JHP acknowledgement coverage gaps weren't visible"

**Common support-call triggers**:
- "Where is the incident's audit trail?"
- "Why can't I close this?"
- "Who hasn't signed the JHP?"

**Adoption-risk indicators**:
- Maintains parallel spreadsheet of incidents
- Doesn't use lifecycle transitions; uses comments instead
- Closes deficiencies without re-inspection (now blocked by Amendment 001)

**Interview questions (10)**:
1. Walk me through your morning across all open incidents.
2. Show me how you find every overdue deficiency.
3. Show me how you check JHP acknowledgement coverage on a job.
4. Walk me through closing an OSHA-recordable incident.
5. If you closed something by mistake, walk me through the recovery.
6. What does the platform tell you that you didn't know yesterday?
7. When was the last time you had to email someone because the platform didn't surface a problem?
8. Show me how you train a new Safety Coordinator on this platform in 30 minutes.
9. How do you know the bilingual surfaces are saying the right thing in Spanish?
10. Name one report you produce manually for executives that the platform should produce.

**Scoring rubric + escalation**: standard.

---

### 3.6 · DISPATCH
**Mission**: Right person · Right vehicle · Right job · Right time · Repeat 40 times a day.

**Core daily responsibilities**:
- Daily dispatch assignments
- Driver qualifications check
- Equipment availability
- Day-1 / Week-1 debrief (post-iter392+)

**Critical workflows**:
- Dispatch board
- Driver shift-start QR
- Driver qualification dashboard (post-iter288)
- Dispatch lifecycle (post-iter392)

**High-risk workflows**:
- Dispatching an unqualified driver (CDL expired, medical card expired)
- Reassigning mid-shift
- Cross-job equipment swaps without approval

**Failure scenarios**:
- "The board says one thing but the driver showed up at the wrong job"
- "I dispatched someone whose CDL expired yesterday"
- "Shop took a truck offline and I didn't see it"

**Common support-call triggers**:
- "Why is this driver flagged?"
- "Why can't I assign this truck?"
- "Where is the Day-1 debrief?"

**Adoption-risk indicators**:
- Uses paper magnet board alongside the platform
- Texts foremen instead of using the platform
- Doesn't open the qualification dashboard

**Interview questions (10)**:
1. Walk me through how you build tomorrow's dispatch board.
2. Show me how you confirm every driver is qualified for tomorrow.
3. Show me what happens when a driver no-shows.
4. Walk me through reassigning a truck mid-shift.
5. How do you know Shop took something offline?
6. Show me the Day-1 debrief flow.
7. When was the last time you had to call someone because the board didn't tell you?
8. What does the platform NOT tell you that you wish it would?
9. How would a brand new dispatcher learn this on day one?
10. Name two manual lookups you do every morning.

**Scoring rubric + escalation**: standard.

---

### 3.7 · HR
**Mission**: Right people on the books · Right records on file · Right pay on Friday · Right training on time.

**Core daily responsibilities**:
- Employee lifecycle (new hire, reactivate, terminate)
- Driver qualification record-keeping
- Training records / expirations
- Payroll variance review + finalization
- Time-off / employee requests queue

**Critical workflows**:
- Employee lifecycle (post-iter152 + Phase Alpha governance)
- Driver qualification (post-iter312 CSV)
- Payroll Variance Lifecycle (post-iter452 + FOCP Release 2 undo)
- HR Portal

**High-risk workflows**:
- Reactivate vs Rehire decision (preserves original_hire_date contract)
- Payroll Variance finalization (no auto-finalize doctrine)
- Driver qualification expiration → Dispatch handoff

**Failure scenarios**:
- "I rehired someone and lost their original hire date"
- "I finalized a variance with a flagged row undecided"
- "Driver kept driving with an expired CDL because HR didn't escalate"

**Common support-call triggers**:
- "Can I undo a finalization?" (now YES post-FOCP Release 2)
- "Why is this person showing as terminated when I reactivated them?"
- "Where is my employee's full status history?"

**Adoption-risk indicators**:
- HR runs the platform in parallel with an HRIS spreadsheet
- HR doesn't use lifecycle; edits records directly
- HR finalizes variances without operator-led review

**Interview questions (10)**:
1. Walk me through onboarding a new employee end-to-end.
2. Show me how you reactivate a previously-terminated employee.
3. Show me payroll variance review for last week.
4. If you finalized a variance by mistake, walk me through the recovery.
5. Show me how you spot a driver whose CDL expires next week.
6. Walk me through approving a time-off request.
7. What records do you keep outside the platform because you don't trust the platform alone?
8. When was the last time you had to escalate to a developer to fix data?
9. How does HR show executives that the workforce is healthy?
10. Name one report you'd like generated automatically every Monday.

**Scoring rubric + escalation**: standard.

---

### 3.8 · SHOP
**Mission**: Trucks roll · Equipment runs · Nothing on the road that shouldn't be.

**Core daily responsibilities**:
- Fleet defect intake (severity-tiered)
- Repair lifecycle (post-iter251)
- Equipment inspections review
- Mechanic assignments

**Critical workflows**:
- Fleet-ops (post-iter295)
- Repair lifecycle (post-iter251)
- Equipment inspection lifecycle
- Driver-reported defects → Shop queue

**High-risk workflows**:
- Approving a vehicle back to service prematurely
- Severity tier misclassification
- Inspection backlog hiding red flags

**Failure scenarios**:
- "A truck went out that should have stayed down"
- "I closed a repair and the same defect reappeared 2 days later"
- "Dispatch couldn't see I took it offline"

**Common support-call triggers**:
- "Where is the last inspection for VIN X?"
- "Why can't I close this repair?"
- "Why is this severity Red?"

**Adoption-risk indicators**:
- Shop maintains paper workorder book
- Shop calls Dispatch instead of marking offline
- Shop bypasses severity tiers

**Interview questions (10)**:
1. Walk me through receiving a driver-reported defect.
2. Show me how you decide severity tier.
3. Show me how you take a unit offline.
4. Walk me through closing a repair.
5. What happens if the same defect comes back?
6. Show me how Dispatch knows the unit is back online.
7. When was the last time a unit went out that shouldn't have?
8. What does the platform tell you Shop needs to know FIRST every morning?
9. How would a new mechanic learn this in a week?
10. Name two things you write down on paper because the platform doesn't capture them.

**Scoring rubric + escalation**: standard.

---

### 3.9 · EXECUTIVE
**Mission**: Trust the data · Decide with confidence · Sleep at night.

**Core daily responsibilities** (light platform use):
- Operational health glance
- Open critical incidents
- Open critical CAPAs
- Variance from plan

**Critical workflows**:
- AdminCommandCenter
- Operations Center
- Recovery Stream (post-FOCP Release 2)
- Operator Digest emails

**High-risk workflows**:
- Making a decision based on data the platform got wrong
- Discovering an open incident from a customer call instead of the platform
- Sitting on a financial variance that the platform surfaced 2 weeks ago

**Failure scenarios**:
- "I learned about this from outside the platform"
- "The data didn't match the field reality"
- "Nobody told me X was overdue"

**Common support-call triggers**:
- "Send me last week's incident summary"
- "How many of my CAPAs are overdue?"
- "What's our compliance rate?"

**Adoption-risk indicators**:
- Executive only sees the platform through emailed digests
- Executive's first question every morning is "is everything OK?" and the platform doesn't answer
- Executive maintains parallel KPI spreadsheet

**Interview questions (10)**:
1. Walk me through your first 5 minutes on the platform every morning.
2. Where does the platform say "you're good" without you asking?
3. Show me where every overdue critical item lives.
4. If a CAPA owned by a PM goes overdue, how do you know?
5. When the digest arrives, do you trust it?
6. When was the last time you learned something operationally important from outside the platform?
7. Show me a number on the platform that you would bet money on.
8. How do you know HR / Safety / Dispatch / Shop are operating healthily?
9. If you went on vacation for 30 days, what would break first?
10. Name one decision you can't make from the platform alone.

**Scoring rubric + escalation**: standard.

---

## 4 · Aggregate scores (derived after all 9 personas interviewed)

### 4.1 · Persona Readiness Score
For each persona, sum 12 dimensions × 10 = 120 max, normalize to 100.

### 4.2 · Platform Dependence Score
Weighted average of all 9 personas, weighted by hours/week on platform:

| Persona | Hours/wk hypothesis | Weight |
|---|---:|---:|
| Laborer | 1 (touch-only) | 0.05 |
| Foreman | 8 | 0.15 |
| Superintendent | 12 | 0.13 |
| PM | 15 | 0.17 |
| Safety | 25 | 0.20 |
| Dispatch | 30 | 0.15 |
| HR | 15 | 0.08 |
| Shop | 10 | 0.05 |
| Executive | 3 | 0.02 |

Operator may adjust weights to match observed reality.

### 4.3 · Jaymn Dependence Score
For each persona interview, count:
- Times persona names Jaymn as the recovery path
- Times persona names Jaymn as the trainer
- Times persona names Jaymn as the escalation point

Jaymn Dependence Score = 100 − (10 × total Jaymn mentions across all 9 interviews · capped at 100).

Target: ≤ 10 (i.e., Jaymn is mentioned ≤ 9 times across the entire 9-persona interview cycle).

---

## 5 · Escalation matrix (cross-persona)

After all 9 personas are scored:

| Composite | Action |
|---|---|
| Any persona < 30 | HALT certification · operator-led remediation cycle required for that persona |
| Platform Dependence Score < 50 | HALT certification · platform not operable independently |
| Jaymn Dependence Score < 60 | HALT certification · tribal knowledge concentrated in one person |
| All ≥ thresholds | Phase 1 PASSED · advance to Phase 4 (Operator Confidence Layer) |

---

## 6 · Output file naming convention

Each completed interview produces one markdown file:

```
/app/memory/interviews/
  laborer_2026-MM-DD.md
  foreman_2026-MM-DD.md
  superintendent_2026-MM-DD.md
  pm_2026-MM-DD.md
  safety_2026-MM-DD.md
  dispatch_2026-MM-DD.md
  hr_2026-MM-DD.md
  shop_2026-MM-DD.md
  executive_2026-MM-DD.md
```

Each file contains:
- Date · interviewer · interviewee role (no PII)
- Verbatim quotes by question
- Capture-taxonomy tags with timestamps + URLs
- Scoring rubric filled in (12 dimensions)
- Persona Readiness Score
- Free-text observations
- Operator-determined remediation candidates (flagged but not authorized)

The AI agent **cannot** generate these files. Only the operator-led interview cycle produces them.

---

## 7 · Refusal conditions

The AI agent MUST refuse to:
- Generate fake interview transcripts.
- Score personas based on AI inference.
- Compute Platform Dependence Score or Jaymn Dependence Score without real interview files in `/app/memory/interviews/`.
- Advance to Phase 4 (Operator Confidence Layer) without all 9 persona scores on file.

Anything in this playbook beyond the protocol itself requires operator data. Period.

---

**End of REALITY VALIDATION INTERVIEW PLAYBOOK · OCEP Phase 1**

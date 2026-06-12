# TRACK 13.8G — Combined Operator Interview Crib Sheet

**Date**: 2026-06-12 · **Mode**: documentation only · **Pages when printed**: ≈ 10
**Use**: Hand to whoever conducts the interviews. Print double-sided. Capture answers in pen.

---

## 1 · Executive Instructions (read before starting)

- This interview is **not a wishlist session**. Do not promise features.
- This interview is **not a complaint session**. Pain matters only if it ties to real work.
- This interview is **not authorization to build**. Authorization comes after the interview, on review.
- Each answer must tie to **work the operator actually did this week**, not "in theory".
- **If nobody can name the workflow → do not build it.**
- **If nobody can name the owner → do not surface it.**
- **If it adds clicks without reducing pain → do not build it.**
- Time budget: 15–25 min per role. The full packet covers 11 roles in one cycle.

---

## 2 · Interview Rules

1. Ask what the operator **actually did this week**, not what they theoretically might do.
2. Ask what they **leave the platform** to do.
3. Ask what they still use **text / email / phone / paper / Excel** for.
4. Ask what they **cannot find** in the platform.
5. Ask what they **ignore** in the platform.
6. Ask what is **duplicated** across the platform.
7. Ask what **slows them down**.
8. Ask what **creates risk** for the company.
9. Ask what **should not be in the platform**.
10. Ask what **must be protected exactly as-is**.

Capture quotes verbatim where possible. Quotes outrank summaries.

---

## 3 · Universal Questions (every role)

| # | Question | Answer (capture verbatim where useful) |
|---|---|---|
| U1 | Top 3 things you do every day | |
| U2 | Of those, which can you do inside MASCI OPS today | |
| U3 | Of those, which still happen outside MASCI OPS | |
| U4 | What do you still text people about | |
| U5 | What do you still phone people about | |
| U6 | What do you still email people about | |
| U7 | What still happens on paper or Excel | |
| U8 | What screen do you open FIRST when you sit down | |
| U9 | What screen do you IGNORE | |
| U10 | What takes too many clicks | |
| U11 | What do you NOT trust in the platform | |
| U12 | What do you TRUST most | |
| U13 | What is missing | |
| U14 | What should NOT be added | |
| U15 | What would save you the most time this week | |

---

## 4 · Role-Specific Questions

### 4.1 · PM
- Do you use `/po-requests`? If yes, how often? If no, why not?
- Who creates POs in your workflow today?
- Who approves POs?
- Who uploads receipts?
- Who chases missing receipts?
- Should PO Requests appear on **PM Hub V2** as an action queue?
- Do Holds / Due Today / Constraints / CAPAs help, or are any of them noise?
- What project-day information do you still hunt for verbally?
- Would an Operational Events project-day panel on PM detail help? Who would use it?
- Do you need scale tickets structured, or are photo attachments enough?

### 4.2 · Superintendent
- Show me the last 3 things you tracked outside the platform.
- Do you use Field Memory / Field Revision today?
- What do you handoff verbally to the next shift that should be a record?
- Do daily quantities live in Excel today?
- MOT changes — how do you track them?
- Would a per-project per-day timeline panel help you?

### 4.3 · Foreman
- What do you do on paper today?
- Punchlist — where does it live?
- Do you ever submit daily reports on someone else's behalf?
- Are job photos useful in your workflow?
- Is DVIR via `/driver` enough, or do you need more?

### 4.4 · Dispatcher
- Is the MapLibre Live Fleet Map still the center of your work? **(HARD LOCK CHECK · expected YES)**
- What about Dispatch must **NEVER** change? Capture exact words.
- Does Shop Recovery Map (in Shop Hub V2) reduce calls from Shop to Dispatch?
- What dispatch work still happens via radio / text / phone?
- Are driver check-ins via `/shift` working?
- Are Motive locations reliable enough on your screen?
- Where should the map NEVER be moved? **(HARD LOCK CHECK)**

### 4.5 · Shop Manager
- Does Shop Hub V2 show the right recovery queues today?
- Is the Recovery Map (Track 13.7B) useful?
- What still requires calling Dispatch?
- What still requires texting mechanics?
- Is Repair Complete vs Returned To Service clear in the UI? **(HARD LOCK CHECK)**
- What is missing from equipment recovery?
- Do you need PO Request visibility on Shop Hub V2?
- Do you need Material Movement visibility?
- Do notifications help or annoy? Which specific notifications?

### 4.6 · Mechanic (≤ 5 min interview · no portal expansion authorized)
- Where do you look to know what to repair next?
- Do you use the platform at all, or paper?
- Would a deep link to a single unit's asset card help? (no portal · just a link)

### 4.7 · Safety Manager
- Does Safety Hub V2 show the right queues?
- Are CAPAs the right granularity, or do you wish for a lighter "field-safety-flag"?
- Trench Safety benchmark — still useful?
- Do you ever ask "where is unit X?" — i.e., would a Safety map lens help? **(HARD LOCK CHECK · expected NO)**

### 4.8 · HR
- Does HR Hub V2 show the right queues today?
- What requests still come through email or text?
- What certification / training items are missed in production?
- Are notifications useful or noise?
- Onboarding / offboarding — what is still on paper or in Outlook?
- What should NOT be added to HR?

### 4.9 · Admin
- Does Admin Hub V2 surface the right admin issues?
- Is **Operational Locations geofence reconciliation** discoverable now (Track 13.8E)?
- Do you actually use geofence reconciliation? How often?
- Do you need counts on the Admin Hub card, or is the link enough?
- Which admin tools are hidden but useful?
- Which admin tools are noise?
- Are scheduler runs / backup verification surfaced where you need them?

### 4.10 · Leadership / Executive
- Does Leadership companion show useful operational awareness?
- What number do you ask for by phone today that the platform should already tell you?
- What is noise?
- Should Leadership ever have a map? **(HARD LOCK CHECK · expected NO)**
- What should stay out of Leadership entirely?

### 4.11 · Driver (≤ 5 min · no portal expansion authorized)
- Do you use `/shift`? When?
- Do you use `/d/:token` magic links?
- Do you use `/driver`?
- Any confusion about no login? **(HARD LOCK CHECK · expected NO)**
- What takes too long in the driver flow?
- What do you still text / call dispatch about?
- Do attachments work? Scale ticket photos in particular?
- Would structured scale ticket entry (4 numeric fields) help or slow you down?

---

## 5 · PO Requests Decision Block (Track 13.8F)

| # | Question | Answer |
|---|---|---|
| PO1 | Does MASCI currently use `/po-requests` inside the platform? | YES / NO |
| PO2 | If YES — who uses them? | |
| PO3 | If NO — why not? | |
| PO4 | Who SHOULD create? | PM / Super / FL / Shop / Admin |
| PO5 | Who SHOULD approve? | PM / FL / Admin |
| PO6 | Who SHOULD upload receipts? | Creator / FL / Admin |
| PO7 | Who SHOULD chase missing receipts? | Admin / FL / PM |
| PO8 | Who SHOULD close? | Approver / Admin |
| PO9 | Should it appear on PM Hub V2? | YES / NO |
| PO10 | Should it appear on Field Leadership Hub? | YES / NO |
| PO11 | Should it appear on Admin Hub V2 (missing-receipt only)? | YES / NO |
| PO12 | Should it stay standalone only? | YES / NO |
| PO13 | Would pending_approval / pending_receipt / overdue_receipt counts be useful? | YES / NO |
| PO14 | Would those counts create noise? | YES / NO |
| PO15 | What exact decision does the PO card help you make? | |

**Decision (circle one)**: Surface PM only · Surface FL only · Surface both · Surface Admin only · Leave standalone · Do not use.

---

## 6 · Material Movement Decision Block

| # | Question | Answer |
|---|---|---|
| MM1 | Does MASCI need Material Movement inside the platform today? | YES / NO |
| MM2 | What material movement is tracked today? | |
| MM3 | Who tracks it? | |
| MM4 | Where is it tracked (Excel / paper / app)? | |
| MM5 | What is painful about it today? | |
| MM6 | Is it tied to Daily Reports? | YES / NO |
| MM7 | Is it tied to haul tickets? | YES / NO |
| MM8 | Is it tied to scale tickets? | YES / NO |
| MM9 | Is it tied to production tracking? | YES / NO |
| MM10 | Should the partial Material Movement be recovered or left dormant? | RECOVER / DORMANT |

---

## 7 · Scale Ticket Decision Block

| # | Question | Answer |
|---|---|---|
| ST1 | Are scale tickets used daily on asphalt days? | YES / NO |
| ST2 | Who collects them today? | Driver / Foreman / Super |
| ST3 | Are they currently photos only (existing `scale_ticket` attach kind)? | YES / NO |
| ST4 | Is photo attachment enough? | YES / NO |
| ST5 | Would 4 structured fields help? | YES / NO |
| ST6 | Which fields are essential? (tick all that apply) | ☐ ticket # ☐ material ☐ tons / qty ☐ truck ☐ job ☐ supplier/plant ☐ date ☐ photo |
| ST7 | Would structured entry slow drivers down on the truck? | YES / NO |
| ST8 | Should drivers enter it? | YES / NO |
| ST9 | Should foremen enter it instead? | YES / NO |
| ST10 | Should PMs review it? | YES / NO |

---

## 8 · Operational Events / Project-Day Block

| # | Question | Answer |
|---|---|---|
| OE1 | Would a project-day timeline panel help? | YES / NO |
| OE2 | Who would use it? | PM / Super / Leadership |
| OE3 | What should appear in it? (tick all that apply) | ☐ Daily Reports ☐ Incidents ☐ CAPAs ☐ Constraints ☐ QA/QC ☐ Photos ☐ Signatures ☐ Material Movement |
| OE4 | Would it reduce hunting? | YES / NO |
| OE5 | Where should it live? | PM project-detail / Super dashboard / Leadership / standalone |

---

## 9 · Notifications Block

| # | Question | Answer |
|---|---|---|
| N1 | Which notifications are useful today? | |
| N2 | Which are noise? | |
| N3 | Which are missing? | |
| N4 | Which are ignored? | |
| N5 | Which must be immediate? | |
| N6 | Which should be daily digest only? | |
| N7 | Which should NEVER be emailed? | |
| N8 | Who receives too much? | |
| N9 | Who receives too little? | |
| N10 | What notification caused real action this week? | |

---

## 10 · Do-Not-Build Confirmation (every role asked)

> *"Should the following stay OUT of MASCI OPS unless a future separate track proves otherwise?"*

| Item | YES — stay out | NO — disagrees (capture why) |
|---|---|---|
| RFIs | ☐ | |
| Submittals | ☐ | |
| Formal Change Orders | ☐ | |
| Pay Applications | ☐ | |
| Cost Management | ☐ | |
| Contract Management | ☐ | |
| Formal Document Control | ☐ | |
| Plan Revision Management | ☐ | |
| Driver login / accounts | ☐ | |
| Driver hub | ☐ | |
| Mechanic portal | ☐ | |
| Vendor location map overlay | ☐ | |
| Safety map lens | ☐ | |
| Leadership map lens | ☐ | |

**Disagreement is captured · NOT authorization.**

---

## 11 · Scoring Sheet (per candidate workflow)

For each candidate the operator mentioned as painful, fill one row:

| Workflow | Pain 1-5 | Freq (D/W/M/R) | Current tool | Time lost / occurrence | Risk if missed | Owner clarity | Platform fit | Pwr / Sim / Bty / Trst / Prv |
|---|---|---|---|---|---|---|---|---|
| | | | | | | clear / unclear | H / M / L | / / / / |
| | | | | | | clear / unclear | H / M / L | / / / / |
| | | | | | | clear / unclear | H / M / L | / / / / |
| | | | | | | clear / unclear | H / M / L | / / / / |

---

## 12 · Final Decision Capture (per candidate)

Mark exactly one verdict per candidate:

| Candidate | Authorize surfacing | Authorize impl. spec | Needs more discovery | Leave standalone | Leave dormant | Do not build | Protect as-is |
|---|---|---|---|---|---|---|---|
| PO Requests card (PM Hub) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| PO Requests card (FL Hub) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Operational Events project-day panel | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| MaterialMovementTile on PM Hub V2 | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Scale-ticket structured entry | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Operational Records list view | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Operational Timeline view | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Field Memory finishing | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Field Revision finishing | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Notifications cadence tuning | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| MaintainX credential activation | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

---

## 13 · Summary Template (one per interviewed person)

```
Interviewed role:
Interviewed person:
Date:

Top 3 workflows performed this week:
  1.
  2.
  3.

Top 3 pains:
  1.
  2.
  3.

Top 3 outside-platform tools:
  1.
  2.
  3.

Systems they USE:
Systems they IGNORE:
Systems they WANT:
Systems they DO NOT want:

PO decision:                 [ PM / FL / Both / Admin / Standalone / Do-not-use ]
Material Movement decision:  [ Recover / Dormant ]
scale_ticket decision:       [ Driver / Foreman / Either / None ]
Operational Events decision: [ Build / Skip / More-discovery ]
Notification decision:       [ Keep / Tune / Reduce / Investigate ]

Final recommendation (one sentence):
```

---

## 14 · Final Operator Authorization Checklist (interviewer signs)

- [ ] Every interviewed role's universal-question section is completed.
- [ ] Every role's role-specific section is completed.
- [ ] All five decision blocks (PO / Material Movement / Scale Ticket / Operational Events / Notifications) are completed.
- [ ] Do-not-build confirmation is completed for every role.
- [ ] Scoring sheet has at least one row per candidate workflow mentioned.
- [ ] Final decision capture has exactly one verdict per candidate.
- [ ] Hard-lock check questions all confirmed (Dispatch map · Driver no-login · Shop Repair ≠ RTS · Safety/Leadership no-map).
- [ ] Disagreements with the do-not-build list captured (without becoming authorization).
- [ ] Interview summary template completed for every interviewed person.
- [ ] Packet returned to the platform team for cross-role synthesis (a separate track).

**Interviewer signature** ______________________________  **Date** __________

**Operations sponsor signature** _______________________  **Date** __________

---

## 15 · Track Status

- **Track**: 13.8G — Combined Operator Interview Crib Sheet · CLOSED.
- **Report path**: `/app/memory/TRACK_13_8G_OPERATOR_INTERVIEW_CRIB_SHEET.md`.
- **Zero code changes confirmed** — this track produced markdown only.
- **Roles covered**: PM · Superintendent · Foreman · Dispatcher · Shop Manager · Mechanic · Safety Manager · HR · Admin · Leadership · Driver (11 roles).
- **Decision blocks included**: PO Requests · Material Movement · Scale Ticket · Operational Events / Project-Day · Notifications · Do-Not-Build · Scoring Sheet · Final Decision Capture.
- **Next step**: operator team conducts interviews offline using this packet, returns completed packet for cross-role synthesis (a separate track when authorized).

---

**Track 13.8G · CLOSED.** Interview tool delivered. No system touched. Reality discovery moves from source to operator.

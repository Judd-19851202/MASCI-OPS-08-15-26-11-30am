# Superintendent Validation Report

_Phase V.2 · Daily Report Evolution · Internal Operational Review · Pre-pilot gate._

> **This is NOT software testing.** This is operational testing —
> a real superintendent (or senior foreman) walking the existing
> Daily Report on a real iPad, with a realistic project, in
> realistic conditions, and reporting whether the post-Wave-1B/1C
> Daily Report still feels like the Daily Report.
>
> Field language must feel natural. If a label triggers
> "what does that mean?", we change the label — not the workflow.

---

## 1 · Scenarios (pick one per session · all three before pilot gate)

### Scenario A — Airport Operations
- Setting: night-shift runway / taxiway / apron work · MOT escorts ·
  CEI / Owner / Operations Center oversight · narrow work windows.
- Things to log: paving production · MOT delays · CEI hold · escort
  delays · weather impacts · extra work directives.

### Scenario B — Utility / Drainage Operations
- Setting: open-cut drainage · pipe install · MOT lane closure ·
  utility conflicts · dewatering.
- Things to log: pipe LF · structures EA · CY material · utility
  delays · survey holds · changed conditions · extra work.

### Scenario C — Concrete / Sidewalk / Curb-and-Gutter Operations
- Setting: walk-behind crews · sidewalk SY · curb LF · panel
  replacements · pedestrian MOT.
- Things to log: SY pour · LF curb · weather delays · trucking
  delays · owner directives · public-relations impacts.

---

## 2 · What worked

> _Fill in during the walk. One bullet per real observation. No
> theory. No "should." Only what actually happened._

- (e.g., "Pulled Production card open in 1 tap · typed 320 LF
   asphalt · saved · moved on. Took less than 30 seconds.")
- (e.g., "Tapped Weather chip · row appeared instantly · typed
   '0.4 in rain 1-2pm' · saved.")
- …

## 3 · What felt awkward

> _Hesitation · confusion · misclicks · re-reads · uncertainty._

- (e.g., "I wanted to log a 'changed condition' but couldn't tell
   if that was the 'Owner / Engineer' chip or the 'Other' chip.")
- (e.g., "The 'Hours Impact' field — is that the crew's lost
   hours, or the schedule slip in hours? Not obvious.")
- …

## 4 · What terminology confused users

> _Word-by-word. Quote the user. Don't paraphrase._

| Term | User's actual question / reaction |
|---|---|
| (e.g., "Extra Work") | "Is that change orders or just non-bid work?" |
| (e.g., "Custom Unit (when OTHER)") | "What do I type here?" |
| … | … |

## 5 · What was unused

> _Cards / chips / fields the user never touched. If the field
> exists but the user skipped it, ask why before the next walk._

- (e.g., "Station / Loc From — user never used it. Said 'we don't
   chain it that way on this job, we use grid coordinates.'")
- …

## 6 · What should be simplified

> _Concrete suggestions from the user · operational language only._

- (e.g., "Fewer chips. Combine 'CEI / Inspection' and 'Owner /
   Engineer' into one 'Owner / CEI' chip — same person in this
   project.")
- (e.g., "Default the Production unit to 'TON' on paving jobs ·
   foreman never picks anything else.")
- …

## 7 · Production tracking usefulness (1-5 + comment)

| Aspect | Score | Comment |
|---|---|---|
| Speed to enter a row |  |  |
| Field naming clarity |  |  |
| Unit list completeness |  |  |
| Station from/to usefulness |  |  |
| Likelihood of daily use |  |  |

## 8 · Delay tracking usefulness (1-5 + comment)

| Aspect | Score | Comment |
|---|---|---|
| Chip names match real-world delay language |  |  |
| Hours Impact field clarity |  |  |
| Notes field length sufficient |  |  |
| One-tap insert speed |  |  |
| Likelihood of daily use |  |  |

## 9 · Workflow familiarity check

| Question | Answer |
|---|---|
| Did this still feel like the Daily Report you've been filling out? | YES / NO |
| Did the new sections feel like additions or like a new form? | additions / new form |
| Did you ever feel slowed down vs. the previous version? | YES / NO |
| Would you push back on rolling this to your crew Monday morning? | YES / NO |
| If YES — what would you fix first? | _free text_ |

## 10 · Recommended changes before pilot

> _Ranked. Highest-friction items first._

| # | Change | Surface | Estimated complexity |
|---|---|---|---|
| 1 |  | _e.g., Constraint UI · helper text_ | _trivial / small / medium_ |
| 2 |  |  |  |
| … |  |  |  |

---

## 11 · Pilot gate decision

| Gate | Decision |
|---|---|
| Scenario A (Airport) walked? | ☐ |
| Scenario B (Utility / Drainage) walked? | ☐ |
| Scenario C (Concrete / Sidewalk) walked? | ☐ |
| All "what felt awkward" items resolved? | ☐ |
| All Section 4 terminology confusions resolved? | ☐ |
| Section 9 #4 ("push back on Monday rollout") all NO? | ☐ |
| Operator approves pilot scoping? | ☐ |

🛑 **Do NOT begin pilot scoping, RFI, Schedule, or P6 work
until every box above is ticked AND the operator issues an
explicit pilot authorization.** Wave-2 (offline strengthening)
may begin earlier at the operator's discretion.

---

## 12 · Doctrine reminder

This validation pass exists to keep the platform speaking
construction. If the language doesn't feel natural to the user
filling the form on the truck, change the language — not the
user.

| Lock | Reaffirmed |
|---|---|
| Doctrine Lock #1 — Simplicity Test (foreman 9-step contract) | ☐ |
| Doctrine Lock #2 — Platform Inheritance (no new deps, reuse existing components) | ☐ |
| Operational Calmness (slate · monospace · signal-only) | ☐ |
| Frozen Archive (DELETE 410 · zero historical mutation) | ☐ |

---

_End of SUPERINTENDENT_VALIDATION_REPORT.md._

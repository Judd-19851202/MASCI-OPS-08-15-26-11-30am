# Executive Command Center — Design Review (Pillar 2 · Pre-Implementation Critique)

**Classification:** OMEGA Pillar 2 · DESIGN REVIEW ONLY · No code · No DB · No endpoints · No UI
**Generated:** 2026-05-31 UTC
**Author:** E1 (self-critique of the blueprint produced earlier this session)
**Scope:** Challenge every card, KPI, rule, and threshold in `EXECUTIVE_COMMAND_CENTER_SPEC.md` / `EXECUTIVE_HEATMAP_SPEC.md` against the 5 mandatory questions: **Why does leadership need this? · What decision does it support? · What action should occur if RED? · Who owns that action? · What happens if this card does not exist?**
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_RISK_ANALYSIS.md` · `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` · `FINAL_PHASE_A_RECOMMENDATION.md`

---

## 1 · Review method

For each of the 10 cards in the blueprint, I answer the 5 mandatory questions, surface the strongest objection I can raise, and assign a verdict (KEEP · MODIFY · REMOVE). I am explicitly **trying to break the design** before code is written.

---

## 2 · Per-card review

### 2.1 Card 1 · Jobs Today

| Question | Answer |
|---|---|
| Why does leadership need this? | To spot jobs that have stalled, are missing reporting, or have unaddressed incidents — before the customer or safety team notices. |
| What decision does it support? | "Should I call the PM/Foreman about job X today?" |
| Action if RED? | PM contacts foreman; Operations Director may dispatch a supervisor visit. |
| Owner of action? | Primary PM on the job; Operations Director as escalation. |
| What if this card doesn't exist? | Leadership relies on `/admin/jobs` + manual scan of `daily_reports` + `incidents`. Today's status. ~15–30 min lost daily. |

**Strongest objections:**
- **JOBS-1 false positive (timezone + cadence):** "no DR filed by 17:00 local" assumes uniform local time and uniform workday. Weekend/holiday/no-work-scheduled days trigger RED falsely. The platform has no PTO/holiday calendar to suppress this.
- **JOBS-2 duplicate with Card 2:** "open incidents severity≥medium" already fires SAF-1. Same record drives two RED items. Inflates RED count.
- **JOBS-3 (orphaned project) is data-hygiene, not daily-ops:** an orphan PM project is a one-time admin alert. RED-forever-until-fixed pollutes the dashboard and trains leadership to ignore RED.

**Verdict:** **MODIFY** — drop JOBS-3 (move to admin compliance scan), make JOBS-1 weekday-aware and configurable, deduplicate JOBS-2 against SAF-1.

---

### 2.2 Card 2 · Safety Today

| Question | Answer |
|---|---|
| Why does leadership need this? | A single severity-weighted view of safety risk. The platform's existence rests on safety culture. |
| What decision does it support? | "Do I need to walk the safety lead through a specific incident today? Do I need to call OSHA-style attention?" |
| Action if RED? | Safety lead briefs Operations Director; possible site visit; possible corrective-action escalation. |
| Owner of action? | Safety lead; Operations Director as escalation. |
| What if this card doesn't exist? | Leadership monitors `/admin/incidents` + `/admin/compliance-findings` separately; misses CA aging signal. |

**Strongest objections:**
- **SAF-4 false positive (dormant projects):** "no safety meeting in 14 days" fires for any project, including dormant ones (paused for weather, scope change, awaiting permits). Must restrict to projects with **DR activity in last 7 days**.
- **Severity inflation risk:** `incidents.severity` is operator-entered. If the safety lead miscategorizes a near-miss as `medium`, this card fires RED unnecessarily.
- **Acknowledged-but-unresolved blind spot:** SAF-3 only catches `severity=red` findings — what about a yellow finding open for 60 days? Possible false negative.

**Verdict:** **KEEP** — but modify SAF-4 to gate on recent project activity, and add a sub-rule for chronically-open yellow compliance findings (>60 days).

---

### 2.3 Card 3 · Equipment Today

| Question | Answer |
|---|---|
| Why does leadership need this? | Equipment downtime directly costs revenue (idle crews, rental escalation, missed deadlines). |
| What decision does it support? | "Do I need to authorize a rental, expedite a part, or reassign a crew today?" |
| Action if RED? | Shop manager + Dispatch coordinate substitution; Operations Director may approve emergency rental. |
| Owner of action? | Shop manager; Operations Director as escalation for cost decisions. |
| What if this card doesn't exist? | `/admin/equipment-inspections/open-items` exists; leadership would discover most of this manually. ~10 min lost daily. |

**Strongest objections:**
- **EQP-3 false positive (intentional holds):** Asset holds aging >7 days fire AMBER, but many holds are deliberate (capital reserve, winter storage, training-only). The `asset_holds.reason` field needs to be inspected (whitelist of "active operations" reasons only).
- **EQP-1 vs EQP-4 overlap:** Both fire on OOS equipment. EQP-4 (DVIR no shop-task) is a stricter subset of EQP-1. One must subsume the other.
- **Critical defect age missing:** `fleet_defects.severity=critical` fires AMBER at 1, RED at 1 — but a critical defect that was created 2 minutes ago should not fire same as one open 5 days. Need age modifier.

**Verdict:** **KEEP** — but modify EQP-3 to whitelist reason codes, consolidate EQP-1+EQP-4 into one rule with subcategories, add age modifier to EQP-2.

---

### 2.4 Card 4 · Accountability Overdue

| Question | Answer |
|---|---|
| Why does leadership need this? | To spot work the platform tracked but no one actually closed. The "did anyone follow up?" gap. |
| What decision does it support? | "Who is letting things slip? Do I need to assign a fixer?" |
| Action if RED? | Direct the assignee (or Admin) to triage the queue. |
| Owner of action? | Each task's assignee; Admin as fallback. |
| What if this card doesn't exist? | Each portal's `/api/tasks` view exists; nothing aggregates them. Genuine gap. |

**Strongest objections:**
- **Task heterogeneity = noise:** Tasks span "approve PO" (high-stakes) to "review training certificate" (low-stakes) to system-generated reminders. Counting them together is meaningless. **Must filter to action-class tasks only** (i.e., excluding informational + system-noise tasks).
- **ACC-3 is a noise generator:** "stale unacknowledged notifications" — many platform notifications are informational and never get explicit ack (e.g., "your DR was reviewed"). 7d threshold means every executive sees RED on day 8 forever. Must be **removed** or restricted to acknowledgement-required notifications only.
- **Threshold too sensitive:** 5 open overdue tasks = AMBER, 15 = RED. In an org with 132 collections and active operations, **15 stale tasks is normal background noise**, not a leadership signal. Real signal lives at ≥30–50 sustained overdue.

**Verdict:** **MODIFY** — remove ACC-3 entirely, define an `action_required=true` task subtype filter (or use existing `tasks.priority ∈ {high, critical}`), raise thresholds substantially.

---

### 2.5 Card 5 · PM Load

| Question | Answer |
|---|---|
| Why does leadership need this? | To detect overloaded PMs before they drop balls. |
| What decision does it support? | "Should I reassign a job, hire, or move a co-PM?" |
| Action if RED? | Operations Director discusses load with overloaded PM, considers redistribution. |
| Owner of action? | Operations Director. |
| What if this card doesn't exist? | Operations Director generally already knows who is overloaded informally. **Real question: does the algorithm add information beyond gut feel?** |

**Strongest objections:**
- **Opaque composite score (`open_DRs×1 + incidents×3 + POs×1 + tasks×2`):** weights are made up. There is **no evidence** PM overload correlates with these specific weights. A PM with 30 routine DRs to review is rated worse than one with 4 active fires. Wrong signal.
- **PML-2 (`last_login_at < 5 days`) catastrophic false-positive engine:** PMs on PTO, sick leave, working on-site without laptop, or working through phone/email all look "not seen." Without a PTO calendar integration, this rule is a slander generator.
- **Small-organization fit:** MASCI has a handful of PMs (per memory references). Leadership already knows who's loaded. **A scoreboard pressures PMs without producing new information.**
- **Surfaces a CULTURAL artifact, not an operational risk:** an "overloaded" PM is a hiring/staffing decision, not a today-decision. Wrong card for the time budget.

**Verdict:** **REMOVE from Phase A.** Replace with a passive read-only **PM Activity Strip** (last login · open items count · scope size) without any RAG. Add load scoring later if and only if Phase A reveals a measurable need.

---

### 2.6 Card 6 · Supervisor Load

| Question | Answer |
|---|---|
| Why does leadership need this? | To detect overloaded supervisors. |
| What decision does it support? | "Should I move a foreman or hire?" |
| Action if RED? | Operations Director rebalances assignments. |
| Owner of action? | Operations Director. |
| What if this card doesn't exist? | Field Leadership Portal already exists; supervisor activity is visible there. **This card replicates existing visibility.** |

**Strongest objections:**
- **Same opacity problem as Card 5:** weighted composite (`DRs×0.2 + records×1 + crew_days×0.5`) has no evidentiary basis. Just made up.
- **No supervisor data model maturity:** "Supervisor" in MASCI today is a role inferred from `daily_reports.supervisor_email` and FL portal users. The data model isn't strong enough for a dedicated load score.
- **Audience mismatch:** supervisor load is a Field Leadership concern, not an Executive concern. Phase C filtered lenses are the right home, not Phase A.

**Verdict:** **REMOVE from Phase A** — defer to Phase C (Field Leadership lens). The Executive view should not contain supervisor-tier metrics.

---

### 2.7 Card 7 · Approvals Aging

| Question | Answer |
|---|---|
| Why does leadership need this? | POs blocked in approval directly cost revenue (delayed materials → delayed work). |
| What decision does it support? | "Which approval needs me to push it?" |
| Action if RED? | Operations Director / executive approver makes the call or forces escalation. |
| Owner of action? | The named approver per `APPROVAL_PERMISSION_MATRIX.md`. |
| What if this card doesn't exist? | Per-portal PO digests exist; no executive-roll-up. Genuine gap. |

**Strongest objections:**
- **5-day RED threshold assumes a turnaround norm that isn't proven for MASCI.** Some POs legitimately take 7–14 days (vendor research, capital approval, owner sign-off on subcontractor changes). Need operator input on actual SLA.
- **APP-4 (receipt-missing) overlaps existing `po_digest_admin.py` cron** — already escalates. Adding it to the dashboard doubles the channel for the same signal.
- **No vendor / dollar-amount weighting:** a $250 PO waiting 6 days has the same RAG weight as a $50,000 PO. Critical false-equivalence.

**Verdict:** **KEEP** — but threshold tunes per operator's actual PO SLA (not invented 5/7-day defaults), and add a `dollar_amount` weight modifier to ensure high-dollar aging is more visible than low-dollar aging.

---

### 2.8 Card 8 · Projects at Risk

| Question | Answer |
|---|---|
| Why does leadership need this? | THE highest-value question — "which project is going off the rails?" Reduces firefighting. |
| What decision does it support? | "Where should I focus my next site visit / staffing reshuffle / customer call?" |
| Action if RED? | Operations Director engages PM, may convene project-recovery meeting. |
| Owner of action? | PM (primary), Operations Director (escalation). |
| What if this card doesn't exist? | Today there is no rolled-up project health; leadership reactively learns project pain from incidents/escalations. Major gap. |

**Strongest objections:**
- **Composite-of-composites complexity:** Card 8 = max(Card 1, Card 2, Card 3 restricted to project) + new project-only rules. If the underlying cards are noisy, this card amplifies the noise.
- **PRJ-2 (P&L variance) data quality unknown:** the `projects.pnl` field exists but is sparsely populated. Rule may be OFF for most projects → silent false negative for the very projects most at risk financially.
- **Cadence rule timezone/calendar problem:** PRJ-1 "no DR in 3 working days" still requires a working-day definition the platform doesn't have.
- **Lag indicator vs leading indicator:** this card is largely lagging (RED only after problems compound). The early-warning value requires Phase B+ recommender intelligence.

**Verdict:** **MODIFY (DEFER to Phase B).** Phase A is not ready to deliver a credible projects-at-risk score. Building it on shaky cadence assumptions trains leadership to distrust the dashboard. Phase B (with the recommender + at least a working-day calendar config + data-quality probe on `projects.pnl`) is the right home.

---

### 2.9 Card 9 · Operational Bottlenecks

| Question | Answer |
|---|---|
| Why does leadership need this? | Spot stuck workflows that quietly drag operations down. |
| What decision does it support? | "Where's the system jammed?" |
| Action if RED? | Unblock by direct intervention or rebroadcast notification. |
| Owner of action? | Varies — Operations Director triages. |
| What if this card doesn't exist? | Bottlenecks today are invisible until they cause customer complaints. Real gap. |

**Strongest objections:**
- **3 of 5 rules acknowledged as duplicates in the heatmap spec itself:**
  - BNK-2 (DRs unreviewed >48h) overlaps Card 4 / Card 5.
  - BNK-3 (POs >5d in queue) explicitly flagged as duplicate of APP-2/APP-3.
  - BNK-4 (OOS w/o WO) duplicates EQP-1/EQP-4.
- **Remaining 2 rules (BNK-1, BNK-5) are weak.** BNK-1 ("dispatch stuck >24h in same state") is plausible but no operator-validated baseline exists for "stuck." BNK-5 (`operations_events.status=stuck`) depends on a field that may not consistently exist (per data source map row 9, flagged 🟡).
- **As a result, Card 9 has no unique signal of its own.**

**Verdict:** **REMOVE from Phase A.** Re-evaluate after Phase A reveals which bottleneck signals are genuinely missing from cards 1–7. Phase B may re-introduce as a refined Bottleneck Detector only if Phase A telemetry shows a gap.

---

### 2.10 Card 10 · Recommender

| Question | Answer |
|---|---|
| Why does leadership need this? | The promise — "what should I focus on next?" answered automatically. |
| What decision does it support? | Direct opening-of-the-day prioritization. |
| Action if RED? | Open the highest-ranked item. |
| Owner of action? | Operations Director directly. |
| What if this card doesn't exist? | Leadership reads cards 1–9 and judges priority manually. Acceptable for Phase A; ideal in Phase B. |

**Strongest objections:**
- **Premature optimization risk:** the priority_score formula uses domain_weight constants invented without evidence. If the formula is wrong, leadership will be misled by the very surface designed to answer the headline operator question.
- **Black-box adoption hazard:** once leadership starts relying on the Top-5 stack, judgment may atrophy. The recommender must be **explainable** (each item shows the rule that ranked it) before it can ship.
- **Phase A vs Phase B conflict:** the blueprint already places the Recommender in Phase B (`EXECUTIVE_IMPLEMENTATION_ROADMAP.md` §2.2). But the **spec mocks the Priority Stack on every screenshot description**, implying it's Phase A. Inconsistent.

**Verdict:** **DEFER to Phase B.** Phase A ships without the Priority Stack. Leadership reads the 4–5 surviving cards and prioritizes manually. After 2–4 weeks of dashboard usage, real telemetry can inform the recommender's weights — evidence-based rather than guessed.

---

## 3 · Summary verdict table

| # | Card | Phase A verdict | Reason |
|---|---|---|---|
| 1 | Jobs Today | MODIFY | Drop JOBS-3 · weekday-aware JOBS-1 · dedup JOBS-2 vs SAF-1 |
| 2 | Safety Today | KEEP (small modify) | Gate SAF-4 on active projects · add chronic-yellow CA rule |
| 3 | Equipment Today | KEEP (small modify) | Whitelist hold reasons · consolidate EQP-1/EQP-4 · age modifier EQP-2 |
| 4 | Accountability Overdue | MODIFY | Remove ACC-3 · filter to high-priority tasks · raise thresholds |
| 5 | PM Load | **REMOVE** from Phase A | Opaque score · PTO false positives · cultural artifact, not ops |
| 6 | Supervisor Load | **REMOVE** from Phase A | Replicates FL portal · audience mismatch · belongs to Phase C |
| 7 | Approvals Aging | KEEP (operator threshold) | Operator must set true PO SLA · add $-amount weight |
| 8 | Projects at Risk | **DEFER to Phase B** | Cadence + P&L data not ready · composite-of-composites amplifies noise |
| 9 | Operational Bottlenecks | **REMOVE** from Phase A | 3 of 5 rules acknowledged duplicates · no unique signal |
| 10 | Recommender | **DEFER to Phase B** (as already planned, but reaffirmed) | Premature without telemetry · black-box adoption risk |

**Phase A surface after this review: 4 cards** (Jobs Today modified · Safety Today · Equipment Today · Approvals Aging) + **1 modified Accountability card** = **5 high-confidence cards**, no Priority Stack, plus the **Pulse Strip** as a composite of those 5.

That is a sharper, smaller, more defensible Phase A than the original blueprint.

---

## 4 · What the review accepts as still-valid from the blueprint

- The 5-sec/60-sec/5-min layout doctrine.
- The `recovery/snapshot`-pattern adoption (RAG pill + `warnings[]` + `computed_at`).
- The "every red/amber item must answer 5 questions" rule.
- The drill-to-existing-detail-pages rule (no duplicate detail pages).
- The threshold-tunability requirement (no hardcoded RAG cutoffs in JSX).
- The Phase B → Phase C → Pillar 4 dependency graph.
- The non-goals list (no notifications, no mobile, no write surface).

These survive the review intact. The fix is in the **card selection and rule design**, not the architecture.

---

## 5 · See also

- `EXECUTIVE_COMMAND_CENTER_RISK_ANALYSIS.md` — missing exec questions · noise generators · false-positive / false-negative inventory · data-quality risks.
- `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` — questions the operator must answer before Phase A is authorized.
- `FINAL_PHASE_A_RECOMMENDATION.md` — the consolidated KEEP/MODIFY/REMOVE call sheet and the slimmer Phase A blueprint that emerges from this review.

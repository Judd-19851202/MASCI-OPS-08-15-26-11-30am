# Executive Command Center — Operator Challenge Questions (Pillar 2)

**Classification:** OMEGA Pillar 2 · OPERATOR INPUT REQUIRED · No code · No DB · No endpoints · No UI
**Generated:** 2026-05-31 UTC
**Author:** E1
**Audience:** Operations Leadership (Jaymn) · Executive Leadership Team
**Purpose:** Surface every decision the operator must make BEFORE Phase A implementation is authorized. Each question is action-blocking — Phase A cannot start until the operator answers.
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_DESIGN_REVIEW.md` · `EXECUTIVE_COMMAND_CENTER_RISK_ANALYSIS.md` · `FINAL_PHASE_A_RECOMMENDATION.md`

---

## 1 · Why these questions block implementation

Every question below maps to a design decision that, if guessed by the agent, will:
- bake operator opinion into code as a hardcoded threshold, OR
- create a noise generator that erodes trust in the dashboard, OR
- couple Phase A to data quality that hasn't been audited.

Refusing to answer is acceptable — the agent will then defer that capability to Phase B/C. But **silent assumptions are not acceptable** under OMEGA discipline.

---

## 2 · Strategic challenge questions

### Q-1 · Does the Operations Director want a load scoreboard for PMs / Supervisors?

The design review's verdict (Cards 5 and 6) is to **REMOVE** the load cards from Phase A on three grounds: opaque composite scores, PTO false-positive engine, replicates leadership's existing informal awareness.

| Option | Implication |
|---|---|
| a. Confirm REMOVE from Phase A · revisit in Phase C as opt-in lens | Dashboard slimmer · no surveillance feel · evidence-led |
| b. Keep a **passive activity strip** (no RAG, just numbers) for PMs only | Compromise · gives data without judgment |
| c. Keep full scoring · operator accepts known false-positive rate | Higher noise · faster delivery of "is X overloaded?" signal |

**Default if unanswered: option (a). Defer to Phase C.**

---

### Q-2 · Should the Recommender / Priority Stack ship in Phase A or Phase B?

The original blueprint placed the Recommender in Phase B (roadmap §2.2) but described the Priority Stack as a Phase A surface (spec §4). This contradiction must be resolved.

| Option | Implication |
|---|---|
| a. Recommender + Priority Stack are **Phase B only**. Phase A ships without the Top-5 stack. Leadership prioritizes manually across 4–5 cards. | Honest · evidence-led · matches roadmap |
| b. Ship a "naive" Priority Stack in Phase A: just sorts all RED items by age. No weighted score. | Quick win · risks training leadership to trust naive ordering |
| c. Ship the full weighted Recommender in Phase A | Phase A bloats · weights unproven · adoption risk |

**Default if unanswered: option (a). Phase A has no Priority Stack.**

---

### Q-3 · Is `document_expirations` data sufficient to power MX-3 (Expirations Card) in Phase A?

The risk analysis recommends adding an Expirations card. The collection has 23 code references but data-completeness is unaudited.

| Option | Implication |
|---|---|
| a. Audit the collection BEFORE Phase A authorization · ship MX-3 if ≥80% coverage on critical doc types (CDL · insurance · trainer-of-record · OSHA-30) | Strongest · evidence-led |
| b. Ship MX-3 in Phase A with whatever data exists · accept partial coverage RED state | Riskier — could be a noise generator if rows missing |
| c. Defer MX-3 to Phase B | Cleaner Phase A but misses the biggest "missing executive question" gap |

**Default if unanswered: option (a). Audit first.**

---

### Q-4 · Should Card 8 (Projects at Risk) ship in Phase A or Phase B?

Design review verdict: **DEFER to Phase B**. Reasons: composite-of-composites amplifies noise · cadence rule needs working-day calendar · P&L data quality unknown.

| Option | Implication |
|---|---|
| a. Confirm DEFER to Phase B | Honest about data readiness |
| b. Ship a "skeleton" projects-at-risk card in Phase A that simply max-rolls Cards 1/2/3 per project — no P&L, no cadence | Low value but visible · honest about being a Phase B placeholder |
| c. Ship the full Phase B design in Phase A | Forces P&L + calendar audit upfront · stretches Phase A scope |

**Default if unanswered: option (a). Phase A excludes Card 8.**

---

### Q-5 · Is there a PTO / holiday / no-work calendar the platform can consume?

Multiple rules (JOBS-1, PML-2, PRJ-1) depend on knowing what "a working day" is. Without it, weekend/holiday/PTO false positives are guaranteed.

| Option | Implication |
|---|---|
| a. There IS a calendar source — please name it (path, API, doc) | Phase A enables proper weekday-awareness |
| b. There IS NOT — Phase A treats Mon–Fri 06:00–18:00 local as "working hours" by static config, and the operator manually marks holidays in a small admin form | Pragmatic; needs ~30 LOC of holidays config UI added to Phase A |
| c. Defer all weekday-aware rules until calendar source exists | JOBS-1 simplified to "no DR in last 36 hours" period · accepts weekend false positives |

**Default if unanswered: option (b). Add a `command_center_calendar` config doc to Phase A scope.**

---

### Q-6 · Is `incidents.severity` consistently calibrated across submitters?

SAF-1 fires RAG based on operator-entered severity. If safety submitters use the levels inconsistently, the entire Safety card is unreliable.

| Option | Implication |
|---|---|
| a. Yes — severity is well-calibrated; trust the field | Ship as designed |
| b. Severity is roughly calibrated but needs an audit; gate Phase A on a one-time severity audit pass | Highest evidence floor |
| c. Severity is **not** trusted; replace severity-based rules with description-keyword detection (e.g., "OSHA," "EMS," "hospital," "injury," "near-miss") | More complex; requires keyword list config |

**Default if unanswered: option (b). One-time audit before Phase A goes live to pilot users.**

---

## 3 · Tactical / numeric questions

### Q-7 · What is MASCI's actual PO approval-turnaround SLA?

Phase A Card 7 threshold defaults are 3-day AMBER, 5-day RED. The defaults are **invented**. The operator must provide reality:

> "A normal PO at MASCI is approved within ___ business days. Anything over ___ business days is operationally late."

The two numbers populate AMBER and RED for APP-1/APP-2/APP-3 in the threshold config doc.

**Default if unanswered:** Phase A ships with 3/5-day defaults and the threshold tuner exposed so the operator can correct within the first pilot week.

---

### Q-8 · What dollar threshold elevates a PO to "executive-attention" automatically?

The risk analysis flags that a $250 PO aging 6 days and a $50,000 PO aging 6 days should not be equal RED items.

> "Any PO ≥ $___ aging beyond Q-7's RED threshold becomes a Priority Stack item automatically."

**Default if unanswered:** Phase A ships **without** dollar weighting; all RED POs treated equally. Add weighting in Phase B once operator names the threshold.

---

### Q-9 · How should the Pulse Strip handle the existing Backup AMBER state?

`/admin/recovery/snapshot` already returns `pill: AMBER` due to long-standing R2 bucket usage and RTO-no-drill. Should the Pulse Strip:

| Option | Implication |
|---|---|
| a. **Exclude** backup signal from Pulse — keep it on `/admin/recovery` only · link from header | Cleanest — Pulse Strip is operations only |
| b. **Include** backup signal — Pulse goes AMBER any time recovery snapshot is AMBER | Aligned but conflates ops with infra |
| c. Show backup as a **separate mini-pill** beside the main Pulse | Compromise; visually busier |

**Default if unanswered: option (a). Pulse Strip = operations only. Backup link present but separate.**

---

### Q-10 · Manual refresh, auto-refresh, or both?

| Option | Implication |
|---|---|
| a. Manual button only · `computed_at` always visible | Cleanest · no hidden polling cost |
| b. 60-sec auto-refresh while page is open · pause when window unfocused | More live · trivial polling cost |
| c. Both · auto-refresh toggle in user prefs (off by default) | Most flexible |

**Default if unanswered: option (a). Manual refresh only in Phase A.**

---

### Q-11 · Mobile/tablet support for Phase A?

The spec declares desktop-only. Confirm.

| Option | Implication |
|---|---|
| a. Desktop-only · Phase A | Matches spec · simplest |
| b. Tablet landscape responsive (iPad-class) · Phase A | Doubles QA surface |
| c. Mobile responsive (phone-class) · Phase A | Triples QA surface; not recommended |

**Default if unanswered: option (a). Desktop-only.**

---

### Q-12 · Who is the Phase A pilot user set?

For the closeout report to include real time-to-priority-identification telemetry, named pilot users must be identified.

> Pilot users (name + portal):
> - Operations Director: _____ (super_admin)
> - Executive: _____ (admin)
> - PM lead: _____ (pm)
> - Safety lead: _____ (safety)
> - (optional) Shop lead: _____ (shop)

These users get exclusive access during pilot. Their before/after time-to-priority-identification is the gating measurement.

**Default if unanswered:** Phase A cannot reach closeout because acceptance criterion §A.3.9 requires this data. Cannot proceed without input.

---

### Q-13 · Should the Command Center include a "What just resolved?" panel?

Mentioned in risk analysis as a trust-builder. Low cost to ship.

| Option | Implication |
|---|---|
| a. Yes — small panel below cards showing last 5 items resolved in the past 24h | +20 LOC · improves dashboard trust |
| b. No — pure pain instrument, save space | Cleaner but emotionally heavier dashboard |

**Default if unanswered: option (b). Skip for Phase A; revisit Phase B.**

---

## 4 · RBAC / governance questions

### Q-14 · Should a new `executive_leadership` directory role be created?

Currently the directory supports super_admin · admin · pm · hr · safety · shop · dispatch · fl · field_leadership_portal. The Command Center audience is "Operations Director + Executive Leadership Team," which doesn't cleanly fit any existing role.

| Option | Implication |
|---|---|
| a. Reuse `super_admin` only — only Jaymn has access in Phase A · expand role model in Phase C | Simplest · matches current super_admin pattern |
| b. Create new `executive_leadership` directory role · admin-strict-equivalent for read access | More flexible · larger Phase A surface |
| c. Use admin role + a flag (`is_executive` boolean on `user_directory`) | Minimal schema change · keeps role model stable |

**Default if unanswered: option (a). super_admin only in Phase A.**

---

### Q-15 · Threshold tuning audience?

| Option | Implication |
|---|---|
| a. super_admin only | Tightest control |
| b. admin + super_admin · `X-Directory-Token` required | Matches existing admin-strict pattern |
| c. Anyone with a `manage_command_center` policy capability (new policy) | Most flexible · requires new policy logic |

**Default if unanswered: option (a). super_admin only.**

---

### Q-16 · Audit logging of threshold changes?

| Option | Implication |
|---|---|
| a. Every threshold change writes to `admin_audit` with before/after values | Strong accountability · ~10 LOC additional |
| b. No audit (small org, small operator pool) | Risky · violates Accountability Pillar 3 doctrine |

**Default if unanswered: option (a). Mandatory audit log entries.**

---

## 5 · Process / next-step questions

### Q-17 · Pilot duration?

| Option | Implication |
|---|---|
| a. 2 weeks · then Phase B authorization decision | Faster iteration |
| b. 4 weeks · then Phase B authorization decision | Closer to a representative "month of operations" sample |
| c. Open-ended until operator decides | Risks indefinite Phase A |

**Default if unanswered: option (b). 4 weeks then operator review.**

---

### Q-18 · Phase A closeout report — who reviews and signs off?

| Role | Required signature |
|---|---|
| Operations Director (Jaymn) | mandatory |
| Safety lead | optional · for SAF rule sign-off |
| Shop lead | optional · for EQP rule sign-off |
| Admin / approver per `APPROVAL_PERMISSION_MATRIX.md` | mandatory for any threshold change PR |

**Default if unanswered:** Operations Director sign-off is the single gating signature.

---

### Q-19 · What stops a future agent from drifting into Pillar 4 (notifications/escalation) during Phase A?

The Command Center spec is explicit that it emits no signals. Phase A code in `routes/command_center.py` will be reviewed for any `emit_notification` / `schedule_auto_email` / `task_service.create` calls. Confirm:

> Operator confirms: Phase A code MUST contain ZERO calls to fan-out helpers. Any such call is an OMEGA discipline violation and triggers stop-condition A.4.

**Default if unanswered:** assumed YES — drift is unauthorized.

---

## 6 · Summary of answer-blocking impact

| Question | Required to ship Phase A? |
|---|---|
| Q-1 PM/Supervisor load posture | YES — affects card count |
| Q-2 Recommender phase | YES — affects card count |
| Q-3 Expirations data audit | YES — affects MX-3 inclusion |
| Q-4 Projects-at-Risk phase | YES — affects card count |
| Q-5 PTO/holiday calendar | YES — affects rule design |
| Q-6 Incident severity calibration | YES — affects Safety card trust |
| Q-7 PO SLA | YES — affects Approvals thresholds |
| Q-8 PO dollar weighting | NO (Phase B) |
| Q-9 Pulse + Backup posture | YES — affects Pulse Strip composition |
| Q-10 Refresh behavior | NO (default acceptable) |
| Q-11 Mobile/tablet support | NO (default acceptable) |
| Q-12 Pilot user set | **YES — closeout cannot complete without** |
| Q-13 "Just resolved" panel | NO (default acceptable) |
| Q-14 Executive role | YES — affects auth wiring |
| Q-15 Threshold tuning audience | YES — affects auth wiring |
| Q-16 Audit logging | NO (default mandatory) |
| Q-17 Pilot duration | NO (default acceptable) |
| Q-18 Sign-off | NO (default acceptable) |
| Q-19 Pillar-4 drift | NO (default mandatory) |

**Hard-blocking questions: Q-1, Q-2, Q-3, Q-4, Q-5, Q-6, Q-7, Q-9, Q-12, Q-14, Q-15** = 11 questions. Without these, Phase A either bakes in unverified opinion or cannot reach closeout.

The agent will halt at the start of any future Phase A batch until these are answered (or the operator explicitly accepts the listed defaults).

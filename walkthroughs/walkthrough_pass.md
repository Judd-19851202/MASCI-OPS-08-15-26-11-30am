# Walkthrough Pass — Editorial Discipline Protocol

> **Audience:** the next operator, contributor, or agent picking up the
> MASCI Operations Platform's contextual-coaching system.
>
> **Status:** load-bearing protocol document. The walkthrough/coaching
> refinement loop is one of the platform's strongest operational
> differentiators — preserve the discipline, not just the artifacts.
>
> **Established:** iter217 (framework) → iter218 (first refinement pass) →
> iter219 (operational-polish pass). Demonstrated reduction: **16 → 5
> actionable findings (-69%) across three cycles, zero regressions.**

---

## 0 · What this loop IS — and what it isn't

**IS:** an editorial cadence for the contextual operational coaching
system (HelpTip engine + reviewer-side coaching + onboarding entries).
It's the discipline that keeps the platform's coaching voice
operationally real and the workflow continuity honest.

**IS NOT:**
- a UI-test framework (no pass/fail gating on findings)
- an analytics system (no Mongo collections of walkthrough runs)
- a telemetry stream (production never emits walkthrough events)
- a dashboard surface (findings live in JSON, read by humans)
- a regression-score-over-time leaderboard (numbers are signal, not target)
- an LMS (no quizzes, no certifications, no completion %)

**If any of the "IS NOT" patterns start to creep in, REVERT.** The
moment the loop becomes a dashboard surface, it becomes an analytics
project and stops being editorial leverage.

---

## 1 · Persona execution order (operator-stated · DO NOT REORDER)

```
1. Foreman          — mobile · 414×896 · field-first    · highest workflow density
2. Superintendent   — tablet · 768×1024 · cross-portal  · multi-job oversight
3. Operator         — mobile · 414×896 · field-first    · single-machine focus
4. Dispatcher       — desktop · 1280×800 · office       · multi-tab dashboard
5. HR               — desktop · 1280×800 · office       · payroll + people ops
6. Safety           — tablet · 768×1024 · field-office  · incident + audit
7. PM               — desktop · 1280×800 · office       · project margin
8. Laborer (new)    — mobile · 414×896 · Day-1          · discoverability bar at MAX
```

Order matters: **highest operational friction first.** Foremen are the
densest workflow surface — if their experience is rough, everything
downstream is rough.

---

## 2 · Walkthrough execution expectations

### When to run a pass

- **After authoring new coaching** (must validate the gap closed)
- **After major surface refactors** (must validate IA still works)
- **Before declaring a coaching iter complete** (delta measurement)
- **Quarterly editorial review** (drift catches)

**Do NOT run walkthroughs on every commit. They are an editorial tool,
not a CI gate.**

### How to run

```bash
# One persona
PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python /app/walkthroughs/foreman.py

# Full sweep (in operator-stated priority order)
for p in foreman superintendent operator dispatcher hr safety pm laborer; do
  PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python /app/walkthroughs/${p}.py
done

# Aggregate findings into the editorial backlog
python /app/walkthroughs/aggregate_findings.py
```

### What each walkthrough produces

- `/app/walkthrough_reports/{persona}/{step-slug}.png` — step screenshots
- `/app/walkthrough_reports/{persona}_findings.json` — typed findings
- `/app/walkthrough_reports/_backlog.json` — sorted prioritized actionable list

### What a walkthrough simulates

A real persona's day. **Not** a script of every clickable element.
Operational moments: arrival → first action → escalation moment →
end-of-day. If a walkthrough step doesn't correspond to a real
operational moment a real human would experience, cut it.

---

## 3 · Finding kinds — the load-bearing vocabulary

Defined in `/app/walkthroughs/_runner.py::FINDING_KINDS`. **Adding a
new kind requires updating the smoke test (`test_iter217_walkthrough_smoke.py`).**

| Kind                    | When to emit                                                    |
|-------------------------|-----------------------------------------------------------------|
| `no-escalation-path`    | High-stakes moment, no coaching about when to stop or call up   |
| `voice-drift`           | Coaching landed but tone is robotic / corporate / OSHA-manual   |
| `missing-coaching`      | Surface needs a HelpTip block and has none                      |
| `weak-tip`              | HelpTip present but operationally shallow / generic             |
| `unclear-wording`       | Words don't land for the persona (jargon, ambiguity, vague)     |
| `workflow-confusion`    | Persona doesn't know what to do next                            |
| `discoverability-gap`   | Right surface exists but persona can't see it from where they are |
| `mobile-clipping`       | Awkward wrap / oversized body / thumb fatigue at 414px          |
| `friction`              | Catch-all for operational drag not fitting elsewhere            |
| `positive-observation`  | Something is working well — preserve so it isn't regressed      |

**Banned vocabulary:** `warning`, `error`, `info`, `bug`, `defect`,
`severity-1`, anything that sounds like a JIRA ticket triage taxonomy.
The operator-load-bearing language is intentional.

---

## 4 · Finding review cadence

### After each walkthrough pass:

1. Run `aggregate_findings.py` to produce `_backlog.json`
2. Read the **TOP-PRIORITY ACTIONABLE BACKLOG** section (terminal output)
3. Group findings by editorial-attention weight (the aggregator already sorts by kind-priority then persona-priority)
4. For each actionable finding, decide:
   - **Author coaching now** → iter the tip registry, wire the surface, re-run that persona
   - **Hold as strategic** → add to `## Strategic holds` section below with operator-stated reasoning
   - **Document architecture** → write a one-paragraph note in PRD.md so future agents don't re-discover it
   - **Mark false positive** → refine the walkthrough's check (see iter219 foreman refinement for the pattern)

### Never:

- Suppress a finding by removing the walkthrough step
- Lower the threshold of a check to make it pass
- Treat `positive-observation` count as a metric to maximize
- Treat actionable-finding count as a number to minimize at any cost

The numbers are signal. Numbers without operational reality become
theater.

---

## 5 · Coaching authoring standards

Authoring new tips happens in **two files**:

- `/app/backend/guidance/tips.py` — EN registry entries
- `/app/backend/guidance/tips_es.py` — ES translations keyed by `(form_key, kind)`

### Canonical surface = 4 tips minimum

Every new `form_key` family must expose at minimum the **canonical 4
operational moments**:
- **why** — why this surface exists operationally
- **who** — who reads this downstream (the 3-5 humans who depend on the data)
- **next** — what happens after the user signs/submits
- **escalate** — when to stop and call up instead of completing the form

Optional sub-surfaces (`.{leaf}` form_keys) can add `mistake`,
`example`, or domain-specific kinds.

### Tone discipline (load-bearing)

Every tip body must:
- be ≤80 words EN, ≤90 words ES
- contain at least one **persona-anchor phrase** from the field-realism
  vocabulary: `foreman · crew · super · dispatch · HR · PM · Shop ·
  Safety · operator · jobsite · supplier · driver · schedule · field`
- pass the **banlists** in the per-iter test file:
  - `ROBOTIC_OSHA_PHRASES` (iter211 baseline · "in accordance with",
    "pursuant to", "shall be required to", etc.)
  - `CORPORATE_DRIFT_PHRASES` (synergize, stakeholder alignment,
    leverage synergies, best-in-class, core competency)
  - `HR_LEGAL_DRIFT_PHRASES` (progressive discipline policy,
    at-will employment, performance improvement plan procedure) —
    load-bearing for HR-adjacent surfaces
  - `CORPORATE_HR_PHRASES` (human capital, team member engagement)

### Positive realism anchors

Each tip family must have at least one **operator-stated cultural
anchor** asserted as a positive-realism test. Examples from prior iters:

| Iter | Family                         | Cultural anchor                                                                     |
|------|--------------------------------|-------------------------------------------------------------------------------------|
| 211  | preop.signoff                  | "Your name is on it — the pressure-to-sign moment is the coaching moment."         |
| 212  | checkout                       | "Checkout is the handshake — you say 'I have this', the system says 'you have this'." |
| 213  | time-verification              | "This is where field hours become paychecks. Quiet edits break trust."             |
| 214  | writeup                        | "The paper is the evidence; the conversation is the work."                          |
| 215  | material-calculator            | "The calculator is for planning; the Daily Report is for truth."                   |
| 216  | dispatch.transfers             | "Dispatch is the operational referee."                                              |
| 218  | field-leadership.records       | "Reviewing isn't auditing — it's the supervisor's reading of the crew's work."     |
| 218  | crew_eval                      | "Calibration beats scoring; specific examples beat generalizations."                |
| 218  | dispatch.idle-alerts           | "Opportunity, not blame; discovery, not gotcha."                                    |
| 218  | dispatch.holds                 | "See and route around — don't second-guess; Safety/Shop decides, Dispatch reads."  |

**A new family without a positive-realism anchor is not done.**

### RBAC discipline

Scope (`scopes: []`) controls who sees the tip via the
`/api/guidance/tips` endpoint. Honest scopes only:
- `public` — anyone, no auth required
- `leadership` — foreman / super / FL-token holders
- `admin` — admin token (also inherits everything operational)
- `hr` / `safety` / `shop` / `dispatch` / `pm` — portal-specific

**Reviewer-side coaching (introduced iter218)** is a NEW operational
class: tips that coach the PERSON REVIEWING a filing, not the person
who filed it. Records-list pages, Time Verification, holds review —
all reviewer-side. Scope them to the reviewing roles only.

### Bilingual discipline

Every EN tip MUST have a body_es. Translations:
- preserve the operator's voice (informal, direct, no academic Spanish)
- keep concrete details intact (specific times, dollar amounts, units)
- use field-current operational vocabulary, not dictionary Spanish
- pass the same word-count budget (≤90 ES words)
- run through the same banlist (ES OSHA-speak is its own variety —
  "en cumplimiento con", "según lo estipulado", etc.)

---

## 6 · Re-run expectations after authoring coaching

After authoring coaching for a finding:

1. Run that persona's walkthrough alone
2. Verify the finding's slug is no longer in the new findings list (or has converted to `positive-observation`)
3. Run any persona whose day touches the same surface (e.g. authoring `dispatch.transfers` affects both Dispatcher AND Foreman walkthroughs because the foreman files Daily-Report equipment notes that Dispatch reads)
4. Re-aggregate
5. Compare actionable-finding counts: previous vs current

**Expected delta after each authoring pass: actionable count drops
≥1 per closed gap. If it doesn't, either the coaching missed the
operational moment or the walkthrough check is wrong.**

---

## 7 · Actionable-finding delta tracking

Track in PRD.md per iter. Example format (proven across iter218 + iter219):

```
| Persona       | Before iter | After iter | Delta |
| Foreman       | 1           | 0          | -1 ✅ |
| Dispatcher    | 4           | 0          | -4 ✅ |
| Total actionable | 16        | 5          | -11    |
```

This is not analytics. It's the smallest possible measurement that
confirms editorial work is improving operational continuity rather
than just adding text.

### When the actionable count GOES UP

Two operationally-healthy reasons exist:

1. **A scaffolded persona walkthrough was fleshed out** — what was
   previously 1 placeholder friction becomes N real operational gaps
   surfaced by an honest day-script. The total rose, but the platform
   didn't regress — coverage expanded. (Demonstrated iter221:
   fleshing the HR scaffold went 5 → 12 actionable; net was +8
   missing-coaching/discoverability findings on previously-hidden HR
   surfaces.)

2. **A new portal / feature shipped without coaching coverage** —
   the walkthrough catches it. Same loop: author the coaching, the
   number drops.

Neither case is a regression. The actionable count is only a
regression signal **when the surfaces and walkthroughs are constant
between runs** and the number still rises — that means coaching that
used to land no longer does.

### When the actionable count SHOULD be ignored

- Right after fleshing a scaffold (read the new findings as the new
  authoring backlog, not as a regression)
- Right after a major IA change (the walkthroughs may need their
  expectations refined — see iter219 foreman false-positive fix)
- When the operator has explicitly added strategic holds that prevent
  closing certain findings (mid-day-defect, etc.)

---

## 8 · Operational realism requirements

Every walkthrough STEP and every coaching TIP must answer:

- **What time of day does this happen?** (06:15 yard arrival, 11:00
  mid-day defect, 14:00 audit walk, 17:30 end-of-day)
- **What's the persona's physical context?** (phone in glove · tablet on
  dashboard · laptop at office desk · standing at the yard QR poster)
- **What just happened before, and what happens after?**
  (workflow continuity, not isolated screens)
- **What goes wrong when this surface fails?**
  (real consequences, not "the user has a poor experience")

If the answer to any of those is hand-wavy, the walkthrough step or
the tip is not operationally grounded yet.

---

## 9 · Anti-pattern guardrails (HARD STOPS)

Never:

- ❌ Add a Mongo collection storing walkthrough runs
- ❌ Build a dashboard rendering walkthrough trends over time
- ❌ Add a "score" or "grade" or "% complete" to any persona walkthrough
- ❌ Emit telemetry from the production app for any walkthrough purpose
- ❌ Add finding kinds without operator-explicit approval
- ❌ Convert findings into JIRA tickets, GitHub issues, or any pipeline
- ❌ Run walkthroughs as part of CI pass/fail gates
- ❌ Add "engagement metrics" to HelpTips themselves (held — see Strategic holds)
- ❌ Generalize the walkthrough framework with "page object models" or other test-framework abstractions
- ❌ Add an LMS layer (quizzes, certifications, completion tracking)
- ❌ Skip the operator's approval before authoring large new tip families

If a future agent is tempted to add any of the above, the response is:
**revert and re-read this protocol.** The editorial cadence is the
value. Adding tooling around the cadence does not improve it; it
dilutes it.

---

## 10 · Strategic holds

Items DELIBERATELY NOT IN SCOPE for tactical walkthrough patching.
These affect platform-level operational philosophy and require
intentional operator-driven architectural design.

| Item                            | Operator-stated reasoning                                                                          | Status |
|---------------------------------|----------------------------------------------------------------------------------------------------|--------|
| Operator mid-day-defect surface | Affects escalation culture · operational communication expectations · ownership boundaries · field defect routing philosophy. Treat as deliberate future operational architecture decision, NOT a tactical patch. | HELD — operator directive 2026-05-18 |
| HelpTip helpfulness-pulse telemetry | Held until Sentry activation · R2 lifecycle activation · timeout production rollout · Phase 2 hardening verification close-out. | HELD — post-hardening |

**Do not implement these unless and until the operator explicitly
moves them out of strategic hold.** "It would be easy to add" is the
wrong reason to break a deliberate hold.

---

## 11 · The cadence in one paragraph

> Run the walkthroughs in operator-stated persona order at the
> documented viewports. Aggregate findings into the backlog. Read the
> typed observations in the operator's voice vocabulary. For each
> actionable finding, decide: author coaching · hold as strategic ·
> document architecture · mark false positive. Authoring follows the
> canonical-4 surface pattern with the load-bearing tone discipline,
> bilingual quality, RBAC honesty, and a positive-realism cultural
> anchor. Re-run the affected personas. Measure the delta. Update
> PRD.md. Never let the cadence become analytics.

That's the whole thing. Everything in this document is just the
operator-stated discipline that protects this paragraph.

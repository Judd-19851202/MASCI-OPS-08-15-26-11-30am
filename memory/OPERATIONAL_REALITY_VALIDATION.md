# OPERATIONAL REALITY VALIDATION

**Authority**: FOCP MASTER PROGRAM · Phase 12
**Status**: 🟡 **DEFERRED — CANNOT BE DONE BY AI ALONE**
**TR ID**: TR-D002

---

## Why this is deferred

Phase 12 explicitly requires interviewing seven personas (HR, Safety, Payroll, PM, Superintendent, Dispatch, Executive) about actual MASCI operations. AI cannot conduct interviews. AI cannot ask follow-up questions in a meeting. AI cannot read faces or hear hesitations.

What AI CAN do is **propose the interview script + scoring rubric + reality-difference matrix**, so that when the operator conducts the interviews, the captured data can be incorporated efficiently.

---

## Proposed interview protocol (operator-led)

### Per-persona script (45-60 min)

For each persona, three sections:

**Section A · Today's actual workflow (15 min)** — "Walk me through your last 5 working days. Show me what you actually click, what you actually look at, what you actually print."

**Section B · Pain points (15 min)** — "What do you do that the platform makes hard? What do you do outside the platform that should be inside? Where do you ask Jaymn for help?"

**Section C · Reality match (15-30 min)** — Present 8-12 candidate workflows (from `WORKFLOW_COMPLETENESS_REGISTER.md`) and ask: "Does this match how you actually do it? If no, what's different?"

### Reality difference matrix (template for operator to fill)

| Workflow | Per-persona reality match | Platform behavior | Reality behavior | Gap class |
|---|---|---|---|---|
| Daily Report | (Foreman / PM) | … | … | matches / drift / divergent |
| Incident filing | (Safety / PM) | … | … | matches / drift / divergent |
| Time-Off request | (Employee / HR) | … | … | matches / drift / divergent |
| Payroll variance flag | (Payroll / HR) | … | … | matches / drift / divergent |
| QA/QC closure | (QA / PM) | … | … | matches / drift / divergent |
| Dispatch reassignment | (Dispatch / Driver) | … | … | matches / drift / divergent |
| Asset transfer | (Dispatch / Shop) | … | … | matches / drift / divergent |
| Employee termination | (HR / Manager) | … | … | matches / drift / divergent |
| Constraint resolution | (Superintendent / PM) | … | … | matches / drift / divergent |
| Equipment hold + release | (Dispatch / Safety / Shop) | … | … | matches / drift / divergent |
| JHP / JHA acknowledgement | (Safety / Foreman) | … (TR-0001 absent) | … | divergent |
| Executive review cadence | (Executive) | … | … | matches / drift / divergent |

### Scoring per-persona

For each persona's interview, the operator scores:

* **Reality coverage** (% of their daily tasks the platform supports without workarounds): 0-100%
* **Platform trust** (1-5): "If you have to choose between the platform and your memory, which do you trust?"
* **Jaymn dependency** (1-5): "How often per week do you ask Jaymn how to do something?"
* **Confidence without Jaymn** (1-5): "If Jaymn took a 90-day vacation, could you do your job?"
* **Spanish proficiency need** (PM / Foreman / Superintendent only): "Do you or your crew need Spanish?"

### Output of Phase 12

After all 7 interviews:

* Per-persona scorecard
* Cross-persona reality-difference matrix
* Top-N reality gaps prioritized by frequency × impact
* List of "Jaymn-only knowledge" items that the platform must absorb

---

## What I CAN provide right now (source-side proxies)

### Predicted reality gaps (source-derived, low-evidence)

| Workflow | Predicted reality-drift class | Why |
|---|---|---|
| Daily Report "Open" status | drift | FRICTION #5 still observable in source |
| Reactivate vs Rehire | divergent | FRICTION #4 — needs HR-doctrine answer |
| 5 employee statuses | divergent | FRICTION #2 — operators almost certainly use a subset |
| Equipment `expires_at` | drift | FRICTION #11 — meaning ambiguity |
| Constraint resolve vs close | drift | FRICTION #7 |
| FleetDVIR pass-with-defects | drift | FRICTION #9 |
| JHP / JHA workflow | divergent | TR-0001 — currently does not exist in app, but is done in reality |

These predictions are **hypotheses to test in Phase 12**, not findings.

## What the operator must deliver to unblock TR-D002

| Input | Effort |
|---|---|
| Schedule 7 interviews (one per persona) | 1 hour scheduling + 7 × 60 min interview |
| Conduct + transcribe each | 1 hour per interview + 1 hour transcription |
| Fill the reality-difference matrix | 2 hours synthesis |
| **Total operator effort** | **~ 12-14 hours over ~ 2 weeks** |

Once provided, AI can synthesize the findings into TR-#### entries within 1 day.

---

End of Operational Reality Validation · TR-D002 remains DEFERRED.

# FIELD TRIAL · FOREMAN FEEDBACK
## OMEGA Automated Proxy — Honest Limits

**Mode**: AUTOMATED PROXY (no real human foremen interviewed)

---

## HONEST LIMIT

The directive's foreman feedback questions are **human-only signal**.
An automated proxy cannot answer them. The 8 questions are reproduced
below verbatim for the real human trial, with the proxy's best
indirect evidence noted underneath each. **None of the answers below
are PROOF — they are inferences from the platform's behaviour that
need confirmation from real foremen.**

---

### Q1 · Was it easy to understand?
**Proxy evidence (not proof)**: form uses plain language, sectioned
disclosure (only relevant sections render based on depth/soil/system),
"Coaching, not punishment" copy block at top, Stop-Work Authority
copy block.
**Human signal needed**: yes/no from each of 3 foremen.

### Q2 · Was anything confusing?
**Proxy evidence**: live OSHA Compliance status card narrates current
state; soil-not-classified yellow callout suggests next action.
However "Emergency Excavation?" block stays in English even when the
rest of the form is Spanish — likely confusing to ES-primary foreman.
**Human signal needed**: confused-language audit per foreman.

### Q3 · Was anything too much typing?
**Proxy evidence**: form uses pickers (JobPicker, EmployeePicker,
TrenchAssetPicker, RoadPlatePicker) instead of free-text where possible.
Required free-text fields: project_name (only if Custom job), work_area,
field_notes (optional), rated-depth acknowledgement reason (only when
fired).
**Human signal needed**: foreman patience threshold on touch keyboards.

### Q4 · Was anything missing?
**Proxy evidence**: directive scope explicitly excludes new features.
The 11 certified workflows are present; FV-7 chips cover the
Superintendent's 30-second audit; reinspection trigger is present.
**Human signal needed**: missing-information report from foremen during
trial.

### Q5 · Did it slow you down?
**Proxy evidence**: API median latency 201 ms; P95 446 ms — within field
cellular bounds.
**Human signal needed**: subjective slow-down compared to paper form or
prior system.

### Q6 · Did it help you catch anything?
**Proxy evidence**: deterministic flag engine fired correctly on all
edge cases — Type C without protective system, depth ≥ 5 ft without
CP, trench-box rated-depth gap, road-plate undersize. These are
"catches" by construction.
**Human signal needed**: foremen's report of a real catch in the field
during the 3-day window.

### Q7 · Would you use this again?
**Cannot infer from proxy.** Human-only.

### Q8 · What would make it faster?
**Cannot infer from proxy.** Human-only. Likely suggestions to expect
based on field-app heuristics:
* QR scan to pre-link an asset (already deferred to future scope per OMEGA)
* Voice-to-text on field notes (not in scope)
* Last-job memory (some draft recovery exists; verify in human trial)

---

## INSTRUCTIONS FOR HUMAN TRIAL CAPTURE

When the real 3-foreman × 3-day trial runs, fill in this same template
with **exact verbatim quotes** from each foreman. Do not summarize
away complaints — directive explicit. Capture in CSV format:

```
foreman_id, day, question_number, exact_quote
FM-A, 1, Q2, "I didn't know what 'Sloping' meant on the screen"
FM-B, 1, Q3, "Too many checkboxes on the access section"
…
```

File: `/app/memory/field_trial_human_feedback_<YYYY-MM-DD>.csv`

---

## DELIVERABLE STATUS

* Automated proxy: **inference only · not proof**.
* Human verbatim capture: **OUTSTANDING**.

This file remains a **placeholder** until the real human trial runs.

# Operational Trust — Validation Report

**Phase V-Prelude · Wave 1 Observation Window**
**Status:** 🟡 **VALIDATING · operator input awaited**
**Date:** 2026-05-28

---

## Purpose

The platform crossed a doctrinal line during Wave 1: it stopped being
"software" and started being "operational trust infrastructure." This
report answers, with intellectual honesty, what is **measurable** today
and what **requires operator presence** to validate.

The 10 trust questions from the operator directive split cleanly into
two columns: machine-verifiable and operator-only.

---

## Machine-verifiable trust signals

These can be answered without operator presence. All are 🟢 green at
window open.

| # | Question | Signal | State |
|---|---|---|---|
| 1 | Is operational link integrity preserved? | `operational_links_doctrine_probe` | 🟢 0 violations · 0 rows |
| 2 | Does chronology stay calm under usage? | `timeline_calmness_probe` | 🟢 score 0.0 · 0 breaches |
| 3 | Is institutional memory un-falsifiable? | `trendline_integrity_probe` | 🟢 0 violations |
| 4 | Is timestamp doctrine intact? | `timestamp_doctrine_probe` | 🟢 0 new violations |
| 5 | Are role boundaries enforced? | PM token sweep (Wave 1.1) | 🟢 audit-only invisible to PM |
| 6 | Does mobile rendering hold? | Playwright iPhone 13 sweep | 🟢 0 body overflow |
| 7 | Does the substrate produce orphans? | Wave 1.1 no-orphan regression | 🟢 every row carries kind+id+at+project_id |
| 8 | Is the API still passive (sidecar)? | code grep + route inspection | 🟢 0 POST/PATCH/DELETE on sidecar |

## Operator-verifiable trust signals

These cannot be answered by the agent. They require the operator
(or real PMs) to interact with the platform and report findings.

| # | Question | What "yes" looks like | How to capture |
|---|---|---|---|
| 9 | Does chronology feel operationally useful? | PMs naturally check the sidecar during morning project review. | Brief field interview · note in this file. |
| 10 | Do PMs naturally understand the timeline? | No PM asks "what is this?" within 30 s of seeing the sidecar. | Observer notes during a PM session. |
| 11 | Does mobile usage remain fatigue-free? | A PM completes a full project review on iPhone without zooming in. | One-paragraph note from an actual mobile session. |
| 12 | Do operational links feel meaningful? | The phrase "evidence for" reads naturally to a field operator. | Vocabulary feedback from one field walkthrough. |
| 13 | Does chronology improve operational clarity? | A PM trying to remember "when did the FPL conflict start?" finds the answer in the sidecar in <10 s. | Time-to-answer measurement during a real reconstruction. |
| 14 | Does the platform still feel calm? | The sidecar does NOT demand attention — operators consciously CHOOSE to look at it. | Operator's own qualitative response. |
| 15 | Is operational trust increasing? | A PM says "I'd want this on my next job" without prompting. | Verbatim quote. |
| 16 | Any early drift toward dashboard chaos? | Nobody asks for charts, badges, or red counters on the sidecar. | Note any feature request that drifts this way. |
| 17 | Does the substrate feel invisible-but-valuable? | When asked "what's new?", PMs mention CONTENT (a conflict they tracked) — not the SURFACE (the sidecar itself). | Qualitative pattern note. |

---

## Field walkthrough scenarios (operator + 1 PM, recommended)

The directive lists eight real operational scenarios. Each is a chance
to surface chronology behavior. **The agent cannot execute these; they
require real operator time with the preview environment.**

| Scenario | Why it stresses the substrate |
|---|---|
| Utility conflict | Exercises owner field + chronology resolution flow + photo-evidence linkage. |
| FAA operational delay | Tests `kind=FAA-closure` + `severity=high` rendering + aging surfacing. |
| MOT sequencing issue | Tests cross-discipline conflict (operations + MOT) + chronology ordering. |
| Drainage issue | Tests `discipline=other` path + readability of free-text impact. |
| Survey discrepancy | Tests `kind=survey` + the chronology note append flow. |
| QC failure | Tests resolution chronology (re-roll · density verified) + close-out tone. |
| Owner delay | Tests responsible-party rendering + aging behavior over multi-day window. |
| Field conflict | Tests `discipline=subcontractor` + `kind=other` fallback path. |

A single PM walkthrough touching 3–4 of these (≤20 minutes) is enough
to surface every UX pain point worth catching pre-Wave-2.

---

## Capture template

When operator walkthroughs occur, append entries below this line in
the form:

```
### Walkthrough · YYYY-MM-DD · <operator initials>
Scenario(s): <which from the list above>
Device: <desktop | iPad | iPhone>
Time-to-comprehension: <seconds>
Verbatim quotes: <≤3 short lines>
Surface friction observed: <none | list>
Feature requests heard (calmness drift markers): <none | list>
Verdict: <calm | drifting | concerning>
```

---

## What this report is NOT

- ❌ A claim that operational trust has been validated. (It hasn't —
  validation requires operator presence.)
- ❌ A scoring rubric for PM behaviour.
- ❌ A reason to start Wave 2 prematurely.

It is a **scaffold for honest observation.**

---

— issued by E1 · V-Prelude Wave 1 observation posture · 2026-05-28

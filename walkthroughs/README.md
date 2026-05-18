# MASCI Operator-Flow Walkthroughs (iter217)

Lightweight, operational, **editorial-tool** walkthroughs of the platform
through each operational persona's actual day. **Not analytics. Not
telemetry.** No new collections, no engagement metrics, no dashboards.

Each walkthrough simulates a real persona's day, observes the
contextual coaching surface at each operational moment, and emits a
typed **findings** JSON that becomes the editorial refinement backlog
for the HelpTip engine.

## Why this exists

> "we need to validate real operational continuity, not just isolated
>  workflows or isolated UI surfaces."  
> — operator, 2026-05-18

The platform has 115 HelpTips across 19 form-key surfaces. That's
enough that isolated surface testing no longer measures workflow
continuity — only persona-driven simulation does.

## Personas (operator-stated priority)

| Order | Persona        | Viewport          | Status                          |
|-------|----------------|-------------------|---------------------------------|
| 1     | Foreman        | 414×896 mobile    | ✅ Fully scripted                |
| 2     | Superintendent | 768×1024 tablet   | ✅ Fully scripted                |
| 3     | Operator       | 414×896 mobile    | ✅ Fully scripted                |
| 4     | Dispatcher     | 1280×800 desktop  | ✅ Fully scripted                |
| 5     | HR             | 1280×800 desktop  | 🟡 Scaffolded (iter213 anchor)  |
| 6     | Safety         | 768×1024 tablet   | 🟡 Scaffolded                   |
| 7     | PM             | 1280×800 desktop  | 🟡 Scaffolded                   |
| 8     | Laborer/new    | 414×896 mobile    | ✅ Fully scripted (Day-1)        |

## Running a walkthrough

```bash
# One persona
PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python /app/walkthroughs/foreman.py

# All eight + aggregate the findings into the refinement backlog
for p in foreman superintendent operator dispatcher hr safety pm laborer; do
  PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python /app/walkthroughs/${p}.py
done
python /app/walkthroughs/aggregate_findings.py
```

Each run produces:
- `/app/walkthrough_reports/{persona}/{step-slug}.png` — step screenshots
- `/app/walkthrough_reports/{persona}_findings.json` — typed findings + step log
- `/app/walkthrough_reports/_backlog.json` (after aggregation) — prioritized actionable list

## Finding kinds (load-bearing vocabulary)

The framework enforces a finite vocabulary so the editorial backlog
stays legible across many runs. Defined in `_runner.FINDING_KINDS`:

- `no-escalation-path` · the persona faces a high-stakes moment with no coaching about when to stop / call up
- `voice-drift` · coaching landed but the tone is robotic / corporate / OSHA-manual
- `missing-coaching` · the surface needs a HelpTip block and has none
- `weak-tip` · a HelpTip is present but operationally shallow
- `unclear-wording` · words don't land for the persona (jargon, ambiguity, vague terms)
- `workflow-confusion` · the persona doesn't know what to do next
- `discoverability-gap` · the right surface exists but the persona can't see it from where they are
- `mobile-clipping` · text wraps awkwardly / body is too tall / thumb fatigue at 414px
- `friction` · catch-all for operational drag that doesn't fit elsewhere
- `positive-observation` · something is working well — captured so it isn't accidentally regressed

Adding a new kind requires updating both `_runner.FINDING_KINDS` AND
the smoke test (`backend/tests/test_iter217_walkthrough_smoke.py`).

## How to extend a scaffolded persona

1. Open the scaffolded file (e.g. `/app/walkthroughs/hr.py`)
2. Replace each `TODO` step body with real navigation + screenshot + finding-emission code
3. Run it: `PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python /app/walkthroughs/hr.py`
4. Re-run the aggregator
5. Review the new findings in `_backlog.json`

Don't add new fields, don't add new finding kinds without operator
approval, don't build a UI on top of this. It's an **editorial
artifact** — like a markdown changelog, just typed.

## Anti-patterns (do not introduce)

- ❌ A Mongo collection storing walkthrough runs
- ❌ A dashboard rendering walkthrough trends
- ❌ Automated "regression score" metrics over time
- ❌ Telemetry hooks emitting from the actual production app
- ❌ Generic UI-test-framework abstractions ("page object models")
- ❌ Asserting walkthroughs pass/fail in CI like unit tests (findings
  are observations, not pass/fail signals)

If any of those start to creep in, the walkthrough framework has
drifted from "editorial tool" toward "analytics system" — revert.

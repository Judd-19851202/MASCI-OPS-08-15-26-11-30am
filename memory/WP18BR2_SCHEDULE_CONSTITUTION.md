# WP18BR2 Schedule Constitution

Date: 2026-08-03

## Constitutional answer

**The existing schedule engine should be `Extend`, not rebuild.**

## Primary facts

1. A deterministic schedule engine already exists.
   - It derives schedule snapshots from assignments, progress, daily rows, and overrides.
   - Evidence: `backend/services/cost_codes/schedule_engine.py:211-540`.

2. Schedule truth is project-scoped and explainable.
   - The engine exposes baseline dates, forecast dates, committed dates, critical path, slack, source records, and explainability metadata.
   - Evidence: `backend/services/cost_codes/schedule_engine.py:431-540`.

3. Schedule overrides and planning lifecycle are already connected.
   - Forecast history, management overrides, publish actions, and weekly rollover all sit on the same path.
   - Evidence: `backend/services/cost_codes/foundation.py:693-709,730-909`; `backend/routes/cost_codes.py:760-920`.

4. Schedule depends on existing planning and production truths.
   - Upstream plan: `jobs_master.assigned_cost_codes`
   - Upstream actuals: `daily_reports.cost_code_quantities`
   - Evidence: `backend/services/cost_codes/foundation.py:658-675,1018-1037`.

## What survives challenge

| Challenge area | Constitutional answer |
|---|---|
| Is there already a real schedule engine? | Yes. |
| Should it be rebuilt? | No. |
| Does it already support project-level CPM-like sequencing and forecast lineage? | Yes, in bounded deterministic form. |
| Is enterprise master-schedule authority already proven? | No. |
| Are constraints/resources/equipment fully bound into the schedule constitution? | No. |

## Enterprise-scale challenge

### Strengths

- One schedule computation path already exists.
- Explainability and override lineage are stronger than a typical opaque schedule layer.
- The engine is already downstream of canonical planning and actuals instead of inventing its own store.

### Bounded conclusions

1. **Project schedule strength must not be over-claimed into enterprise master-schedule authority.**
2. **Constraint propagation into schedule is not yet constitutionally complete.**
3. **Enterprise-scale executive refresh is already latency-bounded, so synchronous portfolio scheduling must not be treated as solved.**
4. **Resource, crew, and equipment commitments remain adjacent federated domains, not fully schedule-owned truth.**

## Long-term technical debt risk if unchanged

| Risk | Why it matters |
|---|---|
| Overstating project schedule as enterprise master schedule | Creates future rework when multi-company portfolio governance arrives. |
| Adding new downstream schedule mirrors | Duplicates authority and weakens trust lines. |
| Ignoring constraint/resource federation gaps | Produces a schedule that looks cleaner than the operation really is. |
| Scaling synchronous portfolio recompute without redesign | Degrades executive trust as project count grows. |

## Alternatives considered

| Alternative | Result | Why rejected |
|---|---|---|
| Build a new schedule engine | Rejected | A real deterministic engine already exists. |
| Declare current schedule stack enterprise-complete | Rejected | Enterprise master-schedule authority and scale posture were not proven. |
| Treat executive dashboards as schedule truth | Rejected | Executive lanes are derived consumers only. |

## Final determination

- **Project schedule engine:** `Extend`

This avoids future rewrite **only if** future work preserves the existing deterministic engine while explicitly solving enterprise hierarchy, constraint propagation, and portfolio-scale refresh posture.
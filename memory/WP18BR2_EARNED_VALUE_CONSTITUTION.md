# WP18BR2 Earned Value Constitution

Date: 2026-08-03

## Constitutional answer

**Earned Value must be `Build New`, and it must come only after Budget Hierarchy exists.**

## Primary facts

1. The repository contains reusable upstream inputs for future EV.
   - project planning truth,
   - deterministic schedule truth,
   - field actual progress truth.
   - Evidence: `backend/routes/cost_codes.py:363-520`; `backend/services/cost_codes/schedule_engine.py:211-540`; `backend/services/cost_codes/foundation.py:658-675,922-946`.

2. No EV owner, formulas, APIs, or persistence engine were evidenced.
   - Prior challenge also failed to find EVM/CPI/SPI/planned-value/actual-cost architecture.
   - Evidence: `WP18BR_EXECUTIVE_RATIFICATION_REPORT.md:132-149`; `WP18B_PROJECT_CONTROLS_READINESS_AUDIT.md:196-200`.

3. Confidence scoring, recovery estimates, executive briefs, and schedule forecasts are not Earned Value.
   - They are adjacent analytical or operational consumers, not constitutional EV truth.

## Why EV cannot be inferred from what already exists

Earned Value requires at minimum:

- an authoritative budget baseline,
- rules for planned value,
- rules for earned value measurement,
- rules for actual cost lineage,
- enterprise rollups,
- and a trustworthy interpretation layer for CPI/SPI-like measures.

Those were not evidenced.

## Enterprise-scale challenge

At enterprise scale, fake EV is worse than no EV.

If EV were improvised today from partial schedule/progress/PO signals, the platform would create:

- misleading executive control metrics,
- untraceable finance disputes,
- and a likely future rewrite when a real budget constitution arrives.

## Alternatives considered

| Alternative | Result | Why rejected |
|---|---|---|
| Derive EV directly from current confidence or recovery metrics | Rejected | Those are not budget-grounded cost/schedule performance measures. |
| Derive EV from schedule and actuals without budget authority | Rejected | EV without budget is architecturally incomplete. |
| Claim EV is already present in hidden code | Rejected | No source evidence supported that claim. |

## Final determination

- **Earned Value:** `Build New`

This conclusion avoids future rewrite **only if** EV is sequenced strictly after Budget Hierarchy and remains a derived layer over reused planning, schedule, and actuals truth.
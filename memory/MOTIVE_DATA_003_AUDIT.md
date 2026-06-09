# MOTIVE-DATA-003 · Audit

**Date:** 2026-02-09
**Source:** `GET /api/admin/asset-mapping/operational-impact` against live preview backend.

## Live numbers

| Metric | Value | Note |
|---|---|---|
| Current Trust Score | **0%** | VER-1 derivation across active dispatches |
| Potential Trust Score | **79.3%** | Headroom if 219 unmapped trucks were mapped |
| HIGH Confidence Matches Waiting | **0** | Preview env has no scored HIGH proposals yet |
| Est. Dispatches Impacted | **0** | Tied to high_confidence_waiting=0 |
| Est. Assets Confirmed | **0** | == high_confidence_waiting |
| Coverage % | **0.0%** | 0 mapped / 219 dispatch trucks |
| Mapped Assets | **0** | Preview env lacks equipment_master twins |
| Unmapped Assets | **219** | All distinct dispatch trucks |
| Readiness Banner | **NOT_READY** | Coverage < 25% AND HIGH queue empty |

## Readiness verdict (per directive rules)

| Condition | Outcome |
|---|---|
| coverage_pct ≥ 75 AND high_waiting == 0 | READY_FOR_ACTIVATION |
| coverage_pct > 25 | PARTIALLY_READY |
| else | **NOT_READY** ← current state |

## Interpretation

The Operational Impact card immediately tells the operator:
1. **Not ready.** Coverage 0%.
2. **What's blocking us.** 219 unmapped trucks, 0 HIGH matches waiting (operator needs to first run `POST /admin/asset-mapping/scan` to score the dispatch fleet against the 190 Motive asset_mappings, then HIGH proposals will start appearing).
3. **What to fix first.** Top 10 table (already there from 002) shows `T-IT417` (24 active dispatches) as the biggest single-truck ROI.
4. **What happens if we fix it.** Projected State shows what coverage/trust/mapped would land at — currently identical to Current State because HIGH queue is empty.

This is the precise pre-Day-1 baseline. Once the operator runs the scan and approves HIGH matches, every metric on this card moves in real-time, providing an in-session compass during production cutover.

## Pillar scorecard

| Pillar | Score |
|---|---|
| Powerful | 🟢 4 operator questions answered above the fold |
| Simple | 🟢 1 endpoint · 1 card · 0 new collections |
| Beautiful | 🟢 Readiness banner · projected-state emerald accent |
| Trusted | 🟢 Honest 0% baseline · no inflated headroom |
| Proven | 🟢 80/80 combined Motive regression green |

## Constitutional checks (all passed)

- ✅ No new collection introduced
- ✅ No new workflow surface
- ✅ No mutation to `dispatch_assignments` / `asset_mappings` / `motive_events` / `daily_reports`
- ✅ No push to Motive (no `httpx`, no `motive_service` import)
- ✅ Readiness banner is read-only — never triggers automation
- ✅ Review HIGH button only scrolls + filters; never auto-approves

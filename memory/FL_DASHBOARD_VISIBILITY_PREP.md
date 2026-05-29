# FL Dashboard Visibility — Preparation Notes

_Phase V.2 · 2026-05-29 · planning only · no code changes._

> **Operator directive (verbatim):** _"Prepare role-based dashboard
> visibility rules. Do not overbuild."_

This document is a planning artifact. It does NOT alter any code, route, capability, or visibility rule today. Implementation requires a separate operator authorization.

## 1 · Canonical visibility ladder

| Surface | Leadman | Foreman | Superintendent | Sr. Superintendent | Admin |
|---|---|---|---|---|---|
| Assigned Daily Reports (own crew · today) | ✅ | ✅ | ✅ (project-level) | ✅ (multi-project) | ✅ |
| Crew / task entry | ✅ | ✅ | ✅ | ✅ | ✅ |
| Photos | ✅ | ✅ | ✅ | ✅ | ✅ |
| Delays / Extra Work | ✅ (own report) | ✅ (own report) | ✅ (project-level summary) | ✅ (multi-project summary) | ✅ |
| Safety observations | ✅ | ✅ | ✅ | ✅ | ✅ |
| Subcontractor entries | view-only | ✅ create/edit | ✅ review | ✅ review | ✅ |
| Submit Daily Reports | draft / assist (if authorized) | ✅ submit | ✅ submit + (future) approve/reject | ✅ submit + (future) approve/reject | ✅ |
| Production summaries | own report only | own report only | project rollup | cross-project rollup | full |
| Cross-project operational risk signals | ❌ | ❌ | project scope | ✅ assigned region / portfolio | ✅ |
| Approval / rejection of Daily Reports | ❌ | ❌ | (future · assigned projects) | (future · assigned region) | ✅ override |

## 2 · Implementation hooks (planned · NOT executed today)

| Hook | Plan |
|---|---|
| Frontend capability primitive | New `lib/fldashboardCapabilities.js` modeled after `poCapabilities.js` · driven by canonical `role_value` |
| Daily Report PDF audience hint | Same audience projector (M0.4) · no new audience codes |
| Backend visibility projector | Reuse existing `compute_pm_scope` pattern · add `compute_fl_scope(actor)` returning project list per role |
| Probe coverage | Authority Mismatch Probe baseline extended with `getFlDashboardCapabilities()` allowlist when implemented |
| Telemetry | Existing `odr_observation_events` doctrine — aggregate-only · never per-user |

## 3 · Forbidden combinations (must NEVER be true at runtime)

- Leadman seeing approval / rejection controls.
- Foreman seeing cross-project rollups.
- Superintendent seeing other projects' approval queues.
- Anyone but Admin overriding a Sr. Super rejection.
- Production / Delay summaries leaking subcontractor-internal PII to external audiences.

## 4 · What is NOT in scope today

- ❌ No code changes to portal hubs.
- ❌ No new routes.
- ❌ No new endpoints.
- ❌ No approval / rejection workflow.
- ❌ No PM Hub wiring of the PM Exposure Tile.

## 5 · Stop condition

🛑 This document is preparation only. Implementation begins only after operator authorization in a future directive.

_End of FL_DASHBOARD_VISIBILITY_PREP.md._

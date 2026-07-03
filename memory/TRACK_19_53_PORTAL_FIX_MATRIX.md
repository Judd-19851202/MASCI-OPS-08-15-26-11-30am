# TRACK 19.53 · Portal Fix Matrix

| P2 | Portal / Surface           | Route(s)                          | File touched                                | Change                                                     | testid                            | OI-powered |
|----|----------------------------|-----------------------------------|---------------------------------------------|------------------------------------------------------------|-----------------------------------|:---------:|
| 6  | Admin Mission Control      | `/admin`                          | `AdminHubV2.jsx`                            | OI strip (Corporate + Weekly Ops + Exec Brief) + V1 retired| `admin-hub-v2-oi-strip`           | ✅        |
| 7  | Dispatch Command Center    | `/dispatch-portal/command`        | `DispatchCommandCenter.jsx`                 | OI strip (`transportation_intelligence`)                   | `dcc-oi-strip`                    | ✅        |
| 8  | Field Leadership Dashboard | `/field-leadership/portal`        | `FieldLeadershipPortalDashboard.jsx`        | "Today's focus" banner (widget ordering)                   | `fl-portal-today-focus`           | N/A       |
| 10 | Asset Admin                | `/admin/asset-admin`              | `admin/AdminAssetAdmin.jsx`                 | OI strip (`fleet_intelligence`)                            | `asset-admin-oi-strip`            | ✅        |
| 11 | Superintendent Today Queue | same as #8                        | (covered by #8 edit)                        | Shared banner                                              | `fl-portal-today-focus`           | N/A       |
| 12 | Cockpit sparkline          | `/admin/operational-intelligence` | `admin/AdminOperationalIntelligence.jsx`    | Inline `TrendSparkline` next to score chip                 | `oi-trend-sparkline`              | ✅        |
| 9  | Guidance restructure       | `/guidance`                       | *(deferred)*                                | Deferred — LARGE scope · needs backend grouping            | —                                 | N/A       |

## Files modified (5)
- `/app/frontend/src/pages/AdminHubV2.jsx`
- `/app/frontend/src/pages/DispatchCommandCenter.jsx`
- `/app/frontend/src/pages/FieldLeadershipPortalDashboard.jsx`
- `/app/frontend/src/pages/admin/AdminAssetAdmin.jsx`
- `/app/frontend/src/pages/admin/AdminOperationalIntelligence.jsx`

## Files NOT modified
- Any backend module.
- Any OI engine file.
- Any product registry entry.
- Any new frontend component (shared `OiAttentionStrip.jsx` reused verbatim).
- Any route table entry.
- Any recipient / group / audit / history / score model file.

## Route swap verification (none needed)
- `/admin` continues to render `AdminHubV2` (Operations Control Center / Mission Control) — Track 19.28 baseline.
- `/dispatch-portal/command` continues to render `DispatchCommandCenter` — unchanged.
- `/admin/asset-admin` continues to render `AdminAssetAdmin` — unchanged.
- `/field-leadership/portal` continues to render `FieldLeadershipPortalDashboard` — unchanged.
- `/admin/operational-intelligence` continues to render the Cockpit — unchanged.

## Testid coverage
Every touched surface exposes at least one new stable `data-testid`. All prior testids on every touched file remain intact — no regression on Track 19.52 or earlier mount points.

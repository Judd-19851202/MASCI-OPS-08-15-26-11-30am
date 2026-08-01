# WP-17D Field Certification Register

Last updated: 2026-08-01

## Scope Rule
- This register tracks **rendered Field-family surfaces only**.
- Pure redirects and aliases that do not render their own UI are excluded from the denominator.
- A route is only marked **COMPLETE** when it passes all gates: Visual, Functional, English, Spanish, Responsive, Console/Network, Constitution Guard, and Anti-Drift.

## Current Denominator
- Total audited Field-family rendered routes: **32**
- Fully certified routes: **0**
- Reopened under Executive Amendment #5: **32**
- Remaining uncertified routes: **32**

## Gate Legend
- Visual: layout, governed primitives, no drift
- Functional: every interactive control exercised
- EN: English content check
- ES: Spanish content check
- Responsive: 390 / 430 / 768 / 1024 / 1440
- Console: no unexpected console/network defects
- Guard: Constitution + anti-drift checks

Status values: `REOPENED`, `IN_PROGRESS`, `COMPLETE`, `BLOCKED`

## Route Register

| Route | Surface Family | Visual | Functional | EN | ES | Responsive | Console | Guard | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/field` | Field landing | Pass (smoke) | Partial | Pass | Pass | Pass | Pass (smoke) | Pass | IN_PROGRESS | ES toggle locator repaired; 390/430/768/1024/1440 checks now pass. Full click-by-click certification still pending. |
| `/field/calculators` | Calculators landing | Pass (smoke) | Partial | Pass | Pass | Pass | Pass (smoke) | Pass | IN_PROGRESS | Shared shell padding + calculator mobile overflow repaired; 390/430/768/1024/1440 checks now pass. |
| `/daily/submit` | Daily Report create | Pass (smoke) | Partial | Pass | Pass | Pass | Pass (smoke) | Pass | IN_PROGRESS | Spanish banners, toasts, GPS/weather copy, and FormShell toggle IDs repaired. Full end-to-end submit recertification still pending. |
| `/equipment/new` | Equipment Pre-Op create | Pass (smoke) | Partial | Pass | Pass | Pass | Pass (smoke) | Pass | IN_PROGRESS | FormShell ES toggle repaired and major visible ES drift removed. Full camera/signature/submit recertification still pending. |
| `/equipment/submit` | Equipment Pre-Op public submit | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Same workflow family as `/equipment/new`, but must be independently certified. |
| `/fleet/dvir/new` | DVIR create | Pass (smoke) | Partial | Pass | Pass | Pass | Pass (smoke) | Pass | IN_PROGRESS | FormShell ES toggle repaired and visible DVIR Spanish drift removed. Full defect/signature/submit recertification still pending. |
| `/fleet/dvir/submit` | DVIR public submit | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Independent route certification required. |
| `/fleet/weekly-lead/new` | Weekly lead inspection | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Needs full route certification. |
| `/fleet/weekly-emergency/new` | Weekly emergency inspection | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Needs full route certification. |
| `/fleet/dvir/submitted/:id` | DVIR confirmation | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Needs ES and responsive certification. |
| `/shift` | Driver shift start | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Field-family operator start surface. |
| `/driver` | Driver active shift | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Must pass live control interaction checks. |
| `/d/:token` | Driver magic-link landing | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Independent route certification required. |
| `/leadership/login` | Field Leadership login | Pass (smoke) | Partial | Pass | Pass | Pass (390) | Pass | Pass | IN_PROGRESS | Successful FL login now lands on the governed dashboard instead of bouncing through legacy `/leadership`, removing interim console/auth drift during certification. |
| `/leadership` | Field Leadership landing | Pass (smoke) | Partial | Pass | Pass | Pass (390) | Pass (smoke) | Pass | IN_PROGRESS | Legacy Leadership subtitle + mission drift removed, notifications suppressed for this route family, and 390px view passes without overflow. Full route-family interaction pass still pending. |
| `/leadership/hub_v2` | Field Leadership companion | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Route exists and must be individually certified. |
| `/leadership/records` | Field Leadership list | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pass | REOPENED | Prior certification exists; ES and full control recertification pending. |
| `/leadership/records/:id` | Field Leadership detail | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pass | REOPENED | Detail surface must be recertified independently. |
| `/leadership/:kind/new` | Field Leadership create | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pass | REOPENED | Dynamic create surfaces still need full route-family recertification. |
| `/field-leadership/portal/login` | Field Leadership portal login | Pass (smoke) | Partial | Pass | Pass | Pass (390) | Pass | Pass | IN_PROGRESS | Independently verified route path now lands on the governed dashboard after FL login; no mobile overflow observed at 390px. |
| `/field-leadership/portal/change-password` | Field Leadership auth maintenance | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Included in Field-family auth scope. |
| `/field-leadership/portal/dashboard` | Field Leadership portal dashboard | Pass (smoke) | Partial | Pass | Pass | Pass (390) | Pass | Pass | IN_PROGRESS | ES dashboard copy repaired, mobile overflow removed, and workflow launchers 0-4 now route to working destinations (`/daily/submit`, `/meetings/submit`, `/jha`, `/equipment/submit`, `/incidents/report`). |
| `/field-leadership/portal` | Field Leadership portal root | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Separate route path; no inherited pass-through allowed. |
| `/field-leadership/portal/driver-qualification` | Field Leadership driver qualification | Pass (smoke) | Partial | Pass | Pass | Pass (390) | Pass (smoke) | Pass | IN_PROGRESS | ES subtitle/portal chrome repaired and 390px mobile layout passes without overflow. Wider-width recertification still pending. |
| `/admin/daily` | Admin daily list | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pass | REOPENED | Field workflow review surface. |
| `/admin/daily/:id` | Admin daily detail | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pass | REOPENED | Field workflow detail surface. |
| `/pm/daily` | PM daily list | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Needs full certification. |
| `/pm/daily/:id` | PM daily detail | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pending | REOPENED | Field workflow detail surface. |
| `/admin/equipment-inspections` | Admin equipment list | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pass | REOPENED | Field workflow review surface. |
| `/admin/equipment/:id` | Admin equipment detail | Prior evidence | Prior evidence | Prior evidence | Reopened | Prior evidence | Prior evidence | Pass | REOPENED | Field workflow detail surface. |
| `/pm/equipment` | PM equipment list | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Needs full certification. |
| `/pm/equipment/:id` | PM equipment detail | Reopened | Reopened | Reopened | Reopened | Reopened | Reopened | Pending | REOPENED | Needs full certification. |

## Current Blockers
- Remaining Field-family routes still need explicit route-by-route reopening, ES review, and full control exercising under Amendment #5.
- The legacy `/leadership` route family still needs its own console-safe recertification pass; the governed login/dashboard flow is now stabilized, but legacy Leadership surfaces remain reopened.

## Immediate Execution Focus
1. Reopen the remaining Field Leadership legacy routes (`/leadership`, `/leadership/records`, `/leadership/records/:id`, `/leadership/:kind/new`) and close their ES/console drift.
2. Certify the remaining crew-facing Field workflows (`/equipment/submit`, `/fleet/dvir/submit`, weekly inspections, `/shift`, `/driver`, `/d/:token`) with full interaction coverage.
3. Reopen Field review/detail surfaces (`/admin/daily`, `/admin/daily/:id`, `/pm/daily`, `/pm/daily/:id`, `/admin/equipment-inspections`, `/admin/equipment/:id`, `/pm/equipment`, `/pm/equipment/:id`).
4. Continue route-by-route until the Field denominator reaches zero uncertified surfaces.
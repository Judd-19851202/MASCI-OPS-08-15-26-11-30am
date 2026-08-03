# WP-18A PM Navigation and Entry Path Audit

Date: 2026-08-03

## Goal
Determine which PM project-controls surfaces have source-backed route and navigation evidence, and which are only implied.

## Confirmed routed surfaces
`frontend/src/app/routing/AppRoutes.jsx` contains exact route definitions for the following audited project-controls paths:

- `/pm/project-staffing`
- `/admin/project-staffing`
- `/pm/project-schedule`
- `/pm/monday-review`
- `/pm/command-center`
- `/constraints`
- `/daily/submit`
- `/daily-reports`
- `/pm/daily`
- `/admin/daily`
- `/pm/operational-intelligence`
- `/admin/operational-intelligence`
- `/admin/executive-operational-intelligence`
- `/admin/cost-registry`
- `/admin/project-identity`
- `/admin/jobs/:projectNumber/team`
- `/pm/job/:projectNumber/team`

## Sidebar and entry-map evidence

### PM sidebar domain map
- `frontend/src/components/pm/sidebar/domainMap.js` states it is sourced from `/app/memory/PM_INFORMATION_PRIORITY_MAP.json`.
- Its header comment states: **6 domains / 23 routes**.
- This is evidence of a deliberate PM information architecture map.

### Sidebar V2 default status
- `frontend/src/components/pm/sidebar/SideNavV2.jsx` states V2 is the default and can be disabled only by an escape hatch (`?pmSidebarV2=0`).
- Therefore the audited PM control surfaces should be treated as reachable through the modern sidebar model unless role gating or path-specific logic says otherwise.

## Entry-path observations by capability

| Capability | Source-backed PM/Admin route | Entry evidence | Notes |
| --- | --- | --- | --- |
| Staffing overview | `/pm/project-staffing`, `/admin/project-staffing` | Shared wrapper pages exist over `ProjectStaffingHub` | Reused consumer; strong reuse signal |
| Team roster | `/pm/job/:projectNumber/team`, `/admin/jobs/:projectNumber/team` | Exact route definitions present | Deep-link route existence is proven; runtime record proof is separate |
| Schedule workspace | `/pm/project-schedule` | Exact route + PM project selector consumer | Strong PM control entry surface |
| Monday review | `/pm/monday-review` | Exact route + page consumer + briefing actions | Strong workflow surface |
| PM command center | `/pm/command-center` | Exact route + command API helper | Existing PM operational cockpit |
| Constraints | `/constraints` | Exact route present | Cross-role/shared controls entry |
| Daily Reports | `/daily/submit`, `/daily-reports`, `/pm/daily`, `/admin/daily` | Exact route set present | Canonical field and review flows already split by role/context |
| PM ODS intelligence | `/pm/operational-intelligence` | Exact route and ODS consumer page | Connected dashboard surface |
| Admin operational intelligence | `/admin/operational-intelligence` | Exact route and legacy OI cockpit page | Distinct from ODS executive route |
| Executive operations/intelligence | `/admin/executive-operational-intelligence` | Exact route and executive intelligence page | Consumes OPPC + ODS data |
| Cost registry | `/admin/cost-registry` | Exact route present | Admin authority surface |
| Project identity governance | `/admin/project-identity` | Exact route present | Governance-only lane |

## Redirect / legacy evidence
- `AppRoutes.jsx` explicitly comments that `/daily-report/v2` redirects to `/daily/submit`.
- The retired shell remains on disk for legacy tests but is no longer the router’s canonical import path.
- This is direct evidence for consolidation rather than new-build work.

## Important non-findings
- Route existence alone does not prove a complete click-path for every role state.
- Shared naming between PM, Admin, and Executive surfaces does not prove they consume the same source-of-truth payloads.
- The audit did not rely on assumed sidebar labels; only file-backed route and component evidence was used.

## WP-18 implication
- PM navigation for core project-controls capability is already materially present.
- WP-18B should document and refine these entry paths rather than redesigning them from scratch.

## Executive conclusion
The PM project-controls navigation system is already structured and route-backed. The strongest next move is to align capability ownership and trust lines behind the existing entry paths, not to invent a new PM controls shell.
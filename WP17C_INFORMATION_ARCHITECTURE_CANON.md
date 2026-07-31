# WP-17C Information Architecture Canon

Source of truth: `WP17B_INFORMATION_ARCHITECTURE.md`, `WP17B_NAVIGATION_AUDIT.md`, `WP17B_EXECUTIVE_REPAIR_REGISTER.md`.

## Canonical IA rules
1. Navigation reflects real work, not feature history.
2. Every usable feature must be human-reachable by nav, search, or contextual entry.
3. Hidden routes require an intentional reason.
4. Detail routes inherit context from list/landing routes and stay out of primary nav.
5. Duplicate destinations with different labels are defects.
6. Redirect aliases stay temporary and explicitly documented.
7. Advanced/admin destinations must not crowd daily operator nav.

## Platform-wide route classes
- **Primary destinations:** Daily work surfaces directly visible in sidebar/header/mobile nav.
- **Secondary destinations:** Frequent supporting pages reachable from a portal domain section.
- **Advanced destinations:** Operationally useful but lower-frequency tools.
- **Administrative destinations:** Governance, maintenance, diagnostics, configuration.
- **Contextual destinations:** Detail routes, modals, drawers, task-specific follow-ups.
- **Search-only destinations:** Useful but not promoted to normal nav.
- **Hidden destinations:** Internal helpers, legacy variants, companion routes.
- **Deprecated aliases:** Redirect-only entry points scheduled for retirement.

## Canonical portal IA matrix
| Portal | Primary navigation | Secondary navigation | Advanced/admin | Contextual/search-only | Hidden/deprecated |
|---|---|---|---|---|---|
| Public & Shared | Sign-in, Guidance, public entry points | Cheat Sheet, company info | None | Session resume, public detail follow-up | Debug/internal public helpers |
| Admin OS | Admin OS domains, search, posture | Business operations shortcuts | Diagnostics, maintenance, recovery, governance | Detail pages, search-only admin items | Legacy imports, old aliases |
| PM | Action queues, jobs, daily, holds, command center | Cost, field coordination, document control | Reference/read-only views | Project/team/detail routes | Legacy PM variants |
| Shop | Recovery, queue, fleet, PM, service/support | Asset care | Asset-admin lane | Work-order/detail/history | Deprecated shop experiments |
| HR | People Ops, Time & Payroll, Compliance & Records | Guidance | Low-frequency forensic/admin support | Employee history/detail | Legacy HR-only helpers |
| Safety | Incidents, corrective actions, field records | Docs/training, compliance, reports | Audits and historical intake | Detail/export views | Admin-only safety leftovers |
| Dispatch | Live board, command, fleet/driver coordination | Guidance/support | Reporting/history | Board/detail views | Stale dead links already removed |
| Transportation | Grouped nav domains | Child tabs | Audit/reports/academy | Prefix-aware detail/context | Internal compare/index routes |
| Field Leadership | Portal, records, notifications | Accountability/support | HR-linked support | Record detail, recent notifications | Internal-only record helpers |
| Training & Guidance | Search, categories, start-here | Return-to-source links | Coverage/admin pages | Article detail | Internal certification routes |
| Driver | Current task flow | Recovery/help | None | Token-specific contextual detail | Token/internal helper routes |
| Executive | Overview, curated summaries | Curated reports | None | Drill-down links to owning portal | Experimental executive variants |
| Developer / Internal | None for normal users | None | Everything internal | Search-only | Hidden by default |

## Route ownership canon
- Admin owns governance, trust, configuration, diagnostics, and platform-wide maintenance.
- PM owns project execution review, project blockers, and PM-specific field coordination.
- Shop owns maintenance recovery and service execution.
- HR owns people lifecycle and payroll/time governance.
- Safety owns incidents, corrective actions, training compliance, and field safety records.
- Dispatch owns live transportation board operations.
- Transportation owns the dual-prefix trucking workspace canon.
- Guidance owns shared coaching content, not operational record ownership.

## Merge / retire rules
- `hub_v2`, `hub_legacy`, and internal comparison routes remain tracked in the ledger and are candidates for merge/retire in WP-17D.
- Detail routes remain mounted but are not promoted to top-level navigation.
- Deprecated aliases survive only while they still protect existing workflows.

## Reachability policy
Every mounted route must satisfy one of these reachability modes:
- visible navigation
- contextual link from a visible page
- search/command palette entry
- intentional hidden/internal classification documented in the ledger

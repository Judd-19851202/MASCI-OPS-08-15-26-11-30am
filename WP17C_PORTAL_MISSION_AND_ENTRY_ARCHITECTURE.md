# WP-17C Portal Mission & Entry Architecture

Source of truth: `WP17B_PLATFORM_MASTER_INVENTORY.md`, `WP17B_INFORMATION_ARCHITECTURE.md`, `WP17B_NAVIGATION_AUDIT.md`.

## Governing intent
Every portal landing must answer five questions in one scan:
1. Where am I?
2. What does this portal do?
3. What requires my attention?
4. What should I do next?
5. How do I reach the tool I need?

Portal landing pages are operational launchpads, not feature catalogs.

## Canonical portal missions

### 1. Public & Shared
- **Mission:** Safe front door for sign-in, guidance, and public/shared entry points.
- **Primary users:** Visitors, crews, new hires, public submitters, returning operators.
- **Top five jobs:** Sign in, resume a session, open shared guidance, open company help, start a public field flow.
- **Landing must show:** Workspace choices, session resume, start-here guidance, support/contact paths.
- **Primary actions:** `Sign in`, `Open workspace`, `Training Center`, `Cheat Sheet`.
- **Alerts:** Session available, access mismatch, offline/public-mode warnings.
- **Do not show:** Admin tools, verbose KPI walls, duplicate shell chrome.
- **Belongs in navigation:** Sign-in, guidance, public entry points.
- **Belongs under advanced/admin:** Nothing.
- **Should remain hidden:** Internal compare/debug routes and deprecated aliases.
- **Currently unreachable but should be tracked:** Any public helper only reachable by deep link.

### 2. Admin OS
- **Mission:** Govern the platform: health, trust, configuration, communications, access, and cross-portal oversight.
- **Primary users:** Super admins, governance operators, technical operations.
- **Top five jobs:** Check posture, search for a domain, investigate risk, open maintenance tools safely, export trust evidence.
- **Landing must show:** Overall posture, critical domains, next actions, search, domain ownership.
- **Primary actions:** `Search everything`, `Refresh`, `Export snapshot`, domain cards.
- **Alerts:** Critical probe failures, degraded integrations, communications gaps, governance drift.
- **Do not show:** Large detail tables above posture, duplicate navigation, destructive controls mixed into hero.
- **Belongs in navigation:** Admin OS domains first; business operations second; hidden detail via breadcrumbs/search.
- **Belongs under advanced/admin:** Diagnostics, maintenance, recovery, deploy readiness, integration detail.
- **Should remain hidden:** Detail pages, import/reconciliation utilities, low-frequency internals.
- **Currently unreachable but should be tracked:** Any mounted admin route missing from SideNav/search.

### 3. Project Management
- **Mission:** Help PMs build projects by surfacing attention, due work, and the shortest path to real queues.
- **Primary users:** Project managers, engineers, coordinators with PM access.
- **Top five jobs:** Review daily reports, handle incidents/CAPAs, clear blockers, watch project risk, act on PO/cost signals.
- **Landing must show:** Mission, action queues, due-today work, blockers, refresh time, obvious next actions.
- **Primary actions:** `Command Center`, `Jobs`, `Daily Reports`, `Holds`, `PO Requests`.
- **Alerts:** Open holds, due-today count, incidents pending, CAPAs due, QA/QC action.
- **Do not show:** Vanity metrics, duplicate cards, noisy tile walls.
- **Belongs in navigation:** Operations first, then cost/coordination, document control, risk/compliance.
- **Belongs under advanced/admin:** Read-only reference views and low-frequency diagnostic views.
- **Should remain hidden:** Detail routes and diagnostic variants.
- **Currently unreachable but should be tracked:** Any PM route only reachable by URL.

### 4. Shop Operations
- **Mission:** Keep fleet and equipment ready with clear recovery, PM, service, and readiness flows.
- **Primary users:** Shop managers, mechanics, service truck operators, asset admins.
- **Top five jobs:** Scan OOS units, route manager queue, open PM workload, create service records, monitor readiness.
- **Landing must show:** Recovery signal, manager queue, PM signal, active recovery, service backlog.
- **Primary actions:** `Manager Queue`, `Fleet Visibility`, `PM Dashboard`, `Service Records`.
- **Alerts:** OOS units, open defects, RTS pending, overdue PM work.
- **Do not show:** Admin governance content or unrelated enterprise metrics.
- **Belongs in navigation:** Recovery, assignments, fleet, PM, service/support, asset care.
- **Belongs under advanced/admin:** Asset-admin lane only for entitled users.
- **Should remain hidden:** Deep history/detail routes.
- **Currently unreachable but should be tracked:** Asset-admin flows still split across portals.

### 5. Human Resources
- **Mission:** Run the workforce lifecycle with clarity across employees, payroll/time, qualifications, and historical records.
- **Primary users:** HR staff, payroll coordinators, workforce admins.
- **Top five jobs:** Review employees, verify time/payroll, handle time off, check qualifications, process records.
- **Landing must show:** Workforce attention, pending approvals, expirations, the next people-work queue.
- **Primary actions:** `Employee Lifecycle`, `Accountability`, `Time Verification`, `Historical Records`.
- **Alerts:** Payroll variance, expiring documents, pending historical records.
- **Do not show:** Cross-portal noise not tied to people/workforce decisions.
- **Belongs in navigation:** People Ops, Time & Payroll, Compliance & Records, Guidance.
- **Belongs under advanced/admin:** Intake/queue tooling and low-frequency forensic views.
- **Should remain hidden:** Per-person detail histories and diagnostics.
- **Currently unreachable but should be tracked:** Any workforce workflow only reachable through Admin.

### 6. Safety Operations
- **Mission:** Surface incidents, corrective action, training, field records, and compliance before risk spreads.
- **Primary users:** Safety managers, auditors, trainers, compliance reviewers.
- **Top five jobs:** Open incidents, close corrective actions, review inspections/meetings/JHAs, watch expirations, open reports.
- **Landing must show:** Escalations first, field-record attention second, compliance risk third.
- **Primary actions:** `Incidents`, `Corrective Actions`, `Inspections`, `Reports`, `Weekly Digest`.
- **Alerts:** Active incidents, overdue CAPAs, expiring records, failed inspections.
- **Do not show:** Passive reference content before active safety work.
- **Belongs in navigation:** Incidents first; documents/training second; field records third; compliance fourth; guidance fifth.
- **Belongs under advanced/admin:** Reports, audits, historical intake.
- **Should remain hidden:** Detail routes and export variants.
- **Currently unreachable but should be tracked:** Safety routes still living only in Admin namespace.

### 7. Dispatch
- **Mission:** Run live transportation dispatch with clear board, command, fleet, and driver-readiness paths.
- **Primary users:** Dispatch operators, transportation coordinators, dispatch leads.
- **Top five jobs:** Scan haul board, open command center, review fleet visibility, verify qualifications, reach help fast.
- **Landing must show:** Live board, current escalations, command actions, fleet/driver readiness.
- **Primary actions:** `Haul Board`, `Dispatch Command`, `Fleet Visibility`.
- **Alerts:** Breakdowns, stale location risk, qualification issues, board exceptions.
- **Do not show:** Slow multi-step navigation or admin-style maintenance noise.
- **Belongs in navigation:** Live board, driver coordination, guidance/support.
- **Belongs under advanced/admin:** Reporting/history.
- **Should remain hidden:** Older lifecycle detail and low-value secondary boards.
- **Currently unreachable but should be tracked:** Any operational dispatch route not present in the canonical nav.

### 8. Transportation
- **Mission:** Establish one canonical IA across the dual-prefix transportation workspace.
- **Primary users:** Transportation managers, carrier/compliance operators, dispatch-adjacent users.
- **Top five jobs:** Open mission control, move through grouped nav, review people/compliance, use intelligence, reach reports.
- **Landing must show:** Mission control, grouped operations, intelligence/admin outputs, route-prefix clarity.
- **Primary actions:** Grouped nav destinations, shell-prefix switching.
- **Alerts:** Compliance lapses, dispatch queue issues, stale cleanup/intelligence work.
- **Do not show:** Competing duplicated nav structures with conflicting labels.
- **Belongs in navigation:** Grouped operations IA with shared child tabs.
- **Belongs under advanced/admin:** Audit, reports, academy, cleanup.
- **Should remain hidden:** Internal comparison/index helpers.
- **Currently unreachable but should be tracked:** Prefix-specific routes not mirrored correctly.

### 9. Field Leadership
- **Mission:** Support crew-level records, accountability, recognition, and follow-up.
- **Primary users:** Foremen, superintendents, field leadership staff.
- **Top five jobs:** Open records, review accountability items, manage documentation, handle follow-up requests, review notifications.
- **Landing must show:** Crew status, pending records, next documentation steps.
- **Primary actions:** `Portal`, `Records`, `Notifications`.
- **Alerts:** Pending documentation, follow-up required, employee-request activity.
- **Do not show:** Admin maintenance or enterprise system noise.
- **Belongs in navigation:** Portal dashboard, records, accountability, notifications.
- **Belongs under advanced/admin:** HR-linked supporting detail views.
- **Should remain hidden:** Internal APIs and record-detail helpers.
- **Currently unreachable but should be tracked:** Any field-leadership route only accessible from HR/Admin.

### 10. Training & Guidance
- **Mission:** Deliver the shared help system, guidance articles, and onboarding without portal clutter.
- **Primary users:** All operators, new hires, supervisors.
- **Top five jobs:** Search guidance, open role-based articles, start onboarding, use cheat sheets, return to the source portal.
- **Landing must show:** Role-based pathways, article search, start-here content, current article categories.
- **Primary actions:** `Search`, `Open article`, `Return to portal`.
- **Alerts:** Only time-sensitive guidance callouts.
- **Do not show:** Portal dashboards or operational KPI boards.
- **Belongs in navigation:** Search, categories, contextual return links.
- **Belongs under advanced/admin:** Coverage/admin certification pages.
- **Should remain hidden:** Coverage and internal certification routes.
- **Currently unreachable but should be tracked:** Articles missing from search or contextual help entry points.

### 11. Driver
- **Mission:** Provide focused token/self-service flows for drivers.
- **Primary users:** Drivers using invite or token-based workflows.
- **Top five jobs:** Start/continue driver flow, validate token, understand task identity, recover from invalid state, get help.
- **Landing must show:** The current task, next required action, recovery paths.
- **Primary actions:** `Continue`, `Start shift`, `Get help`.
- **Alerts:** Invalid/expired token, missing access, incomplete action.
- **Do not show:** Non-driver portals or management dashboards.
- **Belongs in navigation:** Minimal contextual task navigation only.
- **Belongs under advanced/admin:** None.
- **Should remain hidden:** Token detail routes.
- **Currently unreachable but should be tracked:** Recovery/help paths from expired token states.

### 12. Executive
- **Mission:** Give leadership concise posture, not a second Admin portal.
- **Primary users:** Executives, leadership viewers.
- **Top five jobs:** Open executive summary, scan posture, see high-signal KPIs, identify escalation owners, request follow-up detail.
- **Landing must show:** Summary posture, critical escalations, curated KPIs.
- **Primary actions:** `Open overview`, `Open curated reports`.
- **Alerts:** Only business-critical issues.
- **Do not show:** Operator queue clutter or maintenance tooling.
- **Belongs in navigation:** Overview plus curated report destinations.
- **Belongs under advanced/admin:** Deep detail stays in Admin/PM.
- **Should remain hidden:** Experimental executive views.
- **Currently unreachable but should be tracked:** Summary views without a clear drill-down owner.

### 13. Developer / Internal
- **Mission:** Keep internal-only testing surfaces isolated from operators.
- **Primary users:** Developers, QA, internal auditors.
- **Top five jobs:** Reach internal previews, validate internal flows, keep experiments isolated, avoid operator exposure, document risks.
- **Landing must show:** Minimal internal access only.
- **Primary actions:** Open internal login/preview surfaces.
- **Alerts:** Exposure risk, auth mismatch.
- **Do not show:** Production operator content.
- **Belongs in navigation:** Search-only/internal only.
- **Belongs under advanced/admin:** Everything here.
- **Should remain hidden:** All internal-only routes from operator nav.
- **Currently unreachable but should be tracked:** None should become public by accident.

## Entry architecture decisions
- Public entry stays distinct from authenticated portal shells.
- Admin and PM are the first representative landings under WP-17C.
- Transportation remains a governed special case because it uses dual path prefixes.
- Guidance remains cross-portal and must always provide a clear way back to the source portal.

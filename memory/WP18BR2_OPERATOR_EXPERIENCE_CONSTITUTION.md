# WP18BR2 Operator Experience Constitution

Date: 2026-08-03

## Constitutional answer

**Operator experience should be `Extend`, not rebuilt and not declared enterprise-complete.**

## Primary facts

1. The application already exposes a large role-based route and portal surface.
   - Evidence: `frontend/src/app/routing/AppRoutes.jsx:1-320`.

2. PM workflows have explicit project-controls paths.
   - Existing evidence already shows PM schedule, Monday review, daily-report, and intelligence routes.
   - Evidence: `frontend/src/app/routing/AppRoutes.jsx:127-165`; `WP18BR_PROJECT_CONTROLS_CONSTITUTIONAL_RATIFICATION.md:88`.

3. Field, safety, HR, shop, dispatch, executive, and admin portals already exist as distinct operational surfaces.
   - Evidence: `frontend/src/app/routing/AppRoutes.jsx:61-320`; `WP18BR_PROJECT_CONTROLS_CONSTITUTIONAL_RATIFICATION.md:89-99`.

## What the source evidence proves

- The platform is **not** missing operator surfaces.
- The platform is **not** a single-screen or single-role application.
- The platform already carries meaningful role specialization.

## What the source evidence does **not** prove

- that operators can still understand the workflow hierarchy at $500M+ enterprise scale,
- that multiple companies/divisions/service lines can be introduced without IA drift,
- that route abundance equals discoverability,
- or that finance-facing operators already have a ratified Project Controls operating system.

## Enterprise-scale reading by role

| Role family | Current architecture assessment | Enterprise-scale concern | Disposition |
|---|---|---|---|
| PM | Strongest project-controls discoverability evidence. | Naming and hierarchy may become overloaded as more divisions/service lines are added. | Extend |
| Field / Foreman / Superintendent | Strong daily-report and field-entry posture. | Resource/constraint/schedule context remains distributed across multiple surfaces. | Extend |
| Dispatch / Fleet / Shop | Strong operational specialization exists. | Cross-domain planning semantics remain federated rather than singular. | Extend |
| Safety / HR | Strong role-specific operational surfaces exist. | These roles remain adjacent to project-controls truth rather than full constitutional owners of it. | Extend |
| Executive | Executive visibility exists today. | KPI/ODS/Project Health/legacy overlap makes enterprise interpretation fragile. | Extend |
| Finance-facing roles | No final constitutional controls stack was evidenced. | Budget and EV absence blocks enterprise-ready operator architecture here. | Build New (for missing finance domains only) |

## What will create five-year UX debt if ignored?

1. Adding more portals and routes without a stricter enterprise workflow hierarchy.
2. Letting executive readers multiply without one reporting constitution.
3. Expanding finance-facing expectations before budget and EV owners exist.
4. Treating route existence as proof of operator trust and adoption.

## Alternatives considered

| Alternative | Result | Why rejected |
|---|---|---|
| Full operator UX rebuild | Rejected | Existing role surfaces are too substantial to justify broad replacement. |
| Declare current UX enterprise-complete | Rejected | Source evidence proves breadth, not final enterprise-scale intuitiveness. |
| Add more role surfaces before hierarchy cleanup | Rejected | That increases complexity faster than trust. |

## Final determination

- **Operator experience:** `Extend`

The platform already has meaningful role-based operating surfaces. The constitutional need is to sharpen hierarchy, naming, and executive/finance coherence before more scale is layered on top.
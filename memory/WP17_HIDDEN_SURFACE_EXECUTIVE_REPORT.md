# WP-17 Hidden Surface Executive Report

## Executive conclusion
WP-17 did not uncover one single hidden-route problem. It uncovered four different classes of hidden-surface accumulation: legitimate workflow-only detail routes, compatibility aliases and redirects, internal tooling / certification routes, and overlay-only interaction surfaces that had never been reconciled into one closing denominator.

The forensic closeout reconciles those classes without inventing counts:
- **1,190 → 1,193**: the historical WP17C baseline ledger carried 1,190 surfaces; WP17D later reconciled three live admin routes into the current full ledger (`/admin/leadership/records`, `/admin/platform-readiness`, `/admin/wp17d-certification`), producing the current **1,193-surface** master ledger.
- **484**: the current routed-object denominator is real and source-verified across five routed files (`AppRoutes.jsx`, `TransportationApp.jsx`, `_orientation.jsx`, `_intelligence.jsx`, `_command_queue.jsx`).
- **113**: the locked hidden/detail denominator is still valid. It equals every route surface currently in `DETAIL` or `HIDDEN` state except the one explicitly excluded hidden redirect alias `/admin/hub_v2`. The 26 hidden navigation nodes belong to the separate 253-node navigation denominator and were never supposed to be in the 113 total.
- **165**: once compatibility aliases/redirects are added back to the 113 route-hidden universe, the route-level non-primary denominator becomes **165**.
- **169**: adding the four admin-only internal readiness / validation routes that are not hidden by route type but are developer/certification tooling yields the complete route-level forensic denominator.
- **305**: adding the **136 overlay-only surfaces** from the master ledger yields the broad hidden-surface forensic denominator for this closeout.

## Why the ledgers diverged
1. `WP17C_IMPLEMENTATION_LEDGER.csv` is the earlier 1,190-row baseline. It is historically accurate, but not current after WP17D inventory expansion.
2. `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv` is the current 1,193-row surface ledger and is the authoritative denominator for present-day full-surface math.
3. `WP17D_PLATFORM_REACHABILITY_LEDGER.csv` is a route-only ledger. It remained accurate for route discovery at 484 rows, but it does not include overlays and it does not back-propagate every later forensic classification unless another ledger was updated.
4. `WP17D_FINAL_BLOCKER_REGISTER.md` truthfully recorded 16 final blockers. The route-only ledger still shows only the original 7 hard-blocked status codes because the later 9 runtime-data blocker dispositions were captured in the blocker register rather than written back into the route-status columns. That is a documentation drift issue, not a hidden product issue.
5. `WP17D_SURVIVOR_REGISTER.md` is explicitly dated 2026-08-02. Its pending counts are a historical snapshot from before the 2026-08-03 closure wave and must not be treated as the final route-classification state.

## What the hidden surfaces actually were
- **Legitimate workflow-only details / public-token links**: 70 surfaces. These are the dynamic record views, tokenized public links, and bounded continuity routes that should exist but should not be primary navigation items.
- **Legacy aliases, redirects, and replaced implementations**: 72 surfaces. These explain most of the duplicate or compatibility drift.
- **Developer / certification tooling**: 11 surfaces. These are the highest trust-risk items because they can expose internal terminology or readiness concepts if role scoping regresses.
- **Runtime-data / implementation blockers**: 16 route surfaces. These explain every remaining deep-link blocker without pretending the routes were certified.
- **Overlay-only surfaces**: 136 surfaces. These were never a route problem; they were an inventory-governance problem.

## Final blocker accounting
- **7 frozen Administration blockers** remain exactly as documented: `/admin/assets/:assetId`, `/admin/equipment/:id/history`, `/admin/employees/:id/history`, `/admin/equipment/:id`, `/admin/leadership/records/:id`, `/admin/safety/issuance/:id`, `/admin/safety/training/:id`.
- **9 runtime-data blockers** remain exactly as documented: `/pm/incidents/:id`, `/pm/meetings/:id`, `/pm/inspections/:id`, `/pm/equipment/:id`, `/hr/historical-records/batches/:batchId`, `/shop/units/:unitNumber/history`, `/shop/fuel-lube/:visitId`, `/shop/service-truck-reconciliation/:recId`, `/shop/equipment/:id`.
- The broad forensic register therefore records all 16 blocker surfaces without changing the accepted WP-17D closure fact that active-family actionable routes are already zero.

## Confidence statement
Confidence is high because the denominators now reconcile by scope instead of being forced into one number:
- route inventory = 484
- locked hidden/detail route denominator = 113
- route forensic denominator = 169
- overlay-only denominator = 136
- broad hidden-surface forensic denominator = 305
- current full audited-surface denominator = 1,193
- historical baseline denominator = 1,190

## Permanent prevention gate
The new route-governance gate is now source-enforced by `/app/scripts/wp17_route_governance_guard.py` and chained into `/app/scripts/wp17d_constitution_guard.py`.
It fails if any routed object is missing any of the following metadata in `/app/memory/WP17_ROUTE_GOVERNANCE_REGISTRY.csv`: owner, family, intended audience, entry path, navigation source, role requirements, intentionally hidden flag, hidden rationale, canonical relationship, EN/ES compliance state, responsive compliance state, and certification evidence.

## Delivered files
- `/app/memory/WP17_HIDDEN_SURFACE_FORENSIC_REGISTER.csv`
- `/app/memory/WP17_HIDDEN_SURFACE_EXECUTIVE_REPORT.md`
- `/app/memory/WP17_HIDDEN_SURFACE_FAMILY_SUMMARY.md`
- `/app/memory/WP17_ROUTE_GOVERNANCE_REGISTRY.csv`

## Inventory notes outside the denominator math
Source comments still reference some retained-on-disk legacy components used only for historical tests or rollback history. Those retained files were documented as source evidence in comments but were not counted in the route or overlay denominators unless they remained routed or inventoried as a formal surface in the ledgers.

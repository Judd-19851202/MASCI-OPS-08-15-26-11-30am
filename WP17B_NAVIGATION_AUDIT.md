# WP-17B Navigation Audit

## Authoritative Counts
- Navigation items audited: `253`
- Redirect routes audited: `54`
- Hidden/detail route surfaces audited: `113`
- Sidebar families audited: Admin V2, Admin V3, PM V2, HR V2, Safety V2, Dispatch V2, Shop V2, Transportation V2, Transportation sub-tabs, sign-in portal selector

## Findings by navigation family
| Family | Count | Finding | Disposition |
|---|---:|---|---|
| Admin V2 domain map | 43 | Operational grouping is useful but now secondary to Admin V3 | `MERGE` |
| Admin V3 domain map | 55 | Best candidate for canonical Admin IA, but still too broad per domain | `REFINE` |
| PM V2 | 30 | Consistent, calm, route-real, minimal drift | `KEEP` |
| HR V2 | 21 | Clear role grouping; needs standards around historical lanes | `REFINE` |
| Safety V2 | 22 | Strong task grouping; discoverability improved | `KEEP` |
| Dispatch V2 | 8 | Compact and role-true | `KEEP` |
| Shop V2 | 27 | Good task grouping; query-driven slices still dense | `REFINE` |
| Transportation grouped nav | 27 | Useful, but duplicated by sub-tabs and dual shells | `MERGE` |
| Transportation child tab sets | 13 | Valid interior navigation, but too many parallel navigational layers | `STANDARDIZE` |
| Sign-in portal links | 7 | Functional but structurally exposes org chart more than role outcomes | `REBUILD` |

## Navigation defects locked for WP-17C
1. Admin operates with competing navigation truths.
2. Companion hubs (`hub_v2`, `hub_legacy`) are not operator-safe as canonical destinations.
3. Redirect volume (`54`) is too high for a clean executive mental model.
4. Transportation has too many valid navigation surfaces for one domain.
5. Cross-portal “Training Center” and “Guidance” access are inconsistent.

## Canonical Navigation Standard
- One sidebar system per portal
- One command/search entry strategy per portal
- Redirects remain compatibility-only and should not appear in operator nav
- Hidden routes must remain searchable/indexed but not accidentally exposed
- Every navigation label must use the terminology standard in `WP17B_TERMINOLOGY_STANDARD.md`
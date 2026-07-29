# WP16 Coverage Register

Date: 2026-07-29

## Audit scope
This register reports coverage status for the restored `f97ab297` baseline. Coverage is evidence-based only. Unopened routes remain `NOT YET EXERCISED`; blocking runtime failures are recorded as `BLOCKED`.

## Totals
- Total discoverable route patterns inventoried: **480**
- `EXERCISED`: **14**
- `BLOCKED`: **2**
- `UNKNOWN`: **0**
- `NOT YET EXERCISED`: **464**

## Portal coverage summary

| Portal | Routes inventoried | Exercised | Blocked | Unknown | Not yet exercised | Evidence refs |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Admin | 141 | 3 | 0 | 0 | 138 | WP16-EVID-ADMIN-GOVERNANCE.jpeg, WP16-EVID-ADMIN-HOME.jpeg, WP16-EVID-ADMIN-LOGIN.jpeg |
| PM | 47 | 2 | 0 | 0 | 45 | WP16-EVID-PM-HOME.jpeg, WP16-EVID-PM-LOGIN.jpeg |
| HR | 32 | 1 | 2 | 0 | 29 | WP16-EVID-HR-EMPLOYEES.jpeg, WP16-EVID-HR-HOME.jpeg, WP16-EVID-HR-LOGIN.jpeg |
| Safety | 54 | 2 | 0 | 0 | 52 | WP16-EVID-SAFETY-HOME.jpeg, WP16-EVID-SAFETY-LOGIN.jpeg |
| Dispatch | 14 | 2 | 0 | 0 | 12 | WP16-EVID-DISPATCH-HOME.jpeg, WP16-EVID-DISPATCH-LOGIN.jpeg |
| Shop | 26 | 2 | 0 | 0 | 24 | WP16-EVID-SHOP-HOME.jpeg, WP16-EVID-SHOP-LOGIN.jpeg |
| Field Leadership | 12 | 0 | 0 | 0 | 12 | — |
| Training / Guidance | 8 | 0 | 0 | 0 | 8 | — |
| Transportation Ops wrapper | 3 | 0 | 0 | 0 | 3 | — |
| Driver | 3 | 0 | 0 | 0 | 3 | — |
| Executive | 3 | 0 | 0 | 0 | 3 | — |
| Dev | 2 | 0 | 0 | 0 | 2 | — |
| Public / Shared | 135 | 2 | 0 | 0 | 133 | WP16-EVID-PUBLIC-DAILY-FORM.jpeg, WP16-EVID-PUBLIC-HUB.jpeg |

## Exercised routes in this audit pass

- `/admin` — EXERCISED — opened successfully — `WP16-EVID-ADMIN-HOME.jpeg`
- `/admin/governance` — EXERCISED — opened successfully — `WP16-EVID-ADMIN-GOVERNANCE.jpeg`
- `/admin/login` — EXERCISED — opened successfully — `WP16-EVID-ADMIN-LOGIN.jpeg`
- `/pm` — EXERCISED — opened successfully — `WP16-EVID-PM-HOME.jpeg`
- `/pm/login` — EXERCISED — opened successfully — `WP16-EVID-PM-LOGIN.jpeg`
- `/hr` — BLOCKED — blocking runtime errors observed — `WP16-EVID-HR-HOME.jpeg`
- `/hr/employees` — BLOCKED — blocking runtime errors observed — `WP16-EVID-HR-EMPLOYEES.jpeg`
- `/hr/login` — EXERCISED — opened successfully — `WP16-EVID-HR-LOGIN.jpeg`
- `/safety-portal` — EXERCISED — opened successfully — `WP16-EVID-SAFETY-HOME.jpeg`
- `/safety-portal/login` — EXERCISED — opened successfully — `WP16-EVID-SAFETY-LOGIN.jpeg`
- `/dispatch-portal` — EXERCISED — opened successfully — `WP16-EVID-DISPATCH-HOME.jpeg`
- `/dispatch-portal/login` — EXERCISED — opened successfully — `WP16-EVID-DISPATCH-LOGIN.jpeg`
- `/shop` — EXERCISED — opened successfully — `WP16-EVID-SHOP-HOME.jpeg`
- `/shop/login` — EXERCISED — opened successfully — `WP16-EVID-SHOP-LOGIN.jpeg`
- `/` — EXERCISED — opened successfully — `WP16-EVID-PUBLIC-HUB.jpeg`
- `/daily/submit` — EXERCISED — opened successfully — `WP16-EVID-PUBLIC-DAILY-FORM.jpeg`

## Coverage gaps

- The inventory is complete at the route/source level, but most routes remain **not yet exercised in preview**.
- Mobile-specific verification has not been performed in this pass; every exercised screen is desktop-only evidence so far.
- Transportation child routes exist as nested screens inside the shared transportation shell; many remain inventoried-only.
- Dialog/drawer/sheet variants are inventoried from source but only shell-level evidence was captured in this pass.
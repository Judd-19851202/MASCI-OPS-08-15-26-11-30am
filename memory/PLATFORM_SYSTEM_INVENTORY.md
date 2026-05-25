# PLATFORM_SYSTEM_INVENTORY.md
**Phase 19 · iter415 · 2026-05-25**

Total operational surface area of the MASCI Operations Platform — every portal, page, workflow, system, form, guidance article, training surface.

## Top-level numbers
| Metric | Count |
|---|---:|
| Frontend `<Route>` registrations | 234 |
| Frontend page `.jsx` files | 166 |
| Backend `routes/*.py` modules | 57 |
| Backend API endpoints in `server.py` | 179 |
| MongoDB collections | 70+ |
| Guidance articles | 137 |
| Guidance article sections | 8 |
| i18n EN→ES keys | 3,012 |
| Backend tests | 291 |

## Portals (auth-distinct surfaces)
| Portal | Login URL | Token storage | Page count |
|---|---|---|---:|
| Admin Console | `/admin/login` (and `/sign-in` multi-login) | `masci.admin.token` | 26 |
| Dispatch Portal | `/dispatch-portal/login` | `masci.dispatch.token` | ~8 routes |
| PM Portal | `/pm/login` | `masci.pm.token` | ~27 routes |
| Shop Console | `/shop/login` | `masci.shop.token` | ~6 routes |
| Safety Portal | `/safety-portal/login` | `masci.safety.token` (X-Safety-Token) | ~30 routes |
| HR Portal | `/hr/login` | `masci.hr.token` (X-HR-Token) | ~20 routes |
| Field Leadership (legacy shared) | `/leadership` | `X-Leadership-Token` | n/a |
| Field Leadership Portal (per-user) | `/field-leadership/portal/login` | `masci.fl.token` (X-FL-Token) | ~6 routes |
| Safety Forms (legacy shared) | `/safety/forms/login` | `X-Safety-Forms-Token` | n/a |
| Developer Portal | `/dev/login` | `X-Dev-Token` (isolated) | n/a |
| Driver public entry | `/shift` (no auth · magic-link cookie) | session-only | 3 |
| Field public entry | `/field` (no auth) | n/a | 1 + child forms |
| Operational Guidance Center | `/guidance` (RBAC-aware) | inherits caller token | 1 |

## DLS surface area (Phase 12-18 work)
| Surface | Path | Owner | Auth |
|---|---|---|---|
| Dispatch Command Portal (iter411) | `/dispatch-portal` | Dispatch | required |
| Dispatch Board (iter392) | `/dispatch-portal/board` | Dispatch | required |
| Issue Work Drawer (iter407/408/410) | `/dispatch-portal/board` (modal) | Dispatch | required |
| Assignment Create Drawer | (same modal) | Dispatch | required |
| Driver Self-Start Shift (iter401/402) | `/shift` | Public | none |
| Driver Lifecycle Magic Link (iter393) | `/driver/shift?token=...` | Driver | magic-link |
| QR Shift Generator (iter406) | `/admin/dls/shift-qr` | Admin | required |
| PM Haul Activity Tile (iter409) | `/pm` (mounted tile) | PM | required |
| DispatchLifecycleTile (iter396) | PmHub · ShopHub · FieldLeadership (scoped) | scope-aware | required |
| Operational Attention (iter411) | DispatchHub section | Dispatch | required |
| DLS Health Summary (iter412) | `GET /api/admin/dls/health-summary` | Admin | required |
| Field Tile (iter319/403/404) | `/field` | Public | none |

## Public workflows (no-auth field operations)
- `/field` Field Tile (entry · 4 operational lanes)
- `/shift` Driver Self-Start
- `/driver/shift?token=...` Driver Lifecycle (magic-link · no portal login)
- `/inspect/new`, `/meetings/new`, `/incidents/new`, `/daily/new`, `/equipment/new` (public POSTs)
- `/cheatsheet` Printable foreman cheatsheet
- `/jha` Job Hazard Plans (read-only)
- `/trench-boxes` Trench Box fleet reference
- `/admin/dls/shift-qr` (auth · QR sticker output)

## Form workflows audited
| Form | Path | Auth | DLS-linked |
|---|---|---|:---:|
| Daily Report | `/daily/new` · `/daily/submit` | public submit · scoped read | indirect |
| Equipment Pre-Op | `/equipment/new` · `/equipment/submit` | public · shop sign-off | indirect |
| DVIR | `/fleet/dvir/new` | public · shop sign-off | indirect |
| Weekly Lead Inspection | `/fleet/weekly-lead/new` | public · FL+admin read | indirect |
| Weekly Emergency Equipment | `/fleet/weekly-emergency/new` | public · FL+admin read | indirect |
| Inspection | `/inspect/new` | public · safety read | — |
| Safety Meeting | `/meetings/new` | public · safety read | — |
| JHA | `/jha` · `/jha/new` | public · safety/PM | — |
| Incident | `/incidents/new` | public · safety+HR | — |
| QA/QC Inspection | (admin/PM) | scoped | — |
| Safety Equipment Issuance | `/safety/forms/*` | safety-forms | — |
| Safety Equipment Training | `/safety/forms/*` | safety-forms | — |
| Field Leadership Records (10 kinds) | `/leadership/{kind}/new` | leadership | — |

## Lifecycle/operational systems
- **Dispatch Lifecycle System (DLS)** — iter392 foundation · 5 haul types · canonical state machine · 70+ events stored append-only
- **Driver Sessions** — iter393 magic-link · iter401 self-start (synthetic driver_id) · iter402 platform-linked dropdowns
- **Governance Findings (DLS)** — iter395 stuck/wait/breakdown detector
- **Governance Findings (Safety)** — iter354 incident/CAPA-derived
- **Operational Memory** — recents from `dispatch_assignments` + `daily_reports` + masters; iter408 surfaces in lookups
- **Cross-portal tile system** — iter396 `DispatchLifecycleTile` with `scope` prop · iter409 `PmHaulActivityTile`
- **CAPA Lifecycle** — iter356 (Safety+Governance)
- **Employee Linkage** — iter355/363/364 (HR+Safety+FL cross-reference)
- **Driver Qualification** — iter317/352/353 (HR canonical · Dispatch consumer)

## Guidance article sections (137 total)
| Section | Count | Role-coverage notes |
|---|---:|---|
| portals | 49 | All 7 portals + multi-portal patterns |
| knowledge | 32 | "why this matters" + foundational doctrine |
| onboarding | 16 | New-user flows for each role |
| troubleshooting | 13 | Per-portal recovery paths |
| roles | 9 | Per-role canonical guides |
| trucking | 9 | Including 7 new DLS articles (iter414) |
| quickhelp | 8 | Task-based fast-lookup |
| reliability | 1 | Backups + data portability |

## Training surfaces
- **Safety Training Records** (`db.safety_training_records`) — per-employee, tied to track
- **Driver Qualification Dashboard** — HR canonical + Dispatch read-only consumer
- **Equipment Training** (`db.safety_forms.equipment_trainings`)
- **Guidance Center Articles** — coaching+training dual purpose, RBAC-aware
- **iter347 Promo Asset Library** — visual training assets

## Cross-portal tile mounting matrix (canonical)
| Portal | Tile(s) mounted | Source |
|---|---|---|
| `/dispatch-portal` | Operational Attention · Issue Work · Live Flow · Follow-Through · Secondary · Guides (7 sections) | iter411 |
| `/dispatch-portal/board` | DLS board · Assignment drawer · governance banner | iter392/iter395/iter407 |
| `/pm` | `PmHaulActivityTile` + `DispatchLifecycleTile` (scope=pm) | iter409/iter396 |
| `/shop` | `DispatchLifecycleTile` (scope=shop, BREAKDOWN) | iter396 |
| `/field-leadership/portal/dashboard` | `DispatchLifecycleTile` (scope=fl) + iter319 | iter396/iter319 |
| `/field` | Trucking Ops lane → `/shift` link | iter403/404 |
| `/safety-portal` | **NO DLS tile** (intentional restraint) | doctrine |
| `/hr/*` | **NO DLS tile** (intentional restraint) | doctrine |

## Verdict
The platform's operational surface area is **fully mapped**. No surface was excluded from Phase 19 audit. The 8 sibling deliverables drill into each axis: coaching · training · operational assumptions · legacy drift · downstream continuity · bilingual · cognition load · help-search · mobile · role flow · doctrine drift · remediation priority.

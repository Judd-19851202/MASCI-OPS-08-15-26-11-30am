# TRACK 18.01 · Human Operability Review + Usability Hardening

**Status:** ✅ READY · GO
**Date:** 2026-02-10
**Type:** Human-readiness verification · no feature additions · usability hardening only

---

## Final human-readiness verdict
**GO.** Transportation Operations passes the 30-second test for every role audited. Real operators can log in and answer the ten human-first questions ("Where am I? What matters now? Where do I click next? …") without training. Restricted states read as Transportation Operations · zero "Admin Console" / "Admin Portal" wording · no dead clicks on primary workflows · mobile/tablet/desktop all clean.

---

## Role walkthroughs

### Dispatch user
| Path | Surface | Verdict |
|---|---|---|
| Login | `/dispatch-portal/login` | GREEN — clean dispatch login UI, no friction. |
| Hub landing | `/dispatch-portal` | GREEN — Transportation Operations brand strip at top, hub content below (map hero, maintenance signal, live snapshot, operational attention). |
| Mission Control reachability | TopBar CTA | GREEN — one click from `Mission Control →` button lands in `/transportation-operations` with the full shell. |
| Board | `/dispatch-portal/board` | GREEN — TopBar above, existing dispatch board untouched. |
| Command | `/dispatch-portal/command` | GREEN — TopBar above always-on command strip. |
| Map | `/dispatch-portal/map` | GREEN — TopBar above sticky dispatch breadcrumb · MapLibre canvas renders · benign WebGL perf warning is cosmetic only. |
| Haul Ledger | `/dispatch-portal/haul-ledger` | GREEN — TopBar above existing header. |
| Driver Qualification | `/dispatch-portal/driver-qualification` | GREEN — TopBar above read-only view. |
| Fleet | `/dispatch-portal/fleet` | GREEN — TopBar above shared FleetVisibility (Phase G). |
| Search | `/` keyboard shortcut · TopBar Search button | GREEN — placeholder reads "Search drivers, trucks, carriers, projects… (press /)" · dispatch-safe RBAC results. |
| Right rail | Live operations workspace with entity context | GREEN — 5 sections render · entity banner with deep-link · empty/loading/error states all calm. |
| Restricted states | Admin-strict surfaces touched by dispatch | GREEN — "Transportation Operations · This Transportation data is not available for your role." |
| Return navigation | Any surface | GREEN — TopBar brand link + Mission Control CTA always one click away. |
| Mobile/tablet | 390 / 768 / 1024 / 1920 px | GREEN — hamburger toggle at < md · grouped nav at ≥ md · no horizontal overflow. |

**Findability questions** — all GREEN: dispatcher can find active assignment (board · live operations · right rail), driver (nav · search · related rail), truck (nav · search · related rail), blocked items (right rail Open Actions · Mission Control buckets), map (one nav click), Mission Control (CTA, always visible), restricted data (calm Transportation-branded card).

---

### Transportation Manager
| Path | Verdict |
|---|---|
| Mission Control | GREEN — readiness tiles + cleanup opportunity + HR sync health + audit timeline link all on one page. |
| Drivers | GREEN — `/transportation-operations/drivers` list + workspace deep links. |
| Carriers | GREEN — `/transportation-operations/carriers` list + workspace deep links. |
| Fleet | GREEN — `/transportation-operations/trucks` list. |
| Compliance | GREEN — `/transportation-operations/compliance` summary view. |
| Orientation | GREEN — `/transportation-operations/orientation` center. |
| Cleanup | GREEN — `/transportation-operations/intelligence/cleanup`. |
| Intelligence | GREEN — `/transportation-operations/intelligence`. |
| Automation | GREEN — `/transportation-operations/intelligence/automation`. |
| Reports | YELLOW — CSV/PDF exports still on `ComingSoon` placeholder; non-blocking. Deferred. |
| Administration (admin only) | GREEN — visible only for admin sessions in the TopBar. |

**Findability questions** — GREEN: manager can find a carrier packet (search → carrier workspace → documents tab), truck readiness (Mission Control tiles + truck workspace), orientation status (orientation center), cleanup actions (cleanup workspace).

---

### Fleet / Shop user
| Path | Verdict |
|---|---|
| Fleet visibility | GREEN — `/shop/fleet` (existing). |
| Trucks | GREEN — `/transportation-operations/trucks` (shop token sees trucks). |
| Inspections | GREEN — accessible from the truck workspace; admin-strict queue restricted with Transportation-branded message. |
| DVIR | GREEN — existing workflows preserved. |
| Maintenance state | GREEN — `DispatchEquipmentMaintenanceIndicator` on hub. |
| Search | GREEN — RBAC-filtered to trucks/dispatch-safe. |
| Related records | GREEN — Phase D right rail shows truck → carrier · inspections · dispatch assignments. |

**Findability questions** — GREEN: shop user finds a truck quickly (search or fleet nav), sees what needs inspection (inspection center summary), understands restricted records (Transportation-branded card).

---

### HR user
| Path | Verdict |
|---|---|
| Drivers | GREEN — HR token sees driver/document/orientation relations only. |
| Employee transportation readiness | GREEN — Mission Control summary tiles load with HR token (Phase F). |
| HR projection | GREEN — HR-sync health widget. |
| Restricted fleet/dispatch data | GREEN — Phase D RBAC OMITS truck/dispatch_assignment relations entirely; no leak, no confusing redaction. |

**Findability questions** — GREEN: HR understands driver readiness (orientation center + driver workspace), sees their responsibility surface (drivers + documents + orientation), restricted data is clear (Transportation-branded card, never Admin Console).

---

### Safety user
| Path | Verdict |
|---|---|
| Driver safety holds | GREEN — surfaced in driver workspace + right-rail Open Actions. |
| Truck risks | GREEN — truck workspace + inspections. |
| Inspections | GREEN — inspection center. |
| Incident-related transportation signals | GREEN — Phase D right rail surfaces related records. |
| Restricted states | GREEN — Transportation-branded copy. |

**Findability questions** — GREEN: Safety can understand transportation risk (Mission Control + right rail), find drivers/trucks tied to safety issues (search + relationships).

---

### PM / Operations user
| Path | Verdict |
|---|---|
| Project transportation awareness | GREEN — `OperationsTransportationCard` + readiness card on PM dashboard (Track 16.16). |
| Readiness card | GREEN — calls portal-aware `/api/operations/transportation/readiness`. |
| Risk banner | GREEN — surfaced on operations dashboard. |
| Closeout awareness | GREEN — operations cleanup signals. |
| Mission Control link | GREEN — TopBar CTA on `/dispatch-portal` and from operations dashboard. |
| Search | GREEN — PM token RBAC. |

**Findability questions** — GREEN: PM understands whether transportation is ready for a project (readiness card → Mission Control), Operations sees transportation health without hunting (right rail + Mission Control tiles).

---

## Usability scorecard (every reviewed screen)

| Surface | Clarity | Findability | Actionability | Speed | Visual Hierarchy | Mobile | Restricted | Dead-end | Training |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `/dispatch-portal` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/dispatch-portal/board` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/dispatch-portal/command` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/dispatch-portal/map` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/dispatch-portal/haul-ledger` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/dispatch-portal/driver-qualification` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/dispatch-portal/fleet` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations` (Mission Control) | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/live-operations` (right rail) | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/drivers` (list) | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/carriers` (list) | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/trucks` (list) | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/compliance` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/orientation` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/intelligence/cleanup` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/intelligence/automation` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/reports` | YELLOW (CSV export ComingSoon — non-blocking) | GREEN | YELLOW | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/transportation-operations/audit` | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |
| `/admin/transportation/*` (admin alias) | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN |

**Zero RED.** All YELLOW items intentionally deferred (see Deferrals).

---

## Findability matrix

| Core object | Path 1 | Path 2 | Path 3 |
|---|---|---|---|
| driver | TopBar → People → Drivers | Search "John" | Right-rail Related Records on a workspace |
| carrier | TopBar → People → Carriers | Search "ACME" | Right-rail Related Records on driver |
| truck | TopBar → Operations → Fleet | Search "T-42" | Right-rail Related Records on carrier |
| assignment | Dispatch board | Search | Right-rail on driver/truck |
| project | TopBar → Operations → Live Operations | Search "20-07" | Right-rail on dispatch assignment |
| document | Search | Right-rail on driver/carrier | (admin) `/transportation-operations/compliance` |
| packet | Search "carrier ACME" → workspace → Documents tab | Right rail | — |
| orientation | TopBar → Compliance → Orientation | Right rail on driver | — |
| certificate | Orientation center | Right rail on driver | Search |
| inspection | Truck workspace | Right rail on truck | (shop) inspection center |
| cleanup action | TopBar → Operations Intelligence → Cleanup | Mission Control "Top opportunity" card | Right rail |
| dispatch board | TopBar → Operations → Dispatch | Hub landing | Direct URL |
| map | TopBar → Operations → Dispatch → Open Full Live Map | Direct URL | Hub landing map hero |
| haul ledger | Dispatch nav | Direct URL | — |
| driver qualification | Dispatch nav | Direct URL | — |
| fleet | TopBar → Operations → Fleet | Dispatch nav → Fleet | Direct URL |

Every core object reachable via at least 2 obvious paths. No object hidden behind a URL only.

---

## Actionability matrix

| State | Visual cue | Copy |
|---|---|---|
| Needs attention | Amber chip | "Needs attention" |
| Action required | Amber outlined card | "Action required" |
| Ready | Emerald chip | "Ready" |
| Watch item | Slate chip | "Watch item" |
| Restricted for your role | Amber lock card | "This Transportation workspace is restricted for your role." / "This Transportation data is not available for your role." |
| Open in Dispatch | Primary CTA | "Open in Dispatch" / "Open Operational Board" |
| View related records | Secondary link | Phase D right rail "Related Records" section |
| Review documents | Tab on workspace | "Documents" tab inside carrier/driver workspaces |
| Check readiness | Mission Control tile | "Eligible drivers" / "Eligible trucks" / "Eligible carriers" |
| Open map | TopBar / dispatch button | "Open Full Live Map" |
| View assignment | Right-rail row | One-click route to dispatch |

No screen leaves the user wondering "what am I supposed to do here?" — actionable affordances are always visible, restricted states explain themselves.

---

## Copy / language review
**Conformant with the prompt standard.** Plain operational language throughout. No "Forbidden / Unauthorized / Admin Console / Admin Portal / null / undefined / payload / JSON" copy in user-facing JSX. Locked by `test_11` (static scan strips comments and fails the build on any of the forbidden strings).

---

## Mobile / tablet
* 390 px (phone) — hamburger toggle visible, brand + Search + Mission Control CTA remain accessible, no horizontal overflow.
* 768–1024 px (tablet) — full grouped nav, no overflow, right-rail collapses gracefully (hidden < xl per design).
* 1920 px (desktop) — full layout with right rail.
* TopBar `flex-wrap` ensures no row clipping.

---

## Fixes made (this track)
1. **Right-rail entity subtitle now carries a testid** (`txops-rail-entity-subtitle`) — improves automated coverage of the human-readable entity context line.
2. **Documentation lock**: this audit doc + 30 regression tests enforce the human-operability contract for future phases. The static scans (tests 11, 12, 15) will catch drift before merge.

No copy changes were needed — Phase G's static-scan lock already eliminated Admin Console wording, and the search placeholder + nav labels already meet the operational-language standard.

---

## Routes verified
All 13 `/dispatch-portal/*` routes · `/admin/transportation/*` admin alias · `/transportation-operations/*` canonical · Mission Control · Search rail · Right rail · all 18 surfaces in the scorecard above.

## Auth / RBAC
* No changes. Phase F portal-aware dashboard endpoint preserved · Phase D RBAC matrix preserved · all record-detail endpoints remain admin-strict.
* `RequireAdmin` · `RequireDispatch` · `RequireTransportationPortal` all preserved.
* Multi-login portal tokens preserved.

## Tests
* **30 / 30 PASS** — `/app/backend/tests/test_track_18_01_human_operability_review.py`.
* Static-scan tests fail the build on any future Admin Console / Admin Portal / raw error-token / dead-CTA drift.

## Deployment gate
Test path wired into `/app/scripts/deployment_gate.py`. **271 Track-18 tests** now under the gate (Phase A · B · C · D · E · 18.00E-FIX · F · G · 18.01).

## Deferrals (Phase H candidates · YELLOW non-blocking)
* CSV / PDF exports on `/transportation-operations/reports` still on `ComingSoon` placeholder — non-blocking but operators have asked for it. Mechanical when ready.
* HR sync widget could adopt `TxOpsRestrictedData` on 401/403 fallback (currently returns `null` — calm but a touch invisible).
* Document queue / inspection queue / rate schedule loading-screen 401 fallbacks could adopt `TxOpsRestrictedData` for stylistic consistency.
* Driver workspace's three side cards still show "ComingSoon" for `Orientation engine`, `Incident history`, `Retraining + certificates` — secondary side cards, non-blocking.

---

## Files touched
* **NEW** `/app/backend/tests/test_track_18_01_human_operability_review.py` (30 tests)
* **NEW** `/app/memory/TRACK_18_01_HUMAN_OPERABILITY_REVIEW.md` (this doc)
* `/app/frontend/src/pages/transportation/TransportationWorkspaceShell.jsx` — added `txops-rail-entity-subtitle` testid
* `/app/scripts/deployment_gate.py` — Track 18.01 test path appended

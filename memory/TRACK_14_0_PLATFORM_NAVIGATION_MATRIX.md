# MASCI Platform · Navigation Matrix (Track 14.0-PLATFORM-TRUTH-MAP)

**Audit date:** 2026-02-12 · **Mode:** READ-ONLY · **Scope:** every visible navigation element across every portal.

Companion to `TRACK_14_0_PLATFORM_TRUTH_MAP_ROUTE_NAV_SURFACE_INVENTORY.md` and `TRACK_14_0_PLATFORM_ROUTE_INVENTORY.json` (341 routes).

---

## 1 · Portal entry experience map

| Portal | Landing route | Shell component | Sidebar visible by default? | Notes |
|--------|----------------|------------------|:---------------------------:|-------|
| **Admin** | `/admin` → `AdminHub` (legacy) ; `/admin/hub_v2` → `AdminHubV2` | `AdminShell.jsx` (wraps 50+ admin pages) | ✅ YES (desktop) · hamburger sheet (mobile) | Baseline navigation pattern. Every admin page consistently shows the left sidebar via `AdminShell`. |
| **PM** | `/pm` → `PmHomeRedirect` → `/pm/hub` → `PmHubV2` | ❌ **NO SHELL** for the V2 hub. `PmShell.jsx` exists but is used only on **5 legacy pages** (`PmHub` legacy, `PmCrewCompliance`, `PmFieldLeadership`, `PmProjectDetail`, `PmSections`). | ❌ **NO SIDEBAR on PmHubV2 / PmCommandCenter / PmJobs / PmJobTeam** | **CRITICAL**: New PM landing has zero sidebar. PM users must rely on dashboard cards + Command Center to navigate. Legacy `PmShell` still has the blue sidebar (`hidden lg:block` on desktop ≥1024px) but is only reachable by clicking into a legacy page. |
| **Shop** | `/shop` → `ShopHubV2` | Similar V2 pattern (no consistent shell wrapping yet — `ShopHubV2` is hub-only). Most shop pages rely on hub-card navigation. | ❌ partial | Similar discoverability gap to PM, but smaller surface. |
| **HR** | `/hr` → `HrHubV2`; legacy `/hr/hub_legacy` | `HrPageShell.jsx` used on detail pages | ⚠️ inconsistent | Hub uses cards; detail pages use `HrPageShell` with sidebar. |
| **Safety Portal** | `/safety-portal` → `SafetyHubV2`; legacy `/safety-portal/hub_legacy` | `SafetyShell.jsx` for legacy; V2 uses card hub | ⚠️ inconsistent | Same V2-no-shell pattern. |
| **Field Leadership Portal** | `/field-leadership/portal` → `FieldLeadershipPortalDashboard` | FL has its own shell embedded in the page | partial | FL is most "single-page-dashboardy" — sidebar isn't expected by FL users. |
| **Dispatch Portal** | `/dispatch-portal` → `DispatchHub` ; `/dispatch-portal/hub_v2` → `DispatchHubV2` | Hub-card pattern + `DispatchSideNavV2` exists | ⚠️ inconsistent | Same V2-no-shell pattern. |
| **Dev / Internal** | `/dev` (gated) ; `/_internal/*` | DevHub | ✅ | 6 internal routes, properly gated behind RequireDevToken. |
| **Public** | `/` → `Hub` ; `/sign-in` → multi-portal login | n/a | n/a | 79 public routes — crew forms, training, public records (incidents, daily, JHA, trench, equipment, fleet DVIR, etc.). |

### PM landing — DOM-verified findings
- `/pm/command-center` renders `<PmCommandCenter>` directly. No `<PmShell>` wrap. **No left sidebar.**
- `/pm/jobs` renders `<PmJobs>` directly. **No left sidebar.** 28 active jobs visible with per-row Team link.
- `/pm/job/{n}/team` renders `<PmJobTeam>` which uses `PortalShell` (a different, lightweight shell). **No legacy PM sidebar.**
- `/pm/hub_legacy` and `/pm/projects-legacy/:n` use `<PmShell>` — these are the only PM surfaces with the blue sidebar.

### Hidden-sidebar root cause
- PM Portal V2 (`PmHubV2`, `PmCommandCenter`, `PmJobs`, `PmJobTeam`, `PmHolds`, `PmDueToday`, `PmCrewCompliance` etc.) **does not wrap content in PmShell**, so the desktop blue sidebar (`hidden lg:block w-64`) never renders.
- Only legacy `PmHub`, `PmFieldLeadership`, `PmProjectDetail`, `PmSections`, `PmCrewCompliance` import PmShell.
- Result: the PM "blue sidebar" only appears on 5 of the ~35 PM routes.

---

## 2 · Navigation element inventory (PM portal · full · Admin/others · matrix)

### PM Portal — visible navigation elements (after recent RC1 fixes)

| Element | Source page | Target route | Expected role | Status | Should remain? | Recommended action |
|---------|-------------|--------------|----------------|:------:|:--------------:|---------------------|
| PM Hub V2 dashboard cards (8 quadrants) | `/pm/hub` | varies (Holds, DueToday, Field Leadership, Fleet, People, etc.) | PM | ✅ OK | yes | — |
| "Project Roster" card | `/pm/command-center` (section D) | `/pm/jobs` | PM | ✅ FIXED 2026-02-12 (was `/admin/projects` → 404) | yes | — |
| ~~"Dispatch" header shortcut~~ | ~~`/pm/command-center`~~ | ~~`/dispatch-portal/command`~~ | ~~PM~~ | ✅ REMOVED 2026-02-12 | n/a | — |
| "PM Hub" back link | `/pm/command-center` | `/pm` | PM | ✅ OK | yes | — |
| PortalSwitcher | `PmShell` header (legacy pages only) | varies | PM/Admin | ⚠️ MISSING on `PmHubV2` family | — | **GAP**: V2 hub has no PortalSwitcher visible. |
| GlobalSearch | `PmShell` header (legacy only) | varies | PM/Admin | ⚠️ MISSING on `PmHubV2` family | — | **GAP**: V2 hub has no GlobalSearch. |
| NotificationBell | `PmShell` header (legacy only) | bell drawer | PM | ⚠️ MISSING on `PmHubV2` family | — | **GAP**: V2 hub has no NotificationBell. |
| Per-job "Team" link in `/pm/jobs` table | `PmJobsRead.jsx:172` | `/pm/job/{n}/team` | PM | ✅ OK · 28 instances | yes | — |
| "Pay & Margin" tile | `/pm/hub` | `/pm/pnl` (if exists) | PM | ⚠️ check | — | — |
| Mobile hamburger | `PmShell` header (legacy only) | sheet → `<SideNav>` | PM | ⚠️ MISSING on V2 hub family | — | **GAP**: mobile users on V2 hub have no menu. |

### Admin Portal — visible navigation elements (matrix · representative)

| Element | Source page | Target route | Status |
|---------|-------------|--------------|:------:|
| `AdminShell` left sidebar (12 sections, `domainMap.js`) | every admin page | each section's route | ✅ OK |
| Per-job Team link in `AdminJobMasterPanel` | `/admin/jobs` | `/admin/jobs/{n}/team` | ✅ OK |
| AdminHubV2 dashboard cards | `/admin/hub_v2` | varies | ✅ OK |
| NotificationBell · GlobalSearch · PortalSwitcher | AdminShell header | drawer/search/switch | ✅ OK |
| AdminPeople (`/admin/people`) | sidebar · "People" | user CRUD + temp-password | ✅ OK |

### Field Leadership Portal — matrix

| Element | Source page | Target route | Status |
|---------|-------------|--------------|:------:|
| FL Dashboard quadrants | `/field-leadership/portal` | varies | ✅ OK |
| Driver Qualification | `/field-leadership/portal/driver-qualification` | DQ list | ✅ OK |
| Field Leadership records (Phase 2B-1 widget) | embedded `MyAssignedProjectsWidget` | `/leadership/records/:id` | ✅ OK |
| Mobile menu / sidebar | none built | — | ⚠️ matrix-only |

### Safety / Shop / Dispatch / HR portals — matrix

- Each has a `*HubV2` card-based landing + a legacy `*Shell` with sidebar.
- V2 hubs have no consistent sidebar; legacy pages do.
- 6 unguarded admin routes (`/safety/cards`, `/field/calculators`, etc.) are **public-by-design** crew-facing surfaces — no guard expected.

---

## 3 · Broken path / dead-end matrix (post-Phase-2B-2B + RC1-FIX-SWEEP)

| Source | Target | Role tested | Failure type | Severity | Status | RC1 blocker? |
|--------|--------|-------------|---------------|----------|:------:|:------------:|
| ~~PM Command Center "Dispatch" link~~ | `/dispatch-portal/command` | PM | 403 (RequireDispatch fails) | High | ✅ FIXED 2026-02-12 | resolved |
| ~~PM "Project Roster" card~~ | `/admin/projects` | PM | 404 (admin-only) | High | ✅ FIXED 2026-02-12 | resolved |
| PM hub V2 no sidebar | n/a | PM | discoverability | High | ⚠️ OPEN | **YES — RC1-NAV-001** |
| PM hub V2 no NotificationBell / GlobalSearch / PortalSwitcher | n/a | PM | discoverability | High | ⚠️ OPEN | **YES — RC1-NAV-002** |
| Shop hub V2 same gap as PM | n/a | Shop | discoverability | Medium | ⚠️ OPEN | **YES — RC1-NAV-003** |
| HR hub V2 partial | n/a | HR | discoverability | Medium | ⚠️ OPEN | RC1-NAV-004 |
| Safety hub V2 partial | n/a | Safety | discoverability | Medium | ⚠️ OPEN | RC1-NAV-005 |
| Dispatch hub V2 partial | n/a | Dispatch | discoverability | Medium | ⚠️ OPEN | RC1-NAV-006 |
| 27 redirect routes (`/incidents`→`/admin/incidents` etc.) | varies | varies | redirect chain | Low | ✅ OK (intentional) | no |
| `/access-denied` | rendered for guard failure | varies | by design | n/a | ✅ OK | no |
| `*` → `NotFound` | unmatched URL | any | 404 page | n/a | ✅ OK | no |

**Known broken paths after fix sweep: 0.** **Known discoverability gaps: 6** (PM + 5 portal V2 hubs).

---

## 4 · Duplicate / legacy / conflicting experience map

| Group | Routes | Canonical (recommended) | Action |
|-------|--------|--------------------------|--------|
| PM Hub | `/pm/hub` (=V2) · `/pm/hub_legacy` (=PmHub) · `/pm/hub_v2` (=V2) | `/pm/hub` (= `PmHubV2`) | Retire `/pm/hub_legacy` after rolling V2 to 100%. |
| Admin Hub | `/admin` (=AdminHub legacy) · `/admin/hub_v2` (=V2) | `/admin/hub_v2` should be `/admin` | Future track: route `/admin` to V2. |
| Safety Hub | `/safety-portal` (=V2) · `/safety-portal/hub_legacy` · `/safety-portal/hub_v2` | `/safety-portal` | Retire legacy. |
| Shop Hub | `/shop` (=V2) · `/shop/hub_legacy` · `/shop/hub_v2` | `/shop` | Retire legacy. |
| HR Hub | `/hr` (=V2) · `/hr/hub_legacy` · `/hr/hub_v2` | `/hr` | Retire legacy. |
| Dispatch Hub | `/dispatch-portal` (=DispatchHub legacy!) · `/dispatch-portal/hub_legacy` (=DispatchHub) · `/dispatch-portal/hub_v2` (=DispatchHubV2) | **DISCREPANCY**: `/dispatch-portal` still serves legacy `DispatchHub`. Recommended: alias to V2. | Track. |
| QA/QC alias | `/qa-qc` → `/qaqc` | `/qaqc` | ✅ already redirected. |
| Trench Boxes alias | `/trench-boxes` → `/trench-safety/tabulated-data` | `/trench-safety/tabulated-data` | ✅ already redirected. |
| JHA alias | `/jha/submit` · `/jha/new` → `/jha` | `/jha` | ✅ already redirected. |
| Inspections alias | `/inspect/new` · `/submit` · `/inspections/submit` · `/inspections/new` → `InspectionLegacyRedirect` | `/safety/inspections/new` | ✅ legacy redirect helper. |
| Project Roster vs Team Management | `/admin/projects` (admin) · `/pm/jobs` (PM, post-fix) · `/admin/jobs/{n}/team` (admin team) · `/pm/job/{n}/team` (PM team) | `/admin/jobs/{n}/team` for admin · `/pm/job/{n}/team` for PM | ✅ post-fix consistent. |

---

## 5 · Portal navigation design plan (recommendation only · do not implement this track)

### PM portal
- **Recommendation**: V2 hub family (`PmHubV2`, `PmCommandCenter`, `PmJobs`, `PmJobTeam`) should adopt either `PmShell` or a new `PmShellV2` that wraps the V2 card hub. Sidebar should always be visible on desktop (lg:block), accessible via hamburger on mobile.
- **Required header items on every PM page**: NotificationBell, GlobalSearch, PortalSwitcher (if user has multiple portals), Change Password, Sign Out.
- **Sidebar**: keep the 8 `SECTIONS` from `PmShell.jsx:30-43`. Optionally promote "Jobs" and "Team" as first-class items.

### Admin portal
- Already follows the recommended pattern — keep as the platform baseline.

### Shop / HR / Safety / Dispatch portals
- Same problem as PM: V2 hubs need a sidebar shell.
- Each portal already has a `SideNavV2` component built (e.g., `safety/sidebar/SafetySideNavV2.jsx`, `hr/sidebar/HrSideNavV2.jsx`, `dispatch/sidebar/DispatchSideNavV2.jsx`) — they just aren't wrapped.

### Field Leadership portal
- FL is a single-purpose portal (dashboard + driver qualification + records). Sidebar not required if all entry points are visible from the dashboard.

### Public surface
- `/sign-in` is the canonical multi-portal entry. Keep as is.

---

## 6 · Discoverability score (representative · not exhaustive)

| Surface | Score (0–5) | Click-path from portal landing |
|---------|:-----------:|---------------------------------|
| Admin People (CRUD users + temp password) | **5** | `/admin` → "People" sidebar |
| Admin Job Team Management | **5** | `/admin` → "Jobs" sidebar → row → Team |
| Admin Audit Log | **4** | `/admin` → "Compliance" / Audit Log |
| Admin Sessions | **3** | `/admin` → sidebar (deep) |
| PM Project Team Management | **4** (post-fix) | `/pm` → Project Roster card → row → Team |
| PM Holds | **4** | `/pm` → Holds card |
| PM Due-Today | **4** | `/pm` → Due Today card |
| PM Field Leadership records | **3** | `/pm` → `MyAssignedProjectsWidget` deep link |
| PM "Project Roster" pre-fix (now fixed) | ~~0~~ | ~~404~~ |
| PM Command Center back-link to Hub | **5** | hub header |
| Shop Asset Care | **4** | `/shop` → Asset Care card |
| Safety Trench Hub | **4** | `/safety-portal` → Trench Safety card |
| HR Time-Off | **4** | `/hr` → Time-Off card |
| HR Driver Qualification | **3** | `/hr` → DQ card |
| Dispatch Board | **4** | `/dispatch-portal` → Board card |
| Dispatch Haul Ledger | **3** | `/dispatch-portal` → Haul Ledger |
| Operations Center Command | **2** | requires admin route knowledge (`/operations-center`) |
| Operational Records | **1** | route exists, no visible link |
| Operations Actions | **1** | route exists, no visible link |
| Asset Transfers (admin) | **2** | only deep-linked from notifications |
| PO Requests | **2** | no card found |
| Project Health | **2** | direct URL only |
| Constraints | **1** | direct URL only |
| Document Expirations | **1** | direct URL only |
| Tasks | **3** | bell drawer + direct URL |
| Operational Guidance Center | **2** | `/guidance` direct URL |
| Training Hub | **4** | `/training` from Hub |
| ODR Center | **2** | direct URL |

**~12 surfaces with discoverability ≤ 2.** Most are admin-internal (Project Health, Operational Records, Operations Actions, PO Requests, Constraints, Document Expirations) — they exist as routes but have no visible card/link from any hub. Documented as P2 (post-RC1).

---

## 7 · Notification destination map (representative families)

| Notification family | Producer | `link_url` pattern | Expected portal | Click-through status |
|----------------------|-----------|---------------------|-------------------|------------------------|
| Daily Report submitted | `auto_email` (DR has no bell producer · see Phase 2B-2B deferred list) | n/a | PM (email) | ⏳ defer to Phase 2C |
| Site Inspection deficiency | `safety.py · create_inspection` | n/a (no link_url set today) | Safety + PM | ⚠️ producer should add `link_url=/safety-portal/inspections/{id}` and `/pm/inspections/{id}` |
| Safety Meeting submitted | `safety.py · create_meeting` | n/a | Safety | ⚠️ same gap |
| JHA submitted | `safety.py · create_jha` | n/a | Safety | ⚠️ same gap |
| Incident created | `safety.py · create_incident` | n/a | Safety + PM | ⚠️ same gap |
| QA/QC deficiency | `qaqc.py` | n/a | PM + Safety | ⚠️ same gap |
| Pre-Op failed | `equipment.py` | `linked_equipment_id` | Shop + Dispatch | ⚠️ no explicit link_url |
| Asset Doc expired/expiring (D4) | `scheduled_producers_d456.py` | `/shop/asset-care` | Shop / Asset Admin | ✅ verified in D8 click-through audit |
| Field Leadership submitted | `field_leadership.py` | `/leadership/records/{id}` | FL · Safety · PM | ✅ verified |
| Trench reinspection | `trench_safety/excavations.py` | `linked_equipment_id` | Safety · Super | ⚠️ no explicit link_url (uses linked_equipment_id for context) |

**Concern raised in directive — "PM clicks incident notification and gets bounced/re-authenticated."** Status: **Not reproducible** in the Phase-2B-2B D8 click-through audit (OVERALL PASS), but the incident producer does not set `link_url` at all today, so the bell falls back to `/tasks` or `/notifications`, which is portal-agnostic and authenticated against the user's existing session. The "re-auth bounce" claim is **NOT a defect in producer routing** — it would only manifest if a PM clicked a deep link pointing at a Safety-Portal-only route. Recommended P1: each producer family sets a portal-specific `link_url` per recipient role.

---

## 8 · Invite / temp-password / user-access path map

| Portal | User-creation flow | Temp-password flow | Uniform? | Gap |
|--------|--------------------|---------------------|:--------:|-----|
| Admin | `/admin/people` → "Add User" | "Reset Password" mints + emails temp | ✅ canonical | — |
| PM | **no inline invite flow** — PM rosters an employee with `email` only; if the user lacks portal access, the roster row writes but routing silently skips them | n/a | ❌ | **RC1-INVITE-FLOW-001** — surface inline "Invite to portal" on `JobTeamRosterPanel` row |
| FL | Admin must use `/admin/people` | Admin mints | ✅ uniform | — |
| Safety | Admin must use `/admin/people` | Admin mints | ✅ uniform | — |
| HR | `/admin/people` or `/hr` user mgmt page if present | Admin mints | ✅ uniform | — |
| Shop | Admin must use `/admin/people` | Admin mints | ✅ uniform | — |
| Dispatch | Admin must use `/admin/people` | Admin mints | ✅ uniform | — |
| Asset Admin (opt-in role) | `/admin/people` user must be granted `X-Asset-Admin: 1` via Admin UI | n/a | ✅ uniform | — |

**Single canonical flow exists** (`/admin/people` admin temp-password mint). **Single gap**: PM-inline invite CTA on roster row (RC1-INVITE-FLOW-001). No duplicate invite systems found. No HR-only or PM-only temp-password back-channel.

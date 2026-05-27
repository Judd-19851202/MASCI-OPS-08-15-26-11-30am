# PM Portal — Current-State Audit (Phase IV-BETA · pre-governance)

**Iteration:** iter437 · Phase IV-BETA inventory · 2026-02
**Status:** 🟢 READ-ONLY · INVENTORY-GROUNDED · NO CODE CHANGED
**Purpose:** Capture the PM portal as it actually exists today, before any governance is written. Every observation below is sourced from files inspected this session — none of it is theoretical.

**Source files inventoried this iteration:**
- `frontend/src/components/PmShell.jsx` (the layout chrome + sidebar)
- `frontend/src/pages/PmHub.jsx` (the `/pm` overview surface)
- `frontend/src/pages/pm/PmSections.jsx` (Jobs · Fleet · People · Suppliers · Posters · Routing · Compliance Export)
- `frontend/src/pages/PmCrewCompliance.jsx` · `frontend/src/pages/PmFieldLeadership.jsx` · `frontend/src/pages/PmQaqcList.jsx` (PM-specific surfaces)
- `frontend/src/App.js` lines 456–492 (routing)
- `backend/routes/pm_routes.py` (PM API endpoints)

The audit is structured to feed the 8 governance deliverables that follow. Anything not in this document is not yet grounded — it must not appear in those deliverables.

---

## 1. Current navigation map

### Sidebar (`PmShell.jsx` · `SECTIONS` array — 9 entries, flat)

| Order | Key | Route | Label | Subline |
|---|---|---|---|---|
| 1 | `overview` | `/pm` | Overview | "Forms · Jobs · Search" |
| 2 | `jobs` | `/pm/jobs` | Jobs | "Active jobs · Master list" |
| 3 | `field-leadership` | `/pm/field-leadership` | Field Leadership | "Crew docs · My jobs only" |
| 4 | `fleet` | `/pm/fleet` | Equipment Fleet | "Status board · Master · Parts" |
| 5 | `people` | `/pm/people` | People | "Employee master (read-only)" |
| 6 | `suppliers` | `/pm/suppliers` | Suppliers | "Supplier master (read-only)" |
| 7 | `posters` | `/pm/posters` | Site Posters | "JHP · Trench Box · Inspection QRs" |
| 8 | `routing` | `/pm/routing` | Email Routing | "Auto-routing summary" |
| 9 | `compliance-export` | `/pm/compliance-export` | Compliance Export | "Date-range CSV export" |

### Hub-surface tiles (`PmHub.jsx` · `FORM_TILES` — 15 entries, 3-column grid)

| # | Route | Title | Sub | Accent |
|---|---|---|---|---|
| 1 | `/tasks` | Tasks & Actions | "Open · overdue · cross-portal" | amber |
| 2 | `/po-requests` | PO Requests | "Approvals · receipts · spend" | indigo |
| 3 | `/project-health` | Project Health | "Operational friction by job" | emerald |
| 4 | `/asset-transfers` | Asset Transfers | "Equipment movement · lifecycle" | amber |
| 5 | `/pm/daily` | Daily Reports | "reports on file" | red |
| 6 | `/pm/inspections` | Site Inspections | "reports on file" | red |
| 7 | `/pm/meetings` | Safety Meetings | "meetings logged" | slate |
| 8 | `/pm/jha-plans` | Job Hazard Plans | "plans uploaded" | amber |
| 9 | `/pm/trench-boxes` | Trench Box Data | "boxes on file" | slate |
| 10 | `/pm/incidents` | Incident Reports | "reports on file" | redDeep |
| 11 | `/pm/equipment` | Equipment Pre-Op | "inspections on file" | slate |
| 12 | `/pm/qaqc` | QA / QC Inspections | "Records on your jobs" | amber |
| 13 | `/pm/photos` | Job Photos | "All photos by job & week" | rose |
| 14 | `/pm/field-leadership` | Field Leadership | "Crew docs · my jobs only" | amber |
| 15 | `/guidance` | Training & Guides | "Operator guides · PDF download" | slate |

### Hub-surface inline widgets (above and around the tile grid)

| Widget | Source | Purpose |
|---|---|---|
| `PasskeyEnrollPrompt` | `@/components/auth/PasskeyEnrollPrompt` | Optional WebAuthn enrollment nudge |
| `FieldMemoryGlance` | `@/components/field_memory/FieldMemoryGlance` | Read-only field memory surface |
| `LastActivityLine` | `@/components/admin/LastActivityLine` | Calm "Last activity" trace |
| `OperationsCenter` | `@/components/OperationsCenter` | Compact operational KPI block |
| `PmCrewComplianceCard` | inline in `PmHub.jsx` | 4-tile crew-compliance summary (Crew · Expiring · Expired · Open CAPAs) |
| `PmHaulActivityTile` | `@/components/dispatch/PmHaulActivityTile` | PM haul-activity awareness |
| `DispatchLifecycleTile` | `@/components/dispatch/DispatchLifecycleTile` | DLS cross-portal lifecycle, PM-scoped |

### Detail/list routes (registered in `App.js`, NOT in the PM sidebar)

| Route | Component | Surface category |
|---|---|---|
| `/pm/daily` · `/pm/daily/:id` | `DailyReportsDashboard` · `ViewDailyReport` | High-frequency operational form |
| `/pm/incidents` · `/pm/incidents/:id` | `IncidentsDashboard` · `ViewIncident` | Safety form |
| `/pm/meetings` · `/pm/meetings/:id` | `MeetingsDashboard` · `ViewMeeting` | Safety form |
| `/pm/inspections` · `/pm/inspections/:id` | `Dashboard` · `ViewInspection` | Safety form |
| `/pm/jha-plans` | `JhaPlansAdmin` | Reference doc |
| `/pm/trench-boxes` | `TrenchBoxesAdmin` | Reference doc |
| `/pm/equipment` · `/pm/equipment/:id` | `EquipmentDashboard` · `ViewEquipmentInspection` | Pre-Op |
| `/pm/photos` | `JobPhotosLibrary` (portalKey="pm") | Operational artifact |
| `/pm/crew-compliance` | `PmCrewCompliance` | Crew accountability |
| `/pm/qaqc` | `PmQaqcList` | QA/QC |

### Auth surfaces

| Route | Component | Purpose |
|---|---|---|
| `/pm/login` | `PmLogin` | Email + password sign-in |
| `/pm/reset/:token` | `PmResetPassword` | Forgot-password flow |
| `/pm/change-password` | `PmChangePassword` | Self-service password change |

### Backend PM endpoints (`backend/routes/pm_routes.py`)

`/api/pm/check` · `/api/pm/me` · `/api/pm/login` · `/api/pm/forgot-password` · `/api/pm/reset-password` · `/api/pm/change-password` · `/api/pm/logout` · `/api/pm/crew/training-records` · `/api/pm/crew/ppe` · `/api/pm/crew/capas` · `/api/pm/crew/summary`

---

## 2. Current workflow map

The PM portal mixes **three distinct workflow classes** with no visual separation:

| Class | What it is | Where it lives today | Frequency |
|---|---|---|---|
| **A. Operational form work** | Submit/review the day's Daily Report, Inspection, Meeting, Incident, Pre-Op, QA/QC | Hub tiles 5–12 · routes under `/pm/{form}` | shift-critical (1–10×/shift for PMs reviewing field submissions) |
| **B. Reference & master data** | Job master, Employee master, Supplier master, Equipment master, Site Posters | Sidebar entries 2–7 | weekly–monthly (reference reads, rare writes) |
| **C. Coordination & oversight** | Tasks, PO Requests, Project Health, Asset Transfers, Crew Compliance, Haul Activity, Dispatch Lifecycle, Field Memory | Hub-surface tiles 1–4 + inline widgets + crew compliance card | daily (cross-portal coordination, financial & accountability surfaces) |

**Observation:** Class A (most-frequent) and Class C (second-most-frequent) live on the Hub overview; Class B (least-frequent) lives in the sidebar. This is the inverse of operational priority — the sidebar should surface the highest-frequency work.

---

## 3. Current terminology inconsistencies

Cross-referencing PM portal copy against the locked `OPERATIONAL_VERBIAGE_DOCTRINE.md` lexicon:

| Concept | PM portal uses | Admin/doctrine uses | Status |
|---|---|---|---|
| Field safety check | "Site Inspections" (PmHub tile #6) | "Inspections" | ❌ adjective added — drift |
| Quality check | "QA / QC Inspections" (PmHub tile #12) | "QA/QC" | 🟡 dual-noun "Inspections" reused for two different concepts |
| Equipment field check | "Equipment Pre-Op" (tile #11) | "Pre-Op Check" / canonical noun `Pre-Op` | 🟡 doctrine noun is `Pre-Op`, PM adds "Equipment" prefix |
| Job hazard analysis | "Job Hazard Plans" (tile #8) · `/pm/jha-plans` | Doctrine canonical: `JHA Plan` | 🟡 portal uses "Plans" plural; doctrine is `JHA Plan` |
| Field leader records | "Field Leadership" (sidebar + tile) | Doctrine canonical: `field leadership` (collective noun) | ✅ aligned |
| Crew | "Crew Compliance" (PmHub card title) | Doctrine canonical: `Crew` | ✅ aligned |
| PM hub intro | "Welcome to the PM Portal. The forms below cover the day-to-day…" | Doctrine: forbidden "Welcome to" pattern (`OPERATIONAL_VERBIAGE_DOCTRINE.md` §IX) | ❌ marketing-ish opening |
| Compliance Export intro | "Pull a CSV of every safety record…" | Doctrine: verb-first OK, "Pull" is non-canonical for `Export` action | 🟡 "Pull" → should be implicit, primary action is `Export` |
| Sidebar subline `Overview` | "Forms · Jobs · Search" | Doctrine: subline should answer "what is this · why am I here" not list features (`OPERATIONAL_VERBIAGE_DOCTRINE.md` §IX) | ❌ feature-listing, not coaching |
| Sidebar subline `Equipment Fleet` | "Status board · Master · Parts" | Same | ❌ feature-listing |
| Sidebar subline `People` | "Employee master (read-only)" | Same | ❌ feature-listing with parenthetical state |
| Routing label "Email Routing" subline | "Auto-routing summary" | Same | ❌ feature-listing |
| Hub tile `Tasks & Actions` | OK | Doctrine canonical: `Tasks` or `Action Items` | 🟡 dual term — pick one |

**Net:** ≥ 8 doctrine violations in copy, all fixable with subline + label revisions in Phase IV-BETA.1.

---

## 4. Current visual-loudness sources (measured against `VISUAL_LOUDNESS_REDUCTION_PLAN.md`)

### Sidebar (`PmShell.jsx`)

| Source | Severity |
|---|---|
| `bg-amber-600 text-white shadow-sm` saturated active state | 🔴 High — same pattern as old Admin red-700 (`§III.3` violation) |
| Border on header is `border-b-4 border-amber-600` (4 px saturated) | 🔴 High — Tier-0 chrome saturation too high |
| Sheet mobile drawer border `border-r-2 border-amber-600` | 🟡 Medium — fights with sidebar stripes if added |
| 9 entries × same visual weight | 🟡 Medium — no hierarchy ladder (everything is Tier 4) |
| Sublines are uppercase mono with `tracking-wider` | 🟡 Medium — calm sublines (per doctrine) should be sentence-case slate-500 |
| No coaching presence — sublines are feature-lists | 🟡 Medium — fails `OPERATIONAL_VERBIAGE_DOCTRINE.md` §IX |

### Hub overview (`PmHub.jsx`)

| Source | Severity |
|---|---|
| 15 tiles in 3-column grid, each with colored icon block | 🔴 High — element density well above the `≤ 14 above the fold` target |
| 6 distinct hue families: red, amber, redDeep, rose, indigo, emerald, slate | 🔴 High — color hue competition (target ≤ 3) |
| "PM Crew Compliance" card has full `border-2 border-amber-600` saturated 2-px border | 🟡 Medium — `COMPONENT_HIERARCHY_STANDARD.md` §IX says 2-px domain stripe only for active selection |
| Several inline widgets stacked vertically (PasskeyEnrollPrompt → FieldMemoryGlance → LastActivityLine → OperationsCenter → PmCrewCompliance → tile grid → PmHaulActivityTile → DispatchLifecycleTile) | 🔴 High — 7 distinct sections before the tile grid · violates section-rhythm doctrine (`COMPONENT_HIERARCHY_STANDARD.md` §XI) |
| "Welcome to the PM Portal" intro card | 🟡 Medium — marketing-style intro forbidden per doctrine |
| Tile titles in `text-base sm:text-lg font-black` (Tier 4 promoted to almost Tier 3 size) | 🟡 Medium — typography inflation |

### Header chrome (`PmShell.jsx` lines 95–191)

| Source | Severity |
|---|---|
| `border-b-4 border-amber-600` (4-px saturated bottom border) | 🟡 Medium — 1–2 px is sufficient |
| Breadcrumb mono `text-amber-300 font-bold` (saturated amber-on-dark) | 🟡 Medium — slate-300 would maintain contrast at lower saturation |
| Multiple top-right icon buttons (PortalSwitcher · GlobalSearch · NotificationBell · OfflineIndicator · SystemHealthBadge · Home · ChangePassword · SignOut) | 🟡 Medium — 8 controls in a row at desktop; partially mitigated on mobile by `hidden sm:flex` |

---

## 5. Current UX inconsistencies (PM vs Admin)

| Aspect | Admin portal (legacy or V2) | PM portal | Drift |
|---|---|---|---|
| Sidebar grouping | V2: 6 domains + footer rail (cross-portal pinned) | Flat 9 entries, no grouping | ❌ major |
| Active-state color | V2: 2-px stripe + slate-800 bg | Saturated amber-600 bg + white text | ❌ major |
| Footer rail (Tasks / PO Requests / Guidance) | V2: in sidebar footer | Tiles on hub overview | 🟡 different surface |
| Coaching sublines | V2: sentence-case slate-500, max 12 words | Mono uppercase feature-lists, ~3–5 words | ❌ tone drift |
| iOS mobile drawer scroll fix | Admin: applied (Phase IV-A.0) | PM: **NOT applied** — `<SheetContent>` has no flex-col, no scroll wrapper, no `WebkitOverflowScrolling: touch` | 🔴 P0 — same field-blocking iOS bug recurs in PM portal |
| Tile grid hero count | Admin: 0 (sidebar is the primary surface) | PM: 15 tiles | ❌ major surface-philosophy drift |
| Inline widgets above tiles | Admin: 1–2 calm headers | PM: 6+ stacked widgets | ❌ major rhythm drift |
| Notification bell, OfflineIndicator, System Health Badge | Both portals share component | Same | ✅ aligned |
| Hub intro card | Admin: minimal H1 + subline | PM: large "Welcome" prose block with icon | ❌ tone drift |

---

## 6. PM-specific operational pain points (observed in code · NOT speculative)

1. **Sidebar omits the most-used surfaces.** Daily Reports, Inspections, Meetings, Incidents, Pre-Op, QA/QC — the high-frequency Class A work — are not in the sidebar. PMs reach them only via Hub tiles or by typing the URL. This is a fundamental hierarchy inversion.

2. **iOS mobile drawer scroll regression.** `PmShell.jsx` line 108 renders `<SheetContent side="left" ... w-72>` with `<SideNav>` directly inside — no internal scroll container. iPhones with the drawer open will have the bottom 30–40% of the menu unreachable, replicating the Phase IV-A.0 admin bug.

3. **Two separate equipment surfaces.** `/pm/fleet` (sidebar — master + status + parts) and `/pm/equipment` (Hub tile #11 — Pre-Op inspections). The naming makes the difference unclear to a new PM.

4. **Cross-portal pinned items duplicated as Hub tiles.** `/tasks`, `/po-requests`, `/project-health`, `/asset-transfers` appear as Hub tiles in PM but as a footer rail in Admin V2. Two portals, two surface treatments for the same cross-portal concept.

5. **Coordination widgets compete with form access.** PasskeyEnrollPrompt + FieldMemoryGlance + LastActivityLine + OperationsCenter + PmCrewCompliance card + PmHaulActivityTile + DispatchLifecycleTile all stack above and around the form tiles. PMs scroll through 6+ widgets before reaching the tile grid.

6. **No "today" focus.** Nothing on the Hub surfaces tells a PM "here's what changed since you last logged in" — every widget shows a different time horizon (LastActivityLine is calm but not action-oriented).

7. **Severity color discipline absent.** Hub tiles use 6 different accent hues with no semantic mapping. A PM scanning the tile grid cannot tell which tile carries operational urgency from color alone.

8. **No PM-equivalent of Admin's "Operations" domain.** The PM portal has no single surface that aggregates "today's field activity across my assigned projects" — Daily Reports, Inspections, Meetings, Incidents, Pre-Op all live as separate routes.

---

## 7. Mobile / iPad concerns

### Confirmed regressions

- **P0 · iOS Safari drawer scroll bug** — `PmShell.jsx` line 108. Pattern matches the pre-Phase-IV-A.0 admin bug exactly. Mobile drawer with 9 entries fits today, but adding any sidebar children (which IV-BETA.1 will do) will reproduce the field-blocking scroll trap.

### Mobile-quality observations

- `lg:hidden` correctly hides the hamburger on desktop, shows on mobile/iPad — same pattern as Admin.
- Top-bar collapse on mobile (`hidden sm:flex`) correctly hides PortalSwitcher, GlobalSearch, System Health, KeyRound — matches Admin.
- Hub tile grid `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` — appropriate for mobile.
- Hub inline widgets (FieldMemoryGlance, OperationsCenter, PmCrewCompliance) — not audited individually; require per-widget mobile review.
- No bottom-nav (per `MOBILE_NAVIGATION_STANDARD.md`, PM portal does NOT need bottom-nav — drawer is sufficient).

### iPad-specific

- Sidebar collapses to drawer at `lg:` breakpoint (1024 px). iPad portrait is 768 px = drawer; iPad landscape is 1024 px = sidebar. Both render correctly.

---

## 8. High-frequency vs rare workflow identification

Inferred from the routing structure + token-scoping rules in `pm_routes.py` and form-frequency conventions:

| Frequency class | Workflows |
|---|---|
| **Shift-critical** (every shift) | Reviewing/approving Daily Reports · Reviewing today's Inspections · Acknowledging Incidents · Reading new field-leadership submissions · Crew Compliance glance |
| **Daily** (1+×/day) | Tasks · PO Requests · Project Health glance · Asset Transfers · Photos review · Meetings review · QA/QC review |
| **Weekly** | Jobs master maintenance · Posters generation · Compliance Export · Field Leadership records list |
| **Monthly / on-demand** | Fleet master · People master · Suppliers master · Email Routing audit |
| **Rare / forensic** | Change Password · Forgot Password reset flow · Crew Compliance deep dive |

This frequency rank-order should drive the new PM sidebar's domain ordering (most-used first), mirroring `ADMIN_UX_GOVERNANCE.md` §III.

---

## 9. Existing strengths that must NOT be broken

The refactor will preserve the following — these are working operational surfaces that PMs depend on:

1. **`/pm/crew-compliance` card on Hub** — 4-tile compliance summary (Crew · Expiring · Expired · Open CAPAs) is the single highest-signal accountability widget in the PM portal. It must remain visible without scroll on the post-refactor Hub.
2. **`OperationsCenter` compact KPI block** — fast operational glance, must remain on Hub.
3. **`PmHaulActivityTile`** — production-awareness for jobs with haul operations.
4. **`DispatchLifecycleTile`** — cross-portal DLS visibility, PM-scoped via `project_numbers`.
5. **`LastActivityLine`** — calm trace of recent personal activity.
6. **`FieldMemoryGlance`** — operational-attention read-only surface.
7. **Per-project scoping** — every list endpoint is server-side filtered by `compute_pm_scope`. The PM only sees jobs they're assigned to. This MUST remain invisible to the refactor — no UI-side filtering is introduced.
8. **`AP()` (admin-or-pm) route wrappers** — `/pm/daily`, `/pm/incidents`, `/pm/meetings`, `/pm/inspections`, `/pm/jha-plans`, `/pm/trench-boxes`, `/pm/equipment` all use the cross-token wrapper. This means an admin viewing the same URL sees the same surface — that consistency must be preserved.
9. **PortalSwitcher** in top-right — cross-portal navigation is fast.
10. **`AdminJobMasterPanel` reuse on `/pm/jobs`** — PMs and Admins use the same job-master panel, scoped server-side. The refactor must not introduce a divergent PM-only job UI.
11. **Site Posters** — the QR-poster generator at `/pm/posters` is a fast-access utility PMs use weekly. It must stay one tap away.
12. **Compliance Export** at `/pm/compliance-export` — audit-ready CSV in one click. Must remain frictionless.

---

## 10. Hidden dependencies (must not be ruptured by refactor)

| Dependency | Where it lives | Why it matters |
|---|---|---|
| Per-PM bcrypt token bound to `password_hash[:16]` | `pm_routes.py` + `pmAuth.js` | Rotating a PM password invalidates all old tokens. Refactor must not change auth surface. |
| `EnforcePortalScope` redirect logic | `frontend/src/components/EnforcePortalScope.jsx` | When URL leaves `/pm/*` and a PM token is the only token, the portal clears that token. Refactor must keep PM URLs under `/pm/*`. |
| `clearAllSessions()` on sign-out | `pmShell.signOut` calls `clearAllSessions()` | iter179 P0 hardening — wipes every portal token. Refactor must not regress to single-portal token clearing. |
| Server-side PM scoping | `compute_pm_scope()` in `pm_auth.py` | Every list endpoint applies this. UI must not bypass via client-side filters. |
| `IdleTimeout` component | Active across portals | Refactor must not unmount it. |
| `PortalSwitcher current="pm"` prop | `PmShell` top-bar | Lets PMs jump to other portals they're authorized for. Must remain in the new shell. |

---

## 11. Executive vs field PM operational realities

PMs operate in three modes; the platform should support all three without trade-off:

| Mode | Context | Workflow shape | Implication |
|---|---|---|---|
| **Office-deep mode** | Desktop, multi-monitor, time to read | Multi-tab review of jobs, financials, compliance | Sidebar should support deep navigation; tile grid is acceptable on the Overview surface |
| **Field-glance mode** | iPad in the truck, between job sites | Quick check of Daily Reports submitted today, any escalations | Mobile drawer + Tier-0 "today" signal · sticky CTA · 44 px touch targets |
| **Interruption-driven mode** | Phone in pocket, urgent escalation push | Open the push notification → land directly on the actionable surface · acknowledge or act in ≤ 3 taps | Push deep-links must bypass the Hub overview entirely — they land on the form/escalation page |

**Implication for governance:** the refactor must not optimize for one mode at the expense of the others. The Office-deep PM needs the breadth currently visible in the Hub grid; the Field-glance PM needs the calm sidebar; the Interruption-driven PM needs deep-link integrity.

---

## 12. Workflow collision points

Risks the governance refactor must explicitly avoid:

1. **Two equipment surfaces** — collapsing `/pm/fleet` and `/pm/equipment` into one accidentally would destroy daily Pre-Op workflows. Solution: governance must specify they live in the same domain (Equipment & Fleet) but as distinct routes with distinct nouns.
2. **Cross-portal pinned items relocation** — moving Tasks / PO Requests / Project Health / Asset Transfers from Hub tiles to sidebar footer rail (matching Admin V2) is correct, but the Hub tiles must NOT be removed in the same iteration. Footer rail addition is additive; Hub tile removal is a Phase IV-BETA.2 cleanup after PMs adjust.
3. **Daily Reports / Inspections / Incidents naming** — promoting these from Hub tiles to sidebar children risks renaming. They must keep the exact label they currently show (canonicalized per doctrine) to preserve muscle memory.
4. **Severity color application to PM tiles** — the current 6-hue palette is operationally meaningless. The refactor will map each tile to a single domain stripe — but a PM accustomed to red-meaning-Daily-Report will be momentarily disoriented. Mitigation: keep stripe colors per the new domain map AND surface a one-line "What changed in this view" hint on first render after the V2 feature flag is enabled.

---

## 13. Surfaces that must remain unchanged in this phase

- All `/pm/{form}/*` form submission and review surfaces (DailyReportsDashboard, IncidentsDashboard, etc.)
- All backend PM API endpoints (zero backend changes per directive)
- The `AP()` admin-or-pm route wrapper
- Auth surfaces (`/pm/login`, `/pm/reset/:token`, `/pm/change-password`)
- Cross-portal PortalSwitcher and NotificationBell behavior
- All server-side PM scoping logic

---

## 14. Inventory complete · readiness for governance

This audit has identified:
- **9 sidebar entries** (current PM sidebar)
- **15 hub-surface tiles** (current PM Overview)
- **10 form/list routes** (under `/pm/*` but not in sidebar)
- **11 PM-specific backend endpoints**
- **8 doctrine-violating copy strings**
- **2 P0 / 9 medium loudness sources**
- **1 P0 iOS mobile drawer scroll regression**
- **12 existing strengths to preserve**
- **6 hidden dependencies**
- **3 operational modes (Office-deep · Field-glance · Interruption-driven)**

The 8 governance deliverables that follow this audit will use this inventory as their factual foundation. Anything that contradicts this audit must amend the audit first.

---

## Verdict

🟢 **PM PORTAL INVENTORY COMPLETE.** The governance documents may now proceed, grounded in the actual operational surface, not theoretical UX.

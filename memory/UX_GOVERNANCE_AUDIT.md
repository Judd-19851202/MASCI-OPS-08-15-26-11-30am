# MASCI Platform — UX Coherence Audit
*Audit date · 2026-05-21 · scope: full platform · read-only inventory · no code changes*

This document is the **first deliverable** of the Platform-Wide Visual Governance & UX Coherence pass. It is paired with:
- `UX_GOVERNANCE_RULES.md` — the standards to apply going forward
- `UX_REFINEMENT_ROADMAP.md` — the priority-ranked bounded-iteration plan

**Stabilization posture preserved**: nothing in this audit recommends architectural change, workflow change, route renames, or feature removal. Everything here is bounded visual refinement under `STABILIZATION_PRINCIPLES.md`.

---

## 1 · Platform Inventory

**213 React routes** across the application. Twelve top-level hub components:

| Hub | File | Layout family | Notes |
|---|---|---|---|
| Home (`/`) | `Hub.jsx` | Flat grouped (4 numbered sections) | Public front door · uses `BigTile`/`MediumTile`/`PortalPill` (inline components, NOT `SectionTile`) |
| HR (`/hr`) | `HrHub.jsx` | Flat grouped (4 ops sections) | **iter317-C Part 2 already refined** — left-edge stripe, calm groupings |
| Field (`/field`) | `FieldSection` | Flat grid w/ `SectionTile` | |
| Safety (`/safety-portal`) | `SafetyHub.jsx` | KPI strip + flat tile grid | Uses shared `SectionTile` + dedicated `KPI` component (custom) |
| Dispatch (`/dispatch-portal`) | `DispatchHub.jsx` | Tabs-driven inside hub | `max-w-7xl` (different width!) + dark `bg-slate-50` (different chrome!) |
| Shop (`/shop`) | `ShopHub.jsx` | KPI strip + tabs + panels | Custom `Kpi` component, custom tile component |
| Admin (`/admin`) | `AdminHub.jsx` | Inside `AdminShell` (sidebar) | Custom `SectionTile` inline (NOT shared component) |
| PM (`/pm`) | `PmHub.jsx` | Inside `PmShell` (sidebar) | Custom `PmTile` inline |
| Leadership (`/leadership`) | `FieldLeadershipHub.jsx` | Flat grouped (5 numbered sections) | Uses shared `SectionTile` |
| FL Portal (`/field-leadership/portal/dashboard`) | `FieldLeadershipPortalDashboard.jsx` | Compact dashboard | New (iter314) · still rough |
| Safety Forms (`/safety/forms`) | `SafetyFormsHub.jsx` | Flat grid | |
| Training (`/guidance`) | `OperationalGuidanceCenter` | Library navigation | Different paradigm — content layer |

**Reusable tile component exists**: `/app/frontend/src/components/SectionTile.jsx` — 14-accent palette table, unified rhythm (top accent bar, 14×14 icon chip, 3xl/4xl title, mono CTA, bottom-aligned arrow).

**It is NOT used consistently.** Four of the eight major hubs (HR · Shop · PM · Admin) each define their own inline tile. This is the single biggest driver of platform-wide drift.

---

## 2 · Inconsistency Findings (evidence-backed)

### 2.1 · Card weight / border treatment — **HIGH IMPACT DRIFT**
Border-usage counts across `pages/` (from grep):

| Pattern | Count | Where |
|---|---|---|
| `border-2 border-amber-300` | 24 | Mostly information/coaching panels |
| `border-2 border-red-300` | 14 | Warnings, blocked items |
| `border-2 border-red-700` | 11 | Primary CTAs, danger buttons |
| `border-2 border-amber-400/500/600` | 22 | Mixed — buttons, banners, panels |
| `border-slate-300` (no `border-2`) | 434 | Default panel border (correct baseline) |
| `border-slate-200` | 324 | Softer baseline (also correct) |

**Drift evidence**:
- Hub `BigTile`: `border-2 border-slate-300` (hot, ~3xl titles)
- HR Hub tile (post iter317-C): `border border-l-4 border-l-<accent>` (calm) ✅
- Shop Hub tile (Kpi/inline): `border-2 border-slate-200` (medium)
- Admin Hub `SectionTile` (inline custom): `border-2 border-slate-200 hover:border-red-700` (medium, red hover)
- PM Hub `PmTile`: `border-2 border-slate-200 hover:border-amber-600` (medium, amber hover)
- Safety Hub uses shared `SectionTile` → `border-2 border-slate-300 hover:border-<accent>-700` (hot)
- FL Hub uses shared `SectionTile` → same hot pattern

**Result**: HR feels calm; everywhere else still has the "everything screams equally loud" problem the operator just called out. HR is now the reference target.

### 2.2 · Heading hierarchy — **MEDIUM IMPACT DRIFT**
H1 size drift across signed-in hubs:

| Hub | H1 size | Notes |
|---|---|---|
| Home `/` | `text-4xl sm:text-5xl lg:text-6xl` | OK for public hero |
| HR `/hr` | `text-3xl sm:text-4xl` | Calm signed-in tone |
| Shop `/shop` | `text-4xl sm:text-5xl` | Too loud for an interior hub |
| Dispatch `/dispatch-portal` | `text-2xl` | Too quiet (under-emphasized) |
| FL `/leadership` | `text-4xl sm:text-5xl lg:text-6xl` | Same as public hero (over-loud) |
| Safety `/safety-portal` | inside `SafetyShell` | size set by shell, varies |
| PM/Admin | inside Pm/AdminShell | size set by shell |

**Tile H3 size drift inside the grid**:
- `BigTile` (Hub): `text-3xl sm:text-4xl` (very loud)
- `SectionTile` (Safety/FL): `text-3xl sm:text-4xl` (very loud)
- HrHub tile (post-refinement): `text-lg` (calm) ✅
- ShopHub tile: `text-base sm:text-lg` (calm)
- AdminHub tile: `text-base` (calm)
- PmHub tile: `text-base sm:text-lg` (calm)

**Range from `text-base` to `text-4xl` within one platform.** No governing rule.

### 2.3 · Header chrome — **MEDIUM IMPACT DRIFT**
Counts in the header row across hubs:

| Hub | Container | BG | Items in header right cluster |
|---|---|---|---|
| `/` | `max-w-6xl` | `bg-slate-900` | LangToggle + Sign in link |
| `/hr` | `max-w-6xl` | `bg-slate-900` | 9 items (PortalSwitcher · GlobalSearch · Bell · Offline · Lang · CompanyInfo · Password · SignOut · Logo) |
| `/shop` | `max-w-6xl` | `bg-slate-900` | 7+ items |
| `/leadership` | `max-w-6xl` | `bg-slate-900` | 7 items (Guides, Records, etc.) |
| `/dispatch-portal` | **`max-w-7xl`** | **`bg-slate-950`** | 9 items + inline title block |
| `/safety-portal` | inside `SafetyShell` | varies | — |
| `/admin` | `max-w-7xl` | inside `AdminShell` (sidebar) | — |
| `/pm` | inside `PmShell` (sidebar) | — | — |

**Drift**: Dispatch is the outlier (`max-w-7xl` + `slate-950`). Every other flat hub uses `max-w-6xl` + `slate-900`.

The mobile collapse pattern (iter203 — hide `PortalSwitcher`, `GlobalSearch`, `Guides` button below `sm:`) is implemented on HR and Shop but NOT on Dispatch or Leadership — they will overflow at narrow viewports.

### 2.4 · Color semantics — **HIGH IMPACT DRIFT**
The platform uses 14 color families in `SectionTile.ACCENTS` (red, redDeep, amber, orange, yellow, lime, emerald, cyan, blue, indigo, purple, fuchsia, rose, slate). On any single hub today, 5–8 different accent colors coexist with no semantic meaning attached — the picker chose colors by visual taste, not operational meaning.

**Current color → meaning mapping is inconsistent**:
- Red is used for: danger (incidents), primary CTA (Safety home tile), payroll variance, fire extinguishers — meaning collapses.
- Amber is used for: tasks, coaching, fleet, PO requests, attention/caution — meaning is fuzzy.
- Emerald is used for: lifecycle, QA/QC, success/verified, training — mixed.
- Cyan is used for: Safety portal identity AND time-off requests — collision.
- Purple is used for: HR portal identity AND FL portal accounts AND training records — too many roles.
- Indigo is used for: PM identity AND PO requests AND guides — collision.

**No portal-identity color is reserved**. Tiles on Safety Hub include indigo (for Guides) and purple (for Reports), even though Safety's identity color is cyan.

### 2.5 · KPI / stat block patterns — **MEDIUM IMPACT DRIFT**
- `SafetyHub.jsx`: custom `KPI` component, 4-accent palette (cyan/red/amber/emerald), 8 tiles in a 2×4 grid.
- `ShopHub.jsx`: custom `Kpi` component, monochrome, 4 tiles in a 2×4 grid.
- `HrHub.jsx`: uses `OperationsCenter` component (different visual rhythm).
- `AdminHub.jsx`: uses `AdminKpiStrip` component (different again).
- `PmHub.jsx`: KPIs embedded inside tiles (count field per tile).

Five different KPI presentations across five hubs.

### 2.6 · Integration card placement — **LOW–MEDIUM IMPACT DRIFT**
The `IntegrationHealthCard` + `IntegrationEventsCard` pair is placed:
- HR: bottom of page (correct — supports, doesn't compete) ✅
- Safety: middle of page (above operational tiles) — competes
- Dispatch: dedicated "Integrations" tab — buried
- Shop: dedicated "Integrations" tab — buried
- Admin: top of page (right after `OperationsCenter`) — competes

The operator just affirmed (in iter317-C confirmation) that integrations should "support the page, not compete." Currently 3/5 placements violate this rule.

### 2.7 · Operational tone — **GENERALLY CLEAN** ✅
Banned-phrase scan returned only 2 hits across the entire `pages/` and `components/` tree:
- `pages/TrainingTrack.jsx:97` — "Falls back to English seamlessly" (acceptable — operational/technical, not LMS jargon)
- `pages/FieldLeadershipHub.jsx:371` — "compliant with employment-documentation best practices" (acceptable — legal-compliance context, not LMS jargon)

No "stakeholder", "empower", "journey", "culture of", "learning module", or "compliance pathway" anywhere. The platform's operational voice is intact and consistent.

**Minor tone observations**:
- Home `/` headline: `"Run Every Job. Control Every Detail. Protect Everything."` — appropriately marketing-y for the public door.
- DispatchHub kicker: `"Dispatch Portal · iter132"` — an iteration tag leaks to end-users (mild noise, low priority).
- FL Hub badge: `"Restricted · Crew Documentation"` — direct and operational ✅.
- HR Hub kicker: `"HR Portal · {user.name}"` — direct ✅.

### 2.8 · Mobile / tablet — **PARTIALLY CONSISTENT**
- iter203 collapse pattern (hide PortalSwitcher / GlobalSearch / Guides on `<sm`) implemented on HR, Shop. NOT implemented on Dispatch, Leadership — those will overflow.
- HR Hub (post iter317-C) mobile stacking verified clean at 390×844.
- DispatchHub uses `flex-wrap` on the header but the cluster has 9 children — wraps to 3 lines at 390px (cluttered).
- LeadershipHub mobile shows 5 buttons in the right cluster — wraps similarly.

### 2.9 · Sidebar / flat navigation philosophy — **INTENTIONALLY MIXED** ✅
- Admin + PM use `AdminShell`/`PmShell` with left sidebar (appropriate — both have 15+ sub-sections each).
- HR + Safety + Shop + Dispatch + Leadership use flat grouped/tabbed hubs (appropriate — each has 8–15 destinations and crews need direct one-tap entry).
- This split is correct. **DO NOT introduce sidebars on the flat hubs.** Operator-affirmed in iter317-C.

### 2.10 · Hub backgrounds — **MOSTLY CONSISTENT**
- `blueprint-bg` + `caution-stripe` is the canonical signed-in pattern. Used on Hub, HrHub, ShopHub, FieldLeadershipHub.
- DispatchHub uses `bg-slate-50` (no blueprint, no caution stripe) — drift.
- SafetyHub inside `SafetyShell` — has its own chrome.

---

## 3 · Summary · "what's hurting the platform" (priority order)

| # | Finding | Severity | Effort | Confidence |
|---|---|---|---|---|
| 1 | Card weight inconsistency — `border-2 + bg-<accent>-50` hot pattern still on Safety / Shop / Admin / PM / Leadership tiles while HR is now calm | **HIGH** | Medium | High — code-grep evidence |
| 2 | `SectionTile` shared component exists but only 3/8 hubs use it — every hub redefines its own tile | **HIGH** | Medium | High |
| 3 | Color semantics undefined — red/amber/emerald/cyan/purple/indigo each carry 3+ meanings | **HIGH** | Low (just a rules doc + audit pass) | High |
| 4 | Tile H3 size drift (`text-base` → `text-4xl` for the same UX role) | **MEDIUM** | Low | High |
| 5 | Integration cards placed where they compete with operational sections on Safety + Admin (and buried into tabs on Dispatch + Shop) | **MEDIUM** | Low | High |
| 6 | Dispatch container width / bg drift (`max-w-7xl` + `slate-50` vs canonical `max-w-6xl` + `blueprint-bg`) | **MEDIUM** | Low | High |
| 7 | Header chrome inconsistency — Dispatch and Leadership don't implement iter203 mobile collapse | **MEDIUM** | Low | High |
| 8 | KPI/stat block fragmentation — 5 different presentations across 5 hubs | **MEDIUM** | Medium | Medium |
| 9 | H1 size drift across hubs | **LOW–MEDIUM** | Low | High |
| 10 | Iteration tag leakage in Dispatch header (`iter132`) | **LOW** | Trivial | High |
| 11 | Tone | **CLEAN ✅** | n/a | High |
| 12 | Sidebar/flat split | **CORRECT ✅** | n/a | High |
| 13 | Mobile collapse on HR/Shop | **WORKING ✅** | n/a | High |

---

## 4 · Reference HR pattern (post-iter317-C · the target visual contract)

`HrHub.jsx` after iter317-C Part 2 is now the **calm reference target**. Everything we govern against should match its rhythm:

- Tile chrome: `bg-white border border-slate-200 border-l-4 border-l-<accent>` (left-edge stripe, NOT full hot border)
- Tile padding: `p-5`
- Tile H3: `text-lg font-display font-black`
- Tile desc: `text-sm text-slate-600`
- Tile CTA: `inline-flex h-9 px-3 rounded-md bg-<accent>-700 text-white font-bold uppercase tracking-wide text-xs`
- Section heading: `font-mono text-xs uppercase tracking-[0.22em] text-slate-700` + thin slate divider + muted italic subtitle
- Demoted section (Integrations): `text-slate-500` heading + `border-t border-slate-200` separator above
- Hover micro-interaction: `hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300`
- Grid: `grid grid-cols-1 sm:grid-cols-2 gap-4` per group; groups stacked with `space-y-10`

This pattern is what `UX_GOVERNANCE_RULES.md` codifies as the platform standard.

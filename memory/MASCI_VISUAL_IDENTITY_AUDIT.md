# MASCI Visual Identity Audit (Track 13.4E)

**Mode:** discovery only · NO standardisation · NO design.  
**Generated:** 2026-02 (Track 13.4E).  
**Evidence basis:** Phase 1 (Track 13.4B) 44 desktop portal landings + Track 13.4E 30 new iPad-landscape / iPad-portrait / phone landings of 5 authenticated portals + per-component source review from Phase 2A.

---

## 0. Surfaces audited

| Surface family | Phase 1 desktop | Track 13.4E iPad-LS | Track 13.4E iPad-PT | Track 13.4E phone |
|---|---|---|---|---|
| Hub home `/` (public) | ✅ | (not re-captured) | (not re-captured) | (not re-captured) |
| Admin landing | ✅ | ✅ | ✅ | ✅ |
| Dispatch portal | ✅ | ✅ | ✅ | ✅ |
| PM command center | ✅ | ✅ | ✅ | ✅ |
| Shop hub | ✅ | ✅ | ✅ | ✅ |
| HR hub | ✅ | ✅ | ✅ | ✅ |
| Safety portal login | ✅ | — | — | — |
| Leadership gate | ✅ | — | — | — |
| Field Leadership portal login | ✅ | — | — | — |
| Public surfaces (cheatsheet, JHA, trench boxes, public forms × 6, QR landing, master sign-in, dev gate) | ✅ | — | — | — |

74 screenshots total (44 from Phase 1 + 30 new for 13.4E).

---

## 1. Visual identity dimensions

### 1.1 Logo / brand mark
- A MASCI brand mark is rendered inline in each portal header (no central asset). The parent brand asset `forgedops-logo.png` is unused (W-16).
- No portal currently shows the ForgedOps parent brand.

### 1.2 Color (per portal)
- Hardcoded Tailwind palette per portal via `portalPalette.js`.
- Documented drifts (V-01 / V-02 / V-03 from Track 13.4B):
  - Shop header amber-500/700/300 vs Shop tile orange-600/700.
  - PM tile-CTA amber vs canonical PM indigo.
  - Field Leadership red-700 overlaps with Admin / Leadership brand red.
- `tokens.css` exists but unwired (V-04). Components hardcode Tailwind color literals (~690 red-700, ~605 slate-900, ~105 cyan-700 occurrences per `tokens.css` source comment).

### 1.3 Typography
- Single Tailwind defaults (`Inter` / system stack) across all portals — consistent.
- No per-portal typography drift observed at the landing level.

### 1.4 Headers
- ≥4 distinct header strategies (V-06): `<PortalSwitcher>` mounted in Dispatch · Shop · HR; PM uses `<HubV…>`; Safety uses a literal header; Admin uses a slate-900 bar with no PortalSwitcher; Leadership / Field Leadership use bespoke gate chrome.

### 1.5 Hero / KPI strip
- HR (post-13.4A cleanup) → `HrKpiStrip` is HR-native; portals differ:
  - Dispatch → `DispatchMapHero` + counts strip.
  - PM → "MY PROJECTS" project rows + section letters A–E.
  - Shop → tile-grid (no KPI strip).
  - Safety → tile-grid (no KPI strip).
  - HR → `HrKpiStrip`.
  - Admin → command-center cards.
- → **No common KPI-strip primitive**.

### 1.6 Cards / Tables / Status chips
- Card layout: shadcn `<Card>` baseline + bespoke per-hub primitives (V-07).
- Tables: no shared `<Table>` primitive; mix of `data-table` and `<table>` HTML.
- Status chips: 15 distinct components, two share filename `StatusBadge.jsx` (V-07).

### 1.7 Buttons / CTAs
- shadcn `<Button>` baseline. CTAs in tile rows differ per hub (PM uses amber against indigo palette, ShopHub uses amber against orange palette — both documented drifts).

### 1.8 Empty states
- No shared `<EmptyState>` primitive. Empty rows are inlined per consumer (e.g., "No deliveries today" in PM, "No recent operational notes." in HR).

### 1.9 Modals / Dialogs
- shadcn `<Dialog>` baseline. Trench Safety and ODR use bespoke modals; consistent shape.

### 1.10 Layout systems (mobile / iPad / desktop)
- Tailwind responsive utilities; per-hub responsive decisions.
- Track 13.4E phone-viewport screenshots show:
  - **Admin (390×844 phone)** — usable, tile grid stacks vertically.
  - **Dispatch (phone)** — map dominates; counts and CTAs scroll below.
  - **PM (phone)** — project rows full-width.
  - **Shop (phone)** — tile grid stacks.
  - **HR (phone)** — KPI strip + tile groups stack; readable.
- No phone-viewport layout *breaks* the way the original Dispatch map break did, but layout density varies (PM rows feel cramped on phone vs HR which compresses well).

---

## 2. "Does it look like MASCI OPS?"

| Surface | Looks like MASCI OPS? | Visually belongs? | Match standards? | Feels like one platform? | Drift notes |
|---|---|---|---|---|---|
| Hub home `/` | ✅ | ✅ | ✅ | ✅ | strongest portal-cohesion surface |
| Admin | ✅ | ✅ | partial — slate-900 chrome differs from operator portals | mostly | header chrome differs from operator portals |
| Dispatch | ✅ | ✅ | ✅ | ✅ | post-13.4A, strong identity |
| PM | ✅ | partial — amber CTA in indigo palette | drift documented | mostly | V-02 drift |
| Safety | ✅ | ✅ | ✅ | ✅ | (login surface only — no full audit performed at 13.4E) |
| Shop | ✅ | partial — header amber vs tile orange | drift documented | mostly | V-01 drift |
| HR | ✅ | ✅ (post-13.4A) | ✅ | ✅ | HR is the cleanest operator portal today |
| Leadership gate | ✅ | partial — bespoke red gate chrome | does NOT match operator portals | no | gate is a distinct surface family |
| Field Leadership login | ✅ | partial — black/red gate chrome | partial | no | shares Admin red |
| Public cheatsheet | ✅ | — print chrome | n/a | n/a | print-oriented |
| Public JHA | ✅ | ✅ | ✅ | ✅ | |
| Public Trench Boxes | ✅ | ✅ | ✅ | ✅ | |
| Public forms (× 6) | ✅ but each has its own chrome | partial | drift documented | no | V-14 drift |
| Trench Safety QR landing | ✅ strong identity (Trench is exemplary) | ✅ | ✅ | ✅ | preserve-list candidate |
| Operations Map (full) | ✅ | ✅ | ✅ | ✅ | shared with DispatchMapHero |
| Master `/sign-in` | ✅ | ✅ | ✅ | ✅ | clean master-sign-in chrome |
| Dev gate | ✅ | — internal | n/a | n/a | internal surface |

### Where it excels
- **Trench Safety** module — 23 dedicated pages, strong consistent identity (Preserve-List #1).
- **HR post-13.4A** — cleanest operator portal.
- **Hub home `/`** — strong tile-grid identity.
- **PM Command Center** (post-13.4A baseline) — strong role-first identity.
- **Dispatch (post-13.4A)** — dominant map, strong fleet-first identity.

### Where it drifts
- Shop header vs tile colors (V-01).
- PM tile-CTA color (V-02).
- Field Leadership red overlapping Admin red (V-03).
- Public forms each carrying their own chrome (V-14).
- Header strategies — ≥4 distinct (V-06).
- Status-chip sprawl (V-07).
- Multiple "Command Center" pages with overlapping signals (V-09).

---

## 3. Per-viewport observations (Track 13.4E new captures)

### 3.1 Admin
- iPad LS / PT: command-center card grid intact; header chrome scales.
- Phone: tiles stack; admin sub-navigation collapses into vertical list.

### 3.2 Dispatch
- iPad LS / PT: map height appropriate (responsive 420/520px proved out in 13.4A); counts strip and CTAs visible.
- Phone: map at 300px height; counts row scrolls. Map remains primary surface.

### 3.3 PM Command Center
- iPad LS / PT: two-column → single-column flip; section letters A–E remain visible.
- Phone: project rows readable; "MISSING DAILY REPORT" alerts still prominent.

### 3.4 Shop
- iPad LS / PT: tile grid scales (3-col → 2-col).
- Phone: 1-col tile stack; CTAs full-width.

### 3.5 HR
- iPad LS / PT: KPI strip wraps; tile groups intact.
- Phone: KPI strip stacks 1-col; tile groups stack; clean.

---

## 4. Visual identity findings index (cross-references)

| ID | Variance | Where | Severity |
|---|---|---|---|
| V-01 | Shop header amber vs orange tile | Shop | low |
| V-02 | PM tile-CTA amber vs indigo | PM | low |
| V-03 | FL red-700 overlaps Admin | FL · Admin · Leadership | medium |
| V-04 | tokens.css unwired | platform | high (blocks design system) |
| V-05 | Hub size variance 4.6× | all portals | medium |
| V-06 | ≥4 header strategies | all portals | medium |
| V-07 | 15 status-chip components | platform | medium |
| V-09 | 8 *CommandCenter pages | platform | medium |
| V-13 | Mobile evidence gap | (now partly closed at 13.4E for 5 portals) | medium → partial closure |
| V-14 | Public surface chrome drift | public surfaces | high (white-label) |
| V-15 | Driver portal missing | Driver | medium |

---

## 5. What this audit did NOT do
- Did not standardise any visual element.
- Did not propose a Design System V1.
- Did not capture every sub-route at every viewport (sampled at portal landings).
- Did not visit each individual form at each viewport (the next track may).
- Did not score the drift items differently from Track 13.4B Phase 2A.

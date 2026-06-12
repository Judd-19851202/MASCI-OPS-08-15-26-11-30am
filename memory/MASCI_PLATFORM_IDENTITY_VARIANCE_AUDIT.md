# MASCI Platform — Identity & Consistency Variance Audit (Track 13.4B · Phase 2A)

**Mode:** Discovery only. No scoring. No recommendations. No fixes.  
**Generated:** 2026-02 (Track 13.4B Phase 2A)  
**Evidence basis:** Live source tree + DB + Track 13.4B Phase 1 inventory.

---

## A. Visual Identity Variance

### A.1 Theme infrastructure that exists
- `/app/frontend/src/lib/portalPalette.js` — Tailwind palette table keyed by portal id (`admin`, `pm`, `hr`, `shop`, `safety`, `dispatch`, `field_leadership`).
- `/app/frontend/src/styles/portal-system.css` — per-portal CSS-variable accents (paired with the Tailwind table).
- `/app/frontend/src/styles/tokens.css` — semantic token layer (`--brand-primary`, `--ink-*`, `--paper-*`). **Status declared in file:** `"STATUS: PROPOSAL — NOT YET WIRED into any component."`
- `/app/frontend/src/index.css` — shadcn theme bridge.

### A.2 Documented drifts (recorded in `portalPalette.js` source comments)
> Quoted verbatim from the file header so this audit reproduces the engineer's own notes, not invented findings:

1. **Shop hub-header drift** — header uses `amber-500 / amber-700 / amber-300` while the canonical Shop *tile* palette is `orange-600/700`. (Two color systems coexist on the same portal.)
2. **PM tile-CTA drift** — `PmHub` tile-CTA renders `amber-600 hover` + `amber-700 text` even though the canonical PM portal palette is `indigo`. The PmHub TILES array is per-tile (not portal-keyed), so it stays literal.
3. **Field Leadership red-700** — uses `red-700` which matches admin brand-red. *Marked intentional* by the author ("No drift") but the audit notes two portals now visually overlap on the same accent.

### A.3 Hub-file size variance (objective measurement)

| Hub | Lines | Imports |
|---|---|---|
| `AdminHub.jsx` | 145 | 16 |
| `HrHub.jsx` | 343 (post-13.4A cleanup) | 22 |
| `PmHub.jsx` | 506 | 16 |
| `SafetyHub.jsx` | 505 | 16 |
| `ShopHub.jsx` | 597 | 24 |
| `FieldLeadershipHub.jsx` | 567 | 26 |
| `DispatchHub.jsx` | 668 | 27 |

**Range:** 145 → 668 lines (**4.6× variance**). Hubs were not assembled from a shared template.

### A.4 Header / hero component variance
Grepped for the welcome/hero/header component each hub mounts:

| Hub | Header / hero component observed |
|---|---|
| Dispatch | `<PortalSwitcher>` + custom header literal |
| PM | `<HubV…>` family |
| Safety | none of the shared header components matched the regex — likely a literal header |
| Shop | `<PortalSwitcher>` |
| HR | `<PortalSwitcher>` |
| Field Leadership | literal header |
| Admin | literal header |

→ **At least 4 different header/hero strategies coexist.**

### A.5 Status-chip / badge component sprawl
15 distinct status-style components live under `/app/frontend/src/components/`:

```
BackendStatusBanner.jsx        QueueStatusPill.jsx
StatusBadge.jsx                SubmitLangBadge.jsx
BackendVersionBadge.jsx        GovernanceHealthChip.jsx
DraftStatusPill.jsx            iam/IamBadges.jsx
ui/badge.jsx                   GPSHealthBadge.jsx
odr/ArchiveBadge.jsx           oa/StatusBadge.jsx        (← duplicate name)
operations-map/MapTrustChip.jsx
EquipmentStatusBoard.jsx       SessionStatusOverlay.jsx
```

Two components both named `StatusBadge.jsx` (one at root, one under `oa/`).

### A.6 Card / table / empty-state variance
- Card styling: `/app/frontend/src/components/ui/card.jsx` (shadcn baseline) **plus** per-portal bespoke cards inside each hub file (e.g., `DispatchHub.jsx` has 27 imports including its own tile/card primitives).
- Tables: no central `<Table>` standard observed — `data-table` and `<table>` HTML are mixed across modules (deep audit deferred to Phase 2B).
- Empty states: no shared `EmptyState.jsx` component — empty-message rendering is inlined per hub/card.

### A.7 Layout / navigation drift across portal landings
Phase 1 captured 22 portal landing screenshots at 1920×1080
(`/app/memory/track_13_4b_evidence/portal_landings/*.png`). Variance
observed (visual inspection, no scoring applied):

- Dispatch · PM · HR · Shop · Safety · Field Leadership: all use **portal-switcher header** + **tile-grid hub** pattern but the tile-grid dimensions, card padding, and hero placement differ between them.
- Admin: header is a slate-900 bar with no portal switcher — **different chrome family**.
- Leadership gate: bespoke red-700 password page — **does not share portal chrome**.
- Field Leadership Portal login: black/red gate — shares red-700 brand with Admin and Leadership gate.
- Public surfaces (`/`, `/cheatsheet`, `/jha`, `/trench-boxes`, public `/inspect/new`, `/meetings/new`, `/incidents/new`, `/daily/new`, `/equipment/new`): each uses a different header pattern (Hub home grid · clean MASCI red bar · plain JHA list chrome · cheatsheet print chrome · public-form chrome).

### A.8 Mobile / iPad variance
- Track 13.4A captured Dispatch / HR / PM at desktop + iPad landscape + iPad portrait.
- Phase 1 (this track) only captured **desktop 1920×1080** for the 22 portal landings → mobile / iPad evidence for the other portals is **not yet collected**. Deferred to Phase 2B.

---

## B. Role Clarity Variance

For each portal, the question the portal *must* answer:

| Portal | Question the portal must answer | Surfaces that try to answer it |
|---|---|---|
| Dispatch | *Where is my fleet?* | `DispatchMapHero` (fixed in 13.4A), Operational Attention cluster, Fleet KPIs, Live Map link |
| PM | *What requires PM attention today?* | `PmCommandCenter` rows ("MISSING DAILY REPORT", project risk), `PmHub` tile grid |
| Safety | *What requires safety attention today?* | `SafetyHub` tile groups (Incidents, JHA, Inspections, Documents), `safety-portal/dashboard` |
| HR | *What requires HR attention today?* | `HrHub` post-13.4A cleanup: `HrKpiStrip`, tile groups, `ExpirationsSummary`, Driver Safety Events |
| Shop | *What equipment requires recovery?* | `ShopHub` (597 lines, parts/work-order tiles, mechanic queue) |
| Admin | *What requires administrative oversight?* | `AdminCommandCenter`, `AdminHub` (145 lines — much thinner) |
| Field Leadership | *What requires field leadership action?* | `FieldLeadershipHub` (567 lines, 10 record kinds, attendance, write-up workflows) |
| Leadership | *Executive read-only view?* | `/leadership/*` (6 routes; gated by shared password) |
| Driver | *What is my next assignment / pre-trip status?* | dispatch_driver_sessions tokenized URLs (Phase 1 noted: no static login page surfaces explicitly) |

### B.1 Observed role-drift signals
- **Operations Actions tile (OA-1)** was mounted on all 7 portals before Track 13.4A removed it from HR. **It still appears on the other 6** — same component, same cross-portal language. Whether each portal needs it as a top surface is not assessed here (discovery only).
- **`OperationsCenter`** import was left in `HrHub.jsx`'s import list (now removed in 13.4A) but the component itself still exists and is imported into other portal hubs (`AdminHub`, `DispatchHub`). Cross-portal sharing of the "Operations Center" surface is documented; whether each portal needs operational summaries vs role-native summaries is deferred to Phase 2C scoring.
- **Multiple "Command Centers" coexist** (8 distinct ones — see Phase 1 §D): `AdminCommandCenter`, `PmCommandCenter`, `DispatchCommandCenter`, `OperationsCenterCommand`, `OperationalGuidanceCenter`, `OpsTrainingCenter`, `TrenchSafetyOpsCenter`, `OdrCenter`. They share naming conventions but were assembled by different sprints with different layouts.
- **`MotiveDrivers` cleanup tile** lives in HR (per Phase 1 §D `motiveDrivers` row) but the cleanup vocabulary is admin/ops — Phase 1 noted this is borderline.
- **`IntegrationHealthCard`** lived on HR (removed in 13.4A) but is still imported into `AdminIntegrationCenter`, `AdminCommandCenter`, etc. — appropriate; recording for trace only.

### B.2 Missing role surfaces (observed, not scored)
- Driver portal lacks a clearly named landing page among the static `pages/` files (only `/pages/driver/`, with tokenized URLs).
- HR's "Driver Safety Events" card is now the only HR-owned Motive surface; the dispatch-side driver coaching surface is absent from HR (Phase 1 §H lists `coaching/Field Leadership records` under FL).

### B.3 Duplicate role surfaces (observed)
- **Two `StatusBadge.jsx`** files: root + `oa/`.
- **Multiple "Hub" pages owning the same audience**: `Hub.jsx` (public root), `AdminHub.jsx`, `PmHub.jsx`, etc. (Each portal-specific, fine.) But `TrainingHub.jsx` overlaps audience with `OpsTrainingCenter.jsx` and `OpsTrainingGuide.jsx` — 3 surfaces targeting roughly the same audience.
- Operations Map appears at `/operations-map` (full-screen page) **and** as `DispatchMapHero` embed (now fixed). Same component family, two contexts — intentional, but a third Operations Center page (`OperationsCenterCommand.jsx`) also touches fleet data.

---

## C. Status-Language Variance

### C.1 Status engines observed (Phase 1 §K)
~12 per-workflow engines; no central engine.

### C.2 Status vocabulary uniqueness
**23 distinct status strings** observed (deduped across casing):

| Lowercase | Capitalised present? |
|---|---|
| active | yes (`Active`) |
| cancelled | yes (`Cancelled`) |
| closed | yes (`Closed`) |
| complete |  |
| delayed |  |
| disabled |  |
| done |  |
| draft |  |
| expired |  |
| idle | yes (`Idle`) |
| in_progress |  |
| inactive |  |
| live |  |
| locked |  |
| new |  |
| offline |  |
| open | yes (`Open`) |
| pending |  |
| rejected | yes (`Rejected`) |
| scheduled |  |
| submitted | yes (`Submitted`) |
| verified | yes (`Verified`) |
| working | yes (`Working`) |

→ **Mixed case in the same vocabulary** (`active` vs `Active`, `open` vs `Open`, etc.) — recording as inventory variance.

### C.3 Overlapping verbs across engines
| Verb | Engines that use it |
|---|---|
| `open` | Incident · CAPA · Operations Actions · Safety items |
| `closed` | Incident · CAPA · Operations Actions |
| `submitted` | Daily Report · Site Inspection · Safety Meeting · Incident · Equipment Inspection · JHA · ODR |
| `idle` | Dispatch Asset · Operations Map asset band |
| `offline` | Dispatch Asset · Operations Map feed_status · Driver session |
| `live` | Operations Map feed_status only |
| `working` | Dispatch Asset · Operations Map band |
| `green / amber / red / gray` | Operations Map band system (4-color, separate vocabulary) |
| `expired / 30d / 60d / 90d / ok` | Document Expirations (5-stage, separate vocabulary) |
| `requested / approved / denied` | Time Off · Transfer Request · PO Request |

### C.4 Closure verbs vary by workflow
- Incident: `closed`
- Operations Action: `done` **and/or** `closed`
- Equipment Inspection: `signed_off`
- ODR: `final` **and/or** `amended`
- Backup drill: `success` **or** `failed`
- Time Off: `approved` / `denied` (no neutral `closed`)
- Document expiration: no closure verb — state simply rolls to `ok`

### C.5 Conflicting meanings (observed)
- **`offline`** means three different things:
  - Operations Map feed_status: *no recent updates from Motive webhook*
  - Driver session: *driver hasn't checked in*
  - Dispatch asset band-derived state: *asset hasn't moved in N hours*
- **`active`** means:
  - Employee: *currently employed*
  - Job: *not deleted/archived*
  - JHA: *not archived*
  - User account: *not deactivated*
- **`open`** means:
  - Incident: *not yet closed*
  - CAPA: *corrective action outstanding*
  - Operations Action: *not yet assigned/completed*
  - Safety item: *needs attention*
  - Inspections list: sometimes used for *unsigned*

### C.6 Status-chip components per workflow
15 distinct components handle status rendering (§A.5). Two have the same name (`StatusBadge.jsx` at root and at `oa/`) but different chip schemas. Whether they produce visually identical chips is not measured in this discovery phase.

---

## D. Findings index (variance type → location → evidence)

| # | Variance type | Where | Evidence |
|---|---|---|---|
| V-01 | Theme drift | ShopHub header amber-500/700/300 vs Shop tile orange-600/700 | `portalPalette.js` source comment §A.2 |
| V-02 | Theme drift | PmHub tile-CTA amber vs PM canonical indigo | `portalPalette.js` source comment §A.2 |
| V-03 | Theme overlap | Field Leadership red-700 overlaps with Admin/Leadership brand-red | `portalPalette.js` §A.2 |
| V-04 | Token system unwired | `tokens.css` exists as PROPOSAL, components still hardcode Tailwind colors | `tokens.css` header §A.1 |
| V-05 | Hub size variance | Hub files range 145 → 668 lines (4.6× spread) | grep wc-l §A.3 |
| V-06 | Header pattern variance | ≥ 4 different portal-header strategies | grep §A.4 |
| V-07 | Status-chip sprawl | 15 distinct status/badge components, 2 share filename | find §A.5 |
| V-08 | Cross-portal tile leakage | OA-1 tile still on 6 portals; HR removed in 13.4A | Phase 1 §I + Track 13.4A §8 |
| V-09 | Command-center sprawl | 8 distinct *Command/Center pages | Phase 1 §D |
| V-10 | Status case drift | Mixed `Open`/`open`, `Active`/`active` etc. | §C.2 |
| V-11 | Status verb overload | `offline`, `active`, `open` each mean ≥ 3 different things across engines | §C.5 |
| V-12 | Closure verb drift | `closed`, `done`, `signed_off`, `final`, `success`, `approved` — no shared closure verb | §C.4 |
| V-13 | Mobile evidence gap | Only Track 13.4A surfaces have iPad screenshots; remaining 22 portal landings desktop-only | §A.8 |
| V-14 | Public surface chrome drift | Each public form has its own header chrome | §A.7 |
| V-15 | Driver portal landing missing as static page | Inventory could not locate a static driver landing page | §B.2 |

---

## E. What this audit did NOT do
- Did not score any variance (Phase 2 scoring is post-discovery).
- Did not recommend changes.
- Did not propose a Design System V1.
- Did not modify any source code.
- Did not capture mobile / iPad screenshots for the 22 new portal landings (deferred).
- Did not enumerate every form field for typography consistency.
- Did not run pixel-level visual diffs between portal landings.

All of the above are intentionally deferred to later phases.

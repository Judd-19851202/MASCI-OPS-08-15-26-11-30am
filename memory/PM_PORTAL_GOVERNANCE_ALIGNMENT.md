# PM Portal Governance Alignment — Phase IV-BETA.1

**Iteration:** iter437 · Phase IV-BETA · 2026-02
**Status:** 🟢 DOCTRINE LOCKED · GROUNDED IN `PM_PORTAL_CURRENT_STATE_AUDIT.md`
**Inherits from:** `ADMIN_UX_GOVERNANCE.md` · `OPERATIONAL_VERBIAGE_DOCTRINE.md` · `COMMUNICATION_TONE_STANDARD.md` · `MOBILE_NAVIGATION_STANDARD.md` · `COMPONENT_HIERARCHY_STANDARD.md` · `VISUAL_LOUDNESS_REDUCTION_PLAN.md`

This document binds the PM portal to the Phase IV-A governance doctrine. Every rule below derives from a doctrine rule that already governs the Admin portal — applied to PM operational realities documented in the audit.

---

## I. The five alignment principles

| Principle | What it means for PM portal |
|---|---|
| **1. Same doctrine, same voice** | Every rule that governs Admin (verbs, nouns, severity, tone, hierarchy, loudness) applies identically to PM. No portal-specific exceptions. |
| **2. Preserve PM operational speed** | Per audit §9, PMs depend on specific surfaces (Crew Compliance card, OperationsCenter, PmHaulActivity, Dispatch Lifecycle, deep-link integrity). The refactor enhances these — it does not displace them. |
| **3. Hierarchy mirrors operational frequency** | Per audit §8, Class-A shift-critical work (Daily Reports, Inspections, Incidents) must surface in the sidebar — not buried in Hub tiles. |
| **4. Three modes, one surface** | Office-deep · Field-glance · Interruption-driven. Per audit §11, no mode is optimized at the expense of another. |
| **5. Cross-portal continuity** | A PM who also has admin privileges (typical) must feel zero cognitive switch when moving between portals. Same drawer, same tier ladder, same severity language. |

---

## II. PM domain structure (the canonical 6-domain map)

Per `PM_INFORMATION_PRIORITY_MAP.json` (companion artifact this phase) and grounded in audit §1–2:

| Stripe | Domain | Coaching subline | Operational frequency |
|---|---|---|---|
| 🟥 red | **PROJECT OPERATIONS** | Field activity across your assigned projects. | shift-critical |
| 🟦 blue | **FINANCIALS & COST** | Purchase orders, change exposure, budget signals. | daily |
| 🟨 amber | **FIELD COORDINATION** | RFIs, subcontractors, materials, logistics. | daily |
| 🟪 violet | **DOCUMENT CONTROL** | Drawings, specs, JHAs, trench boxes, posters. | weekly |
| 🟧 orange | **COMPLIANCE & RISK** | Incidents, QA/QC, audits, crew compliance. | shift-critical (incidents) · weekly (rest) |
| ⬛ slate | **SYSTEM & COMMUNICATIONS** | Email routing, notification preferences, escalations. | weekly |

The order mirrors PM operational rhythm — most-used first, infrastructure last — matching the Admin V2 ladder.

---

## III. Domain content (which existing routes belong where)

Every route below is one that already exists in the audited PM portal. No new routes are introduced this phase.

### Project Operations (red stripe)

| Route | Label | Doctrine subline |
|---|---|---|
| `/pm` | Overview | Today's signal across your assigned projects. |
| `/pm/jobs` | Jobs | Active jobs assigned to you · master list. |
| `/pm/daily` | Daily Reports | Field production, manpower, operational progress. |
| `/pm/inspections` | Inspections | Field safety and quality checks. |
| `/pm/meetings` | Meetings | Pre-shift, toolbox, project, management meetings. |
| `/pm/field-leadership` | Field Leadership | Crew documentation across your assigned projects. |
| `/pm/photos` | Job Photos | Field photos by job and week. |

### Financials & Cost (blue stripe)

| Route | Label | Doctrine subline |
|---|---|---|
| `/po-requests` | PO Requests | Pending approvals and financial exposure. |
| `/project-health` | Project Health | Operational friction by job. |
| `/asset-transfers` | Asset Transfers | Equipment movement and lifecycle. |

### Field Coordination (amber stripe)

| Route | Label | Doctrine subline |
|---|---|---|
| `/pm/fleet` | Equipment Fleet | Asset status board, master roster, parts. |
| `/pm/equipment` | Pre-Op Checks | Today's pre-shift checks across your fleet. |
| `/pm/suppliers` | Suppliers | Approved supplier roster (read-only). |
| `/pm/people` | People | Employee master (read-only). |

### Document Control (violet stripe)

| Route | Label | Doctrine subline |
|---|---|---|
| `/pm/jha-plans` | JHA Plans | Job hazard analyses by asset and task. |
| `/pm/trench-boxes` | Trench Boxes | Box specifications and inspections. |
| `/pm/posters` | Site Posters | Printable JHA, trench box, and inspection QRs. |

### Compliance & Risk (orange stripe)

| Route | Label | Doctrine subline |
|---|---|---|
| `/pm/incidents` | Incidents | Open and recent safety/quality deviations. |
| `/pm/qaqc` | QA/QC | Quality records across your assigned projects. |
| `/pm/crew-compliance` | Crew Compliance | Training, PPE, CAPA exposure, expirations. |
| `/pm/compliance-export` | Compliance Export | Date-range CSV for audits and insurance reviews. |

### System & Communications (slate stripe)

| Route | Label | Doctrine subline |
|---|---|---|
| `/pm/routing` | Email Routing | Active auto-routing rules (admin-edited). |
| `/pm/change-password` | Change Password | Rotate your sign-in credentials. |

### Footer rail (cross-portal pinned — matches Admin V2)

| Route | Label | Doctrine subline |
|---|---|---|
| `/tasks` | My Tasks | Action items across all domains. |
| `/guidance` | Guidance | Doctrine, SOPs, training. |

PO Requests appears in Financials & Cost rather than footer rail (PM-specific operational placement — PMs spend more time in PO than non-PM portals do).

---

## IV. Visual treatment (binding)

All rules from `COMPONENT_HIERARCHY_STANDARD.md` apply. PM-specific bindings:

| Element | Specification |
|---|---|
| Sidebar stripe (Project Operations) | `#dc2626` red-600 · 2 px wide |
| Sidebar stripe (Financials & Cost) | `#2563eb` blue-600 · 2 px wide |
| Sidebar stripe (Field Coordination) | `#d97706` amber-600 · 2 px wide |
| Sidebar stripe (Document Control) | `#7c3aed` violet-600 · 2 px wide |
| Sidebar stripe (Compliance & Risk) | `#ea580c` orange-600 · 2 px wide |
| Sidebar stripe (System & Communications) | `#475569` slate-600 · 2 px wide |
| Active sub-entry background | `bg-slate-800 text-white` (NOT `bg-amber-600` — eliminated) |
| Top-bar bottom border | `border-b border-slate-800` (1 px · was `border-b-4 border-amber-600`) |
| Top-bar breadcrumb color | `text-slate-300` (was `text-amber-300`) |
| Active-domain row background | `bg-slate-800/60` (matches Admin V2) |

**The saturated amber-600 active state is ELIMINATED.** Amber is reserved for the FIELD COORDINATION stripe and for severity-amber Tier-2 banners — nowhere else in PM chrome.

---

## V. Hub overview restructuring

Per audit §4 (loudness sources) and §9 (strengths to preserve), the PM Hub is restructured as:

```
┌─ Tier 0 · Today signal banner ──────────────────────────┐
│   (Only when ≥ 1 Tier 2+ items demand attention)         │
├─────────────────────────────────────────────────────────┤
│ Tier 2 · H1 "Overview" + coaching subline                │
├─────────────────────────────────────────────────────────┤
│ Tier 1 · OperationsCenter (compact KPI block)            │   ← preserved
├─────────────────────────────────────────────────────────┤
│ Tier 1 · Crew Compliance card (4-tile summary)           │   ← preserved
├─────────────────────────────────────────────────────────┤
│ Tier 2 · "Today" section · Daily Reports / Inspections   │
│         / Incidents quick-action tiles (3 max)           │
├─────────────────────────────────────────────────────────┤
│ Tier 3 · Coordination strip · Tasks · PO Requests ·      │
│         Project Health · Asset Transfers (4 tiles)       │
├─────────────────────────────────────────────────────────┤
│ Tier 3 · PmHaulActivityTile                              │   ← preserved
├─────────────────────────────────────────────────────────┤
│ Tier 3 · DispatchLifecycleTile                           │   ← preserved
├─────────────────────────────────────────────────────────┤
│ Tier 4 · LastActivityLine                                │   ← preserved
├─────────────────────────────────────────────────────────┤
│ Tier 5 · FieldMemoryGlance                               │   ← preserved · de-emphasized
└─────────────────────────────────────────────────────────┘
```

### What changes vs current

- The 15-tile grid is REMOVED (sidebar now carries that navigation).
- The Hub becomes a "today's operational signal" surface, not a feature list.
- Inline widgets reorder by tier (Operations & Compliance → quick actions → coordination → activity trace).
- PasskeyEnrollPrompt becomes a dismissible Tier 5 footer (or moves to /pm/change-password).

### What is preserved

- OperationsCenter · Crew Compliance card · PmHaulActivityTile · DispatchLifecycleTile · LastActivityLine · FieldMemoryGlance — all remain operational surfaces.

---

## VI. Mobile drawer iOS scroll fix (P0 from audit)

The PM `<SheetContent>` in `PmShell.jsx` line 108 MUST be refactored to the canonical drawer pattern from `MOBILE_NAVIGATION_STANDARD.md` §II:

```jsx
<SheetContent side="left" className="flex flex-col p-0 w-72 bg-slate-900">
  <SheetHeader className="shrink-0 px-4 pt-4 pb-2 border-b border-slate-800">
    <SheetTitle>…</SheetTitle>
  </SheetHeader>
  <div
    data-testid="pm-mobile-nav-scroll"
    className="flex-1 min-h-0 overflow-y-auto overscroll-contain"
    style={{ WebkitOverflowScrolling: "touch" }}
  >
    <SideNavV2 onNavigate={…} />
  </div>
</SheetContent>
```

This lands in Phase IV-BETA.1 alongside the V2 sidebar. A Playwright regression `test_pm_mobile_nav_scroll.py` mirrors the Admin test exactly, locking the fix.

---

## VII. Implementation phasing (locked, ≤ 200 LOC per sub-step)

| Step | Scope | Risk |
|---|---|---|
| **IV-BETA.0** (this iteration) | Inventory + 8 governance docs | NONE |
| **IV-BETA.1** | PM Sidebar V2 (additive, feature-flagged) · iOS scroll fix · Playwright regression | LOW |
| **IV-BETA.2** | Hub overview re-tiering · 15-tile grid retired · inline widgets reordered | MEDIUM |
| **IV-BETA.3** | Coaching sublines + verbiage cleanup · doctrine compliance | LOW |
| **IV-BETA.4** | Loudness reduction · saturated amber elimination · top-bar calm refactor | LOW |
| **IV-BETA.5** | Feature flag cut · legacy PM sidebar retired | MEDIUM |

Each sub-step ships behind the feature flag `masci.pm.sidebar.v2` (same mechanism as Admin) and is independently reversible.

---

## VIII. Operator-trust principles for PM portal

1. **A PM signing in tomorrow knows where every surface is.** No surface is hidden, renamed, or removed without an in-portal redirect.
2. **A PM scanning the new sidebar in 2 seconds knows what each domain owns.** Coaching sublines carry that load.
3. **A PM whose only daily destination is Daily Reports reaches it in ≤ 2 taps.** Sidebar → Project Operations (auto-expanded) → Daily Reports.
4. **A PM hit with an Escalation push lands on the actionable surface, not the Hub.** Deep-link integrity preserved.
5. **A PM switching to Admin (or back) experiences identical chrome.** Same drawer, same tier ladder, same severity language.

---

## Verdict

🟢 **PM GOVERNANCE ALIGNMENT LOCKED.** The PM portal now has a binding doctrine that mirrors Admin, respects PM operational realities (per audit), and lands incrementally behind a feature flag. Implementation begins in IV-BETA.1.

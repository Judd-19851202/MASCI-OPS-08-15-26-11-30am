# MASCI Platform — UX Governance Rules
*Established 2026-05-21 · paired with `UX_GOVERNANCE_AUDIT.md` and `UX_REFINEMENT_ROADMAP.md`*

These are the **platform-wide visual & UX standards** that bounded refinement passes must honor. Modeled directly on the iter317-C Part 2 HR Hub refinement (the calm reference target) and on `STABILIZATION_PRINCIPLES.md` (the operational posture).

**The platform's greatest strength is operational directness. Every rule below exists to amplify that — never to obscure it with style.**

---

## RULE 1 · Card weight & border treatment

**Default tile**: `bg-white border border-slate-200 border-l-4 border-l-<accent> rounded-md p-5`
- Soft full border + left-edge accent stripe for identity recognition.
- NO full hot borders (`border-2 border-<accent>-500`) on tile grids.
- NO `bg-<accent>-50` tile fills (the colored backgrounds add visual heat without information).

**Hover state**: `hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300 transition-all duration-150` — preserve the muscle-memory micro-interaction.

**Allowed exceptions**:
- Warning banners (e.g. duplicate detection, blocked items): `border-2 border-amber-300 bg-amber-50` — these need the heat to grab attention.
- Primary danger alerts: `border-2 border-red-300 bg-red-50` — same rationale.
- Inline coaching tips / HelpTipBlocks: use their own existing chrome (do not refactor).

---

## RULE 2 · Color semantics (platform-wide)

**Operational color = meaning. Reserved palette below. No reuse outside the role.**

| Color | Meaning | Use for |
|---|---|---|
| **Red** | Danger · action needed · must-fix | Incidents · payroll variance · overdue items · destructive actions · termination paths |
| **Amber** | Caution · review needed · pending | Tasks · coaching · attention items · pending approvals · time-off pending |
| **Emerald** | Verified · success · operational-good | Lifecycle (employee active) · time verification · QA/QC · cleared-to-operate |
| **Blue** | Operational tool · informational | Field Leadership Records · neutral operational surfaces |
| **Cyan** | Safety identity | Safety Portal · safety records · safety-owned tiles |
| **Purple** | HR identity | HR Portal · HR-owned tiles · FL portal accounts (HR-managed) |
| **Indigo** | PM identity / planning | PM Portal · PO Requests (PM-issued) · planning/projection |
| **Orange** | Shop / mechanic identity | Shop · maintainability · MaintainX integration |
| **Slate / gray** | Secondary · supporting · neutral | Guidance · reference · integrations · meta-information |
| **Rose** | Documentation lifecycle | Document expirations · document-driven workflows |

**Portal identity colors are reserved** — Cyan = Safety, Purple = HR, Indigo = PM, Orange = Shop, Amber = Dispatch, Red = brand/Admin/Leadership. Tiles on a portal page may use other semantic colors (e.g., red for danger on a cyan Safety hub) but must NOT use another portal's identity color for non-identity meaning.

**Color count per hub**: aim for ≤ 5 distinct accent colors per visible surface. The rest go gray/slate.

---

## RULE 3 · Hierarchy & typography

### Page-level hierarchy
| Surface | H1 size | Notes |
|---|---|---|
| Public landing (`/`, `/sign-in`, `/leadership/login`) | `text-4xl sm:text-5xl lg:text-6xl` | Loud OK — these are doors |
| Interior signed-in hubs | **`text-3xl sm:text-4xl`** | The HR rule — calm and operational |
| Interior sub-pages | `text-2xl sm:text-3xl` | Quieter — supports the breadcrumb |
| Modal / drawer headings | `text-xl` | Compact |

### Tile-level hierarchy (grid cards)
- Tile H3: `font-display text-lg font-black` (calm, the HR rule)
- Tile description: `text-sm text-slate-600` (NOT `text-slate-700` — too dark)
- Tile CTA chip: `font-bold uppercase tracking-wide text-xs` in tile color
- Icon: `w-6 h-6 text-slate-700` (NOT a giant colored chip — the left stripe carries the color signal)

### Section heading (within a hub)
```
<h2 class="font-mono text-xs uppercase tracking-[0.22em] text-slate-700">{TITLE}</h2>
<span class="h-px flex-1 bg-slate-200" />
<span class="text-xs text-slate-500 italic">{subtitle}</span>
```

Demoted/supporting sections (e.g. Integrations): use `text-slate-500` for the heading + a `border-t border-slate-200 pt-6` separator above the section.

---

## RULE 4 · Grouping logic (every hub with ≥ 6 tiles)

Standard operational groups (when present, render in this order):
1. **Primary [Portal] Actions** — the daily-driver workflows
2. **Compliance & Accountability** — records, reviews, audits
3. **Payroll / Time** — payroll, time, expense (HR only typically)
4. **Operations & Spending** — purchasing, equipment, fleet
5. **Integrations & Systems** *(visually demoted)* — guides, integration health, training center

Hubs with < 6 tiles may skip grouping and use a flat 2-col grid.

---

## RULE 5 · KPI / stat blocks

**One unified pattern**: subdued surface, no hot borders, restraint on color.

```jsx
<div className="bg-white border border-slate-200 rounded-md p-4">
  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
  <div className="font-display text-3xl font-black text-slate-900 mt-1 leading-none">{value}</div>
  {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
</div>
```

- KPIs **inform** — they should not dominate the page.
- A KPI may use a colored value (`text-red-700` for overdue counts, `text-emerald-700` for verified counts) but the chrome stays neutral.
- KPI grids: `grid grid-cols-2 md:grid-cols-4 gap-3` standard. NO `border-2`. NO hot accent bg.
- A SafetyHub-style 8-card grid is OK when there's genuine breadth — but only one row of bold values, the rest stay quiet.

---

## RULE 6 · Integration placement (Motive · MaintainX · external systems)

**Integrations must support the page, not compete with it.**

- Place integration health/events cards **at the bottom** of the hub, **below** all operational sections, **after** a top-border separator (`border-t border-slate-200`).
- Visually demoted: `text-slate-500` heading, neutral chrome, supporting role.
- Tabs-as-burial (Dispatch · Shop "Integrations" tab) is acceptable when the hub is tab-driven by design, but the tab label should be `Integrations` not `Plug · Integrations` — quieter.

---

## RULE 7 · Header chrome (signed-in interior hubs)

**Canonical**:
- Container: `max-w-6xl mx-auto px-5 sm:px-8 py-4`
- BG: `bg-slate-900 border-b-4 border-<portal-identity>`
- Caution stripe + `blueprint-bg` body background
- Left cluster: Home · Back · Logo
- Right cluster (in this order): PortalSwitcher · GlobalSearch · NotificationBell · OfflineIndicator · LangToggle · CompanyInfo · Password · SignOut
- **iter203 mobile collapse** mandatory: hide `PortalSwitcher` · `GlobalSearch` · `CompanyInfo` · `Password` · `Guides` link below `sm:`. Keep NotificationBell · Offline · LangToggle · SignOut visible.

**Exceptions**:
- Public Home `/` and `/sign-in` keep their lighter chrome (no `Home/Back` because they ARE home).
- AdminShell / PmShell sidebars have their own chrome and don't follow this rule.

---

## RULE 8 · Operational tone (wording)

**Reject**: stakeholder · journey · best practices · empower · culture of · learning module · compliance pathway · seamless · synergy · leverage · ecosystem · holistic.

**Prefer**: direct verbs · field-usable nouns · operational specifics.

**Style**:
- Page headlines: 4–7 words, what the page IS, not what it does for you.
- Tile descriptions: one operational sentence, ≤ 25 words, joins workflow items with ` · `.
- Button labels: 1–3 words, uppercase, present-tense imperative (`OPEN`, `SAVE`, `SIGN OUT`).
- Section subtitles: italic, slate-500, ≤ 12 words.

**Bilingual**: every visible string MUST flow through `t()`. The `useT()` hook provides `{t, lang}` — never call `useT()` as a function. ES parity is a release gate.

---

## RULE 9 · Mobile / tablet behavior

**Required**:
- All hub grids: `grid grid-cols-1 sm:grid-cols-2` (or `lg:grid-cols-3` for dense hubs). NEVER skip the 1-col mobile state.
- Touch targets: minimum 40px tap height.
- Headers: `flex-wrap` with iter203 collapse pattern (Rule 7).
- No `max-w-7xl` interior hubs (forces unwanted horizontal scroll at narrow tablet widths).
- No fixed widths on modal/dialog content.
- Test viewports for any hub change: Desktop 1920 · iPad 1024 · Mobile 390. Take three screenshots and visually verify before merging.

---

## RULE 10 · Sidebar vs flat hub

**Use a sidebar (AdminShell / PmShell) when**:
- Hub has ≥ 15 distinct admin-level sub-sections.
- User is power-user / desk-bound (Admin, PM).
- Sub-sections are routinely deep-linked from other portals.

**Use a flat hub when**:
- Hub has 4–14 destinations.
- Primary user is field-facing or task-driven (HR, Safety, Shop, Dispatch, Leadership).
- One-tap entry from QR / shortcut is operationally important.

**Never convert a flat hub to a sidebar without explicit operator approval.** The muscle-memory cost is non-trivial.

---

## RULE 11 · Empty states & error states

**Empty state (no records yet)**:
- Center-aligned within the panel.
- Single line of slate-500 text describing what would appear here.
- Optional: one quiet CTA to the form that creates the missing record.
- NEVER: illustrations, mascots, or apologetic phrasing.

**Error state (failed load)**:
- Inline red-700 text inside the panel that should have held the data.
- Single concrete actionable next step (`Sign out and back in`, `Retry`, `Contact admin`).
- Admin surfaces fail visibly (red banner, `toast.error`); crew-facing surfaces may fail quietly if the operational risk is low.

---

## RULE 12 · Stabilization discipline (the meta-rule)

Every visual refinement must satisfy ALL of the following before shipping:
1. Bounded scope — touches one hub or one component family, not the whole platform at once.
2. No workflow change — identical clicks, identical destinations, identical operational meaning.
3. No testid renames or removals — regression contract preserved.
4. Bilingual `t()` calls preserved.
5. Hover micro-interaction preserved (`hover:-translate-y-0.5 hover:shadow-md`).
6. Screenshot verification at 1920 · 1024 · 390 viewports.
7. Combined regression pytest pass on iter314+316+317-A/B/C/(this iter).
8. New invariant test added that locks the new visual contract.

**If a refinement cannot satisfy all 8, it does not ship in this phase.**

---

## RULE 13 · What this governance does NOT do

- Does NOT mandate dashboard gimmicks (no animated stats, no skeleton loaders with shimmer, no parallax).
- Does NOT introduce dark-mode / theme switching (operator has not asked).
- Does NOT introduce accordions, collapsibles, drawers where flat layout works.
- Does NOT add navigation complexity (mega-menus, hover menus, breadcrumbs deeper than 2 levels).
- Does NOT remove functionality, rename routes, or change permissions.
- Does NOT refactor working hubs for "purity" — only addresses the documented inconsistency findings.

---

## Reference: the calm tile contract (HR · iter317-C Part 2)

```jsx
<Link
  to={tile.to}
  className="block rounded-lg border border-slate-200 border-l-4 border-l-<accent>
             bg-white p-5 hover:shadow-md hover:-translate-y-0.5
             hover:border-slate-300 transition-all duration-150 relative"
  data-testid={`<portal>-tile-${tile.to.split('/').pop()}`}
>
  {badge > 0 && <span className="absolute top-3 right-3 ..." />}
  <div className="flex items-start gap-3">
    <tile.icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
    <div className="flex-1 min-w-0">
      <h3 className="font-display text-lg font-black">{t(tile.label)}</h3>
      <p className="text-sm text-slate-600 mt-1">{t(tile.desc)}</p>
      <span className="mt-3 inline-flex items-center h-9 px-3 rounded-md
                       bg-<accent>-700 text-white font-bold uppercase
                       tracking-wide text-xs">
        {t("OPEN →")}
      </span>
    </div>
  </div>
</Link>
```

This is the canonical pattern. Every hub-tile refinement targets this shape.

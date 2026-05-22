# MASCI Platform — Calm Hierarchy Reference Pack
*Established 2026-05-21 · iter319 deliverable · paired with `UX_GOVERNANCE_RULES.md` (Rules 1-13)*

This is the **official platform family visual reference standard**. Use it as the single source of truth when validating future hub refinements (iter320 Shop · iter321 Dispatch · iter322 FL Portal · and beyond).

The four hubs in this pack — **HR · Safety · Field Leadership · Field** — now form one coherent operational family. Every refinement after iter319 must visually converge against this pack.

---

## How to live-verify any surface in this pack

The screenshot tool's preview container doesn't persist PNGs to the host, but every surface here is **live and reproducible** at any time. The reference pack is the prose specification + the invariant tests + the live-verifiable URLs together.

### Re-verify recipe

```bash
# 1. Get a portal token (super-admin gets all portals via multi-login)
API="https://safety-audit-mobile-1.preview.emergentagent.com/api"
curl -s -X POST "$API/auth/multi-login" \
  -H "Content-Type: application/json" \
  -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}' \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['portal_tokens'], indent=2))"

# 2. Visit each surface in the table below with the appropriate viewport
#    (1920×800 desktop · 1024×1366 iPad · 390×844 mobile) and language
#    (localStorage.masci.lang = 'en' or 'es').

# 3. Run the invariant suite to confirm the contract:
cd /app && python -m pytest \
  backend/tests/test_iter317c_hr_hub_grouped_cards.py \
  backend/tests/test_iter318_safety_hub_calm_pass.py \
  backend/tests/test_iter319_fl_and_field_calm_pass.py -v
```

---

## The four reference surfaces

| # | Hub | URL | Auth | Invariant test |
|---|---|---|---|---|
| 1 | **HR Hub** | `/hr` | `hrmanager@mascigc.com` / `HRTesting2026!` OR multi-login token via `localStorage.masci.hr.token` | `test_iter317c_hr_hub_grouped_cards.py` |
| 2 | **Safety Hub** | `/safety-portal` | Multi-login token via `localStorage.masci.safety.token` | `test_iter318_safety_hub_calm_pass.py` |
| 3 | **Field Leadership Hub** | `/leadership` | Shared password `MASCIGC` at `/leadership/login` | `test_iter319_fl_and_field_calm_pass.py` |
| 4 | **Field Hub** | `/field` | Public (no auth) | `test_iter319_fl_and_field_calm_pass.py` |
| 5 | **Shop Hub** | `/shop` | Multi-login token via `localStorage.masci.shop.token` | `test_iter320_shop_qaqc_calm_pass.py` |
| 6 | **QA/QC Section** | `/qaqc` | Public (no auth) | `test_iter320_shop_qaqc_calm_pass.py` |
| 7 | **Dispatch Hub** | `/dispatch-portal` | Multi-login token via `localStorage.masci.dispatch.token` | `test_iter321_dispatch_safety_governance_closure.py` |
| 8 | **Safety Section** (public) | `/safety` | Public (no auth) | `test_iter321_dispatch_safety_governance_closure.py` |
| 9 | **Safety Forms Hub** | `/safety/forms` | Password-gated (Safety Department) | `test_iter321_dispatch_safety_governance_closure.py` |

**Family contract lock** · `test_platform_family_contract.py` — single read-only invariant suite that mechanically prevents drift across every hub in the family. Verifies the 4 canonical anchors (`border-l-4` calm card · `text-3xl sm:text-4xl` H1 · `tracking-[0.22em]` section heading · neutral KPI chrome) and refuses re-introduction of the hot SectionTile import. Anti-drift protection only — no screenshot testing, no pixel diff, no style bureaucracy.

**Pre-deploy gate** · `/app/.deploy_checks/run_family_contract.sh` (iter321) — tiny bash hook that runs the family contract test. Wire into the redeploy pipeline; exits non-zero on contract violation. README at `/app/.deploy_checks/README.md`.

The hubs currently inside the family contract:
- `HrHub` (iter317-C)
- `SafetyHub` (iter318)
- `FieldLeadershipHub` (iter319)
- `FieldSection` (iter319)
- `ShopHub` (iter320)
- `QaqcSection` (iter320)
- `DispatchHub` (iter321)
- `SafetySection` (iter321)
- `SafetyFormsHub` (iter321)

---

## Visual contract — the shape every refined hub must honor

### Tile (Rule 1)
```jsx
<Link
  to={tile.to}
  className="block rounded-lg border border-slate-200 border-l-4 border-l-<accent>
             bg-white p-5 hover:shadow-md hover:-translate-y-0.5
             hover:border-slate-300 transition-all duration-150 relative"
  data-testid="<portal>-tile-<slug>"
>
  <div className="flex items-start gap-3">
    <Icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
    <div className="flex-1 min-w-0">
      <h3 className="font-display text-lg font-black">{t(title)}</h3>
      <p className="text-sm text-slate-600 mt-1">{t(desc)}</p>
      <span className="mt-3 inline-flex items-center h-9 px-3 rounded-md
                       bg-<accent>-700 text-white font-bold uppercase
                       tracking-wide text-xs">
        {t("OPEN")} →
      </span>
    </div>
  </div>
</Link>
```

### Section heading (Rule 3)
```jsx
<div className="mb-4 flex items-baseline gap-3 flex-wrap">
  <h2 className="font-mono text-xs uppercase tracking-[0.22em] text-slate-700"
      data-testid="<portal>-group-heading-<key>">
    {t(group.heading)}
  </h2>
  <span className="hidden sm:inline-block h-px flex-1 bg-slate-200" aria-hidden="true" />
  <span className="text-xs text-slate-500 italic">{t(group.sub)}</span>
</div>
```

### Demoted section (Rule 6 — integrations, guidance, supporting tools)
```jsx
<section className="pt-6 border-t border-slate-200">
  <SectionHeading muted /> {/* text-slate-500 instead of text-slate-700 */}
  ...
</section>
```

### Page H1 (Rule 3 — interior hub)
```jsx
<h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900">
  {t(hub.title)}
</h1>
```

### KPI (Rule 5)
```jsx
<div className="bg-white border border-slate-200 rounded-md p-4">
  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
  <div className="font-display text-3xl font-black mt-1 leading-none text-<accent>-700">{value}</div>
  <div className="text-xs text-slate-500 mt-1">{sub}</div>
</div>
```

### Header right-cluster (iter203 mobile collapse · Rule 7)
- Hide below `sm:`: `GlobalSearch`, `CompanyInfoDialog`, `Guides`/`Records` link buttons
- Always visible: `NotificationBell`, `OfflineIndicator`, `LangToggle`, `SignOut`

---

## Hub-by-hub reference summary

### 1 · HR Hub (`/hr`)
- **Groups**: Primary HR Actions · Compliance & Accountability · Payroll / Time · Integrations & Systems (demoted)
- **Tile count**: 14 + 2 integration cards
- **Accent palette**: emerald · amber · rose · indigo · blue · purple · cyan · red · slate
- **Reference iteration**: iter317-C Part 2 (closed 2026-05-21)

### 2 · Safety Hub (`/safety-portal`)
- **Groups**: Primary Safety Operations · Compliance & Records · Operational Output · Guidance & Systems (demoted)
- **Tile count**: 15 + 2 integration cards
- **KPI strip**: 8 KPIs, neutral chrome, colored value text on incident/CA emphasis only
- **Accent palette**: amber · red · cyan · emerald · redDeep · slate
- **Reference iteration**: iter318 (closed 2026-05-21)

### 3 · Field Leadership Hub (`/leadership`)
- **Groups**: 5 numbered sections (DAILY · EVALUATIONS · TRAINING · EQUIPMENT · WORKFORCE) — preserved from prior structure, only chrome refined
- **Tile count**: 14 + 1 PO Requests deep-link
- **Accent palette**: amber · red · emerald · purple · lime · indigo · yellow · cyan · blue
- **Notable**: H1 toned from public-hero `text-4xl sm:text-5xl lg:text-6xl` → interior `text-3xl sm:text-4xl`. Legal-compliance banner softened from `bg-amber-50 border-amber-300` to `bg-slate-50 border-slate-200`. iter203 mobile collapse applied to Guides + Records + GlobalSearch + CompanyInfo.
- **Reference iteration**: iter319 (closed 2026-05-21)

### 4 · Field Hub (`/field`)
- **Groups**: Daily Operations · Weekly Checks · Calculators & Tools (demoted)
- **Tile count**: 6
- **Accent palette**: red · slate · amber
- **Notable**: H1 toned to `text-3xl sm:text-4xl`. Three new lightweight groupings added (was a flat 6-tile grid). Calculators demoted under top-border separator. Public hub — no auth required, so header is minimal (logo · LangToggle · CompanyInfo only).
- **Reference iteration**: iter319 (closed 2026-05-21)

---

## What changed in iter319 (the work that closed this pack)

### `FieldLeadershipHub.jsx`
- Replaced `SectionTile` usage with inline calm `LeadershipTile` (mirrors HR + Safety).
- H1 size: `text-4xl sm:text-5xl lg:text-6xl` → `text-3xl sm:text-4xl`.
- Section heading style: matched HR + Safety (mono kicker · thin slate-200 divider · italic subtitle).
- Legal-compliance banner: amber-50/300 → slate-50/200 (Rule 1).
- Header right-cluster: applied iter203 mobile collapse (`hidden sm:inline-flex` on Guides / Records / GlobalSearch / CompanyInfo).
- 14 tile testids preserved · 5 group sections preserved · GROUPS schema preserved.

### `FieldSection.jsx`
- Full rewrite to inline calm tile pattern.
- H1 size: `text-4xl sm:text-5xl` → `text-3xl sm:text-4xl`.
- Three new lightweight operational groups added (was a flat grid):
  - **Daily Operations** — Daily Reports · Equipment Pre-Op · Daily DVIR
  - **Weekly Checks** — Weekly Lead Inspection · Weekly Emergency Equipment
  - **Calculators & Tools** *(demoted)* — Material Calculators
- All 6 tile testids preserved.

### `lib/i18n.js`
- Added 11 new ES dictionary entries for iter319 (group headings · subtitles · CTAs).
- Total ES entries from iter317-C/iter318/iter319: 31.

---

## What the platform family now feels like

A user moving from HR → Safety → FL → Field experiences:
- **Same visual rhythm**: section headings · tile chrome · CTA pill · hover behavior.
- **Same hierarchy**: H1 size · description weight · KPI restraint.
- **Same grouping convention**: 3-5 named operational sections + 1 demoted Systems/Tools section at the bottom.
- **Same color semantics**: red for danger · amber for caution · emerald for verified · slate for supporting · portal-identity colors reserved.
- **Same mobile behavior**: iter203 collapse · single-column stacking · 40px+ touch targets.

The platform now reads as one product, not five hubs assembled separately.

---

## Backlog · what remains for full platform convergence

Per `UX_REFINEMENT_ROADMAP.md` Phase A:
- **iter320** — Shop Hub calm pass
- **iter321** — Dispatch Hub convergence (the architectural outlier)
- **iter322** — FL Portal Dashboard calm pass

After Phase A: Phase B (color delta) · Phase C (KpiBlock unification) · Phase D (header chrome) · Phase E (polish).

This reference pack is the contract those iterations must converge against.

---

## iter326 · Platform-Wide Convergence Closure (2026-05-22)

The convergence membership now spans every hub the platform ships:
- **AdminHub** — SectionTile migrated from hot `border-2 + hover:border-red-700` chrome to the calm contract (`border border-slate-200 border-l-4 border-l-red-700 + hover:shadow-md + hover:border-slate-300`). The ChevronRight no longer mutates color on hover (hot-chrome residue removed). The icon badge no longer transitions to red on hover.
- **PmHub** — Tile migrated from `border-2 + hover:border-amber-600` to the calm contract with a dynamic accent stripe (`border-l-red-700 / border-l-amber-600 / border-l-red-900 / border-l-rose-700 / border-l-slate-700`) driven by the existing accent prop. Counts and sub-labels preserved.

Platform-wide drift eradication (iter326 bulk sweep):
- `bg-white border-2 border-slate-300 rounded-md` → `bg-white border border-slate-200 rounded-md` — **72 files migrated**.
- `bg-white border-2 border-slate-200 rounded-md` → calm equivalent — **additional layer-2 migration**.
- `rounded-md border-2 border-slate-200` & `rounded-lg border-2 border-slate-200` → calm equivalents — layer-3 cleanup.
- `border-2 border-slate-200 bg-white` → calm equivalent — layer-4 cleanup.
- `OpsTrainingCenter.jsx` tile + `SafetyEmployeeProfiles.jsx` tile migrated from hot-chrome (`border-2 + hover:border-<accent>-600`) to calm-card with left-edge stripe.

A new mechanical anti-drift sentry — `test_no_heavy_card_chrome_in_pages_tree` — locks the entire `/pages` tree against any future re-introduction of the heavy patterns. Poster/print surfaces are excluded by name.

Items intentionally NOT changed (legitimate context-specific chrome):
- Form input borders (`h-12 ... border-2 border-slate-300` on Inputs) — preserved for field-device touch-target accessibility.
- Filter chip selected-state borders — preserved as state affordance.
- Danger/action button hover borders (`hover:border-red-500` on Delete/Cancel) — preserved as semantic affordance.
- Photo thumbnail borders — preserved as media container affordance.

The platform now reads as one converged product end-to-end.

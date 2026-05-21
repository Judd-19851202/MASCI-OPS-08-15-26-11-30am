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

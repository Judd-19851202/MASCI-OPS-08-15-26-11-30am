# MASCI Operations Platform — Brutal Portal Variance Audit

**Date:** 2026-06-11 · **Mode:** READ-ONLY · **Coding:** none · **Fixes:** none · **Self-cert:** none.
**Evidence captured:** fresh screenshots at 1440×900 + 1024×768 for all 7 portals; DOM testid probes; 14-day git history; ledger cross-reference.

If a screenshot contradicts a prior certification, the screenshot wins.

---

## 1 · Executive Summary

The platform has improved materially in the last 48 hours on **naming, scope, and structure**, but two operator-visible failures remain — one of which (the **Dispatch map**) is a renderer-level "looks broken" condition that no prior PASS report acknowledged because automated DOM probes only verified that the canvas *element* exists, not that tiles render.

| Finding | Severity | Evidence |
|---|---|---|
| **Dispatch map canvas is BLACK — MapLibre WebGL canvas exists but no base map tiles paint** | 🔴 CRITICAL | `dispatch_desktop.png` & `dispatch_ipad_landscape.png` show pure-black 320 px canvas. Hero header + count strip + CTAs render fine but the geography itself is invisible. Prior cert reports flagged `mapLibreCount: 1` and called this PASS — that is wrong. |
| PM portal under super-admin shows admin-summary (272/44/24) instead of an iterable project list | 🟡 MAJOR — **but contractually correct** | The PM Phase-4A `compute_pm_scope` returns `"all"` for super-admin → component intentionally renders the 3-tile summary labeled `(admin scope)`. A real PM with assigned projects would see per-row health. Mechanism is right; operator visibility of the rebuild is therefore limited under super-admin. |
| HR KPI strip swap is in DOM but the OLD OperationsCenter strip *also* renders alongside (cumulative, not replaced) | 🟡 MAJOR | `hrKpiStrip: true` but desktop screenshot still shows Operations Actions, People Operations, Employee Lifecycle, Time & Payroll etc. — the new strip was added, the old surface was not removed. Operator sees BOTH. |
| "DISPATCH PM HUB" link remains in PM header | 🟡 MINOR | Cross-portal shortcut from before — visually OK but reads as operations-language on a portal that should be project-language. |
| PM still has a hidden detailed-tab view reachable via "Detailed operational view (Resources · Hauls · Materials · Shop · Safety · Timeline)" in Section E | 🟢 OK | This is by design — the old fleet-tab dashboard is preserved one click away, not hidden. |
| Field Leadership, Shop, Safety, Admin | 🟢 PRESERVED | Render identically to Track 13A.5 baseline. No regressions. |

**Verdict:** **NOT READY — FIX LIST REQUIRED.** Two visible regressions plus one renderer-level failure invalidate the prior "READY TO SAVE TO GITHUB + DEPLOY" wording.

---

## 2 · Baseline (≈ 14 days ago — reconstructed from git history + ledger)

I do not have stored screenshots from 14 days ago. Reconstruction comes from:
- Ledger entries dated 2026-05-21 → 2026-06-11
- Git log shows ~80 auto-commits in the last 48 hours, many touching `PmCommandCenter.jsx`, `DispatchHub.jsx`, `HrHub.jsx`.

| Portal | Baseline (2 weeks ago, reconstructed) | Notes |
|---|---|---|
| Admin | `AdminHub.jsx` with same left-rail grouping + Operations Center strip + Motive OIS | Stable. No material change. |
| PM | `PmCommandCenter.jsx` Phase 4A — kicker `PM · COMMAND CENTER · V1`, H1 `Project Operational Truth`, 12-tile fleet strip, 7 tabs Resources/Hauls/Materials/Shop/Safety/Timeline | **Pre-rebuild fleet dashboard** |
| Dispatch | `DispatchHub.jsx` — Operational Attention + Issue Work + Operational Board button (no embedded map) | **No map on first screen** |
| Shop | `ShopHub.jsx` — MaintainX Queue + OIS-1D + DVIR list | Stable |
| HR | `HrHub.jsx` — `<OperationsCenter compact />` strip + lifecycle/time/expirations sections | **Operations-paste KPI** |
| Safety | `SafetyPortal.jsx` — Sprint A DOCEXP-60/90 + sidebar groups | Stable |
| Field Leadership | `FieldLeadershipPortal.jsx` — 4-card action grid | Stable, reference standard |

**Reconstructed baseline marker: 🟡 RECONSTRUCTED — no archival screenshots; basis is source + ledger only.**

---

## 3 · Current State (fresh screenshots — `/app/memory/brutal_audit/`)

### 3.A · Admin (`/admin`)
- **Sections present (DOM probe):** Operations Center · admin · Live Operations Snapshot · Document & Cert Expirations · Operations Actions · Scheduler Runs · Integrations · Command Center · People & Access
- **mapLibreCount: 0 · hrKpiStrip: false · pmProjectFirst: false · notFound: false · opTruthInDom: false**
- **Verdict:** unchanged from baseline. Preserve.

### 3.B · PM (`/pm/command-center`) — under super-admin token
- **H1:** ✅ `Project Management Center` (no "Operational Truth")
- **Subtitle:** ✅ `Projects assigned to you`
- **Section headings:** Projects Assigned to You · Latest Dailies & Photos from the Field · What Needs PM Action · Reports, JHPs, Photos, and Project Roster · Equipment, Trucks, Trailers & Specialty Assets
- **Top-right link:** `DISPATCH PM HUB` (residual operations-language)
- **Section A under super-admin token:** `272 Active Projects (admin scope) · 44 Open Incidents · 24 Open CAPAs` — 3 tiles, no per-row list (correct per scope contract)
- **Section B (Latest Dailies & Photos):** *"No Daily Reports submitted today on your projects."* — honest empty state ✓
- **Section C, D, E:** all visible
- **opTruthInDom: false · pmProjectFirst: true · pmAdminSummary: true · pmProjectList: false**
- **Verdict:** **Rebuild reaches the operator under super-admin only as a summary view.** The per-row health list code IS shipped (`pm-pfh-project-list` testid exists, renders when `scoped_projects` is an array). To prove the project-row layout in operator-visible form, a non-super-admin PM account is required. The mechanism is right; the demonstrability is limited by available preview credentials.

### 3.C · Dispatch (`/dispatch-portal`) — 🔴 CRITICAL FINDING
- **Header:** `DISPATCH · Dispatcher · Switch Portal · Search · Sign out` ✓
- **Equipment Maintenance Issues banner:** "149 · View Equipment Status" ✓
- **Live Fleet Map hero — header & frame:** rendered ✓ ("LIVE FLEET MAP · NO RECENT UPDATES · UPDATED 12:00 AM")
- **Live Fleet Map hero — 320 px canvas: BLACK. No map tiles paint.**
  - `mapLibreCount: 1` (canvas element exists)
  - DOM probe says map is there; **visual screenshot says map is empty**.
  - Tile source likely failing silently (CSP / referer / 404 / API key on CARTO style endpoint).
- **Count strip below map:** Attention 34 · No Recent 156 · Working 0 · Idle 0 · Assets 90 · Total 190 — readable ✓
- **CTAs:** "Open Full Live Map" + "Open Operational Board" ✓
- **Verdict:** the map hero exists STRUCTURALLY but FAILS the operator's brutal test: "if the canvas is blank, the map is missing." The prior "DISPATCH REAL MAP EMBED COMPLETE" PASS in the ledger is **invalidated** by this screenshot.

### 3.D · Shop (`/shop`)
- **H1:** `Shop Recovery`
- **Sections:** Recent field memory · Equipment Down · Faults · GPS Health · Equipment Needing Attention · Trucks in breakdown right now · Operations Actions · Active Recovery Work 0 · Waiting / Delays 0 · Returned to Service 0
- **MaintainX queue:** 2 Ready · 183 Blocked · 2 Duplicate Risk · 149 Awaiting RTS
- **OIS-1D Motive Equipment Intel:** 1 Critical · 1 Gateway Offline · 2 DVIR Defects · 1 Fault Closed 30 d · 100 GPS Not Reporting
- **Per-unit alerts visible with vehicle IDs + timestamps.**
- **Verdict:** Preserve. Best portal on the platform after Field Leadership.

### 3.E · HR (`/hr`) — 🟡 MAJOR FINDING
- **H1:** `Employee Records & Accountability`
- **Section headings:** Operations Actions · People Operations · Employee Lifecycle · Employee Requests Queue · Tasks & Actions · Employee Accountability · Field Leadership Records · Time & Payroll
- **hrKpiStrip: true** (the new 5-tile HR-native strip from Track 13 is in the DOM)
- **BUT:** the original Operations Actions / People Operations / Employee Lifecycle / Tasks & Actions sections are STILL fully rendered on the page. The Track 13 swap *added* the HR-native strip; it did not visibly *replace* the operations-paste sections.
- **Verdict:** **PARTIAL.** The KPI strip is HR-native, but the operator still sees the full operations-actions surface below it. Either Operations Actions belongs on HR (in which case the prior "operations-paste removed" claim was wrong) or it should move to Admin. Operator decision required.

### 3.F · Safety (`/safety-portal`)
- **H1:** `Safety Operations Dashboard · Governance Drift 100/100`
- **Sidebar:** Incidents & Escalation (Incidents & Near Misses · Corrective Actions · Tasks & Actions) · Documents & Training · Compliance & Records
- **Sprint A · DOCEXP-60/90 strip:** 28 Expired · 6 ≤30 d · 11 ≤60 d · 8 ≤90 d · 88 Healthy
- **Verdict:** Preserve. Solid role fit.

### 3.G · Field Leadership (`/leadership`)
- **H1:** `Field Leadership`
- **Sections:** Recent field memory · Daily Crew Documentation · Verbal Coaching · Employee Write-Up · Attendance / Tardy · Recognition / Reward · Evaluations & Career Path
- **Verdict:** Preserve. Reference standard intact.

---

## 4 · Variance Table (baseline → today)

| Portal | Element | Variance | Class |
|---|---|---|---|
| PM | Header H1 `Project Operational Truth` → `Project Management Center` | ✅ Improved | Improved |
| PM | Subtitle `All my projects` → `Projects assigned to you` | ✅ Improved | Improved |
| PM | 12-tile fleet strip → scope-aware list (per-PM) or 3-tile summary (admin) | ✅ Improved | Improved |
| PM | 7-tab resource layout (Resources/Hauls/Materials/Shop/Safety/Timeline) | ✅ Moved to "Detailed operational view" button (one click away) | Preserved |
| PM | "DISPATCH PM HUB" link in header | 🟡 Operations-language residue | Drifted (minor) |
| Dispatch | Live Fleet Map hero added at top | ✅ Structurally present | Added |
| **Dispatch** | **Map canvas paints tiles** | **🔴 NO — canvas is black** | **REGRESSED vs. /operations-map (full page renders tiles)** |
| Dispatch | Count strip + CTAs | ✅ Visible & accurate | Added |
| HR | `<OperationsCenter compact />` → `<HrKpiStrip />` | ✅ HR-native strip rendered | Improved |
| HR | Operations Actions / People Operations sections | 🟡 Still rendered alongside (not replaced) | Drifted |
| Admin / Shop / Safety / FL | All | Preserved | Preserved |
| Cross-portal chrome | All identical | Preserved | Preserved |

---

## 5 · Last-48-Hour Intent Alignment

| Intent | Status | Evidence |
|---|---|---|
| PM called "Project Management Center" | ✅ YES | DOM probe: h1 = `Project Management Center` |
| PM shows only assigned projects (PM scope) | ✅ MECHANISM CORRECT | `compute_pm_scope` wired into every PM endpoint; super-admin sees admin scope (correct contract). Per-PM list would render under PM token; could not be visually demonstrated with available preview credentials. |
| PM avoids company-wide project dump | ✅ YES | Admin scope tile is explicitly labeled `(admin scope)`. |
| PM visually matches MASCI platform | ✅ YES | Same chrome, palette, typography, spacing. |
| PM has project health rows | 🟡 PARTIAL | Code path exists (`pm-pfh-project-list` testid). Cannot be operator-visually proven under super-admin token. |
| PM can open Daily Reports | ✅ YES | "View all" → `/daily` confirmed in Track 13.1 audit. |
| PM can open Photos | ✅ YES | "View all" → `/pm/photos` confirmed in Track 13.1 audit. |
| PM can open project detail | ✅ YES | `/pm/command-center?project_number=<pn>` deep-link. |
| Road plates demoted from KPI | ✅ YES | Now in Section E as one of 6 demoted rollups. |
| **Dispatch shows actual map on first screen** | **🔴 NO** | **Map canvas is BLACK. Tiles do not render.** |
| Dispatch can open full Live Map | ✅ YES | "Open Full Live Map" button → `/operations-map`. |
| Dispatch can open Operational Board | ✅ YES | "Open Operational Board" button. |
| HR KPIs HR-native | 🟡 PARTIAL | HR-native strip rendered but operations-paste sections (Operations Actions, etc.) still render alongside it. |
| Shop preserved | ✅ YES |
| Safety preserved | ✅ YES |
| Admin preserved | ✅ YES |
| Field Leadership preserved | ✅ YES | Reference standard intact. |

---

## 6 · Five-Pillar Scoring (current)

| Portal | Powerful | Simple | Beautiful | Trusted | Proven | **Total /25** | Δ vs baseline |
|---|---:|---:|---:|---:|---:|---:|---|
| Field Leadership | 5 | 5 | 5 | 5 | 5 | **25** | unchanged |
| Shop | 4.5 | 4 | 4 | 5 | 4.5 | **22** | unchanged |
| Safety | 4 | 4 | 4 | 5 | 4 | **21** | unchanged |
| Admin | 5 | 3 | 4 | 4 | 4 | **20** | unchanged |
| PM | 3.5 | 4 | 4 | 3.5 | 3 | **18** | **+6** (was 12) |
| **Dispatch** | **3** | 4 | **2 (black canvas)** | 3 | **2** | **14** | **−5.5** (was 19.5 — map regression) |
| HR | 3.5 | 3 (duplication) | 4 | 3.5 | 3.5 | **17.5** | **−1** (cumulative addition, not swap) |

Platform aggregate: **137.5 / 175 (78.6 %)** — essentially flat. PM improved by +6; Dispatch lost 5.5 to the black canvas; HR lost 1 to additive vs. swap. **The PM rebuild paid for the Dispatch and HR regressions.**

---

## 7 · Screenshot Index — `/app/memory/brutal_audit/`

| File | Portal | Viewport | Verdict |
|---|---|---|---|
| `admin_desktop.png` | Admin | 1440×900 | Preserve |
| `pm_desktop.png` | PM | 1440×900 | Improved (naming + structure correct) |
| `dispatch_desktop.png` | Dispatch | 1440×900 | 🔴 Map canvas black |
| `shop_desktop.png` | Shop | 1440×900 | Preserve |
| `hr_desktop.png` | HR | 1440×900 | 🟡 Cumulative addition |
| `safety_desktop.png` | Safety | 1440×900 | Preserve |
| `fl_desktop.png` | Field Leadership | 1440×900 | Reference standard |
| `pm_ipad_landscape.png` | PM | 1024×768 | OK |
| `dispatch_ipad_landscape.png` | Dispatch | 1024×768 | 🔴 Map canvas still black |
| `shop_ipad_landscape.png` | Shop | 1024×768 | Preserve |
| `hr_ipad_landscape.png` | HR | 1024×768 | 🟡 same as desktop |
| `safety_ipad_landscape.png` | Safety | 1024×768 | Preserve |

---

## 8 · Route & Feature Variance

**Routes:** No routes added or removed in the last 48 hours. RC-2 route inventory guardrail (23 canonical + 1 banned + 3 health surfaces) still PASS. Photo route corrected `/admin/job-photos` → `/pm/photos`.

**Features:**

| Feature | Status |
|---|---|
| PM Section A scope-aware list | Exists; visible to non-super-admin only |
| PM Daily Reports click-through | Exists & visible |
| PM Photos click-through | Exists & visible |
| Dispatch Live Fleet Map header | Exists & visible |
| **Dispatch Live Fleet Map tiles** | **Exists structurally, BLANK visually** |
| HR-native KPI strip | Exists & visible |
| HR operations-paste sections | **Should-be-removed, still rendered** |
| FL action grid | Exists & visible |

---

## 9 · Critical · Major · Minor

### 🔴 CRITICAL (must fix before deploy)
1. **Dispatch map canvas renders black.** The hero element + count strip + CTAs all work, but the MapLibre base layer paints nothing. Likely tile source unreachable from the preview pod (style URL · CORS · referer · 404). The full `/operations-map` page renders tiles correctly, so the failure is hero-specific (style config / container sizing / WebGL init timing).

### 🟡 MAJOR (fix before deploy)
2. **HR — operations-paste sections still rendered alongside the HR-native KPI strip.** Track 13 added the new strip but did not remove the old surface. Either remove the operations sections on HR or move them into a clearly-labeled "Operations crosswalk" subsection.
3. **PM project-row layout cannot be operator-visually proven under super-admin.** Add a second seeded PM account (preview-only, no production data) so the per-row layout is demonstrable.

### 🟢 MINOR
4. PM header "DISPATCH PM HUB" link — operations-language residue on a project-language portal.
5. PM Section A admin-summary copy reads `Across every project (admin scope).` — minor wording polish opportunity.

---

## 10 · Preserve · Revert · Rebuild · Fix-First

| Action | Targets |
|---|---|
| **PRESERVE (do not touch)** | Admin · Shop · Safety · Field Leadership · cross-portal chrome · PM naming · PM Section B/C/D/E · 117-case predeploy gate · RC-1/RC-2/RC-2.1/Final Pre-Save state |
| **REVERT** | None. No prior good state to roll back to — the rebuild was net-positive on PM and net-negative on Dispatch/HR only because of additive vs. replacement choices. |
| **REBUILD** | None. Surgical fixes only. |
| **FIX FIRST (in this order)** | (1) Dispatch map tile rendering — root-cause the WebGL/style-url failure inside the 320 px hero. (2) HR — decide whether operations sections stay (clearly labeled) or move out. (3) PM second-PM seed for visual proof of the per-row list. |

---

## 11 · "DO NOT TOUCH" list

- Field Leadership portal
- Shop portal
- Safety portal
- Admin left-rail grouping
- Cross-portal chrome (header, preview banner, EN/ES, portal switcher, sign-out)
- 117-case predeploy_certify gate
- `compute_pm_scope` mechanism
- All RC-2 guardrail files
- `/api/operations-map/snapshot` contract
- `/api/health/full` contract
- Any audit log, backup, or production data

---

## 12 · Operator Approval Checklist (before next sprint)

- [ ] Operator confirms Dispatch black-canvas is the priority fix
- [ ] Operator chooses HR direction: remove operations sections OR keep & label
- [ ] Operator confirms PM second-PM seed is acceptable for visual demonstration
- [ ] Operator confirms 117-case predeploy gate must stay green after the fix
- [ ] Operator confirms no production data writes
- [ ] Operator confirms no Save to GitHub, no deploy until next visual approval

---

## 13 · Recommended Next Sprint (Track 13.3 — proposed scope)

**One sprint. Three surgical fixes. No new features. No new portals.**

1. **Dispatch map tile fix** — root-cause the empty canvas inside `DispatchMapHero.jsx`. Likely candidates: (a) style URL needs absolute origin or fallback when the certified `MapCanvas` is rendered inside a fixed-height container with `overflow: hidden`; (b) WebGL `requestAnimationFrame` not firing because the parent uses CSS transforms; (c) snapshot data path missing the geometry the full page uses. Inspect the network tab on a real browser session against the preview pod to confirm which tile request is failing.
2. **HR operations-section disposition** — operator picks one of: (a) remove Operations Actions / People Operations / Employee Lifecycle / Tasks & Actions from HR (move to Admin); (b) keep them, but wrap in a clearly-labeled "Cross-portal Operations Surfaces" subsection beneath the HR-native KPI strip.
3. **PM second-PM seed** — add a preview-only PM fixture (`pm.demo@mascigc.com` mapped to project numbers `26-01` and `26-02`) so the per-row health list can be screenshot-proven in operator-visible form.

After fixes:
- Run `bash /app/scripts/predeploy_certify.sh` (117 cases — must stay green)
- Capture fresh screenshots
- Operator visual approval

---

## 14 · BRUTAL AUDIT VERDICT

# 🔴 NOT READY — FIX LIST REQUIRED

**Reasons:**
1. Dispatch map canvas is black. The prior PASS report's "DISPATCH REAL MAP EMBED COMPLETE" wording is contradicted by the screenshot.
2. HR change was additive, not a swap; operations-paste sections still render.
3. PM per-row layout is correct code but not operator-visually proven under the only available test account (super-admin → admin scope summary).

**Reasons it is not REVERT or REBUILD:**
- PM rebuild and the platform's preserved portals are all good or improved.
- No prior good state to revert *to* — the rebuild was net-positive.
- The fixes are surgical (one tile-renderer, one section disposition, one fixture).

**Do not Save to GitHub. Do not deploy. Operator review and Track 13.3 first.**

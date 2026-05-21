# MASCI Platform — UX Refinement Roadmap
*Established 2026-05-21 · paired with `UX_GOVERNANCE_AUDIT.md` + `UX_GOVERNANCE_RULES.md`*

A **bounded, priority-ranked** implementation plan for applying the governance rules across the platform. Strict stabilization posture: section-by-section, screenshot-verified, regression-locked, NO mass-update passes.

**Sequencing rule**: each iteration ships independently. Operator approves each before the next begins. No iteration touches more than one hub family at a time.

---

## Phase A · HIGH-IMPACT calm passes (apply HR pattern to other flat hubs)

Each iteration here is roughly the same scope as iter317-C Part 2 (one hub · grouped-card refinement · left-edge stripe · calm hierarchy · screenshot verification · 6–10 invariant tests). **No backend changes.**

### iter318 · Safety Hub Visual-Hierarchy Refinement
**Why first**: Safety Hub is the most-visited interior hub after HR. 15 tiles + KPI strip + 2 integration cards mid-page — currently the second-loudest hub. High operational visibility = highest user-facing payoff.

**Scope** (bounded):
- Refactor `SafetyHub.jsx` tile grid into 4 grouped sections:
  - **Daily Safety Operations** — Tasks & Actions · Corrective Actions · Incidents & Near Misses · Audits & Inspections
  - **Compliance & Records** — Training & Certifications · Employee Safety Profiles · Fire Extinguishers · Safety Document Library · Document Expirations
  - **Operational Output** — Weekly Digest · Reports & Exports · Topic Library · Trucking · Fleet
  - **Integrations & Systems** (demoted) — Training Center & Guides · Change Password · IntegrationHealthCard · IntegrationEventsCard
- Convert tile chrome to HR pattern (left-edge stripe, calm).
- Move Motive integration cards from mid-page to the demoted Integrations group at the bottom.
- KPI strip: convert to Rule-5 neutral chrome (subdued).
- Preserve all 15 testids, hover behavior, bilingual `t()` calls.

**Effort**: Medium (1 hub file + 1 invariant test).
**Risk**: Low.
**Testing**: screenshot 1920/1024/390 · 8 invariant tests · combined regression with iter314+316+317.

---

### iter319 · Field Leadership Hub Visual-Hierarchy Refinement
**Why second**: FL Hub is the second-most-trafficked surface. Already grouped (5 groups), but tile chrome is still hot (uses shared `SectionTile` with `border-2 border-slate-300` + large H3s).

**Scope**:
- Leave the existing 5-group structure intact (already correct).
- Convert `SectionTile` usage to the calm HR pattern (left-edge stripe, `text-lg` titles instead of `text-3xl/4xl`). This requires either:
  - **Option A (recommended)**: extend `SectionTile.jsx` with a `variant="calm"` prop and pass it where appropriate, OR
  - **Option B**: render an inline calm tile in `FieldLeadershipHub.jsx` (mirrors HrHub's approach).
- Tone down the H1 from `text-4xl sm:text-5xl lg:text-6xl` to the interior-hub size `text-3xl sm:text-4xl`.
- Drop the iter145 button-cluster ("Guides", "Records", "Sign Out") into the iter203 mobile-collapse pattern (currently doesn't collapse).
- Preserve all testids, the password-gate fallback, admin-bypass behavior.

**Effort**: Medium.
**Risk**: Low–Medium (touches the shared `SectionTile` if Option A chosen).
**Testing**: screenshot × 3 · 6 invariant tests · combined regression.

---

### iter320 · Shop Hub Visual-Hierarchy Refinement
**Why third**: Shop Hub has a custom `Kpi` component + custom inline tile + tabs + multiple panels — visually noisy. Mechanics use this daily on tablets in the shop.

**Scope**:
- Convert custom `Kpi` chrome to Rule-5 neutral (drop `border-2 border-slate-200` to single `border`).
- Tone down the Fleet · DVIR link banner (currently `border-2 border-amber-300 hover:border-amber-600 hover:bg-amber-50` — hot).
- Tabs styling: keep the tab pattern (operationally important for Shop) but reduce the border-b-4 weight.
- H1 size: `text-4xl sm:text-5xl` → `text-3xl sm:text-4xl`.
- Move integration content from "Integrations" tab to a small demoted section under the active tab (so health is always visible, not buried).

**Effort**: Medium.
**Risk**: Low.
**Testing**: screenshot × 3 · 7 invariant tests.

---

### iter321 · Dispatch Hub Convergence
**Why fourth**: Dispatch is the architectural outlier (`max-w-7xl`, `bg-slate-50`, no `blueprint-bg`, no `caution-stripe`, no iter203 mobile collapse, "iter132" leak). Highest single-hub drift score.

**Scope**:
- Container: `max-w-7xl` → `max-w-6xl` (matches every other flat hub).
- BG: `bg-slate-50` → `blueprint-bg` + add `caution-stripe`.
- Header: `bg-slate-950` → `bg-slate-900`, apply iter203 mobile-collapse pattern.
- Drop the `iter132` literal from the kicker (replace with empty or "Operational Dispatch").
- Tabs styling: same calm treatment as Shop.
- KPI/stat blocks: Rule-5 neutral chrome.

**Effort**: Medium.
**Risk**: Medium (more files touched — header chrome change · BG change).
**Testing**: screenshot × 3 · 8 invariant tests · verify all 6 tab contents still render.

---

### iter322 · FL Portal Dashboard Calm Pass
**Why fifth**: New surface (iter314), still rough. Per-user FL accounts now sign in and see this — first impressions matter.

**Scope**: same calm pattern · grouped sections · HR-style chrome · subdued KPIs.
**Effort**: Small (single page, low tile count).
**Risk**: Very Low.

---

## Phase B · COLOR SEMANTICS audit pass

### iter323 · Platform-wide color semantic audit (read-only first)
**Purpose**: With Rules 2 + 3 in hand, walk every hub touched in Phase A and verify color choices match the semantic table. Output is a delta report.

**Scope** (read-only · NO code changes):
- Run a grep + visual scan against the rules.
- Output: `/app/memory/UX_COLOR_DELTA.md` — list of every tile whose accent color violates the semantic rule.
- Operator reviews and approves the corrections in batches before any code change.

**Effort**: Small (audit + doc).
**Risk**: None (no code change).

### iter324 · Color semantic corrections (operator-approved batches)
- Apply the iter323 delta in **operator-approved batches** (e.g., "fix all `purple` non-HR usages first").
- Bounded · screenshot · invariant test per batch.
- Most likely targets: Driver Qualification tile (emerald-600 → semantic decision needed), Training Records tile (purple → indigo? or stays purple as HR-domain content?).

**Effort**: Medium spread across 3–4 sub-iterations.
**Risk**: Low (no functional change, just tile color tokens).

---

## Phase C · KPI / STAT BLOCK unification

### iter325 · Unified `KpiBlock` component
- Build a single `KpiBlock` component matching Rule 5 (subdued chrome, optional colored value, neutral border).
- Migrate `SafetyHub.KPI` · `ShopHub.Kpi` · `AdminKpiStrip` panels · KPI cells in PmHub tiles to use it.
- Keep `OperationsCenter` as-is (it's a different paradigm — real-time aggregation).
- Existing testids preserved.

**Effort**: Medium (new component + 4-5 migration sites).
**Risk**: Medium (touches multiple hubs — needs careful testing).
**Testing**: testing_agent_v3_fork frontend pass · screenshot every touched hub.

---

## Phase D · HEADER CHROME convergence

### iter326 · Header chrome standardization
**Purpose**: Apply Rule 7 to every interior hub that has a header.

**Scope**:
- Verify iter203 mobile-collapse on EVERY hub (currently HR + Shop ✅; Dispatch + Leadership pending).
- Ensure container is `max-w-6xl` on every flat hub (after iter321 this should be true).
- Ensure right-cluster button order matches Rule 7.
- Reduce `border-2` chrome on header buttons to `border` where the bg already carries weight.

**Effort**: Medium (touches 4–5 hub files for header-only changes).
**Risk**: Low.

---

## Phase E · LOW-PRIORITY polish (deferred until A+B+C+D land)

| Iter | Scope | Effort |
|---|---|---|
| iter327 | Tone polish — drop "iter132" leak · audit any iteration tag leaks · clean up FL Hub legal-compliance footnote | Trivial |
| iter328 | Empty states pass — apply Rule 11 across all panels | Medium |
| iter329 | Modal / dialog visual rhythm — reduce hot borders in confirmation dialogs | Medium |
| iter330 | PDF chrome standardization (per Rule 7 equivalent for PDF output) | Medium |
| iter331 | Login-page hierarchy parity (every portal login should feel like the same family) | Medium |
| iter332 | Mobile/tablet edge audit · iPhone, iPad portrait/landscape, Android | Small |

---

## What's intentionally NOT in this roadmap

- ❌ No platform-wide mass refactor in a single iteration.
- ❌ No sidebar introduction on flat hubs (operator-rejected; muscle-memory protected).
- ❌ No dashboard gimmicks, animated stats, skeleton-shimmer loaders.
- ❌ No dark-mode / theme switching.
- ❌ No `SectionTile` API redesign beyond an optional `variant` prop (if iter319 chooses Option A).
- ❌ No new navigation paradigm (mega-menus, top-bar nav, etc.).
- ❌ No changes to `STABILIZATION_PRINCIPLES.md` deferrals (legacy test debt stays deferred).
- ❌ No removal of working functionality anywhere.
- ❌ No iter317-D / iter317-E (FL Lifecycle/Rehire articles, AddDialog coaching mount) — those stay in the existing audit queue, not in this UX governance roadmap.

---

## Sequencing recommendation

**Default operator flow**:
1. Approve `UX_GOVERNANCE_RULES.md` (or revise) — **one ask_human pass**
2. Operator picks the next iteration from Phase A (iter318 Safety is the recommendation)
3. Agent ships that bounded iteration · screenshots · regression · doc update
4. Operator reviews · approves next
5. Repeat through Phase A · then Phase B · then C · then D · then E

**Estimated total scope**: 8–10 bounded iterations spread over multiple operator-approved sessions. No single iteration takes more than one focused agent pass.

---

## Closing principle

> *Bring the entire platform into one coherent operational family. Same operational power. Cleaner hierarchy. Better flow. Better feel. Better trust.*

Every iteration above passes that test or it doesn't ship.

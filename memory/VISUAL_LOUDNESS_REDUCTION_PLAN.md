# Visual Loudness Reduction Plan — Phase IV-A

**Iteration:** iter437 · Phase IV-A · 2026-02
**Status:** 🟢 REDUCTION TARGETS LOCKED · MEASURED · ACTIONABLE
**Companion docs:** `COMPONENT_HIERARCHY_STANDARD.md` · `ADMIN_UX_GOVERNANCE.md` · `OPERATIONAL_VERBIAGE_DOCTRINE.md`

The current admin portal is **loud**. This is not subjective — it is measurable. This document quantifies the loudness, locks reduction targets per dimension, and defines the verification gate that ensures the platform stays calm as it scales.

The goal is not "minimalism." The goal is **calm signal density** — every visual element earns its volume because it is operationally important, and nothing else competes with it.

---

## I. What "loud" means operationally

Visual loudness is the sum of stimuli competing for the operator's foveal attention. A loud surface degrades decision quality even when the operator is not consciously distracted. Loudness manifests through six measurable dimensions:

| Dimension | How it's measured |
|---|---|
| **Color saturation** | % of surface area covered by ≥ 50% saturated color (red, orange, green, blue, etc.) |
| **Color competition** | Count of distinct hue families on a single surface (≤ 3 is calm; ≥ 5 is loud) |
| **Element density** | Visible interactive/clickable elements per 1000 px² of surface |
| **Notification density** | Count of badges, dots, counts, and alert markers per surface |
| **Typography contrast** | Count of distinct font sizes + weight combinations in use on a single surface |
| **Motion stimulus** | Active animations (pulses, transitions, spinners) per second of operator dwell time |

A surface is **calm** when all six dimensions are within their target range. A surface is **loud** when ≥ 2 are out of range. The current admin portal has surfaces with ≥ 4 out of range — this plan brings them in.

---

## II. Audit findings — current loudness baseline

Measured on the current `AdminShell.jsx` sidebar + the admin landing page (`/admin`) before Phase IV-A.1.

| Dimension | Current value | Target | Status |
|---|---|---|---|
| Color saturation (sidebar) | ~22% (red active state, red headers, red badges) | ≤ 4% | ❌ |
| Color competition (sidebar) | 5 hues (red, blue, amber, green, gray) | ≤ 3 | ❌ |
| Element density (sidebar) | 29 interactive items / ~600 × 800 px panel | ≤ 14 visible at once | ❌ |
| Notification density (sidebar) | 7 "NEW"/"BETA" badges + 4 counts + 2 dots = 13 markers | ≤ 6 | ❌ |
| Typography contrast (sidebar) | 4 sizes × 3 weights = 9 combinations | ≤ 4 combinations | ❌ |
| Motion stimulus | Spinning sync icon (always) + pulsing dot + animated badge | ≤ 1 ambient + on-action | ❌ |

**Verdict:** The current sidebar is loud across all 6 dimensions. This is the worst-offending surface in the platform.

| Dimension | Current value (admin landing) | Target | Status |
|---|---|---|---|
| Color saturation | ~14% | ≤ 5% | ❌ |
| Color competition | 4 hues | ≤ 3 | 🟡 |
| Element density | 38 cards on initial render | ≤ 12 above the fold | ❌ |
| Notification density | 9 badges visible | ≤ 4 | ❌ |
| Typography contrast | 7 combinations | ≤ 4 | ❌ |
| Motion stimulus | 3 ambient animations | ≤ 1 ambient + on-action | ❌ |

---

## III. Reduction targets — measurable, per dimension

### III.1 — Red usage reduction

**Current:** Red appears on 22% of sidebar surface area and 14% of the admin landing area.

**Target:** Red appears on **≤ 4% of any sidebar surface · ≤ 2% of any non-incident page · 0% of all governance/settings surfaces.**

**Allowed red elements (per surface, max 1 of these visible at once):**
- 1× OPERATIONS domain 2-px stripe (sidebar only)
- 1× Tier-4 escalation badge
- 1× Tier-5 emergency takeover (full surface override — replaces all other red)
- 1× Asset `Failed` / `Down` state badge in tables (per row)
- 1× Form validation error text (per field, on error only)

**Forbidden red usage from this point forward:**
- Red active/selected backgrounds on nav items → replaced by 2-px stripe + slate-50 background tint
- Red H1/H2 headers → replaced by slate-900 (color tier is for severity, not branding)
- Red dividers / borders → replaced by slate-200
- Red icons in non-severity contexts → replaced by slate-500 default
- Red hover states → replaced by slate-100 background

**Verification:** Pixel-counter script (`/app/scripts/measure_red_saturation.py`, Phase IV.A.4) computes red pixel ratio per snapshot. Surfaces > 4% red fail the gate.

---

### III.2 — Badge reduction

**Current:** Sidebar shows 13 markers (badges + counts + dots). Admin landing shows 9.

**Target:** **≤ 6 markers in sidebar at any time · ≤ 4 markers per page above the fold · 0 decorative badges anywhere.**

**Reduction actions:**

| Marker type | Current count | Target | Action |
|---|---|---|---|
| "NEW" / "BETA" / "PREVIEW" badges | 7 in sidebar | 0 | Delete all in IV.A.2 |
| Version badge in sidebar footer | 1 | 0 | Move to `/admin/system-health`, hide from sidebar |
| Per-feature count badges | 4 in sidebar | ≤ 6 *across all 6 domains*, ≤ 1 per domain | Aggregate at domain level (e.g., "OPERATIONS · 3") |
| Decorative dots (online indicators) | 2 in sidebar | 0 | Replaced by an explicit `Active` state badge in the account-avatar dropdown |
| Page-level "in this view" badges | 9 on admin landing | ≤ 4 | Inline state badges in cards only — no page-header badges |

**Verification:** Frontend lint rule (`badge-density-check`, Phase IV.A.4) counts `<Badge>` and similar primitives per route. Routes exceeding limits fail build.

---

### III.3 — Saturation reduction

**Current:** Multiple surfaces use saturated 600–700 weight colors as backgrounds (red-600 nav active, blue-600 buttons, amber-600 banners).

**Target:** **Saturated 600+ weights are reserved for ≤ 5% surface coverage. The other 95% uses 50–200 weight tints for backgrounds, 700–900 weight for text only.**

**Concrete substitutions:**

| Where saturated color is used today | Replacement |
|---|---|
| `bg-red-600` active sidebar state | `bg-slate-50` + 2-px `border-l-red-600` |
| `bg-blue-600` primary buttons | `bg-slate-900` primary buttons (the platform's neutral primary is slate-900, NOT blue) |
| `bg-amber-100` always-visible warning banner | Tier-2 banners are still amber, but appear conditionally — not always-on |
| `bg-emerald-100` "success" badges everywhere | Only on `Approved` / `Resolved` / `Active` state badges, nowhere else |
| Gradient backgrounds (any) | Solid slate-50 / slate-900 only |

**Verification:** Tailwind config gets a deprecation list (Phase IV.A.4). PRs referencing forbidden classes (`bg-red-600` outside escalation contexts, `bg-blue-600` anywhere, any `bg-gradient-*` outside the brand splash) fail lint.

---

### III.4 — Simultaneous CTA reduction

**Current:** Some admin pages show 3–5 "primary"-styled CTAs simultaneously (e.g., the equipment list page has `Add Equipment`, `Bulk Import`, `Export`, `Filter`, all styled identically).

**Target:** **Exactly 1 primary CTA per page. All other actions are secondary (slate-outlined buttons) or live in an overflow `…` menu.**

**Reduction rules:**

- Page header: 1 primary action button, top-right.
- Secondary header actions: 0–2 outlined buttons OR a `…` overflow menu.
- Row-level actions: 1 primary verb per row (`Open`, `Approve`, etc.) — secondary verbs in row `…` overflow.
- Modal: 1 primary verb + 1 `Cancel`.

**Anti-pattern eliminated:** Two equally-weighted "primary" buttons next to each other (e.g., `Save` + `Submit`). This pattern means the page is doing two jobs — split it.

**Verification:** PR-time visual regression. Any page snapshot with ≥ 2 elements matching `bg-slate-900` button styling at H1-level placement is flagged.

---

### III.5 — Modal reduction

**Current:** Some admin flows open 2 modals in sequence ("Are you sure?" → "Configure options" → submit).

**Target:** **Modals appear ≤ once per operator-initiated flow. Multi-step decisions become inline forms or routed pages, not stacked modals.**

**Reduction actions:**

- Audit all `<Dialog>` and `<AlertDialog>` usage (Phase IV.A.3). For each, classify:
  - **Justified** → confirms irreversible action OR Tier-4 escalation acknowledgment. KEEP.
  - **Convertible to inline** → multi-field forms wrapped in modals. CONVERT to sheets (mobile) / routed pages (desktop).
  - **Convertible to toast** → "Are you sure?" for reversible actions. REPLACE with optimistic UI + undo toast.
  - **Delete** → modals that exist only to confirm what just happened ("Success! Click OK to continue."). DELETE.

**Target ratio:** ≤ 1 modal per 8 operator-initiated actions, across the whole portal.

---

### III.6 — Notification reduction

**Current:** Multiple notification surfaces compete for attention: bell badge + inline banner + toast + modal escalation + email + push.

**Target:** **Per surface, exactly 1 notification channel may be visible at once.** See `COMPONENT_HIERARCHY_STANDARD.md` §V for the layering rule. This reduction codifies the consequence:

| Channel | Reduction |
|---|---|
| Bell badge | Shows count only — no inline preview unless dropdown opened |
| Inline banner | ≤ 1 per tier per surface · auto-collapses ≥ 3 same-tier into a digest |
| Toast | ≤ 1 visible at a time (queue subsequent ones · 4 s duration · auto-clear queue on route change) |
| Modal escalation | Tier 4–5 only · supersedes all other channels |
| Email | Per `COMMUNICATION_TONE_STANDARD.md` §IV quotas |
| Push | Per `COMMUNICATION_TONE_STANDARD.md` §IV quotas |

**Verification:** Phase IV.A.4 ships a runtime check `<NotificationStackGuard>` that monitors visible-notification count and warns in dev mode if > 1 per channel.

---

### III.7 — Typography simplification

**Current:** 7+ font-size/weight combinations across the admin portal (text-xs, text-sm, text-base, text-lg, text-xl, text-2xl, text-3xl, with mixed font-normal/medium/semibold/bold).

**Target:** **6 sizes × 3 weights = 6 used combinations on any given surface · ≤ 4 distinct combinations per surface.**

**Reduction actions:**

| Reduction | Rationale |
|---|---|
| Eliminate `text-xl` and `text-4xl`+ from operational surfaces | The 6-step scale from `COMPONENT_HIERARCHY_STANDARD.md` §X covers all needs |
| Eliminate `font-bold` for body paragraphs | Bold is for in-paragraph emphasis only |
| Eliminate italic text (anywhere in operational copy) | Italic is reserved for legal/compliance footnotes |
| Eliminate uppercase outside Tier-1 eyebrows | Uppercase is a hierarchy signal, not decoration |
| Eliminate inline color text in paragraphs (red sentences, blue sentences) | Color carries severity, not emphasis |

**Verification:** `eslint-plugin-tailwindcss` custom rule rejects forbidden classes.

---

### III.8 — Spacing normalization

**Current:** Spacing is inconsistent — buttons have 8 px padding in one place and 16 px in another, card gaps range from 4 px to 32 px arbitrarily.

**Target:** **All spacing is a multiple of 4 px and drawn from the 8-step scale: 4, 8, 12, 16, 20, 24, 32, 48.**

**Reduction actions:**

- Audit all spacing utility classes (Phase IV.A.5). Replace non-conforming values with the nearest scale value.
- The 8-step scale is enforced via a custom Tailwind plugin that aliases out-of-scale values to nearest scale value at build time (with a console warning in dev).

**Spacing semantics:**

| Context | Spacing |
|---|---|
| Inside a button (padding-y) | 8 px (small) · 12 px (default) · 16 px (large) |
| Between siblings in a form | 16 px |
| Between siblings in a card grid | 12 px (dense) · 16 px (standard) · 24 px (expanded) |
| Between sections of a page | 24 px |
| Between domains in sidebar | 8 px |
| Inside a modal (content padding) | 24 px |
| Mobile horizontal page padding | 16 px |
| Desktop horizontal page padding | 24 px |

**Verification:** Tailwind plugin warning at build time. Phase IV.A.5 ships the plugin and the audit report.

---

### III.9 — Border reduction

**Current:** Many surfaces use multiple border colors and weights (slate-200, slate-300, blue-200, red-200) simultaneously.

**Target:** **Borders are slate-200 (1 px) by default. Only state-bearing borders use color (e.g., a 2-px border-stripe in domain color for active items, a 1-px red-300 border on invalid form fields).**

**Reduction actions:**

- Eliminate decorative borders (e.g., section dividers that exist for "visual interest")
- Replace double borders (border + inset shadow) with single 1-px slate-200
- Card borders: 1-px slate-200 default · 2-px domain-color border for active selection only
- Form fields: 1-px slate-300 default · 1-px slate-500 focus · 1-px red-300 error

**Verification:** Border-classes audit (Phase IV.A.5). Forbidden classes flagged in PR review.

---

### III.10 — Shadow reduction

**Current:** Multiple shadow elevations used inconsistently — some cards have `shadow-md` always, others have `shadow-lg` on hover.

**Target:** **Three shadow elevations only · used semantically:**

| Elevation | Use |
|---|---|
| `shadow-none` (default) | Cards at rest, inputs at rest, buttons at rest |
| `shadow-sm` (subtle) | Hover state on cards · default for modals · default for popovers |
| `shadow-md` (clear) | Modal panels above backdrop · drawer panels |
| `shadow-lg` and above | **forbidden** (no surface should shout via shadow) |

**Reduction actions:**

- Replace all `shadow-lg`, `shadow-xl`, `shadow-2xl` with `shadow-sm` or `shadow-md` per context.
- Eliminate colored shadows (`shadow-red-500/20`, etc.) — shadows are always neutral.
- Eliminate hover-state shadow on table rows (use background-color shift instead).

---

### III.11 — Visual rhythm standards

Even when all individual elements are calm, **rhythm breaks** make a surface feel loud. Rhythm targets:

| Rhythm constraint | Target |
|---|---|
| Max consecutive elements at the same Tier | 6 (e.g., 6 cards in a row before a divider or section break) |
| Min vertical gap between major sections | 24 px |
| Max vertical gap between major sections | 48 px (more = floating-section syndrome) |
| Card alignment within a grid | Strict — all cards in a row have identical height (use `auto-rows-fr` or fixed `min-h`) |
| Horizontal alignment of CTAs | All page-header CTAs aligned to the right edge of the content area (same x-position across pages) |
| Sidebar entry height | 56 px desktop · 64 px mobile · identical for all entries in same tier |

**Verification:** Visual regression snapshots (Phase IV.A.6) include rhythm-line overlays — diffs in alignment flag the PR.

---

## IV. The "what makes the platform feel loud" inventory

Concrete observations of loudness sources in the current codebase (pre-Phase IV-A.1):

1. **Red headers in the sidebar.** Domain headers were styled red because operations are critical. But every domain header was red — the signal lost meaning.
2. **"NEW" and "BETA" badges on 7 sidebar items.** Every feature appeared new; nothing was actually new.
3. **The pulsing sync indicator** in the sidebar footer. Always pulsing. Always present. Trains the eye to ignore motion.
4. **The version-number badge.** "v2.41.6" served no operator purpose and consumed visual real-estate.
5. **The "PREVIEW" environment badge** in production sidebar. Bug — already fixed via environment-identity verification — but the badge itself was always visually loud.
6. **Gradient background on the admin landing hero.** Loud + non-functional + slow on mobile.
7. **Multiple competing CTAs** on the equipment page (Add, Import, Export, Filter, Sort — all primary-styled).
8. **Toasts that auto-stack to 4 visible** during bulk operations. Operators stopped reading.
9. **A flashing red banner** on system-health when latency exceeded 500 ms. Latency now displayed as a calm metric on the system-health page only.
10. **Multiple notification surfaces firing simultaneously** for the same event (bell + banner + toast + email for "Daily Report submitted"). Coordinated reduction: bell only, banner only on the report's page, no toast, email at Tier 0 daily-digest cadence.

---

## V. The systematic reduction approach

The reductions land across 6 phased sub-iterations (Phase IV.A.1 through IV.A.6), each ≤ 200 LOC, each individually reversible.

| Phase | Reduction scope | Risk |
|---|---|---|
| **IV.A.1** | Sidebar re-architecture — domain-grouping, stripe-only color, "NEW"/"BETA" removal | LOW · behind feature flag |
| **IV.A.2** | Sidebar color/saturation cleanup — replace red active state, kill version badge | LOW |
| **IV.A.3** | Modal audit — convert convertibles, delete deletables | MEDIUM · changes user flows |
| **IV.A.4** | Notification channel coordination — codify "1 channel per surface" enforcement | LOW · runtime guard in dev |
| **IV.A.5** | Typography + spacing + border + shadow normalization across the admin portal | MEDIUM · touches many files |
| **IV.A.6** | Visual regression snapshot suite · rhythm-line audit · feature flag cut | MEDIUM · removes the old flat nav |

Each sub-phase ends with a snapshot of the loudness-score dashboard. The score must monotonically decrease.

---

## VI. The loudness-score dashboard (the measurement gate)

Phase IV.A.4 ships a per-surface loudness measurement script:

**Location:** `/app/scripts/measure_visual_loudness.py`

**Inputs:** Playwright snapshots of the 20 most-trafficked admin routes, captured at 3 viewport sizes (375 px iPhone, 768 px iPad, 1440 px desktop).

**Outputs:** Per-route loudness score across the 6 dimensions (§I). JSON report committed to `/app/test_reports/visual_loudness_<iter>.json`.

**Gate behavior:**
- Each dimension has a max-acceptable value per surface type (`sidebar`, `landing`, `form`, `table`, `detail`).
- Surfaces > threshold on ≥ 2 dimensions fail the gate.
- The pre-deploy gate computes a portal-wide loudness average. Average must be ≤ previous deploy's average minus 0% (i.e., must not regress). At a deploy that reduces loudness, the new baseline is recorded.

**Trend tracking:**
- The score is logged in `/app/memory/LOUDNESS_TRENDLINE.json` per deploy.
- A monthly review surfaces the trendline at `/admin/system-health#loudness`.

---

## VII. Cognitive-load doctrine

Visual loudness is the surface-level symptom. The underlying disease is **cognitive load** — the operator's working memory consumed by parsing the interface instead of doing the work.

### The five cognitive-load reduction principles

1. **Predictability reduces load.** When the operator knows where the primary CTA always lives (top-right desktop, bottom-thumb mobile), they stop searching.
2. **Hierarchy reduces load.** When the eye knows which element is most important without conscious effort, the operator's attention budget is spent on operational decisions, not on triage.
3. **Naming reduces load.** When `Submit` always means the same thing, the operator stops re-parsing intent.
4. **Severity reduces load.** When red always means Tier 4+, the operator can scan an entire surface in 1 second and know if anything demands action.
5. **Silence reduces load.** When the platform is quiet during nominal operations, the operator's nervous system trusts that silence = OK. Background noise destroys that trust.

### Operator-trust principles applied to loudness

- **The platform never decorates.** Every visual element earns its presence operationally.
- **The platform never updates layout cosmetically.** A redesign that doesn't reduce loudness or improve operational decision quality does not ship.
- **The platform never "celebrates" successes** with animations, confetti, or emojis. Success is the expected state.
- **The platform never warns when no warning is needed.** Banners that say "Tip: try X" are forbidden.
- **The platform never grows louder over time.** The loudness trendline is monitored. Drift triggers governance review.

---

## VIII. Anti-patterns explicitly forbidden from this point forward

| Anti-pattern | Why forbidden |
|---|---|
| Gradient backgrounds in any operational view | Visual noise + slow on mobile + brand-marketing aesthetic |
| Glassmorphism beyond 12-px blur radius on ≤ 1 element per screen | Performance + visual noise |
| Parallax scroll effects on any admin surface | Motion stimulus + accessibility (vestibular) |
| Scroll-triggered animations (fade-in on scroll, slide-in on scroll) | Distract from operational scanning |
| Custom illustrations / mascots / character art | Aesthetic noise; the platform is not a consumer product |
| Confetti / celebratory animations | The platform does not celebrate; it confirms |
| Pulsing/breathing animations on idle elements | Trains the eye to ignore motion |
| Loading-screen "fun facts" or "tips" | Operators want speed, not entertainment |
| Auto-rotating banners / hero carousels | Removes operator control · creates noise |
| Floating action buttons (FAB) | Obscure content + no fixed semantic role |
| Toast-stacking ≥ 3 visible | Operators stop reading |
| Tooltip-on-everything for "discoverability" | If a control needs a tooltip, its label is wrong |

---

## IX. Enforcement

- **Pre-deploy gate:** `scripts/measure_visual_loudness.py` runs on every deploy · build fails if portal-average loudness regresses.
- **PR checklist additions:** Every PR touching frontend declares predicted impact on each of the 6 loudness dimensions.
- **Quarterly visual audit:** Platform engineering reviews the loudness trendline · any regression triggers a doctrine amendment PR.
- **No marketing involvement in operational UI:** Marketing-driven UI changes (logo flourishes, hero rotators, animated CTAs) are rejected at PR review.
- **Designer / PM playbook:** This document is the source of truth for visual-loudness budgets. New surfaces start with the loudness budget allocated; designers prove they spent it operationally.

---

## X. Reduction targets — summary scorecard

| Dimension | Current portal average | Target | Owner |
|---|---|---|---|
| Red surface saturation | 18% | ≤ 4% sidebar · ≤ 2% pages | IV.A.1, IV.A.2 |
| Color hue competition | 4–5 hues per surface | ≤ 3 hues | IV.A.2 |
| Element density (above fold) | 30+ interactive | ≤ 14 | IV.A.1, IV.A.3 |
| Notification markers visible | 9–13 | ≤ 6 | IV.A.1, IV.A.4 |
| Typography combinations | 7–9 per surface | ≤ 4 per surface | IV.A.5 |
| Ambient motion elements | 3 | ≤ 1 | IV.A.2, IV.A.5 |
| Modal occurrences per flow | 2+ | ≤ 1 | IV.A.3 |
| Concurrent notification channels | 4 | ≤ 1 per surface | IV.A.4 |
| Border-color variants | 5+ | 2 (slate-200 + state) | IV.A.5 |
| Shadow elevations in use | 5 | 3 max | IV.A.5 |

---

## Verdict

🟢 **LOUDNESS REDUCTION PLAN LOCKED · MEASURABLE · GATED.** The platform now has a numerical loudness budget per surface, a measurement script that will land in Phase IV.A.4, and a phased reduction roadmap that brings every offending surface within target across 6 sub-iterations. The platform will get quieter — not by aesthetic taste, but by enforced doctrine.

From this iteration forward, "loud" is not an opinion. It is a number. And the number must trend down.

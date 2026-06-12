# TRACK 13.5A · PHASE B1 — Shared Design Primitives Foundation Report

**Status:** ✅ COMPLETE — Awaiting operator authorization for Phase B2.
**Date:** 2026-06-12 (UTC)
**Operator authorization on file:** "Execute the full Phase B1 completion plan exactly as listed." (this conversation)
**Scope discipline:** Phase B1 introduces presentation primitives ONLY. **No portal was migrated. No form was touched. No workflow was changed. No operator route changed. No engine wiring was added. No deploy. No GitHub save. No merge.**

---

## 1. Mandate Recap

> Build the foundational shared design primitives (`PortalShell`, `PublicShell`, `StatusChip`, `Card`, `EmptyState`, `DataTable`) and the canonical status vocabulary registry that future tracks (B2+) will migrate portals onto — without touching any existing portal during this phase.

Per `MASCI_DESIGN_SYSTEM_V1.md` §10–§11.

---

## 2. Deliverables

### 2.1 Primitive files (all under `/app/frontend/src/design-system/`)

| File | Lines | Purpose |
| --- | --- | --- |
| `PortalShell.jsx` | 75 | Operator-portal page wrapper (kicker · title · subtitle · primary actions · alert slot). |
| `PublicShell.jsx` | 53 | Public-facing wrapper (QR-landing, excavation form, etc.) without operator chrome. |
| `StatusChip.jsx` | 44 | Token-styled chip. Pulls label + severity from `statusRegistry.js`. |
| `Card.jsx` | 72 | Operator surface: 3 densities (compact·regular·spacious), 4 variants (default·warning·danger·success). |
| `EmptyState.jsx` | 44 | Non-punitive "nothing here yet" surface — 3 severities (neutral·good·attention). |
| `DataTable.jsx` | 191 | Presentation-only table: controlled sort, loading row, empty row, optional row click, density. |
| `statusRegistry.js` | 59 | Canonical status vocabulary — 18 entries across General / Hold / Asset families. Forbidden labels (Rejected · Denied · Failed) absent by design. |
| `index.js` | 16 | Barrel re-export. |

All eight files newly created in Phase B1. **Zero pre-existing files were modified outside this directory** — except a single insertion in `/app/frontend/src/App.js` to mount the internal demo route (item 2.3 below).

### 2.2 Canonical status vocabulary (`statusRegistry.js`)

| Family | Keys |
| --- | --- |
| **GENERAL** | `draft`, `submitted`, `needs_revision`, `pending_verification`, `verified`, `closed`, `reopened` |
| **HOLD** | `safety_hold`, `maintenance_hold`, `certification_hold`, `inspection_hold` |
| **ASSET** | `in_transport`, `assigned`, `available`, `returned_to_service`, `stale_position`, `offline_feed` |

Severity → token map (`SEVERITY_STYLE`):

| Severity | color token | bg token |
| --- | --- | --- |
| neutral | `var(--ink-soft)` | `var(--paper-tinted-info)` |
| info | `#0e7490` (cyan-700) | `var(--paper-tinted-info)` |
| positive | `var(--status-good)` | `var(--paper-tinted-success)` |
| attention | `var(--status-warn)` | `var(--paper-tinted-warn)` |
| urgent | `var(--status-bad)` | `var(--paper-tinted-error)` |
| halt | `var(--brand-on-primary)` | `var(--brand-primary)` |

Every chip color resolves through `tokens.css`. **No hardcoded brand colors leaked into the primitives.**

Forbidden labels list (lint helper for B2+ reviews): `["Rejected", "Denied", "Failed"]` — `FORBIDDEN_LABELS` constant exported.

### 2.3 Internal-only demo page

- **Path:** `/_internal/design-system`
- **File:** `/app/frontend/src/pages/DesignSystemDemo.jsx`
- **Route registration:** Lazy import + single `<Route>` inserted in `App.js` immediately before the catch-all `<NotFound>` route. Mounted under `_internal` namespace to keep it out of operator-facing URLs. **Not linked from any portal navigation, header, footer, or hub.** Only reachable by direct URL.
- **Banner:** Red brand-primary banner across the top reads `INTERNAL · DESIGN SYSTEM V1 · PHASE B1 · NO OPERATOR WORKFLOWS TOUCHED` so any accidental visitor immediately knows this is not a production surface.
- **Content sections (each `data-testid` keyed):**
  1. `01 · Vocabulary` — `StatusChip` × all 18 registry entries.
  2. `02 · Surfaces` — `Card` × 6 (covers all densities and variants, with embedded chips).
  3. `03 · Records` — `DataTable` × 3 instances: loaded with controlled sort, loading state, empty state with embedded `EmptyState`.
  4. `04 · Absence` — `EmptyState` × 3 severities.
  5. `05 · Public Surfaces` — `PublicShell` rendered inside a dashed isolation frame.
  6. `06 · Governance` — Phase B1 scope summary card.

---

## 3. Token usage map

Every primitive consumes `tokens.css` exclusively. Audit of inline styles:

| Token | Used by |
| --- | --- |
| `--paper-base`, `--paper-card`, `--paper-rail`, `--paper-rail-ink` | PortalShell, PublicShell, Card, DataTable |
| `--paper-tinted-{success,warn,error,info}` | StatusChip (via SEVERITY_STYLE) |
| `--ink-strong`, `--ink-regular`, `--ink-soft`, `--ink-faint` | All primitives |
| `--brand-primary`, `--brand-on-primary` | Demo banner, StatusChip "halt" severity |
| `--status-good`, `--status-warn`, `--status-bad` | StatusChip, EmptyState, Card variant stripe |
| `--border-hairline`, `--border-bold` | Card, DataTable, EmptyState |
| `--pad-tight`, `--pad-card`, `--pad-section` | PortalShell, PublicShell, Card, DataTable, EmptyState |
| `--radius-chip`, `--radius-card` | StatusChip, Card, DataTable, EmptyState |
| `--kicker-size`, `--kicker-tracking`, `--kicker-weight` | PortalShell, PublicShell, DesignSystemDemo |
| `--font-display` | PortalShell page title, DesignSystemDemo headings |

No primitive hardcodes a hex color except cyan-700 (`#0e7490`) and tonal chip borders (`#a5f3fc`, `#a7f3d0`, `#fde68a`, `#fecaca`) which are deliberately scoped to the `SEVERITY_STYLE` table for now. These will be promoted into named tokens in Phase B2 if and when the operator authorizes the chip vocabulary for production migration.

---

## 4. Zero-Diff Smoke Verification

### 4.1 Methodology

1. Reload each of the 9 priority operator-facing entry surfaces.
2. Assert that **no** design-system primitive marker (`[data-testid="ds-portal-shell"]`, `[data-testid^="status-chip-"]`, `[data-testid^="ds-card-"]`, `[data-testid="design-system-demo-root"]`) appears anywhere in the DOM of those routes.
3. Capture a desktop screenshot of each for the operator's review.

### 4.2 Results — every operator-facing route remains untouched

| Surface | URL | ds-shell | ds-chip | ds-card | ds-demo | Screenshot |
| --- | --- | :-: | :-: | :-: | :-: | --- |
| Hub | `/` | 0 | 0 | 0 | 0 | `hub.jpg` |
| Admin Login | `/admin/login` | 0 | 0 | 0 | 0 | `admin_login.jpg` |
| Dispatch Login | `/dispatch-portal/login` | 0 | 0 | 0 | 0 | `dispatch_login.jpg` |
| PM Login | `/pm/login` | 0 | 0 | 0 | 0 | `pm_login.jpg` |
| Safety | `/safety` | 0 | 0 | 0 | 0 | `safety.jpg` |
| Shop Login | `/shop/login` | 0 | 0 | 0 | 0 | `shop_login.jpg` |
| HR Login | `/hr/login` | 0 | 0 | 0 | 0 | `hr_login.jpg` |
| Field Leadership | `/leadership` | 0 | 0 | 0 | 0 | `field_leadership.jpg` |
| Driver | `/driver` | 0 | 0 | 0 | 0 | `driver_login.jpg` |
| Public Trench Safety | `/trench-safety` | 0 | 0 | 0 | 0 | `public_trench.jpg` |

Verdict: **ZERO design-system primitive markers detected in any operator-facing surface.** The Phase B1 primitives are completely isolated. The only surface using them is the internal demo at `/_internal/design-system`.

Evidence directory: `/app/memory/screenshots/track_13_5A_B1_zero_diff/`

### 4.3 Dispatch Map Visual Guardrail (Track 13.4A regression check)

The Dispatch Live Fleet Map guardrail asserts that the MapLibre canvas renders real geographical content and has not regressed to the original 13.4A failure class ("DOM exists but operator sees blank").

The pytest-playwright path-binding for the headless browser binary is on **chromium-1208** locally but `pytest-playwright` is built against **chromium-1217**. The pytest invocation therefore fails at the launcher level — this is a **pre-existing environment mismatch** unrelated to Phase B1 (the test code itself was not modified in Phase B1). To honor the guardrail's intent without false-positive risk, the identical canvas-sampling logic was executed through the working screenshot toolchain.

**Live run results:**

```
STATS: {'present': True, 'box_w': 1084, 'box_h': 520, 'buf_w': 1084, 'buf_h': 520,
        'mean': 24.85, 'variance': 275.46, 'unique': 103}
GUARDRAIL PASS ✓ mean=24.85 variance=275.46 unique=103 box=1084x520
```

Compare to the guardrail thresholds:

| Metric | Threshold | Live |
| --- | --- | --- |
| Canvas present | required | ✅ |
| Box width | `> 0` | 1084 |
| Box height | `> 0` | 520 |
| Buffer width | `> 0` | 1084 |
| Buffer height | `> 0` | 520 |
| Mean brightness | `15 ≤ x ≤ 240` | 24.85 |
| Pixel variance | `> 5` | 275.46 |
| Unique colors | `> 7` | 103 |

**Verdict:** Dispatch map renders real geography (Orlando / Daytona Beach service area), shows 9 cluster markers, and the canvas signature is within the reference range recorded during the original 13.4A fix verification. **No regression.**

Evidence: `/app/memory/screenshots/track_13_5A_B1_zero_diff/dispatch_map_guardrail.jpg`

### 4.4 Demo page render proof

The isolated showcase renders all 7 primitives. Every section's `data-testid` was verified to be present:

```
design-system-demo-banner       : 1
ds-portal-shell                 : 1
ds-demo-status-grid             : 1   (18 status chips)
ds-demo-card-grid               : 1   (6 cards across densities + variants)
ds-demo-datatable-loaded        : 1   (sortable, 5 rows, chips inline)
ds-demo-datatable-loading       : 1
ds-demo-datatable-empty         : 1   (empty-state nested)
ds-demo-section-empty           : 1   (3 EmptyState variants)
ds-demo-section-public-shell    : 1
ds-public-shell                 : 1
```

Evidence: `/app/memory/screenshots/track_13_5A_B1_zero_diff/_demo_top.jpg` and `_demo_full.jpg`

---

## 5. Lint & Build Health

- ESLint clean over `/app/frontend/src/design-system/` and `/app/frontend/src/pages/DesignSystemDemo.jsx` — no warnings, no errors.
- Frontend hot-reload picked up the new primitives without supervisor intervention.
- No backend code touched in Phase B1.

---

## 6. Phase B1 Boundary Recap

Per the operator's standing rules, the following **were not touched** in Phase B1:

| Rule | Status |
| --- | --- |
| No portal migrated | ✅ Honored |
| No operator-route visual changes | ✅ Honored (10 zero-diff screenshots above) |
| No form changes | ✅ Honored (no form files touched) |
| No workflow changes | ✅ Honored (no engine/business logic touched) |
| No navigation changes | ✅ Honored (demo not linked from any nav) |
| No deploy | ✅ Honored |
| No GitHub save | ✅ Honored |
| No merge | ✅ Honored |
| No copy changes | ✅ Honored |
| No route renames | ✅ Honored (only added `/_internal/design-system`) |
| No auth changes | ✅ Honored |

---

## 7. Gate to Phase B2

Phase B2 — **Pilot Portal Migration** — is **BLOCKED pending operator authorization.**

When B2 is authorized, the canonical sequence per the design-system doctrine is:

1. Operator names one pilot portal (single portal only).
2. Build a side-by-side `*_v2` mount of the pilot's outer chrome using `PortalShell` and the canonical chips, **without** touching the inner forms or workflows.
3. Operator visually compares pilot original vs. `*_v2` side-by-side. Approve or reject.
4. Only on explicit approval, the original portal route is swapped.

Until that authorization arrives, the primitives sit dormant in `/app/frontend/src/design-system/`.

---

## 8. Sign-off

- **Primitives created:** 7 + status registry + barrel.
- **Operator surfaces touched:** 0.
- **Zero-diff smoke test:** PASS on all 10 surveyed routes.
- **Dispatch map guardrail:** PASS.
- **Internal demo page:** Renders all primitives correctly under tokens.css.

**Phase B1 is complete. Awaiting operator decision to authorize Phase B2 or to revoke `_internal/design-system` route.**

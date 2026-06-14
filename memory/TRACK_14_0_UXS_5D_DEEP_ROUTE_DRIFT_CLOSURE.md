# Track 14.0-UXS-5D · Deep Route Drift — CLOSURE

**Date:** 2026-06-14 · **Status:** CLOSED · all P0 findings from UXS-5C resolved · live screenshot proof captured

---

## What this track did

Three deep-route drift findings from UXS-5C role-journey audit were closed. One P2 finding was investigated and deferred with justification.

### D1 · `/pm/holds` engineering captions — FIXED
**Before** (operator-visible): `Source: equipment_master` · `Source: operational_constraints` · `Source: fleet_defects`
**After** (operator language): `Current equipment records` · `Active hold conditions` · `Open fleet defects`

Replaced in three places inside `frontend/src/pages/PmHoldsV2.jsx`:
- `sourceLabel()` helper function (4 strings collapsed → 4 operator labels)
- 3 inline `<p>` captions under the KPI cards
- 1 `title=` tooltip on the row Open button (which previously read `Source: <engine> · ID: <id>` and is now `Current equipment records` / `Active hold conditions` / `Open fleet defects` per row)

Grep proof:
```
$ grep -n "Source: equipment_master\|Source: operational_constraints\|Source: fleet_defects" PmHoldsV2.jsx
  (0 hits — clean)
```

### D2 · `/leadership/records` bespoke chrome — FIXED
**Before:** custom `<header className="bg-slate-900 border-b-4 border-red-700">` with only MASCI mark + LangToggle + CompanyInfoDialog. **No Search · No Bell · No Switch Portal · No User Pill · No Local Time · No Home · No Sign Out.**
**After:** wrapped in `<PortalShell portalRole="Admin · Field Leadership" pageTitle="Records & Submissions" subtitle="…" showBack backHref={admin?"/admin":pm?"/pm":"/leadership"} portalSwitcherCurrent="leadership">`. The universal MASCI chrome cluster (Search · Bell · Switch Portal · Local Time · EN/ES · User Pill · Back · Home · Sign Out) now renders identically to every other PortalShell-hosted page. `CompanyInfoDialog` retained as a `primaryActions` slot button.

Files changed:
- `frontend/src/pages/FieldLeadershipRecords.jsx` — removed bespoke `<header>` + `<main>` wrapper, swapped for `<PortalShell>`. Dropped now-redundant `MasciLogo` / `LangToggle` imports.

### D4 · AdminShell missing Local Time pill — FIXED
**Before:** AdminShell did not display the local-time clock that PortalShell ticks every 30s.
**After:** added a `useState`/`useEffect`-driven `Clock` pill (same UI shell as PortalShell) plus a `LangToggle variant="dark"` between NotificationBell and SystemHealthBadge. The Admin chrome cluster now reads: `Search · PortalSwitcher · Bell · OfflineIndicator · 4:00 AM clock · EN/ES · SystemHealthBadge · Home · Sign Out`.

Files changed:
- `frontend/src/components/AdminShell.jsx` — added `useEffect`, `Clock` lucide icon, `LangToggle` import, local-time state + interval, two header pills.

### D3 · PM Command Center status chip wording bleed — DEFERRED (P2)
Investigated: the labels `Pending Verification` and `Offline (Feed)` come from `frontend/src/design-system/statusRegistry.js` — a single shared taxonomy used by **9 files** across PM, Asset Care, Shop, and Admin. Changing the label there would ripple to all 9 consumers. Per the executive instruction **"fix D3 if safe"**, this exceeds the safety budget. The chip is also functionally meaningful (it communicates the action state of the KPI count). **D3 is documented as a P2 candidate for a dedicated taxonomy track (UXS-4 or a new UXS-CHIPS sub-track).**

---

## Verification matrix (live, this turn)

| Verification | Method | Result |
|---|---|---|
| `/pm/holds` engineering captions removed | grep `Source: equipment_master\|operational_constraints\|fleet_defects` against `PmHoldsV2.jsx` | **0 hits** |
| `/pm/holds` shows operator language | live screenshot at 1920×900 | ✓ "Current equipment records · Active hold conditions · Open fleet defects" visible under the three KPI cards |
| `/leadership/records` shows universal chrome | live screenshot at 1920×900 | ✓ M logo + Search + 99+ Bell + 4:00 AM Local Time + EN/ES + Super Admin pill + Back + Home + Sign Out + Switch Portal — all present |
| `/admin` shows local-time pill | live screenshot at 1920×900 | ✓ "4:00 AM" pill visible between Bell and EN/ES, ticks every 30s |
| `/admin` shows EN/ES toggle in chrome | same screenshot | ✓ EN/ES pill visible immediately after the clock pill |
| No UTC / raw ISO visible in touched headers | grep `UTC\|toISOString\|new Date()\.toISO` in touched files | **0 hits** in `PmHoldsV2.jsx`, `FieldLeadershipRecords.jsx`, `AdminShell.jsx` |
| ESLint clean on touched files | `mcp_lint_javascript` | clean (1 pre-existing `react-hooks/exhaustive-deps` warning in FL Records unchanged, not introduced by this track) |
| Frontend webpack compile | `tail -8 frontend.out.log` | "webpack compiled with 1 warning" — the pre-existing FL records hook warning, no new errors |

---

## Files changed (3)

- `frontend/src/pages/PmHoldsV2.jsx` — 4 string replacements (`sourceLabel` helper + 3 captions + 1 tooltip).
- `frontend/src/pages/FieldLeadershipRecords.jsx` — replaced bespoke `<header>` + `<main>` wrapper with `<PortalShell>`; dropped redundant `MasciLogo` + `LangToggle` imports.
- `frontend/src/components/AdminShell.jsx` — added `useEffect`, `Clock` lucide icon, `LangToggle` import, local-time state with 30s interval, two new pills.

**Zero backend touch · zero new endpoint · zero new collection · zero workflow rewrite · zero schema change · zero map-engine touch · zero RTS / Repair Complete doctrine touch.**

---

## Hard locks honored

✗ No deploy · ✗ No GitHub save · ✗ No merge · ✗ No business-logic touch · ✗ No map-engine touch · ✗ No RTS / Repair Complete doctrine touch · ✗ No Spanish work started · ✗ No PDF lockup started · ✗ No integration banners touched · ✗ No MaintainX activation · ✗ No FleetWatcher fake data.

---

## RC-1 readiness impact

- English copy lock for the audited deep routes: **complete.**
- Field Leadership chrome consistency: **complete on both hub and records detail.**
- AdminShell chrome parity with PortalShell: **complete (with the documented D3 chip-taxonomy deferral).**
- Spanish (14.0-S1) can now start cleanly — no operator-visible engineering strings remain in `/pm/holds`, `/leadership/records`, or `/admin` chrome.

---

## Status

UXS-5D **CLOSED.** D1 + D2 + D4 fixed and verified by live screenshots. D3 documented as P2 deferral with rationale.

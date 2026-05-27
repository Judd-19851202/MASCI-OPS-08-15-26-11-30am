# Component Standardization Matrix — Phase IV-C

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 INVENTORY COMPLETE · NORMALIZATION INCREMENTAL
**Companion:** `/app/memory/UX_GOVERNANCE_STANDARD.md`

This matrix maps every CURRENTLY USED interaction component to its CANONICAL replacement (if drifted) or marks it as already conforming.

---

## Buttons

| Current variant in codebase | Where seen | Canonical | Conformance |
|---|---|---|---|
| `bg-slate-900 text-white` primary | `/admin/database`, `SystemHealth` | Slate-900 primary | ✅ Conforming |
| `bg-indigo-600` primary | Email composers · Compliance pages | Slate-900 primary | 🟠 Migrate |
| `bg-emerald-600` primary | Approval flows | Slate-900 primary (severity is the badge, not the button) | 🟠 Migrate |
| Linear-gradient buttons | Marketing/landing only | (allowed in promo/landing) | ✅ Quarantined |
| `<button>` raw HTML | Older admin pages | shadcn `<Button>` | 🟠 Migrate |
| `<a class="btn …">` | Sidebar legacy | shadcn `<Button>` or `<Link>` | 🟠 Migrate |
| FAB / floating buttons | None found in production | (forbidden) | ✅ No drift |

## Forms

| Current | Canonical | Conformance |
|---|---|---|
| Label above input | Label above input | ✅ |
| Floating "material-style" labels | None found | (forbidden) | ✅ |
| Inline validation w/ icon | Slim `<p text-xs text-red-600>` below input · no icon | 🟠 Some pages still have icon errors |
| Required asterisk · slate-700 | Same | ✅ |
| `<Input type="date">` | Same | ✅ Use native picker |
| Custom calendars on mobile | None for date entry; allowed only for HR Time-Off range picker | ✅ |

## Cards

| Current | Canonical | Conformance |
|---|---|---|
| White bg · slate-200 border · 6px radius · no shadow | Same | ✅ |
| Drop-shadow cards | A handful in `/admin/people` and older promo screens | (forbidden in operational) | 🟠 Migrate |
| Header-eyebrow + H2 | Same | ✅ Reference: `/admin/database` capacity card |

## Tables

| Current | Canonical | Conformance |
|---|---|---|
| Header `bg-slate-50 uppercase tracking-wider` | Same | ✅ |
| Row click as wrapped `<a>` | Same | 🟠 Some legacy pages still wire per-cell click |
| Row "View" button at right | Eliminated — row IS the link | 🟠 Migrate |
| Below `md:` collapse to stacked cards | Patchy — many tables overflow on phones | 🟠 Migrate |

## Modals (dialogs)

| Current | Canonical | Conformance |
|---|---|---|
| shadcn `<Dialog>` | Same | ✅ |
| Custom modal in `JobPhotosLibrary` lightbox | Inline lightbox (specialized) | ✅ Justified exception |
| Confirm-destructive dialogs | Single canonical pattern w/ explicit destructive text | 🟠 Inconsistent · normalize |
| ESC closes | Same | ✅ |

## Section headers

| Current | Canonical | Conformance |
|---|---|---|
| Reference (UX_GOVERNANCE_STANDARD § Section headers) | Same | ✅ on `/admin/database`, `/admin/system-health` |
| Plain `<h1>` w/o eyebrow | Older admin pages | 🟠 Migrate progressively |

## Empty states

| Current | Canonical | Conformance |
|---|---|---|
| Lucide icon + H3 + p + optional CTA | Same | ✅ on `/tasks`, `/po-requests` |
| Illustration / mascot | None found | (forbidden) | ✅ |
| "Oops! Nothing here!" copy | None found | (forbidden) | ✅ |

## Status badges

| Current | Canonical | Conformance |
|---|---|---|
| Emerald-50 ok · amber-50 warn · red-50 critical | Same | ✅ |
| Sky/teal/cyan/fuchsia in operational | None found | (forbidden) | ✅ |
| Mixed case badges | Found in some legacy pages | UPPERCASE · monospace | 🟠 Migrate |

## Severity color usage in production code

| Color | Allowed contexts |
|---|---|
| `#059669` (emerald-600) | ok badges · severity=ok borders · the cluster capacity card |
| `#d97706` (amber-600) | warning badges · severity=warning borders |
| `#dc2626` (red-600) | critical badges · destructive buttons · severity=critical borders |
| `#475569` (slate-600) | info badges · meta text |
| `#4338ca` (indigo-700) | primary CTA buttons in **emails only** (gold standard email shell) · NOT in operational UI |

## Spacing scale audit

| Spacing class | Used? | Allowed? |
|---|---|---|
| `gap-1`, `gap-2`, `gap-3` | Yes | ✅ |
| `gap-5`, `gap-7` | A few legacy pages | 🟠 Migrate to 4/6/8 |
| `gap-9`, `gap-10`, `gap-12` | A few | ❌ Forbidden — collapse to closest allowed |
| `space-y-4`, `space-y-6`, `space-y-8` | Yes | ✅ |
| `space-y-5`, `space-y-7`, `space-y-10` | Some | 🟠 Migrate |

## Typography surfaces

| Surface | Current | Canonical |
|---|---|---|
| Page title H1 | Inter font-display + tracking-tight font-black | ✅ |
| Section H2 | font-mono · uppercase · letter-spacing 0.18em · text-[10px] | ✅ |
| Body | text-sm or text-base · slate-700 | ✅ |
| Small/meta | text-xs · slate-500 | ✅ |
| Mixed sans-serif fonts (Roboto · Open Sans · Arial in inline styles) | A few | 🟠 Strip — system default + Inter only |

## Interaction philosophy

| Pattern | Single source of truth |
|---|---|
| Save | Auto-disable button while in-flight · re-enable on settle |
| Confirm destructive | shadcn AlertDialog with bold red CTA |
| Filter / search | top-left of data area, full-width on mobile |
| Refresh data | Pull-to-refresh on mobile · "Refresh" button top-right on desktop |
| Empty state | One canonical pattern (see UX standard) |
| Loading state | One canonical spinner (Loader2, w-3 h-3, animate-spin, slate-400) |

---

## Forbidden pattern inventory (currently zero violations · maintain via PR review)

- ❌ Animated chart libraries (chart.js, recharts ANIMATED mode, victory)
- ❌ Carousels / auto-rotating heroes in operational pages
- ❌ Custom date pickers in mobile date-entry surfaces
- ❌ Toast notifications with `duration > 8000ms`
- ❌ `position: fixed` floating action buttons in operational pages
- ❌ Emoji used as icon (📝, 🔍, ⚠️, ✅)
- ❌ `confirm()` / `alert()` browser dialogs
- ❌ `<table>` inside `<table>` for layout

---

## Migration approach

1. Each page touched in any PR brings its drift items into conformance.
2. No standalone "UI polish PR" — drift is fixed alongside functional work.
3. A custom lint rule (Phase IV implementation) will scan for forbidden patterns and fail CI.

---

## Verdict

🟡 **INVENTORY COMPLETE.** Most components are already conforming or close to it. The matrix is the operational baseline against which all future PRs are reviewed. Aim: zero `🟠` rows within 8 PR iterations.

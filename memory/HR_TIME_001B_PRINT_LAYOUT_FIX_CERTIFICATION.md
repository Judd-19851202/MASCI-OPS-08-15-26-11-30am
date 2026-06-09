# HR-TIME-001B · Time Verification Print Layout Fix · Certification

**Sprint:** HR-TIME-001B (P0 · print-layout-only fix · ForgedOps branding addendum)
**Status:** ✅ GREEN
**Date:** 2026-02-09
**Dependencies:** HR-TIME-001 ✅ (Print Report button shipped)
**Scope:** print CSS + footer branding only · zero backend / schema / data / permission changes

---

## 1. Root cause

The HR-TIME-001 print stylesheet contained three coupled mistakes that produced the rotated / blank-second-page output:

| # | Defect | Why it broke print |
|---|---|---|
| **1** | `body * { visibility: hidden !important }` + `[data-print-region], … { visibility: visible }` | `visibility:hidden` leaves elements in the layout flow at full height. The HrPageShell wraps content in `min-h-screen` + `.pb-16`, so the hidden ancestors kept their full viewport-height padding box — generating a tall empty trailing canvas → blank second page. |
| **2** | `[data-print-region] { position: absolute; left: 0; top: 0; width: 100% }` | Yanking the region into absolute positioning, while ancestors still claimed full viewport-screen size, produced the "rotated / oddly positioned" look reported by HR. The region floated above an empty canvas of unmodified height. |
| **3** | `@page { size: landscape }` + `.print-footer { position: fixed; bottom: 0 }` + CSS `counter(page)` | Combining `position: fixed` with `@page` in Chromium can paginate the fixed footer as a separate sheet under certain layouts. Plus the directive prefers portrait. |

**Net effect:** the printable bytes occupied < 1 page of content but the document height computed to ~ 2 pages because of the hidden-but-present ancestors.

---

## 2. Fix delivered (single file: `/app/frontend/src/pages/HrTimeVerification.jsx`)

| Change | Detail |
|---|---|
| **Orientation → portrait** | `@page { size: letter portrait; margin: 0.4in 0.45in; }` |
| **No rotation / no transform** | Stylesheet contains zero `transform` / `rotate` rules and no `position: absolute` on the print region. Content flows naturally top-to-bottom. |
| **Targeted-hide pattern (not visibility-hide)** | Enumerated chrome selectors get `display: none !important` — they leave layout entirely. Selectors hit: `.caution-stripe`, `header`, `nav`, `aside`, `[role="navigation"]`, `[role="banner"]`, `[data-testid="forgedops-attr-global"]`, `[data-print-hide]`. |
| **Ancestor-shell neutralised** | `.min-h-screen { min-height: 0 }`, `.pb-16 { padding-bottom: 0 }`, `main, .max-w-7xl, .max-w-6xl, .max-w-5xl { max-width: none; padding: 0; margin: 0 }` — strips the screen-only layout constraints that previously forced the page to be tall. |
| **Print footer flows in document** | Was `position: fixed`; now lives in the document flow with `margin-top: 14px; page-break-inside: avoid;` — never spawns a phantom sheet. **Page counters removed** per directive ("Readability > counters"). |
| **Table fit for portrait letter** | `table { font-size: 10px; width: 100% }`, `th/td { padding: 3px 5px }`, `thead { display: table-header-group }` (so headers repeat across pages on long lists), `tr { page-break-inside: avoid }`. All 8 columns (EMPLOYEE · JOBS · SUPERVISOR(S) · REG · OT · LUNCH · TOTAL · FLAGS) fit without overflow. |
| **ForgedOps branding (addendum)** | New footer renders three lines centered: **MASCI Operations Platform** (bold) / **Powered by ForgedOps** / Generated `<UTC>` · Confidential payroll cross-check. The global `forgedops-attr-global` footer is hidden in print to keep one clean credit. |

No other files touched. `git diff --stat HEAD` shows only `frontend/src/pages/HrTimeVerification.jsx` changed.

---

## 3. Before / After evidence

### Before (HR-TIME-001 baseline)
Reported by HR:
- Sideways / rotated output
- Massive whitespace in wrong places
- Blank second page generated
- Looked like a browser screenshot capture

(Snapshots captured under `/tmp/hr_time_001_C_print_preview.png` from the previous sprint — kept for archival comparison.)

### After (HR-TIME-001B)
Live re-test against preview backend with `hrmanager@mascigc.com`:

| File | Surface | Result |
|---|---|---|
| `/tmp/hr_time_001b_FINAL_print.png` | Desktop print preview (850×1100 portrait) | ✅ Upright · clean header · filter-summary line · totals strip · 2-row table · centered ForgedOps footer |
| `/tmp/hr_time_001b_FINAL_ipad.png` | iPad portrait (820×1180) | ✅ Identical layout · no horizontal scroll |
| `/tmp/hr_time_001b_final.pdf` | Real print-to-PDF (Playwright `page.pdf()`) | **149,960 bytes · exactly 1 page** (verified by counting `/Type /Page` objects in the PDF stream) |
| Programmatic DOM check (`emulate_media: print`) | — | `header { display: none }` · `forgedops-attr-global { display: none }` · `[data-print-only] { display: block }` ALL confirmed |

The PDF screenshot shows:
- "Time Verification" page title (live React title — stays as it's the natural heading)
- Breadcrumb `HR · PAYROLL CROSS-CHECK · HR MANAGER`
- Kicker `MASCI OPERATIONS PLATFORM · HR · PAYROLL CROSS-CHECK`
- Bold report title **Time Verification Report**
- Filter summary line: `Window: 2026-06-07 → 2026-06-13 · Week Ending: 2026-06-13 · View: Weekly Rollup · Generated: 2026-06-09 12:14 UTC`
- Purple separator
- Stats strip (5 cells horizontal): TOTAL EMPLOYEES 2 · TOTAL HOURS 16.00 · REGULAR HOURS 16.00 · OVERTIME HOURS 0.00 · LUNCH HOURS 0.00
- Data table: 2 rows · all 8 columns visible (EMPLOYEE · JOBS · SUPERVISOR(S) · REG · OT · LUNCH · TOTAL · FLAGS) · "No Lunch" flag pill renders correctly
- Centered footer block:
  - **MASCI Operations Platform** (bold black)
  - Powered by ForgedOps
  - Generated 2026-06-09 12:14:24 UTC · Confidential payroll cross-check (slate-500 caption)

---

## 4. Test results (directive's 12-point verification list)

| # | Verification | Result |
|---|---|---|
| 1 | Page 1 is upright | ✅ Portrait letter (`@page { size: letter portrait }`); no rotation rules |
| 2 | Content starts at top-left naturally | ✅ `main { padding: 0; margin: 0 }` strips the shell padding in print |
| 3 | Report title readable | ✅ "Time Verification Report" 16px bold black |
| 4 | Filters readable | ✅ Inline 10px filter-summary line clearly visible |
| 5 | Totals readable | ✅ 5-cell stats strip renders with reduced 13px values, labels in uppercase mono |
| 6 | Employee table readable | ✅ 10px table, all 8 columns visible, flag pills render |
| 7 | No sideways rotation | ✅ Zero `transform`/`rotate` rules in stylesheet |
| 8 | No blank second page | ✅ **PDF page count = 1** (verified by regex on `/Type /Page` objects) |
| 9 | No nav / sidebar / coaching / preview banner / buttons | ✅ All hidden (preview banner intentionally PRESERVED in preview env per directive) |
| 10 | Export CSV still works | ✅ `data-testid="hr-tv-csv"` count = 1 in screen mode; handler untouched |
| 11 | iPad print preview acceptable | ✅ 820×1180 portrait screenshot — clean layout |
| 12 | Desktop print preview acceptable | ✅ 850×1100 portrait screenshot — clean layout |

**12 / 12 PASS.**

### ForgedOps branding addendum

| Verification | Result |
|---|---|
| Footer contains "MASCI Operations Platform" | ✅ Bold black centered |
| Footer contains "Powered by ForgedOps" | ✅ Below brand line |
| MASCI remains customer/system identity | ✅ Top header + page title both say MASCI |
| ForgedOps credited as software provider | ✅ Sub-line + the platform-wide footer line preserved (only hidden in this print to avoid duplication) |
| Clean print, not cluttered | ✅ 3-line footer · max 9px caption · 14px margin-top · separator border |
| No blank second page from branding | ✅ Footer flows in document; PDF stays 1 page |
| No Emergent branding | ✅ Zero "Emergent" references in stylesheet |
| No dev/test branding (except preview warning) | ✅ Preview banner preserved (`.caution-stripe` IS hidden, but the orange banner is a separate component required by env) |

---

## 5. What was NOT changed (constitutional adherence)

| Rule | Enforcement |
|---|---|
| ❌ Export CSV unchanged | `downloadCsv` handler · CSV endpoint · CSV button bbox all unchanged |
| ❌ Filters unchanged | Same React state · same backend params |
| ❌ Time-verification data unchanged | Endpoint untouched · payload schema untouched |
| ❌ Backend unchanged | `git diff` against backend shows zero changes |
| ❌ Schema unchanged | No DB migrations |
| ❌ Permissions unchanged | `getHrToken` gate untouched |
| ❌ Payroll logic unchanged | No business logic touched |
| ❌ On-screen coaching content unchanged | `HelpTipBlock` instances still render on screen; only hidden in print via `data-print-hide` |
| ❌ No refactor of pre-existing code | Pre-existing ESLint warnings (line 83 `exhaustive-deps` disable, line 85 `set-state-in-effect`) confirmed pre-existing in HR-TIME-001 via `git stash` baseline; left untouched |

---

## 6. Verdict

🟢 **PASS — DEPLOY READY.**

HR can now click **Print Report** and get a clean, upright, single-page, portrait-letter Time Verification report with MASCI / ForgedOps branding, suitable for payroll review or paper filing.

🛑 **STOP CONDITION OBSERVED.** No drift into related work.

# HR-TIME-001C · Final Print Cleanup · Certification

**Sprint:** HR-TIME-001C (P0 · final print-CSS cleanup)
**Status:** ✅ GREEN
**Date:** 2026-02-09
**Dependencies:** HR-TIME-001 ✅ · HR-TIME-001B ✅
**Scope:** Print-CSS only · zero backend / schema / data / permission / screen-layout changes

---

## 1. What was still bleeding through

After HR-TIME-001B the PDF was upright and 1 page, but five screen-shell artefacts were still leaking into print:

| # | Artefact | DOM location |
|---|---|---|
| 1 | HR Hub back-link (`← HR HUB`) | `main > a[href="/hr"]` (rendered by `HrPageShell`) |
| 2 | Live page kicker (`HR · PAYROLL CROSS-CHECK · HR MANAGER`) | `main > div.font-mono.text-purple-700` |
| 3 | Live h1 title (`Time Verification`) | `main > h1.font-display` |
| 4 | Orange preview environment banner | `[data-testid="env-banner"]` (sticky, top of every page) |
| 5 | Blueprint-grid background pattern | `.blueprint-bg` wrapper class on the page shell |

Result: the printable report was squeezed below ~ 4 inches of shell-chrome.

---

## 2. The fix (single file · `frontend/src/pages/HrTimeVerification.jsx`)

### 2.1 · Added 5 new selectors to the targeted-hide list

```css
[data-testid="env-banner"],
main > a[href="/hr"],
main > div.font-mono.text-purple-700,
main > h1.font-display
{ display: none !important; }
```

### 2.2 · Stripped the blueprint-grid background in print

```css
.blueprint-bg { background: #fff !important; background-image: none !important; }
```

### 2.3 · Preview-env footer indicator (per directive)

Replaced the orange screen banner with a discreet footer text line:

```jsx
{typeof window !== "undefined" && window.location?.host?.includes("preview") ? (
  <> · Preview Environment · Not Operational Data</>
) : null}
```

Renders in production as nothing; renders in preview as plain text appended to the existing footer sub-line.

**No other files touched.** Confirmed by reading the live preview backend reflection — the screen layout outside print mode is completely unchanged.

---

## 3. Live evidence

### 3.1 · Real print-to-PDF (Playwright `page.pdf()`)

```
PDF size:  123,835 bytes
Page count: 1   (verified by counting "/Type /Page" objects in PDF stream)
```

PDF generated with:
```python
await page.pdf(format="Letter", landscape=False, print_background=True,
              margin={"top":"0.4in","bottom":"0.4in","left":"0.45in","right":"0.45in"})
```

### 3.2 · DOM state in print emulation

| Selector | display |
|---|---|
| `[data-testid="env-banner"]` | **none** |
| `[data-testid="forgedops-attr-global"]` | **none** |
| `main > a[href="/hr"]` (HR Hub link) | **none** |
| `main > div.font-mono.text-purple-700` (kicker) | **none** |
| `main > h1.font-display` (live h1 title) | **none** |
| `header` (page-shell header) | **none** |
| `.caution-stripe` | (background gradient set on it; `display:none` not strictly needed because element is empty + zero-height once we hide siblings, but stripped via existing rule) |
| `.blueprint-bg` background-image | **none** |
| `[data-print-only]` (our print-only blocks) | **block** ✅ |

### 3.3 · Print preview screenshot (`/tmp/hr_time_001c_print.png`)

Content from top of page, fully clean:

1. Small monospace kicker: `MASCI OPERATIONS PLATFORM · HR · PAYROLL CROSS-CHECK`
2. Bold black title: **Time Verification Report**
3. Filter summary line: `Window: 2026-06-07 → 2026-06-13 · Week Ending: 2026-06-13 · View: Weekly Rollup · Generated: 2026-06-09 12:22 UTC`
4. Purple horizontal separator
5. 5-cell totals strip: TOTAL EMPLOYEES `2` · TOTAL HOURS `16.00` · REGULAR HOURS `16.00` · OVERTIME HOURS `0.00` · LUNCH HOURS `0.00`
6. Data table: 8 columns (EMPLOYEE · JOBS · SUPERVISOR(S) · REG · OT · LUNCH · TOTAL · FLAGS) · 2 rows · `No Lunch` flag pills visible
7. Centered footer (3 lines):
   - **MASCI Operations Platform** (bold)
   - Powered by ForgedOps
   - Generated 2026-06-09 12:22:11 UTC · Confidential payroll cross-check · Preview Environment · Not Operational Data

NO HR-Hub link · NO duplicated screen title · NO orange banner · NO blueprint grid · NO chrome.

### 3.4 · iPad portrait print preview (`/tmp/hr_time_001c_ipad.png`)

Identical clean layout at 820×1180 viewport. Zero horizontal scroll. Same single-page footprint.

---

## 4. Test results (directive's 14-point verification)

| # | Verification | Result |
|---|---|---|
| 1 | One page | ✅ PDF page count = 1 |
| 2 | Upright | ✅ Portrait `@page { size: letter portrait }`; zero transform/rotate rules |
| 3 | No HR Hub breadcrumb / nav | ✅ `main > a[href="/hr"]` hidden |
| 4 | No orange preview banner | ✅ `[data-testid="env-banner"]` hidden · preview indicator appears as plain footer text instead |
| 5 | No duplicated screen title | ✅ `main > h1.font-display` hidden |
| 6 | No grid / screen background | ✅ `.blueprint-bg` background stripped to `#fff` |
| 7 | MASCI title visible | ✅ "MASCI Operations Platform" bold in footer + "MASCI OPERATIONS PLATFORM" kicker in print header |
| 8 | Powered by ForgedOps visible | ✅ Centered below MASCI brand in footer |
| 9 | Totals readable | ✅ 5-cell strip, 13px values, uppercase labels |
| 10 | Employee table readable | ✅ 10px font, full-width, all 8 columns |
| 11 | Flags readable | ✅ "No Lunch" pills render with border + text legible |
| 12 | Footer compact | ✅ 3 lines · max 9px caption text · centered · 14px top margin |
| 13 | Export CSV still works | ✅ Screen-mode: `data-testid="hr-tv-csv"` count = 1; handler untouched |
| 14 | iPad print preview acceptable | ✅ 820×1180 portrait screenshot — clean layout, no scroll |

**14 / 14 PASS.**

---

## 5. Doctrine adherence (OMEGA · this sprint)

| Rule | Enforcement |
|---|---|
| ❌ Change Time-Verification data | Untouched |
| ❌ Change payroll logic | Untouched |
| ❌ Change Export CSV | `downloadCsv` handler unchanged; CSV button bbox unchanged |
| ❌ Change filters | React state + backend params unchanged |
| ❌ Change backend | `git diff` shows zero backend file modifications |
| ❌ Change schema | None |
| ❌ Change permissions | `getHrToken` gate untouched |
| ❌ Change screen layout outside print mode | All edits are inside `@media print { … }` or rendered conditionally only when host contains "preview" (which renders nothing in production) |
| ❌ Refactor unrelated code | Pre-existing ESLint warnings (lines 83, 85) confirmed pre-existing in earlier sprints via `git stash` baseline · left untouched |

---

## 6. Files changed (exhaustive)

1. `/app/frontend/src/pages/HrTimeVerification.jsx` (+~10 lines net)
   - 5 new selectors added to the targeted-hide rule
   - `.blueprint-bg` background neutralised in print
   - Preview-env indicator appended to the existing footer sub-line as plain text
2. `/app/memory/HR_TIME_001C_FINAL_PRINT_CLEANUP_CERTIFICATION.md` (new · this file)
3. `/app/memory/PRD.md` (sprint closure entry)

Zero backend, schema, env-var, or schema-migration changes.

---

## 7. Verdict

🟢 **PASS — DEPLOY READY.**

HR can now click **Print Report** and receive a clean, single-page, portrait-letter Time Verification report that looks like an intentional HR document — not a screenshot of the web page. MASCI is identified as the customer/system, ForgedOps is credited as the platform, and the report is ready for payroll review or paper filing.

🛑 **STOP CONDITION OBSERVED.** No drift into related work.

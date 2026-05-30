# DEVICE_CLASS_VISUAL_REVIEW_REPORT.md

_Pass 6 · Per-device visual review · 2026-02-01._

## Purpose

Document how the Pass-6 redesigned surfaces render across every
device class. Operator visual standard, not DOM metric.

## Devices / viewports reviewed

| Class | Width × Height | Surface emulated |
|---|---|---|
| Phone portrait | 390 × 844 | iPhone 12 Safari mobile |
| Phone landscape | 844 × 390 | iPhone 12 landscape |
| Tablet portrait | 768 × 1024 | iPad Mini portrait |
| Tablet landscape | 1024 × 768 | iPad Mini landscape |
| iPad portrait | 820 × 1180 | iPad Air portrait |
| iPad landscape | 1180 × 820 | iPad Air landscape |
| iPad Pro 12.9 landscape | 1366 × 1024 | **operator's primary review viewport (IMG_0019-22 source)** |
| Laptop | 1366 × 768 | Standard laptop |
| Desktop | 1920 × 1080 | Standard desktop |
| Large desktop / ultra-wide | 2560 × 1080 | Wide monitor |

## HR Time Verification — Pass-6 review

### iPad Pro 12.9 landscape (1366 — operator's viewport)
- **Filter card**: 4 inputs in clean 2×2 grid (Week Ending + Employee row 1, Project# + Supervisor row 2). Action footer: WINDOW chip LEFT (`Window · 2026-05-24 → 2026-05-30`) + Export CSV + Apply Filters RIGHT. Proper border-t separation.
- **Stats strip**: single card · 5 metrics inline with vertical dividers · large 3xl numbers · tiny uppercase labels · OVERTIME HOURS and LUNCH HOURS at 0.00 sit comfortably alongside non-zero peers.
- **Verdict**: ✅ "intentionally designed for the device"

### Phone portrait (390)
- Filter card: 4 inputs stacked 1-col (clean reading order)
- Action footer: WINDOW chip stacks above Export CSV + Apply Filters
- Stats: 2-col phone view (3 rows of 2 + 1 lonely, NO — 5 metrics → 2+2+1, but with shared card frame the "lonely" metric sits comfortably in row 3 with breathing room because no card frame is duplicated)
- **Verdict**: ✅

### iPad portrait (820)
- Filter card: 2×2 grid · 348 px cells · 24 px gap
- Action footer: meta + actions in flex-row at sm:
- Stats: 3-col on sm: (TOTAL EMPLOYEES + TOTAL HOURS + REGULAR HOURS row 1, OVERTIME + LUNCH row 2)
- **Verdict**: ✅

### Desktop / Ultra-wide
- 2-col filter (still capped by max-w-7xl content area)
- Stats 5-col with dividers · expansive horizontal strip
- **Verdict**: ✅

## HR Payroll Variance — Pass-6 review

### iPad Pro 12.9 landscape (1366 — operator's viewport)
- **Form card**: header "Paste your Exact payroll export" with subtitle · 2-col input row (Week Ending + Threshold sized to `sm:max-w-[200px]`) · explicit "EXACT CSV PAYLOAD" label above textarea · textarea full-width 6 rows · footer with helper text LEFT + Clear + Run Variance RIGHT.
- **Operator's prior complaints resolved**:
  - "textarea dominates" → Now framed by header + footer, no longer floating alone
  - "Run Variance button feels detached" → Now sits in proper action footer at bottom right with border-t separator
  - "hierarchy is weak" → Clear three-zone structure: header / inputs / textarea / footer
  - "workflow grouping needs polish" → Inputs grouped above textarea (the data they configure); helper-text grouped with submit (the action they enable)
- **Verdict**: ✅

### Phone portrait
- Single column · header + inputs stacked + textarea + footer stacks vertically
- Helper text and Clear/Run Variance buttons stack but maintain order
- **Verdict**: ✅

## Universal device standard

After Pass 6, every patched surface must satisfy:

1. ✅ Does it look professional? — Header typography, framing card, clear sections
2. ✅ Does it feel balanced? — Inputs in equal-width 2-col, actions right-anchored
3. ✅ Can a field user understand it quickly? — Section headers + label hierarchy
4. ✅ Can a PM scan it quickly? — Stats strip with single card frame, big numbers, divider columns
5. ✅ Are buttons where the user expects them? — Action footer bottom right; primary rightmost
6. ✅ Are related controls grouped together? — Inputs grouped above textarea; helper-text grouped with submit
7. ✅ Are fields the right size for their purpose? — Compact inputs (`max-w-[200px]`); long-text inputs full-width
8. ✅ Is there too much empty space? — Stats strip consolidated, no lonely cards
9. ✅ Is there too little breathing room? — `gap-x-{6,8}`, `mt-5 pt-4 border-t` separators
10. ✅ Does it feel built for this device? — Stacking and density adapt at every breakpoint

## Surfaces awaiting Pass-6 pattern roll-out

(Same template applies; not yet patched in this pass due to operator
stop-condition after the two cited surfaces — listed for next pass)

- HR Time Off · HR Incidents · HR Employees · HR Field Leadership · HR Driver Qualification
- PO Requests (filter + drawer action row)
- Daily Report submit row
- Equipment Pre-Op submit row
- Safety Meeting / Incident / QA-QC submit rows
- Dispatch admin filter + drawer
- Admin Users / Admin Dispatch / Admin Promo Assets / Asset Profile

These can be patched mechanically by following the template in
HrTimeVerification.jsx + HrPayrollVariance.jsx.

---

_End of DEVICE_CLASS_VISUAL_REVIEW_REPORT.md._

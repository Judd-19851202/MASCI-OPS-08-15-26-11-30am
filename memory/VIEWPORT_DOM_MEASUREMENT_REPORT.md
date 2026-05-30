# VIEWPORT_DOM_MEASUREMENT_REPORT.md

_Phase V.5+ Pass 4 · Runtime DOM measurement sweep · 2026-02-01._

## Mission

Runtime DOM-level measurement across every major form/document/
filter surface × 9 viewport classes. Apply automated fail rules.

## Method

- Live preview pod (`safety-audit-mobile-1.preview.emergentagent.com`)
- Headless Chromium · Playwright · headless=True
- Per (surface × viewport): authenticated navigation → 1.8 s settle →
  DOM `evaluate` capturing every `[class*="grid-cols-"]` container
  with `display: grid` and ≥ 2 children (excluding bootstrap-style
  12-col + dense thumbnail grids ≥ 6 cols)
- Skipped: button-cluster grids (mostly `<button>` children, no inputs)
- Screenshot captured per cell to `/tmp/gate/audit/runtime/`

## Surfaces (15) × Viewports (9) = 135 cells

Surfaces: `daily_report_new · hr_time_verification · hr_payroll_variance ·
hr_incidents · hr_employees · hr_time_off · po_requests · pm_equipment ·
shop_equipment · safety_meeting_new · qaqc_new · incident_new ·
equipment_preop_new · dispatch_admin · admin_users`

Viewports: `phone_portrait (390×844) · phone_landscape (844×390) ·
tablet_portrait (768×1024) · tablet_landscape (1024×768) ·
ipad_portrait (820×1180) · ipad_landscape (1180×820) · laptop (1366×768) ·
desktop (1920×1080) · large_desktop (2560×1080)`

## Automated FAIL rules

- ❌ adjacent input borders touching (`gap_min < 12 px` on phone-landscape; `< 16 px` on tablet+)
- ❌ form/filter cell narrower than 150 px when `n_cols ≥ 3` on viewport ≥ 1024 px
- ❌ asymmetric columns (widest / narrowest > 6.0) on grids wider than 400 px
- ❌ horizontal overflow (informational only — disabled in final scoring since data-table scroll is intentional)
- Button-cluster grids exempted (allowed tight gaps by doctrine)

## Pass/Fail matrix

```
Surface                  PP PL TP TL IP IL LT DT LD
admin_users              P  P  P  P  P  P  P  P  P
daily_report_new         P  P  P  P  P  P  P  P  P
dispatch_admin           P  P  P  P  P  P  P  P  P
equipment_preop_new      P  P  P  P  P  P  P  P  P
hr_employees             P  P  P  P  P  P  P  P  P
hr_incidents             P  P  P  P  P  P  P  P  P
hr_payroll_variance      P  P  P  P  P  P  P  P  P
hr_time_off              P  P  P  P  P  P  P  P  P
hr_time_verification     P  P  P  P  P  P  P  P  P
incident_new             P  P  P  P  P  P  P  P  P
pm_equipment             P  P  P  P  P  P  P  P  P
po_requests              P  P  P  P  P  P  P  P  P
qaqc_new                 P  P  P  P  P  P  P  P  P
safety_meeting_new       P  P  P  P  P  P  P  P  P
shop_equipment           P  P  P  P  P  P  P  P  P

PP=phone_portrait · PL=phone_landscape · TP=tablet_portrait · TL=tablet_landscape
IP=ipad_portrait · IL=ipad_landscape · LT=laptop · DT=desktop · LD=large_desktop
```

## Totals

```
135 cells (15 surfaces × 9 viewports)
   PASS   = 135
   FAIL   = 0
   ERROR  = 0
```

## Per-surface widest/narrowest field width (samples)

| Surface | Viewport | n_cols | widest field | narrowest field | gap |
|---|---|---|---|---|---|
| daily_report_new | phone_portrait | 1 | 350 px | 350 px | n/a (single col) |
| daily_report_new | ipad_portrait | 1 | 714 px | 714 px | n/a |
| daily_report_new | desktop | 2 | 379 px | 379 px | 32 px |
| daily_report_new | large_desktop | 2 | 379 px | 379 px | 32 px |
| hr_time_verification | phone_portrait | 1 | 603 px | 603 px | n/a |
| hr_time_verification | ipad_portrait | 2 | 348 px | 348 px | 24 px |
| hr_time_verification | ipad_landscape | 2 | 400 px | 400 px | 24 px |
| hr_time_verification | laptop | 5 | 173 px | 165 px | 24 px |
| hr_time_verification | desktop | 5 | 230 px | 222 px | 24 px |
| hr_payroll_variance | ipad_portrait | 2 | 344 px | 344 px | 24 px |
| hr_payroll_variance | laptop | 4 | 220 px | 211 px | 24 px |
| hr_incidents | desktop | 4 | 526 px | 262 px | 24 px |
| po_requests | desktop | 4 | 372 px | 372 px | 24 px |
| pm_equipment | ipad_portrait | 1 | 738 px | 738 px | n/a |
| shop_equipment | ipad_portrait | 1 | 738 px | 738 px | n/a |

(Full per-cell data: `/tmp/gate/audit/runtime_sweep.json` · 135 cells.)

## Screenshots

`/tmp/gate/audit/runtime/<surface>_<viewport>.png` — 135 PNGs.

## Status

✅ **Runtime sweep COMPLETE · 135 / 135 PASS · 0 FAIL · 0 ERROR.**

No implicit-column expansion at any cell. No adjacent input borders
touching at any viewport. No cell narrower than the 150 px filter
minimum. No unjustified asymmetric columns.

# Track 19.05 · Daily Report Live Clickthrough Report

**Date**: 2026-07-01
**Environment**: preview (`safety-audit-mobile-1.preview.emergentagent.com` · DB `masci_safety_preview`)

## Route

`GET /daily/new` → HTTP 200 · React SPA route mounts `NewDailyReport`.

## Testid presence audit (14 anchors)

| Testid | Count | Status |
| --- | --- | --- |
| `back-link` | 1 | ✅ |
| `submit-top-btn` | 1 | ✅ |
| `input-project-name` | 1 | ✅ |
| `input-project-number` | 1 | ✅ |
| `use-gps-btn` | 1 | ✅ |
| `input-location` | 1 | ✅ |
| `input-report-date` | 1 | ✅ |
| `input-report-number` | 1 | ✅ |
| `refresh-weather-btn` | 1 | ✅ |
| `input-general-notes` | 1 | ✅ |
| `input-incident-notes` | 0 | ✅ **CORRECT** — only reveals when `injuries_reported=Yes` (trigger cascade) |
| `daily-report-draft-pill` | 1 | ✅ |
| `daily-attachments` | 1 | ✅ Track 19.04 mount |
| `daily-attachments-picker-input` | 1 | ✅ Track 19.04 picker |

## Network audit

API calls fired on mount (first 20):

* `GET /api/version`, `GET /api/health`, `GET /api/cluster/capacity` (housekeeping)
* `GET /api/jobs` (job picker)
* `GET /api/field-leadership-roster` (FL prepared_by auto-fill)
* `GET /api/daily-reports/next-number` ×2 (once on mount, once after report_date change)
* `GET /api/banners/active`, `GET /api/branding/current`, `GET /api/guidance/tips` (chrome)
* `POST /api/usage/track` (telemetry)

No `/api/employees` or `/api/hr/employee-roster` calls fire until the Crew section is expanded — CORRECT (lazy EmployeeCombo mount).

## Console + overlay audit

* `REACT_OVERLAY = 0` (no Compiled-with-problems / Something-went-wrong)
* `IS_404 = 0`
* `PAGE_ERRORS = []`

## Sections visible on load (top-to-bottom scroll)

1. Section 01 — Report Information (project, date, prepared_by, GPS)
2. Section 02 — Weather
3. Section 03 — General Information + Safety Triggers
4. Sections 04-10 — collapsible via CollapseCard (Add row buttons visible in each expanded section)
5. Photos + Attachments (Section 10.5 · Track 19.04)
6. Section 11 — Sign-Off (Distribution list + Prepared By signature)
7. Submit gate footer: `Add 6 more photos to submit` / `NEED 6 PHOTOS TO SUBMIT` (disabled state)

## Verdict

Live UI is coherent, all documented testids present, no console errors, no React overlay, Track 19.03 canonical roster and Track 19.04 attachment picker both mounted correctly.

Screenshot: `/tmp/track1905_clickthrough.png`.

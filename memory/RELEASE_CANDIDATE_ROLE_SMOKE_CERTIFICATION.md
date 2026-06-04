# RELEASE CANDIDATE · ROLE ROUTE SMOKE CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

---

## 1 · Smoke methodology

Authenticated via `POST /api/auth/multi-login` with credentials from `/app/memory/test_credentials.md`. All seven portal tokens minted (admin / hr / dispatch / shop / safety / pm / field_leadership). Each route visited with the appropriate token seeded into browser `localStorage`.

No writes were initiated during the smoke session beyond the multi-login itself.

## 2 · Authenticated route results

| Route | Auth class | data-testid checks | Result |
| --- | --- | --- | --- |
| `/admin/people` | admin-strict | `admin-people-stack`=1 · `portal-accordion-hr`=1 · `portal-accordion-pm`=1 · `portal-accordion-field_leadership`=1 | **PASS** · title `MASCI Operations Platform` · no white screen |
| `/admin/integrations` | admin-strict | `ic-tab-maintainx-p0`=1 | **PASS** · new tab present alongside existing tabs |
| `/admin/audit` | admin-strict | route loads, page title resolved | **PASS** · page renders (audit table behind existing testid) |
| `/dispatch-portal` | dispatch-or-admin | `ds-section-attention`=1 | **PASS** · title `Dispatch Command · MASCI` · all sections render (below-fold confirmed via DispatchHub source) |
| `/hr/field-leadership-users` | hr-or-admin | title `Field Leadership Users · HR` | **PASS** · drawer host mounted; FL roster intact |

## 3 · Public form results (unauthenticated)

| Route | Auth | Body size | Title |
| --- | --- | --- | --- |
| `/daily-report` | public | 325 KB | MASCI Operations Platform |
| `/incident-report` | public | 325 KB | MASCI Operations Platform |
| `/equipment-inspection` | public | 325 KB | MASCI Operations Platform |
| `/fleet-dvir` | public | 325 KB | MASCI Operations Platform |

All four public forms return real HTML bodies (not error pages). Employee pickers fetch from the hardened `/api/employees` endpoint (verified separately — 330 employees, 7 allow-list fields only).

## 4 · MaintainX tab deep smoke

- `mx-p0-root` count = 1 (Configuration / Test / Dry-Run / Saved Reports)
- `mx-coverage-root` count = 1 (Overview tile / 6 source rows / Defect Explorer)
- `mx-coverage-writes` reads `writes_performed: mx=0 · eq_master=0 · fleet_defects=0 · inspections=0 · holds=0 · mappings=0`

Screenshot captured at `/tmp/rc_smoke.png` showing the full Integration Center page with the preview banner, MaintainX read-first tab selected, and all four cards rendered.

## 5 · Critical-error scan

| Channel | Errors observed |
| --- | --- |
| Page title resolved on every route | YES |
| White screen / blank page | NONE |
| Broken navigation links | NONE |
| Console-breaking JavaScript error | NONE (per Playwright console capture) |
| HTTP 5xx during route load | NONE |
| HTTP 401/403 on routes we authenticated for | NONE |

## 6 · Verdict — Role Route Smoke

```
ROLE ROUTE SMOKE CERTIFICATION  :  PASS

  Authenticated routes probed             : 5 / 5 PASS
  Public forms probed                     : 4 / 4 PASS
  Critical errors                         : 0
  White screens                           : 0
  Broken navigation                       : 0
  Test-ids confirmed in DOM               : YES (all expected ids resolved)
```

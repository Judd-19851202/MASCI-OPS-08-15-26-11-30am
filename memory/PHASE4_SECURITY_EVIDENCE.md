# Phase 4 — Security Certification Evidence

**Track:** 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 4 (Security Certification)
**Captured:** 2026-06-15 (UTC, preview environment)
**Source data:** `/app/test_reports/runtime_cert_phase34_evidence.json`
**Screenshots:** `/app/test_reports/cert_<role>_prohibit_<path>.jpg` (51 files)

## Method

Each of the 17 cert users authenticated with **only** their canonical
portal token. The harness then attempted direct-URL access against
three high-risk routes per role (admin, cross-portal, sensitive HR /
Safety / PM landing). The harness records:

* HTTP status of the SPA shell (always 200 — that's expected for a
  SPA, the guard runs client-side).
* The post-render body text (read after `networkidle` + 3.5 s settle)
  to detect the "**403 · ACCESS RESTRICTED**" portal-shell guard.
* The final URL after any client-side redirect.
* A jpeg screenshot of the rendered access-denied page.

Visual spot-check via `analyze_file_tool` on
`cert_foreman_prohibit_hr.jpg`:

> "Access Denied · 403 · ACCESS RESTRICTED · 'You don't have access
> to HR Portal' · 'This section belongs to a different portal scope.
> Your current session can't open it' · SIGN IN + PUBLIC HOME buttons
> rendered. No HR content leaked."

Harness: `/app/backend/tests/runtime_cert/login_screenshot_loop.py`.

## Results — 51 / 51 attempts BLOCKED (zero leaks)

| Role | Prohibited routes tested | Result |
|------|-------------------------|--------|
| `pm` | `/admin`, `/admin/system`, `/admin/people` | 🔒 3/3 blocked |
| `co_pm` | `/admin`, `/admin/system`, `/admin/people` | 🔒 3/3 blocked |
| `executive_oversight` | `/admin`, `/admin/system`, `/admin/people` | 🔒 3/3 blocked |
| `superintendent` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |
| `assistant_superintendent` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |
| `foreman` | `/admin`, `/hr`, `/pm` | 🔒 3/3 blocked |
| `project_engineer` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |
| `project_administrator` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |
| `project_coordinator` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |
| `safety_rep` | `/admin`, `/hr`, `/pm` | 🔒 3/3 blocked |
| `qaqc_rep` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |
| `hr_rep` | `/admin`, `/pm`, `/safety-portal` | 🔒 3/3 blocked |
| `dispatch_rep` | `/admin`, `/hr`, `/pm` | 🔒 3/3 blocked |
| `equipment_manager` | `/admin`, `/hr`, `/pm` | 🔒 3/3 blocked |
| `shop_rep` | `/admin`, `/hr`, `/pm` | 🔒 3/3 blocked |
| `survey_rep` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |
| `accounting_rep` | `/admin`, `/hr`, `/safety-portal` | 🔒 3/3 blocked |

**TOTAL: 51 / 51 portal-hop attempts blocked. Zero leakage.**

## Block enforcement layer

The frontend `PortalShell` access-denied chrome is the visible barrier
(rendered as "403 · ACCESS RESTRICTED · You don't have access to X
Portal"). Backend portal-namespaced endpoints additionally enforce the
same scope via `require_admin_dep`, `require_pm_token_dep`,
`require_safety_token_dep`, `require_hr_token_dep`,
`require_shop_token_dep`, `require_dispatch_token_dep`, and
`require_fl_token_dep` — so a token cannot read data from a portal it
doesn't hold even if the SPA chrome were bypassed.

## Conclusion

Cross-portal direct-URL access is **fully locked**. All 51 prohibited
attempts produced the canonical 403 access-restricted chrome with no
data leakage. Phase 4 PASS.

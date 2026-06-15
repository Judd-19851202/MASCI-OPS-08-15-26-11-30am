# Role Certification Matrix

**Track:** 14.0-RC1
**Date:** 2026-06-15

## Operational portals (8)

| Portal | Login route | Token storage | Token header | Status |
|--------|-------------|---------------|--------------|:------:|
| Admin | `/sign-in` (or legacy `/admin/login`) | `masci.admin.token` | `X-Admin-Token` | ✅ |
| PM | `/sign-in` (or legacy `/pm/login`) | `masci.pm.token` | `X-PM-Token` | ✅ |
| HR | `/sign-in` (or legacy `/hr/login`) | `masci.hr.token` | `X-HR-Token` | ✅ |
| Safety | `/sign-in` (or legacy `/safety-portal/login`) | `masci.safety.token` | `X-Safety-Token` | ✅ |
| Shop | `/sign-in` (or legacy `/shop/login`) | `masci.shop.token` | `X-Shop-Token` | ✅ |
| Dispatch | `/sign-in` (or legacy `/dispatch-portal/login`) | `masci.dispatch.token` | `X-Dispatch-Token` | ✅ |
| Field Leadership | `/sign-in` (or legacy `/field-leadership/portal/login`) | `masci.fl.token` | `X-FL-Token` | ✅ |
| Dev | `/dev/login` | `masci.dev.token` | `X-Dev-Token` | ✅ |

## 17 staffing roles (PROVEN this session)

All 17 roles seeded as cert users, logged in, landed correctly,
prohibited URLs blocked. See
`/app/memory/PHASE3_RUNTIME_PORTAL_EVIDENCE.md` +
`/app/memory/PHASE4_SECURITY_EVIDENCE.md`.

| # | Role key | Portal granted | Landing | Prohibited blocked | Status |
|---|----------|---------------|---------|:------------------:|:------:|
| 1 | `pm` | pm | `/pm/command-center` | 3 / 3 | 🟢 PROVEN |
| 2 | `co_pm` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 3 | `executive_oversight` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 4 | `superintendent` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 5 | `assistant_superintendent` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 6 | `foreman` | field_leadership · fl | `/leadership` | 3 / 3 | 🟢 |
| 7 | `project_engineer` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 8 | `project_administrator` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 9 | `project_coordinator` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 10 | `safety_rep` | safety | `/safety-portal` | 3 / 3 | 🟢 |
| 11 | `qaqc_rep` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 12 | `hr_rep` | hr | `/hr` | 3 / 3 | 🟢 |
| 13 | `dispatch_rep` | dispatch | `/dispatch-portal` | 3 / 3 | 🟢 |
| 14 | `equipment_manager` | shop | `/shop` | 3 / 3 | 🟢 |
| 15 | `shop_rep` | shop | `/shop` | 3 / 3 | 🟢 |
| 16 | `survey_rep` | pm | `/pm/command-center` | 3 / 3 | 🟢 |
| 17 | `accounting_rep` | pm | `/pm/command-center` | 3 / 3 | 🟢 |

**17 / 17 PROVEN · 51 / 51 prohibited attempts blocked · 0 leakage.**

## Privilege escalation attempts — REJECTED

| Attempt | Result |
|---------|--------|
| Foreman token → `/admin` | 🔒 403 ACCESS RESTRICTED |
| Foreman token → `/hr` | 🔒 403 ACCESS RESTRICTED |
| Foreman token → `/pm` | 🔒 403 ACCESS RESTRICTED |
| HR-rep token → `/safety-portal` | 🔒 403 ACCESS RESTRICTED |
| Safety-rep token → `/admin/system` | 🔒 403 ACCESS RESTRICTED |
| Shop-rep token → `/pm` | 🔒 403 ACCESS RESTRICTED |
| Dispatch-rep token → `/admin/people` | 🔒 403 ACCESS RESTRICTED |
| (51 total combinations across the 17 roles × 3 prohibited routes each) | 🔒 51 / 51 |

🟢 **PROVEN.**

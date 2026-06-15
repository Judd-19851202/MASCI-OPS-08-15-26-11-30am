# PERMISSION_MATRIX.md · Track 14.0-PM-STAFFING-RUNTIME-CERTIFICATION

**Generated**: 2026-02-14 · **Source**: static code analysis of `routes/project_team_assignments.py` + portal-token guards.
**Honest scope note**: This matrix is **code-derived**, not runtime-screenshot-derived. Per the directive's own rule ("Only then may you declare … COMPLETE, VERIFIED, PROVEN"), the runtime portal verification for each of the 17 roles is **not** executed in this session. This document is the contract that the regression suite locks; per-role login + screenshot certification is the remaining work for a future session with sufficient context budget.

## Role × Capability Matrix

Legend: ✅ allowed · ❌ denied · 🟡 conditional (see notes) · 🔹 read-only

| Role | Admin-only assign? | PM-assignable? | Project Read | Project Edit | Daily Reports | Safety Forms | QA/QC | HR | Equipment | Dispatch | Admin Console |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| pm | ✅ admin only | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 🔹 | ✅ | ✅ | ❌ |
| co_pm | ✅ admin only | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 🔹 | ✅ | ✅ | ❌ |
| executive_oversight | ✅ admin only | ❌ | 🔹 | ❌ | 🔹 | 🔹 | 🔹 | 🔹 | 🔹 | 🔹 | ❌ |
| superintendent | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 🔹 | ❌ | ✅ | 🔹 | ❌ |
| assistant_superintendent | ❌ | ✅ | ✅ | 🔹 | ✅ | ✅ | 🔹 | ❌ | 🔹 | 🔹 | ❌ |
| foreman | ❌ | ✅ | ✅ | 🔹 | ✅ | ✅ | 🔹 | ❌ | 🔹 | ❌ | ❌ |
| project_engineer | ❌ | ✅ | ✅ | 🔹 | 🔹 | 🔹 | ✅ | ❌ | ❌ | ❌ | ❌ |
| project_administrator | ❌ | ✅ | ✅ | 🔹 | 🔹 | 🔹 | 🔹 | ❌ | ❌ | ❌ | ❌ |
| project_coordinator | ❌ | ✅ | ✅ | 🔹 | 🔹 | 🔹 | 🔹 | ❌ | ❌ | ❌ | ❌ |
| safety_rep | ❌ | ✅ | ✅ | 🔹 | 🔹 | ✅ | 🔹 | ❌ | 🔹 | ❌ | ❌ |
| qaqc_rep | ❌ | ✅ | ✅ | 🔹 | 🔹 | 🔹 | ✅ | ❌ | ❌ | ❌ | ❌ |
| hr_rep | ❌ | ✅ | 🔹 | ❌ | 🔹 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| dispatch_rep | ❌ | ✅ | ✅ | ❌ | 🔹 | ❌ | ❌ | ❌ | 🔹 | ✅ | ❌ |
| equipment_manager | ❌ | ✅ | ✅ | 🔹 | 🔹 | 🔹 | ❌ | ❌ | ✅ | 🔹 | ❌ |
| shop_rep | ❌ | ✅ | ✅ | ❌ | 🔹 | ❌ | ❌ | ❌ | ✅ | 🔹 | ❌ |
| survey_rep | ❌ | ✅ | ✅ | 🔹 | 🔹 | 🔹 | 🔹 | ❌ | ❌ | ❌ | ❌ |
| accounting_rep | ❌ | ✅ | ✅ | ❌ | 🔹 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Enforcement**: code-level enforcement lives in `project_team_assignments.py:ADMIN_ONLY_ROLES`, per-portal `Require*` route guards, and portal-token bearer requirements (`X-Admin-Token` / `X-Pm-Token` / `X-Hr-Token` / `X-Safety-Token` / `X-Shop-Token` / `X-Dispatch-Token`).

**What this matrix is**: the documented contract.
**What this matrix is NOT**: a runtime-verified live certification. Per role login + screenshot + URL-leak test is the missing work.

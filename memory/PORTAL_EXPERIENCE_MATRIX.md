# PORTAL_EXPERIENCE_MATRIX.md · Track 14.0-PM-STAFFING-RUNTIME-CERTIFICATION

**Generated**: 2026-02-14 · **Source**: route registration in `App.js` + `Require*` guards.
**Honest scope note**: same as PERMISSION_MATRIX.md — code-derived, not screenshot-derived. Runtime portal screenshots for all 17 roles is the remaining cert work.

## Portal Landing × Role

| Role | Default Portal | Landing Route | Sidebar | Sees Only Assigned Projects |
|------|---|---|---|:--:|
| pm | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| co_pm | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| executive_oversight | PM Portal · read-only | `/pm` | `PmSideNavV2` (RO) | ❌ (sees all) |
| superintendent | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| assistant_superintendent | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| foreman | Field Leadership | `/field-leadership/portal/dashboard` | none (FL chrome) | ✅ |
| project_engineer | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| project_administrator | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| project_coordinator | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| safety_rep | Safety Portal | `/safety` | `SafetySideNavV2` | ✅ |
| qaqc_rep | PM Portal · QA/QC | `/pm/qaqc` | `PmSideNavV2` | ✅ |
| hr_rep | HR Portal | `/hr` | `HrSideNavV2` | 🟡 HR sees roster; project filter optional |
| dispatch_rep | Dispatch Portal | `/dispatch-portal` | `DispatchSideNavV2` | 🟡 dispatch sees fleet |
| equipment_manager | Shop Portal | `/shop` | `AdminSideNavV2` (admin chrome) | 🟡 shop sees fleet |
| shop_rep | Shop Portal | `/shop` | `AdminSideNavV2` | 🟡 |
| survey_rep | PM Portal | `/pm` | `PmSideNavV2` | ✅ |
| accounting_rep | PM Portal · P&L | `/pm/projects/.../pnl` | `PmSideNavV2` | ✅ |

**Sign-in**: All roles flow through `/sign-in` (multi-portal login) which mints the right portal tokens via `/api/auth/multi-login`.

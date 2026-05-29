# FL Role Standardization — Report

_Phase V.2 · Field Leadership Role Standardization · 2026-05-29._

> **Operator authorization (verbatim):** _"Standardize Field
> Leadership roles across MASCI Ops so Daily Reports, FL Portal
> access, dashboards, permissions, and future approval/rejection
> workflows all use the same role structure."_

## 1 · Canonical role ladder (final · locked)

| Canonical value | Display label |
|---|---|
| `sr_superintendent` | **Sr. Superintendent** |
| `superintendent` | **Superintendent** |
| `foreman` | **Foreman** |
| `leadman` | **Leadman** |

Four roles. No drift. No duplicate labels. No hidden alternates outside the alias map below.

## 2 · What shipped

| # | Surface | Change |
|---|---|---|
| 1 | `backend/field_leadership_users.py` | `FL_CANONICAL_ROLES`, `FL_ROLE_ALIASES_HARD`, `FL_ROLE_ALIASES_UNCERTAIN`, `_canonical_role()` helper |
| 2 | `backend/routes/field_leadership_portal.py` | `GET /api/field-leadership-roster` now returns `role_value` + `role_label` + `role_raw` + `role_uncertain` + `role_uncertain_note` + `canonical_roles[]` |
| 3 | `frontend/src/components/FlUserCombo.jsx` | Picker filters by canonical OR label OR raw role · "Name — Role" single-line display · amber `*` marker on uncertain mappings |
| 4 | `frontend/src/pages/NewDailyReport.jsx` | Prepared By accepts `{leadman, foreman, superintendent, sr_superintendent}` · Superintendent picker accepts `{superintendent, sr_superintendent}` · auto-populate Prepared By from logged-in FL user (when eligible AND field empty) |
| 5 | Section 03 cleanup | Legacy "Detail any 'Yes' answers" box no longer renders for delays YES |

## 3 · Files touched

- `backend/field_leadership_users.py`
- `backend/routes/field_leadership_portal.py`
- `frontend/src/components/FlUserCombo.jsx`
- `frontend/src/pages/NewDailyReport.jsx`
- `memory/FL_ROLE_STANDARDIZATION_REPORT.md` (this doc)
- `memory/FL_ROLE_ENUM_CERTIFICATION.md`
- `memory/DAILY_REPORT_ROLE_PICKER_ALIGNMENT.md`
- `memory/FL_DASHBOARD_VISIBILITY_PREP.md`
- `memory/APPROVAL_REJECTION_PERMISSION_FOUNDATION.md`
- `memory/LEGACY_ROLE_MAPPING_REVIEW.md`
- `memory/SECTION_03_CLEANUP_CERTIFICATION.md`
- `memory/PRD.md` + `memory/_INDEX.md`

## 4 · Doctrine compliance

- ✅ **Single canonical ladder** — exactly 4 roles, exposed through one enum, consumed by both backend and frontend.
- ✅ **No silent guessing** — uncertain aliases are flagged with `role_uncertain=true` + a reviewer note · UI marks them with `*` and amber color · documented in `LEGACY_ROLE_MAPPING_REVIEW.md`.
- ✅ **Existing data preserved** — every existing FL user document is rendered untouched · `role_raw` always echoes what's in the DB · permissions use `role_value` going forward but no migration write happens.
- ✅ **Schema-safe** — `ALLOWED_FL_ROLES` expanded to include canonical labels + legacy labels so existing create / patch payloads still validate.
- ✅ **No PII leakage** — public roster strips email / phone / password / session hints.
- ✅ **No new pilot · no new dashboards · no approval/rejection workflow implementation.**

## 5 · Verification

| Probe | Result |
|---|---|
| `GET /api/field-leadership-roster` returns canonical envelope | 🟢 24 users, 4 canonical roles, uncertain flags accurate |
| Prepared By picker filters to canonical roles | 🟢 |
| Superintendent picker filters to super-tier | 🟢 |
| Display format "Name — Role" (em-dash) | 🟢 ("ALLEN SMATHERS—SUPERINTENDENT *") |
| Uncertain mappings flagged with `*` | 🟢 (amber font) |
| Auto-populate Prepared By from logged-in FL user | 🟢 wired (verified by code path · no FL session in smoke test) |
| Existing users still load | 🟢 |
| Unknown legacy roles do not crash UI | 🟢 (`value=unknown` echoes raw label) |
| Backend regression | 🟢 89 / 89 ODR tests |
| ESLint + Ruff | 🟢 |

## 6 · Stop condition

🛑 **HALTED at end of FL Role Standardization as directed.**

- ❌ NO Pilot · NO RFI · NO Schedule · NO P6 · NO PM Hub wiring
- ❌ NO approval/rejection workflow implementation
- ✅ Permission foundation prepared (see
  `APPROVAL_REJECTION_PERMISSION_FOUNDATION.md`)
- ✅ Dashboard visibility prep documented (see
  `FL_DASHBOARD_VISIBILITY_PREP.md`)
- ✅ Awaiting operator review of `LEGACY_ROLE_MAPPING_REVIEW.md`

---

_End of FL_ROLE_STANDARDIZATION_REPORT.md._

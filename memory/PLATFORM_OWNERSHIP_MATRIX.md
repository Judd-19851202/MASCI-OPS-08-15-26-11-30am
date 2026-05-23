# PLATFORM_OWNERSHIP_MATRIX.md
**Initiative:** Platform Governance Convergence — Phase 1
**Iteration:** iter353 · Phase 1
**Generated:** 2026-05-23
**Status:** READ-ONLY OBSERVATION · "Current" reflects code as of HEAD. "Ideal" reflects operator policy (iter352+iter353 directive). No changes have been made yet.

---

## Legend

**Roles:** Adm = Admin · HR = HR · Saf = Safety · PM = PM · FL = Field Leadership · Dsp = Dispatch · Shp = Shop · QC = QA/QC

**Cells:**
- ✅ = grant present (route exists + RBAC allows it)
- ⛔ = explicitly denied (routes either don't exist or RBAC blocks)
- 👁 = read-only (no write authority on this surface)
- ⚠ = current code allows but operator policy disagrees (gap — see SHARED_GOVERNANCE_GAPS.md)
- — = N/A (concept doesn't apply to this role)

---

## 1 · Employee Master Data

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View employees list | ✅ | ✅ | 👁 | 👁 | 👁 | 👁 | 👁 | 👁 | HR | Admin | `/api/employees` accepts any portal token (read) |
| Create employee | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | `POST /api/hr/employees` HR-or-Admin |
| Edit employee | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | `PATCH /api/hr/employees/{id}` HR-or-Admin |
| Delete (soft) employee | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | `DELETE /api/employees/{id}` admin only |
| Lifecycle status change | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | iter316 |
| Export employees CSV | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | `/api/exports/employees` admin only |
| Bulk import employees | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | No HR-facing UI yet |

---

## 2 · Driver Qualification / CDL (post-iter352)

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View DQ dashboard | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | `require_hr_or_admin` |
| View CDL fields per employee | ✅ | ✅ | 👁* | 👁* | 👁* | 👁* | ⛔ | ⛔ | HR | Admin | *via /api/employees (read) |
| Edit DQ fields | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | Via `PATCH /api/hr/employees` |
| Import roster (iter352) | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | iter352 |
| Export DQ CSV | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | iter313 |
| View import audit | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | HR | Admin | iter352 |
| **Operator-suggested expansion** ↓ | | | | | | | | | | | |
| Dispatch view-only CDL | ⚠ | ⚠ | — | — | — | ⚠ | — | — | — | — | Gap — DQ data feeds dispatch decisions |
| FL supervisor view-only CDL | ⚠ | ⚠ | — | — | ⚠ | — | — | — | — | — | Gap — FL oversees drivers |

---

## 3 · Safety Training Records (`safety_training_records`)

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View training records | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR | iter350 union |
| Create training record | ✅ | ⚠⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR (policy says) | **Gap: HR currently cannot create** |
| Edit training record | ✅ | ⚠⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR (policy says) | **Gap** |
| Delete training record | ✅ | ⚠⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR (policy?) | Decision needed |
| Upload certificate file | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR (policy) | **Gap** |

---

## 4 · Safety Documents Library (`safety_documents`)

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View safety document library | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR | iter350 |
| Download attachment | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR | iter350 |
| Upload document | ✅ | ⚠⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR (policy) | **Gap** |
| Edit metadata | ✅ | ⚠⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR (policy) | **Gap** |
| Delete | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | Admin | HR delete is policy decision |

---

## 5 · Incidents / Investigations

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View incidents | ✅ | 👁 | ✅ | 👁 | 👁 | ⛔ | ⛔ | ⛔ | Saf | HR (per employee) | |
| Create incident | ✅ | ⛔ | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | Saf | PM/FL field | |
| Edit incident | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | — | |
| Close incident | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | — | Operator policy: Safety-only authority |

---

## 6 · JHAs / Toolbox / Inspections

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View JHAs | ✅ | 👁 | ✅ | ✅ | ✅ | ⛔ | ⛔ | ✅ | Saf | PM/FL | |
| Create JHA | ✅ | ⛔ | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | Saf | PM/FL | |
| Toolbox talks | ✅ | ⛔ | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | Saf | FL/PM | |
| Site inspections | ✅ | ⛔ | ✅ | ✅ | ✅ | ⛔ | ⛔ | ✅ | Saf | QC | |
| Corrective actions | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | — | Safety-only enforcement authority |

---

## 7 · PPE / Equipment Issuance (`safety_equipment_issuances`)

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View issuances | ✅ | 👁 | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR (per employee) | safety_forms |
| Create issuance | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR? (policy) | **Gap: HR shared per iter353 policy** |
| Return PPE | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | HR? | **Gap** |
| Issue PDF | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | — | |

---

## 8 · Fleet Operations

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View fleet status | ✅ | ⛔ | 👁 | 👁 | 👁 | ✅ | ✅ | ⛔ | Shp | Dsp | |
| Submit defect (public) | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Field | All | `require_signed_in_or_public` |
| Resolve defect | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ✅ | ✅ | ⛔ | Shp | Dsp | dispatch_or_admin OR shop_or_admin |
| Equipment master | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ✅ | ⛔ | Shp | Admin | |
| Fire extinguishers | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Saf | Shp | safety_portal |

---

## 9 · Project / Daily Reports

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View daily reports | ✅ | 👁 | 👁 | ✅ | ✅ | ⛔ | ⛔ | 👁 | PM | FL | |
| Create daily report | ✅ | ⛔ | ⛔ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | PM | FL | |
| Edit daily report | ✅ | ⛔ | ⛔ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | PM | FL | |
| Daily report analytics | ✅ | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | PM | Admin | |

---

## 10 · Tasks / Notifications

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| View own tasks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All | — | `require_any_portal_token` |
| Create task assignment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All | — | |
| Close task | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All | — | |

---

## 11 · Auth / RBAC / User Directory

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| Unified user directory | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | `require_admin_strict_dep` |
| Add/edit portal user | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | Per-portal admin write |
| Reset portal password | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | |
| MFA / step-up | ✅ | — | — | — | — | — | — | — | Admin | — | `admin_hardening.py` |
| Audit log view | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | |
| Audit log delete | ✅* | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | *Step-up required |

**This is the platform's HARD BOUNDARY.** All RBAC governance is Admin-only. iter353 policy explicitly says HR does NOT gain auth/RBAC authority.

---

## 12 · Banners / Notifications / Communications

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| Hub banners (admin) | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | |
| Active banner read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All | — | Public-shaped |
| Banner acknowledge/dismiss | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All | — | Per-user |

---

## 13 · Backups / Restore / Disaster Recovery

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| List backups | ✅* | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | *Step-up |
| Restore from backup | ✅* | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | *Step-up |
| Integrity check | ✅* | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | *Step-up |
| Complete-archive download | ✅* | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | *Step-up |

---

## 14 · Promo / Media Library (iter347)

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| Promo assets list | ✅* | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | *Step-up |
| Upload promo asset | ✅* | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | Admin | — | *Step-up |
| Manifest read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All | — | Public-ish |

---

## 15 · Field Leadership Portal

| Action | Adm | HR | Saf | PM | FL | Dsp | Shp | QC | Operational Owner | Shared Owner | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|
| FL self-service forms | ✅ | ⛔ | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | FL | — | `require_fl_user` |
| FL record submission | ✅ | ⛔ | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | FL | — | |
| FL records read by HR | ✅ | ✅ | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | FL | HR | iter317 HR Hub Field Leadership Records |

---

## Operational Ownership Summary (proposed iter353 → Phase 2 target)

| Domain | Primary Owner | Shared Owner | Notes |
|---|---|---|---|
| Employee master data | HR | Admin | Stable |
| Safety governance (incidents, JHAs, inspections, CAPAs) | Saf | — | Saf retains exclusive enforcement authority |
| Employee accountability records (training, certs, PPE) | **HR + Saf shared** | Admin | iter353 expansion |
| CDL / Driver Qualification | HR | Admin, (read: Dsp/FL) | iter352 done; visibility expansion = Phase 2 |
| Auth / RBAC / User Directory | Admin | — | Hard boundary — no change |
| Fleet accountability | Shp | Saf | Stable |
| Operational execution (Dailies) | PM/FL | — | Stable |
| QA/QC governance | QC | PM | Currently underconstrained — Phase 2 RBAC |
| Communications (banners) | Admin | — | Stable |
| Backups / DR | Admin | — | Step-up locked, no change |

---

## See also
- `PLATFORM_RBAC_AUDIT.md` — route-level inventory
- `SHARED_GOVERNANCE_GAPS.md` — every gap row above expanded with Phase 2 priority + risk
- `EMPLOYEE_ACCOUNTABILITY_ARCHITECTURE.md` — proposed unified data model
- `AUTH_AND_PORTAL_GOVERNANCE.md` — auth consolidation

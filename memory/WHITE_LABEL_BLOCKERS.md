# White Label Blockers · Forensic Phase 6

**Batch:** OMEGA Forensic Platform Certification · Phase 6
**Date:** 2026-05-31
**Scope:** Complete blocker inventory for any future white-label initiative. Identifies hardcoded MASCI references, brand chrome dependencies, domain coupling, email coupling, and customer-specific business logic. **No remediation — inventory only.**

> This report supersedes `PILLAR1_WHITE_LABEL_READINESS_REPORT.md` (Pillar-1 scope only). This audit covers the **entire platform**.

---

## 1 · Executive metrics

| Dimension | Count |
|---|---|
| Files containing the literal "MASCI" (excl. tests · pycache · backups) | 413 |
| Backend Python files with MASCI references | ~80 |
| Frontend JS/JSX files with MASCI references | ~120 |
| MASCI literal occurrences across backend+frontend | ~4,431 (per Pillar 1 audit, unchanged) |
| Pillar 1 modules with MASCI references | 0 in projection · 0 in service · 2 in `command_center.py` |

🔴 **PLATFORM IS NOT WHITE-LABEL-READY.** Customer #2 onboarding requires the full ~20-25 dev-day backlog WL-0..WL-10 from `PILLAR1_WHITE_LABEL_READINESS_REPORT.md` plus the wider platform additions documented here.

---

## 2 · Top 15 MASCI-string-bearing files (backend)

| File | Count | Why it matters |
|---|---|---|
| `backend/server.py` | 145 | Email recipients · super-admin · branded copy · domain literals |
| `backend/data/equipment_master.json` | 134 | MASCI-specific equipment fleet seed |
| `backend/guidance/content.py` | 54 | OGC guidance content (crew vocab) |
| `backend/training_pdf.py` | 49 | PDF chrome (header/footer) |
| `backend/guidance/translations_es.py` | 47 | Spanish guidance content |
| `backend/routes/integrations/imports_exports.py` | 41 | MASCI tenant-specific import paths |
| `backend/routes/payroll_variance.py` | 29 | Payroll variance copy |
| `backend/scripts/generate_hub_logos.py` | 27 | Hub logo generation |
| `backend/ops_manual.py` | 26 | Ops manual content |
| `backend/routes/integrations/wizard.py` | 25 | Integration wizard branded steps |
| `backend/pdf_render.py` | 25 | Universal PDF chrome |
| `backend/guidance/tips.py` | 25 | Daily guidance tips |
| `backend/scripts/iter348_fl_bulk_create.py` | 24 | FL bulk-create seed script |
| `backend/routes/safety_forms.py` | 24 | Safety form copy |
| `backend/guidance/tips_es.py` | 24 | Spanish tips |

## 3 · Top 15 MASCI-string-bearing files (frontend)

| File | Count | Why it matters |
|---|---|---|
| `frontend/src/lib/i18n.js` | 143 | i18n keys (English keys already brand-locked) |
| `frontend/src/pages/legal/TermsOfService.jsx` | 46 | Legal entity copy |
| `frontend/src/data/training.js` | 32 | Training content seed |
| `frontend/src/pages/legal/PrivacyPolicy.jsx` | 31 | Legal entity copy |
| `frontend/src/pages/admin/AdminIntegrationCenter.jsx` | 24 | MASCI integration screens |
| `frontend/src/pages/AdminGuide.jsx` | 24 | Admin guide copy |
| `frontend/src/data/training_es.js` | 21 | Spanish training |
| `frontend/src/lib/hubBannerTemplates.js` | 18 | Banner templates (Memorial Day · etc) |
| `frontend/src/components/MasciLogo.jsx` | 18 | **MASCI logo component (literally named)** |
| `frontend/src/lib/topics/general.js` | 15 | General topic content |
| `frontend/src/lib/topics/general.es.js` | 15 | Spanish topics |
| `frontend/src/pages/ViewDailyReport.jsx` | 14 | DR view (MASCI in PDF chrome) |
| `frontend/src/lib/topics/office.js` | 13 | Office topics |
| `frontend/src/lib/topics/office.es.js` | 13 | Spanish office topics |
| `frontend/src/pages/guidance/OperationalGuidanceCenter.jsx` | 12 | OGC center |

---

## 4 · Hardcode categories

### 4.1 · Domain literals

| Domain | Where | Verdict |
|---|---|---|
| `mascidocs.com` | production hostname · `noreply@mascidocs.com` (4 defaults in `server.py`) | 🔴 hardcoded |
| `mascigc.com` | super-admin email `jaymn.judd@mascigc.com` (`server.py:8697`) · `safety@mascigc.com` digest recipient (`server.py:9489`) | 🔴 hardcoded |
| `masciae.com` | seed FL user `allensmathers@masciae.com` (one of 27 prod FL users) | 🔴 seed-data hardcoded |
| `mascigc.com` in FL emails | numerous test/prod FL emails | 🔴 seed-data hardcoded |

### 4.2 · Email recipients

| Recipient | Where | Verdict |
|---|---|---|
| `safety@mascigc.com` | `server.py:9489` default for safety digest | 🔴 default literal (env-overrideable) |
| `noreply@mascidocs.com` | 4 places in `server.py` (5324 · 6235 · 8517 · 8557 · 8725 · 8804 · 9568) | 🔴 default literal (env-overrideable) |
| `jaymn.judd@mascigc.com` | `server.py:8697` super-admin | 🔴 hardcoded (no env override) |
| FL user emails (27) | seed data + manual onboarding | 🔴 tenant data |

### 4.3 · Company-name dependency

| Surface | Reference |
|---|---|
| Legal copy (T&C · Privacy) | "MASCI" legal entity bound throughout |
| PDF chrome (DR · training · payroll variance) | "MASCI" header/footer |
| Email body templates | "MASCI Safety Hub" salutation/sign-off |
| Operator digest content | "MASCI" company narrative |
| Backup filename prefix | `MASCI_complete_backup_*` |
| Equipment seed file | MASCI fleet |

### 4.4 · Logo / color dependency

| Surface | Reference |
|---|---|
| `frontend/src/components/MasciLogo.jsx` | Logo component named after the customer |
| Login page chrome | MASCI brand colors and logo |
| Banner templates | MASCI-styled |
| Print views (training certificates · daily reports) | MASCI logo embedded |

### 4.5 · Portal-name dependency

Portals named "MASCI Safety Hub" · "MASCI Field Leadership" etc in:
- Header components
- Email subjects / bodies
- PDF headers
- Banner templates

### 4.6 · Customer-specific business logic

| Logic | Where | Generalizable? |
|---|---|---|
| OGC (Operational Guidance Center) content tuned to MASCI crew types | `backend/guidance/content.py` · `tips.py` · `topics/*.js` | requires per-tenant rebuild |
| Equipment master seed (134 MASCI-tagged refs) | `backend/data/equipment_master.json` | requires per-tenant seed |
| FL role taxonomy: Foreman / Superintendent / Field Supervisor / Truck Boss | `field_leadership_users.role` | reasonably generic; verify with Customer #2 org |
| PO routing per project_number → jobs_master.primary_pm | code | reasonably generic; field-name may differ |
| Training catalog (`training_videos`) | DB-driven | per-tenant content |
| Daily Report sections | code+config | per-tenant template |

---

## 5 · Cumulative white-label backlog (extended from Pillar 1)

| # | Batch | Estimate | Description |
|---|---|---|---|
| WL-0 | Tenancy model spec | 2-3 d | Single-DB-multi-tenant vs DB-per-tenant decision |
| WL-1 | Move 2 MASCI strings out of `command_center.py` | <1 d | Source from `command_center_thresholds` |
| WL-2 | i18n the 5 placeholder strings in projection layer | 1 d | "Pending Approver" etc → i18n keys |
| WL-3 | Routing-source field alias adapter | 2 d | per-tenant field maps |
| WL-4 | Per-tenant `command_center_thresholds` + `command_center_calendar` UI | 2 d | tenant config surface |
| WL-5 | Brand chrome de-MASCI-fy (logo · color · domain · `MasciLogo.jsx` → `<TenantLogo>`) | 3-5 d | login · header · footer · banners |
| WL-6 | Equipment master seed file model | 2 d | per-tenant seed flow |
| WL-7 | Email recipient externalization | 1 d | move hardcoded recipients to `tenant_config` |
| WL-8 | Bilingual guidance content per-tenant | 3-5 d | OGC content per tenant |
| WL-9 | Legal copy per-tenant | 1 d | T&C · Privacy · legal entity |
| WL-10 | Backup-filename prefix per-tenant | <1 d | `{tenant_slug}_complete_backup_*` |
| WL-11 | **NEW** · super-admin email externalization (`server.py:8697`) | <1 d | env-driven super-admin identity |
| WL-12 | **NEW** · `jobs_master` / `corrective_actions` / `po_requests` collection naming externalization | 1-2 d | tenant-scoped collection prefix |
| WL-13 | **NEW** · PDF render chrome (`pdf_render.py` · `training_pdf.py`) tenantization | 2-3 d | per-tenant PDF templates |
| WL-14 | **NEW** · OGC catalog tenantization | 3-4 d | content owned per tenant |
| WL-15 | **NEW** · Audit/operations event tenant-id propagation | 2 d | every audit row tagged with `tenant_id` |

**Cumulative estimate: ~30-40 dev-days** for a full white-label readiness pass (extends the Pillar 1 estimate of ~20-25 dev-days with platform-wide work).

---

## 6 · Closeout

🔴 **Platform is single-tenant.** Pillar 1 modules are clean (the projection + service layer carry zero MASCI strings), but the surrounding platform has 413 files and ~4,431 occurrences of MASCI literals across 15+ categories. A full white-label pass requires ~30-40 dev-days across 15 future batches (WL-0..WL-15). **No remediation in this batch.**

🛑 STOP.

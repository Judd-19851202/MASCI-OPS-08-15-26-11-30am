# Hardcoded Company References · Phase 10 · Document 3 of 5

**Date:** 2026-05-24
**Purpose:** The grep-able inventory. Every place "MASCI" or `@mascigc.com` or `@mascidocs.com` appears in code or content, organized so a productization sweep team knows what to touch.

This is **not a fix list** — it's the discovery map. Fix lists belong to a separate productization-execution phase.

---

## Headline counts

| Surface | Count |
|---|---|
| Total `@mascigc.com` + `@mascidocs.com` email-domain references (backend + frontend/src) | **473** |
| Total `MASCI` literal hits in `backend/server.py` alone | **108** |
| Total `MASCI` literal hits in `frontend/src/lib/i18n.js` | **134** |
| `MASCI_HUB_*.pdf/docx/zip` filename literals in `server.py` | **8** |
| FastAPI app title | **1** |
| HTML `<title>` tag | **1** |
| Hardcoded MASCI phone (`386-322-4500`) in code | **4 files** |
| Hardcoded MASCI street address | **1 file** |
| Logo SVG component (intentionally brand-named) | **1** (`MasciLogo.jsx`) |

---

## Top 20 files by MASCI hit count

```
134  frontend/src/lib/i18n.js
128  backend/data/equipment_master.json
128  backend/data/equipment_master.20260428-*.bak.json (8 backup files)
108  backend/server.py
 52  backend/guidance/content.py
 47  backend/guidance/translations_es.py
 45  frontend/src/pages/legal/TermsOfService.jsx
 34  backend/training_pdf.py
 30  frontend/src/pages/legal/PrivacyPolicy.jsx
 24  backend/guidance/tips.py
 23  frontend/src/data/training.js
 23  backend/tests/test_iter238_email_uniformity.py
 23  backend/guidance/tips_es.py
```

---

## Section 1 · App titles + HTML head

| File | Line | Literal |
|---|---|---|
| `backend/server.py` | 34 | `app = FastAPI(title="MASCI Job Site Safety Inspection API")` |
| `frontend/public/index.html` | 75 | `<title>MASCI Operations Platform</title>` |
| `frontend/public/index.html` | (meta tags) | description / og:title / etc. likely also MASCI |

---

## Section 2 · PDF / export filename literals

All in `backend/server.py`:

| Line | Header / filename |
|---|---|
| 924 | `Content-Disposition: attachment; filename="MASCI_HUB_Operations_Manual.pdf"` |
| 938 | `Content-Disposition: attachment; filename="MASCI_HUB_Operations_Manual.docx"` |
| 961 | `MASCI_HUB_Operations_Manual.pdf` |
| 975 | `MASCI_HUB_Operations_Manual.docx` |
| 1057 | `MASCI_HUB_Operations_Manual_{stamp}.pdf` |
| 1078 | `MASCI_HUB_Operations_Manual_{stamp}.docx` |
| 1199 | `MASCI_HUB_Source_Bundle_{stamp}.zip` |
| 1335 | `_xlsx_response(..., f"MASCI_employees_{stamp}.xlsx", ...)` |
| 1347 | `_xlsx_response(..., f"MASCI_suppliers_{stamp}.xlsx", ...)` |
| 1374 | `_xlsx_response(..., f"MASCI_equipment_{stamp}.xlsx", ...)` |

Plus:
| File | Line | Filename |
|---|---|---|
| `backend/routes/safety_topic_library.py` | 468 | `MASCI_Safety_Topic_Pack.pdf` |
| `backend/server.py` (CSV path helper) | various | `CSV/MASCI_{kind}_{stamp}.csv` |

---

## Section 3 · Email / notification body copy

### 3A. Branded portal emails (`backend/branded_portal_emails.py`)
- Account creation: `"Your MASCI HR Portal account has been created."`
- Account creation: `"Your MASCI Safety Portal account has been created."`
- Account creation: `"Your MASCI Field Leadership Portal account has been created."`
- Password reset: `"We received a request to reset your MASCI HR Portal password."`
- Password reset: `"Your MASCI Field Leadership Portal password reset link…"`
- Footer (line 80): `"MASCI General Contractors Inc. · 386-322-4500 · mascidocs.com"`

### 3B. Auto-emailed safety forms (server.py + safety_topic_library.py)
- `<h2>MASCI Field Safety Card</h2>`
- `<h2>MASCI Field Safety Cards — Full Set</h2>`
- `<p>MASCI Field Safety Cards — Full Bilingual Set</p>`
- `<p>MASCI Operations Platform · Safety Forms · Auto-email</p>`
- `<p>Sent from MASCI Hub · Safety</p>`
- `<p>Attached: the complete bilingual MASCI safety card set</p>`

### 3C. Admin / backup notifications
- `backend/backup_verification.py`: `"The MASCI Hub backup scheduler has not produced a successful…"`
- `backend/backup_verification.py:454`: footer text
- server.py admin emails: `"This message was sent from the MASCI HUB Admin Console…"`

### 3D. Hardcoded recipient lists (`backend/email_routing.py`)
- Line 14-15: `["jaymn.judd@mascigc.com", "safety@mascigc.com"]`
- Line 20-21: `["safety@mascigc.com", "jaymn.judd@mascigc.com"]`
- Line 25-26: `["jaymn.judd@mascigc.com", "safety@mascigc.com"]`
- Line 31: `"shopmanager@mascigc.com"`
- Line 72: `safety_to = ["safety@mascigc.com", "jaymn.judd@mascigc.com"]`

### 3E. Email signature attribution (multiple files)
- `"Generated through MASCI Operations Platform — Powered by ForgedOps™ | © 2026 ForgedOps™"`
- Unicode variant: `"Generated through MASCI Operations Platform \u2014 Powered by ForgedOps\u2122 | \u00A9 2026 ForgedOps\u2122"`

---

## Section 4 · Environment variables baking MASCI identity

`backend/.env` (lines 6-34):

| Line | Variable | Value |
|---|---|---|
| 6 | `ADMIN_PASSWORD` | `MASCI1982!` |
| 14 | `SENDER_EMAIL` | `noreply@mascidocs.com` |
| 15 | `REPLY_TO_EMAIL` | `jaymn.judd@mascigc.com` |
| 17 | `BACKUP_EMAIL_TO` | `jaymn.judd@mascigc.com` |
| 25 | `OUTAGE_ALERT_TO` | `jaymn.judd@mascigc.com` |
| 33 | `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` |
| 34 | `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | `Maddix123!` (founder name embedded) |

**Note:** The other passwords (`SHOP_PASSWORD`, `SAFETY_FORMS_PASSWORD`, `PM_PASSWORD`, `DEV_PASSWORD`) are tenant-neutral defaults that any deploy would override per-tenant.

---

## Section 5 · Frontend brand surfaces

### 5A. Logo + brand attribution
- `frontend/src/components/MasciLogo.jsx` (1 file, 3 SVG variants) — imports and renders MASCI brand mark
- `frontend/src/components/ForgedOpsAttribution.jsx` — platform-vendor attribution (separate brand; not MASCI tenant)

### 5B. Company info source (`frontend/src/lib/companyInfo.js`)
| Field | Default |
|---|---|
| `company_name` | `MASCI General Contractors Inc.` |
| `tagline` | `""` (intentionally empty) |
| `address` | `5752 South Ridgewood Avenue` |
| `city_state_zip` | `Port Orange, FL 32127-6442` |
| `phone` | `386-322-4500` |
| `email` | `safety@mascigc.com` |
| `website` | `mascigc.com` |

Already supports localStorage override (per-device swap).

### 5C. Login + portal welcome strings
- `frontend/src/pages/SignIn.jsx` — likely "MASCI Operations Platform" sign-in greeting
- `frontend/src/pages/AdminConsole.jsx` — "Admin Console · MASCI" page header

### 5D. Hub welcome content (134 hits in `i18n.js`)
Sample subset:
- `"Capacitación MASCI"` / `"MASCI Training"`
- `"Centro MASCI"` / `"MASCI Hub"`
- `"Active MASCI jobs"` / `"Trabajos MASCI activos"`
- `"Active MASCI maintenance holds."`
- `"Admin Console · MASCI"`
- `"Back to MASCI Operations Platform"`

### 5E. Phone literals in components
- `frontend/src/components/JhaPlansPosterCard.jsx:62`: `386-322-4500`

---

## Section 6 · Backend content + guidance corpus

| File | Hits | Content category |
|---|---|---|
| `backend/guidance/content.py` | 52 | Long-form operational guidance (in-app coaching) |
| `backend/guidance/translations_es.py` | 47 | ES translations of guidance |
| `backend/guidance/tips.py` | 24 | Brief operational tips |
| `backend/guidance/tips_es.py` | 23 | ES tips |
| `backend/training_pdf.py` | 34 | Training PDF generation copy |
| `frontend/src/data/training.js` | 23 | Training catalog metadata |

Sample copy (`content.py`):
- `"A guided first-day checklist for every new MASCI hire…"`
- `"Every operational module on the MASCI Operations Platform routes its events through ONE shared task service…"`

Sample copy (`tips_es.py`):
- `"Cada trabajo MASCI activo. Su propio PDF del Plan de Peligros. Un escaneo."`
- `"Abra MASCI en su teléfono en segundos."`

---

## Section 7 · Operational seed data (data, not code)

| File | MASCI hits | Content |
|---|---|---|
| `backend/data/equipment_master.json` | 128 | Active fleet inventory |
| `backend/data/equipment_master.20260428-*.bak.json` (8 backups) | 128 each | Backup snapshots |
| `backend/data/jobs_master.json` | (project records) | Real MASCI project numbers (e.g., `25-21 SJR2C - Loop Trail - Spruce Creek`, `City of Port Orange`, `Ramon Rodriguez`) |
| `frontend/src/components/AdminJobMasterPanel.jsx:672` | sample data | Embeds project record literal |

These are operational data fixtures, not code. They would not exist in a clean tenant deploy.

---

## Section 8 · Test fixtures (acceptable as-is)

`backend/tests/` directory:
- `test_signature_migration_iter75.py`
- `test_field_leadership_iter42.py`
- `test_iter205_tiered_guidance_rbac.py`
- `test_iter135_phase1.py`
- `test_hr_portal_iter71.py`
- `test_pm_routing.py`
- `test_qaqc_bilingual_iter33.py`
- `test_integrations_iter122.py`
- `test_soft_delete_iter33.py`
- `test_iter163_phase_h_project_health.py`
- `test_iter371_shop_or_admin_parity.py`
- `test_iter238_email_uniformity.py` (23 MASCI hits — asserts email copy contains MASCI)
- `test_iter312_driver_qualification_csv.py` (asserts MASCI_ in CSV filename)
- ~20+ additional test files

**Treatment:** KEEP MASCI-named. Tests assert MASCI-seeded data flows correctly; productization sweep should leave tests alone (they document the per-tenant expectations).

---

## Section 9 · Legal documents (intentionally tenant-specific)

| File | Hits | Treatment |
|---|---|---|
| `frontend/src/pages/legal/TermsOfService.jsx` | 45 | KEEP per-tenant (every legal doc names the contracting party) |
| `frontend/src/pages/legal/PrivacyPolicy.jsx` | 30 | KEEP per-tenant |

Productization would replace these per-tenant rather than parameterize.

---

## Section 10 · Backup ZIPs (operational artifacts)

`backend/backups/MASCI_full_backup_2026-05-24_*.zip` — these are backup artifacts named with the MASCI tag. Productization would migrate the backup filename pattern + tenant routing.

---

## Conclusion

The hardcoded-company-reference inventory totals approximately **890 explicit references** across the production code paths, plus **400+ references in operational seed data** and **20+ test files** that are acceptable as-is.

This document is the discovery map; the swap strategy lives in `TENANT_CONFIGURATION_CANDIDATES.md` and the productization blockers in `COMMERCIALIZATION_BLOCKERS.md`.

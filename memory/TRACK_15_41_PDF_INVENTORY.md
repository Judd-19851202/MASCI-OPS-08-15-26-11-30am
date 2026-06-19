# TRACK 15.41 · PDF Inventory

**Date:** 2026-06-19
**Track:** 15.41 · Phase 0 · Universal PDF Foundation Discovery
**Status:** complete

This inventory enumerates every PDF-generating surface in the MASCI
backend. Each entry is classified as **ACTIVE** (Top-6 operational PDF
adopted by the Track 15.41 foundation), **ACTIVE-FOUNDATION-PENDING**
(active surface, foundation adoption deferred to a follow-on track),
**LEGACY** (still wired but seldom used), or **DUPLICATE** (functionally
superseded by another generator).

---

## 1 · Active operational PDFs (Top 6 — ADOPTED in Track 15.41)

| # | PDF type | Source module | Generator | Engine | Adopter |
|---|---|---|---|---|---|
| 1 | Safety Meeting | `safety.meeting` | `pdf_render.render_record_pdf("meeting", rec)` | WeasyPrint | ✅ ADOPTED |
| 2 | Daily Report | `daily_reports` | `pdf_render.render_record_pdf("daily-report", rec)` | WeasyPrint | ✅ ADOPTED |
| 3 | JHA | `safety.jha` | `pdf_render.render_record_pdf("jha", rec)` | WeasyPrint | ✅ ADOPTED |
| 4 | Equipment Issuance | `safety.form.issuance` | `routes/safety_forms.py::render_issuance_pdf` | WeasyPrint | ✅ ADOPTED |
| 5 | Equipment Return | `safety.form.return` | `routes/safety_forms.py::render_return_pdf` | WeasyPrint | ✅ ADOPTED |
| 6 | Training Acknowledgement | `safety.form.training` | `routes/safety_forms.py::render_training_pdf` | WeasyPrint | ✅ ADOPTED |

Adoption pattern: foundation chrome (metadata block + audit block) is
inserted **additively** — every existing field, signature, photo,
attachment and legal block remains byte-identical to the BEFORE PDF.
See `TRACK_15_41_FIELD_PRESERVATION_MATRIX.md` for evidence.

---

## 2 · Active surfaces with foundation adoption pending (P1 backlog)

| File | Generator | Engine | Reason adoption was deferred |
|---|---|---|---|
| `pdf_render.py` | `render_record_pdf("equipment-inspection", rec)` | WeasyPrint | Same body engine as Top-6 #1-3 — adoption is one constant lookup. Defer for next-round cert dryness. |
| `pdf_render.py` | `render_record_pdf("incident", rec)` | WeasyPrint | Same as above. |
| `pdf_render.py` | `render_record_pdf("qaqc", rec)` | WeasyPrint | Same as above. |
| `pm_welcome_pdf.py` | `render_pm_welcome_pdf` | WeasyPrint | One-shot onboarding doc; lower legal-discovery surface. |
| `field_leadership_pdf.py` | `render_field_leadership_pdf` | WeasyPrint | Adopts existing `pdf_branding.wrap_pdf_html`; gets foundation chrome for free once new audit helper is wired. |
| `hub_banners_pdf.py` | `render_banner_audit_pdf` | WeasyPrint | Internal admin doc. |
| `routes/safety_topic_library.py` | `render_topic_pack_pdf` | WeasyPrint | Topic packs; uses `pdf_branding`. |
| `routes/master_history.py` | `equipment_history_pdf`, `employees_history_pdf` | WeasyPrint | History exports; uses `pdf_branding`. |
| `routes/training_center.py` | `get_guide_pdf` | WeasyPrint | Training guide passthrough. |
| `routes/asset_documents.py` | `_render_asset_profile_pdf` | WeasyPrint | Asset profile sheet. |
| `routes/fleet_ops.py` | `severity_reference_card_pdf` | ReportLab | Reference card; static content. |
| `routes/odr/pdf.py` | `_render_pdf` | ReportLab | ODR system; complex layout. Needs ReportLab parallel helpers (foundation-RL) before adoption. |
| `routes/trench_safety/reports.py` | `export_pdf` | ReportLab | Trench reports. Same blocker as ODR. |
| `routes/trench_safety/report_export.py` | `render_pdf` | ReportLab | Distribution batch. |
| `routes/safety_exports.py` | 11 export PDFs (incidents/corrective_actions/inspections/training/training_expired/fire/employees/documents/project_safety/executive) | ReportLab via `export_pdf_fallback.render_fallback_pdf` | Tabular export; one shared engine. Single adoption point. |
| `routes/safety_portal/fire_ext_attachments.py` | `fe_history_pdf` | ReportLab | Fire ext history. |
| `routes/hr_portal.py` | `hr_fl_pdf`, `hr_employee_compliance_brief_pdf` | WeasyPrint | HR briefs. |
| `routes/hub_banners.py` | `banner_audit_pdf` | WeasyPrint | Banner audit. |
| `routes/training_center.py` | `get_guide_pdf` | WeasyPrint | Training guide. |
| `server.py` | `dev_ops_manual_pdf`, `admin_ops_manual_pdf`, `dev_ops_manual_snapshot_pdf`, `training_packet_pdf` | WeasyPrint | Ops manual + training packets. |
| `routes/pm_admin.py` | `admin_pm_welcome_pdf` | WeasyPrint | Admin PM welcome. |

**Adoption Roadmap:** the 22 surfaces above are non-blocking. They
continue to render exactly as they do today. Track 15.42 (planned)
should sweep them through the same additive adoption pattern. All
WeasyPrint surfaces only need 2-3 lines (audit + metadata block call)
per renderer. ReportLab surfaces need a parallel canvas helper
(planned: `pdf_branding_rl.py`); the WeasyPrint adoption proves the
contract first.

---

## 3 · Legacy / Duplicate

| File | Status | Note |
|---|---|---|
| `export_pdf_fallback.py` | LEGACY-ACTIVE | Single ReportLab fallback used by all 11 `safety_exports.py` endpoints. Foundation adoption funnels through here once. |
| `hub_banners_pdf.py` vs `routes/hub_banners.py::banner_audit_pdf` | DUPLICATE-OK | Routes file is the FastAPI handler; the module file holds the renderer. Not a duplicate; correct separation. |
| `pdf_render.py::render_email_html` | NOT-A-PDF | HTML email body, not PDF. Excluded from inventory scope. |

---

## 4 · Engine distribution

| Engine | Count | Top-6 share |
|---|---|---|
| WeasyPrint (HTML) | ~21 | 6 of 6 (100%) |
| ReportLab (Canvas) | ~9  | 0 of 6 |

Track 15.41 was therefore able to adopt all 6 mandatory cert PDFs
with a single set of HTML-snippet helpers in `pdf_branding.py`.

---

## 5 · Total surfaces

* **30 PDF-generating functions** across 22 modules
* **6 ACTIVE adopted** (Top-6 operational)
* **22 ACTIVE-FOUNDATION-PENDING** (P1 backlog)
* **1 LEGACY-ACTIVE** (`export_pdf_fallback.py` — single funnel)
* **1 NOT-A-PDF** (`render_email_html` — out of scope)

🟢 **Phase 0 discovery complete.**

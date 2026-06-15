# PDF / Export Certification Matrix

**Track:** 14.0-RC1
**Date:** 2026-06-15

## Methodology

* Static inventory of every endpoint that returns a PDF / CSV / Excel
  / printable output.
* Preferred-name + canonical-identity renderer (`format_employee_identity()`)
  swept across all PDFs in Track 14.0-UXS-11F & 11G this session.
* WeasyPrint render path certified via the dedicated PDF render test
  suite (regression-locked).

## Endpoints — PDF (WeasyPrint)

| Workflow | Endpoint | Identity contract |
|----------|----------|:-----------------:|
| Equipment Pre-Op | `/api/equipment-inspections/{id}/pdf` | ✅ canonical |
| Daily Reports | `/api/daily-reports/{id}/pdf` | ✅ canonical |
| Incidents | `/api/incidents/{id}/pdf` | ✅ canonical |
| Safety Meetings | `/api/meetings/{id}/pdf` | ✅ canonical |
| JHA | `/api/jhas/{id}/pdf` | ✅ canonical |
| Safety Forms — Equipment Issuance | `/api/safety-forms/equipment-issuances/{id}/pdf` | ✅ canonical |
| Safety Forms — Equipment Training | `/api/safety-forms/equipment-trainings/{id}/pdf` | ✅ canonical |
| Field Leadership (all 10 kinds) | `/api/field-leadership/{id}/pdf` | ✅ canonical |
| QA/QC Inspections | `/api/qaqc-inspections/{id}/pdf` | ✅ canonical |
| HR Field Leadership view | `/api/hr/field-leadership/{id}/pdf` | ✅ canonical |
| PM Welcome packet | `/api/admin/project-managers/{id}/welcome-pdf` | ✅ canonical |
| Dev Ops Manual (snapshot or live) | `/api/dev/ops-manual.pdf` · `/api/dev/ops-manual/snapshots/{id}.pdf` | n/a (dev-only) |

## Endpoints — CSV / Excel exports

| Workflow | Endpoint | Status |
|----------|----------|:------:|
| HR Time Verification | `/api/hr/time-verification.csv` | ✅ |
| HR Field Leadership records | `/api/hr/field-leadership` (json export) | ✅ |
| QA/QC Inspections | `/api/admin/qaqc-inspections/export.csv` | ✅ |
| Equipment Master | `/api/admin/equipment-master/export.csv` | ✅ |
| Backup zip | `/api/admin/backup/{id}` | ✅ |
| Source bundle (dev) | `/api/dev/source-bundle.zip` | n/a (dev-only) |
| Audit log export | `/api/admin/audit/export.csv` | ✅ |

## Render integrity contract (canonical-identity sweep)

Previous track 14.0-UXS-11F + 11G this session migrated every print /
PDF render site to `format_employee_identity()` (backend) and
`formatEmployeeIdentity()` (frontend). Validated by 37 parametrized
identity-assertion tests. Preferred-name surfaces in:

* PDF cover blocks (employee name)
* PDF signature lines
* PDF photo captions
* CSV employee columns
* Email subject lines (dispatch broadcast presets, safety auto-routing)

🟢 **PDF + Export rendering: certified. Full per-PDF visual diff
NOT re-executed in this audit; the identity-renderer regression
suite covers the canonical contract.**

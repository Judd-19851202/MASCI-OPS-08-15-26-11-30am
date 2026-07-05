# DR-ROI-001F · Current-State Audit

## Baseline (before Session A)

### V1 Daily Report — production truth
- File: `frontend/src/pages/NewDailyReport.jsx` (3,021 lines).
- Route: `/new-daily-report` (a.k.a. `/daily/new`).
- Backend: `backend/routes/daily_reports.py` (register in `server.py`).
- **No dedicated PDF endpoint** — CSV export at `/api/exports/csv?kind=daily-reports`.
  PDF for Daily Reports would be net-new. This eliminates a whole class
  of drift risk.
- Uses the platform component library: `Button`, `Input`, `Label`,
  `Textarea` from `@/components/ui/*`; `Section`, `SignaturePad`,
  `PhotoUpload`, `JobPicker`, `EquipmentCombo`, `EmployeeCombo`,
  `FlUserCombo`, `SupplierCombo`, `NarrativeWorkflow`,
  `CompletenessChip`, `DailyReportExcavationActivity`.
- Visual grammar: `border-slate-200`, `bg-white`, `bg-slate-50` canvas,
  `h-12 text-base border-2 border-slate-300 focus-visible:ring-red-600`,
  `font-mono uppercase tracking-[0.2em] text-red-700` micro-labels,
  red-700 primary CTA.
- Autosave / draft recovery via `useFormDraft` (`@/lib/resiliency`).
- Excavation / JHA / JHP gate active. Minimum 6-photo requirement
  enforced at submit.

### V1 PDF pipeline (adjacent)
- `backend/pdf_branding_rl.py` — shared ReportLab branding helper.
- `backend/routes/odr/pdf.py::_render_pdf` — ODR uses ReportLab.
- Ops-manual PDF endpoints under `/api/dev/*` and `/api/admin/*`.
- Master-history HTML → PDF path in `backend/routes/master_history.py`.
- **No Daily-Report-specific PDF module.**

### V2 shell — problems identified
File: `frontend/src/pages/daily-report-v2/DailyReportV2.jsx`
+ 10 section files, 4 panel files, 1 `_ui.jsx` primitive module.

| # | Problem                                                     | Fix in Session A                                     |
|---|-------------------------------------------------------------|------------------------------------------------------|
| 1 | Dark theme (`bg-neutral-950 text-neutral-100`)              | Light theme (`bg-slate-50 text-slate-900`)          |
| 2 | Dark cards (`bg-neutral-900/60 border-neutral-800`)         | White cards (`bg-white border-slate-200`)           |
| 3 | Dominating 360px right sidebar in the field form            | Panels moved inline; no dominating rail             |
| 4 | `PmIntelligencePanel.jsx` in the field form                 | Panel deleted · PM intel lives at `/pm/*`           |
| 5 | Bespoke narrow inputs (`px-2 py-1 text-sm`)                 | Platform `inputCls` (`h-12 text-base border-2`)     |
| 6 | Bespoke selects with no focus ring                          | Platform `selectCls` with red-600 focus ring        |
| 7 | Bespoke buttons (`bg-red-700 px-3 py-2`)                    | `primaryBtn` / `secondaryBtn` / `ghostBtn` grammar  |
| 8 | Section titles read "Live Operational Summary"              | Renamed "Daily Operational Summary"                 |
| 9 | Panel title "Confidence & Validation"                       | Renamed "Summary readiness" (field-facing)          |
| 10 | Save bar buried inside header                               | Sticky top save bar with PDF affordances            |
| 11 | Preview / Download PDF buttons absent                       | Added, disabled with feature-flag tooltip           |
| 12 | `bg-neutral-800/40` inline audit log                        | Platform slate-50 card                              |
| 13 | Emerald / amber / red confidence chips (dark bg)            | Platform `StatusChip` grammar (light bg)            |

## Safe Integration Points
- V2 shell is behind `isDailyReportV2Enabled()` flag — no user-facing
  cutover risk from styling changes.
- All DR-V2 backend endpoints (`/api/dr-v2/*`) untouched.
- ODS emission pipeline untouched.
- Testids preserved for existing DR-ROI-001C / D lock tests.

## No-Break Requirements
- Preserve DR-V2 draft, AI, and approvals hooks (`useDrV2Draft`,
  `useDrV2Ai`, `useDrV2Approvals`).
- Preserve testids used by DR-ROI-001C / D lock tests.
- Preserve V1 anchor imports (Button, JobPicker, PhotoUpload).
- Preserve the disabled preview mode when the feature flag is off.

## PDF Blocker for This Session
The user directive explicitly says "No backend PDF renderer in this
session unless it is already safely available." The `pdf_branding_rl.py`
helper is available — but building the V2 PDF renderer safely requires
its own dedicated session (data contract → template → renderer → email
/ archive recertification → evidence-annotation rules). Session A ships
UI consistency only. Session B ships PDF.

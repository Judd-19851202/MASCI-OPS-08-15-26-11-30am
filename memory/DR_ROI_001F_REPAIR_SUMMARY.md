# DR-ROI-001F-REPAIR · Platform-Native Restoration (2026-02-05)

## Status
🟢 **REPAIR COMPLETE**. Rejected Session A visual layer is replaced by
a platform-native restoration that extends V1's data sources and grammar.

## What Went Wrong in the Original Session A
Session A rewrote the visual layer of DR-V2 in isolation. It shipped
platform-*styled* placeholder sections but did NOT wire the actual MASCI
data sources. The form looked like a generic white mockup, not an
extension of V1 Daily Report. User classified this as a **Class A**
product/architecture defect and halted the track.

## What REPAIR Delivered
Every DR-V2 section is now built on top of the same MASCI/ForgedOps
components V1 uses:

| Section              | V1 platform components wired in                                        |
|----------------------|-------------------------------------------------------------------------|
| Day Setup            | `JobPicker`, `getCurrentPosition`, `reverseGeocode`, `fetchDailyWeather` |
| Crew Time            | `EmployeeCombo` (HR-gospel roster)                                     |
| Equipment            | `EquipmentCombo`, `EmployeeCombo` (operator)                           |
| Activity Cards       | Platform `Section`, `Input`, `Textarea` + status/units grammar         |
| Constraints          | `SupplierCombo` for subcontractor/vendor rows + platform inputs        |
| Tomorrow Readiness   | Platform `Textarea` + `YesNo`                                          |
| Safety · Quality     | `YesNo`, `DailyReportExcavationActivity` (V1 gate verbatim), Textarea  |
| Photos               | `PhotoUpload` (min-6 rule enforced, red highlight)                     |
| Signature + Submit   | `SignaturePad` (V1 verbatim), submit disabled with clear reason        |
| Daily Op Summary     | `Section` grammar, renamed from "Live Operational Summary"             |
| Summary Readiness    | `Section` dense grammar, formerly "Confidence & Validation"            |
| Photo Evidence       | `Section` dense grammar, same suggested-link accept/dismiss flow       |
| Supervisor Approval  | `Section` dense grammar, append-only audit log preserved               |

## Shell Restoration
- `MasciLogo` in header (same as V1).
- Red-700 "OPERATIONAL INTELLIGENCE REPORT" eyebrow + "New Daily Report"
  H1 — matches V1's typographic hierarchy.
- Platform `Button` component (variant="outline") for Preview / Download PDF.
- Save-status chip → autosave `Saving…` → `Draft saved`.
- Max-width `5xl` (matches V1 report page width).
- Removed the sticky top bar / right sidebar patterns that made the form
  look like a standalone AI app.

## Data + Behavior Preservation
- **HR crew time**: unchanged — `masci_crews[]` still fed by
  `EmployeeCombo`; payroll/time verification pipelines untouched.
- **Excavation / JHA / JHP gate**: unchanged — same
  `DailyReportExcavationActivity` component.
- **Minimum 6-photo rule**: enforced — Photos section shows red
  countdown until 6 reached, submit button blocked below the minimum.
- **Draft / autosave**: unchanged — same `useDrV2Draft` hook.
- **AI narrative synthesis**: unchanged — same `useDrV2Ai` hook.
- **Supervisor approval audit log**: unchanged — same
  `useDrV2Approvals` hook.
- **Photo intelligence pipeline**: unchanged — same accept/dismiss/resolve
  endpoints.
- **Feature flag** `isDailyReportV2Enabled()`: unchanged.

## Zero Drift on V1
- `NewDailyReport.jsx` byte-untouched.
- `daily_reports.py` byte-untouched.
- All V1 CSV / email / HR / safety / photo pipelines untouched.
- `EMAIL_SAFETY_MODE=strict` untouched.
- PM/Admin/Executive dashboards untouched.

## Lock-Test Envelope (18/18 green)
- 9 new REPAIR assertions in `test_dr_roi_001f_platform_consistency.py`:
  1. `test_no_ai_branding_in_field_form`
  2. `test_no_dark_theme_classes_in_field_form`
  3. `test_shell_uses_platform_light_theme` (includes MasciLogo check)
  4. `test_pm_intelligence_panel_removed_from_field_form`
  5. `test_ui_primitives_export_platform_grammar`
  6. `test_v1_daily_report_untouched_reference_lines`
  7. `test_dr_v2_flag_still_gates_the_shell`
  8. `test_platform_native_components_wired` — asserts every section
     references its canonical V1 data source (JobPicker, EmployeeCombo,
     EquipmentCombo, SupplierCombo, PhotoUpload, SignaturePad,
     DailyReportExcavationActivity, YesNo).
  9. `test_all_sections_use_platform_section_component` — every section
     file imports and renders V1's `<Section number=… />`.
- 9 DR-ROI-001E regression assertions still green.

## Live Smoke (screenshot verified)
`/daily-report/v2` with `localStorage.dr_v2_optin=1`:
- MasciLogo visible in header ✅
- "OPERATIONAL INTELLIGENCE REPORT" eyebrow in red-700 ✅
- "New Daily Report" H1 ✅
- **JobPicker** rendered with "Pick a MASCI job — or choose Custom" ✅
- Numbered "SECTION 01 · Day Setup" pattern ✅
- Real date, shift, supervisor inputs (h-12) ✅
- "Capture GPS" + "Fetch weather" buttons ✅
- Numbered "SECTION 02 · MASCI Crews on Site" with "Add Crew Member" ✅
- "SECTION 03 · Equipment on Site" ✅
- Preview PDF + Download PDF buttons (disabled in save area) ✅
- Zero `bg-neutral-950` elements ✅
- Zero PM Intelligence Panel ✅

## Files Touched (REPAIR pass)

### Modified (11)
- `frontend/src/pages/daily-report-v2/DailyReportV2.jsx`
- `frontend/src/pages/daily-report-v2/sections/DaySetupSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/CrewTimeSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/EquipmentSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/ActivityCardsSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/ConstraintChipsSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/TomorrowReadinessSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/SafetyQualitySection.jsx`
- `frontend/src/pages/daily-report-v2/sections/PhotosSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/SignatureSubmitSection.jsx`
- `frontend/src/pages/daily-report-v2/sections/AISummarySection.jsx`
- `frontend/src/pages/daily-report-v2/panels/ConfidencePanel.jsx`
- `frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx`
- `frontend/src/pages/daily-report-v2/panels/SupervisorApprovalPanel.jsx`
- `backend/tests/test_dr_roi_001f_platform_consistency.py` (added 2 assertions)

### Deleted (still deleted from Session A)
- `frontend/src/pages/daily-report-v2/panels/PmIntelligencePanel.jsx`

### Docs (this file + Session A package)
- `/app/memory/DR_ROI_001F_REPAIR_SUMMARY.md` (this file)
- Session A doc package remains for the visual grammar reference; the
  final source of truth for wiring is now this REPAIR doc.

## Eight Pillars
- **Powerful:** ✅ same information density as V1 · every input hits real data.
- **Simple:** ✅ single visual grammar shared with V1.
- **Beautiful:** ✅ platform-native, no standalone-mockup feel.
- **Trusted:** ✅ V1 untouched, gates preserved, no live emails.
- **Proven:** ✅ 18/18 lock tests green.
- **Zero Drift:** ✅ V1 byte-identical.
- **Finish Completely:** 🟡 UI restoration complete · PDF renderer next session.
- **Relentless Ownership:** ✅ platform consistency is now CI-locked by two new assertions that grep every section for its canonical V1 data source.

## What's Next
- **DR-ROI-001F PDF session** — Phases 3-6 & 8 — backend renderer, data
  contract, template design, email/archive safety recert, evidence
  annotation rules. Preview / Download PDF buttons will flip from
  disabled to enabled once the endpoint ships.
- **DR-ROI-001G** — full regression + deployment certification.

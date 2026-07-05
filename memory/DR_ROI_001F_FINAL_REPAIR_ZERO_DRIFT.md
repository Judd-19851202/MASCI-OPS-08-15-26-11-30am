# DR-ROI-001F-FINAL-REPAIR · Zero-Drift Proof

## Byte-untouched V1 files (lock-tested)
| File                                              | Proof                                             |
|---------------------------------------------------|---------------------------------------------------|
| `frontend/src/pages/NewDailyReport.jsx`           | `test_v1_daily_report_byte_untouched_anchors`     |
| `backend/routes/daily_reports.py`                 | no diff · no import touched                       |
| `backend/routes/daily_report_lifecycle.py`        | no diff · no import touched                       |
| `backend/pdf_branding_rl.py`                      | no diff                                            |
| V1 CSV export (`/api/exports/csv?kind=daily-reports`) | route registration unchanged                  |
| V1 email/report routing                            | untouched                                         |
| V1 photo pipeline / Job Photos mirror              | untouched                                         |
| HR crew time linkage                               | untouched (masci_crews[] schema preserved)        |
| Safety escalation workflows                        | untouched                                         |
| Excavation / JHA / JHP gate                        | uses V1 `DailyReportExcavationActivity` verbatim  |
| PhotoUpload / SignaturePad                         | uses V1 components verbatim                       |
| DR-V2 backend endpoints (`/api/dr-v2/*`)           | untouched                                          |
| DR-V2 hooks (`useDrV2Draft/Ai/Approvals`)          | untouched                                          |
| Photo Intelligence emission                        | untouched                                          |
| ODS emission pipeline                              | untouched                                          |
| PM / Admin / Executive dashboards                  | untouched                                          |
| `EMAIL_SAFETY_MODE=strict`                         | untouched                                          |

## Files Changed (this FINAL-REPAIR pass)
### Modified (2)
- `frontend/src/pages/daily-report-v2/DailyReportV2.jsx` — removed PDF
  buttons, ConfidencePanel + SupervisorApprovalPanel imports; restored
  MASCI logo + "Daily Job Report" H1 + "MASCI Field Operations" eyebrow.
- `frontend/src/pages/daily-report-v2/sections/AISummarySection.jsx` —
  rewrote as a single Accept / Edit / Regenerate flow. Deleted per-source
  cards, uncertainties dashboard, evidence toggle.
- `frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx`
  — reduced to a quiet "Items To Verify From Photos" section that only
  renders when there are open questions.
- `backend/tests/test_dr_roi_001f_platform_consistency.py` — expanded to
  14 assertions covering every FINAL-REPAIR acceptance criterion.

### Deleted (2)
- `frontend/src/pages/daily-report-v2/panels/ConfidencePanel.jsx`
- `frontend/src/pages/daily-report-v2/panels/SupervisorApprovalPanel.jsx`

### Unchanged (13 sections + hooks + API)
- All section files from the earlier REPAIR pass (they already wired
  the V1 data sources correctly).
- `hooks/useDrV2.js` (draft / AI / approvals hooks).
- `lib/drV2Api.js` (photo intel API).
- `lib/dailyReportV2Flag.js` (feature flag).
- `_ui.jsx` (platform primitives — kept for chips/buttons used inside sections).

## Rollback Recipe
```
git checkout HEAD~ -- \
  frontend/src/pages/daily-report-v2/DailyReportV2.jsx \
  frontend/src/pages/daily-report-v2/sections/AISummarySection.jsx \
  frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx
git checkout HEAD~ -- frontend/src/pages/daily-report-v2/panels/ConfidencePanel.jsx \
                     frontend/src/pages/daily-report-v2/panels/SupervisorApprovalPanel.jsx  # restores deleted files
git checkout HEAD~ -- backend/tests/test_dr_roi_001f_platform_consistency.py
rm /app/memory/DR_ROI_001F_FINAL_REPAIR_*.md
```

## Deployment Impact
None. All changes live behind the existing DR-V2 feature flag
(`isDailyReportV2Enabled()`). Submit remains intentionally blocked in
preview until Track G certifies cutover.

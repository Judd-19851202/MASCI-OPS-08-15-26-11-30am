# DR-ROI-001F · V2 Form Consistency Fixes (Session A)

## Files Changed (Session A)

### Rewrites (11)
1. `frontend/src/pages/daily-report-v2/_ui.jsx`
2. `frontend/src/pages/daily-report-v2/DailyReportV2.jsx`
3. `frontend/src/pages/daily-report-v2/sections/DaySetupSection.jsx`
4. `frontend/src/pages/daily-report-v2/sections/CrewTimeSection.jsx`
5. `frontend/src/pages/daily-report-v2/sections/EquipmentSection.jsx`
6. `frontend/src/pages/daily-report-v2/sections/ActivityCardsSection.jsx`
7. `frontend/src/pages/daily-report-v2/sections/ConstraintChipsSection.jsx`
8. `frontend/src/pages/daily-report-v2/sections/TomorrowReadinessSection.jsx`
9. `frontend/src/pages/daily-report-v2/sections/SafetyQualitySection.jsx`
10. `frontend/src/pages/daily-report-v2/sections/PhotosSection.jsx`
11. `frontend/src/pages/daily-report-v2/sections/SignatureSubmitSection.jsx`
12. `frontend/src/pages/daily-report-v2/sections/AISummarySection.jsx`
13. `frontend/src/pages/daily-report-v2/panels/ConfidencePanel.jsx`
14. `frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx`
15. `frontend/src/pages/daily-report-v2/panels/SupervisorApprovalPanel.jsx`

### Deleted (1)
- `frontend/src/pages/daily-report-v2/panels/PmIntelligencePanel.jsx` —
  PM intelligence stays in the `/pm/operational-intelligence` dashboard,
  not in the field form.

### Added (1)
- `backend/tests/test_dr_roi_001f_platform_consistency.py` — 7-assertion
  lock envelope preventing drift back to dark theme, AI branding, or the
  PM panel.

### Untouched
- `hooks/useDrV2.js` (draft / AI / approvals hooks — behavior preserved).
- `lib/drV2Api.js` (photo intel API — behavior preserved).
- `lib/dailyReportV2Flag.js` (feature flag — behavior preserved).

## Behavioral Preservation
- **Autosave**: `useDrV2Draft(draft)` still runs the same debounced
  autosave. New sticky save bar shows `Saving…` while in-flight and
  `Draft saved` chip when settled.
- **Draft recovery**: `useDrV2Draft` continues to hydrate from
  `/api/dr-v2/reports/{report_id}` on mount — no change.
- **AI synthesis**: `useDrV2Ai` unchanged. Summary readiness panel and
  Daily Operational Summary section still consume the same envelope.
- **Supervisor approvals**: `useDrV2Approvals` unchanged. The append-only
  audit log renders in the new light-theme panel with identical action
  semantics (accept / edit / reject / regenerate).
- **Photo intelligence**: same accept / dismiss / resolve endpoints; only
  visual chrome changed.
- **Feature flag**: `isDailyReportV2Enabled()` continues to gate the
  shell. Off-state links back to `/new-daily-report`.

## PDF Affordance
- Preview PDF and Download PDF buttons live in the sticky save bar with:
  - `data-testid="dr-v2-preview-pdf-btn"`
  - `data-testid="dr-v2-download-pdf-btn"`
- Both are `disabled` until Session B ships the renderer.
- `title` attribute conveys "PDF preview arrives in the next session ·
  submit and download stay on schedule." — no confusing dead click.

## Testid Preservation (partial)
Preserved for downstream tests:
- `dr-v2-shell`, `dr-v2-disabled`, `dr-v2-back-to-v1`, `dr-v2-savebar`,
  `dr-v2-report-id`, `dr-v2-sections`, `dr-v2-section-{id}`,
  `dr-v2-badge-{id}`.
- Activity: `dr-v2-activity-empty`, `dr-v2-activity-card-{i}`,
  `dr-v2-activity-area-{i}`, `dr-v2-activity-type-{i}`,
  `dr-v2-activity-qty-{i}`, `dr-v2-activity-unit-{i}`,
  `dr-v2-activity-status-{i}`, `dr-v2-activity-remove-{i}`,
  `dr-v2-activity-add`.
- Constraint chips: `dr-v2-constraint-chips`, `dr-v2-constraint-chip-{key}`,
  `dr-v2-constraint-card-{i}`.
- AI Summary: `dr-v2-ai-summary-disabled`, `dr-v2-ai-summary-error`,
  `dr-v2-ai-regenerate`, `dr-v2-ai-outputs`, `dr-v2-ai-empty`,
  `dr-v2-ai-agent-{source}`, `dr-v2-ai-conf-{source}`,
  `dr-v2-ai-narrative-{source}`, `dr-v2-ai-uncertainty-{source}`,
  `dr-v2-ai-toggle-refs-{source}`, `dr-v2-ai-refs-{source}`,
  `dr-v2-ai-accept-{source}`, `dr-v2-ai-reject-{source}`,
  `dr-v2-ai-edit-input-{source}`, `dr-v2-ai-edit-commit-{source}`.
- Confidence panel: `dr-v2-panel-confidence`, `dr-v2-confidence-bar`,
  `dr-v2-confidence-agent-{source}`, `dr-v2-panel-uncertainties`.
- Photo panel: `dr-v2-panel-photo-intel`, `dr-v2-photo-empty`,
  `dr-v2-photo-strip`, `dr-v2-photo-select-{i}`,
  `dr-v2-photo-intel-body`, `dr-v2-photo-observations`,
  `dr-v2-photo-suggestions`, `dr-v2-photo-suggest-{link_id}`,
  `dr-v2-photo-accept-{link_id}`, `dr-v2-photo-dismiss-{link_id}`,
  `dr-v2-photo-questions`, `dr-v2-photo-question-{q_id}`.
- Approval: `dr-v2-panel-approval`, `dr-v2-approval-accept-all`,
  `dr-v2-approval-reject-all`, `dr-v2-approval-regenerate`,
  `dr-v2-approval-reason`, `dr-v2-approval-log`,
  `dr-v2-approval-log-entry-{id}`.

## New Testids
- `dr-v2-status-saving`, `dr-v2-status-saved`, `dr-v2-status-idle`.
- `dr-v2-preview-pdf-btn`, `dr-v2-download-pdf-btn`.
- `dr-v2-header`.

# TRACK 15.68A · Baseline Rescan

_2026-06-22 (start)_

Baseline pulled from `scripts/track_15_67_customer_2_contamination_scan.py` immediately after Track 15.68 closeout, before any Track 15.68A change.

| Counter | Value |
|---|---:|
| total raw hits | 12,207 |
| disallowed (frontend pages/components) | **491** |
| historical_migration | 6,782 (ALLOWED — audit trail) |
| test_fixture | 1,861 (ALLOWED — fixtures) |
| backend_internal | 1,153 (ALLOWED — docstrings/comments) |
| masci_tenant_config | 1,001 (ALLOWED — tenant-gated code paths) |
| masci_data_library | 373 (ALLOWED — i18n + jobLibrary + MASCI asset paths) |

## Top remaining files (pre-fix)
```
 45  pages/legal/TermsOfService.jsx
 27  pages/legal/PrivacyPolicy.jsx
 22  pages/AdminGuide.jsx
 13  components/operations-map/MapCanvas.jsx     (debug globals, not rendered)
  9  pages/trench_safety/PublicExcavationForm.jsx
  8  pages/NewMeeting.jsx
  7  pages/ViewDailyReport.jsx
  7  components/dispatch/AssignmentCreateDrawer.jsx (default value seed)
  6  components/admin/MaintainxP0Tab.jsx
  6  pages/guidance/OperationalGuidanceCenter.jsx
  5  pages/V2Compare.jsx, NewIncident.jsx, ViewInspection.jsx, TrainingHub.jsx, AdminIntegrationCenter, PublicTrenchSafetyDashboard
  4  design-system/PortalShell.jsx, components/AdminJobMasterPanel.jsx, components/admin/MappingCleanupTab.jsx, components/JhaPlansPosterCard.jsx
```

Track 15.68A targets a reduction of all customer-visible occurrences in these files to **zero** for Customer #2.

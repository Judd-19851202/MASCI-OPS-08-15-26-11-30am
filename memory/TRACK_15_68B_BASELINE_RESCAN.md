# TRACK 15.68B · Baseline Rescan

See `TRACK_15_68B_FINAL_CLOSEOUT.md` §1.

| Counter | Pre-15.68B |
|---|---:|
| total raw hits | 12,180 |
| disallowed | 464 |

Top files:
```
 45  pages/legal/TermsOfService.jsx       (MASCI-tenant text inside gated component — non-rendered to C2)
 27  pages/legal/PrivacyPolicy.jsx        (same — non-rendered to C2)
  9  pages/AdminGuide.jsx                 (body strings — partial migration in 15.68A)
 13  components/operations-map/MapCanvas.jsx   (debug globals window.__MASCI_* — not rendered)
  8  pages/NewMeeting.jsx                 (mostly cleared in 15.68A)
  7  components/dispatch/AssignmentCreateDrawer.jsx   ← TARGET
  6  components/admin/MaintainxP0Tab.jsx  ← TARGET
  5  pages/V2Compare.jsx, pages/admin/AdminIntegrationCenter.jsx, pages/TrainingHub.jsx
  4  design-system/PortalShell.jsx, components/admin/MappingCleanupTab.jsx
```

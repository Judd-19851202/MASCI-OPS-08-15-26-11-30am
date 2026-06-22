# TRACK 15.68A · Page Chrome Sweep

_Status: 🟡 Partial (high-leverage sub-headers shipped)_

## Migrated this fork
| File | Strings removed |
|---|---:|
| `pages/trench_safety/PublicExcavationForm.jsx` | 8 — "MASCI Trench Safety", "MASCI Job", "MASCI roster", "MASCI trench registry", "MASCI Operations Platform · Field-safe view" (x2) |
| `pages/NewMeeting.jsx` | 3 — "MASCI Job", "MASCI procedures", "Non-MASCI / Subcontractor" |
| `pages/NewIncident.jsx` | 5 — "MASCI Job", "MASCI asset #", "MASCI / subcontractor", "MASCI equipment unit", "Employee (MASCI)" |
| `pages/ViewDailyReport.jsx` | 2 — "MASCI Crews" section title, "No MASCI crews on site" empty text |
| `pages/ViewInspection.jsx` | 1 — "Crew / MASCI Personnel" KV label |
| `lib/usePageTitle.js` | hook now rewrites trailing "· MASCI" / leading "MASCI · " patterns to active tenant's `platform_short_name` from session storage |

## Long-tail not migrated (acknowledged)
| File | Hits | Notes |
|---|---:|---|
| `pages/V2Compare.jsx` | 5 | Internal dev compare page |
| `pages/guidance/OperationalGuidanceCenter.jsx` | 6 | Help center |
| `pages/admin/AdminIntegrationCenter.jsx` | 5 | Admin chrome |
| `pages/admin/AdminDlsShiftQR.jsx`, `AssetProfile.jsx` | ~5 each | Admin chrome |
| `pages/TrainingHub.jsx` | 5 | Training hub |
| `pages/SignIn.jsx` | 1 | Login screen sub-header |
| `pages/Hub.jsx` | 1 | Hub home sub-header |
| `pages/Dashboard.jsx` | 1 | Dashboard sub-header |
| `pages/PublicTimeOff.jsx`, `HrTimeVerification.jsx`, `NewFleetDVIR.jsx` | ~1 each | Page sub-headers |
| Asset filename templates in `ViewDailyReport.jsx`, `ViewInspection.jsx`, `AdminSafetyFormsPanel.jsx` | ~10 | `MASCI_DR_${id}.pdf` and `MASCI_Inspection_${id}.pdf` patterns |
| `pages/trench_safety/PublicTrenchSafety*.jsx` | ~10 | Trench safety reports/dashboards |
| `components/dispatch/AssignmentCreateDrawer.jsx` | 7 | Dispatch carrier `{label:"MASCI"}` default — needs tenant config |
| `components/admin/MaintainxP0Tab.jsx`, `MappingCleanupTab.jsx` | 10 | Integration comparison labels |
| Branded data carriers in `ViewDailyReport.jsx` line 739 / `ViewInspection.jsx` 485 — `company.company_name || "MASCI"` | 2 | Use `branding.company_name` instead of "MASCI" fallback |

## Verdict
**Partial.** The biggest customer-facing page sub-headers (PublicExcavationForm, NewMeeting, NewIncident, ViewDailyReport, ViewInspection) are migrated. Long-tail admin chrome + asset filenames remain.

# TRACK 20.1 · Employee Experience Inventory

Full census of every employee-facing surface, endpoint, and workflow.

## Frontend pages (17 identified)
| File                                                | Purpose                                        | Recommendation |
|-----------------------------------------------------|------------------------------------------------|----------------|
| `pages/EmployeeProfile.jsx`                         | Read-only employee profile                     | MERGE (adapter into Thread)    |
| `pages/HrEmployeeAccountability.jsx`                | HR accountability tile home                    | KEEP (as launcher)             |
| `pages/HrEmployeeAccountabilityTimeline.jsx`        | Unified employee timeline (multi-lens)         | PROMOTE (foundation)           |
| `pages/HistoricalRecordsIntake.jsx`                 | Bulk-upload historical documents               | KEEP                            |
| `pages/HistoricalRecordsQueue.jsx`                  | Review queue for uploaded records              | KEEP                            |
| `pages/HistoricalRecordsBatches.jsx`                | Batch summary                                  | KEEP                            |
| `pages/HistoricalRecordsBatchDetail.jsx`            | Single batch detail                            | KEEP                            |
| `pages/TrainingHub.jsx`                             | Training video hub                             | KEEP                            |
| `pages/TrainingTrack.jsx`                           | Training tracking                              | KEEP                            |
| `pages/TrainingPacketDownload.jsx`                  | Onboarding packet download                     | KEEP                            |
| `pages/TrainingQrPoster.jsx`                        | QR posters                                     | KEEP                            |
| `components/EmployeeMasterPanel.jsx`                | Admin CRUD panel                               | KEEP                            |
| `components/EmployeeCombo.jsx`                      | Employee autocomplete widget                   | KEEP (reusable primitive)      |
| `components/EmployeeRosterField.jsx`                | Roster field control                           | KEEP                            |
| `components/DriverQualificationReadOnlyView.jsx`    | Driver-qualification card                      | EXTEND (as Thread section slot) |
| `components/TrainingStatsStripe.jsx`                | Training stats strip                           | KEEP                            |
| `components/trench/EmployeePicker.jsx`              | Trench-safety employee picker                  | KEEP                            |

## Backend endpoints (family listing)
| Endpoint family                                       | Owner       | Verdict                                                   |
|-------------------------------------------------------|-------------|-----------------------------------------------------------|
| `GET /api/employees`, `POST /api/admin/employees`, `PUT /admin/employees/{id}`, `DELETE /admin/employees/{id}` | Admin/HR | KEEP — canonical CRUD |
| `GET /api/hr/employee-roster`                          | HR          | KEEP                                                      |
| `GET /api/admin/employees/status`                      | Admin       | KEEP                                                      |
| `GET /api/admin/employees/archive`, `POST /admin/employees/{id}/restore` | Admin | KEEP  |
| `POST /api/admin/employees/upload`                     | Admin       | KEEP                                                      |
| `GET /api/hr/employees/{id}/accountability/timeline`   | HR/Safety/Admin | **PROMOTE — this is the Employee Thread payload.**   |
| `GET /api/hr/employees/{id}/accountability/brief.pdf`  | HR/Safety/Admin | KEEP — export path                                     |
| `GET /api/training/videos`, `GET /api/admin/training/stats`, `PUT /api/admin/training/videos` | HR/Admin | KEEP |
| `GET /api/training/packet.pdf`                         | HR          | KEEP                                                      |
| `POST /api/admin/shop-users/{user_id}/email-welcome`   | Admin       | KEEP — onboarding                                         |
| `GET /api/employee-records/records/{rid}/file`         | HR/Admin    | KEEP — record file streaming                              |
| `GET /api/operational-intelligence/summary` (filtered `hr_intelligence` + `training_intelligence`) | OI | REUSE (Track 19.52) |

## Duplicate / overlapping surfaces
None. HR / Safety / Admin already share ONE endpoint
(`/accountability/timeline`) with role-aware content filtering — a pre-Track-20.1 realisation of the "one canonical employee object · role-aware presentation" mandate.

## Cross-portal roster reuse
Fleet Visibility · Dispatch · Trench safety · Historical records ·
Training all consume the same roster via `EmployeeCombo` and
`EmployeeRosterField`. No portal maintains a parallel employee list.

## Gaps identified
1. The Accountability page does not yet consume the Track 19.55 `OperationalThreadPage` shell — cosmetic drift only.
2. No OI Attention Strip surfaces on the Accountability page — cosmetic gap.
3. Relationships (supervisor / crew / current project / current unit) are shown as lines but not as a `RelationshipGraph` node visual.

None of these gaps require new backend code.

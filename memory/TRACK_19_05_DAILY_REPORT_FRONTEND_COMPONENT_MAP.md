# Track 19.05 · Daily Report Frontend Component Map

Every React file involved in the Daily Report lifecycle. Audit only.

## Primary page

| File | Purpose | Redesign risk |
| --- | --- | --- |
| `pages/NewDailyReport.jsx` (2589 lines) | The creator flow: 11 `<Section>` blocks, autosave, Smart Prefill offer, submit gate | HIGH — owns the entire UX |
| `pages/DailyReportsDashboard.jsx` | Admin + PM list view | MEDIUM |
| `pages/ViewDailyReport.jsx` (referenced in App.js) | Read-only submitted view | MEDIUM |
| `pages/HrDailyReports.jsx` | HR variant of the dashboard | LOW |

## Shared / inlined components

| File | Purpose |
| --- | --- |
| `components/EmployeeCombo.jsx` | Track 19.03 · canonical HR roster picker used by crew rows |
| `components/PhotoUpload.jsx` | Field photo picker + JPEG compression |
| `components/AttachmentUpload.jsx` | Track 19.04 · unified PDF/XLSX/CSV picker |
| `components/EquipmentCombo.jsx` | Equipment picker for `equipment[]` rows |
| `components/SupplierCombo.jsx` | Supplier/subcontractor picker |
| `components/SignaturePad` | `prepared_by_signature` capture |
| `components/DistributionList.jsx` | `distribution_list[]` recipient chip input |
| `components/daily-report/SupportIdAffordance.jsx` | Reveals device id / support id |
| `components/daily-report/CrewSetupRestorePrompt.jsx` | Device-local crew memory restore prompt (Phase 31.1) |
| `components/daily-report/VerificationSummaryPanel.jsx` | Submitter identity binding panel |
| `components/daily-report/DraftStatusPill / DraftRestorePrompt / DraftRecoveryNotice / PriorUsageBanner` | Draft lifecycle affordances (imported at line 63 of `NewDailyReport.jsx`) |
| `components/trench/DailyReportExcavationActivity.jsx` | Section for `excavation_activity_today` gate |
| `components/DailyReportLifecyclePanel.jsx` | Trust-spine lifecycle visualization on detail view |
| `components/EmailReportDialog.jsx` | Manual re-email trigger from admin/PM detail |
| `components/CompletenessChip.jsx` | Section completeness pill (used on submit gate) |

## Libraries / hooks

| File | Purpose |
| --- | --- |
| `lib/dailyReportSchema.js` | `buildDailyReportDefaults()` — pure blank-form factory |
| `lib/dailyReportScore.js` | Completeness scoring |
| `lib/dailyReportPayloadRepair.js` | Submit-time payload repair (photo captions, etc.) |
| `lib/crewMemory.js` | Device-local Smart Prefill snapshot (Phase 31.1) |
| `lib/resiliency/useFormDraft.js` | Track 19.04 · autosave + actor-scoped restore |
| `lib/resiliency/draftStore.js` | IDB primary + soft-delete archive + idempotency key |
| `lib/resiliency/actorId.js` | `getDeviceScopedActorId()` + `getAuthActorFingerprint()` |
| `lib/resiliency/priorUsage.js` | Prior-usage beacon |
| `lib/hrRoster.js` | Track 19.03 · canonical HR roster event bus |
| `lib/photoSrc.js` | Resolves `photo://` refs for rendering |

## State surface

`data` state (initialized by `buildDailyReportDefaults()`) contains:
`project_name, project_number, location, report_date, report_number, prepared_by, superintendent, weather_summary, weather_snapshots[], schedule_delays, schedule_delays_notes, weather_impact, weather_impact_notes, safety_incidents_today, injuries_reported, incident_notes, safety_notified, safety_contact_person, safety_contact_time, incident_report_filled, incident_report_time, general_notes, masci_crews[], subcontractors[], visitors[], equipment[], materials[], activities[], outbound_materials[], production[], constraints[], photos[], photo_captions[], attachments[] (19.04), distribution_list[], prepared_by_signature, superintendent_signature, narrative_sections{}, excavation_activity_today, linked_excavation_ids[]`.

## API calls made from the frontend

| Call | Purpose |
| --- | --- |
| `GET /api/daily-reports/next-number?date=…` | On mount + date change |
| `GET /api/jobs/{pn}/recent-context` | On job pick — Smart Prefill offer (v19.04) |
| `GET /api/weather-snapshots?date=…&lat=…&lng=…` | Weather refresh button |
| `GET /api/employees` + `GET /api/hr/employee-roster` | Via `EmployeeCombo` (Track 19.03 golden source) |
| `POST /api/daily-reports/attachments/upload` | Attachment upload |
| `POST /api/daily-reports` | Submit |

## Redesign risk summary

* `NewDailyReport.jsx` — 2500+ lines, 11 sections. HIGH risk. Any redesign must preserve every `data` field and its bindings.
* `buildDailyReportDefaults()` — must remain pure. Any drift in field set breaks autosave restoration.
* All `data-testid` identifiers documented in the Control Audit are consumed by tests and testing agent.

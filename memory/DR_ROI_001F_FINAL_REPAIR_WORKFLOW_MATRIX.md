# DR-ROI-001F-FINAL-REPAIR · Workflow Restoration Matrix

For every V1 Daily Job Report data source / gate, this matrix records:
- V1 component / source of truth
- Whether V2 currently uses it
- Data source, validation, autosave/draft, submit impact

| # | V1 Section                    | V1 Component / Source                              | V2 Uses?      | Data Source                                 | Preserved Behavior                                           |
|---|-------------------------------|----------------------------------------------------|---------------|---------------------------------------------|--------------------------------------------------------------|
| 1 | Project / Job                 | `<JobPicker />`                                    | ✅ same        | `GET /api/jobs`                             | Autocomplete + Custom fallback identical to V1               |
| 2 | Report date / shift           | `<Input type="date" />`, native `<select>`         | ✅ same        | supervisor input                            | Native picker · same validation                              |
| 3 | Supervisor / prepared by      | `<Input />`                                        | ✅ same        | supervisor input                            | Plain text field · unchanged                                 |
| 4 | Weather                       | `fetchDailyWeather(date, lat, lng)`                | ✅ same        | Open-Meteo via `lib/weather.js`             | Fetched on click · stored on `draft.weather`                 |
| 5 | GPS                           | `getCurrentPosition()`, `reverseGeocode()`         | ✅ same        | `navigator.geolocation` + `lib/geolocation` | Manual capture · stored on `draft.day_setup.gps`             |
| 6 | Crew / employees              | `<EmployeeCombo />`                                | ✅ same        | HR-gospel employee master                   | Same list; hours flow to payroll pipeline unchanged          |
| 7 | Equipment used                | `<EquipmentCombo />`                               | ✅ same        | `GET /api/equipment-master`                 | Same list; idle/breakdown flags preserved                    |
| 8 | Equipment operator            | `<EmployeeCombo />`                                | ✅ same        | HR-gospel employee master                   | Optional operator per unit · same field                      |
| 9 | Subs / vendors                | `<SupplierCombo />`                                | ✅ same        | `GET /api/suppliers`                        | Wired in Constraint Cards → Subcontractor / Material Delay   |
| 10 | Activity capture             | Structured cards (V2 addition on top of V1 activities) | ✅ new but additive | supervisor input                          | Feeds ODS production facts on submit — pipeline unchanged    |
| 11 | Constraints / Delays         | Structured chip picker + follow-up form            | ✅ new but additive | supervisor input                          | Feeds ODS delay facts — pipeline unchanged                   |
| 12 | Tomorrow / Follow-Up         | `<Textarea />`, `<YesNo />`                        | ✅ same        | supervisor input                            | Same structured schema as V1 Section 10b                     |
| 13 | Safety / Quality             | `<YesNo />`, `<Textarea />`                        | ✅ same        | supervisor input                            | Same YesNo grammar                                           |
| 14 | Excavation / JHA / JHP gate  | `<DailyReportExcavationActivity />`                | ✅ same file   | V1 component verbatim                       | Gate behavior unchanged                                      |
| 15 | Photos                       | `<PhotoUpload />`                                  | ✅ same        | R2 upload pipeline                          | Minimum 6 photos enforced; red countdown until met           |
| 16 | Signature                    | `<SignaturePad />`                                 | ✅ same        | canvas → base64                             | Same signature capture; required for submit                  |
| 17 | Submit                       | Sticky primary button                              | 🟡 disabled in preview | POST `/api/dr-v2/reports/{id}/submit` | Intentionally blocked until Track G cutover                  |
| 18 | Autosave / draft recovery    | `useDrV2Draft(draft)`                              | ✅ same        | PATCH `/api/dr-v2/reports/{id}`             | Debounced autosave; page refresh hydrates from server        |

## New Field-Facing Concept (only one)
| # | Section                       | Purpose                                                                                | User controls                                    |
|---|-------------------------------|----------------------------------------------------------------------------------------|--------------------------------------------------|
| 19 | **Daily Operational Summary** | Platform drafts a professional summary from entered facts + photos.                    | Accept Summary · Edit Summary · Regenerate Summary |

## Not Shown To Supervisor (moved out of field form)
- Confidence / readiness scoreboards — deleted from field form.
- Supervisor approval audit log — deleted from field form (server still
  keeps the append-only log; supervisors only see the current summary).
- Photo detection observation dashboard — deleted from field form.
- Preview / Download PDF buttons — deleted from field form (PDF belongs
  in PM/Admin/Document Center after submit).
- PM / Admin / Executive dashboard content — never rendered here.
- Model / provider / token / cost / agent language — CI-locked forbidden.

## Data-Source Guardrails (CI-locked)
The `test_platform_native_components_wired` assertion greps every
section file for the exact V1 data source it must reference. Any future
PR that swaps a real source for a mock breaks CI immediately.

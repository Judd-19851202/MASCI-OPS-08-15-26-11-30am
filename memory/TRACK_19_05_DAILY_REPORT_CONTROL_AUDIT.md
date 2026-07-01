# Track 19.05 · Daily Report Control / Button / Dropdown Audit

Every interactive control on `/daily/new` (source: `NewDailyReport.jsx` testid + button audit). No changes.

## Global submit + status

| Control | Testid / Selector | Behavior |
| --- | --- | --- |
| Submit (top) | `submit-top-btn` | Calls submit gate, disabled until 6 photos + REQ fields present |
| Submit Daily Report (footer) | text: "SUBMIT DAILY REPORT" / "NEED N PHOTOS TO SUBMIT" | Same handler as top |
| Draft status pill | `daily-report-draft-pill` | Shows "Saved Xs ago" / "Save failed" / "Saving…" |
| Back to Home | `back-link` | Navigates to `/` |
| Language toggle EN/ES | header | i18n switch |

## Draft / autosave / prefill controls

| Control | Testid | Behavior |
| --- | --- | --- |
| Resume draft | `daily-report-draft-restore-prompt` (Restore) | Applies `pendingDraft` to `data` |
| Discard draft | `daily-report-draft-restore-prompt` (Discard) | Soft-deletes to 24 h archive |
| Bring it back | `daily-report-draft-recovery` (Recover) | Restore from 24 h soft-delete |
| Use crew setup | `daily-report-crew-setup-prompt` | Applies device-local Phase 31.1 snapshot with project-change guard |
| Change project (setup) | `daily-report-crew-setup-prompt` (ChangeProject) | Clears project + foreman only, keeps crew |
| Start blank (setup) | `daily-report-crew-setup-prompt` (StartBlank) | Ignores saved setup |
| Clear saved setup | `daily-report-crew-setup-prompt` (Clear) | Removes localStorage snapshot |
| **Smart Prefill Apply** | `daily-report-smart-prefill-apply` | Track 19.04 · applies prior crew+equipment from `/api/jobs/{pn}/recent-context` |
| **Smart Prefill Dismiss** | `daily-report-smart-prefill-dismiss` | Discards the offer for this session |

## Section 01 buttons

* `use-gps-btn` — capture GPS coords into `gps_lat/gps_lng/gps_accuracy`.

## Section 02 buttons

* `refresh-weather-btn` — fetches `weather_snapshots[]`.

## Section 03 controls

* Yes/No radios for `weather_impact`, `schedule_delays`, `safety_incidents_today`, `injuries_reported`, `safety_notified`, `incident_report_filled`.
* `open-incident-form-link` — navigates to `/safety/incident/new` when incident_report_required warning fires.

## Row-based section controls (Sections 04-10 pattern)

| Control | Testid pattern | Behavior |
| --- | --- | --- |
| Add row | `{testIdBase}-add` (e.g. `add-crew-btn`, "Add Crew Member") | Pushes empty row into array |
| Remove row | `{testIdBase}-remove-{i}` (e.g. `crew-remove-{i}`) | Splices array at index |
| Row content inputs | `{testIdBase}-{field}-{i}` | Row-level state updates |
| EmployeeCombo (crew name) | Track 19.03 canonical picker | Sets `name` + `employee_id` linkage |
| EquipmentCombo | equipment description | Sets `description` |
| SupplierCombo | subcontractor company | Sets `company` |

## Photo + attachment controls

| Control | Testid | Behavior |
| --- | --- | --- |
| Photo picker | Native input via `PhotoUpload` | Compresses & appends to `photos[]` |
| Attachment picker | `daily-attachments-picker-input` (Track 19.04) | POSTs to `/api/daily-reports/attachments/upload`, appends metadata to `attachments[]` |
| Attachment remove | `daily-attachments-remove-{idx}` | Splices `attachments[]` |
| Attachment group headers | `daily-attachments-group-{category}` (photo/pdf/spreadsheet) | Display only |

## Signature controls

* SignaturePad `prepared-by-sig` — draws base64 signature onto `prepared_by_signature`.
* Clear button — clears the pad.

## Distribution list controls

* `daily-dist-*` — chip input for up to 20 recipient emails.

## Redesign risk per control

* HIGH · Submit gate + Add/Remove row testids (consumed by tests + testing_agent).
* HIGH · Smart Prefill offer/apply/dismiss testids (Track 19.04 regression).
* HIGH · EmployeeCombo (Track 19.03 canonical roster).
* MEDIUM · GPS / weather refresh (external service calls).
* LOW · Language toggle, help tips.

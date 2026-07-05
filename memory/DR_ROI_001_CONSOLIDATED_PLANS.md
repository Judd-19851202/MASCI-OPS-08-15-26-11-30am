# DR-ROI-001 · Photo Intelligence Plan · UI Flow · Backward Compat · Test Plan · Zero-Drift Matrix · PM KPI · PDF Plan

**Consolidated design brief covering plans 7–13.** Split into sections for clarity.

---

## 1. Photo Intelligence Plan (`DR_ROI_001_PHOTO_INTELLIGENCE_PLAN`)

**Objective:** Turn photos from opaque attachments into structured evidence.

**Pipeline (Track D):**
1. Supervisor uploads photos (existing endpoint; no change to upload flow).
2. Photo Vision Agent (GPT-5.2 Vision, called in ONE batch request per pre-submit) returns:
   - `photo_id`, `tags[]` (equipment types, work types, safety items, materials)
   - `suggested_activity_link` (nearest Activity Card by content match)
   - `flags[]` (safety-critical observation, missing-activity-link)
3. Frontend Photo Intel panel surfaces:
   - Auto-tags with confidence
   - "Link to Activity" suggestion buttons
   - "This photo shows pipe install but no Activity Card exists — Add?" prompt (`ai_questions[]`)
4. Supervisor confirms / edits linking → written to `photo_activity_links[]`.

**Evidence-only role:** Vision output NEVER becomes final narrative directly. It flows back to Operations/Safety/Quality agents as evidence with `evidence_id = "photo:<id>"`.

---

## 2. PM KPI Plan (`DR_ROI_001_PM_KPI_PLAN`)

**Objective:** 22 named KPIs written to `daily_report_kpis` at submit time.

**Hybrid storage (per user Q4 decision):**
- Full report doc = immutable source of truth.
- `daily_report_kpis` collection = normalized, aggregation-friendly analytics layer.
- Extraction happens synchronously at submit (fail-open — if extraction fails, report still submits; KPIs regenerated later via `/api/daily-report-kpis/reindex/{report_id}`).

**KPI list (all 22 required):**
1. `production_by_activity[]` · 2. `production_by_area[]` · 3. `crew_hours_by_activity[]` · 4. `equip_hours_by_activity[]` · 5. `material_loads_in` · 6. `material_loads_out` · 7. `truck_count`
8. `weather_delay_hours` · 9. `equip_delay_hours` · 10. `delay_counts_by_category` (14-enum) · 11. `extra_work_events`
12. `open_pm_actions` · 13. `unresolved_safety_issues` · 14. `unresolved_quality_issues` · 15. `tomorrow_readiness_risks`
16. `photo_compliance` · 17. `ai_confidence_score` · 18. `report_completeness_score`
19. `utility_conflict_count` · 20. `inspection_delay_count` · 21. `material_delay_count` · 22. `subcontractor_issue_count`

**PM Dashboard tiles (Track E):**
- Today's PM Brief · Production Summary · Delay Log · Open PM Actions · Tomorrow Readiness · Safety/Quality Flags · Photo Evidence · KPI trend cards · Extra-work / claim-risk flags

**Regeneration:** Any KPI record can be regenerated from its source report via `POST /api/daily-report-kpis/reindex/{report_id}` (admin-only).

---

## 3. PDF Output Plan (`DR_ROI_001_PDF_OUTPUT_PLAN`) — deferred to Track F per user Q5

**Session decision:** Preserve current PDF pipeline byte-for-byte. Architect V2 PDF here; do not implement.

**V2 PDF sections (planned):**
1. Executive Header (project · date · shift · weather · GPS · supervisor · report #)
2. Today's PM Brief (from `pm_action_items[]` + PM Agent output)
3. Production Summary (from `production_by_activity[]` + `production_by_area[]`)
4. Delay / Constraint Log (from `constraint_cards[]`)
5. Crew Time Summary (from `masci_crews[]`)
6. Equipment Summary (from `equipment[]` + `equip_hours_by_activity[]`)
7. Material / Truck Summary (from `materials[]` + `outbound_materials[]`)
8. Safety / Quality section (from existing gate fields)
9. Approved Operational Narrative (from `final_approved_narrative`)
10. AI Confidence + Source Trace (compact summary from `ai_source_trace{}`)
11. Photo Evidence (thumbnails linked to activity cards)
12. Signature + Audit Metadata (verification QR code)

**Cutover flag:** `PDF_V2_ENABLED=false` in prod until Track F certifies dual-render.

---

## 4. UI Flow (`DR_ROI_001_UI_FLOW`)

**Route:** `/daily-report/v2` (feature-flagged · V1 remains at existing route)

**Progressive shell (10 sections + 4 panels):**
1. Day Setup · 2. Crew Time · 3. Equipment · 4. Activity Cards · 5. Constraint Chips · 6. Tomorrow Readiness · 7. Safety / Quality · 8. Photos · 9. AI Summary · 10. Signature + Submit

**Sticky panels (right rail on desktop; collapsible drawer on tablet/phone):**
- Confidence Panel · PM Intelligence Panel · Photo Intelligence Panel · Supervisor Approval Panel

**Interaction principles:**
- Field-first, narrative-last
- Chip-driven for enums (constraints, tomorrow needs)
- Card-based repeating groups (activities)
- Live validation checklist (visible at all times)
- Sticky "AI questions" tray (max 3 at a time · dismissible with logged reason)

**Target device support:** iPad primary · phone secondary · ToughBook (Windows tablet) tertiary · desktop for PM read-out.

**Time target (per directive):** 5–8 min normal day · structured even on complex day.

---

## 5. Backward Compatibility (`DR_ROI_001_BACKWARD_COMPATIBILITY`)

| Contract | Guarantee | Verified by |
|---|---|---|
| Legacy V1 POST succeeds | `extra="allow"` on `DailyReportCreate` | Existing `test_daily_reports.py` |
| Legacy V1 GET returns full doc | V2 fields default null | Existing tests |
| V2 POST with legacy fields only succeeds | Same schema, same defaults | New lock test (this session) |
| V2 POST with V2 fields succeeds today | Extra keys land as-is in Mongo | New lock test |
| HR crew-time reads unchanged | `masci_crews[]` untouched | HR portal tests |
| Safety gate unchanged | 8 fields untouched | Safety portal tests |
| Excavation gate unchanged | 422 still fires when yes+no-links | Existing `test_daily_reports.py` |
| Photo min 6 unchanged | Enforcement preserved | Existing tests |
| Signature required unchanged | `prepared_by_signature` + `superintendent_signature` unchanged | Existing tests |
| Job Photos mirror unchanged | Only new `photo_ai_tags[]` added later (Track D) | Job Photos tests |
| Audit trail unchanged | Trust-spine events keep firing on existing verbs | Track 15.13h tests |
| CSV export unchanged | V2 fields excluded until opt-in | Existing CSV test |
| PDF unchanged | Track F cutover only | PDF regression |
| Email delivery unchanged | No change to workflow POSTs · strict mode remains | Track 22.1H tests |

---

## 6. Test Plan (`DR_ROI_001_TEST_PLAN`)

### Frontend (this session)
- V2 route mounts at `/daily-report/v2` behind feature flag
- Feature flag default OFF (V1 remains default)
- V2 shell renders all 10 sections + 4 panels
- Activity Card add / edit / delete works client-side
- Constraint Chip open / follow-up works client-side
- Photo min 6 enforced in V2 shell
- Placeholder panels render clean "Coming in Track C/D/E" states
- Zero interference with V1 route

### Backend (this session)
- `test_dr_roi_001a_b_shell.py` lock: docs exist + V2 route exists + V1 untouched + backend runtime parity

### Backend (Track C onward)
- New AI fields accepted via `extra=allow` today
- New AI fields formalized as optional in Track C schema update
- All existing DR tests still pass
- No live email dispatch during AI wiring

### Frontend (Track C onward)
- AI summary preview button triggers agent orchestration
- Supervisor approval blocks submit until acted upon
- AI question tray shows / dismisses
- Confidence panel reflects live scores

### PM KPI (Track E)
- Submit writes `daily_report_kpis` row
- Regeneration endpoint restores KPIs from source report
- PM dashboard tiles consume KPI collection

### PDF (Track F)
- V1 PDF still bytewise identical
- V2 PDF renders correctly with V2 fields
- Cutover flag toggles output

### Regression (Track G)
- Full Track 22.* lock envelope (currently 268/268)
- Existing DR tests: `test_daily_reports.py` + 4 Track 19.* tests
- Playwright: submit V1 report · submit V2 report · HR reads · Safety escalation · Excavation gate
- No live emails
- Testing agent independent verification

---

## 7. Zero-Drift Matrix (`DR_ROI_001_ZERO_DRIFT_MATRIX`) — session-scope

| Layer | Baseline | Post-session | Δ |
|---|---:|---:|---:|
| `NewDailyReport.jsx` line count | 3,021 | 3,021 | 0 |
| `dailyReportSchema.js` line count | 112 | 112 | 0 |
| `DailyReportsDashboard.jsx` line count | 243 | 243 | 0 |
| `backend/routes/daily_reports.py` line count | 665 | 665 | 0 |
| Existing DR tests | pass | pass | 0 |
| Backend routes | 1,441 | 1,441 | 0 |
| Backend Track 22.* lock envelope | 268/268 | 268/268 | 0 |
| Lifecycle complete | true | true | 0 |
| Email safety strict | true | true | 0 |
| Bytecode fingerprints clean | 9/9 | 9/9 | 0 |
| New V2 route mounted | — | `/daily-report/v2` (feature-flagged) | +1 (additive) |
| New V2 shell files | — | scaffolded | +N (additive, isolated) |
| V1 code path | active | active (unchanged) | 0 |

---

## 8. Implementation Report (`DR_ROI_001_IMPLEMENTATION_REPORT`) — this session
See `DR_ROI_001_EXECUTIVE_SUMMARY.md` for the session-closing verdict.

# TRACK 15.62 · Session B Execution Plan
**Handoff document for the next session agent. No code in this session.**

## Mission for Session B

Close Track 15.62 by shipping the operator-facing FE redesign + admin/exec surfaces + production verification + cleanup + certification. Feature flag `DR_RECOVERY_ENABLED` flips from `false` → `true` in production env ONLY after every check below passes.

## Inputs already on disk (no re-work needed)

| Input | Path |
|---|---|
| Approved architecture | `/app/memory/TRACK_15_62_IMPLEMENTATION_ARCHITECTURE.md` |
| Session A delivered backend report | `/app/memory/TRACK_15_62_SESSION_A_REPORT.md` |
| Backend aggregator (already live) | `/app/backend/lib/daily_report_rollup.py` |
| New admin endpoints (already live) | `/app/backend/routes/dr_admin_intel.py` |
| Schema additions (already live) | `narrative_sections`, `photo_captions` in `routes/daily_reports.py:DailyReportCreate` |
| PMCC fixes (already live) | `routes/pm_command_center.py` — K-MM-1, K-HAUL-1, K-AGG-1 |
| PDF render extension (already live) | `pdf_render._render_narrative_sections()` |
| Session A verification harness (8/8 pass) | `/app/tests/post_deploy/track_15_62_session_a_verify.py` |
| 15.61 forensics baseline | `/app/memory/track_15_61_data/forensics.json` |
| Track 15.61 audit harness (regression sentinel) | `/app/tests/post_deploy/track_15_61_audit.py` |

## Files to be created or edited in Session B

### Frontend — new components

| File | LOC est. | Purpose |
|---|---|---|
| `frontend/src/components/NarrativeWorkflow.jsx` | ~180 | Six guided prompts that write to `narrative_sections` |
| `frontend/src/components/OutboundHaulRow.jsx` | ~150 | Canonical material dropdown + EquipmentCombo hauler + Loads/Trips unit + destination |
| `frontend/src/components/CompletenessChip.jsx` | ~80 | Header pill: scores the report against a meaningful rubric, lights green when ≥ 5 of 8 dimensions are populated |
| `frontend/src/lib/dailyReportScore.js` | ~60 | Client-side scorer mirroring `daily_report_rollup.score()` shape |

### Frontend — edited

| File | Edit summary |
|---|---|
| `frontend/src/pages/NewDailyReport.jsx` | Replace narrative block with `<NarrativeWorkflow>`. Replace outbound row inputs with `<OutboundHaulRow>`. Replace `prepared_by` + `superintendent` `<Input>` with `<EmployeeCombo>` (R-IDENTITY). Add `<CompletenessChip>` in header. Add per-photo caption input field to existing `<PhotoUpload>` integration (writes to `photo_captions[i]`). Move `schedule_delays_notes`, `weather_impact_notes`, `linked_excavation_ids` behind a `<Collapsible>` "More details" toggle (R-DEAD-FIELDS). Gate the entire new UX behind `DR_RECOVERY_ENABLED` check returned from `/api/admin/material-vocabulary` response (vocab presence = flag on). Legacy form path preserved for fallback. |
| `frontend/src/pages/admin/AdminCommandCenter.jsx` (or the equivalent admin hub file) | Add new tab "Daily Roll-Up" consuming `GET /api/admin/daily-roll-up?from=&to=`. Tabs: Today · 7d · 30d · 90d · custom window picker. Renders: total loads in/out (big-number tile), per-material bar chart, per-project table, top haulers table. |
| Same admin hub | Add "Daily Report Health" card consuming `GET /api/admin/daily-report-health?days=30`. Renders: completion % donut, blank % badge (color-coded), median word count, story missing %, tomorrow plan missing %. |
| `frontend/src/components/PhotoUpload.jsx` (or wherever the daily report uses it) | Accept `captions` prop + `onCaptionChange` callback so the parent can hold `photo_captions[]` in state |

### Backend — small additions Session B will need

| File | Edit |
|---|---|
| `backend/lib/daily_report_rollup.py` | Add `rollup_window_per_section_health()` for the tighter "tomorrow_plan_missing_pct" / "delays_missing_pct" metric (current implementation returns conservative upper bound). |
| `backend/routes/dr_admin_intel.py` | Tighten `_section_missing_pct()` once the per-section query lands. |
| (Optional) `backend/routes/pm_command_center.py` | If wired: extend `/hauls` rows to include `motive_truck_id` from `asset_mappings` cross-walk (R-MOTIVE UX side). |

### Verification harness

| File | Purpose |
|---|---|
| `/app/tests/post_deploy/track_15_62_session_b_verify.py` | Playwright + API end-to-end harness. Submits a tagged `TRACK_15_62_DELETE` synthetic Daily Report through the new FE, asserts narrative_sections persistence + PDF render + Admin Roll-Up shows the new loads + Health card percentages updated + Six Pillars contract met. Re-runs `track_15_61_audit.py` as the regression sentinel. Idempotent. Exit 0 on full pass. |

## Components to be created — contract summary

### `NarrativeWorkflow`

Props: `value`, `onChange`, `lang`. Writes to `data.narrative_sections` (six-key dict). Each prompt is a labeled `<Textarea>` with a one-line helper hint ("e.g. 'Backfilled 200 LF station 314-322'"). No prompt is mandatory. Auto-saves into the existing `useFormDraft` hook attached to NewDailyReport (already in place since iter440).

### `OutboundHaulRow`

Props: `value`, `onChange`, `onRemove`, `vocab` (loaded once from `/api/admin/material-vocabulary`). Inputs:
- Material → `<Select>` with vocab options + "Other (type below)" free-text fallback
- Quantity → numeric `<Input>`
- Unit → `<Select>` constrained to ["Loads", "Trips", "Tons", "Cubic Yards", "Each"]
- Hauler → `<EquipmentCombo>` (when hauler="Masci" pulls Motive trucks); free-text for third parties
- Destination → `<Input>` with project-scoped recent-destinations memory
- Ticket / Manifest → optional `<Input>`

### `CompletenessChip`

Props: `report`. Scores against the 15.61 8-question rubric (Q1–Q8). Returns `{score, label, color}`. Render = compact pill in header showing "5/8 · Good" with tooltip detail. Updates live on every keystroke (debounced 300ms).

## Verification strategy

### Preview verification (must pass before flag flip)

| Tier | Tool | Expectation |
|---|---|---|
| 1 · API smoke | curl | `/api/admin/material-vocabulary` returns ≥ 14 rows · `/api/admin/daily-roll-up` returns numbers · `/api/admin/daily-report-health` returns metrics |
| 2 · Aggregator regression | curl | Re-run Session A's `track_15_62_session_a_verify.py` — still 8/8 pass |
| 3 · UI smoke | Playwright | `/daily/new` renders new NarrativeWorkflow + OutboundHaulRow + CompletenessChip + EmployeeCombo on preparer/super + per-photo captions + collapsed dead fields |
| 4 · Write workflow | Playwright | Submit a tagged `TRACK_15_62_DELETE` daily report via the new FE. Verify the PDF renders all six narrative sections + photo captions. |
| 5 · Admin surfaces | Playwright | Admin Command Center "Daily Roll-Up" tab renders, shows the loads from the tagged report. Health card shows the latest completion % |
| 6 · Forensics regression | re-run `track_15_61_audit.py` | Activity Log completion % ≥ pre-15.62 baseline (sanity floor) · narrative_sections completion shows ≥ 1 % (proves the new path is reaching DB) |

### Production validation (after preview green + flag flip)

| Tier | Tool | Expectation |
|---|---|---|
| 7 · Production API | curl | All Session A endpoints respond with real numbers from the production DB. PMCC haul rows include DR-sourced rows for at least one active project. |
| 8 · Production UI | Playwright | Hit `https://mascidocs.com/daily/new`, screenshot proves NarrativeWorkflow + OutboundHaulRow + CompletenessChip live. Admin Roll-Up tab loads on `/admin`. |
| 9 · Production PDF | API | `POST /api/email-report` against a real production report renders PDF including narrative section block when present. |
| 10 · Regression sentinel | re-run `track_15_61_audit.py` against production | Activity Log completion % captured as the new operational floor for the 14-day baseline measurement. |

## Production validation strategy

After Session B FE ships and Session A backend lands together in one coordinated deploy:

1. Set `DR_RECOVERY_ENABLED=true` in production env.
2. Run `track_15_62_session_b_verify.py` against `https://mascidocs.com`.
3. Capture screenshots: `/daily/new` (new form) · `/admin` → Daily Roll-Up tab · Admin Health card.
4. Re-run `track_15_61_audit.py` against production immediately post-deploy. Save as `15.62_day_0_baseline.json`.
5. Schedule re-runs at day 7 and day 14 to measure adoption lift.

## Cleanup strategy

| Artefact | Cleanup |
|---|---|
| Synthetic daily reports tagged `TRACK_15_62_DELETE` | DELETE via `/api/daily-reports/{id}` then re-list and verify 0 leftover. |
| Synthetic employee_requests (none expected) | sweep `/api/hr/employee-requests` for tag · expect 0 |
| Email side-effects | restrict to single envelope to `safety@mascigc.com` if PDF proof is needed; tagged `[AUTOMATED · TRACK_15_62_DELETE]` |
| R2 photo blobs | the test report should use 1 small placeholder photo only; backup retention sweep cleans within standard lifecycle |

## Success metrics (per operator directive)

Compare day-0 and day-14 against the 15.61 baseline:

| Metric | 15.61 baseline | Day-0 (immediately post-flag-flip) | Day-14 target | Day-30 stretch |
|---|---|---|---|---|
| Activity Log completion % | 26.0 % | ≥ 26.0 % (no regression) | ≥ 45 % | ≥ 60 % |
| Any-narrative completion % | 53.2 % | ≥ 53.2 % | ≥ 75 % | ≥ 85 % |
| Median word count | 0 | ≥ 0 | ≥ 15 | ≥ 25 |
| Avg word count | 7.0 | ≥ 7.0 | ≥ 30 | ≥ 50 |
| Blank narrative reports % | 46.8 % | ≤ 46.8 % | ≤ 25 % | ≤ 15 % |
| PMCC hauls visibility | 0 rows / broken | DR rows surface | continues | continues |
| Executive endpoint | 404 | live | live | live |
| Photo captions adoption | 0 % | n/a | ≥ 30 % | ≥ 60 % |

If day-14 targets are NOT met, the next agent must investigate UX friction (Track 15.63 likely scope) — but the system itself is structurally correct.

## Definition of Done (per operator directive)

Track 15.62 closes ONLY when ALL of the following hold simultaneously:

1. ✅ Field entry: operator on `mascidocs.com/daily/new` can submit a Daily Report using the new NarrativeWorkflow + OutboundHaulRow + EmployeeCombo + photo captions.
2. ✅ Daily Report: the submitted record persists `narrative_sections`, `outbound_materials` (canonical material), `photo_captions`, `prepared_by_identity`, `superintendent_identity`.
3. ✅ PM Visibility: PM Command Center hauls tab + materials tab + overview show the new submission within the current day window.
4. ✅ Executive Visibility: Admin Command Center "Daily Roll-Up" tab shows the new loads and material aggregation.
5. ✅ Historical Record: the rendered PDF contains the six narrative sections + captioned photos.
6. ✅ Operational Intelligence: the Daily Report Health card moves from the 15.61 baseline.
7. ✅ Verification: Session B harness 100 % pass on both preview and production.
8. ✅ Cleanup: zero `TRACK_15_62_DELETE` artefacts remain.
9. ✅ Flag flipped to `true` in production.
10. ✅ Day-0 production baseline captured and stored.

Only then does the next agent emit the `TRACK_15_62_FINAL_CERTIFICATION.md` + close-out CHANGELOG entry.

## Six Pillars contract for Session B

Powerful 10 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 10 · Deployable 10 → must score ≥ 58/60 for the final close.

## Deliverables expected from Session B

`TRACK_15_62_SESSION_B_REPORT.md` · `TRACK_15_62_HAUL_WORKFLOW.md` · `TRACK_15_62_IDENTITY_RECOVERY.md` · `TRACK_15_62_PHOTO_CAPTIONS.md` · `TRACK_15_62_COMPLETENESS_SCORING.md` · `TRACK_15_62_PM_VISIBILITY_PROOF.md` · `TRACK_15_62_EXEC_VISIBILITY_PROOF.md` · `TRACK_15_62_PRODUCTION_VALIDATION.md` · `TRACK_15_62_CLEANUP_PROOF.md` · `TRACK_15_62_DAY_0_BASELINE.md` · `TRACK_15_62_FINAL_CERTIFICATION.md` · `TRACK_15_62_IMPLEMENTATION_REPORT.md` (updated) · `TRACK_15_62_EXECUTIVE_SUMMARY.md` (updated) · `TRACK_15_62_SIX_PILLAR_CERTIFICATION.md` (updated) · `PRD.md` + `CHANGELOG.md` updated.

## What the next agent should do FIRST

1. Read `TRACK_15_62_IMPLEMENTATION_ARCHITECTURE.md` (approved plan).
2. Read `TRACK_15_62_SESSION_A_REPORT.md` (what backend already exists).
3. Run `python3 /app/tests/post_deploy/track_15_62_session_a_verify.py` to confirm Session A is still green on preview.
4. Begin frontend implementation per the contracts above.
5. Do NOT flip `DR_RECOVERY_ENABLED` until every Definition-of-Done bullet is satisfied.

**Track 15.62 remains OPEN.**
**Feature flag remains OFF.**
**No deployment authorization exists.**

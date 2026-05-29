# ODR MIGRATION PLAN

_Phase V.1 · Operational Daily Record · Architecture Artifact 5 of 5 · 2026-05-29_

Plan for retiring the legacy `daily_reports` collection and the
`NewDailyReport.jsx` / `ViewDailyReport.jsx` / `DailyReportsDashboard.jsx`
/ `HrDailyReports.jsx` surfaces in favour of the unified ODR.

**Governing doctrine**

- Zero data loss — every legacy row remains retrievable for 12 months.
- Zero parallel workflows — by end of cutover, only ODR is writable.
- Zero downtime — migration runs in waves; reads stay live throughout.
- Single source of truth — `daily_reports` is frozen, never updated again.

---

## 1 · Source-of-truth inventory

### 1.1 Legacy artefacts to retire (after cutover)

| Surface | Path | Disposition |
|---|---|---|
| Pydantic model `DailyReportCreate` / `DailyReport` | `backend/routes/daily_reports.py` | retain (read-only) · mark `@deprecated` |
| Collection `daily_reports` | Mongo | **freeze writes** at cutover |
| Route `POST /api/daily-reports` | `daily_reports.py` | return `410 Gone` after cutover with helpful message + redirect |
| Routes `GET /api/daily-reports[/...]` | `daily_reports.py` | retain read-only during 12-month archival window |
| CSV export `/api/daily-reports.csv` | `daily_reports.py` | retain |
| Auto-email cron `schedule_auto_email` | `daily_reports.py` | rewire to ODR before cutover |
| Frontend `NewDailyReport.jsx` | `frontend/src/pages/` | replace with `OdrEntry.jsx` |
| Frontend `ViewDailyReport.jsx` | `frontend/src/pages/` | retain in read-only "archive" mode; replace primary use with `OdrView.jsx` |
| Frontend `DailyReportsDashboard.jsx` | `frontend/src/pages/` | replace with `OdrDashboard.jsx` |
| Frontend `HrDailyReports.jsx` | `frontend/src/pages/` | rewire to read ODR via HR projector |
| Frontend `lib/dailyReportSchema.js` | `frontend/src/lib/` | replace with `lib/odrEnums.js` + `lib/odrValidation.js` |
| `frontend/src/components/daily-report/*` | dir | replace with `components/odr/*` |

### 1.2 New artefacts to create (during cutover)

| Surface | Path |
|---|---|
| New routes package | `backend/routes/odr/` (init, model, routes, projectors, pdf) |
| New collection | `odr` |
| New collection (registry) | `odr_photos` |
| New collection (telemetry) | `odr_section_events` |
| New frontend surfaces | `frontend/src/pages/OdrEntry.jsx` · `OdrView.jsx` · `OdrDashboard.jsx` |
| New frontend lib | `frontend/src/lib/odrEnums.js` · `lib/odrValidation.js` |
| New component library | `frontend/src/components/odr/*` (Section1-16 partials, photo tagger, readiness, etc.) |
| Migration script | `scripts/migrate_daily_reports_to_odr.py` (idempotent, dry-run capable) |
| Doctrine probe | `scripts/odr_doctrine_probe.py` (mirrors `operational_links_doctrine_probe.py`) |

---

## 2 · Field-level mapping (`DailyReport` → `ODR`)

| Legacy field | ODR field | Notes |
|---|---|---|
| `project_name` · `project_number` · `location` | `project.project_name` / `project_number` / synthesized from `jobs_master.lat_long` | denormalized |
| `report_date` | `project.report_date` | unchanged |
| `report_number` (`DR-YYYY-NNNNN`) | new `doc_id` (`ODR-YYYY-NNNNN`) + `legacy_daily_report_id = id` | per-year sequence restart at 1 for ODR; legacy chain preserved |
| `prepared_by` | `project.foreman_name`; UID resolved from `user_directory` lookup | fuzzy match · review needed for ambiguous |
| `superintendent` | `project.superintendent_name` / UID lookup | as above |
| `weather_summary` · `weather_snapshots[]` | `project.weather` (latest snapshot) + new `weather_pulled_at_utc` | strict parse · unparseable strings stored on `migration_notes` |
| `schedule_delays` (Yes/No) + `schedule_delays_notes` | `delays.any_delays` + `delays.entries[0].description` with `delay_type="other"` | conservative: closed-set type unknown for legacy rows |
| `weather_impact` + `weather_impact_notes` | `weather_impact.weather_impacted_work` + `.description` | direct map |
| `safety_incidents_today` + `injuries_reported` + `incident_notes` | `safety.incident` / `safety.injury` + `incident_report_link_id` (best-effort lookup in `safety_incidents` by date+project) | manual review for unmatched |
| `safety_notified` · `safety_contact_person` · `safety_contact_time` | `safety.safety_notified` · `contact_name` · `contact_time_utc` | direct |
| `incident_report_filled` · `incident_report_time` | `safety.incident_report_complete` + telemetry | direct |
| `general_notes` | `tomorrow.planned_work` if it talks about tomorrow; else `delays.entries[].description` heuristic | heuristic — flagged for PM review post-migration |
| `masci_crews[]` | `manpower.rows[]` + (one row per crew member) | crew rosters were nested arrays of `{name, role, hours}` — flattened |
| `subcontractors[]` | `subcontractors.entries[]` | direct |
| `visitors[]` | (deprecated — captured under `subcontractors` with `kind=visitor`) | doctrine decision |
| `equipment[]` | `equipment.rows[]` | hours/idle/down inferred where present, else null |
| `materials[]` | `production.<polymorphic>.materials[]` or top-level `production.other.materials` if shape ambiguous | conservative |
| `activities[]` | `production.<polymorphic>.runs[]` if pipe/paving shape detected; else `production.other.notes` | heuristic |
| `photos[]` | `odr_photos` rows + `photos` array of `PhotoRef` | tag defaults to `general`; reviewer can re-tag |
| `prepared_by_signature` · `superintendent_signature` | `review.status_history[]` synthetic entries with `actor_role=foreman/superintendent` | |
| `distribution_list` | preserved on the original row only · not migrated to ODR (one-time emails) | |
| `id` · `created_at` · `doc_id` | `legacy_daily_report_id` · `migration_notes.created_at_legacy` | end-to-end traceability |

**Crew Type (Section 2)** — legacy daily reports do not carry
`crew_type`. The migration script writes `crew_type = "other"` for
every legacy row and flags it as `requires_manual_review = True`. PMs
will need to back-fill the crew type during the 30-day post-cutover
window; the dashboard surfaces the queue.

---

## 3 · Cutover sequence (waves)

### Wave M0 — Read-only window opens (week 0)

- Deploy ODR routes, projectors, and frontend in **dual-write** mode:
  - `POST /api/daily-reports` continues to write to `daily_reports`.
  - `POST /api/odr` writes to `odr`.
  - Both surfaces visible to operators — but ODR is marked "BETA — Foremen Preview" and only enabled for a hand-picked group of foremen behind a feature flag (`?odr=1`).
- Frontend: keep `/daily-reports/new` live; expose `/odr/new` for the pilot group.
- Doctrine probes activated (`odr_doctrine_probe.py`).
- No data migration yet.

**Exit gate**: 7 days of green probe runs · 0 console errors on `/odr/new` · 100% of pilot foremen successfully submitting ODRs.

### Wave M1 — Backfill migration (week 1 night-batch)

- Run `scripts/migrate_daily_reports_to_odr.py --dry-run --limit 100` first.
- Operator review of the dry-run report (counts · ambiguity flags · field-loss tally).
- Operator approval → `--live` migration runs nightly:
  - 1 night: project 43-217 (pilot project · ~ 200 rows)
  - 2 nights later: top 10 projects by row count
  - 1 week later: tail
- Each night writes:
  - `odr` row with `legacy_daily_report_id` populated.
  - `daily_reports.{id}.migrated_to_odr_id` written back (sole write to legacy collection during migration; preserves bidirectional link).
  - One row to `odr_section_events` per migration event.
- After each night, `/api/admin/odr/migration-status` returns counts.

**Safety rail**: legacy rows remain unchanged except for the
`migrated_to_odr_id` reference. The migration is reversible at any
point by deleting the new `odr` rows.

### Wave M2 — All foremen on ODR (week 2)

- Default route flips: `/daily-reports/new` redirects to `/odr/new`.
- `POST /api/daily-reports` begins returning `410 Gone` with the
  message:
  > "Daily Reports have been retired. Please use the Operational Daily Record at /odr/new."
- Existing in-flight drafts on the legacy form are migrated automatically on next save attempt (the legacy frontend prompts the user to "convert and continue").

**Exit gate**: 14 consecutive days of 100% ODR adoption · zero new
`daily_reports` rows · all projector consumers green.

### Wave M3 — Read surfaces re-platformed (weeks 3–4)

- Old read surfaces (`DailyReportsDashboard.jsx`, `HrDailyReports.jsx`,
  `ViewDailyReport.jsx`) gain a banner: "Now reading from ODR archive".
- New read surfaces (`OdrDashboard.jsx`, `OdrView.jsx`) become primary.
- Legacy read surfaces remain accessible at `/legacy/daily-reports/*`
  for 12 months.

### Wave M4 — Cleanup (month 3)

- Delete the deprecated frontend files (`NewDailyReport.jsx`,
  `DailyReportsDashboard.jsx`).
- Mark `daily_reports.py` `@deprecated` in route docstring; retain
  routes for archive reads.
- Probe `pre_deploy_check.sh` warns if any frontend or backend code
  newly imports the deprecated module.

### Wave M5 — Sunset (month 12)

- Operator-approved CSV export of full `daily_reports` collection
  to cold storage (R2 `archive/daily_reports/`).
- Remove `daily_reports` routes from `server.py`.
- Drop the `daily_reports` collection (after final R2 archive verified by `restore_drill.py`).
- Annotate `DEPLOYMENT_HISTORY.json` with the sunset stanza.

---

## 4 · Migration script outline (`migrate_daily_reports_to_odr.py`)

```python
"""
Idempotent, dry-run-capable migration from daily_reports → odr.

Safety rails:
  - --dry-run prints a summary report; writes nothing.
  - --limit N processes only the N oldest unmigrated rows.
  - --project P restricts to one project_number.
  - --since DATE / --until DATE for date-bounded runs.
  - Refuses to write when DB_NAME != "masci_safety_preview" UNLESS
    --i-know-what-i-am-doing is passed.
  - Refuses to overwrite an existing ODR row with the same
    legacy_daily_report_id.

Output:
  - JSON report at /app/memory/odr_migration_<run_id>.json
  - One row per processed legacy row (status, ambiguities, decisions)
  - Append entry to /app/memory/ODR_MIGRATION_TRENDLINE.json
"""
```

The trendline file is integrity-anchored by the same
`trendline_integrity_probe.py` introduced in Wave 1.1B — so the
migration's append-only history cannot be silently truncated.

---

## 5 · Risk register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | Field mapping ambiguity (legacy general_notes → ODR structured fields) | medium | flag for manual review · PM workspace queue surfaces ambiguous rows |
| R2 | Photo references → R2 paths break during migration | medium | migration script verifies each R2 key exists; missing keys logged but not failed |
| R3 | Crew type unknown for legacy rows | low | default `other` + queue for PM back-fill within 30 days |
| R4 | Safety incident link-ups (incident_notes → incident_report_link_id) cannot be guaranteed | medium | best-effort lookup by date+project; ambiguous matches require manual confirmation |
| R5 | PM/Super UID lookup fails for legacy free-text names | low | unresolved rows flagged with `pm_uid=null` + `migration_notes` |
| R6 | Foremen resist switching to ODR | medium | pilot wave M0 + 30-day side-by-side · adoption telemetry surfaced to PMs |
| R7 | Projectors (Shop/HR/Safety/etc.) misclassify legacy rows | medium | run projectors with `provisional=True` on migrated rows; require PM-approval to confirm |
| R8 | Wave 1 substrate collections (operational_constraints) get noisy from legacy back-fills | medium | migration writes constraints with `source=migration` · separate filter on Memory views |
| R9 | Storage growth on dual-write | low | `odr` doc size budgeted ~ 12 KB / day / crew · 1 GB / year at 50 active crews |
| R10 | Audit-trail break between legacy and new | high | every ODR row carries `legacy_daily_report_id` + every legacy row carries `migrated_to_odr_id` |

---

## 6 · Acceptance criteria

The migration is **complete** when:

- [ ] 100% of `daily_reports` rows have a non-null `migrated_to_odr_id`.
- [ ] 100% of new field-day reporting traffic writes to `odr`.
- [ ] `POST /api/daily-reports` returns `410 Gone` in production.
- [ ] All eight downstream consumers (PM/Safety/Dispatch/Shop/HR/Exec/Memory/Search) read ODR data exclusively for new days.
- [ ] `odr_doctrine_probe.py` and `trendline_integrity_probe.py` both green for 30 consecutive days.
- [ ] CSV export at `/api/daily-reports.csv` still works against archive.
- [ ] Zero open rows in the "ambiguous mapping" queue (i.e., every R1–R5 flag resolved).
- [ ] `DEPLOYMENT_HISTORY.json` carries the cutover stanza.

---

## 7 · Rollback plan

The cutover is **fully reversible** at any wave through M3:

| Wave | Rollback step |
|---|---|
| M0 | Disable `?odr=1` flag · disable `POST /api/odr` writes |
| M1 | Delete `odr` rows where `legacy_daily_report_id is not null`; clear `daily_reports.migrated_to_odr_id` |
| M2 | Re-enable `POST /api/daily-reports`; revert `/odr/new` → `/daily-reports/new` redirect |
| M3 | Revert read surfaces; legacy reads were never offline |
| M4–M5 | Not reversible (cleanup completed; needs full restore drill) |

Until M3 inclusive, the legacy system stays available as a hot
fallback. The doctrine: every step must be safe to walk back from.

---

## 8 · Telemetry during migration

A new admin surface `/admin/odr/migration` shows:

- Rows migrated · rows pending · rows flagged for review
- Per-project · per-day completeness heatmap
- Per-consumer projector lag (Safety should be 0)
- Foreman adoption rate (ODRs / day / foreman vs legacy DR submission rate)
- Ambiguity queue size + average resolution time

All metrics are read-side; this dashboard does not mutate data.

---

## 9 · Open migration questions for operator review

1. Should the dual-write window (M0) be 7 days, or longer to allow
   more pilot foremen? (Default: 7 days · expand to 14 if pilot
   adoption < 80%.)
2. Should we backfill `crew_type` for every legacy row before
   cutover, or accept the post-cutover queue? (Default: post-cutover
   queue · faster cutover.)
3. Should `visitors[]` from legacy be migrated as a separate
   `visitors` block on ODR, or merged into `subcontractors`?
   (Default: merged with `kind=visitor`.)
4. Should the 12-month archive read window be hardcoded, or
   operator-configurable? (Default: operator-configurable in
   `admin_digest_config.py` — same pattern as other retention knobs.)
5. Should the migration also re-render legacy PDFs into the new ODR
   PDF format for the archive, or leave legacy PDFs alone? (Default:
   leave legacy PDFs alone; on-demand re-render at `/legacy/daily-reports/{id}/pdf?asOdr=1`.)

Awaiting operator decisions before implementation.

---

_Artifact 5 of 5 · STOP CONDITION REACHED · architecture review awaited._

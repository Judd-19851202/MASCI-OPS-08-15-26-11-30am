# TRACK 19.41 · Transportation Intelligence Readiness

**Status:** 🟡 CONTRACT-REGISTERED (Track 19.40) · READY FOR IMPLEMENTATION (Track 19.42 or 19.43).

Product ID: `transportation_intelligence`.

## Contract (locked in Track 19.40)

| Field | Value |
|---|---|
| `product_id` | `transportation_intelligence` |
| `display_name` | Transportation Intelligence Digest |
| `permission_role` | `safety_or_admin` |
| `template_key` | `executive_v1` |
| `schedule_freq` | `weekly` |
| `schedule_iso_day` | 1 (Monday) |
| `schedule_hour_utc` | 13 |
| `status` | `CONTRACT_REGISTERED` |
| `aggregator` | `_not_implemented` (raises `NotImplementedError`) |
| Recommended recipient groups | `transportation`, `safety` |

## Recommended recipient groups

- Transportation Admin
- Dispatch Leadership
- Safety
- Executive Leadership (summary tier — cc)

## Data sources to consume

| Source | Collection / Endpoint | Coverage today | Gaps |
|---|---|---|---|
| **DVIR** | `db.dvir` (Track 19.12 modernization) · `db.equipment_inspections` | ✅ Present · daily submissions live | Aggregation by driver/unit for weekly rollup not pre-computed |
| **Driver Qualification** | `db.driver_qualifications` · `db.driver_history` (Track 19.00 audit) | ✅ Present · full lifecycle stamped | Need expiring-cert projection for the week |
| **Transportation Portal** | `/api/transportation-portal/*` routes | ✅ Present | No digest-shaped endpoint |
| **Fleet records** | `db.fleet_units` · `db.equipment_master` (Track 19.02 fleet projection) | ✅ Present · state machine live | Need OOS-count by category |
| **Dispatch** | `db.dispatch_events` · `db.dispatch_assignments` | ✅ Present · today+tomorrow scoped | Need weekly summary aggregation |
| **Vehicle assignments** | `db.vehicle_assignments` · `db.driver_assignments` | ✅ Present | Need unassigned-vehicle count |
| **Motive integration** | Motive event feed (Track 15.63 · MOTIVE_EVENT_INTELLIGENCE_MATRIX_AUDIT.md) | ✅ Present · 7-day live validated | Need de-duped violation summary |
| **Incident vehicle accidents** | `db.incident_cases` filtered by `incident_type="vehicle_accident"` | ✅ Present · Track 19.38 aggregator applies | Reuse `_rows_for_cases` |
| **Equipment / Vehicle OOS** | `db.equipment_units` where `status IN ("OOS", "Down")` | ✅ Present | Need aging (days-in-OOS) |
| **Driver issues** | `db.driver_events` · `db.hr_records` cross-lookup | ✅ Partial | Explicit "driver watchlist" projection needed |
| **Open defects** | `db.equipment_defects` · Track 15.63 defect explorer | ✅ Present | Need trend vs previous week |

## Metric semantics

| Metric | ▲ Direction | Ownership |
|---|---|---|
| OOS unit count | Bad | Fleet |
| Overdue DVIR follow-ups | Bad | Safety |
| Expiring driver certs (30d window) | Bad | Safety + HR |
| Unassigned vehicles | Bad | Dispatch |
| Motive violation count | Bad | Safety |
| Vehicle accidents this period | Bad | Safety |
| DVIR completion % | Good | Safety |
| Driver qualification currency % | Good | HR + Safety |
| Fleet availability % | Good | Fleet |

## Score contributors (proposed)

**Positive**
- `dvir_completion_over_95` — DVIR compliance ≥ 95%
- `fleet_availability_high` — Fleet availability ≥ 90%
- `no_vehicle_accidents` — Zero recordable vehicle incidents this week
- `driver_qualification_current` — 100% of active drivers current

**Negative**
- `oos_units` — Weighted by aging bucket (0–7d · 7–30d · >30d)
- `overdue_dvir_followups` — Blocking outstanding actions
- `expiring_certs_next_30d` — Count of certs expiring in the next 30 days
- `unassigned_vehicles` — Vehicles without a current assignment
- `motive_violations_high_severity` — High-severity Motive events this week
- `vehicle_accidents_this_week` — Any vehicle accident in the period

## Standard layout section mapping

| Section | Transportation Intelligence content |
|---|---|
| Executive Summary | Total active units · OOS · Assigned · Drivers current · DVIR completion % |
| Score | Composite from contributors above |
| Trend Direction | Week-over-week change in OOS + DVIR completion |
| Top Wins | e.g. "Zero recordable vehicle incidents" |
| Needs Immediate Attention | Units OOS >30d · Overdue driver certs |
| Top 5 Items | Top 5 OOS units by age, or top 5 drivers by open defects |
| Core Metrics | KPIs above |
| Trend Table | 4-week OOS · DVIR completion · Fleet availability |
| Recommendations | Actionable follow-ups (return OOS units · renew certs) |
| Upcoming Risks | Certs expiring in the next 14 days |
| Recent Changes | Newly-OOS units · newly-assigned drivers · closed defects |
| Deep Links | `/admin/transportation/command-queue`, `/fleet`, `/hr/training-records`, `/safety/incidents?type=vehicle_accident` |
| No-Auto-Decision Notice | Verbatim doctrine — Safety + Fleet + Transportation own classification |
| Audit Footer | Product · period · generated at |

## Existing digest to consolidate

**Transportation Command Digest** (Track 16.10A · `backend/lib/transport_command_digest.py`).

Coverage: dispatch command queue · document center · inspections · orientation · email pilot panel.

Migration plan for Track 19.42 / 19.43:

1. Wrap `build_transport_command_digest(...)` inside `_agg_transportation_intelligence` (analogous to how Track 19.41 wraps `send_po_digest_once`).
2. Keep `transport_command_digest_scheduler_loop` running until the engine-composed layout is operator-accepted.
3. After acceptance, set `TRANSPORT_COMMAND_DIGEST_ENABLED=false` and let the engine become the sole Transportation sender.
4. Add operator-facing `/api/operational-intelligence/transportation_intelligence/preview` endpoint (already available via Track 19.40 preview route once aggregator lands).

## Implementation checklist (Track 19.42 or 19.43)

- [ ] Write `_agg_transportation_intelligence(db, **kwargs) -> dict`.
- [ ] Compose via `build_standard_layout(...)`.
- [ ] Use `compute_trend` for OOS · DVIR completion · Fleet availability.
- [ ] Emit an `OperationalIntelligenceScore` with 4+ contributors.
- [ ] Reuse `list_recipients_for(db, product_id="transportation_intelligence")` — do not hardcode.
- [ ] Add lock test `test_track_19_42_transportation_intelligence.py`.
- [ ] Regression: Track 19.34 – 19.41 locks green.
- [ ] Update PRD.md + CHANGELOG.md.
- [ ] Write `TRACK_19_42_TRANSPORTATION_INTELLIGENCE.md` + `..._QUALITY_GATE_CLOSEOUT.md` + `..._ZERO_DRIFT_MATRIX.md`.

## What is deliberately out of scope for Track 19.41

- Implementing the aggregator.
- Registering the recommended recipient groups (admins do this manually via the recipient engine or in a follow-up seed script).
- Migrating the legacy `transport_command_digest_scheduler_loop`.

Foundation stands ready. Aggregator can ship in isolation without touching the engine again.

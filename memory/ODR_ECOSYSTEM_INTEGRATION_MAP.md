# ODR ECOSYSTEM INTEGRATION MAP

_Phase V.1 · Operational Daily Record · Architecture Artifact 3 of 5 · 2026-05-29_

The ODR is the **single field-day data source**. Eight downstream
consumers read its data through **per-consumer projector views**;
no consumer mutates the ODR directly. This artifact catalogues
every data slice, where it lands, and the contract that governs it.

---

## 1 · Architecture pattern · projector / consumer

```
                       ┌─────────────────────┐
                       │   ODR (Mongo)       │
                       │   ──────────────    │
   foreman ──submit──▶ │  one document       │
                       │  per crew/day/proj  │
                       └──────────┬──────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
                  ▼                               ▼
        ┌──────────────────┐         ┌─────────────────────┐
        │  ODR Projector   │         │  Append-only events │
        │   (per-consumer) │         │  odr_section_events │
        └────────┬─────────┘         └─────────────────────┘
                 │
   ┌───┬────┬────┴────┬────┬────┬──────────┬──────────────┐
   ▼   ▼    ▼         ▼    ▼    ▼          ▼              ▼
   PM  Safety  Dispatch Shop  HR  Executive Memory     Search/RFI/
                                  Center    (Wave 1+) Schedule/Claims
```

**Contract**

- **Write boundary**: only the ODR API (`/api/odr/*`) writes to the
  `odr` collection. Consumers may write *their own* records (e.g.,
  a Shop ticket) but must store `source.kind = "odr"` +
  `source.id = odr_id` for traceability.
- **Read boundary**: each consumer uses a single dedicated projector
  function. Projectors live in `backend/routes/odr/projectors/`.
- **Idempotency**: every projector run is `(odr_id, projector_kind)`-
  keyed. Re-running on an unchanged ODR produces zero side effects.
- **Telemetry**: every projector run writes one row to
  `odr_section_events` (`event="projector_dispatched"`).

---

## 2 · Per-consumer integration

### 2.1 PM consumer

| ODR slice consumed | PM surface |
|---|---|
| `production.*` (polymorphic) | PM project detail · production rollup |
| `delays.entries[]` · `delays.total_hours_lost` | PM project detail · delay panel + Operational Timeline sidecar |
| `constraints.entries[]` | PM constraints panel · feeds `operational_constraints` (Wave 1) |
| `extra_work.entries[]` | PM extra-work tracker · feeds future RFI / change-order |
| `plan_vs_actual` | PM look-ahead variance |
| `tomorrow.planned_work` | PM look-ahead panel |
| `review` | PM Review queue (Phase 2) |

Projector emits: `pm_project_rollup` view rows + zero direct writes.

### 2.2 Safety consumer

| ODR slice consumed | Safety surface |
|---|---|
| `safety.accident · incident · near_miss · property_damage · environmental_release · injury` (any True) | Safety incident queue (auto-link via `incident_report_link_id`) |
| `safety.contact_*` · `safety.incident_report_complete` | Safety audit trail |
| `photos[]` where `tag in {safety}` | Safety evidence drawer |
| `weather_impact` (when correlating environmental release) | Safety incident context |

**Hard contract**: when `safety.any_event = True` and the ODR is in
`submitted` state, the Safety projector MUST find a non-null
`incident_report_link_id`. If it doesn't, the ODR submission was
not allowed to proceed (see § 10 hard-stop). No duplicate incident
entry — Safety reads from the same row the ODR points to.

### 2.3 Dispatch consumer

| ODR slice consumed | Dispatch surface |
|---|---|
| `equipment[].equipment_id · hours · idle · down` | Dispatch board · equipment utilization summary |
| `equipment[].maintenance_issue` (severity ≥ warn) | Dispatch board · "equipment needs attention" lane |
| `manpower.rows[].missing_personnel_flag` | Dispatch board · "personnel gaps" lane |
| `tomorrow.required_resources` | Dispatch board · tomorrow's resource asks |
| `subcontractors[].deliveries` | Dispatch board · today's deliveries |

### 2.4 Shop consumer

| ODR slice consumed | Shop surface |
|---|---|
| `equipment[].maintenance_issue` (any severity) | Shop ticket queue (auto-created with `source.kind="odr"`) |
| `equipment[].down_hours > 0` | Shop downtime rollup |
| `equipment[].photos[]` of `tag = equipment` | Shop ticket attachments |

**Auto-ticket rule**: every `maintenance_issue` with `severity in {warn, critical}` deterministically creates exactly one Shop ticket; the ticket id is written back to `equipment[].maintenance_issue.auto_shop_ticket_id` so the ODR can show "Shop has it".

### 2.5 HR consumer

| ODR slice consumed | HR surface |
|---|---|
| `manpower.rows[].employee_uid · hours · overtime_hours` | HR payroll variance comparator |
| `manpower.rows[].present · absent_reason` | HR attendance ledger |
| `manpower.rows[].missing_personnel_flag` | HR attendance follow-up queue |
| `manpower.rows[].classification` vs employee master craft | HR training-deficiency detector |

HR never duplicates roster entry — ODR's payroll-grade hours become
the authoritative record after PM Review approval.

### 2.6 Executive consumer

| ODR slice consumed | Executive surface |
|---|---|
| `production.*` (rolled up by crew_type, project, period) | Executive productivity dashboard |
| `delays.*` rollup | Executive delay-trends dashboard |
| `extra_work.*` rollup (cost + schedule) | Executive **claims indicators** dashboard |
| `equipment[].utilization_pct` rollup | Executive equipment utilization view |
| `plan_vs_actual.completed_planned_work` rate | Executive execution-rate KPI |
| `constraints.entries[]` recurrence | Executive constraint trends |

Calmness doctrine applies — executive views use the same single-red,
text-first vocabulary, not enterprise dashboard chrome.

### 2.7 Operational Memory consumer (V-Prelude Wave 1 successor)

| ODR slice consumed | Memory surface |
|---|---|
| `constraints.entries[]` (recurring) | `operational_constraints` rows (Wave 1 substrate) |
| `delays.entries[]` (recurring patterns) | Memory · delay-pattern detector |
| `production.*` (per crew_type per project segment) | Memory · production-rate baselines |
| `extra_work.entries[]` (per requested_by_org per project) | Memory · external-driver pattern detector |
| `plan_vs_actual.variance_reason` (recurring) | Memory · variance-reason pattern detector |

Wave 1 already laid the operational_links / operational_constraints
/ operational_timeline / photo_governance substrates. The ODR is
where those rows are now **born**. Memory becomes the read-side.

### 2.8 Search / RFI / Schedule / Claims / future AI (planned consumers)

| ODR slice consumed | Future surface |
|---|---|
| Full-text indexable fields (descriptions · notes · captions) | Operational Search (V-Prelude Wave 2) |
| `extra_work.entries[]` + photos | RFI seed (V.1.1+) |
| `production.*` per station limits | Schedule / P6 correlation (V.3+) |
| `delays · extra_work · constraints` per project lifetime | Claims package generator |
| All slices · transcripts · photo captions | AI assistant retrieval index |

These consumers do not yet exist; the projector pattern reserves
their seats so they can plug in without re-architecting the ODR.

---

## 3 · Read-time projection contract

Every projector function has the same signature:

```python
def project_odr_for_<consumer>(
    odr: ODR,
    db: Database,
) -> ProjectionResult:
    ...
```

`ProjectionResult` carries:

- `rows`: list of records to upsert into the consumer's read-view collection.
- `tickets`: list of consumer-side side-effect records (e.g., Shop tickets, Safety links).
- `telemetry`: list of audit rows for `odr_section_events`.
- `coaching`: list of operator-facing nudges (surfaced in readiness § 15).

**Pure**: no network, no time, no random. All inputs are the ODR
document + the database snapshot at call time. Re-running a projector
is safe.

---

## 4 · Dispatch ordering

When an ODR transitions `draft → submitted`, the dispatcher runs
projectors in this strict order (each one idempotent):

1. **Safety** — must succeed before any other projector runs.
2. **Memory** — writes constraint/delay/variance lineage.
3. **Shop** — creates equipment tickets.
4. **Dispatch** — refreshes the board.
5. **HR** — updates attendance + variance.
6. **PM** — refreshes project rollup.
7. **Executive** — incremental dashboard refresh.
8. **Search / RFI / Schedule / Claims / AI** — index updates.

If Safety fails, the whole transition is rolled back to `draft` and
the foreman sees the failure on the readiness screen. All other
projectors are best-effort with retry; failures are logged to
`odr_section_events` and surfaced to admin.

---

## 5 · Anti-patterns explicitly forbidden

| Anti-pattern | Why forbidden |
|---|---|
| Allowing Safety, Shop, HR, Dispatch, or PM portals to mutate fields *on* the ODR | Breaks single-source. Each portal owns *its own* derived records, never the ODR row itself. |
| Storing rolled-up totals inside the ODR (e.g., a 7-day production sum) | The ODR is a day. Rollups live in consumer views. |
| Letting two projectors create the same Shop ticket | Idempotency violation. The projector pattern keys on `(odr_id, equipment[i].equipment_id)`. |
| Backfilling weather after submit | TRUST-TIME doctrine. Weather is the snapshot at time-of-record. |
| Duplicating Safety event entry | The ODR's `incident_report_link_id` is the only entry point. |

---

## 6 · Telemetry contract

Per submission, the dispatcher writes:

```
odr_section_events  ←  one row per projector run
   { odr_id, projector, started_at, finished_at, ok, error?,
     rows_written, tickets_created, telemetry_rows }
```

Append-only. Subject to the same `trendline_integrity_probe.py`
posture as the Wave 1 ledgers (Wave 1.1B governance memory
self-protection).

---

## 7 · Open ecosystem questions for operator review

1. Should Executive views read directly from the ODR projector
   tables, or through an additional rollup layer (precomputed
   weekly / monthly aggregates)? (Default: precomputed rollups,
   refresh nightly + on-submit incremental.)
2. Should the Safety projector hard-block the ODR submit if the
   linked incident is in `draft` status? (Default: yes — incident
   must be at least `submitted`.)
3. Should the Shop auto-ticket carry a "Shop has seen this" flag
   back into the ODR equipment row, or just the ticket id? (Default:
   both — ticket id + a soft "acknowledged_at" timestamp.)
4. Should HR be able to "lock" a manpower row after payroll runs?
   (Default: yes — once payroll is locked, the ODR shows the row
   read-only with a "locked by HR" attribution.)
5. Should the Memory projector emit constraint rows on every
   submission, or only on PM-approved submissions? (Default: emit
   on submission, mark `provisional=True` until PM-approved, then
   flip to `provisional=False`.)

Awaiting operator decisions before implementation.

---

_Artifact 3 of 5 · proceed to ODR_PDF_LAYOUT_DESIGN.md_

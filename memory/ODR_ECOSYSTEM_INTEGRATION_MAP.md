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

---

# Delta Integration Addendum (D1–D8) · 2026-05-29

This addendum revises the ecosystem map to reflect D1–D8. Consumer
contracts here **supersede** the original where they differ. The
single-entry / multi-consumer doctrine (O6) is preserved end-to-end.

## E1 · Bilingual canonical-read contract (D6)

**Every consumer reads `LocalizedString.text` (English canonical) only.**
No consumer reads `.original` (the Spanish-as-entered text).

| Consumer | Reads `.text`? | Reads `.original`? |
|---|---|---|
| PM | ✅ | ❌ |
| Safety | ✅ | ❌ |
| Dispatch | ✅ | ❌ |
| Shop | ✅ | ❌ |
| HR | ✅ | ❌ |
| Executive | ✅ | ❌ |
| Operational Memory | ✅ | ❌ |
| Search · RFI · Schedule · Claims · AI | ✅ | only AI retrieval may opt-in for bilingual training corpus, with explicit `odr_translation_events` audit; default ❌ |

**PDF rendering also reads `.text` only** — guarantees English-only PDF.

## E2 · Per-segment projector contracts (D1)

Projectors that previously consumed `production.*` now iterate
`production_segments[]`:

| Consumer | Per-segment behaviour |
|---|---|
| PM | Aggregates production across all segments for the day; respects each segment's `work_area_id` |
| Memory | Production-rate baselines now keyed by `(crew_type, work_area_id, primary_operation)` triple |
| Executive | Productivity dashboards roll up segments per day per project per crew_type |
| Schedule (P6) | Each segment correlates separately by station limits |
| Search · AI | Index per segment; segment_id surfaces in search results |

**Idempotency key** changes from `(odr_id, projector_kind)` to
`(odr_id, projector_kind, segment_id?)` where segment_id is included
for projectors that emit per-segment rows.

## E3 · Work-area aware reads (D2)

Every consumer that reads event-bearing entries now respects
`work_area_id`:

- **PM project rollup** carries per-work-area drill-down.
- **Memory** detects recurring constraints / delays per work_area —
  "this corner of the project repeatedly has utility conflicts".
- **Claims package** groups events by work_area for spatial defence.
- **Executive** can filter productivity per work_area.

Projector output schema gains a `work_area_id: Optional[str]` column
on event-derived rows.

## E4 · Materials projector (D3)

New projection fan-out for the `materials[]` block:

| Consumer | Consumes from `materials[]` |
|---|---|
| PM | Delivery + consumption rollup per project |
| Memory | Vendor-reliability patterns · recurring shortages |
| Executive | Material cost-burn rate · waste-rate KPI |
| Shop | `kind=rejected` or `issue=damage` items surface for inspection |
| Claims | Shortages / rejects / damages with photos = claims evidence |
| Search · AI | Indexed by material_code · vendor · ticket_numbers |

No new consumer surface for Dispatch, HR, or Safety on materials.

## E5 · Reliability projector contract (D4)

The reliability block is **not** projected to operational consumers.
It feeds two governance surfaces only:

| Surface | Reads |
|---|---|
| `/admin/odr/health` | sync_state distribution · autosave counts · offline_origin rate · device_fingerprint OS mix |
| `odr_section_events` · audit | sync_conflicts (each resolution logged) |

Foreman never sees this data per doctrine O9 (no grades / no
punishment).

## E6 · Completion telemetry projector (D5)

Single consumer: `/admin/odr/health · simplicity-doctrine panel`.

- Median seconds_to_submit per crew_type
- Per-section dwell-time heatmap
- Auto-fill accept rate (proves auto-fill is doing its job)
- Voice usage rate (per-language)

**Not surfaced to foremen.** Not used for any performance review.

## E7 · Safety per-event projector (D7)

Safety projector iterates `safety.events[]`:

- For each event, look up `incident_report_link_id` and verify it
  matches an existing `safety_incidents` row.
- Each event gets its own row in the Safety queue (no merging).
- Hard-block contract (unchanged) applies to **each** event
  independently.

## E8 · Bilingual probe (D8)

`scripts/odr_bilingual_probe.py` runs in `pre_deploy_check.sh`
between `operational_links_doctrine_probe.py` and
`trendline_integrity_probe.py`. Mode: **HARD gate** on missing
`LocalizedString` fields; **WARN** on translation-lineage gaps.

Probe asserts:

1. Every one of the 10 wrapped fields has a `LocalizedString` shape
   (no raw string fallback).
2. When `original_lang != "en"`, both `original` and `translated_by`
   are present.
3. Every value of `translated_by="model"` has a matching row in
   `odr_translation_events`.
4. PDF renderer code reads `.text` only (no grep matches for
   `.original` in `backend/pdf_render*.py` or any odr renderer).
5. Spanish UI labels exist in `frontend/src/lib/i18n/es/*.json` for
   every section title, dropdown enum, and coaching message.
6. Safety hard-stop strings exist in both EN and ES.

## E9 · Revised dispatch order

Same order as original § 4 (Safety still first). Per-segment +
per-event iteration happens **inside** each projector — the dispatch
order is unchanged.

## E10 · Anti-patterns (additions)

Adds to original § 5:

| Anti-pattern | Why forbidden |
|---|---|
| Reading `.original` from any production consumer (PM/Safety/etc.) | Breaks English-canonical contract |
| Rendering `.original` in the PDF | Breaks O10 English-only PDF |
| Storing translations outside `odr_translation_events` | Breaks append-only audit |
| Re-projecting a segment without the right idempotency key | Causes duplicate consumer rows |
| Surfacing `completion_telemetry` to a foreman | Breaks O9 coach-not-punish |

## E11 · Doctrine anchors (O1–O10 in ecosystem)

| Doctrine | Anchor |
|---|---|
| O5 platform > foreman | E2/E3/E4/E7 projectors do the heavy lifting |
| O6 single-entry · multi-consumer | E1–E4 + E7 confirm 12 consumers read · 0 duplicate writes |
| O7 bilingual native | E1 + E8 |
| O8 reliability | E5 |
| O9 coach not punish | E6 (no foreman exposure) |

_End of Delta Integration Addendum (D1–D8) · ECOSYSTEM_INTEGRATION_MAP._

---

# Public-Link Device Continuity Addendum · 2026-05-29

This addendum extends the ecosystem map with the public-link trust
boundary (O11–O20). Sections here **supersede** the matching parts
of earlier addenda where they differ.

## C1 · Trust boundaries (revised)

The platform now has **two distinct trust surfaces** for ODR data:

```
   Public surface (no auth · device-continuity gate only)
     ↓
   ─────────────────────────────────────────────────────
   ↑
   Authenticated surface (PM-token · Admin-token)
```

- **Public surface**: serves the link-based foreman entry flow.
  Reads only today's own ODR + (when continuity passes) seed data
  from the prior ODR. Cannot enumerate other crews / projects /
  prior reports beyond the linked context.
- **Authenticated surface**: serves all 12 consumer projectors,
  PM Review queue, Admin override flow, preload-attempt log
  inspection, and operator knobs.

The continuity engine is the **only** bridge from a public request
to prior-ODR data, and it always emits one `odr_preload_attempts`
row per request.

## C2 · No-cross-crew preload rule

The continuity engine MUST refuse a preload request when:

- `public_link_id` does not match the prior ODR's `public_access.link_id`.
- `project_id` does not match the prior ODR's `project.project_id`.
- `link_scope="project_crew"` AND `crew_id` does not match the prior ODR's `crew_profile.crew_id`.

These three rules are evaluated **before** the seven continuity
signals. No fingerprint match can override a wrong project / wrong
link / wrong crew context.

## C3 · Prior-report data exposure prevention

When the continuity engine returns anything other than `allowed`,
the route layer:

1. Returns a sanitized envelope: `{ preload_allowed: false, denial_reason: "…", today_link_context: {…} }`.
2. The `today_link_context` carries **only** project name + project
   number + report_date + weather snapshot + sunrise/sunset.
3. The envelope does NOT include: prior crew roster · equipment ·
   subs · production · materials · delays · safety answers · photos
   · constraints · notes.
4. The envelope does NOT mention the existence of a prior ODR
   (e.g., does not return `prior_odr_id`).
5. The route writes one `odr_preload_attempts` row server-side and
   returns the envelope to the public client.

## C4 · Override flow · single authenticated path

The only path to an override is:

```
PM/Admin authenticated portal
     → POST /api/odr/preload/override
        body: { prior_odr_id, target_fingerprint, reason }
        auth: X-PM-Token (PM-scoped) OR X-Admin-Token
```

The route:

- Verifies the actor has rights over the project.
- Verifies `target_fingerprint` is a well-formed `DeviceFingerprint`.
- Appends one `DeviceToken` to the prior ODR's
  `public_access.device_tokens[]` with `issued_via` set accordingly.
- Writes one `odr_preload_attempts` row with `outcome="override_used"`.
- Returns 204.

The public link surface **never** sees this route.

## C5 · Consumer projector posture

The 12 consumers are unaffected by this addendum — they all read
`odr` collection data from the authenticated server side, post-
submission. The continuity engine sits **upstream** of submission;
once an ODR is submitted, the projectors see it the same way they
see any other ODR.

One small augmentation: every consumer may read
`prior_report_preload_allowed` + `preload_denial_reason` if they
want to distinguish "seeded from yesterday" rows from "true blank"
rows for analytics purposes. **No consumer makes decisions based on
those flags** — they are observational only.

## C6 · Probe responsibility

`odr_public_link_continuity_probe.py` (PLANNED · D8-companion):

- Wired into `pre_deploy_check.sh` between the bilingual probe and
  the trendline integrity probe.
- HARD gate. Failure blocks deploy.

`trendline_integrity_probe.py` extended to cover
`odr_preload_attempts` (append-only · snapshot anchor).

## C7 · Doctrine anchors (O11–O20 in ECOSYSTEM)

| Doctrine | Anchor |
|---|---|
| O11 public scope | § C1 boundary diagram + § C3 sanitized envelope |
| O15 no leak | § C3 enumerates forbidden fields |
| O17 override authenticated only | § C4 single authenticated path |
| O18 append-only log | § C3 + § C4 both write `odr_preload_attempts` |
| O19 applies to every preload surface | § C3 covers every prior-data class |

_End of Public-Link Device Continuity Addendum · ECOSYSTEM._

---

# Final Governance Addendum · 2026-05-29

This addendum codifies the **governance vs consumption split** in
the ecosystem map. Read alongside `ODR_FINAL_GOVERNANCE_ADDENDUM.md`.

## G1 · Governance vs consumption boundary

```
                Field Leadership Portal (governance owner)
                ├── ODR Center: Inbox · Mine · Search/Export
                ├── Roles: Foreman · Super · Senior Super
                ├── Powers: edit (24h FL) · amend (Super+) · return · approve
                └── Audit: writes odr_amendments + odr_section_events
                                  │
                                  ▼
              ┌────────────────────────────────────────────┐
              │   odr collection · single backend          │
              └────────────────────────────────────────────┘
                                  ▲
                ┌─────────────────┴────────────────────┐
                │                                      │
        PM Portal (consumer)              All other consumers
        ├── Read-only ODR panel           ├── Safety · Dispatch · Shop
        ├── Search · Export               ├── HR · Executive · Memory
        ├── Quality/completion dash       ├── Search · RFI · Schedule
        │   (aggregated · no scoring)     ├── Claims · future AI
        └── No edit · no amend            └── via per-consumer projectors

                Public Link (data collection only)
                ├── Create / draft / submit one ODR
                ├── Never sees other crews / projects / prior reports
                └── Device-continuity gate (O11–O20)
```

There is **one `odr` collection** and **one projector layer**. PM,
FL, Safety, Shop, HR, Exec, Memory, Search, RFI, Schedule, Claims,
and AI all read the same source through their own projectors.
Governance authority is route-gated by token type — not by
collection partitioning.

## G2 · Per-token authority matrix (re-affirmed)

| Token | Read | Edit ≤ 24h | Amend any time | Return | Approve | Override continuity | Manage Inbox |
|---|---|---|---|---|---|---|---|
| (public link · anonymous) | own ODR today only | own (if author) | ❌ | ❌ | ❌ | ❌ | ❌ |
| `X-FL-Token` Foreman | own ODRs | ✅ within 24h | ❌ | ❌ | ❌ | ❌ | ❌ |
| `X-FL-Token` Super | scope projects | ✅ | ✅ | ✅ | ✅ | ❌ (continuity stays separate route) | ✅ |
| `X-FL-Token` Sr Super | regional | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `X-PM-Token` PM | own projects | ❌ | ❌ | ❌ | ❌ | ❌ | read-only |
| `X-Admin-Token` | platform | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Continuity override remains a **separate authenticated route**
(O17). The FL Superintendent token is **not** automatically a
continuity-override token; an explicit admin/PM override action is
required because continuity touches public-link trust.

(Operator may at lock time choose to grant Super continuity-override
power; today's default keeps continuity overrides admin/PM only.)

## G3 · PM as pure consumer (O22)

PM Portal's new read-only ODR panel reads through the existing
`PM` projector (ECOSYSTEM § 2.1) plus three new consumer queries:

- `GET /api/pm/odr/search` — text + filter search across PM's projects
- `GET /api/pm/odr/export.csv` — selection export
- `GET /api/pm/odr/quality-summary` — aggregated coaching counts
- `GET /api/pm/odr/completion-summary` — aggregated section completion

All four are **read-only**; none accept `PATCH` / `POST` on ODR
rows. Per O27, none expose per-foreman scoring.

## G4 · Inbox queries (FL · server-side · same `odr` collection)

The Inbox does not require a separate collection. Five server-side
queries:

| Category | Query shape (project-scoped) |
|---|---|
| Missing | join `(project, crew, report_date)` expected tuples (from dispatch board) ← LEFT JOIN `odr` ON `(project, crew, report_date)` WHERE odr is null |
| Draft | `odr.status="draft"` |
| Submitted | `odr.status="submitted"` |
| Returned | `odr.status="returned"` |
| Approved | `odr.status="approved"` |

A small server-side helper builds the Missing list. No new
collection; existing indexes on `{project_number, report_date, crew_id}`
cover it.

## G5 · Amendment dispatch

When an amendment is committed:

1. Route layer (FL portal · authenticated) writes the new value to
   the `odr` row.
2. Append one row to `odr_amendments`.
3. Re-run the relevant consumer projector(s) (because, e.g., a
   compaction-value amendment affects PM project rollup).
4. If the amended field is rendered on the PDF, set
   `triggers_pdf_rerender=True` so the cached PDF is purged.
5. Telemetry: append one row to `odr_section_events` with
   `event="amended"`.

## G6 · Public-link surface scope (re-affirmed · O23 · O24)

Public-link surface in production:

| Endpoint | Method | Returns |
|---|---|---|
| `/api/public/odr/<link_id>/today/init` | GET | project + date + weather + continuity decision (allowed/denied seeds vs blank) |
| `/api/public/odr/<link_id>/today/draft` | PATCH | partial save (own draft) |
| `/api/public/odr/<link_id>/today/submit` | POST | finalize (writes status=submitted + foreman_ack + amend_allowed_until_utc) |
| `/api/public/odr/<link_id>/today/photo` | POST | upload photo to own ODR only |
| `/api/public/odr/<link_id>/today/attachment` | POST | upload attachment to own ODR only |

That is the **entire** public surface. Listing prior ODRs,
viewing approval status, browsing other crews — all out of scope
for the public link.

## G7 · Single-entry preserved (O6 + O34)

Every governance action (amend / return / approve) writes through
the same routes consumers read from. There is **no** PM-side ODR
model, **no** parallel collection, **no** consumer-owned mutation
surface.

## G8 · Doctrine anchors (O21–O35 in ECOSYSTEM)

| Doctrine | Anchor |
|---|---|
| O21 FL governance | § G1 + § G2 |
| O22 PM consumer | § G3 four read-only endpoints |
| O23–O24 public-link scope | § G6 enumerates entire surface |
| O25 ODR Center | § G2 + § G4 |
| O26 5-category Inbox | § G4 server queries |
| O29 amendment chain | § G5 dispatch order |
| O30 official record | submission writes status=submitted (system of record · projectors fan out) |
| O34 single backend | § G1 diagram + § G7 |
| O35 audit append-only | § G5 step 5 |

_End of Final Governance Addendum · ECOSYSTEM_INTEGRATION_MAP._

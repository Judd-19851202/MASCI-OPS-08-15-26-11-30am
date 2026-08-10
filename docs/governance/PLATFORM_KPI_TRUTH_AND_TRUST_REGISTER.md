# MASCI OPS — PLATFORM KPI TRUTH AND TRUST REGISTER

Last updated: 2026-08-09T17:47Z

Status: **OPEN / NO-GO**

This register is now part of the active PRE-C10 remediation denominator.
No KPI is considered certified because a card renders, an endpoint returns 200, or a preview screenshot looks correct.

## Permanent doctrine inheritance

- This register now inherits `docs/governance/MASCI_OPS_PERMANENT_FIX_DOCTRINE.md`.
- Earlier KPI passes are inherited only where they already prove root cause elimination, full source-to-consumer truth, human-operable workflow meaning, cross-surface parity, and durable regression protection.
- Missing applicable proof means the KPI row remains **FAIL / NOT PROVEN**, even if a prior suite, screenshot, or green badge existed.

## Governing architecture

Required chain for every KPI:

`Source Records → Trust Spine / Evidence → Canonical Authority → Governed Metric / KPI Engine → All Consumers`

Non-negotiable rules:

- No frontend-only KPI calculation for material operational or executive truth.
- No duplicate KPI engine.
- No duplicate calculation for the same governed concept.
- No silent stale fallback.
- No missing-data → `0` coercion.
- No insufficient-evidence → `GREEN` coercion.
- No cross-portal formula drift for the same business fact.

## Discovery method used for this denominator

This register is being built from the live preview runtime plus source-backed route and test evidence:

1. Existing governed KPI dictionary: `/api/admin/wp17a/kpi-dictionary` (`entry_count=25`)
2. Route scan for `kpi_metadata`, governed formulas, and canonical-source annotations
3. Runtime calls to material KPI endpoints using current auth/session contracts
4. Existing parity/certification tests already passing in preview
5. Project-controls downstream parity evidence (`schedule → C7 → C8 → C9`)

Important: if a KPI family lacks explicit metadata, drilldown, or parity proof, it remains **FAIL** even if the payload is present.

## Runtime evidence snapshot captured in this run

| Surface | Endpoint | Runtime result | Notes |
|---|---|---:|---|
| WP17A KPI dictionary | `/api/admin/wp17a/kpi-dictionary` | 200 | `entry_count=25` |
| Executive Overview | `/api/admin/executive/overview` | 200 | Tile family present; child parity still expanding |
| Project Health | `/api/project-health` | 200 | `summary.total=43` |
| Safety company posture | `/api/safety/company/safety-kpis?window=30d` | 200 | `status_band=amber` |
| Draft Health | `/api/admin/draft-health` | 200 | Remediated truth metadata present |
| Governance Summary | `/api/admin/governance/summary` | 200 | Freshness + metadata present |
| R2 Lifecycle Health | `/api/admin/r2/lifecycle/health` | 200 | Freshness / ownership / orphan split present |
| Cluster Capacity Current | `/api/cluster/capacity` | 200 | Public-safe point-in-time KPI |
| Cluster Capacity History | `/api/cluster/capacity/history?days=30` | 200 | Forecast/history payload present |
| OCC Health | `/api/admin/occ/health` | 200 | `overall_status=MISMATCH` |
| Platform Trust Validator | `/api/admin/platform-trust/validate` | 200 | `validation_status=MISMATCH` |
| Production Certification | `/api/admin/production-certification` | 200 | `platform_band=amber` |
| FL Time-Off Queue | `/api/field-leadership/time-off/stats` | 200 | Metadata present |
| HR Employee Requests Queue | `/api/hr/employee-requests?status=pending` | 200 | Metadata present |
| HR Roster | `/api/hr/employee-roster?limit=5` | 200 | Metadata present |
| Ops Expirations Summary | `/api/operations/expirations/summary` | 200 | Metadata present |
| PM Operational KPIs | `/api/pm/projects/OD-100/operational-kpis?window=ptd` | 200 | Top-level `kpi_metadata` now present; parity tests exist |
| Safety Project KPIs | `/api/safety/projects/OD-100/safety-kpis?window=ptd` | 200 | No top-level `kpi_metadata`; parity tests exist |
| C7 Forecasting Workspace | `/api/pm/project-controls/projects/ZZ-RUNTIME-CERT-2026/forecasting/workspace` | 200 | Downstream parity lane active |
| C8 Earned Value | `/api/admin/governance/project-controls/projects/ZZ-RUNTIME-CERT-2026/earned-value` | 200 | `summary` present |
| C9 Portfolio Intelligence | `/api/admin/governance/project-controls/portfolio-intelligence` | 200 | `projects=43` |
| Schedule Overview | `/api/pm/project-controls/projects/ZZ-RUNTIME-CERT-2026/schedule/overview` | 200 | Active version/history present |
| Rolling Two-Week Lookahead | `/api/pm/project-controls/projects/ZZ-RUNTIME-CERT-2026/schedule/lookahead` | 200 | Overlay evidence present |
| Daily Work Plan | `/api/pm/project-controls/projects/ZZ-RUNTIME-CERT-2026/schedule/daily-work-plan?work_date=2026-08-08` | 200 | Overlay evidence present |
| Trust Spine | `/api/admin/trust-spine` | 200 | `platform_band=green`, `canonical_status=VERIFIED` |
| System Recovery Collection Diagnostics | `/api/admin/crew-recovery/status` | 200 | `count_audit` now classifies raw counts as canonical/live, legacy/deprecated, telemetry, or genuine zero; no longer presented as business KPI truth |

## KPI denominator status

This denominator is now explicitly split into:

- **CERTIFIED rows**: runtime + governed formula + canonical-source + parity/drilldown proof present
- **FAIL rows**: missing one or more of formula, parity, drilldown, trust-chain coverage, or consumer inventory

Until every row below is PASS, PRE-C10 remains **OPEN / NO-GO**.

## Register

| KPI | Business definition | Formula | Owner | Source records | Canonical authority | Trust Spine / evidence coverage | Freshness | Completeness | Truth state | Calculation / version | Operator consumers | Executive consumers | Exports / outputs | Parity result | Drilldown result | Runtime evidence | PASS / FAIL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Daily Report Draft Health | Distinct logical draft slots, not raw append-only event noise | Governed draft entity bucketing over `draft_telemetry`; entity-aware buckets + limitations | `daily-report-resiliency` | `draft_telemetry` | `/api/admin/draft-health` | Partial; metadata present, but Trust Spine-to-consumer matrix still not fully linked | Current snapshot (`generated_at`) | Partial legacy telemetry disclosed explicitly | `PARTIAL` | Current endpoint metadata; WP17A governed remediation | Admin Operations Control Center | Ops / admin decision surfaces | OCC child card usage | Not yet expanded across every downstream consumer | Endpoint exposes definitions/limitations | 200; `entity_basis`, `entity_confidence`, `limitations` present | FAIL |
| Governance Summary | Persisted compliance findings inventory plus scan freshness/confidence | Severity/status/category/rule rollups + scan freshness SLA | `governance-trust` | `compliance_findings`, `compliance_scans` | `/api/admin/governance/summary` | Good at source; broader platform KPI coverage still needs child linkage | Current within SLA | Good for current endpoint | `CURRENT` | Live governance summary formula | Governance / admin | Executive trust consumers via derived posture | Governance scan outputs | Local endpoint good; not yet reconciled to every derivative badge | Rule catalog + freshness present | 200; freshness object present | FAIL |
| R2 Lifecycle Health | Object storage posture split by freshness, ownership coverage, and orphan risk | Weighted subscores over freshness / ownership / orphan evidence | `storage-reliability` | `r2_inventory`, `r2_classifications`, `r2_lifecycle_runs`, `backup_health` | `/api/admin/r2/lifecycle/health` | Partial; source evidence present, Trust Spine linkage not fully mapped to all storage surfaces | Aging/Current depends on inventory state | Explicitly disclosed | `PARTIAL` | Current endpoint contract | Admin storage/recovery | Executive recovery posture consumers | Recovery snapshot derivatives | Cross-surface parity still open versus recovery dashboard | Subscores + sections present | 200; metadata present | FAIL |
| Cluster Capacity Current | Point-in-time quota usage posture | `storage_used_mb / tier_quota_mb * 100` + severity thresholds | `storage-reliability` | `dbStats`, managed DB identity | `/api/cluster/capacity` | Bounded runtime evidence exists; Trust Spine not the direct owner | Current point-in-time | Good | `CURRENT` | `WP17A-KPI-021-current` | Admin / storage operators | Executive infra visibility | Public-safe capacity surface | Must still reconcile with history + recovery surfaces | Public-safe endpoint explains formula via metadata | 200; metadata validated | FAIL |
| Cluster Capacity Forecast / History | Growth slope and exhaustion forecast from retained snapshots | Slope / projection over `cluster_capacity_history` | `storage-reliability` | `cluster_capacity_history` | `/api/cluster/capacity/history` | Bounded evidence exists; no full portfolio consumer inventory yet | Current over retained samples | Depends on retained sample count | `CURRENT` | `WP17A-KPI-021-history` | Admin / diagnostics | Executive infra visibility | Capacity history/forecast outputs | Current/history intentional exception documented; broader parity still open | Forecast metadata present | 200; `rows=676` | FAIL |
| OCC Health Aggregator | Operations Control aggregator of child truth surfaces | Derived from child endpoint fanout + canonical truth registry | `operations-control` | Child endpoint fanout, truth registry | `/api/admin/occ/health` | Partial; aggregator discloses child ownership, but lane currently mismatched | Current snapshot | Completeness depends on child probes | `MISMATCH` | `WP17A-KPI-022` | OCC operators | Executive admin surfaces | OCC dashboard outputs | FAIL by current status | Child-card reason path present | 200; `overall_status=MISMATCH` | FAIL |
| Platform Trust Validator | Platform-wide bounded validator that may only downgrade unsupported trust claims | Composite validation over archive lineage, email routing, workflow delivery, PM coverage | `platform-trust-program` | `archive_lineage`, `email_routing_audit_v2`, workflow delivery evidence, PM coverage | `/api/admin/platform-trust/validate` | Good bounded evidence; still not canonical owner | Current snapshot | Partial by design | `MISMATCH` | `WP17A-KPI-024` | Admin / trust operators | Executive readiness viewers | Trust validation outputs | Current lane intentionally fail-closed | Reasons exposed | 200; validator mismatch | FAIL |
| Production Certification Freshness | Release/trust posture based on terminal business evidence, not HTTP reachability | Workflow counters and freshness policy over release evidence | `production-certification` | certification records, workflow evidence | `/api/admin/production-certification` | Strong for workflow evidence; not yet reconciled with every KPI consumer | Current snapshot | Partial where workflows unexercised | `PARTIAL` | Current production-certification contract | Admin / release operators | Executive release consumers | Certification outputs | Needs reconciliation against final PRE-C10 release gate | Counters and freshness context present | 200; `platform_band=amber` | FAIL |
| Executive Overview — Jobs tile | Company-wide job/project count posture | Count over governed job/project definitions | `executive-truth` | `jobs_master`, related project sources | `/api/admin/executive/overview` tile `jobs` | Partial; route metadata exists but per-tile Trust Spine lineage not fully inventoried | Current snapshot | Unknown until full denominator closes | `PARTIAL` | Current executive overview tile family | Admin / ops | Executive overview | Executive exports / screenshots | Tile-family parity still open | Tile metadata exists in route code, not fully surfaced in runtime register | 200; tiles present | FAIL |
| Executive Overview — Overdue tile | Company-wide overdue work/obligation posture | Governed overdue rollup over canonical overdue concepts | `executive-truth` | schedule / corrective-action / work obligation sources | `/api/admin/executive/overview` tile `overdue` | Partial | Current snapshot | Partial | `PARTIAL` | Current executive overview family | Admin / ops | Executive overview | Executive outputs | Needs consumer-by-consumer parity | Drilldown inventory incomplete | 200; tiles present | FAIL |
| Executive Overview — Staffing tile | Staffing posture for active operations | Governed staffing rollup over employee/project assignment truth | `executive-truth` | employee / staffing / project-assignment sources | `/api/admin/executive/overview` tile `staffing` | Partial | Current snapshot | Partial | `PARTIAL` | Current executive overview family | Admin / staffing operators | Executive overview | Executive outputs | Still open versus HR/staffing surfaces | Drilldown inventory incomplete | 200; tiles present | FAIL |
| Executive Overview — Equipment tile | Fleet/equipment friction posture | OOS + monitor + open defects + high-severity holds | `executive-truth` | `fleet_status`, `fleet_defects`, `asset_holds` | `/api/admin/executive/overview` tile `equipment` | Partial | Current snapshot | Partial | `PARTIAL` | Current executive tile formula in route | Fleet / admin ops | Executive overview | Executive outputs | Not yet reconciled across Fleet / Dispatch / Exec surfaces | Tile metadata exists in source | 200; tiles present | FAIL |
| Executive Overview — Safety tile | Executive safety posture | Governed unresolved incidents + corrective actions and safety readiness concepts | `safety-truth` | `incidents`, `corrective_actions`, training / meeting evidence | `/api/admin/executive/overview` tile `safety` | Better than earlier; Safety truth repairs active, but full downstream denominator still open | Current snapshot | Good for corrected CA counts; broader safety denominator open | `PARTIAL` | Reuses corrected corrective-action truth helper | Safety / admin | Executive overview | Executive outputs | Safety archive/history/export/notification parity still open | Limited runtime drilldown | 200; tiles present | FAIL |
| Executive Overview — Activity tile | Activity / operational attention posture | Derived executive activity rollup | `executive-truth` | ops activity sources | `/api/admin/executive/overview` tile `activity` | Partial | Current snapshot | Partial | `PARTIAL` | Current executive family | Ops | Executive overview | Executive outputs | Not yet fully reconciled | Drilldown inventory incomplete | 200; tiles present | FAIL |
| Project Health Summary | Portfolio rollup of project health colors and totals | Governed status ladder over project row indicators | `project-health` | canonical project indicators | `/api/project-health` | Partial; endpoint runtime and count contract good, downstream consumer inventory still open | Current snapshot | Good at endpoint level | `CURRENT` | Current project-health contract | PM / admin / ops | Executive portfolio views | Project health exports / cards | Local summary internally reconciles; broader parity still open | Row-level indicators exposed | 200; `summary.total=43` | FAIL |
| HR Employee Requests Queue | Pending HR request workload | Count over `employee_requests` by status | `hr-queue-integrity` | `employee_requests` | `/api/hr/employee-requests` | Not a Trust Spine workflow owner; evidence is source-based | Current snapshot | Good | `CURRENT` | Current route metadata | HR operators | Admin staffing / executive people ops | Queue exports / PDFs if any still need inventory | Endpoint-level parity good; consumer inventory open | Queue endpoint exposes metadata | 200; metadata present | FAIL |
| HR Time-Off Queue | FL-submitted time-off requests by decision status | Counts over `field_leadership_records` HR decision state | `hr-time-off` | `field_leadership_records` | `/api/field-leadership/time-off/stats` | Source-based evidence good; downstream badge inventory still open | Current snapshot | Good | `CURRENT` | Current route metadata | HR / field leadership | Admin people-ops | Notifications / email / PDF still need KPI parity inventory | Endpoint good; cross-surface parity still open | Pending count traceable to queue | 200; metadata present | FAIL |
| Active Employee Roster Count | Active employee roster truth | Canonical roster filter over employee lifecycle/roster truth | `hr-identity` | employee lifecycle / roster collections | `/api/hr/employee-roster` | Partial; employee truth lane still open platform-wide | Current snapshot | Partial until employee/project-member closure completes | `PARTIAL` | Current route metadata | HR / staffing / field pickers | Admin staffing | Exports and pickers still need parity inventory | Cross-surface employee truth still open | Endpoint metadata present | 200; metadata present | FAIL |
| Operations Expirations Summary | Expiration posture across docs/training | Combined expiration-band counts across expiration sources | `expiration-governance` | `document_expirations`, `safety_training_records` | `/api/operations/expirations/summary` | Source-based evidence present; full consumer inventory still open | Current snapshot | Good | `CURRENT` | Current route metadata | HR / Safety / Ops | Admin / executive operational health | Alerts / exports still need inventory | Needs parity proof across every badge/card | Endpoint metadata present | 200; metadata present | FAIL |
| Safety Company Posture — status band | Company-wide safety attention band | Governed band from incident / near miss / escalation-gap conditions | `safety-truth` | Safety aggregator inputs | `/api/safety/company/safety-kpis` | Partial; source chain tested, but not fully linked to Trust Spine and all consumers | Current snapshot | Good for endpoint payload; broader denominator open | `PARTIAL` | `contract_version=23.8` | Safety portal operators | Executive / admin safety readers | Safety exports / digests / dashboards | PM↔Safety parity partly tested | Portal has drilldown card, full proof still open | 200; `status_band=amber` | FAIL |
| Safety Company Posture — totals family | Company-wide totals for events, incidents, meetings, JHAs, inspections, injuries, escalations | Shared operational KPI aggregator | `safety-truth` | daily reports, incidents, safety records | `/api/safety/company/safety-kpis` | Partial; shared aggregator verified, consumer denominator still open | Current snapshot | Good at endpoint level | `PARTIAL` | `contract_version=23.8` | Safety portal | Executive/admin via derived consumers | Safety reports / exports still need inventory | Some parity tests exist, not 100% of consumers | Portal drilldown exists | 200; totals present | FAIL |
| PM Operational KPI family | Per-project labor/equipment/materials/production/delays/safety/intelligence posture | Shared operational KPI aggregator over canonical operational facts and safety sources | `operations-control` / project-controls domain | `operational_facts`, safety collections, supporting project sources | `/api/pm/projects/{project}/operational-kpis` | Partial; parity tests exist, top-level runtime metadata is now present, but not every consumer is mapped yet | Current snapshot | Depends on source family completeness | `PARTIAL` | `contract_version=23.7` | PM project detail | Executive via downstream derived views | None fully inventoried yet | PM↔Safety subset parity tested | Drilldown partly available by section | 200 for `OD-100` | FAIL |
| Safety Project KPI family | Per-project safety-only subset from the shared operational KPI spine | Shared aggregator subset over governed project safety facts | `safety-truth` | same governed safety sources as PM operational family | `/api/safety/projects/{project}/safety-kpis` | Partial | Current snapshot | Good at endpoint payload; PM mirror metadata now aligns with the subset's governed lineage | `PARTIAL` | Shared `23.7/23.8` KPI lineage | Safety project operators | Executive via derived safety posture | Safety reports still need inventory | PM↔Safety parity tests exist for subset | Drilldown partial | 200 for `OD-100` | FAIL |
| Schedule Overview | Canonical approved/current schedule authority, history, counts, activities, lookahead overlays | Governed schedule authority engine | project-controls schedule authority | schedule versions, activities, work blocks, daily report actuals | `/api/pm/project-controls/projects/{project}/schedule/overview` | Improving; downstream Trust Spine and parity evidence partially proven | Current snapshot | Partial until full revision lifecycle and UI proof close | `PARTIAL` | active version/history contract | PM / project controls | Admin governance / executive downstream | Schedule exports still need inventory | Core parity positive, denominator incomplete | Version/history visible in payload | 200 for certification project | FAIL |
| Rolling Two-Week Lookahead | Governed overlay over approved schedule + current field constraints | Overlay from approved schedule, work blocks, actuals, constraints | project-controls schedule authority | schedule overview + lookahead records + field overlays | `/api/pm/project-controls/projects/{project}/schedule/lookahead` | Partial; overlay relationship validated in tests | Current snapshot | Partial until all consumers mapped | `CURRENT` | current overlay contract | PM / field execution | Executive downstream via schedule summaries | Lookahead outputs still need inventory | Overlay parity test exists | Payload exposes tasks/constraints | 200 for certification project | FAIL |
| Daily Work Plan | Day-specific execution overlay tied to lookahead and baseline | Governed plan over lookahead + active/baseline versions | project-controls schedule authority | schedule versions, lookahead, day plan sources | `/api/pm/project-controls/projects/{project}/schedule/daily-work-plan` | Partial | Current snapshot | Partial | `CURRENT` | current overlay contract | PM / field execution | Executive downstream as derivative only | Daily plan outputs still need inventory | Overlay parity test exists | Notes/version lineage visible | 200 for certification project | FAIL |
| C7 Forecasting Workspace | Governed forecasting/commitments workspace from schedule + production + resources + constraints | Shared forecasting workspace with scenario comparison and commitments | project-controls forecasting | schedule authority, work blocks, commitments, production/resource inputs | `/api/pm/project-controls/projects/{project}/forecasting/workspace` and admin governance mirror | Trust coverage partial but active; downstream parity tests exist | Current snapshot | Partial until all material projects/consumers close | `PARTIAL` | current forecasting workspace contract | PM / Field Leadership constrained view | Admin governance / executive project-controls | Snapshot outputs / commitment records | Selected parity to schedule and C9 is PASS; denominator incomplete | Workspace exposes scenario/governance sections | 200 for certification project | FAIL |
| C8 Earned Value Summary | BAC/PV/EV/AC/CPI/SPI/EAC posture for project controls | Earned-value governed calculations over schedule/budget/actual evidence | project-controls earned value | budget lines, schedule, actual costs, commitments | `/api/admin/governance/project-controls/projects/{project}/earned-value` | Partial but better; parity tests exist to C9 | Current snapshot | Partial until line-level and consumer denominator closes | `PARTIAL` | current earned-value engine | Project controls operators | Admin governance / executive portfolio | EV reports still need inventory | Selected C8↔C9 parity PASS; denominator incomplete | Lines + evidence present | 200; summary present | FAIL |
| C9 Portfolio Intelligence | Portfolio-level performance posture across projects | Governed portfolio aggregation over C7/C8/schedule/project data | project-controls portfolio intelligence | project schedule + financial + forecasting lineage | `/api/admin/governance/project-controls/portfolio-intelligence` | Partial; downstream parity exists for certification project | Current snapshot | Partial across full portfolio denominator | `PARTIAL` | current portfolio intelligence contract | PM portfolio / admin governance | Executive portfolio | Portfolio exports still need inventory | Certification-project parity PASS; full portfolio parity open | Project-level rows present | 200; `projects=43` | FAIL |
| Trust Spine Platform Band | Workflow evidence posture for governed operational chains | Aggregated from workflow lifecycle evidence and cadence policy | `trust_spine` | trust spine events, workflow profiles | `/api/admin/trust-spine` | Strong for workflow evidence itself | Current snapshot | Good for workflow chain | `CURRENT` | current trust spine contract | Admin / operations control | Executive platform posture | Trust/event exports | Trust Spine itself PASS; KPI consumer coverage still open | Workflow-level drilldown exists | 200; `platform_band=green` | FAIL |
| System Recovery Collection Diagnostics | Exception-only technical collection presence for recovery triage | Raw `count_documents` by collection plus governed truth classification envelope | `system-recovery` | raw Mongo collections (`users`, `projects`, `equipment_master`, `employees`, etc.) | `/api/admin/crew-recovery/status` `count_audit` | Strong after the Admin OS repair; the endpoint now explicitly states that these figures are technical diagnostics only and routes each count back to its canonical governed surface | Current snapshot (`refreshed_at`) | Partial by design; this is technical presence data, not business completeness truth | `TECHNICAL_DIAGNOSTIC` | current `count_audit` contract | Exception-only Admin System Recovery | None — primary Admin OS and executive consumers are intentionally excluded | No exports or business rollups allowed | Landing-page parity PASS after re-home to `/admin/system` | Classification labels + canonical surface mapping present | 200; sample returns legacy-deprecated Crew Hub counts alongside canonical/live equipment and employee master counts | PASS |

## Material KPI families explicitly added to the active denominator but still needing row expansion

These families are now mandatory active work, not backlog:

- Admin hub / Admin Operations Dashboard card sets
- Executive Operations Dashboard and Executive Operational Intelligence scorecards
- PM hub, PM command center, PM project budget, PM schedule, PM controls, PM portfolio
- Field Leadership dashboards and constrained forecast/schedule posture surfaces
- Safety digests, safety workspace counts, archives/history/search totals, exports, notifications
- HR dashboards, employee lifecycle/status totals, staffing/project-member counts
- Shop hub KPI strips and queue metrics
- Dispatch hub/board/command center KPI strips and transportation forecast surfaces
- Fleet / equipment / transportation health, status, availability, OOS, defect and utilization surfaces
- Daily reports dashboard and operational intelligence rollups
- Compliance, governance, qualifications, training and audit posture cards
- C6 operational intelligence consumers
- Every C7 / C8 / C9 summary, card, score, badge, band, and export

Any unexpanded family above still counts against final PRE-C10 GO.

## Current findings from this run

1. The old WP17A KPI governance lane is useful but not sufficient; it covers 25 entries, while PRE-C10 now requires platform-wide KPI denominator closure.
2. Several modern KPI families return valid runtime payloads but still lack full drilldown provenance or downstream consumer inventory; the PM operational KPI family now exposes top-level `kpi_metadata`, but broader denominator work remains.
3. `OCC Health` and `Platform Trust` are currently truthful in failing closed (`MISMATCH`) rather than falsely green — this is preferable, but still blocks closure.
4. Project-controls downstream runtime evidence is materially stronger now: schedule, lookahead, daily work plan, C7, C8, and C9 all returned live certification-project payloads in this run.
5. Executive safety KPI parity was rechecked against an independent source-record oracle. The intermediate `open=10` reading was not a legitimate alternate KPI — it was preview test pollution from lifecycle rows that were wrongly created as `live_operational`. After governed reclassification plus test-harness repair, live runtime truth returned to `open=2`, `overdue=2`.
6. Independent hostile tests now prove that explicit governed hidden markers exclude technical rows, while test-like names alone do **not** hide legitimate operator records.
7. Schedule source-chain testing now proves exact value parity from source records → schedule authority → lookahead/daily-work-plan → C7 → C8 → C9 for the deterministic certification project, and surfaced a real stale-lookahead defect that has now been repaired in preview.
8. The Admin OS / System Recovery amendment is now part of the KPI truth ledger: raw recovery counts are explicitly downgraded to technical diagnostics and re-homed off the primary landing, preventing collection totals from masquerading as business truth.

## Exit criteria for this register

This register may only flip to PASS when all of the following are true:

- KPI denominator = 100% dispositioned
- material KPI truth defects = 0
- cross-surface KPI parity defects = 0
- fake-zero defects = 0
- false-green defects = 0
- unexplained stale KPI states = 0
- duplicate KPI calculations = 0
- decision-critical Trust Spine coverage gaps = 0

Until then:

- **GO — READY TO SAVE & DEPLOY** is not allowed
- **LIVE PRODUCTION: REDEPLOYMENT REQUIRED** remains true
- **C10: NOT AUTHORIZED** remains true
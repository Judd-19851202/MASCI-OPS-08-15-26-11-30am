# BCSS Release 2 · Program 2 · Wave 3 · Family 3C
# Operational Events — Phase A Discovery

## Scope and Method
- Scope executed as authorized: **read-only repository discovery** and **documentation synthesis only**.
- No application code, tests, configuration, roadmap, PRD, or changelog files were modified.
- Repository evidence reviewed focused on the bounded Family 3C owner and its direct ecosystem:
  - `/app/backend/routes/operational_events.py`
  - `/app/backend/services/motive_service.py`
  - `/app/backend/lib/event_fanout.py`
  - `/app/backend/lib/operational_signals.py`
  - `/app/backend/routes/operational_signals.py`
  - `/app/backend/lib/workflow_state_events.py`
  - `/app/backend/routes/operational_timeline.py`
  - `/app/backend/routes/operational_links.py`
  - `/app/backend/routes/operational_constraints.py`
  - `/app/backend/routes/operations_intelligence.py`
  - `/app/backend/server.py`
  - `/app/frontend/src/pages/PmProjectDetail.jsx`
  - `/app/memory/PRD.md`

## Executive Determination
**Yes — the repository contains one bounded constitutional Family 3C Operational Events family, but only when defined narrowly as the normalized M-2 operational event spine owned by `/app/backend/routes/operational_events.py`, writing to `operational_events`, and consuming raw Motive ingress from `motive_events` plus verified `operational_locations`.**

The repository does **not** support treating every event-like subsystem as one unified Family 3C. The broader ecosystem includes multiple adjacent event mechanisms that are separate in ownership and purpose:
- raw Motive ingress telemetry (`motive_events`)
- normalized operational presence events (`operational_events`)
- workflow audit events (`workflow_state_events`)
- operational telemetry signals (`usage_events` with `kind="operational_signal"`)
- chronology/link substrates (`operational_constraints`, `operational_links`, `operational_timeline`)
- read-only intelligence aggregations that consume raw telemetry directly (`operations_intelligence.py`)

This means Family 3C is constitutionally bounded, but the overall repository event ecosystem is **multi-family / multi-substrate**, not one monolith.

## Repository-Aligned Family Definition
The strongest repository-backed Family 3C owner evidence is:
- `PRD.md` explicitly records the Wave 3 Family 3 split and names `3C — Operational Events` with repository owner `/app/backend/routes/operational_events.py`.
- `server.py` wires `build_operational_events_router(db, require_admin)` as a distinct router.
- `operational_events.py` declares itself as **"M-2 · Event Router"**, reads from `motive_events` and verified `operational_locations`, and writes only to `operational_events`.

## Event Ownership, Lifecycle, and Boundary

### Canonical Family 3C Ownership
**Canonical owner:** `/app/backend/routes/operational_events.py`

Evidence from the file establishes the following constitutional posture:
- reads from `motive_events` plus verified `operational_locations`
- writes only to `operational_events`
- materialization is idempotent on stable deterministic IDs
- unknown geofences remain `UNKNOWN`; no guessing is allowed
- storage is gated to a narrow allowed-field schema to prevent surveillance / behavior drift

### Operational Event Lifecycle
1. **Ingress:** `MotiveService.process_webhook(...)` and `MotiveService.sync_events(...)` persist raw Motive rows into `motive_events`.
2. **Classification at ingress:** raw event families are classified into Motive event families such as `vehicle_gps`, `geofence_enter`, `geofence_exit`, `asset_geofence_enter`, `asset_geofence_exit`, `hos_violation`, `fault_code`, `dvir`, `gateway_disconnected`, `gateway_reconnected`, `ai_coach_recap`, and `other`.
3. **Normalization / routing:** `POST /api/admin/operational-events/materialize` reads a Motive window, resolves verified locations and asset labels, and produces deterministic normalized operational events.
4. **Canonical storage:** normalized rows are upserted into `operational_events` by stable `id`.
5. **Read-side consumption:** project-day summaries, per-asset timelines, dispatch verification status, verification routes, and downstream service-event projections read from `operational_events`.

### Adjacent But Non-Owner Event Systems
The following are evidence-backed adjacent systems, not the Family 3C owner:
- **`motive_events`**: raw telemetry ingress and classifier output
- **`workflow_state_events`**: append-only workflow transition audit for lifecycle modules
- **`usage_events` / operational signals**: lightweight telemetry rollups, best-effort, non-transactional
- **`operational_links` / `operational_constraints` / `operational_timeline`**: chronology and relationship substrate
- **`operations_intelligence.py`**: read-only role-specific aggregations over `motive_events`

## Additional Discovery Emphasis 1 — Event Taxonomy

### A. Raw Telemetry Taxonomy (`motive_events`)
Repository evidence shows raw ingress events are classified at write time in `services/motive_service.py` into a Motive-facing taxonomy including:
- `vehicle_gps`
- `harsh_event`
- `fault_code`
- `fault_code_closed`
- `dvir`
- `geofence_enter`
- `geofence_exit`
- `asset_geofence_enter`
- `asset_geofence_exit`
- `hos_violation`
- `gateway_disconnected`
- `gateway_reconnected`
- `ai_coach_recap`
- `other`

These are raw/provider-derived event families, not the Family 3C normalized canonical event vocabulary.

### B. Canonical Operational Taxonomy (`operational_events`)
Family 3C normalizes only location/presence transitions. `operational_events.py` maps verified location categories into canonical arrival/departure event types such as:
- `PROJECT_ARRIVAL` / `PROJECT_DEPARTURE`
- `ASPHALT_PLANT_ARRIVAL` / `ASPHALT_PLANT_DEPARTURE`
- `CONCRETE_PLANT_ARRIVAL` / `CONCRETE_PLANT_DEPARTURE`
- `PIT_ARRIVAL` / `PIT_DEPARTURE`
- `YARD_ARRIVAL` / `YARD_DEPARTURE`
- `SHOP_ARRIVAL` / `SHOP_DEPARTURE`
- `DISPOSAL_ARRIVAL` / `DISPOSAL_DEPARTURE`
- `VENDOR_ARRIVAL` / `VENDOR_DEPARTURE`
- `UNKNOWN_ARRIVAL` / `UNKNOWN_DEPARTURE`

This taxonomy is materially narrower than raw Motive taxonomy and is the best evidence of the actual Family 3C constitutional domain.

### C. Audit / Derived / Substrate Taxonomies Outside Family 3C Ownership
- `workflow_state_events`: workflow transition audit rows (`workflow`, `from_state`, `to_state`, actor, evidence, request metadata)
- `usage_events` with `kind="operational_signal"`: passive operational signals such as `incident.created`, `equipment.fail`, `po.approve`, `ca.closed`
- `operational_constraints` chronology rows and `operational_links` relationship/status changes

**Conclusion on taxonomy:** the repository supports a **narrow canonical Family 3C taxonomy** for normalized operational presence events, surrounded by several adjacent event taxonomies.

## Additional Discovery Emphasis 2 — Event Source of Truth

### Raw Source of Truth
For Motive-origin telemetry, the repository evidence points to **`motive_events`** as the raw source of truth.

Why:
- `MotiveService.process_webhook(...)` persists webhook deliveries there
- `MotiveService.sync_events(...)` backfills polling rows there
- unique `(provider, event_signature)` index is the dedup/storage guarantee
- `operations_intelligence.py` reads `motive_events` directly for several operational read models

### Canonical Family 3C Source of Truth
For **normalized operational arrival/departure presence facts**, the source of truth is **`operational_events`**.

Why:
- `operational_events.py` is the only explicit normalizer/router
- it declares write exclusivity to `operational_events`
- public read endpoints (`project-day`, `timeline`, `dispatch-status`) all read `operational_events`
- downstream verification and service-event readers also consume `operational_events`

### Supporting Authorities, Not Event Owners
- **`operational_locations`**: authority for geofence-to-location-type/location identity; if unresolved, event remains `UNKNOWN`
- **`asset_mappings`**: label / MASCI equipment resolution support only

### Source-of-Truth Conclusion
There is **not one platform-wide event source of truth**.

There are at least two distinct truths:
- raw provider truth: `motive_events`
- canonical normalized Family 3C truth: `operational_events`

That split is repository-backed and must be preserved in any future family boundary.

## Additional Discovery Emphasis 3 — Event Ordering

Repository evidence shows **deterministic per-actor ordering**, not a single global event-order contract.

### Ordering Rules in the Family 3C Router
Inside `route_motive_events(...)`:
- raw presence events are grouped by actor key (`vehicle:<id>` or `equipment:<id>`)
- each actor stream is sorted by parsed `event_at`
- contiguous duplicate enters/exits for the same geofence are collapsed
- a new enter on a different location can synthesize a departure for the prior open location
- orphan exits are ignored unless they match the tracked current location

### Resulting Ordering Model
- **Guaranteed:** deterministic sequencing within one actor stream for one materialization run
- **Not evidenced:** a repository-wide global total order across all actors and all event systems
- **Implication:** Family 3C ordering is sufficient for normalized presence lifecycles, but it is not a universal platform event-ordering substrate

## Additional Discovery Emphasis 4 — Failure Semantics

### Ingress Failure / Duplicate Semantics
`MotiveService` implements strong replay suppression:
- deterministic `event_signature`
- unique partial index on `(provider, event_signature)`
- webhook duplicates return `status="duplicate"` and suppress side effects
- polling overlap with webhook deliveries is also deduped by the same signature model

This is strongly evidenced by `tests/test_motive_webhook_dedup.py`, including:
- first delivery stored once
- retry ignored
- 100 retries collapse to one row
- concurrent insert race collapses to one stored row
- scheduler/webhook overlap collapses to one row

### Router / Materialization Failure Semantics
In `operational_events.py`:
- invalid docs are rejected by the allowed-field storage gate
- forbidden surveillance/behavior fields are rejected at write time
- missing actor keys or bad timestamps are skipped
- unknown geofence mappings are preserved as `UNKNOWN`, not guessed
- upserts by stable ID make materialization idempotent

### Adjacent Family Failure Semantics
- `event_fanout.py`: explicitly best-effort and never transactional
- `operational_signals.py`: best-effort only; never blocks originating workflow
- `workflow_state_events.py`: best-effort append-only audit write; never blocks caller mutation

### Failure-Semantics Conclusion
Family 3C has strong deduplication and idempotent normalization semantics, but broader platform event durability is intentionally uneven because several adjacent audit/telemetry systems are best-effort by design.

## Additional Discovery Emphasis 5 — Platform-Wide Event Map

### Layer 1 — Raw Ingress / Provider Telemetry
- **Owner:** `services/motive_service.py`
- **Collection:** `motive_events`
- **Role:** captures provider-origin rows, classification, severity/priority decoration, and dedup

### Layer 2 — Canonical Family 3C Normalization
- **Owner:** `routes/operational_events.py`
- **Collection:** `operational_events`
- **Role:** canonical normalized operational presence spine (arrival/departure by verified location)

### Layer 3 — Read Models / Consumers of Family 3C
- `GET /api/operational-events/project-day/{project_number}/{date}`
- `GET /api/operational-events/timeline/{detection_key}/{date}`
- `GET /api/operational-events/dispatch-status/{asset_key}`
- `routes/verification.py` reads `operational_events`
- `routes/asset_service_events.py` reads `operational_events`
- `frontend/src/pages/PmProjectDetail.jsx` consumes the project-day endpoint

### Layer 4 — Adjacent Event Substrates Outside Family 3C Ownership
- `workflow_state_events` for lifecycle audit
- `operational_links` for cross-artifact relationships
- `operational_constraints` chronology for blockers
- `operational_timeline` as read-only chronology aggregation over links/constraints
- `usage_events` operational signals for telemetry rollups
- `operations_intelligence.py` role-specific read-side aggregation over `motive_events`

### Platform-Wide Map Conclusion
The repository demonstrates an **event ecosystem**, not a single global event family. Family 3C is the normalized operational presence spine inside that ecosystem.

## Additional Discovery Emphasis 6 — Survivability Awareness

### What Appears Durable
- `operational_events` is not in the explicit backup exclusion list reviewed in `server.py`
- `workflow_state_events` appears as durable append-only audit with indexes but no reviewed TTL evidence
- `operational_links` and `operational_constraints` appear as durable substrates

### What Is Explicitly Ephemeral / Regenerable
- `usage_events` has a 90-day TTL in `routes/usage_analytics.py`
- `usage_events` is explicitly excluded from complete backups in `server.py`
- `operational_signals` intentionally reuses `usage_events`, so signal telemetry is survivability-light by design

### What Is Uncertain / Contradictory
- repository documentation in `training_center.py` states `motive_events` has a 30-day TTL and need not be backed up
- reviewed code shows **no TTL index for `motive_events`** and `motive_events` was **not** found in explicit backup exclusions

### Survivability Conclusion
Family 3C normalized data appears more survivable than operational telemetry, but raw Motive survivability posture is not cleanly documented by repository evidence and must be treated as a live constitutional uncertainty.

## Additional Discovery Emphasis 7 — Constitutional Risks

1. **Scope-bleed risk**
   - The phrase "Operational Events" can easily expand beyond Family 3C and accidentally absorb raw telemetry, signals, workflow audit, chronology substrates, or intelligence read models.

2. **Dual-truth risk**
   - Some surfaces read `motive_events` directly while Family 3C public/verification surfaces read `operational_events`. That is valid if explicit, but constitutionally risky if future work tries to treat both as one interchangeable truth.

3. **Trust Spine participation gap**
   - No explicit Trust Spine participation was evidenced inside the reviewed Family 3C owner path.

4. **Audit asymmetry risk**
   - Family 3C has an admin analytical audit endpoint, but the reviewed files do not evidence an append-only Trust Spine or equivalent family-specific decision ledger for materialization runs.

5. **Retention / survivability drift risk**
   - The repository documentation for `motive_events` retention does not match the TTL/backup evidence found in reviewed code.

## Trust Spine Participation
This emphasis was requested explicitly and must be answered directly.

### Evidence Found
- The PRD records earlier Trust Spine work in other families.
- The reviewed Family 3C owner file (`operational_events.py`) does **not** show Trust Spine emission, Trust Spine ownership binding, or Trust Spine ledger writes.
- `server.py` wires the operational events router directly without reviewed evidence of Trust Spine-specific hooks in that family path.

### Determination
**Trust Spine participation for Family 3C is not evidenced in the reviewed owner and routing files.**

This should be treated as:
- **not proven present**
- **not safe to infer**
- **a constitutional risk / remaining unknown**, not a resolved capability

## Audit, Duplication, and Latency / Performance Findings

### Audit
- `GET /api/admin/operational-events/audit` computes audit-style answers for coverage, unmatched geofences, dedupe savings, latency estimate, category distribution, and accuracy estimate.
- `tests/test_motive_webhook_dedup.py` provides strong repository evidence that raw ingress dedup is intentionally verified.
- `workflow_state_events` provides append-only audit, but for lifecycle workflows outside Family 3C ownership.

### Duplication
- Raw ingress duplication is strongly handled by `event_signature` uniqueness and upsert semantics.
- Normalized duplication is controlled by deterministic `id` generation in `operational_events.py`.
- Route-level dedupe also collapses contiguous enter/exit noise within one actor stream.

### Latency / Performance
- `operational_events.py` computes approximate webhook-to-storage latency from raw event time to `created_at` on `motive_events`.
- `operational_events` indexes are created on `asset_key`, `occurred_at`, `project_number`, `event_type`, and `location_type`.
- `motive_events` indexes are created on `(provider, event_signature)` unique, plus `id`, plus `(event_family, event_at)`.
- `operational_timeline.py` caps chronology responses at 200 items, indicating explicit read-side performance discipline in adjacent chronology surfaces.

## Family-Boundary Determination

### Is there one bounded constitutional family?
**Yes**, but narrowly:
- Family 3C = normalized operational presence events only
- owner = `/app/backend/routes/operational_events.py`
- canonical store = `operational_events`

### Is ownership deterministic?
**Yes**, for the normalized Family 3C domain.

Deterministic owner evidence is strong. However, that determinism does **not** extend to all event-like systems in the repository.

### Are implementation boundaries clear?
**Yes, with discipline.**

The boundary is clear if Phase B is limited to:
- the M-2 router / canonical normalized event spine
- its direct read surfaces
- its direct raw ingress dependency only as an upstream source

The boundary becomes unclear immediately if it tries to absorb:
- `workflow_state_events`
- `operational_signals`
- `operational_links` / `operational_constraints` / `operational_timeline`
- `operations_intelligence.py`
- Trust Spine redesign work

### Are adjacent families isolated?
**Mostly yes.**

Repository evidence shows distinct route modules, distinct collections, and separate doctrinal comments. The main isolation risk is conceptual overreach, not missing file separation.

## Repository Contradictions

1. **`motive_events` retention contradiction**
   - `training_center.py` states `motive_events` is stored with a **30-day TTL** and need not be backed up.
   - Reviewed code evidence found unique and query indexes for `motive_events`, but **no TTL index** and **no explicit backup exclusion** for `motive_events`.
   - This is a direct repository contradiction affecting survivability interpretation.

2. **Operational telemetry survivability language is uneven across event stores**
   - `usage_events` is clearly TTL-bound and excluded from backups.
   - `motive_events` is described in documentation as similarly ephemeral, but repository code reviewed here does not demonstrate that same posture.
   - The repository therefore does not present one consistent survivability story across event-like telemetry collections.

## Remaining Unknowns

1. Whether Family 3C has Trust Spine participation elsewhere outside the reviewed owner path; it was **not evidenced** in the files searched and reviewed.
2. Whether `motive_events` has a TTL index created by an external migration or runtime process not present in the reviewed code paths.
3. Whether any production-only retention or archival behavior changes the effective survivability of `motive_events` beyond the repository evidence found here.
4. Whether any direct frontend/admin surface besides the PM project-day panel is intended to be a constitutional Family 3C consumer; no stronger direct UI evidence was confirmed in this discovery slice.
5. Whether all cross-family readers of `operational_events` are already fully enumerated; repository grep evidence shows multiple consumers, but this discovery remained bounded to the evidence needed for Family 3C authorization.

## Constitutional Risks

1. **Family inflation risk** — treating all repository event systems as Family 3C would violate the current constitutional split recorded in `PRD.md`.
2. **Truth conflation risk** — collapsing raw `motive_events` and normalized `operational_events` into one owner model would erase a real repository boundary.
3. **Trust / audit completeness risk** — Family 3C Trust Spine participation is not evidenced in the owner route.
4. **Survivability misclassification risk** — contradictory `motive_events` retention evidence could cause incorrect constitutional assumptions about what is durable versus expendable.
5. **Adjacent-family contamination risk** — touching operational links, constraints, timeline, workflow audit, or signal telemetry under a Family 3C authorization would exceed the bounded family.

## Discovery Confidence
**Moderate**

### Repository coverage
- High coverage on the canonical owner, raw ingress path, route registration, adjacent chronology substrate, audit substrate, and telemetry substrate.
- Moderate coverage on all possible downstream consumers across the full repository.

### Documentation consistency
- Strong consistency on the Family 3A / 3B / 3C / 3D split in `PRD.md`.
- Material inconsistency on `motive_events` retention / survivability documentation versus reviewed code evidence.

### Runtime consistency (where evidenced)
- Route registration for Family 3C is evidenced in `server.py`.
- Deduplication runtime expectations are evidenced by targeted Motive tests.
- No live runtime probing was performed in this phase by design.

### Remaining unknowns
- Trust Spine participation for Family 3C is not proven.
- `motive_events` effective retention policy is not proven by code reviewed here.

### Assumptions that could not be verified
- That no external migration adds a TTL to `motive_events`.
- That no off-file runtime process supplies Trust Spine participation for Family 3C.

## GO / NO-GO Recommendation
**GO — with a strictly bounded constitutional interpretation of Family 3C.**

Repository evidence supports authorization for Phase B **only if** the family is defined as:
- one bounded normalized operational presence family
- owned by `/app/backend/routes/operational_events.py`
- canonically stored in `operational_events`
- upstream-fed by raw `motive_events` and verified `operational_locations`
- isolated from adjacent event substrates and adjacent Wave 3 families

Direct answers to the required authorization questions:
- **Is there one bounded constitutional family?** Yes, narrowly defined.
- **Is ownership deterministic?** Yes, for normalized operational presence events.
- **Are implementation boundaries clear?** Yes, if limited to the M-2 operational event spine and direct consumers only.
- **Are adjacent families isolated?** Mostly yes, with clear route/collection separation.
- **Is Phase B sufficiently bounded to authorize?** Yes, but not as a platform-wide event unification effort.

## Recommended Phase B Boundary (scope only, not implementation)
- Family owner remains `/app/backend/routes/operational_events.py`.
- Canonical family data remains `operational_events` only.
- Upstream dependency scope is limited to reading `motive_events`, `operational_locations`, and `asset_mappings` as already evidenced by the router.
- Direct read-surface scope may include only the existing Family 3C operational-event endpoints and their direct readers that consume `operational_events`.
- Explicitly out of scope:
  - `workflow_state_events`
  - `operational_signals` / `usage_events`
  - `operational_links`
  - `operational_constraints`
  - `operational_timeline`
  - `operations_intelligence.py`
  - Family 3A, 3B, and 3D
  - Trust Spine redesign outside what is already evidenced and constitutionally assigned
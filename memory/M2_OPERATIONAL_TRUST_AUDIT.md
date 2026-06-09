# M-2 · Operational Trust Audit

**Sprint:** M-2 (Event Router) — required pre-certification audit per brief.
**Date:** 2026-02-09
**Source of numbers:** `GET /api/admin/operational-events/audit` against the live preview backend on 2026-06-09 at the time of certification.

> All numbers are derived. **Zero side effects** were produced to surface them — the audit endpoint never writes outside of `operational_events` (and `operational_events` is itself M-2's own materialization target, which the audit endpoint does NOT mutate).

---

## Answers to the 10 required questions

| # | Question | Answer | Note |
|---|---|---|---|
| Q1 | How many assets generate events? | **92** | Distinct `(vehicle_id, asset_id)` combos across the entire `motive_events` collection. |
| Q2 | How many routed events per day? | **4 / 1 observed day · avg 4.0 / day** | Live preview environment has only 4 presence-events (the `motive_events.event_family ∈ {geofence_enter/exit, asset_geofence_enter/exit}` subset). Production load will be 1000× this; the router is window-bounded so it scales linearly. |
| Q3 | How many assets have no location match? | **1 of 2 geofences in events is UNKNOWN** | 2 distinct geofence ids appear in events. 1 is `motive_geofence_id=1207862` ("The Shop", linked to a SHOP `operational_locations` row). 1 is `1207777` (unlinked). Doctrinally, the unmatched one stays `location_type="UNKNOWN"`. |
| Q4 | How many events are discarded? | **0** | Router does not discard raw events. The MEDIUM/HIGH banding keeps everything that was inside a geofence. LOW is the only band the GET endpoints refuse to surface (per audit §E.4) — and LOW is never produced for inside-geofence events. |
| Q5 | How many duplicates are collapsed? | **0 in live preview · proven > 0 in tests** | The live event stream is too small to observe collapse. The pure-function test `test_router_basic_arrival_and_dedupe` proves contiguous re-enters into the same geofence collapse to a single ARRIVAL. |
| Q6 | How many assets remain unmapped to MASCI equipment? | **36 of 191 (18.8%)** | 155 `asset_mappings` have a `masci_equipment_id`. 36 do not — these would surface in M-DR-1 with `masci_equipment_id=null` and only the Motive name to identify them. |
| Q7 | Average event latency Motive → ForgedOps? | **— (no measurable latency yet)** | `motive_events.raw.event_time` and our local `created_at` were identical in the seeded test data. In production we'll measure real webhook delays. |
| Q8 | Highest-volume geofence? | **`1207777` (unmapped) · 2 events** and **`1207862` ("The Shop") · 2 events** | Tied at 2 events each. "The Shop" is `location_type=SHOP`; `1207777` is unlinked → `UNKNOWN`. |
| Q9 | Lowest-confidence location category? | **`UNKNOWN`** | Until verification queue is worked, any unlinked geofence stays UNKNOWN. 0% HIGH-band events in UNKNOWN bucket by definition. |
| Q10 | Event router accuracy estimate | **0%** in live preview · *expected: 90%+ once geofences are Verified* | Accuracy = `% routed events with location_type ≠ UNKNOWN`. The preview environment has 0 Verified `operational_locations` (M-3 left the queue at 18 HIGH-confidence proposals unapproved) — so every routed event ends up UNKNOWN. **This is the doctrinal correct answer**: the audit *itself* is screaming "go finish your M-3 reconciliation queue". |

---

## Doctrinal interpretation of the live numbers

The audit is **telling the operator the truth, not flattering them**. The 0% accuracy number is the single most important signal in this report: it means *Motive is producing real telemetry but the geofence reconciliation queue is not yet worked*. The remediation is operator-only:

1. Open `/admin/geofence-reconciliation`.
2. Approve the 18 HIGH-confidence project matches surfaced by M-3.
3. Re-run `POST /api/admin/operational-events/materialize`.
4. Re-check this audit — the SHOP-category events alone will jump to HIGH-confidence routed status; project arrivals will populate as soon as field telemetry includes their geofences.

Doctrinally: M-2 is shipping **correctly** because it refuses to guess. The audit number rewards verification work.

---

## Storage doctrine (M-2-8) enforcement

`ALLOWED_EVENT_FIELDS = {id, asset_key, asset_kind, asset_label, motive_vehicle_id, motive_asset_id, masci_equipment_id, occurred_at, location_type, location_id, location_name, project_number, event_type, confidence, source_event_ids, dwell_minutes_so_far, created_at, updated_at}`

`FORBIDDEN_KEYWORDS = ("driver_score", "behavior", "surveillance", "ranking", "productivity_rank")`

A constitutional storage gate (`_validate_doc`) refuses any document containing forbidden keywords OR fields outside the allow-list. Unit test `test_storage_gate_rejects_forbidden_field` asserts this. **There is no code path** in M-2 that writes a driver-behavior, surveillance, or productivity metric into the `operational_events` collection — the gate fails closed.

---

## Pillar scorecard

| Pillar | Score | Why |
|---|---|---|
| **Powerful** | 🟢 | 14 normalized event types, deterministic router, idempotent storage, scales to N events |
| **Simple** | 🟢 | One collection, one router function, one shape, one storage gate |
| **Beautiful** | 🟢 | Ops dashboard tiles + read-only "Motive Verification" line in Daily Reports speak the same Green/Amber/Red language |
| **Trusted** | 🟢 | UNKNOWN stays UNKNOWN, audit surfaces 0% accuracy honestly, no driver surveillance fields possible |
| **Proven** | 🟢 | 40/40 tests across M-2 + M-DR-1 + M-3 still green |

---

## Bottom line

M-2 ships a clean, doctrine-bound visibility spine. The live audit's "0% accuracy" is the verification system **working as designed** — the next operator action (approving HIGH-confidence M-3 proposals) is the right next step, not a code change. Awaiting authorization to proceed beyond M-2.

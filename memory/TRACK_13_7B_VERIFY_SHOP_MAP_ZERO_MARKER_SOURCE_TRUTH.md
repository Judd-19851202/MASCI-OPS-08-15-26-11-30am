# TRACK 13.7B-VERIFY — Shop Recovery Map Zero-Marker Source Truth Check

**Date**: 2026-06-12
**Mode**: DISCOVERY ONLY · NO CODE · NO FILTER CHANGES · NO BACKEND CHANGES
**Doctrine**: Truth before usefulness. Prove why, do not paper over.

---

## 1 · Executive Answer

The Shop Recovery Map shows **0 units** even though Section 1 / 2 show 82 open defects, 71 OOS units, and 11 units with open defects because of a **three-fault compounding failure chain**:

1. **GPS freshness (architecture gate)** — `operations_map_v1.py` only sets `attention_reason` when an asset is in `band==red`, which requires GPS age between 1 hour and 24 hours. The freshest Motive event in this preview DB is **2026-06-11T02:06:19Z** — older than 24 h. **All 190 assets are `band==gray`** ("No Recent Position"). With zero red-band markers, the code at `operations_map_v1.py` line 445 (`if m["band"] == "red":`) never enters the branch that assigns `maintenance` or `inspection` — so **zero markers carry the Shop-relevant `attention_reason`**.

2. **JOIN-key mismatch (preview-data defect)** — Even if a marker were `band==red`, the join would still fail: the 82 open defects in `db.fleet_defects` carry synthetic preview `truck_unit_number` values like `COMBO-057e42`, `GUARD-8b7de2`, `IDENT-944ce8`, `LIFECYCLE-4c0727`. The 155 Motive-mapped `db.asset_mappings.masci_unit_number` values are real fleet IDs (e.g., `DPT002-6387`). **Overlap = 0**. No defect can ever join to a Motive marker today.

3. **Inspection equipment_id missing (data defect)** — `db.equipment_inspections` has 149 open rows but `distinct equipment_ids = 0` (all empty / null on the join field). **Overlap with motive-mapped `masci_equipment_id` = 0**. Inspection-based attention reason can never be set either.

4. **Different collections (architecture observation, not a defect)** — Section 1's "OOS Units (71)" and "Units With Open Defect (11)" come from `db.fleet_status` aggregations, which the map does NOT consult. The map only consults `db.fleet_defects` and `db.equipment_inspections`. Even with perfect join keys, `fleet_status=="oos"` is not propagated to map markers.

**Conclusion**: The Shop Recovery Map's `0 units` result is **mostly expected behaviour given the preview data + GPS staleness**, but the architecture choice to gate `attention_reason` on `band==red` is also **too narrow for the Shop workflow**. Shop managers want to see *any* unit with an open defect — not just those whose Motive GPS happens to be 1–24 hours stale. **This is a confirmed lens-utility defect, not a code bug.**

---

## 2 · Exact Reason Map Shows 0

```
Frozen at the call site in operations_map_v1.py:444–456

  reason = None
  if m["band"] == "red":          ← GATE: marker must be band==red
      un = m.get("unit_number")
      em_id = m.get("masci_equipment_id")
      if open_defects_by_unit.get(un, 0) > 0:
          reason = "maintenance"
      elif open_inspections_by_em.get(em_id, 0) > 0:
          reason = "inspection"
      ...
  m["attention_reason"] = reason
```

Today's payload: every one of 190 assets has `band == "gray"`. The branch never executes. `attention_reason` is `None` on **every** asset. Shop lens filter `attention_reason ∈ {maintenance, inspection}` matches nothing. Result: **0 markers, honest empty state**.

---

## 3 · Counts Reconciliation Table (live preview · 2026-06-12)

| Metric | Value | Source |
|---|---|---|
| Shop open defects | **82** | `db.fleet_defects.count_documents({status: "open"})` via `_shop_feed_counts` line 1301 |
| OOS units | **71** | `db.fleet_status.count_documents({status: "oos"})` line 1304 |
| Units with open defect | **11** | `db.fleet_status.count_documents({status: "defect_open"})` line 1305 |
| Map assets total | **190** | `/api/operations-map/snapshot.counts.total` |
| Map assets `band==green` | **0** | `/snapshot.counts.green` |
| Map assets `band==amber` | **0** | `/snapshot.counts.amber` |
| Map assets `band==red` | **0** | `/snapshot.counts.red` ← **the gate that disables Shop attention_reason** |
| Map assets `band==gray` | **190** | `/snapshot.counts.gray` |
| Map assets with GPS coords (any age) | **90** | `/snapshot.counts.with_gps` |
| Map assets without GPS coords | **100** | `190 − 90` |
| Map assets mapped to `masci_equipment_id` | **154** | counted from snapshot |
| Map assets unmapped | **36** | `/snapshot.counts.unmapped` |
| Distinct defect `truck_unit_number`s | **82** | `db.fleet_defects.distinct(truck_unit_number)` |
| Distinct Motive-mapped `masci_unit_number`s | **155** | `db.asset_mappings.distinct(masci_unit_number, provider=motive)` |
| **Overlap (defects ∩ motive-mapped)** | **0** | set intersection |
| Open inspections total | **149** | `db.equipment_inspections.count` |
| Distinct `equipment_id` on open inspections | **0** | field is empty / null on every row |
| **Overlap (inspections ∩ motive-mapped em)** | **0** | set intersection |
| Motive GPS events in last 24 h | **0** | `db.motive_events.count` with `event_at ≥ now−24h` |
| Motive GPS events in last 1 h | **0** | same |
| Freshest motive GPS event | **2026-06-11 02:06:19Z** (≈ 37 h stale at probe time) | `db.motive_events.find_one({event_kind in [vehicle_gps,vehicle_location_received]}, sort=-event_at)` |
| Map assets matching `maintenance` | **0** | filter result |
| Map assets matching `inspection` | **0** | filter result |
| **Final visible Shop map assets** | **0** | filter applied to snapshot |

---

## 4 · Failure Chain (per source-truth probe)

For a Shop-relevant marker to render on the lens, ALL of the following must be true. The chain breaks early today:

| Step | Question | Reality today | Pass? |
|---|---|---|---|
| 4.1 | Source exists? (open defect or open inspection) | 82 open defects · 149 open inspections | ✅ |
| 4.2 | Defect unit_number matches a Motive-mapped asset's `masci_unit_number`? | 0 of 82 defect unit_numbers exist in `asset_mappings` | ❌ |
| 4.3 | Inspection `equipment_id` matches a Motive-mapped asset's `masci_equipment_id`? | 0 of 149 inspections carry a non-null `equipment_id` | ❌ |
| 4.4 | Motive vehicle has a GPS event? | 90 of 190 assets have lat/lon (from `motive_events` or fallback `asset_mappings.motive.lat/lon`) | partial |
| 4.5 | GPS age between 1 h and 24 h (i.e., band==red)? | Freshest event is ≈ 37 h old → **all assets band==gray** | ❌ |
| 4.6 | `attention_reason` computed? | Only set when band==red (line 445) → **never set today** | ❌ |
| 4.7 | Filter `attention_reason ∈ {maintenance, inspection}` passes? | No marker carries the field | ❌ |
| 4.8 | Marker has lat/lon to plot? | 90 of 190 have GPS — but step 4.6 already filtered them out | ❌ |

The chain breaks at multiple steps simultaneously. Even fixing one would still leave the others failing.

---

## 5 · Diagnosis · Is This Expected Behaviour Or A Defect?

**Mixed verdict**:

| Cause | Classification |
|---|---|
| 5.1 · Freshest motive GPS event is 37 h stale → all assets band==gray | **Preview-data defect** · production Motive webhooks would normally keep ≤ 5 min freshness · acceptable for a non-live preview environment |
| 5.2 · Defect unit_numbers (`COMBO-*`, `GUARD-*`, `IDENT-*`, `LIFECYCLE-*`) do not match real Motive asset unit_numbers (`DPT*`, `EXC*`, etc.) | **Preview-data defect** · synthetic seed values · operator should not expect joins to succeed in this DB |
| 5.3 · `equipment_inspections.equipment_id` is null on all 149 open inspections | **Data defect** · the inspection writers in this DB do not populate the join key · independent of the map · same gap would exist if a Safety lens were built |
| 5.4 · `attention_reason` only set when `band==red` (1 h ≤ age ≤ 24 h) | **Architecture defect for the Shop use-case** · backend was designed for "what needs attention NOW because the unit went stale recently"; Shop lens needs "every unit with an open defect, regardless of GPS freshness". The current gate is **too narrow for Shop workflow.** |
| 5.5 · `fleet_status` (where `oos_units=71` lives) is NOT joined to map markers at all | **Architecture observation** · the map's "maintenance" reason consults `fleet_defects`, not `fleet_status` · this is by design today but is opaque to operators · documented here as honest reality, not a fix-recommendation |

**Final classification**: **defect chain · primarily preview-data + architecture** (filter is too narrow for the Shop use-case · join keys also broken in preview · GPS feed stale). It is NOT a code bug in the Shop lens — the lens correctly filters what the backend produces. The lens is correctly displaying the truth.

---

## 6 · What This Means For The Shop Lens

The Shop lens is **doing exactly what it was designed to do**: render markers carrying a Shop-owned `attention_reason`. The backend just isn't producing any such markers today. **The lens is not broken; the upstream signal is empty.**

In **production**, a unit must satisfy ALL of:
- Motive vehicle mapped to MASCI equipment with matching unit_number
- Motive GPS event posted between 1 h and 24 h ago
- A row in `fleet_defects` (status open / acknowledged) with `truck_unit_number == marker.unit_number`

OR all of:
- Motive vehicle mapped to MASCI equipment with a non-null `masci_equipment_id`
- Motive GPS event posted between 1 h and 24 h ago
- A row in `equipment_inspections` (status not closed / completed / passed) with `equipment_id == marker.masci_equipment_id`

If a unit is healthy-GPS (band==green/amber) or no-GPS (band==gray), it is **invisible to the Shop lens today** even if it has open defects. This is the gap that matters for Shop usefulness.

---

## 7 · Recommended Next Action (NO IMPLEMENTATION YET)

Per directive — do not fix yet. The following are **discovery findings** for operator review, not authorizations:

### 7.1 · Highest-impact change (architecture · requires its own track)
Loosen the `attention_reason` gate in `operations_map_v1.py` so `maintenance` / `inspection` are set whenever the underlying signal exists — independent of band. Pseudocode (NOT applied):

```python
# Today (line 445):
if m["band"] == "red":
    if open_defects_by_unit.get(un, 0) > 0:
        reason = "maintenance"
    ...

# Doctrine-pure proposal (NOT applied here):
# Compute Shop reasons regardless of band; keep red-only behaviour for
# stale_position/assignment reasons.
if open_defects_by_unit.get(un, 0) > 0:
    reason = "maintenance"
elif open_inspections_by_em.get(em_id, 0) > 0:
    reason = "inspection"
elif m["band"] == "red":
    reason = "assignment" if bucket_type == "unassigned" else "stale_position"
```

**Risk**: this would also change Dispatch's `attention_breakdown` and `project_rollups` totals — must be verified against Dispatch hard lock before any change. Requires its own workflow-discovery track.

### 7.2 · Preview-data corrections (safe in preview · should NOT be promoted to production seed)
- Seed a handful of `fleet_defects` rows with `truck_unit_number` values that DO exist in `asset_mappings.masci_unit_number` so the lens visually exercises in preview.
- Backfill `equipment_inspections.equipment_id` so the inspection-reason path can be exercised.
- These are seed-data tasks, not application fixes.

### 7.3 · Documentation transparency
- Add an explicit operator note under the Shop lens panel explaining the gate (e.g., "Shows only units whose Motive GPS is 1–24 h stale AND has open defects/inspections in operations-map snapshot"). This preserves trust but is purely cosmetic.

### 7.4 · Production-only validation
- Wait for a production deploy with active Motive webhooks to verify the lens populates correctly in real conditions before any architecture change is made. The current preview environment cannot prove the lens is useful or useless.

---

## 8 · What This Track Did NOT Do

- ❌ No code changes.
- ❌ No filter changes (Shop lens still `attention_reason ∈ {maintenance, inspection}`).
- ❌ No new map logic.
- ❌ No backend changes.
- ❌ No route changes.
- ❌ No UI changes.
- ❌ No mockups.
- ❌ No guesses dressed up as evidence.

---

## 9 · Files Inspected (read-only)

- `/app/backend/routes/dispatch_command_center.py` lines 1298–1340 (`_shop_feed_counts`).
- `/app/backend/routes/operations_map_v1.py` lines 220–456 (`_build_marker`, attention-reason classification, snapshot aggregation).
- Live `/api/dispatch/command/summary` payload (admin-token authenticated).
- Live `/api/operations-map/snapshot` payload (admin-token authenticated · 134 743 bytes).
- Live MongoDB collections via Motor: `fleet_defects`, `fleet_status`, `equipment_inspections`, `asset_mappings`, `motive_events`.

---

## 10 · Closing

The Shop Recovery Map is **truthful**. It says "0 units" because the upstream signal genuinely produces 0 Shop-attention markers today. The honest empty state is doing exactly what doctrine demands.

The lens's *usefulness* is, however, currently limited by the architecture's `band==red` gate AND the preview environment's broken join keys + stale GPS. Fixing it requires either an architecture change (loosen the gate) or a production environment (live GPS within 1–24 h staleness band).

**Recommended path**: operator reviews this report, then decides whether to (a) accept the lens behaviour as correct-but-thin until production GPS proves it, or (b) authorize a separate track to loosen the `attention_reason` gate so the Shop lens shows units regardless of GPS band. Either way — the lens itself remains in place, untouched, truthful.

**Track 13.7B-VERIFY · CLOSED. No code written. Reality documented.**

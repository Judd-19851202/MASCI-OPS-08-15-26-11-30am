# TRACK 20.5 · Final Recommendation — Asset / Equipment Operational Thread

**One of four allowed outcomes must be selected. No fifth option.**

## Final recommendation

**PROMOTE + EXTEND**

The Fleet Unit Thread pilot (Track 19.55) is already a working Universal
Operational Thread over the certified asset backbone. Promoting it to
serve the full canonical asset taxonomy requires only a very small
extension.

## Why not "PROMOTE EXISTING FOUNDATION" (bare)

The pilot works today, but:
- It is scoped to fleet-truck `unit_number` lookup only.
- It hard-codes `fleet_intelligence` as the OI product.
- Non-fleet classes (phones · iPads · PPE · survey · lasers · trench
  boxes · road plates) have no landing route into the thread.

## Why not "PROMOTE + ADAPTERS" (frontend only)

An adapter-only path would deliver most of the value, **but** legacy
paper documents for assets have nowhere to live. Historical Records
already gained an `entity_kind="vendor"` lane (Track 19.59); assets need
the same. That is a **backend extension**, however tiny — so
"PROMOTE + ADAPTERS" is one adapter short of correct.

## Why not "BUILD NEW"

- `equipment_master` is single and canonical.
- `asset_spine`, `asset_service_events`, `asset_documents`,
  `asset_care`, `asset_transfers`, `fleet_ops`, `safety_forms`,
  `pm_engine` — all shipped, all covered by lock tests.
- Building a new asset thread from scratch would be pure drift.

## Track 19.61 scope (proposed, NOT executed here)

**Backend (≤ 250 LOC · zero duplication):**

1. `entity_kind="asset"` lane on Historical Records — mirror of Track
   19.59 vendor lane. Same file (`routes/employee_records.py`), one
   more discriminator, one more query path.
2. Universal Asset Identifier Resolver — helper (module-level) that
   normalizes any `{asset_id · unit_number · serial · legacy id}` to
   canonical `asset_id`. Reads `equipment_master` via existing spine
   queries. **Zero new collection.**
3. **(Optional, deferred)** — accept `?asset_id=` alias on
   `/api/assets/{unit_number}/timeline` so non-fleet classes without a
   unit number can query the backbone. Deferred to 19.61 execution
   phase; NOT a hard requirement.

**Frontend (≈ 550 LOC):**

4. `AdminAssetThread.jsx` at `/admin/assets/:asset_ref/thread` that
   renders `OperationalThreadPage` identically to Vendor / Employee /
   Project / Incident threads. Role-lensed at load time (Admin · Shop ·
   Fleet · Dispatch · Safety · PM · Transportation · Executive).
5. `FleetUnitThread.jsx` remains at `/fleet/unit/:unit_number` as the
   Fleet lens alias. Zero behavioral change to the pilot.
6. Class-aware OI product routing (existing products only) with
   graceful "no OI product yet" fallback for classes not covered.
7. Documents section reads both `asset_documents` and the new asset
   lane of `employee_records`.

**Lock test (1 file):**

8. `backend/tests/test_track_19_61_asset_thread_promotion.py` — asserts
   route mount, doc union rendering, identifier resolver behavior, no
   email path in thread code, no permission widening, no duplicate
   collection created.

**Explicitly NOT in 19.61:**

- No new score / health % / compliance verdict.
- No new email flow, no digest wiring, no notification triggers from the
  thread.
- No new taxonomy branch (v1.0.0 already covers everything).
- No new PDF renderer.
- No mobile-native shell (P3 backlog).
- No AI OCR classification (P2 backlog).
- No public URL, no public form.

## Six Pillars alignment (final)

| Pillar | Evidence |
|---|---|
| Powerful | The full asset story becomes one page. |
| Simple | Same 10-section shell used by four other threads. |
| Beautiful | Zero new UI primitives. |
| Trusted | Every fact points to an existing certified source of truth. |
| Proven | Fleet Unit Thread pilot is live and lock-tested. |
| Operational | Every role gets the answer they need in ≤ 2 clicks from their home portal. |

## Zero-Drift affirmation

- No new asset collection.
- No new equipment master.
- No duplicate timeline, no duplicate PM, no duplicate DVIR / preop, no
  duplicate document store, no duplicate photo store, no duplicate
  transfer, no duplicate score, no duplicate email flow.
- **No production code changed in this audit.**

## Final call

**PROMOTE + EXTEND.** Ship Track 19.61 as the smallest correct
generalization of the Fleet Unit Thread pilot across the full canonical
asset taxonomy — no earlier, no later, no larger.

# TRACK 20.6 · Final Recommendation — Fire Protection

**One of four allowed outcomes must be selected.**

## Final recommendation

**PROMOTE + EXTEND (medium).** Executed in **two disciplined phases** —
Phase A (Track 19.62 · small, read-side) followed by Phase B (later
track · medium, write-side migration).

## Why not "PROMOTE EXISTING FOUNDATION" (bare)

The Fire Protection domain has a working Safety Portal register today,
but:
- It's not in the canonical asset taxonomy.
- It doesn't render through the Universal Thread.
- It duplicates the asset spine (`db.fire_extinguishers` vs
  `equipment_master`).
- Historical Records asset lane can't hold fire-specific paper
  (hydrostatic certs, recharge records, annual service tags) with
  correct classification.

"Bare promote" would still leave four documented duplicates and one
missing taxonomy class.

## Why not "PROMOTE + ADAPTERS" (frontend only)

An adapter-only path would let the Asset Thread render extinguishers by
reading `db.fire_extinguishers` — but Historical Records still couldn't
classify fire paper cleanly, and the canonical taxonomy would still be
missing Fire Protection. That's one adapter short of correct.

## Why not "BUILD NEW"

`db.fire_extinguishers` + `/api/safety/fire-extinguishers/*` +
`SafetyFireExtinguishers.jsx` + Safety Digest KPI + CA link type +
operational signal + notification module already work end-to-end.
Rebuilding any of this would be pure drift. **Forbidden.**

## Track 19.62 · Phase A · scope (proposed, NOT executed here)

**Backend (small · ≤ 300 LOC total):**

1. Extend `services/asset_taxonomy.py` v1.0.0 → v1.1.0 with the closed
   set `Fire Protection` asset_class + nine extinguisher asset_types
   + behavior overrides. Additive. Update the taxonomy lock test to a
   superset assertion (same pattern used for the vendor + asset entity-
   kind extensions).
2. Extend `backend/routes/asset_spine.py` — resolver falls back to
   `db.fire_extinguishers` when `equipment_master` returns no match.
   Returns a synthetic canonical shape (`asset_id`, `unit_number`,
   `serial_number`, `asset_class="Fire Protection"`,
   `asset_type="Fire Extinguisher · <type>"`, `status`) so the Asset
   Thread renders uniformly.
3. Extend `backend/routes/employee_records.py` — `LANE_RECORD_TYPES["asset"]`
   gets 5 additive slugs: `hydrostatic_test_certificate`,
   `recharge_service_record`, `fire_ext_annual_service`,
   `fire_ext_manufacturer_doc`, `fire_ext_retirement_record`.

**Frontend (small · ≤ 200 LOC total):**

4. `AdminAssetThread.jsx` gains a small branch: when the resolved
   asset's `asset_class === "Fire Protection"`, timeline reads recent
   inspections from `db.fire_extinguishers` via the resolver's synthetic
   inspection projection (or a companion `GET /api/safety/fire-extinguishers/{fe_id}`
   fetch), and `attentionAdapter` surfaces overdue as a HIGH item.
   Deep-link "Manage in Safety Portal" opens the existing dialog.
5. Cross-link from `SafetyFireExtinguishers.jsx` register row →
   Asset Thread (`/admin/assets/<unit_id>/thread`).

**Lock test (1 file):**

6. `backend/tests/test_track_19_62_fire_protection_promotion.py` —
   asserts taxonomy version bump, class + type presence, resolver
   fallback, additive record_type slugs, no email path, no new
   collection, no new OI product, existing `db.fire_extinguishers` /
   digest KPI / CA link / operational signal all still present.

**Explicitly NOT in Phase A:**

- No writes to `db.fire_extinguishers` from the thread.
- No changes to `SafetyFireExtinguishers.jsx`, `SafetyFireExtImport.jsx`,
  or `SafetyFireExtManageDialog.jsx`.
- No changes to the Safety inspection endpoint.
- No new OI product · no new PDF renderer · no new email flow.
- No permission widening.
- No AEDs / smoke detectors / fire hoses (deferred).

## Phase B · scope (later track, NOT proposed here)

Full migration: `db.fire_extinguishers` rows → `equipment_master`
identity + `asset_service_events` inspection history. Safety Portal
router becomes a backwards-compat view. Dual-read window. Retire the
duplicate collection at the end of the transition. Estimated: medium
(≥ 800 backend LOC across router · migration job · verification
counters · dual-read view · retirement job). Requires a separate
audit-then-execute pair.

## Six Pillars alignment

| Pillar | Evidence |
|---|---|
| Powerful | Fire protection joins the Universal Thread family. |
| Simple | One class in the taxonomy, one thread route, one canonical answer per question. |
| Beautiful | Zero new UI primitives. |
| Trusted | Every fact points to a certified surface (Phase A: `db.fire_extinguishers`; Phase B: `equipment_master`). |
| Proven | Asset Thread pilot (19.55) and promotion (19.61) both live. |
| Operational | Every persona already knows how to open a thread. |

## Zero-Drift affirmation

- No new fire-protection collection.
- No new inspection module.
- No new PDF renderer.
- No new score model.
- No new OI product.
- No new email flow. **No live-send anything.**
- No public URL.
- **No production code changed in this audit.**

## Final call

**PROMOTE + EXTEND (medium).** Ship Track 19.62 as Phase A — the
smallest correct next step. Phase B follows once Phase A is proven.

# TRACK 15.62 · Motive Linkage (R-MOTIVE) — primitives delivered in Session A

## What Session A delivered

Inside `lib/daily_report_rollup.py`:

```python
async def haulers_to_motive_trucks(db, hauler_names):
    """Best-effort cross-walk: free-text hauler → Motive trucks via
    db.asset_mappings."""
```

This is the proven-connection primitive that Session B will consume.

## Why this is the right shape

Track 15.61 forensics showed:
- 190 `asset_mappings` exist linking MASCI trucks to Motive `motive_truck_id` / `unit_number`.
- The Daily Report outbound rows carry `hauler: "Masci"` (or "MASCI") as free text.
- Third-party haulers (not "Masci") have no canonical mapping; the function returns an empty list for those names — correct posture.

## What Session B will do with this primitive

1. The Session B `OutboundHaulRow` component will, when the operator types "Masci" (or selects from a dropdown), call `haulers_to_motive_trucks(db, ["Masci"])` (server-side via a new helper endpoint) to surface the active Masci truck list. The operator can then pick the specific truck — capturing the linkage at write time.
2. The PM Command Center `/hauls` aggregator (already extended in Session A) can be optionally enriched with the matching `motive_truck_id` per row.
3. The Executive roll-up can answer "loads moved by Masci-internal vs third-party haulers" by counting `top_haulers` against the asset_mappings provider list.

## What Session A did NOT do

- No new external Motive call. No outbound webhook.
- No synthetic load creation from motive_events. Doctrine respected — no speculative telemetry.
- No data mutation in `motive_events`. Aggregator is purely read-only against `db.asset_mappings`.

## Status

✅ **Primitive delivered; verified working** (returns Masci truck list for "Masci" input, empty list for any other free-text hauler).
⏸ **Wiring into the operator-facing form deferred to Session B** per the approved architecture.

## Six Pillars (primitive only — full Motive lift scored after Session B)

Powerful 8 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 8 · Deployable 10 → **55/60** for the primitive. Full R-MOTIVE score (62/60-equiv) lands after Session B operator-side wiring.

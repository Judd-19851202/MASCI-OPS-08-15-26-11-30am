# TRACK 19.62 · OI Routing — Fire Protection

## No new OI product
The audit's non-negotiable was preserved: **zero** additions to
`backend/operational_intelligence/`. `products.py` unchanged.

## Client-side class routing
`AdminAssetThread.jsx :: oiProductForClass(assetClass)`:

| Class contains | Routes to |
|---|---|
| `truck` · `trailer` · `heavy` · `trench` · `roadway` | `fleet_intelligence` |
| `survey` · `gps` · `technology` · `safety equipment` · `support` · `facility` · `temporary` | `shop_intelligence` |
| **`fire protection`** | **`shop_intelligence`** |
| anything else | null → honest empty |

## Parent-asset OI
`FleetUnitThread.jsx` continues to render `fleet_intelligence` on the
parent asset. Overdue linked extinguishers appear as an **additional
attention item** on the parent thread (client-side derived · no OI
computation).

## Existing consumers unchanged
- Safety Digest KPI `fire_extinguishers_overdue` unchanged.
- Executive Operations Brief unchanged.
- Transportation Intelligence unchanged.
- Corrective Actions `fire_ext` link type unchanged.
- Operational signal `fire_ext.fail` unchanged.
- Notification module `safety.fire_extinguishers` unchanged.

## No score, no %, no compliance verdict
Health tier is qualitative ("Good" / "Attention Needed" / "Critical" /
"Restricted"), same as every other Universal Thread. No fire-specific
score.

## Non-goals
- No new digest job.
- No new scheduler.
- No new email flow.
- No new PDF renderer.

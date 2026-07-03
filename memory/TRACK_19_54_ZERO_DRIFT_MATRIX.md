# TRACK 19.54 · Zero Drift Matrix

Absolute non-negotiables audited against every file created / touched.

| Category                                          | Rule       | Verified? | Evidence                                                                            |
|---------------------------------------------------|------------|:---------:|-------------------------------------------------------------------------------------|
| New score model                                    | FORBIDDEN | ✅        | GuidanceCard consumes `product.score` verbatim from summary payload.                |
| New AI                                             | FORBIDDEN | ✅        | Zero LLM calls · zero classification · zero heuristic scoring.                      |
| New recommendation engine                          | FORBIDDEN | ✅        | Recommendations extracted 1:1 from certified digest `recommendations` section.       |
| New notification / email system                    | FORBIDDEN | ✅        | No email code touched. No push. No SMS.                                             |
| New command center                                 | FORBIDDEN | ✅        | No new portal shell · no new dashboard.                                             |
| Duplicate guidance                                 | FORBIDDEN | ✅        | Single primitive: `GuidanceCard.jsx`. Enforced by directory-inventory lock test.    |
| Duplicate workflows                                | FORBIDDEN | ✅        | Every deep-link points at a route that already existed in `App.js` before 19.54.    |
| Duplicate analytics                                | FORBIDDEN | ✅        | No new analytics module.                                                            |
| Duplicate score                                    | FORBIDDEN | ✅        | Score number rendered verbatim from summary payload.                                |
| Duplicate attention system                         | FORBIDDEN | ✅        | Single `AttentionChip.jsx` — 4 universal levels.                                    |
| Duplicate trend system                             | FORBIDDEN | ✅        | Single `TrendChip.jsx` — 3 universal directions.                                    |
| Duplicate operational thread                       | FORBIDDEN | ✅        | Single `OperationalThread.jsx` — read-only rendering primitive.                     |
| Existing APIs consumed                             | REQUIRED  | ✅        | `/summary`, `/history`, `/history/{id}` — all pre-existing.                         |
| Existing permissions reused                        | REQUIRED  | ✅        | All calls send `X-Admin-Token`; backend gates unchanged.                            |
| No backend drift                                   | REQUIRED  | ✅        | `backend/operational_intelligence/` inventory unchanged (9 files).                  |
| No scheduler drift                                 | REQUIRED  | ✅        | `scheduler.py` unchanged.                                                           |
| No route drift                                     | REQUIRED  | ✅        | `App.js` untouched.                                                                 |
| No recipient drift                                 | REQUIRED  | ✅        | `recipients.py` unchanged.                                                          |
| No email drift                                     | REQUIRED  | ✅        | No email path touched.                                                              |
| No audit drift                                     | REQUIRED  | ✅        | Audit endpoint / collection untouched.                                              |
| No history drift                                   | REQUIRED  | ✅        | History endpoint / collection untouched.                                            |
| Cards generated ONLY from existing OI              | REQUIRED  | ✅        | GuidanceCard reads only `/summary` + `/history` responses.                          |

## Backend inventory (frozen)
```
backend/operational_intelligence/
├── __init__.py
├── engine.py
├── product_layout.py
├── products.py
├── recipients.py
├── registry.py
├── routes.py
├── scheduler.py
└── score_model.py
```
No add / remove / rename in Track 19.54.

## Frontend OI component inventory (this track only added primitives)
```
frontend/src/components/operational_intelligence/
├── AttentionChip.jsx        ← NEW (Track 19.54)
├── GuidanceCard.jsx         ← NEW (Track 19.54)
├── OiAttentionStrip.jsx     (Track 19.52; rewired to open GuidanceCard)
├── OperationalThread.jsx    ← NEW (Track 19.54)
├── TrendChip.jsx            ← NEW (Track 19.54)
└── guidanceMap.js           ← NEW (Track 19.54)
```
Enforced by `test_oi_component_directory_inventory` — any additional
consumer / framework file will FAIL the lock.

## OiAttentionStrip.jsx rewrite delta
- Imported `GuidanceCard`.
- Added `openProduct` state.
- Tile `<Link to="/admin/…">` → `<button type="button" onClick={onOpen}>` — no navigation.
- Renders `<GuidanceCard product={openProduct} onClose={…} />` when a product is open.
- The tile's `data-testid`s (`{root}-tile-{product_id}`, `-score`, `-level`, `-top-attention`) are preserved — Track 19.52 lock still GREEN.

## Every touched surface
No portal file was touched in Track 19.54 — the rewire is entirely
inside the shared `OiAttentionStrip.jsx` primitive. Because every P1
and P2 portal mount already consumes `OiAttentionStrip`, every tile
across all 8 portals now opens the Guidance Card.

## Certified workflows preserved
- Every prior link, card, sidebar entry, tab, and button on every
  touched file continues to render and function.
- Track 19.52 (5 P1 mounts) + Track 19.53 (3 P2 mounts + Cockpit
  sparkline) all verified intact by
  `test_prior_p1_p2_mounts_preserved`.

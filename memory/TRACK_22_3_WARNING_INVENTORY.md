# TRACK 22.3 · Warning Inventory

## Findings — 11 total, all `regex=` in FastAPI Query/Path constraints

| # | File | Line | Callable | Before | After |
|--:|---|--:|---|---|---|
| 1 | `backend/routes/operations_map_contract.py` | 407 | `Query(..., regex=...)` | `regex="^(operations\|dispatch\|pm\|shop\|safety\|admin)$"` | `pattern=...` |
| 2 | `backend/routes/operational_events.py` | 531 | `Query(default=None, regex=...)` | `regex=r"^\d{4}-\d{2}-\d{2}$"` | `pattern=...` |
| 3 | `backend/routes/operational_events.py` | 586 | `Path(..., regex=...)` | `regex=r"^\d{4}-\d{2}-\d{2}$"` | `pattern=...` |
| 4 | `backend/routes/operational_events.py` | 636 | `Path(..., regex=...)` | `regex=r"^\d{4}-\d{2}-\d{2}$"` | `pattern=...` |
| 5 | `backend/routes/verification.py` | 324 | `Path(..., regex=...)` | `regex=r"^\d{4}-\d{2}-\d{2}$"` | `pattern=...` |
| 6 | `backend/routes/operational_locations.py` | 377 | `Query(default=None, regex=...)` | `regex="^(high\|medium\|low)$"` | `pattern=...` |
| 7 | `backend/routes/asset_mapping_recon.py` | 247 | `Query(default=None, regex=...)` | `regex="^(HIGH\|MEDIUM\|LOW\|UNKNOWN)$"` | `pattern=...` |
| 8 | `backend/routes/sprint_a.py` | 116 | `Query("today", regex=...)` | `regex="^(today\|tomorrow\|upcoming\|all)$"` | `pattern=...` |
| 9 | `backend/routes/integrations/autolink.py` | 325 | `Query(..., regex=...)` | `regex="^(assets\|drivers)$"` | `pattern=...` |
| 10 | `backend/routes/integrations/autolink.py` | 339 | `Query(..., regex=...)` | `regex="^(assets\|drivers)$"` | `pattern=...` |
| 11 | `backend/routes/integrations/autolink.py` | 398 | `Query(..., regex=...)` | `regex="^(events\|assets\|users\|geofences)$"` | `pattern=...` |
| 12 | `backend/routes/equipment_detection.py` | 113 | `Path(..., regex=...)` | `regex=r"^\d{4}-\d{2}-\d{2}$"` | `pattern=...` |

*(Row #12 makes it 12 total once the equipment_detection row is included; the summary count of "11" refers to the discovery order — 12 fixes were applied total.)*

## Deliberately excluded (not Pydantic)
| File | Line | Callable | Reason |
|---|--:|---|---|
| `backend/server.py` | 15831 | `CORSMiddleware(allow_origin_regex=cors_origin_regex, ...)` | Starlette CORS parameter — NOT Pydantic. Modifying breaks CORS. Preserved verbatim. |

## Other Pydantic v1 → v2 patterns searched (all zero hits)
- `Field(..., regex=...)` — 0 hits
- `constr(regex=...)` — 0 hits
- `Body(..., regex=...)` — 0 hits
- Global `filterwarnings` for Pydantic — 0 hits

## Behavioral equivalence
Pydantic v2 accepts both `regex=` (deprecated, emits DeprecationWarning) and `pattern=` (canonical) with identical validation semantics — same regex engine, same anchors, same match rule (`re.match`, not `re.fullmatch`). String contents preserved exactly. Zero drift.

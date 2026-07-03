# TRACK 19.55 · Zero Drift Matrix

Every absolute non-negotiable audited against every file created / touched.

| Category                                          | Rule       | Verified? | Evidence                                                                                          |
|---------------------------------------------------|------------|:---------:|---------------------------------------------------------------------------------------------------|
| New Fleet system                                   | FORBIDDEN | ✅        | No new backend module. `FleetUnitThread.jsx` is a page that consumes existing endpoints.          |
| New Employee / Project / Incident / Vendor / Asset system | FORBIDDEN | ✅ | None built · they are future adopters of the same shell.                                          |
| New score model                                    | FORBIDDEN | ✅        | Operational Health is derived client-side with plain-English explanation, not a numeric score.    |
| New Operational Intelligence engine                | FORBIDDEN | ✅        | `backend/operational_intelligence/` unchanged (9 files).                                          |
| New Guidance engine                                | FORBIDDEN | ✅        | Guidance Card reused from Track 19.54.                                                            |
| New document store                                 | FORBIDDEN | ✅        | No document endpoints created; Section 6 is a slot for existing documents.                       |
| New photo store                                    | FORBIDDEN | ✅        | No photo endpoints created; Section 7 is a slot for existing photos.                              |
| New audit store                                    | FORBIDDEN | ✅        | No audit endpoints created; Section 10 is a slot for existing audit rows.                         |
| Duplicate timeline framework                       | FORBIDDEN | ✅        | Section 4 uses the Track 19.54 `OperationalThread` primitive verbatim.                            |
| Duplicate relationship graph framework             | FORBIDDEN | ✅        | Only ONE `RelationshipGraph.jsx` exists · locked by OI-directory inventory test.                  |
| Duplicate health engine                            | FORBIDDEN | ✅        | Health derivation is a small client-side function; no new backend engine.                         |
| Existing OI reused                                 | REQUIRED  | ✅        | `/summary` filtered client-side for `fleet_intelligence` powers Sections 3 and 8.                 |
| Existing Guidance Card reused                      | REQUIRED  | ✅        | Section 3 opens the Track 19.54 GuidanceCard.                                                      |
| Existing History API reused                        | REQUIRED  | ✅        | Section 9 slot accepts history rows from the certified `/operational-intelligence/history` endpoint. |
| Existing Audit API reused                          | REQUIRED  | ✅        | Section 10 slot accepts audit rows from the certified `/operational-intelligence/audit` endpoint. |
| Existing Summary API reused                        | REQUIRED  | ✅        | Only `/summary` + `/history` + `/history/{id}` are called across the stack.                       |
| No new backend route duplication                   | REQUIRED  | ✅        | Zero backend changes.                                                                             |
| No scheduler changes                               | REQUIRED  | ✅        | `scheduler.py` unchanged.                                                                         |
| No email changes                                   | REQUIRED  | ✅        | No email path touched.                                                                            |
| No recipient changes                               | REQUIRED  | ✅        | `recipients.py` unchanged.                                                                        |
| No score duplication                               | REQUIRED  | ✅        | Health is explanatory tier + why-list; not a numeric score.                                       |
| Fleet uses only existing operational data          | REQUIRED  | ✅        | Only Track 13.26 backbone + certified OI summary.                                                 |
| Future thread architecture documented              | REQUIRED  | ✅        | `TRACK_19_55_UNIVERSAL_THREAD_STANDARD.md` names 19.56–19.60 adopters explicitly.                 |

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
No add / remove / rename in Track 19.55.

## Frontend OI-component inventory (new baseline · locked)
```
frontend/src/components/operational_intelligence/
├── AttentionChip.jsx            (Track 19.54)
├── GuidanceCard.jsx             (Track 19.54)
├── OiAttentionStrip.jsx         (Track 19.52 · rewired 19.54)
├── OperationalThread.jsx        (Track 19.54)
├── OperationalThreadPage.jsx    ← NEW (Track 19.55 · universal 10-section shell)
├── RelationshipGraph.jsx        ← NEW (Track 19.55 · universal relationship visual)
├── TrendChip.jsx                (Track 19.54)
└── guidanceMap.js               (Track 19.54)
```
Enforced by `test_oi_component_directory_inventory`.

## Frontend page inventory (new pilot page)
```
frontend/src/pages/fleet/
└── FleetUnitThread.jsx          ← NEW (Track 19.55 · Fleet Unit pilot)
```

## Route table delta
- `+ /fleet/unit/:unit_number` — behind existing Shop-portal auth gate.
- No other route added, removed, or renamed.

## Preserved certified workflows
- Every Track 19.51–19.54 mount, testid, and workflow remains intact.
- Fleet Visibility unit cards still expand/collapse; the unit-number title now also links to the new Thread page (`fleet-unit-card-<unit>-open-thread`).
- `/shop/units/:unit/history` (Track 13.26 detailed history) continues to work — the Thread page deep-links to it.

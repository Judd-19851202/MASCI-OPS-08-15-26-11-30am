# Search Certification

## Reuse path (per Phase 7.5A architecture)
Trench Safety assets mirror into `equipment_master` automatically (via `upsert_equipment_master_mirror` in `_helpers.py` — fires on every create/update/retire). The existing platform global search indexes `equipment_master` and therefore picks up every trench safety asset by:
- Asset ID (`TB-01`, `EP-001`, `SP-001`, …)
- Serial Number
- Manufacturer
- Model
- Make / Make-Model composite
- Size, Color, Condition
- Current project name / number

## Phase 7.5B additions (no new index)
- **Inspections / Certifications / Repairs / Field Reports / Holds / QR Activity / Photo Activity** are reachable from the Asset Detail (one drill-down from any equipment search hit). The Asset Detail surfaces every one of those records, so a single search → click sequence reaches every directive item.
- The Daily Posture tiles act as **saved searches** for the most operational queries.

## Notification stream as search index
The Phase 7.5C bell store (`db.notifications`) is queryable via `GET /api/notifications`. The frontend NotificationBell renders rows filtered by recipient. This is the de-facto search surface for "what just happened" — a complementary search to the equipment-master index.

## What was NOT added
No parallel search index. No new global search bar. Adding a dedicated Trench Safety search bar would duplicate the existing one and is parked for a future phase.

## Verdict
🟢 PASS — Production-ready (reuses existing infrastructure exclusively).

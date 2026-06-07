# Search Certification (Final Verification Sprint)
**Verdict:** 🟢 PASS

## Reuse path
Every trench safety asset write triggers `upsert_equipment_master_mirror` in `_helpers.py` — the row lands in the canonical `equipment_master` collection that backs the existing platform global search.

## Searchable fields (via mirror)
Asset ID · Serial Number · Manufacturer · Make · Model · Size · Color · Condition · Status · Location · Project — all indexed via the canonical `equipment_master` document.

## Per-record types reachable from search
One click from any equipment-master hit → Asset Detail (`/safety/trench-safety/assets/{id}`) surfaces:
- Holds list · Inspections list · Certifications list · Repairs · Field Reports · QR Activity history · Photo grid · Complete Audit Timeline.

## Notification stream as complementary index
`GET /api/notifications` returns rows with `linked_equipment_id == asset_id`. Operators filter the bell drawer by recent activity per asset.

🟢 PASS.

(Note: this final-verification certification supplements the earlier Phase 7.5A search certification with the same content — both confirm the reuse path through `equipment_master`.)

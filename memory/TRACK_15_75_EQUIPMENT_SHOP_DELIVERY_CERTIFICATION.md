# TRACK 15.75 · Phase 7 — Equipment / Shop Delivery Certification

Evidence: `/tmp/t1575_phaseall.py`, Track 15.73 Slice 1 (equipment resolver) + Slice 3 (picker canonical emit).

## Equipment lookup chain

* `equipment_master` (705 rows) — canonical asset registry.
* Slice 1 (`test_track_15_73_slice1_equipment_resolver`) verifies
  resolver prefers `unit_number`, falls back to `serial_number`,
  then `display_label`. PASS.
* 247 / 705 missing `unit_number` (legacy small gear) — picker
  guardrail (`test_equipment_combo_pick_prefers_unit_number`)
  ensures new submissions emit `unit_number` when present.

## Pre-Op routing

* `schedule_auto_email("equipment-inspection", doc)` — PM_ONLY kind:
  primary PM in To, co-PMs in CC, **no office CC** (operational).
* On failure: `PRE_OP_FAIL_FALLBACK = ['shopmanager@mascigc.com']`
  configured (live verified).
* 196 / 870 inspections show defects (`fail_count>0` or `out_of_service=true`).
* Severity-critical defects: `fleet_defects` (170 rows) carries the
  defect lifecycle for shop triage.

## Shop / Equipment Admin visibility

* `shop_users` collection — 12 accounts authorized for Shop portal.
* Shop portal endpoints (`routes/shop_portal_deps.py`,
  `routes/shop_intel.py`) — per-user HMAC tokens (Track 15.30
  retirement of static HMAC complete).

## PM project-linked equipment visibility

* When equipment inspection carries `project_number`, the PM of
  that job receives the email (verified for 24-06 → `davidjewett@…`,
  no office CC).

## Verdict

**🟢 GREEN.** Equipment resolver + defect escalation + shop fallback
all wired correctly. Slice 1 + Slice 3 regression suite (6 tests)
covers the canonical resolution path.

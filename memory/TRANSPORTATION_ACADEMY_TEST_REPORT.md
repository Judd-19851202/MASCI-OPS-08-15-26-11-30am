TRANSPORTATION ACADEMY · TEST REPORT
=====================================

DATE      : 2026-06-29
SUITE     : `/app/backend/tests/test_track_19_01_transportation_academy.py`
RESULT    : 21 / 21 PASS

────────────────────────────────────────────────────────────────────────────
TEST INVENTORY
────────────────────────────────────────────────────────────────────────────
DOCS (7 parametrised cases)
  · TRACK_19_01_LEGACY_22_MODULE_AUDIT.md exists                              ✅
  · TRACK_19_01_TRANSPORTATION_ORIENTATION_VIDEO_INTEGRATION.md exists        ✅
  · TRACK_19_01A_TRANSPORTATION_ACADEMY_CURRICULUM.md exists                  ✅
  · TRANSPORTATION_ACADEMY_CURRICULUM_STRUCTURE.md exists                     ✅
  · TRANSPORTATION_ACADEMY_MODULE_STANDARD.md exists                          ✅
  · TRANSPORTATION_ACADEMY_PLACEHOLDER_ARCHITECTURE.md exists                 ✅
  · TRANSPORTATION_ACADEMY_TEST_REPORT.md exists                              ✅

ENDPOINT + CURRICULUM SHAPE
  · `/api/admin/transportation/academy/modules` returns 11 entries        ✅
  · curriculum_order is exactly 1..11                                     ✅
  · Modules 1 + 2 published with video_url + canonical titles             ✅
  · Modules 3-11 in_development with full metadata + reserved quiz        ✅
  · Modules 4 + 11 use the new keys (driver_qualification_compliance,
    final_review_certification)                                           ✅

LEGACY ISOLATION
  · 12 retired legacy keys are EXCLUDED from the Academy view             ✅

SOURCE-LEVEL ASSERTS
  · `bootstrap_track_19_01a` function exists                              ✅
  · Bootstrap is idempotent (LEGACY_RETIRED_TRACK check present)          ✅
  · Endpoint is wired with `Depends(ops_guard)` (dispatch + admin)        ✅
  · Video player reads `video_url` and the Academy "Module in production"
    professional copy ships                                               ✅
  · Frontend Academy page exposes the canonical testids                   ✅
  · `TransportationApp.jsx` wires `path="academy"` + the detail route     ✅
  · Sidebar `txops-nav-academy` entry exists                              ✅

SAFETY
  · Bootstrap performs no `delete_many` / `drop_collection` calls — 45
    historic `welcome_to_masci` E2E rows are preserved.                   ✅

────────────────────────────────────────────────────────────────────────────
LIVE SMOKE (Super Admin, preview)
────────────────────────────────────────────────────────────────────────────
  · `/transportation-operations/academy` renders 11 module cards.
  · Module 1 detail page renders the `<video>` with controls and the
    customer-assets MP4 URL.
  · Module 3 detail page renders the In Development panel and the
    canonical professional copy.
  · Sidebar entry "Transportation Academy" highlights correctly while
    inside the Academy route.
  · No raw 401/403. No React red overlay. No "Sky AI video placeholder"
    surfaces on any Academy path.

────────────────────────────────────────────────────────────────────────────
REGRESSION COVERAGE
────────────────────────────────────────────────────────────────────────────
  · Existing Track 16.08 orientation endpoints unchanged.
  · Existing Track 18.12C dispatcher acceptance + Track 19.00 driver/
    carrier foundation tests remain unaffected (legacy retire is the
    only DB write, and it only touches `transport_orientation_modules`).
  · Existing `OrientationCenter` route still mounted under
    `/transportation-operations/orientation` for backwards compatibility.

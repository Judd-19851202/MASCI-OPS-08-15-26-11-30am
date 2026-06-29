TRACK 19.01 · TRANSPORTATION ORIENTATION VIDEO INTEGRATION
===========================================================

DATE  : 2026-06-29
DEPS  : Track 16.08 orientation framework, Track 19.01A hybrid migration.

────────────────────────────────────────────────────────────────────────────
SCOPE
────────────────────────────────────────────────────────────────────────────
Integrate the two uploaded Transportation Orientation videos into the
existing Transportation Operations Orientation system as Modules 1 and
2 of the new Transportation Academy curriculum (Track 19.01A).

  · Video 1 → Module 1 · `welcome_to_masci` · "Welcome to MASCI Transportation Operations"
  · Video 2 → Module 2 · `driver_expectations` · "Driver Expectations & Professional Standards"

Both modules ship Published, English, Required, version v1.0.

────────────────────────────────────────────────────────────────────────────
ARCHITECTURE
────────────────────────────────────────────────────────────────────────────
NO new orientation engine. NO new collection. The existing
`transport_orientation_modules` document already supports a
`placeholders[*]` array keyed by language. Track 19.01 adds one new
field per placeholder:

    placeholders[*].video_url   (string, optional)

When `video_url` is present, the `MasciVideoPlayer` renders an actual
HTML5 `<video src>` with native controls. When absent, the player
falls back to the existing `sky_asset_id` Sky-AI placeholder path or
to the Track 19.01A "Module in production" copy.

This decoupling means future Sky-AI-generated assets, additional
uploaded mp4s, and CDN-hosted assets all flow through the same field
without any further architecture change.

────────────────────────────────────────────────────────────────────────────
VIDEO STORAGE
────────────────────────────────────────────────────────────────────────────
The two videos are hosted as public emergent customer-asset URLs:

  Module 1:
    `https://customer-assets.emergentagent.com/job_safety-audit-mobile-1/artifacts/gsq6iqsz_MASCI%20Vid%201%20Transport%20.mp4`

  Module 2:
    `https://customer-assets.emergentagent.com/job_safety-audit-mobile-1/artifacts/t0nuqy4b_MASCI%20Vid%202%20Transport%20%202.mp4`

R2 upload is intentionally NOT required for this track. When MASCI
re-encodes / hosts the videos through R2 or an alternate CDN, the
operator simply patches `placeholders[*].video_url` for the affected
module — no schema change, no migration.

────────────────────────────────────────────────────────────────────────────
VIDEO PLAYER (`MasciVideoPlayer.jsx`)
────────────────────────────────────────────────────────────────────────────
Render order:
  1. If `placeholder.video_url` (or `module.video_url`) is truthy →
     real `<video src>` with native controls.
  2. Else if `placeholder.sky_asset_id` is truthy → Sky AI mode
     (existing Track 16.08 placeholder · unchanged for non-Academy
     content).
  3. Else → Track 19.01A "Transportation Academy module in production"
     professional copy. The legacy "Sky AI video placeholder" string
     has been REMOVED from the Academy user-facing path (still used by
     legacy Track 16.08 admin previews if anyone surfaces them).

────────────────────────────────────────────────────────────────────────────
ENDPOINT
────────────────────────────────────────────────────────────────────────────
NEW · `GET /api/admin/transportation/academy/modules`
  Returns only `curriculum_track="transportation_academy_v1"` AND
  `active=True`, sorted by `curriculum_order` ASC. Includes the
  surfaced top-level `video_url` (English placeholder) so the frontend
  can render the player without poking into the placeholders array.
  Accepts both Admin and Dispatch tokens.

The Track 16.08 endpoints remain unchanged and continue to serve the
full module catalog (legacy + Academy + retired) for administrative
use.

────────────────────────────────────────────────────────────────────────────
TESTING
────────────────────────────────────────────────────────────────────────────
`/app/backend/tests/test_track_19_01_transportation_academy.py` covers:
  · 7 required docs exist
  · `/academy/modules` returns 11 entries in curriculum_order 1-11
  · Modules 1 + 2 published with `video_url`
  · Modules 3-11 in_development with full metadata
  · Retired legacy keys do not leak into the Academy view
  · Bootstrap function exists and is idempotent
  · Video player consumes `video_url` and no longer surfaces "Sky AI
    video placeholder" copy on the Academy path
  · Frontend Academy page + module detail route + sidebar entry wired
  · Bootstrap never deletes assignments / certificates

────────────────────────────────────────────────────────────────────────────
RISKS
────────────────────────────────────────────────────────────────────────────
  · Public emergent asset URLs are not behind MASCI auth. The videos
    are training content (no sensitive operational data), and the
    URLs are not advertised on the public site. If MASCI later wants
    auth-gated streaming, the `video_url` field accepts any HTTPS
    source — swap to a signed R2 URL with no code change.

────────────────────────────────────────────────────────────────────────────
DEFERRALS
────────────────────────────────────────────────────────────────────────────
  · R2 / CDN re-hosting (operator decision).
  · Quiz / knowledge-check (reserved metadata in place; engine ships
    in a follow-on track).
  · Spanish / Cuban-Spanish / French translations (slots reserved in
    `placeholders[*]` per language; awaits content uploads).

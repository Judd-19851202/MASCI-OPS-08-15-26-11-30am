TRACK 19.01A · TRANSPORTATION ACADEMY CURRICULUM (HYBRID MIGRATION)
====================================================================

DATE     : 2026-06-29
APPROACH : Option C · Hybrid migration of the legacy Track 16.08
           21-module outline into the new permanent 11-module
           Transportation Academy curriculum.
DOCTRINE : Powerful · Simple · Beautiful · Trusted · Proven · Field First
           · Operations First · Mobile First · Visible = Usable · Zero Drift.

────────────────────────────────────────────────────────────────────────────
WHAT SHIPPED
────────────────────────────────────────────────────────────────────────────
- 11 active Transportation Academy modules, `curriculum_track="transportation_academy_v1"`,
  ordered 1-11.
- 2 published modules with English videos (Modules 1 + 2).
- 9 In Development modules with complete metadata.
- 12 legacy module keys retired (`active=false`, `curriculum_track="legacy_track_16_08_retired"`).
- 1 new endpoint: `GET /api/admin/transportation/academy/modules`.
- 1 new frontend page: `/transportation-operations/academy` + module
  detail route `/transportation-operations/academy/:moduleKey`.
- 1 sidebar entry: "Transportation Academy" inside the existing
  "Compliance" group, alongside the original Orientation entry.
- `MasciVideoPlayer` updated to render `placeholder.video_url`
  natively; legacy "Sky AI video placeholder" copy removed from the
  Academy user-facing path.

────────────────────────────────────────────────────────────────────────────
THE 11-MODULE CURRICULUM
────────────────────────────────────────────────────────────────────────────
| # | Key                              | Title                                                    | Status         |
|---|----------------------------------|----------------------------------------------------------|----------------|
| 1 | welcome_to_masci                 | Welcome to MASCI Transportation Operations               | published      |
| 2 | driver_expectations              | Driver Expectations & Professional Standards             | published      |
| 3 | safety_culture                   | Transportation Safety Fundamentals                       | in_development |
| 4 | driver_qualification_compliance  | Driver Qualification & Regulatory Compliance             | in_development |
| 5 | backing_procedures               | Safe Driving Operations                                  | in_development |
| 6 | traffic_control                  | Jobsite Traffic Control & Site Operations                | in_development |
| 7 | loading_procedures               | Equipment Loading, Heavy Haul & Transport Operations     | in_development |
| 8 | dumping_procedures               | Dump Truck & End Dump Operations                         | in_development |
| 9 | communications                   | Transportation Communication & Technology                | in_development |
| 10 | emergency_procedures             | Emergency Response & Environmental Responsibilities      | in_development |
| 11 | final_review_certification       | Transportation Operations Final Review & Certification   | in_development |

9 reused legacy keys (renamed via metadata, stable identifier preserved
so any historic assignments / certificates stay queryable).
2 brand-new keys for Module 4 and Module 11.

────────────────────────────────────────────────────────────────────────────
RETIRED LEGACY KEYS (audit-only · `active=false`)
────────────────────────────────────────────────────────────────────────────
customer_expectations · ppe · near_miss_reporting · incident_reporting ·
hauling_procedures · jobsite_arrival · asphalt_plant_operations ·
equipment_awareness · truck_readiness · environmental_responsibilities ·
end_of_shift · annual_refresher.

Topics from these 12 keys are absorbed into the new 11 Academy modules
(e.g. PPE / incident reporting → Module 3 Safety Fundamentals; soft
ground / overhead → Module 8 Dump & End Dump).

────────────────────────────────────────────────────────────────────────────
BOOTSTRAP FUNCTION (`bootstrap_track_19_01a`)
────────────────────────────────────────────────────────────────────────────
File: `/app/backend/routes/transportation_orientation.py`
Wired in `server.py` `_track_16_08_bootstrap_on_startup` (runs
immediately after `bootstrap_track_16_08`).

Behaviour:
  1. For each of the 11 Academy entries, find the existing module by
     key. If present → `update_one` with the Academy metadata + a
     fresh `placeholders` array (Module 1 + 2 receive the English
     video URL). If absent → `insert_one` with full Academy metadata.
  2. For each of the 12 retired legacy keys, set `active=false` +
     `curriculum_track="legacy_track_16_08_retired"`. Skipped if
     already retired.
  3. Returns `{academy_total, promoted, inserted, retired}` for the
     boot log.

Idempotency:
  · `update_one` is non-destructive; reruns produce the same row.
  · Retire step skips already-retired rows.
  · No `delete_many` / `drop_collection`. Tests assert this.

Live first-boot result on preview Atlas:
  `academy=11 promoted=11 inserted=0 retired=12`.

────────────────────────────────────────────────────────────────────────────
ENDPOINT CONTRACT
────────────────────────────────────────────────────────────────────────────
`GET /api/admin/transportation/academy/modules` → dispatch + admin.

Response (truncated):
```json
{
  "curriculum_track": "transportation_academy_v1",
  "total": 11,
  "published": 2,
  "in_development": 9,
  "items": [
    { "curriculum_order": 1, "key": "welcome_to_masci",
      "title": "Welcome to MASCI Transportation Operations",
      "status": "published", "published": true,
      "description": "...",
      "video_url": "https://customer-assets.emergentagent.com/.../MASCI%20Vid%201%20Transport%20.mp4",
      "estimated_runtime_minutes": 12,
      "topics": [...], "learning_objectives": [...],
      "quiz_enabled": false, "quiz_required": false,
      "question_count": 5, "passing_score": 80,
      "quiz_status": "reserved", "required": true,
      "languages": ["en","es","es_CU","fr"] },
    { "curriculum_order": 2, ... }
  ]
}
```

────────────────────────────────────────────────────────────────────────────
FRONTEND
────────────────────────────────────────────────────────────────────────────
Files:
  · `/app/frontend/src/pages/transportation/TransportationAcademy.jsx`
    — list page + module detail page (two named exports).
  · `/app/frontend/src/pages/transportation/TransportationApp.jsx`
    — wires `path="academy"` and `path="academy/:moduleKey"` inside
    the Transportation Operations shell.
  · `/app/frontend/src/pages/transportation/_shared.jsx`
    — adds the "Transportation Academy" sidebar entry next to
    "Orientation" (testid `txops-nav-academy`).
  · `/app/frontend/src/components/transportation/MasciVideoPlayer.jsx`
    — reads `placeholder.video_url`; falls back to legacy
    `sky_asset_id` mode; "Sky AI video placeholder" copy removed from
    the Academy path.

UI Highlights:
  · Premium dark "Module in production" panel on In Development
    modules — NOT a "coming soon" graphic, NOT an empty card.
  · Progress strip showing `2 of 11 modules available · 9 additional
    modules in production`.
  · Per-card status chip (Published / In Development) + Required badge.
  · Module detail page: title eyebrow, status chip, Required badge,
    breadcrumb back, real `<video>` for published modules, full
    learning objectives + topics lists, prev/next module navigation,
    reserved knowledge-check disclosure.
  · Mobile / tablet / desktop responsive via existing Transportation
    Operations design language.

────────────────────────────────────────────────────────────────────────────
ASSIGNMENTS / CERTIFICATES (PRESERVED)
────────────────────────────────────────────────────────────────────────────
Track 19.01A's bootstrap is read-mostly. It NEVER calls `delete_many`
or `drop_collection` on `transport_orientation_assignments`,
`transport_orientation_certificates`, or any related collection. The
45 historic E2E rows (all attached to `welcome_to_masci`) remain
intact and queryable.

────────────────────────────────────────────────────────────────────────────
ROLLBACK
────────────────────────────────────────────────────────────────────────────
  1. Setting `active=false` on retired keys is reversible —
     `db.transport_orientation_modules.update_many({"curriculum_track":"legacy_track_16_08_retired"},
     {"$set":{"active":True}})`.
  2. Removing the Academy entries is safe — no Academy module yet
     has assignments because no users have been onboarded against
     the new keys at the time of this writing.
  3. Removing the new endpoint is a one-line revert. The Track 16.08
     endpoints continue to serve the catalog.

────────────────────────────────────────────────────────────────────────────
LIVE SMOKE (Super Admin, preview pod)
────────────────────────────────────────────────────────────────────────────
  · `/transportation-operations/academy` renders 11 module cards.
  · Module 1 detail page renders the `<video>` element with
    controls and the customer-assets MP4 URL.
  · Module 3 detail page renders the In Development panel with the
    canonical professional copy.
  · Sidebar entry "Transportation Academy" highlights correctly.
  · No raw 401/403 surfaces. No React red overlay.

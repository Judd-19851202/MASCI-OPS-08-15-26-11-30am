TRACK 19.01 · LEGACY 22-MODULE AUDIT
=====================================

DATE  : 2026-06-29
SCOPE : Identify what the existing "22" orientation modules are, whether
        they carry real production training data, and recommend a safe
        migration path to the new 11-module Transportation Academy
        curriculum (Track 19.01 / 19.01A).

────────────────────────────────────────────────────────────────────────────
HEADLINE
────────────────────────────────────────────────────────────────────────────
The "22" is actually **21 unique module keys** seeded by the Track 16.08
bootstrap (`MODULES` constant in
`/app/backend/routes/transportation_orientation.py`, lines 55-77). All
21 are bootstrap-seeded shells. **No video has ever been attached** to
any of them — every module has `published_placeholders=0` across all
four supported languages (en, es, es_CU, fr). Only ONE module
(`welcome_to_masci`) has any historical traffic at all, and on
inspection that traffic is **synthetic E2E test data, not real
production training history**.

→ Verdict: the 21 are not a live operational catalog. They are the old
Track 16.08 over-expanded orientation outline, and they have been
consolidated by the user into the new 11-module Transportation Academy.

────────────────────────────────────────────────────────────────────────────
WHAT THE 21 MODULES ARE
────────────────────────────────────────────────────────────────────────────
Source: `MODULES` constant in transportation_orientation.py + the
`bootstrap_track_16_08` function. Created by `system_bootstrap` on
every backend boot since Track 16.08 shipped. No video assets attached.

| # | Key                              | Title                              | Category     | Req | published_placeholders | Notes |
|---|----------------------------------|------------------------------------|--------------|-----|------------------------|-------|
| 1 | welcome_to_masci                 | Welcome to MASCI                   | intro        | Y   | 0                      | only module with any historic refs (45 synthetic E2E asn+certs) |
| 2 | safety_culture                   | Safety Culture                     | safety       | Y   | 0                      | zero refs |
| 3 | traffic_control                  | Traffic Control                    | operations   | Y   | 0                      | zero refs |
| 4 | jobsite_arrival                  | Jobsite Arrival                    | operations   | Y   | 0                      | zero refs |
| 5 | asphalt_plant_operations         | Asphalt Plant Operations           | operations   | Y   | 0                      | zero refs |
| 6 | loading_procedures               | Loading Procedures                 | operations   | Y   | 0                      | zero refs |
| 7 | hauling_procedures               | Hauling Procedures                 | operations   | Y   | 0                      | zero refs |
| 8 | backing_procedures               | Backing Procedures                 | operations   | Y   | 0                      | zero refs |
| 9 | dumping_procedures               | Dumping Procedures                 | operations   | Y   | 0                      | zero refs |
| 10 | truck_readiness                  | Truck Readiness                    | vehicle      | Y   | 0                      | zero refs |
| 11 | driver_expectations              | Driver Expectations                | expectations | Y   | 0                      | zero refs |
| 12 | ppe                              | PPE                                | safety       | Y   | 0                      | zero refs |
| 13 | incident_reporting               | Incident Reporting                 | safety       | Y   | 0                      | zero refs |
| 14 | near_miss_reporting              | Near Miss Reporting                | safety       | Y   | 0                      | zero refs |
| 15 | emergency_procedures             | Emergency Procedures               | safety       | Y   | 0                      | zero refs |
| 16 | equipment_awareness              | Equipment Awareness                | vehicle      | Y   | 0                      | zero refs |
| 17 | communications                   | Communications                     | operations   | Y   | 0                      | zero refs |
| 18 | customer_expectations            | Customer Expectations              | expectations | Y   | 0                      | zero refs |
| 19 | environmental_responsibilities   | Environmental Responsibilities     | safety       | Y   | 0                      | zero refs |
| 20 | end_of_shift                     | End of Shift                       | operations   | Y   | 0                      | zero refs |
| 21 | annual_refresher                 | Annual Refresher                   | annual       | N   | 0                      | zero refs |

(The Track 16.08 docstring says "22 default modules"; the live count is
21. The 22nd was the per-language placeholder per module — not a 22nd
module key.)

────────────────────────────────────────────────────────────────────────────
ASSIGNMENTS / COMPLETIONS / CERTIFICATES
────────────────────────────────────────────────────────────────────────────
Collection                                  Total  Active  Completed  Certs
transport_orientation_assignments           45     0       45         —
transport_orientation_certificates          45     —       —          45

All 45 reference the SAME module: `welcome_to_masci`.
The other 20 modules: 0 assignments · 0 completions · 0 certificates.

Inspection of the 45 `welcome_to_masci` assignments:
  · 45 DISTINCT `transport_person_id`s — every driver is named "E2E Driver"
    (synthetic Playwright/pytest fixture seed).
  · `assigned_by="admin"` on every row.
  · Median time-to-complete = **~2 seconds** (assigned_at 22:41:08 →
    completed_at 22:41:10 in the sample). No human can watch an
    orientation in 2 seconds.
  · Date range: 2026-06-27 22:41 UTC → 2026-06-28 22:48 UTC (yesterday
    — during Track 18.12C dispatcher acceptance testing).

→ ZERO real production training history exists in the legacy 22.
The 45 assignment/cert rows are E2E test fixtures from this week's
regression sweep. They can safely be left in place (audit-only) or
purged in a follow-on cleanup track.

────────────────────────────────────────────────────────────────────────────
USER-FACING IMPACT
────────────────────────────────────────────────────────────────────────────
Today, the legacy 21 modules ARE returned by:
  · `GET /api/admin/transportation/orientation/modules`
  · `GET /api/admin/transportation/orientation/dashboard`
  · `GET /transportation/invite/{token}/orientation/modules`
  · The orientation admin / driver workspace UI.

But because every module has `published_placeholders=0`, the on-page
experience is the existing "Sky AI video placeholder · {module.title}"
message inside `MasciVideoPlayer`. No real driver in production has
ever been able to actually watch any of these modules.

→ Removing or replacing them will not break any user-visible
production flow. The only "experience" being replaced is the Track
16.08 dev placeholder shell.

────────────────────────────────────────────────────────────────────────────
MAPPING TO NEW 11
────────────────────────────────────────────────────────────────────────────
The new 11-module curriculum cleanly subsumes the legacy 21. Every
legacy concern maps to a topic inside one of the new 11:

| New # | New Title                                                  | Best legacy key to REUSE      | Legacy keys it ABSORBS / RETIRES                                                                                  |
|-------|------------------------------------------------------------|-------------------------------|------------------------------------------------------------------------------------------------------------------|
| 1     | Welcome to MASCI Transportation Operations                 | `welcome_to_masci`            | —                                                                                                                |
| 2     | Driver Expectations & Professional Standards               | `driver_expectations`         | `customer_expectations` (absorb as topic)                                                                        |
| 3     | Transportation Safety Fundamentals                         | `safety_culture`              | `ppe`, `near_miss_reporting`, `incident_reporting` (absorb)                                                      |
| 4     | Driver Qualification & Regulatory Compliance               | NEW `driver_qualification_compliance` | —                                                                                                        |
| 5     | Safe Driving Operations                                    | `backing_procedures`          | `hauling_procedures` (absorb)                                                                                    |
| 6     | Jobsite Traffic Control & Site Operations                  | `traffic_control`             | `jobsite_arrival` (absorb)                                                                                       |
| 7     | Equipment Loading, Heavy Haul & Transport Operations       | `loading_procedures`          | `asphalt_plant_operations`, `equipment_awareness`, `truck_readiness` (absorb)                                    |
| 8     | Dump Truck & End Dump Operations                           | `dumping_procedures`          | —                                                                                                                |
| 9     | Transportation Communication & Technology                  | `communications`              | —                                                                                                                |
| 10    | Emergency Response & Environmental Responsibilities        | `emergency_procedures`        | `environmental_responsibilities`, `end_of_shift` (absorb)                                                        |
| 11    | Transportation Operations Final Review & Certification     | NEW `final_review_certification` | `annual_refresher` (absorb)                                                                                   |

Total: 9 legacy keys REUSED as the canonical Academy keys.
Plus 2 NEW keys for Modules 4 and 11.
Plus 11 legacy keys RETIRED (set `active=false` and tagged
`curriculum_track="legacy_track_16_08_retired"` so the audit trail
is preserved but they disappear from the UI).

→ The 45 historic E2E test certificates remain attached to
`welcome_to_masci`. They remain queryable but invisible in the new
Academy dashboard (which filters on `curriculum_track="academy_v1"`).

────────────────────────────────────────────────────────────────────────────
RECOMMENDATION
────────────────────────────────────────────────────────────────────────────
**Option C — Hybrid migration.**

Specifically:
  1. KEEP the 9 best-matching legacy keys as the canonical Academy
     keys for Modules 1-3, 5-10. Update title / description /
     learning_objectives / topics / status / curriculum metadata
     in place. ZERO destruction of `welcome_to_masci`'s 45 historic
     cert references.
  2. CREATE 2 new keys for Modules 4 and 11
     (`driver_qualification_compliance`, `final_review_certification`).
  3. RETIRE the 10 remaining legacy keys (set `active=false` +
     `curriculum_track="legacy_track_16_08_retired"`). They stay
     in the database for audit, but are excluded from the new
     Academy dashboard.
  4. Attach Video 1 → `welcome_to_masci` placeholder (en).
  5. Attach Video 2 → `driver_expectations` placeholder (en).
  6. Modules 3-11 (the 9 in-development entries): full metadata,
     `status="in_development"`, professional "module in production"
     copy in the placeholder shell.

WHY OPTION C IS THE RIGHT ANSWER
  · No real production training history exists today (all 45 historic
    rows are E2E test fixtures).
  · Option A (add 11 beside existing 21) would duplicate concepts
    (welcome × 2, driver_expectations × 2, etc.) and force the user
    to look at both lists. Violates "No duplicate curriculum".
  · Option B (full replacement) is safe data-wise but loses the
    `welcome_to_masci` key + its 45 historic E2E cert rows. Those rows
    are not valuable but they're useful for testing migrations.
  · Option C preserves the audit trail, avoids duplicate keys,
    consolidates the catalog cleanly, and keeps the existing
    Track 16.08 endpoints working unchanged.

────────────────────────────────────────────────────────────────────────────
SAFE IMPLEMENTATION PLAN (awaits user confirmation)
────────────────────────────────────────────────────────────────────────────
Backend
  · Extend `bootstrap_track_16_08(db)` (or add a sibling
    `bootstrap_track_19_01a(db)` called immediately after) that:
      - Patches the 9 reused keys: sets `curriculum_track="academy_v1"`,
        `curriculum_order` 1-3,5-10, new `title`, `description`,
        `learning_objectives`, `topics`, `estimated_runtime_minutes`,
        `status="published"` (modules 1+2) or "in_development" (others),
        `quiz_enabled=false`, `quiz_required=false`, `question_count=5`,
        `quiz_status="reserved"`.
      - Inserts the 2 new keys (Module 4 + Module 11) with the
        same metadata shape.
      - Updates `welcome_to_masci` and `driver_expectations`
        placeholders (en) with the uploaded asset URLs:
          - Module 1: `https://customer-assets.emergentagent.com/job_safety-audit-mobile-1/artifacts/gsq6iqsz_MASCI%20Vid%201%20Transport%20.mp4`
          - Module 2: `https://customer-assets.emergentagent.com/job_safety-audit-mobile-1/artifacts/t0nuqy4b_MASCI%20Vid%202%20Transport%20%202.mp4`
        Stored in NEW field `video_url` on the per-language placeholder
        object (alongside existing `sky_asset_id`).
      - Retires the 10 unused legacy keys by setting `active=false`
        and `curriculum_track="legacy_track_16_08_retired"`.
  · Add module fields (idempotent migration):
      `curriculum_track`, `curriculum_order`,
      `learning_objectives` [], `topics` [], `estimated_runtime_minutes`,
      `status` ("published" / "in_development" / "retired"),
      `quiz_enabled`, `quiz_required`, `question_count`,
      `placeholders[*].video_url`.
  · New endpoint `GET /api/admin/transportation/academy/modules`
    returns ONLY `curriculum_track="academy_v1"` modules in
    `curriculum_order` ascending.
  · Update `MasciVideoPlayer` to use `placeholder.video_url` as the
    `<video src>` when present.

Frontend
  · New page `/app/frontend/src/pages/transportation/TransportationAcademy.jsx`
    — overall progress strip + 11 module cards (2 with Watch CTA,
    9 with "In Development" professional copy).
  · Module detail route `/transportation-operations/academy/:moduleKey`
    — video player for published modules; objectives/topics
    placeholder for in-development modules.
  · Sidebar entry "Transportation Academy" inside the existing
    Orientation group.

Tests + Docs
  · `/app/backend/tests/test_track_19_01_transportation_academy.py`
  · 6 markdown deliverables.
  · PRD.md update.

Rollback
  · No destructive deletes. Setting `active=false` is reversible.
  · The 2 new module keys can be removed safely (no assignments
    exist for them).
  · `welcome_to_masci`'s 45 historic E2E rows are preserved.

DO NOT IMPLEMENT UNTIL USER CONFIRMS THE RECOMMENDATION.

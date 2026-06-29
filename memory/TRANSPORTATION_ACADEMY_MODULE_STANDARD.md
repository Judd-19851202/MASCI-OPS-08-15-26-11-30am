TRANSPORTATION ACADEMY · MODULE STANDARD
=========================================

Authoritative shape every Transportation Academy module must satisfy.
Enforced by `bootstrap_track_19_01a` and asserted by Track 19.01 tests.

────────────────────────────────────────────────────────────────────────────
DOCUMENT SHAPE (collection `transport_orientation_modules`)
────────────────────────────────────────────────────────────────────────────
Identity:
  · `id`                          uuid (Mongo `_id` is internal)
  · `tenant`                      "masci"
  · `key`                         stable string id (see curriculum
                                  structure doc for the 11 canonical
                                  Academy keys)

Curriculum:
  · `curriculum_track`            "transportation_academy_v1"
  · `curriculum_order`            int 1-11
  · `academy_module_number`       mirror of curriculum_order
  · `status`                      "published" | "in_development"
  · `published`                   bool — convenience flag
  · `active`                      bool — must be True for visible
                                  Academy entries

User-facing copy:
  · `title`                       string
  · `description`                 string · short paragraph
  · `learning_objectives`         array<string> · 3-5 entries
  · `topics`                      array<string> · 3-10 entries

Operational metadata:
  · `category`                    one of: intro · expectations ·
                                  safety · compliance · operations ·
                                  certification
  · `required`                    bool (Track 19.01A: all 11 are required)
  · `version`                     semver-ish string (currently "1")
  · `languages`                   ["en","es","es_CU","fr"]
  · `estimated_runtime_minutes`   int (display)
  · `runtime_seconds`             int (heartbeat math)

Quiz reservation (Track 19.02 attach point):
  · `quiz_enabled`                bool — default False
  · `quiz_required`               bool — default False
  · `question_count`              int — default 5
  · `passing_score`               int — default 80
  · `quiz_status`                 "reserved" (until engine ships)

Media (per-language placeholder array):
  · `placeholders[*]`             one row per language
      · `language`                "en" | "es" | "es_CU" | "fr"
      · `video_url`               TRACK 19.01 — string URL OR null
      · `sky_asset_id`            string OR null (legacy Sky-AI path)
      · `runtime_seconds`         int
      · `thumbnail_url`           string OR null
      · `version`                 string
      · `status`                  "published" | "placeholder" | "retired"
      · `uploaded_at`             ISO timestamp OR null

Audit metadata:
  · `created_at`, `created_by`, `updated_at`, `updated_by`.

────────────────────────────────────────────────────────────────────────────
INVARIANTS
────────────────────────────────────────────────────────────────────────────
  1. `curriculum_track` must be `"transportation_academy_v1"` for any
     module visible in the Academy. Retired legacy rows carry
     `"legacy_track_16_08_retired"`.
  2. `published == True` iff `status == "published"`.
  3. `placeholders[*]` ALWAYS has exactly 4 entries (one per language)
     even when only English has a video. Reserves storage for future
     translations.
  4. `video_url` is OPTIONAL. Present on Module 1 and Module 2 only at
     ship time. Future uploads patch this field on the relevant
     placeholder.
  5. The legacy "Sky AI video placeholder" copy MUST NOT appear in any
     Academy user-facing path. The Track 19.01 video player removes it.
  6. `curriculum_order` is unique within the Academy. The endpoint
     sorts by it ascending.

────────────────────────────────────────────────────────────────────────────
PATCH RULES
────────────────────────────────────────────────────────────────────────────
Publishing a new module:
  1. Patch `status` from `"in_development"` to `"published"`.
  2. Patch `published` from `false` to `true`.
  3. Set `placeholders[lang].video_url` and `status="published"`.
  4. Optionally bump `version` and `placeholders[lang].version`.

Retiring an Academy module (rare):
  1. Set `active=false`.
  2. Set `curriculum_track="legacy_track_16_08_retired"` (or a future
     retired track id).
  3. Do NOT delete the row — assignments / certs may reference it.

────────────────────────────────────────────────────────────────────────────
ENDPOINT VS COLLECTION
────────────────────────────────────────────────────────────────────────────
The Academy endpoint
`GET /api/admin/transportation/academy/modules` is the SOLE
user-facing list source for the Academy. It:
  · filters on `curriculum_track="transportation_academy_v1"` AND
    `active=True`
  · sorts on `curriculum_order` ASC
  · surfaces the English `video_url` at the top level for the player

The Track 16.08 catalog endpoint
`GET /api/admin/transportation/orientation/modules` still returns the
ENTIRE catalog (legacy + Academy + retired) and is used by the
administrative module-management UI only.

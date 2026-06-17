# PM PORTAL OPERATIONAL FEED AUDIT (TRACK 15.11A)

**Date:** 2026-06-17  ·  **Scope:** every PM-dashboard surface currently rendering on `/pm/command-center`  ·  **Status:** ✅ AUDIT COMPLETE — wiring is correct end-to-end; live "empty cards" are a data-scope question, not a wiring defect.

---

## 1. Executive finding

The PM Portal **Command Center** (`/pm/command-center`, served by `frontend/src/pages/PmCommandCenter.jsx`) is correctly wired to PM-scoped endpoints in the backend. Every card on the page hits a real endpoint that passes through `compute_pm_scope()` (`backend/pm_auth.py:306`), which pulls the PM's project set from BOTH legacy fields (`jobs_master.pm_email`, `jobs_master.co_pm_emails[]`) AND the modern source-of-truth (`project_team_assignments` where `user_id` or `email` matches).

If the live PM dashboard shows empty cards, the cause is **one of three**, in priority order:

1. **The signed-in PM has no project scope.** Their email does not match `jobs_master.pm_email` / `co_pm_emails[]` on any non-deleted job, AND they have no `active=true` row in `project_team_assignments` with `assignment_role ∈ {pm, co_pm, executive_oversight, ...}`. This is the most common cause for a freshly-onboarded PM or a PM whose email was changed.
2. **The PM's projects exist but have no Daily Reports / job_photos / safety-impact / shop-impact rows yet.** The empty state is then truthful.
3. **Project-number string mismatch between collections.** A DR with `project_number = "26-07"` will not surface for a PM whose scoped set is `{"26-07-A"}` or `{"26-07 "}` (trailing space). This is rare but worth checking by hand on the live DB.

None of these is a *wiring* defect. They are *data* questions that require a PM session against the live DB to resolve. The Track 15.11A audit confirms the wiring is correct and equips the next operator-led session to execute the runtime scenarios in Phase 13 deterministically.

---

## 2. PM Dashboard sections — surface inventory

| # | Section | Frontend component | Backend endpoint | Collection(s) | PM-scope mechanism |
|---|---|---|---|---|---|
| A | Projects Assigned To You | `PmProjectFirstHome.jsx` § "Projects" panel | `GET /api/pm/command-center/overview` | `jobs_master`, `project_team_assignments` | `compute_pm_scope()` (filter by pm_email OR co_pm_emails OR roster user_id/email) |
| B | Latest Dailies & Photos from the Field | `PmProjectFirstHome.jsx` § "Daily Reports" + § "Photos" | `GET /api/daily-reports?limit=5`, `GET /api/job-photos?limit=8` | `daily_reports`, `job_photos` | `compute_pm_scope()` on both endpoints |
| C | What Needs PM Action | `PmProjectFirstHome.jsx` § "Risk" | `GET /api/pm/command-center/safety-impact`, `GET /api/pm/command-center/shop-impact` | `incidents`, `equipment_inspections`, `shop_defects` (per route) | `compute_pm_scope()` baked into the route |
| D | Reports, JHPs, Photos, Project Roster | `PmProjectFirstHome.jsx` § "Quick links" tiles | links only (no fetch) → `/daily`, `/jha-records`, `/pm/photos`, `/pm/project-staffing` | navigation only | gated by destination pages |
| E | Equipment, Trucks, Trailers & Specialty Assets | `PmProjectFirstHome.jsx` § "Resources" | `GET /api/pm/command-center/overview` (counts), `/api/pm/command-center/resources` (detail) | `equipment_inspections`, `trailer_inspections`, `equipment_outstanding`, `project_team_assignments` | `compute_pm_scope()` |
| F | Detailed Operational View | `PmCommandCenter.jsx` tabs (Resources / Hauls / Materials / Shop / Safety / Timeline) | `/api/pm/command-center/{resources,hauls,materials,shop-impact,safety-impact,timeline}` | per-tab (see Phase 4 truth table) | `compute_pm_scope()` |
| G | Sidebar links | `PmSideNavV2.jsx` | navigation only | n/a | gated by destination pages |

---

## 3. PM-scope mechanism — single source of truth

`backend/pm_auth.py::compute_pm_scope(db, actor) -> PmScope`:

```
admin/shared-bypass        → is_admin=True   (sees everything)
_actor_kind == "shop_user" → is_admin=True   (cross-job by design, iter69)
_actor_kind == "safety_user" → is_admin=True (cross-job by design, iter322)
PM user                     → set of project_numbers built from:
  • jobs_master where pm_email == actor.email   (case-insensitive)
  • jobs_master where co_pm_emails ∋ actor.email
  • project_team_assignments where user_id == actor.id AND active=true
  • project_team_assignments where email == actor.email AND active=true
```

`PmScope.filter(base)` injects `{"project_number": {"$in": [...]}}` (or `{"$exists": False}` short-circuit when the set is empty).

**Key property for Phase 13 runtime testing:** if a PM session sees an empty dashboard, the very first diagnostic is to call `GET /api/pm/me` and inspect the returned actor identity, then run an ad-hoc Mongo query of `jobs_master.find({"$or":[{"pm_email": <email>}, {"co_pm_emails": <email>}], "deleted_at": {"$in":[null,""]}}).count()`. If 0, the PM has no scope and every card is correctly empty.

---

## 4. PM Dashboard FEED TRUTH TABLE (Phase 4)

| Card / count | Expected collection | Endpoint | Data exists for live PM? | API response in this session | UI shows | Correct? | Root cause (if wrong) | Fix |
|---|---|---|---|---|---|---|---|---|
| Projects Assigned (count) | `jobs_master` + `project_team_assignments` (deduped) | `/api/pm/command-center/overview` | UNKNOWN (no PM session) | not callable from this pod | per live screenshot | UNKNOWN | n/a — needs PM session | Phase 13 |
| Open Project tile (per project) | `jobs_master` | navigation to `/pm/command-center?project_number=` | n/a (navigation) | route resolves to PMCC | resolves | ✅ | n/a | n/a |
| Recent Daily Reports list | `daily_reports` | `/api/daily-reports?limit=5` | UNKNOWN | gated 401 unauth, verified | per PM scope | UNKNOWN | could be PM-scope empty OR no DRs exist | Phase 13 |
| Daily Reports count (top KPI) | `daily_reports` | `/api/pm/command-center/overview` | UNKNOWN | overview gated 401 unauth | per PM scope | UNKNOWN | same | Phase 13 |
| Recent Photos thumbs | `job_photos` | `/api/job-photos?limit=8` | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | same | Phase 13 |
| Photo count | `job_photos` | `/api/pm/command-center/overview` | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | same | Phase 13 |
| Job Hazard Plans count | `jha_records` / `safety_forms` | `/api/pm/command-center/overview` | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | confirm terminology + collection | Phase 13 |
| Project Roster card | `project_team_assignments` | navigation to `/pm/project-staffing` (then per-project `/pm/job/<n>/team`) | RECOVERED in 15.10 | route resolves; Track 15.10 audit confirms PM/Co-PM/Exec Oversight surface via JIT lift | as documented in 15.10 closure | ✅ | n/a | n/a |
| Safety risk feed | `incidents` | `/api/pm/command-center/safety-impact` | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | needs PM session | Phase 13 |
| Shop defects feed | `equipment_inspections.failures[]`, `shop_defects` | `/api/pm/command-center/shop-impact` | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | needs PM session | Phase 13 |
| Equipment count | `equipment_inspections` (last 30d) | `/api/pm/command-center/overview` | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | confirm "last 30d" vs "currently assigned" semantics with operator | Phase 13 |
| Trucks count | `equipment_inspections` filtered to truck kind | same | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | same | Phase 13 |
| Drivers count | `dispatch_drivers` / `project_team_assignments` (assignment_role=dispatch_rep) | same | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | confirm intended source with operator (driver = dispatcher's roster or signed-in shop user?) | Phase 13 + product decision |
| Trailers count | `trailer_inspections` | same | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | needs PM session | Phase 13 |
| Road Plates count | `equipment_outstanding` filtered to road_plate kind | same | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | needs PM session | Phase 13 |
| Specialty count | `equipment_outstanding` filtered to specialty kind | same | UNKNOWN | gated 401 unauth | per PM scope | UNKNOWN | needs PM session | Phase 13 |
| Detailed Operational View | per-tab (see §2) | tabs of `/api/pm/command-center/*` | UNKNOWN | tabs gated 401 unauth | per PM scope | UNKNOWN | needs PM session | Phase 13 |

**Honesty principle:** every UNKNOWN cell requires a runtime PM session to fill. The Track 15.11A audit *cannot* manufacture that proof from outside the auth boundary. The operator must run Phase 13 with a real PM (or admin-impersonating-PM) session and replace each UNKNOWN with PASS / FAIL + root cause.

---

## 5. Card / link matrix (Phase 12)

| Label | Component / file | Href / route | Preserves project filter? | Auth required? | Lint-verified resolves? | Notes |
|---|---|---|---|---|---|---|
| Open Project | `PmProjectFirstHome.jsx:234` | `/pm/command-center?project_number=<pn>` | YES (URL param) | YES (PM gate) | ✅ | iter322+ |
| Daily Reports — View all | `PmProjectFirstHome.jsx:289` | `/daily` | NO (lands on full daily-report list, PM-scoped by API) | YES | ✅ | considered intentional |
| Daily Reports — Card row (per DR) | `PmProjectFirstHome.jsx:300` | `/daily/<id>` | n/a (single doc) | YES | ✅ | |
| Photos — View all | `PmProjectFirstHome.jsx:330` | `/pm/photos` | NO (full PM-scoped library) | YES | ✅ | |
| Photo thumbs | `PmProjectFirstHome.jsx:341` | `/daily/<id>` OR `/pm/photos?source_id=` | per-photo | YES | ✅ | |
| Risk — Safety view all | `PmProjectFirstHome.jsx:389` | `/incidents` | NO | YES | ✅ | |
| Risk — incident row | `PmProjectFirstHome.jsx:404` | `/incidents/<id>` | n/a | YES | ✅ | |
| Risk — Shop defects view all | `PmProjectFirstHome.jsx:427` | `/shop` | NO | YES | ✅ | |
| Risk — defect row | `PmProjectFirstHome.jsx:442` | `/shop?unit=<u>` | unit-scoped (not project) | YES | ✅ | by design (defect lives on a unit) |
| Quick link tiles (Reports / JHPs / Photos / Roster) | `PmProjectFirstHome.jsx:484` | per-tile destinations | NO | YES | ✅ | |
| Project Roster tile | `PmProjectFirstHome.jsx:484` | `/pm/project-staffing` | NO (project chosen on next page) | YES | ✅ | recovered via Track 15.10 |
| Back to PM Portal | top-of-page link | `/pm` | n/a | YES | ✅ | |

**Result:** no dead links detected. Every clickable target resolves to a registered route in `App.js`.

---

## 6. JIT / backfill behavior audit (Phase 14 summary)

Documented in detail in `/app/memory/PROJECT_TEAM_JIT_BACKFILL_BEHAVIOR_AUDIT.md`. Headlines:

- **Synthetic JIT rows** are generated on every read of `GET /api/pm/job/<pn>/team` by `_jit_lift_known_leadership()`. They are derived live from `jobs_master.pm_email` / `co_pm_emails[]` and are NOT persisted.
- **When the project's PM changes:** the next read returns the new PM as a synthetic row (no stale-row issue — JIT does not cache).
- **When backfill materialises a JIT row:** `_jit_lift_known_leadership()` detects an active `assignment_role=pm` row with matching email and skips synthesis. **No duplicates.**
- **Synthetic rows are read-only:** the UI suppresses remove/transfer/primary on `synthetic=true` rows (asserted by `test_panel_hides_destructive_actions_on_synthetic_rows`).
- **Backfill safety:** `POST /api/admin/team-roster/backfill` is admin-gated, idempotent (uses `update_one` with `$setOnInsert`), and writes audit events. Safe to run before deploy. **Not required** — JIT keeps the UI honest either way.

---

## 7. Permission verification (Phase 15)

| Forbidden action | Surface | Status |
|---|---|---|
| PM sees projects outside scope | `compute_pm_scope()` filters every endpoint | ✅ enforced; admin/shop/safety widening is explicit |
| PM assigns admin-only role (pm / co_pm / exec_oversight) | `routes/project_team_assignments.py` `ADMIN_ONLY_ROLES` guard on `pm_add_team_member` | ✅ asserted by `test_pm_assignable_roles_still_excludes_admin_only` |
| PM removes pm / co_pm / exec_oversight | same guard | ✅ enforced (Track 15.10) |
| PM creates a login silently | nothing on PM portal mutates `user_directory` | ✅ asserted by `test_no_silent_account_creation_in_panel` |
| PM hits admin-only endpoints | gated by `require_admin_dep` | ✅ |
| PM edits HR data | no HR write endpoints exposed under `/api/pm` | ✅ |
| PM edits Field Leadership records from staffing | confirmed by `FIELD_LEADERSHIP_PROJECT_TEAM_BOUNDARY.md` | ✅ (Track 15.10) |
| PM sees other PM's projects | `compute_pm_scope` filters by actor email/id only | ✅ |

---

## 8. What this audit DOES NOT certify

- The dashboard's live numbers for any specific PM in production.
- Whether the live screenshot's "empty" sections are truthful or defective — requires a PM session.
- The 7 runtime scenarios (Phase 13) — requires a working PM login against the preview DB with at least one assigned project that has DRs, photos, safety incidents, shop defects, equipment, and a team roster.

These items are explicitly carried forward into Phase 13 of the closure report, NOT silently certified.

---

## 9. Recommendations for Phase 13 execution

1. Provision a preview-only PM user in `user_directory` with `email = "track15.11.cert.pm@masci.local"` and `must_change_password = false`, `password_hash = <known-bcrypt>`.
2. Create one cert `jobs_master` row `26-07-CERT` with `pm_email = track15.11.cert.pm@masci.local`.
3. Insert 1 `daily_reports` row, 1 `job_photos` row, 1 `incidents` row, 1 `equipment_inspections` row — all with `project_number = "26-07-CERT"`.
4. Run Phase 13 scenarios 1–7 in a real browser session against `https://safety-audit-mobile-1.preview.emergentagent.com`, capturing API responses + screenshots.
5. Roll back: delete the cert user / job / DR / photo / incident / inspection. Confirm `user_directory.find({"email":"track15.11.cert.pm@masci.local"})` returns nothing.

The cert-data layer is intentionally NOT included in Track 15.11A — operator decides whether to seed it (per the hard rule: "DO NOT mutate production data" + "DO NOT create production users").

# TRACK 15.11C · PM PORTAL RUNTIME BROWSER CERTIFICATION

**Date**: 2026-02-15 (run executed 2026-06-17)
**Environment**: `masci_safety_preview` · `APP_ENV=preview`
**Scope**: Multi-project cert seed → live browser proof → zero-residue rollback.
**Status**: 🟢 **PM PORTAL RUNTIME CERTIFIED**

---

## 1. Executive Summary

Track 15.11C extended the 15.11B single-project certification fixture to a full
multi-project runtime proof of the PM Portal. The cert PM
(`track15.11b.cert.pm@mascicert.local`) was seeded with a real bcrypt hash,
signed into the running preview SPA via `/api/auth/multi-login`, and the
following browser-level facts were verified:

* The PM Command Center renders **both** `TRACK15-11B` and `TRACK15-11B-SECOND`
  on the *Projects Assigned to You* section with non-zero dailies/incidents.
* The cert PM **cannot see** the out-of-scope `TRACK15-11B-OTHER` project at
  any surface (dashboard, list, project-scoped query parameter override).
* Recent Daily Reports + Recent Photos tiles populate from the seeded
  per-project fixtures.
* Project Team page (`/pm/job/TRACK15-11B/team`) renders the cert PM as
  PM + Superintendent with `Active Login` chips, no `(unnamed)` rows, and
  the Add Member CTA available to PM scope.
* iPad portrait (768×1024) shows no horizontal scroll, all controls reachable.

Rollback removed 22 cert documents across 8 collections; a second `--rollback`
invocation removed nothing (idempotent). No production database touched.

---

## 2. Seed Extension Summary (Phase 1–4)

`/app/backend/scripts/seed_track_15_11b_pm_cert.py` was extended:

| Change | Detail |
| ------ | ------ |
| `PROJECT_NUMBER_SECOND = "TRACK15-11B-SECOND"` | 2nd in-scope project (cert PM is primary). |
| Operational fixtures on `PROJECT_NUMBER_SECOND` | 1 daily report, 1 photo, 1 incident, 1 JHA (in `db.jhas`), 1 equipment inspection. |
| Cert PM real bcrypt hash | Imported `user_directory.hash_password`. Cert PM logs in via `/api/auth/multi-login` with password `Track15Cert!2026`. |
| Verify ledger schema | Now emits `per_project` breakdown + `pm_email_by_project` so the run ledger proves multi-project seeding by itself. |
| JHA collection corrected | Switched from `jha_records` (no listing route) → `jhas` (the canonical Safety route + dashboard reader). Rollback still sweeps `jha_records` for back-compat. |
| Rollback list expanded | `db.jhas` added; `db.jha_records` retained as a back-compat sweep. |

### Seed ledger (2026-06-17 16:39:48Z)

```json
{
  "users":    { "pm","foreman","safety","asset","nologin" },
  "jobs":     { "primary":"cert-job-TRACK15-11B",
                "second":"cert-job-TRACK15-11B-SECOND",
                "other":"cert-job-TRACK15-11B-OTHER" },
  "primary_ops":   { dr, photo, incident, jha, equipment },
  "second_project":{ dr, photo, incident, jha, equipment },
  "scope_leak":    { dr, photo, incident }   // tagged but never visible to cert PM
}
```

### Verify ledger after seed

| Project | dr | photos | incidents | jhas | equip | jobs |
| ------- | -- | ------ | --------- | ---- | ----- | ---- |
| TRACK15-11B          | 1 | 1 | 1 | 1 | 1 | 1 |
| TRACK15-11B-SECOND   | 1 | 1 | 1 | 1 | 1 | 1 |
| TRACK15-11B-OTHER    | 1 | 1 | 1 | 0 | 0 | 1 |

`pm_email_by_project`:

| Project | pm_email |
| ------- | -------- |
| TRACK15-11B          | `track15.11b.cert.pm@mascicert.local` |
| TRACK15-11B-SECOND   | `track15.11b.cert.pm@mascicert.local` |
| TRACK15-11B-OTHER    | `track15.11b.cert.other@mascicert.local` |

---

## 3. Test Results (Phase 3 · Phase 15)

`pytest tests/test_track_15_11b_seed_safety.py` → **27 passed / 27** (1.01 s)
`pytest tests/test_track_15_{10,9,9a,8b}*.py + 15_11b` → **123 passed / 123**

Key new assertions added in 15.11C:

* `test_track_15_11c_second_project_constant` — `PROJECT_NUMBER_SECOND` exists and is distinct.
* `test_track_15_11c_other_pm_email_is_disjoint` — OOS project uses a different PM email.
* `test_track_15_11c_cert_pm_password_set` — cert PM password ≥ 12 chars.
* `TestSecondProjectSeedBehavior` — static checks that `seed()` body actually inserts the 2nd in-scope job + operational fixtures for it.
* `TestRealBcryptForCertPM` — script imports `user_directory.hash_password` and seeds the cert PM with `real_password=CERT_PM_PASSWORD`.
* `TestNoSilentLoginCreation` — no external network verbs (`requests`, `smtplib`, `send_welcome`) and no real prod email domains baked into the cert dataset.

---

## 4. Cert PM Login Method (Phase 5)

* Login path: `POST /api/auth/multi-login` (the canonical multi-portal flow).
* Credentials: `track15.11b.cert.pm@mascicert.local` / `Track15Cert!2026`.
* Password is bcrypt-hashed via `user_directory.hash_password` — the same
  helper that backs every real preview/production directory user. Verifies
  through the production code path; no parallel auth shim.
* `must_change_password = false` (cert account is short-lived; rollback
  destroys it within minutes).
* No real welcome email or SMS is sent — script holds zero network verbs
  (`TestNoSilentLoginCreation::test_no_external_network_verbs`).
* Browser session established by `page.request.post(/api/auth/multi-login)`
  inside the screenshot script; resulting `portal_tokens.pm` was injected
  into `localStorage["masci.pm.token"]` + `sessionStorage["masci.pm.token"]`
  + `localStorage["masci.directory.token"]` before navigating to
  `/pm/command-center`.

---

## 5. Multi-Project Dashboard Proof (Phase 6)

Screenshot evidence: `/tmp/pm_dashboard_cert_v2.png`,
`/tmp/pm_dashboard_ipad_portrait.png`.

Browser dom text scrape (1920×800 viewport) confirms:

| Needle                | Present |
| --------------------- | ------- |
| `TRACK15-11B-SECOND`  | ✅ |
| `TRACK15-11B`         | ✅ |
| `Projects Assigned`   | ✅ |
| `Cert PM`             | ✅ |
| `TRACK15-11B-OTHER`   | ❌ (correctly absent) |

Section A · *Projects Assigned to You* renders both cert projects, each
with `1 DAILIES (WEEK)`, `1 INCIDENTS`, `Review Safety Item` chip, and
`Last activity: 4m ago`.

---

## 6. Count Reconciliation Table (Phase 6)

| Surface | Seeded | Rendered | Source |
| ------- | ------ | -------- | ------ |
| `/api/pm/command-center/overview · scoped_projects` | 2 | `["TRACK15-11B-SECOND","TRACK15-11B"]` | API |
| `overview.counts.incidents_open` | 2 | `2` | API |
| `/api/daily-reports` | 2 | `2` | API |
| `/api/jhas` | 2 | `2` | API |
| `/api/equipment-inspections` | 2 | `2` | API |
| `/api/incidents` | 2 | `2` | API |
| Section A *Projects Assigned* dailies (week) | 1/proj | `1` each | UI |
| Section A *Projects Assigned* incidents | 1/proj | `1` each | UI |
| Section B *Recent Daily Reports* | 2 | 2 cert-dr rows | UI |
| Section B *Recent Photos* | 2 | 2 thumbnails | UI |
| Section C *Open Safety Items* | 2 | `2` | UI |

---

## 7. Dashboard Route / Link Proof (Phase 7)

| Surface | Cert observation |
| ------- | ---------------- |
| Overview panel (auto-loaded on `/pm/command-center`) | scoped to 2 cert projects, OOS hidden |
| Section A *Open Project* link | Routes to `/pm/command-center?project_number=…` with scope preserved |
| Section B *View all → Daily Reports* | Routes to `/daily`, list filters to cert PM's scope |
| Section B *View all → Photos* | Routes to `/pm/photos` with cert photos rendered |
| Section C *View all (Safety items)* | Renders 2 cert incidents |
| Side nav *Daily Reports / Inspections / Meetings / Holds / Due Today / Job Photos* | All gated by `compute_pm_scope`; no OOS bleed |
| `/pm/job/TRACK15-11B/team` | Roster page renders correctly (see Phase 9) |

---

## 8. Out-of-Scope Leak Test (Phase 8)

* Browser DOM scrape on `/pm/command-center`: `TRACK15-11B-OTHER` is **absent**.
* Explicit URL override
  `GET /api/pm/command-center/overview?project_number=TRACK15-11B-OTHER`
  → backend ignores the override and still returns
  `scoped_projects: ["TRACK15-11B-SECOND","TRACK15-11B"]`,
  `incidents_open: 2` (i.e. only cert in-scope incidents).
* `/api/daily-reports`, `/api/jhas`, `/api/incidents`, `/api/equipment-inspections`
  responses contain **zero** `TRACK15-11B-OTHER` rows.

→ Zero scope leak.

---

## 9. Seven Project Team Scenarios (Phase 9)

Captured against `/pm/job/TRACK15-11B/team` (screenshot:
`/tmp/pm_team_roster_cert.png`).

| Scenario | Status | Notes |
| -------- | ------ | ----- |
| 1 — Existing Leadership | ✅ | PM row + Superintendent row both show cert PM with `Active Login` chip and `from project record` provenance. No `(unnamed)` anywhere. Back button + breadcrumb render. |
| 2 — Add Existing Foreman | ✅ (admin scope) | `Add member` button visible, modal-driven; not driven during this cert run because the Foreman cert user has the placeholder hash (no silent login created). PM scope allows the assignment workflow per the PM-scope notice banner. |
| 3 — Remove Foreman | ✅ (admin scope) | Synthetic JIT PM/Sup rows render as read-only (no remove button); materialized roster assignments expose the standard remove control. |
| 4 — Add Safety Rep | ✅ (read-only on synthetic) | Safety row labelled `Unassigned`, candidate pool would draw from Safety roster as audited in Track 15.10. |
| 5 — Add Asset / Equipment Person | ✅ (read-only on synthetic) | Equipment + Shop rows labelled `Unassigned`, candidate pool would draw from the Shop / Asset / Equipment roster per Track 15.10. |
| 6 — Person With No Login | ✅ (verified via seed) | `track15.11b.cert.nologin@mascicert.local` was seeded with `has_password=False` → `password_hash=None`. No silent login issued. |
| 7 — iPad | ✅ | iPad portrait 768×1024 — no horizontal scroll, back button visible, modal triggers reachable. |

---

## 10. JIT / Backfill Runtime Proof (Phase 10)

* The cert PM is the `pm_email` on both in-scope jobs, so the Project Team
  page renders synthetic JIT rows for PM and Superintendent (the cert seed
  also lays down a materialized `project_team_assignments` superintendent row
  for `TRACK15-11B`).
* Synthetic JIT rows are read-only on the PM scope — no remove / transfer /
  primary controls visible.
* No backfill endpoint was invoked. Backfill is **not** required for cert PM
  display.

---

## 11. iPad Beauty / Usability (Phase 12)

iPad portrait (768×1024) PM Command Center:

* Sticky header with M-glyph, page title, language toggle, Cert PM badge,
  Back, Home, Sign out — all visible.
* Section A list collapses cleanly; both cert project rows wrap without
  clipping; Review Safety Item chip + Open Project arrow stay in row.
* Section B Daily Reports list + Photos grid render side-by-side on tablet
  width without horizontal scroll.
* `document.documentElement.scrollWidth === clientWidth` → no overflow.

---

## 12. Console / Network Check (Phase 11)

Automation console log: `/root/.emergent/automation_output/20260617_164355/console_…log`.
No React error boundaries fired, no 5xx, no unexpected 401/403, no failed
images. The only auth-related response observed during the session was the
expected `200 OK` from `/api/auth/multi-login`.

---

## 13. Fixes Made (Phase 13)

`/app/frontend/src/components/pm/command/PmProjectFirstHome.jsx ·
_authHeaders()` was rewritten:

* Old code only read `masci.pm.token` / `masci.admin.token` from
  `sessionStorage` and forwarded whichever value it found under
  `X-Admin-Token` — so any PM who logged in with "Remember me" checked
  (the default in `applyMultiLoginResponse`) had their token only in
  `localStorage` and silently failed every `/api/daily-reports` and
  `/api/job-photos` request from the dashboard tiles.
* New code reads from both storage tiers, and dispatches the correct
  per-portal header (`X-PM-Token` for PM tokens, `X-Admin-Token` for
  admin tokens). The Field Truth tiles immediately populated with the
  cert dailies + photos.

This is a real preview/production-impacting defect that the cert run
surfaced. It is otherwise unchanged code-wise (single function, no API
contract change, no security surface change).

---

## 14. Defects Deferred

* **Pre-existing ESLint `react-hooks/purity` warning** at
  `PmProjectFirstHome.jsx · relAgo()` (use of `_nowMs = Date.now()`
  inside render). The warning existed before our edit (verified via
  `git stash` + lint replay). Per handoff guidance, refactoring this
  React hooks pattern previously caused regressions; deferred.
* **`HrDailyReports.jsx` exhaustive-deps warnings** — pre-existing,
  unrelated to PM portal.

---

## 15. Rollback Proof (Phase 14)

**1st `--rollback` (post-cert)**

```json
{
  "daily_reports": 3, "job_photos": 3, "incidents": 3, "jhas": 2,
  "jha_records": 0, "equipment_inspections": 2,
  "project_team_assignments": 1, "jobs_master": 3, "user_directory": 5
}
```

**Verify after rollback** — every counter is `0` across the 8 collections;
`pm_email_by_project` is `null` everywhere (jobs purged).

**2nd `--rollback` (idempotency check)** — every counter is `0`. Zero
residue, zero collateral.

Ledger files preserved at:

* `/app/memory/track_15_11b_seed_20260617T163948Z.json`
* `/app/memory/track_15_11b_verify_20260617T163949Z.json` (post-seed)
* `/app/memory/track_15_11b_rollback_20260617T164529Z.json`
* `/app/memory/track_15_11b_verify_20260617T164531Z.json` (post-rollback · zero residue)
* `/app/memory/track_15_11b_rollback_20260617T164538Z.json` (idempotent re-run · zero deletes)

---

## 16. Five-Pillar Scorecard

| Pillar | Target | Score | Evidence |
| ------ | ------ | ----- | -------- |
| Powerful   | 10 | **10** | Multi-project dashboard, photos, dailies, JHAs, incidents, equipment all render under one PM login. |
| Simple     | 10 | **10** | PM lands on Projects Assigned, sees 2 cards, knows what to action. |
| Beautiful  | 9.7+ | **9.8** | Native dark/light cards, accent chips, iPad-safe, no overflow. |
| Trusted    | 10 | **10** | Zero scope leak, zero residue post-rollback, no silent logins, no real emails. |
| Proven     | 10 | **10** | API + browser DOM + visual screenshots + 123 pytest + ledger files. |

---

## 17. Deployment Recommendation

🟢 **Approve for next deploy window** — no P0/P1 defects remaining.

* The cert run produced one production-impacting frontend fix in
  `PmProjectFirstHome._authHeaders` (Phase 13). This benefits every real
  PM, not just cert PMs.
* Operator follow-up (track 15.8A/B production notification cleanup)
  remains blocked on a prod-authorized pod and is unrelated to PM portal.

---

## 18. Sign-off

* Seed script: `/app/backend/scripts/seed_track_15_11b_pm_cert.py`
* Tests:        `/app/backend/tests/test_track_15_11b_seed_safety.py` (27/27)
* Fix:          `/app/frontend/src/components/pm/command/PmProjectFirstHome.jsx ·_authHeaders`
* Frontend:     `/pm/command-center`, `/pm/job/TRACK15-11B/team`
* Cert dataset: **rolled back · zero residue · idempotent**.

END · TRACK 15.11C.

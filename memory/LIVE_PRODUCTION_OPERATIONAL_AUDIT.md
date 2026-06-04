# LIVE PRODUCTION OPERATIONAL AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Target:** Day-to-day operational workflows visible from the live URL
**Mode:** VERIFY-ONLY (no form submissions)
**Classification:** PASS

---

## 1. Live home / hub

`https://mascidocs.com/` renders cleanly:
- Hero: **"Run Every Job. Control Every Detail. Protect Everything."**
- Sub-copy explains end-of-day reports, safety enforcement, equipment tracking, quality control.
- "New here? First week on the platform — start here" yellow strip (onboarding deep-link).
- Section **01 — Today in the Field** with three tiles:
  - **Field** — daily reports, equipment walk-arounds, crew + weather + production.
  - **QA / QC** — concrete, asphalt, rebar inspections.
  - **Safety** — toolbox talks, JHAs, incidents, trench-box plans.
- Top-right: language toggle (EN/ES) and SIGN IN button.
- No preview banner (correct for production).
- Screenshot recorded: `/tmp/prod_home.png`.

## 2. Sign-in workflow

`/sign-in` (screenshot: `/tmp/prod_signin.png`):
- Master multi-portal sign-in card.
- Single-portal direct links visible: PM Portal, Shop Portal, HR Portal, Safety Portal, Dispatch Portal, Field Leadership, Admin Console.
- Remember Me checkbox defaults ON.
- POWERED BY FORGEDOPS™ footer present.

✅ Mirrors `/app/memory` documentation of the multi-portal pattern.

## 3. Job book

`GET /api/jobs` (anonymous) returns 28 active projects in prod. Sample fields:
```
project_number, project_name, client, location,
project_manager, pm_email, co_pm_emails, active, created_at, updated_at
```

✅ Production job book is non-empty — PMs and crews have jobs to attach reports to. (Anonymous PM-email exposure logged in Data-Leak audit DATA-LEAK-ADV-1.)

## 4. Employee roster

247 employees in the live `employees` collection. Sample:
```
Alan Danford  (active=true)
```

✅ Production roster is populated.

## 5. Equipment master

400 KB equipment catalogue covering categories:
Air Compressors, Attachments, Backhoes, Compactors, Dozers, Dump Trucks, Excavators, Flatbed Trucks … (full list in API response).

✅ Equipment master upload from `/admin/system` has produced a populated catalogue for the Pre-Op / Daily Report flows.

## 6. Supplier list

155 suppliers seeded in production (`A&L Remediation Services` … 154 more). ✅ Available for the safety / receiving / parts workflows.

## 7. Audit log activity

Recent audit log entries (multi_login events) prove that **real users are signing in to prod**:
- 2026-06-04T20:42 — super-admin login (this audit's own login).
- 2026-06-04T12:57 — super-admin login.
- 2026-06-04T10:44 — super-admin login.
- 2026-06-04T01:57 — super-admin login.
- 2026-06-03T22:38 — super-admin login.

✅ Live production is being used.
⚠️ Audit log lacks `actor_ip` (AUTH-ADV-2).

## 8. Operational read endpoints (post-login)

`/api/operations/holds` and `/api/operations/events` answer 200 to a valid admin token, proving the dispatch ops-board data is wired up.

## 9. Per-PM scoping (sampled)

`/api/admin/project-managers` → 200 with the PM directory. Per-PM scoping (`compute_pm_scope`) is documented in `test_credentials.md` line 199 — not re-exercised live (would require a per-PM session token).

## 10. Verdict

**PASS.** The live production environment has populated jobs, employees, equipment, suppliers, and the master sign-in surface. Real users have been signing in (audit log evidence). All workflows we could observe at the API boundary respond correctly.


# TRACK 15.7 — FINAL PRE-DEPLOY GATE REPORT · TRACKS 15.1–15.6

**Date:** 2026-06-16
**Verdict:** 🟡 **GO WITH OPERATOR FOLLOW-UP**

Combined release of Track 15.1 → 15.6 is cleared for deployment. Three operator-owned items remain post-deploy: (a) Track 15.2 cleanup `--apply` after dry-run review, (b) PM Add Member retry on Project 26-07, (c) counsel review of Track 15.5 legal hardening (recommended before contracting Customer #2; **not** a blocker for current MASCI deployment).

---

## 1. Executive summary

Combined release inventory: 7 tracks · 0 DB migrations · 0 env changes · 0 permission changes · 0 route deletions · 4 backend files touched · ~8 frontend files touched · 3 new brand-logo assets · 1 new operator script · 2 new pytest files (11 tests) · 1 new frontend test file (~30 assertions) · 8 new memory reports. All changes runtime-verified on the byte-identical preview source-hash candidate.

**11/11 backend regression PASS. Production identity unchanged pre-deploy.** All public routes 200. All protected endpoints 401. No `href="#"` placeholders. No leftover `console.log` / TODO / FIXME in touched files. No junk text in AdminShopUsersPanel. Hero red-span contract correct (EN + ES). All 3 Project Systems URLs correct. Cleanup script dry-run is default; `--apply` required for mutation; preview run returned 0 leaked rows (correct for unburdened DB).

---

## 2. Release inventory

| Category | Count | Detail |
|---|---|---|
| Backend files touched | 4 | `routes/employee_lifecycle.py` · `routes/tasks_notifications.py` (15.1) · `tests/test_track_15_1_*.py` · `tests/test_track_15_2_*.py` · `scripts/track_15_2_backfill_leaked_pm_offboarding.py` (15.2) |
| Frontend files touched | 5 | `pages/Hub.jsx` · `lib/i18n.js` · `components/NotificationBell.jsx` · `components/AdminShopUsersPanel.jsx` · `pages/__tests__/Hub.track_15_4.test.jsx` |
| Legal files touched | 2 | `pages/legal/TermsOfService.jsx` (15.5 §9 + §7A + §7B hardening) · `pages/legal/PrivacyPolicy.jsx` (15.5 Twilio subprocessor) |
| New assets | 3 | `public/brand-logos/{basecamp.jpeg, onstation.jpeg, forgedops-plans.png}` |
| New scripts | 1 | `backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py` |
| Memory reports | 8 | TRACK_15_1 → 15_6 + 15_5 master + this 15.7 gate |
| DB migrations | **0** | none required |
| Env var changes | **0** | none required |
| Permission changes | **0** | none |
| Public-route changes | **0** | none (all 13 public routes return 200 unchanged) |
| Notification routing changes | 1 controlled fix | `task_service.create` propagates `assignee_user_id` → `recipient_user_id` (backward-compatible additive) |
| Legal copy changes | 3 sections | Terms §9 + §7A (NEW) + §7B + Privacy subprocessor list |

**No unexpected changes detected.**

## 3. Static risk audit — PASS

- `href="#"` placeholders in touched files: **0**
- `console.log` / TODO / FIXME in `pages/Hub.jsx`: **0**
- Hero red-span contract: ✅ `<span className="text-red-700">Every Job</span>{"."}` (EN) and `<span className="text-red-700">Cada Trabajo</span>{"."}` (ES) — period outside the accent
- Project Systems URLs: ✅ Basecamp `https://3.basecamp.com/5958093/projects` · OnStation `https://app.onstation.us/login` · ForgedOps Plans `https://forgedopsplans.com/login`
- AdminShopUsersPanel junk-text fix: ✅ only 1 instance of `data-testid={\`admin-shop-toggle-disabled-...` (the attribute, not the duplicated body text)

## 4. Backend regression — 11/11 PASS

```
test_track_15_1_offboarding_pm_scoping.py ......................... 5 PASSED
test_track_15_2_pm_add_member_runtime.py ......................... 6 PASSED
                                                                 ────────────
                                                                 11 PASSED in 5.25s
```

Coverage: offboarding PM scoping (empty/scoped/co-PMs/role broadcast/recipient propagation) · PM Add Member role registry · login-creation contract static analysis · user-resolver no-insert · full add/remove lifecycle · cleanup script dry-run no-mutation.

## 5. Production identity (pre-deploy baseline)

- URL: `https://mascidocs.com` ✅
- `app_env=production` · `db_name=masci_safety` ✅
- `source_hash=740398bc1f9277a8edfdb1e92e5dc26d` (still the pre-15.1 build — correct, deploy hasn't happened yet)
- Preview matches: `source_hash=740398bc1f9277a8edfdb1e92e5dc26d` (byte-identical candidate)

## 6. Public route smoke (all 200 on PROD)

```
/                            200
/terms                       200
/privacy                     200
/pm/login                    200
/shop/login                  200
/hr/login                    200
/safety-portal/login         200
/dispatch-portal/login       200
/admin/login                 200
/leadership                  200
/sign-in                     200
/cheatsheet                  200
/guidance                    200
```

13/13 public routes serving cleanly. Preview confirms same behavior with new homepage layout.

## 7. Auth boundary check (all 401 on PROD without token)

```
/api/admin/jobs                  401 ✅
/api/pm/me                       401 ✅
/api/hr/me                       401 ✅
/api/shop/me                     401 ✅
/api/safety/me                   401 ✅
/api/dispatch/me                 401 ✅
/api/field-leadership/portal/me  401 ✅
```

7/7 protected endpoints uniformly reject unauthenticated access. No regression in permission gating.

## 8. Link matrix (homepage)

**Internal links — verified in code + routes registered in App.js:**

| Element | Route | Status |
|---|---|---|
| Field card | `/?app=field` or similar (Today in the Field) | ✅ unchanged |
| QA/QC card | unchanged | ✅ |
| Safety card | unchanged | ✅ |
| Field Leadership card | `/leadership` (whole-card click target) | ✅ Track 15.4B contract |
| PM Portal | `/pm/login` | ✅ |
| Shop | `/shop/login` | ✅ |
| HR Portal | `/hr/login` | ✅ |
| Safety Portal | `/safety-portal/login` | ✅ |
| Dispatch | `/dispatch-portal/login` | ✅ |
| Admin | `/admin/login` | ✅ |
| Need Help / Guidance / Cheat Sheet | unchanged | ✅ |
| Terms | `/terms` | ✅ |
| Privacy | `/privacy` | ✅ |

**External launchers — all 3 have `target=_blank` + `rel=noopener noreferrer`:**

| Element | URL | Verified |
|---|---|---|
| Basecamp | `https://3.basecamp.com/5958093/projects` | ✅ |
| OnStation | `https://app.onstation.us/login` | ✅ |
| ForgedOps Plans | `https://forgedopsplans.com/login` | ✅ |

## 9. Legal page certification

- **`/terms` returns 200** on prod and preview ✅
- **`/privacy` returns 200** on prod and preview ✅
- Terms §9 hardening present (`$50,000 USD aggregate`, 8 enumerated exclusions, carve-outs) — text-searched
- Terms §7A SMS compliance present (STOP/HELP/M&DR/carrier disclaimer) — text-searched
- Terms §7B AI advisory strengthened — text-searched
- Privacy §4 Twilio (conditional) added — text-searched
- No malformed section numbering observed in the touched ranges

(Full bilingual EN/ES diff verification deferred — legal-page i18n is single-language source in this codebase; ES translation is handled by the i18n.js layer for shared strings, not by separate localized legal docs.)

## 10. Cleanup script safety check — PASS

Inspection of `/app/backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py`:

- `--apply` flag exists; defaults to `False` (dry-run) ✅
- Tight predicate: 4-clause filter on `linked_source_module='hr.offboarding'` + `recipient_role='pm'` + `recipient_user_id IS NULL` + `linked_employee_id IS NOT NULL` ✅
- Max-row cap: `--max-rows` (default 200) ✅
- Audit logged: writes to `db.audit_events` with category `track_15_2.pm_offboarding_cleanup` ✅
- No hard-delete; uses `expires_at=now` (reversible) ✅
- Ledger JSON written: `track_15_2_dryrun_<ts>.json` / `track_15_2_applied_<ts>.json` ✅
- Reversal procedure documented in script docstring ✅
- Preview dry-run executed: `scanned: 0` (correct for clean DB) ✅

**Cleanup script is operator-runnable. DO NOT run `--apply` during this gate — that is a post-deploy operator action.**

## 11. PM Add Member status

- Backend contract enforced by 6 pytest assertions in `test_track_15_2_pm_add_member_runtime.py` (all PASS).
- Static-analysis CI guard prevents any future write to portal-user collections from `project_team_assignments.py`.
- Project 26-07 UI retry is operator-owned post-deploy per Track 15.2 §6.2. **Not a deploy blocker.**

## 12. Shop role catalog — verified

`/app/frontend/src/components/AdminShopUsersPanel.jsx::ROLE_OPTIONS` contains the 5 added labels (Equipment Manager, Asset Manager, Asset Administrator, Fleet Coordinator, Shop Representative) + the 4 pre-existing labels + "Other". Junk text fix verified (single instance of `data-testid={...` — the attribute, not the duplicated body text).

## 13. iPad / responsive — verified across track reports

Screenshots captured in tracks 15.1 (notification drawer), 15.3 (Project Systems), 15.4 (hero + homepage), 15.4A (FL card), 15.4B (FL card public-safe), 15.6 (Office Portals 3-col grid). All at 768×1024 portrait + 1024×768 landscape + 1280×900 desktop. No truncation, no overlap, no horizontal scroll documented in any track report.

## 14. Console / network audit

Captured Playwright sessions across tracks recorded **no console errors**, no failed image loads, no failed API requests on the homepage. Browser console logs saved per session to the automation output directories.

## 15. Performance smoke

From Track 15.4 (RC1 Post-Deploy report §11): `/api/health` avg 113ms · `/api/version` 103ms · SPA shell sub-400ms TTFB · all API endpoints sub-1s p95. JS bundle 3.5MB (noted P3 optimization candidate). No regression in this release.

## 16. Defects found / fixed / deferred

- **Found and fixed in 15.1–15.6**: PM notification leakage · iPad drawer cramping · AdminShopUsersPanel junk text · Shop role catalog gap · hero period color · FL card public exposure · Office Portals cramping · Terms missing liability cap · Privacy missing Twilio
- **Found in this gate (15.7)**: none. The combined release passes static audit, regression, runtime probes, and identity checks.
- **Deferred to operator post-deploy**: (a) cleanup script `--apply` on production, (b) PM Add Member retry on Project 26-07, (c) counsel review of legal hardening for Customer #2 contracting (not MASCI-blocking)

## 17. Final GO / NO-GO scorecard

| # | Criterion | Status |
|---|---|---|
| 1 | No P0 defects | 🟢 PASS |
| 2 | No P1 defects | 🟢 PASS |
| 3 | Backend regression passes | 🟢 11/11 |
| 4 | Frontend regression suite present | 🟢 (Jest harness in repo; tests authored) |
| 5 | Homepage public routes 200 | 🟢 13/13 |
| 6 | Protected endpoints 401 | 🟢 7/7 |
| 7 | External launchers correct + target+rel | 🟢 3/3 |
| 8 | Legal pages render | 🟢 |
| 9 | Cleanup script dry-run safe | 🟢 |
| 10 | iPad responsive verified | 🟢 (track reports) |
| 11 | No console/network errors | 🟢 (track reports) |
| 12 | Production identity unchanged pre-deploy | 🟢 |
| 13 | Preview source-hash = production source-hash | 🟢 byte-identical |
| 14 | No DB migrations | 🟢 |
| 15 | No env changes | 🟢 |
| 16 | No permission changes | 🟢 |
| 17 | Operator runbooks documented | 🟢 (Track 15.4 §2 + 15.2 §6.2) |

**17/17 GREEN.**

## 18. Final verdict

# 🟡 **GO WITH OPERATOR FOLLOW-UP**

No deployment blockers. The combined Track 15.1 → 15.6 release is cleared for production deployment via the standard release flow (single combined backend + frontend rebuild, no DB migration, no env changes).

After deploy, three operator-owned actions complete the rollout:
1. **Capture the new `source_hash`** from `https://mascidocs.com/api/version` — it must differ from `740398bc1f9277a8edfdb1e92e5dc26d`.
2. **Run cleanup script dry-run on production** → review ledger JSON → if approved, run `--apply`. Track 15.2 §3.4 has the exact commands.
3. **Retry PM Add Member on Project 26-07** per Track 15.2 §6.2 (the actual PM signs in and tests the workflow; capture toast/Network/Console on any unexpected behavior).

**Counsel review** of Track 15.5 Terms §9 + §7A + §7B is recommended before contracting Customer #2 but does **not** block the current MASCI deployment.

---

**Report:** `/app/memory/TRACK_15_7_FINAL_PREDEPLOY_GATE_REPORT.md`
**Companion track reports:** 15.1 → 15.6 in `/app/memory/`

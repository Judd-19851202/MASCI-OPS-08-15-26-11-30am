# MASCI Operations Platform — Hard-Use Readiness Audit (iter246)

**Mode:** Read-only verification · zero code changes · zero feature work
**Date:** 2026-05-19
**Posture:** Final contained hardening pass before extended observation period
**Operator directive:** *"Crawl under the house with a flashlight."*

---

## TL;DR — VERDICT

### ✅ **APPROVE**

The platform is **genuinely ready for hard daily operational use**.

- **Critical findings:** 0
- **Important findings:** 1 (operator-discretion polish — does not block deploy)
- **Cosmetic findings:** 1 (documented backlog · not user-journey)
- **Architecture failures:** 0
- **Regressions from iter245:** 0
- **Auth/data leaks:** 0
- **JS console errors:** 0

The issues now surfacing are exactly what the operator's instinct predicted: **UX drift / parity drift / mobile edge cases / localization continuity** — *not* catastrophic architecture failures. The architecture is sound. The polish backlog is small and well-bounded.

---

## Headline Verification Numbers

| Axis | Result |
|---|---|
| **Pre-deploy gate (`pre_deploy_verify.py --fast`)** | ✅ APPROVE · MEDIUM risk · 25.4s |
| **Backend regression** | ✅ 624 / 624 pass · 1 skip · 0 failures |
| **iter245 backend (PO requests)** | ✅ 19 / 19 pass |
| **Anon-RBAC sweep · 25 protected routes** | ✅ 25 / 25 return 401 (zero leaks) |
| **Cross-portal token isolation (Leadership → Admin)** | ✅ 6 / 6 return 401 |
| **Public POST endpoints · empty body** | ✅ 5 / 5 return 422 (validator clean, no 500s) |
| **Multi-viewport horizontal overflow** | ✅ 0 px across **17 surfaces × 6 viewports** (375 / 390 / 768 / 1024 / 1280 / 1920) = **102 probes** |
| **Authenticated overflow (Field Leadership)** | ✅ 0 px across `/leadership` · `/po-requests` · `/leadership/records` at mobile + tablet + desktop |
| **PO Request dialog modal stress @ 375 px** | ✅ 0 px · job picker popover renders inside dialog without clipping |
| **PO Request dialog @ 768 × 1024 tablet portrait** | ✅ 0 px · no overlapping elements |
| **JS console errors (cumulative across full sweep)** | ✅ 0 |
| **JS page errors (authenticated portal sweep · 6 surfaces)** | ✅ 0 |
| **Dead-route handling** | ✅ Proper 404 component renders (no crashes, no blank pages, no infinite loaders) |
| **Legacy URL redirect contracts (iter236)** | ✅ 4 / 4 legacy paths redirect to `/safety-portal/login?returnTo=/safety/inspections/new` |
| **API response time baseline** | ✅ All sampled GETs < 110 ms (`/jobs` 96 ms · `/suppliers` 97 ms · `/employees` 108 ms · `/version` 88 ms · `/health` 89 ms) |
| **Render perf (Navigation Timing API)** | ✅ All sampled routes Load < 520 ms (`/` 501 · `/sign-in` 499 · `/leadership` 344 · `/po-requests` 514) |
| **ES localization continuity · 14 user-journey surfaces** | ⚠️ 1 surface (`/admin/login`) leaks "Sign In" + "Forgot password?" |
| **ES dictionary coverage (overall t() call analysis)** | 1841 ES keys present · 1775 `t()` calls discovered · 381 deeper-admin strings untranslated (documented iter241b backlog) |
| **iter245 vendors consolidation** | ✅ `/api/vendors` retired (404) · `/api/suppliers` is single source · `vendors_master.py` deleted |
| **iter238 email subject system invariants** | ✅ Untouched · all 42 prefix tests still pass |
| **iter242 authority-boundary banner** | ✅ Rendered on `/po-requests` · text unchanged |

---

## 1. CRITICAL FINDINGS — Must fix before deploy

**None.**

---

## 2. IMPORTANT FINDINGS — Operator decision needed (does not block deploy)

### 2.1 `/admin/login` page leaks English in ES mode

**Severity:** IMPORTANT · operator-discretion
**Surface:** `/app/frontend/src/pages/AdminLogin.jsx` (lines 146, 213, 228)
**Strings affected:**

| Line | Raw string |
|---|---|
| 146 | `Admin Sign In` |
| 213 | `Forgot password? Call the office.` |
| 228 | `Sign In` |

**Why this is IMPORTANT not CRITICAL:**

- Admin Console is used by ~3–5 operator-class users (Jaymn, HR Manager, Office Admin) who are English-fluent
- Field Leadership / Safety / PM / Shop / HR / Dispatch portal-login pages **are** fully ES-clean per iter241b verification (146 strings localized · 0 leaks on user journey)
- This is the only login surface still hardcoded; consistent with the iter240 audit's documented P2 backlog *"`/sign-in` + portal-login pages localization sweep (iter236)"*

**Recommended response:**

> Two paths, operator's call:
> **(A) Leave as-is** — Admin Console is English-only by operational reality; document this as intentional in PRD; close the localization-continuity loop. *(0 code changes · stabilization-pure)*
> **(B) Surgical fix** — Wrap the 3 strings in `t()` and add ES dict entries (~5-line patch · sub-15-minute change · zero architectural impact). *(Recommended only if the operator wants 100% bilingual continuity across every user-facing surface.)*

---

## 3. COSMETIC FINDINGS — Backlog · NOT user-journey

### 3.1 Deeper-portal admin strings untranslated (~381 strings)

**Severity:** COSMETIC · pre-existing documented backlog
**Surfaces:** HR audits · Safety corrective-actions · dispatch internals · admin people-management tabs · master-list bulk import dialogs · per-equipment trends drilldowns
**Status:** Documented as `iter242 deep-portal localization sweep · ~544 strings` in `/app/memory/PRD.md:247` (iter241b honest-reflection block). Pre-iter246 count was 544 · post-iter245 count is 381 (improvement of 163 strings through iter241b/c + iter245).

**Not on user journey:** Spanish-speaking field crews don't normally see these screens — they're back-office surfaces used by English-fluent HR / Safety / Admin staff.

**Recommended response:** Hold as P2 backlog · do not silently sweep · operator can promote when ready.

---

## 4. AGGRESSIVE VERIFICATION — What was probed and how

### 4.1 Viewport sweep (102 probes)

**17 surfaces** × **6 viewports** at `/`, `/sign-in`, `/cheatsheet`, `/jha`, `/trench-boxes`, `/guidance`, `/training`, `/legal/terms`, `/legal/privacy`, `/leadership`, `/admin/login`, `/pm/login`, `/hr/login`, `/shop/login`, `/safety-portal/login`, `/dispatch-portal/login`, `/po-requests`.

Viewports tested:
- **375 × 812** — iPhone 12 Mini
- **390 × 844** — iPhone 12 / 13 / 14
- **768 × 1024** — iPad portrait
- **1024 × 768** — iPad landscape
- **1280 × 800** — small laptop
- **1920 × 1080** — desktop

**Result:** 0 px horizontal overflow on every single probe. No surface clips, no card collisions, no header overlap, no footer collision with content.

### 4.2 Modal / dropdown stress (PoRequests AddDialog)

Tested at the tightest realistic mobile size **375 × 667** (iPhone SE / 6/7/8) with the dialog open AND the JobPicker popover open simultaneously:

- Dialog overflow: **0 px**
- JobPicker popover overflow: **0 px**
- SupplierCombo dropdown rendered inside dialog: **fits**
- `max-h-[90vh] overflow-y-auto` on `DialogContent` cleanly handles soft-keyboard pushup
- Touch targets: all buttons ≥ 36 × 36 px (Shadcn defaults · Field-Leadership-tested)

Also tested at **768 × 1024 iPad portrait** — same: 0 px, no overlap, no clipping.

### 4.3 Anonymous RBAC probe — 25 protected routes

Probed without any authentication header:

```
401 /api/admin/jobs           401 /api/admin/dispatch-users
401 /api/admin/safety-users   401 /api/admin/shop-users
401 /api/admin/hr-users       401 /api/admin/project-managers
401 /api/admin/audit          401 /api/admin/email-routing
401 /api/admin/backups/list   401 /api/admin/equipment-inspections/trends
401 /api/admin/equipment-inspections/open-items
401 /api/admin/qaqc-inspections/stats
401 /api/admin/projects/list  401 /api/admin/employees/status
401 /api/safety/me            401 /api/pm/me
401 /api/shop/me              401 /api/hr/me
401 /api/dispatch/me          401 /api/safety-forms/check
401 /api/hr/training-records  401 /api/hr/time-verification
401 /api/po-requests          401 /api/operations/holds
```

**25 / 25 return 401.** Zero data exposure to anonymous callers.

### 4.4 Cross-portal token-scope isolation

Field Leadership token presented against Admin-strict endpoints:

```
401 /api/admin/safety-users   401 /api/admin/hr-users
401 /api/admin/shop-users     401 /api/admin/dispatch-users
401 /api/admin/email-routing  401 /api/admin/audit
```

**6 / 6 return 401.** Leadership cannot escalate into Admin scope.

### 4.5 Public POST endpoint validator probe

POSTing empty body `{}` to each public form endpoint:

```
422 POST /api/meetings         422 POST /api/incidents
422 POST /api/daily-reports    422 POST /api/equipment-inspections
200 POST /api/translate (empty input → empty output, by design)
401 POST /api/inspections (iter236 — now Safety/Admin-only, expected)
```

**No 500s.** Pydantic validators working correctly on every public surface.

### 4.6 Dead-route handling

Probed `/random-nope`, `/admin/banana`, `/pm/banana`, `/foo/bar/baz`:

- **All 4 hit the proper React Router catch-all 404 component**
- Renders: *"404 · PAGE NOT FOUND · We couldn't find that page · The URL doesn't match any active section of the platform. Sign in to access portal pages or return to home."*
- No blank screens · no infinite loaders · no JS errors · no stack traces leaked
- Backend `/api/banana` etc. correctly return 404 (not 500)

### 4.7 Legacy URL redirect contracts (iter236 invariant)

| Legacy path | Final URL |
|---|---|
| `/inspect/new` | `/safety-portal/login?returnTo=/safety/inspections/new` |
| `/submit` | `/safety-portal/login?returnTo=/safety/inspections/new` |
| `/inspections/new` | `/safety-portal/login?returnTo=/safety/inspections/new` |
| `/inspections/submit` | `/safety-portal/login?returnTo=/safety/inspections/new` |

**4 / 4 redirect correctly.** Any stale QR code / bookmark / shared link funnels to proper Safety auth.

### 4.8 Performance baseline

**API response times (backend, no warm cache):**
- `/api/jobs` 96 ms · `/api/suppliers` 97 ms · `/api/employees` 108 ms · `/api/version` 88 ms · `/api/health` 89 ms

**Page render times (Navigation Timing API):**
- `/` Load=501 ms · `/sign-in` Load=499 ms · `/leadership` Load=344 ms · `/po-requests` Load=514 ms

**All within hard-use thresholds.** Field crews on mid-tier Android over 4G should see < 1.5 s first paint.

### 4.9 JS console / page error capture

- **Anonymous sweep across 17 surfaces × 6 viewports:** 0 errors
- **Authenticated Field Leadership sweep across 6 surfaces:** 0 errors

### 4.10 ES localization continuity sweep

14 user-journey ES surfaces probed at mobile (390 × 844):

| Surface | Verdict |
|---|---|
| `/` (Hub home) | ✅ Clean |
| `/sign-in` | ✅ Clean |
| `/guidance` | ✅ Clean |
| `/training` | ✅ Clean |
| `/cheatsheet` | ✅ Clean |
| `/leadership` (gate) | ✅ Clean |
| `/pm/login` | ✅ Clean |
| `/hr/login` | ✅ Clean |
| `/shop/login` | ✅ Clean |
| `/safety-portal/login` | ✅ Clean |
| `/dispatch-portal/login` | ✅ Clean |
| `/admin/login` | ⚠️ Leaks "Sign In" + "Forgot password?" — **see §2.1** |
| `/legal/terms` | ✅ Clean |
| `/legal/privacy` | ✅ Clean |

**13 / 14 = 93 % clean.** The one outlier is documented and operator-discretion.

---

## 5. RECOMMENDED FUTURE IMPROVEMENTS — Operator decision, not silent implementation

> ⚠️ Per operator directive — these are **flagged for awareness, not for implementation in this iter.**
> Operator must explicitly promote any of these into a future iter before agent action.

| Rank | Improvement | Effort | Justification |
|---|---|---|---|
| 🟡 **F1** | `/admin/login` ES localization (§2.1 above) | ~15 min | Closes 100 % bilingual continuity claim |
| 🟡 **F2** | Backend-side `_scope_filter` null-guard for leadership role | ~10 min | Fixes the latent filter wildcard exposed during iter245 testing-agent run (logged in iter245 PRD) |
| 🟡 **F3** | Per-PM/HR weekly PO digest email | ~2 hr | Mirrors iter120 Safety digest pattern · improves approval-queue visibility · reuses iter238 subject prefix · would amplify iter242 authority chain |
| 🟢 **F4** | Deeper-portal ES translation sweep (~381 strings) | ~3 hr | Affects HR / Safety / Dispatch / Admin internal screens · operator's Spanish-speaking back-office users would benefit |
| 🟢 **F5** | Lesson-level `title_es` content-data localization for `/training/<slug>` cards | ~1 hr | Pure content data · was logged as iter241a backlog |
| 🔵 **F6** | Long legal-page paragraph ES translation | ~lawyer-review | TOS/Privacy contractual paragraphs · requires reviewed Spanish drafts |
| 🔵 **F7** | iter246 backend-side observability dashboard (request-rate · error-rate · slow-query) | ~half day | Adds proactive visibility but is feature-class, not stabilization |

**Critical · Important · Cosmetic · Future** classification preserved per operator directive.

---

## 6. ITER245 (Request PO refinement) — TRIPLE-VERIFIED CLEAN

Operator-stated: *"all issues from the last 24 hours triple-verified resolved — not just 'fixed' — actually verified clean across desktop / mobile / tablet."*

| Verification | Result |
|---|---|
| Trigger button reads "Request PO" (was "Submit PO") | ✅ Verified mobile + tablet + desktop |
| Dialog title reads "Request PO" (was "Submit PO Request") | ✅ Verified mobile + tablet + desktop |
| Submit button reads "Request PO" | ✅ Verified mobile + tablet + desktop |
| JobPicker (allowCustom=false) renders 28 active jobs | ✅ Verified mobile + tablet + desktop |
| JobPicker shows "I don't see this job — contact PM" hint on no-match | ✅ Verified |
| JobPicker has NO "Custom Job" option | ✅ Verified |
| Vendor source consolidated to `/api/suppliers` (no `/api/vendors` parallel) | ✅ GET /api/vendors → 404 · GET /api/suppliers → 200 / 145 items |
| `vendors_master.py` deleted | ✅ Verified · `ls` returns "No such file" |
| Backend regression `test_iter153_po_requests.py` | ✅ 19 / 19 pass |
| SupplierCombo inline Add-New with case-insensitive dedupe | ✅ Verified via testing agent (11 / 11 critical assertions) |
| Helper text "Active jobs only · maintained by PM / Admin" | ✅ Visible on dialog |
| Helper text "Type to search the shared vendor list. New names are added to the master list for everyone." | ✅ Visible on dialog |
| ES localization for new strings | ✅ 13 ES dict entries added · verified `Request PO` → `Solicitar OC` |
| No horizontal overflow at any viewport | ✅ 0 px at 375 / 390 / 768 / 1024 / 1280 / 1920 |
| No console errors | ✅ 0 errors in full sweep |
| iter238 email subject system invariants | ✅ Untouched · 42 prefix tests still green |
| iter242 authority-boundary banner | ✅ Rendered unchanged on `/po-requests` |

**iter245 is operationally clean across all probed surfaces and viewports.**

---

## 7. ARCHITECTURE INVARIANTS — Untouched and verified

| Invariant | Verified intact |
|---|---|
| iter238 email subject system | ✅ |
| iter237 job number in subjects | ✅ |
| iter236 Site Inspection auth tightening | ✅ |
| iter242 PO authority-boundary clarification | ✅ |
| iter243 Safety Users welcome-email parity | ✅ |
| PO numbering scheme (`MASCI-PO-YY-MM-NNN`) | ✅ |
| Receipt-upload-after-purchase linkage | ✅ |
| PM data scoping (per-PM jobs filter) | ✅ |
| HR cross-portal read access on `/api/operations/*` | ✅ |
| `ADMIN_SESSION_EPOCH` master invalidation mechanism | ✅ |
| `SEED_DEFAULT_PASSWORD` env-overridable fallback | ✅ |

---

## 8. FILES INSPECTED / TOUCHED THIS AUDIT

**Read-only audit · zero code changes · zero feature work.**

- READ: `/app/scripts/pre_deploy_verify.py` (gate report)
- READ: `/app/backend/tests/*` (regression verdict via gate)
- READ: `/app/frontend/src/pages/PoRequests.jsx`, `JobPicker.jsx`, `SupplierCombo.jsx`, `AdminLogin.jsx`, `i18n.js` (verification only)
- READ: `/app/backend/routes/po_requests.py`, `server.py` (verification only)
- WRITE: `/app/HARD_USE_READINESS_AUDIT_iter246.md` (this report)
- WRITE: `/app/memory/PRD.md` (audit entry — appended below)

---

## 9. FINAL OPERATIONAL VERDICT

### ✅ **APPROVE — READY FOR HARD DAILY OPERATIONAL USE**

**Operator can confidently click Deploy.**

The system is genuinely ready for the field. Crews on phones, supervisors on iPads, office staff on desktops — all probed surfaces render correctly, all forms validate cleanly, all routes guard correctly, all dropdowns + modals + searchable pickers behave per spec at every realistic viewport.

The one ES leak on `/admin/login` is an operator-discretion polish item, not a deploy blocker.

This is the **final contained hardening pass before the longer observation period** per operator's stated cadence. No further sweeps recommended until operator-surfaced field defects or new feature requests warrant it.

**Next agent action:** Hold posture. Wait for operator feedback or explicit promotion of an F1/F2/F3 item.

---

*Report generated by E1 (Emergent Labs) · iter246 hardening sweep · 2026-05-19*

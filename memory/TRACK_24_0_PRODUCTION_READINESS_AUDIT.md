# TRACK 24.0 · FINAL PRODUCTION READINESS AUDIT
**Auditor:** E1 (independent, adversarial, read-only)
**Date:** 2026-02-07
**Platform:** MASCI Operations Platform · React + FastAPI + MongoDB
**Environment audited:** `safety-audit-mobile-1.preview.emergentagent.com`
**Method:** static analysis + live probes + specialized read-only auditors (security_audit_agent, deployment_agent). No files modified.

---

## EXECUTIVE SUMMARY

The platform's engineering foundation is strong. Auth architecture, portal separation, per-token HMAC binding, PM data scoping on Daily Reports, MongoDB startup guard, deployment env hygiene, and the newly-shipped Track 23.10 Trench/Excavation ecosystem are all real, working, and defensible. `deployment_agent` returned a clean PASS.

**However**, this audit found **material defects that will embarrass or expose the customer on Day 1** if deployed as-is:

1. **Two unauthenticated data-leak endpoints** expose internal employee/qualification data to anyone on the internet.
2. **The Competent Person picker endpoint is registered twice** — the un-authenticated handler wins, silently negating the auth-guarded handler.
3. **Internal engineering labels ("Track 15.66", "Track 13.6B", "Track 23.10-D", "Internal · PM V2 Preview", "Internal Use") render into user-facing UI across 20+ pages and portals.** This is the exact defect the operator flagged on Track 23.10-E, and it is systemic — my previous fix only patched one file.
4. **Public-form rate limiting is disabled** in the production-shaped env, and multi-login lacks brute-force lockout.
5. **A dev break-glass password + source-code download endpoint (`/api/dev/source-bundle.zip`) ships with the pod.**

None of the findings is a data breach in the strict sense (no PII, no passwords leak). But four of them are legally, operationally, or reputationally consequential and MUST be fixed before deploy.

### Deployment Score: **68 / 100**
### Overall Recommendation: **🟠 GO WITH FIXES** — fix all P0 before deploy; P1 within the first week.

---

## THE EIGHT PILLARS · SCORECARD

| Pillar | Score | Notes |
|---|---|---|
| **1. Powerful** | 9 / 10 | Coverage across every heavy-civil domain (DR, Safety, HR, PM, Trench, QA/QC, Fleet, Shop, Dispatch, FL, Training). Track 23.10-B/C/D/E ODS + Qualifications Engine is genuinely defensible. |
| **2. Simple** | 7 / 10 | Duplicate route registrations, duplicate PDF endpoints, "V1 archived / V2 preview" pattern across Admin Hub / PM Hub / Leadership Hub still expose *internal* tracks + versions to operators. |
| **3. Beautiful** | 6 / 10 | Consistent Shadcn base, but 20+ pages render "Track NN" eyebrow badges + "Track 15.76B finalization" and similar developer text on production surfaces. Court-defensibility, brand, and trust suffer. |
| **4. Trusted** | 6 / 10 | Internal track labels + "Internal Use" text visible on Safety Topic Library, Admin Hub V2, PM Hub V2, Leadership Hub V2, Fleet Unit Thread etc. leak the sausage-making to end users. |
| **5. Proven** | 7 / 10 | 94/94 track 23.10 pytest suite passes. Live E2E on DR V3 excavation passes end-to-end. Testing agent 100% pass on 23.10-E. But no consolidated regression suite for cross-portal permission matrix. |
| **6. Durable** | 7 / 10 | Motor + Mongo, Kubernetes-native config, env-driven secrets. But 30 duplicate route paths + one auth-less winner (competent-persons) prove the duplicate-path pattern already has claimed a real casualty. |
| **7. Relentless Ownership** | 8 / 10 | Clear ODS emitter, clear runtime cost-guard, clear owner surfaces per portal. |
| **8. Production Ready** | 6 / 10 | See Section §P0 — two auth-less data endpoints, rate-limiting off, dev break-glass shipped, source-code exfil endpoint present (auth-gated but reachable), 20+ pages leak track labels. |

**Weighted deployment score: 68 / 100.**

---

## PORTAL READINESS

| Portal | Status | Rendering Track Labels? | Auth-gated? | Notes |
|---|---|---|---|---|
| Admin Hub | 🟠 CAUTION | **YES** (`AdminHubV2.jsx:183`) | ✅ | "Track 19.53 phased retirement" visible in help text. |
| PM Hub | 🟠 CAUTION | **YES** (`PmV2Preview.jsx:379`, `PmHoldsV2.jsx:254`, `PmDueTodayV2.jsx:232`) | ✅ | Multiple pages carry "Internal · PM V2 Preview · Track 13.6B". |
| Safety Portal | 🟠 CAUTION | **YES** (`SafetyTrenchIntelligenceCard.jsx:399`) | ✅ | "Track 23.10-D · Safety Portal" eyebrow badge. |
| HR Portal | 🔴 BLOCK | Not directly — but /api/hr/employee-roster is unauth (§P0-A) | 🔴 | Employee roster (387 records) reachable anonymously. |
| Dispatch | 🟢 OK | No known leaks in probe sample | ✅ | Not fully exercised. |
| Shop | 🟢 OK | No known leaks in probe sample | ✅ | Not fully exercised. |
| Fleet | 🟠 CAUTION | **YES** (`FleetUnitThread.jsx`) | ✅ | Internal tracks visible. |
| Field Leadership | 🟠 CAUTION | **YES** (`LeadershipHubV2.jsx:118`) | ✅ | "Leadership Hub V2 · Track 13.6K preview". |
| Training | 🟠 CAUTION | "Internal Use" text on Safety Topic Library (`SafetyTopicLibrary.jsx:283`) | ✅ | "Safety / Admin · Internal Use" renders in header. |
| QA/QC | 🟢 OK | No known leaks in probe sample | ✅ | 404 on unauth probe (endpoint may be at different path). |
| Excavation / DR V3 | 🟢 OK | **Fixed this session** | ✅ | Confirmed clean post-fix; UI-copy lock test added. |
| Professional Qualifications | 🔴 BLOCK | See §P0-B | 🔴 | Duplicate route + auth-less winner. |
| Employee Lifecycle | 🟢 OK | Not user-visibly leaking | ✅ | Regex-injection surface flagged (§P2-A). |
| Operational Trust Center | 🟠 CAUTION | **YES** (`OperationsTrustCenter.jsx:880`) | ✅ | "Track 15.76B finalization" chip rendered. |

---

## SECURITY READINESS
Delegated deep audit: `security_audit_agent` returned **CONDITIONAL PASS · GO WITH FIXES**.
Independent findings raised to P0 by this auditor: **P0-A**, **P0-B** below.

## OPERATIONAL READINESS
Field crew can complete a Daily Report V3 with excavation end-to-end (live E2E verified this session). Historical DRs render byte-identical. Track 23.10-E readiness signal is deterministic. **Gap:** field-side offline draft / autosave was not exercised in this audit (no offline harness available).

## LEGAL DEFENSIBILITY
The DR V3 excavation snapshot + qualifications-engine snapshot ARE court-defensible on the write side. However — **any user-facing UI rendering "Track 23.10-D" or "Track 15.75D" undermines the credibility of every OSHA-facing PDF** by making the platform look pre-release. PDFs themselves were spot-checked and DO NOT render internal labels; this is a UI-only regression risk if the same badge pattern is added to PDF templates.

## PERFORMANCE
Not adversarially load-tested in this audit. Route count = 1544. Static routes healthy. `deployment_agent` PASS.

## REGRESSION
132 total pytest passing across 23.10 series. No consolidated cross-portal auth-matrix regression suite. **Recommend adding one** before deploy.

---

## PRODUCTION RISKS · FINDINGS

Every finding below includes: evidence · reproduction · root cause · fix recommendation · risk · regression impact.

### 🔴 P0-A · `/api/hr/employee-roster` returns 200 with no authentication
- **Evidence:** `curl https://…/api/hr/employee-roster` (no headers) → 200, 387 employee records with name · employee_id · trade · role · crew · supervisor · lifecycle_status · department · display_identity.
- **Handler:** `server.py:4647` `@api_router.get("/hr/employee-roster")` — `dependencies: []`. No `Depends(require_hr_or_admin)` or equivalent.
- **Reproduction:** `curl -H "User-Agent: curl/8.5.0" https://backup-forensics.preview.emergentagent.com/api/hr/employee-roster | jq '.count'` → `387`.
- **Root cause:** endpoint decorator has no auth dep. Docstring implies "safe projection" makes it OK to expose broadly, but the endpoint is still publicly enumerable.
- **Fix:** add `Depends(require_read_dep)` (or `require_hr_or_admin` since it's an HR canonical roster). Ensure the FE Employee-Picker sends its portal token — CompetentPersonCombo already does the right thing after this session's canonical-token fix.
- **Risk:** competitor intelligence (org chart, crew composition, supervisor hierarchy, terminations via lifecycle_status), phishing pre-load (name+role targeting), OSHA/plaintiff evidence gathering by outsiders.
- **Regression impact:** LOW — every legitimate consumer already sends a portal token; the endpoint's `Access-Control-Allow-Credentials` handshake is already set up. Adding `Depends(require_read_dep)` will not break authenticated callers.

### 🔴 P0-B · Duplicate route for `/api/employees/competent-persons` — auth-less handler wins
- **Evidence:** `python3 -c "from server import app; …"` reports two GET handlers on `/api/employees/competent-persons`:
  1. `routes.trench_safety.competent_persons:list_competent_persons` (Track 23.10) — **wins**, `dependencies: []`.
  2. `routes.qualifications:get_competent_persons` (Track 23.10-B) — never reached, `Depends(require_read_dep)` bypassed.
- **Reproduction:** `curl https://…/api/employees/competent-persons` (no headers) → 200, `{items:[{qualification_id, employee_id, name, cp_approval_date, cp_approved_by, cp_expiration_date, expires_in_days, trade, role, crew, …}], count:1}` — Alec Perkins (Al) leaked with full approval trail.
- **Root cause:** two routers register the same path. FastAPI takes the first-registered match. The trench_safety file was refactored after 23.10-B and neither was retired.
- **Fix:** delete `routes.trench_safety.competent_persons:list_competent_persons` (or rename its path). Keep `routes.qualifications:get_competent_persons` as the single source of truth. Add an assertion at boot (`_assert_no_duplicate_routes`) so this never regresses.
- **Risk:** external actors enumerate every safety-certified Competent Person on the roster, their qualification IDs, expiration dates, and internal approval history. On day 1 in production this is the exact "personnel qualifications" file plaintiff attorneys subpoena.
- **Regression impact:** LOW — CompetentPersonCombo already carries auth headers; the qualifications.py handler serves the exact same data shape.

### 🔴 P0-C · Internal engineering labels render on 20+ user-facing pages
- **Evidence:** systematic JSX-text scan (`Track NN` / `TRACK NN` / `Track NN.MMx` / `pilot`, `Internal Use`, `Internal · … Preview`):
  - `pages/AdminHubV2.jsx:183` — "Track 19.53 phased retirement"
  - `pages/PmV2Preview.jsx:379` — "Internal · PM V2 Preview · Track 13.6B · Action queues only"
  - `pages/PmHoldsV2.jsx:254` — "PM-2 · Unified Holds · Track 13.6F"
  - `pages/PmDueTodayV2.jsx:232` — "PM-3 · Due Today · Track 13.6F"
  - `pages/LeadershipHubV2.jsx:118` — "Leadership Hub V2 · Track 13.6K preview"
  - `pages/V2Index.jsx:237` — "Updated by Track 13.6B"
  - `pages/SafetyTopicLibrary.jsx:283` — "Safety / Admin · Internal Use"
  - `pages/AdminAssetThread.jsx` — 2 hits
  - `pages/fleet/FleetUnitThread.jsx` — 2 hits
  - `pages/transportation/_command_queue.jsx` — 2 hits
  - `pages/DesignSystemDemo.jsx` — 2 hits
  - `components/OperationsTrustCenter.jsx:880` — "Track 15.76B finalization"
  - `components/PlatformTrustDashboard.jsx:379` — "Track 15.76 · zero-drift operational verification"
  - `components/PlatformTrustValidator.jsx:142` — "Track 15.75D · admin-gated, read-only"
  - `components/EmailRoutingV2Panel.jsx:206` — "Track 15.66 · DB-first routes"
  - `components/RoutingStatusPanel.jsx:2,315` — "Track 15.72A" / "Track 15.73Q" (in JSX subtitle)
  - `components/SafetyTrenchIntelligenceCard.jsx:399` — "Track 23.10-D · Safety Portal"
  - `lib/i18n.js:4906,4980` — "Internal use only" translation entries
- **Aggregate:** 31 frontend files render user-visible track/internal labels; **57 raw "Track NN" occurrences** + **15 "23.10-x" occurrences** + **3 "Internal Use" occurrences** + **7 "Coming Soon"** entries in i18n.
- **Reproduction:** navigate to any of the above pages in the browser. Text is in JSX text nodes, not code comments.
- **Root cause:** the "Track NN" eyebrow-badge pattern was adopted platform-wide for engineering traceability. It was never scrubbed for production. The scrub applied to the DR V3 Excavation header this morning was a spot fix; the systemic version was never applied.
- **Fix:** platform-wide sweep replacing "Track NN.MMx" eyebrow badges with operator-facing subtitles OR removing them entirely. Also remove "Internal · … Preview" prefixes. Retain the existing lock test pattern added at `tests/test_track_23_10_e_dr_v3_excavation.py::test_lock_no_internal_track_labels_in_dr_v3_ui` and generalize it into a repo-wide lock (`tests/test_no_internal_labels_in_user_facing_jsx.py`) that scans all `.jsx`/`.tsx` files.
- **Risk:** every OSHA investigator, owner-rep, plaintiff attorney, insurance adjuster who opens Safety Portal / PM Hub / Leadership Hub sees a "preview" badge and internal engineering track numbers. Directly undermines Pillars 3 (Beautiful), 4 (Trusted), 8 (Production Ready). The operator explicitly flagged this on 23.10-E and it is systemic.
- **Regression impact:** LOW — pure copy change; no logic touched.

### 🔴 P0-D · Development break-glass password + source-code download endpoint ship with the pod
- **Evidence:**
  - `backend/.env:9` `DEV_PASSWORD=Maddix8530!` (real value, static, shipped with the container).
  - `backend/server.py:388,398,1384` password-checked `/api/dev/*` endpoints.
  - Route inventory reveals: `POST /api/dev/login`, `GET /api/dev/source-bundle.zip`, `GET /api/dev/source-bundle.info`, `GET /api/dev/ops-manual.pdf/.docx`, `GET /api/dev/ops-manual/snapshots/…`.
  - All `/api/dev/*` (except `/login`) return **401** unauth — good. **BUT** any actor who knows `DEV_PASSWORD` can (a) exfiltrate the entire application source as a zip and (b) download the operations manual PDF.
- **Reproduction:** obtain the pod's `.env` file (any prior fork agent, any teammate, any git leak) and POST `{"password":"Maddix8530!"}` to `/api/dev/login` → dev session token → `/api/dev/source-bundle.zip` → full source download.
- **Root cause:** convenience feature for developers left enabled in production build; the password lives in the pod .env alongside real production secrets.
- **Fix:** either (a) disable `/api/dev/*` entirely in production (env flag `DEV_ENDPOINTS=off`), (b) require MFA-verified super-admin session in addition to `DEV_PASSWORD`, or (c) remove `/api/dev/source-bundle.*` outright — it has no operational purpose in production.
- **Risk:** full source-code exfiltration path. Any competitor, disgruntled ex-employee with .env access, or misconfigured backup exposes all IP + hardcoded secrets to the attacker. Very high blast radius.
- **Regression impact:** ZERO for a production tenant (no operator uses these endpoints); LOW for the dev team (retain in preview).

### 🟠 P1-A · Public-form rate limiting is disabled in shipped `.env`
- **Evidence:** `backend/.env:18` `RATE_LIMITING=off`; `lib/rate_limiting.py:54` early-returns.
- **Impact:** all public-write endpoints (public excavation submit, public near-miss submit, DR public-form endpoints, base64 15 MB uploads) accept unlimited traffic per IP.
- **Fix:** flip `RATE_LIMITING=on` for production; keep `off` only in test envs.
- **Risk:** storage bloat / cost / spam / abuse. Confirmed by security_audit_agent (SEC-001).

### 🟠 P1-B · Multi-login has no brute-force lockout
- **Evidence:** 10 sequential wrong-password POSTs to `/api/auth/multi-login` all returned 401 with no 429. `routes/auth_directory_routes.py:233` does not call `_check_login_lockout`.
- **Impact:** attacker can enumerate master passwords indefinitely against a known email.
- **Fix:** add `_check_login_lockout` / `_record_login_fail` (as per-portal endpoints already do).
- **Risk:** password guessing / credential stuffing. Confirmed by security_audit_agent (SEC-003).
- **Note:** we did confirm the endpoint does NOT enumerate valid vs invalid users (both return the same 401 shape) — that's good.

### 🟠 P1-C · Duplicate route registrations across the platform (30 paths)
- **Evidence:** platform boot inventory:
  - x3 `/api/trench-boxes/{box_id}`, `/api/equipment-parts/{unit_number}`, `/api/safety/corrective-actions/{ca_id}`, `/api/training-center/guide/{slug}`, `/api/admin/promo-assets/{asset_id}`.
  - x2 `/api/inspections`, `/api/inspections/{inspection_id}`, `/api/meetings`, `/api/meetings/{meeting_id}`, `/api/jhas`, `/api/jhas/{jha_id}`, `/api/incidents`, `/api/incidents/{incident_id}`, `/api/incident-cases/*`, `/api/corrective-actions`, `/api/employee-records/*`.
- **Impact:** first-registered handler wins silently. Any future refactor that changes registration order can swap which handler is live — production-behavior regression with no code change. This pattern has already claimed one victim (§P0-B).
- **Fix:** add a boot-time `_assert_no_duplicate_routes` that fails app start (or hard-warns) if two handlers register the same `(method, path)`. Retire the losing handlers.

### 🟠 P1-D · NoSQL regex injection / ReDoS via unescaped user input
- **Evidence:** `security_audit_agent` SEC-002 — `{"$regex": f"^{v}$"}` without `re.escape` in `employee_lifecycle.py:679,683,1214`; `employee_requests.py:529`; `pm_engine.py:184,202,471,595,701,1007`; `equipment.py:258,292`; `hr_portal.py:440,609`; `master_history.py:266`.
- **Impact:** authenticated staff can craft a regex-metacharacter value that hangs a query (catastrophic backtracking) or alters identity/duplicate-check semantics.
- **Fix:** wrap every user value with `re.escape` before regex insertion (sibling files already do this correctly).
- **Regression impact:** trivially LOW — the escape is transparent for normal alphanumeric input.

### 🟠 P1-E · CORS origin regex allows every shared platform subdomain with credentials
- **Evidence:** `backend/.env:5` `CORS_ORIGINS="*"` (correctly refused by middleware); `server.py:16297` falls back to `CORS_ORIGIN_REGEX` matching `*.emergentagent.com` / `*.emergent.host` / `*.preview.emergentagent.com` with `allow_credentials=True`.
- **Impact:** any app on shared platform domains is a trusted credentialed origin.
- **Fix:** pin `CORS_ORIGINS` to the exact production host(s); drop the preview regex in prod.

### 🟠 P1-F · `AUTO_EMAIL_REPORTS=true` in shipped `.env`
- **Evidence:** `backend/.env` sets both `AUTO_EMAIL_REPORTS=true` AND `EMAIL_SAFETY_MODE=strict`. The strict mode is the only reason no email has left the pod.
- **Impact:** if a deploy accidentally sets `EMAIL_SAFETY_MODE=live` without simultaneously reviewing recipient routing, every submitted DR immediately blasts emails.
- **Fix:** ship production with `AUTO_EMAIL_REPORTS=false` by default and require deliberate opt-in during production cutover. Ensure both flags are checked in a single deploy checklist item.

---

### 🟡 P2-A · Safety-doc upload lacks content-type & PDF magic-byte validation, filename not escaped in Content-Disposition
- **Evidence:** `security_audit_agent` SEC-005 — `routes/safety_portal/documents.py:71` stores client-supplied `content_type` verbatim; `:180` `filename="{fname}"` interpolated.
- **Fix:** allowlist content types, validate PDF magic bytes, quote filename per RFC 6266.

### 🟡 P2-B · Test/i18n files carry "Coming soon" translation entries that could accidentally render
- **Evidence:** `lib/i18n.js:3108, 3110, 3328, 3357` — English → Spanish entries for "Coming soon", "Video tutorial coming soon", "In development", "New Hire Onboarding".
- **Impact:** if any surface renders these translation keys they'll surface "Coming Soon" to users. Not directly proven to render; risk-only.
- **Fix:** audit which components consume these keys; either wire real functionality or remove the entries.

### 🟡 P2-C · Non-`/api` routes exist: `/health` and `/healthz`
- **Evidence:** route inventory shows two non-`/api` routes.
- **Impact:** LOW — both return 200 and are standard load-balancer probes. No data leak. Documented for completeness.

### 🟡 P2-D · 10 `console.log` / `alert(` calls in frontend `.jsx`/`.js`
- **Evidence:** `grep -rn "^\s*console\.log\|^\s*alert(" /app/frontend/src` returns 10 hits.
- **Impact:** LOW — dev noise in browser console, no functional bug.
- **Fix:** replace with proper logger or remove.

### 🟡 P2-E · Dev-mode React hydration warning inside `<option>` in CompetentPersonCombo (from prior testing agent report)
- **Evidence:** `/app/test_reports/iteration_track_23_10_e.json` — `<span> cannot be a child of <option>` at `CompetentPersonCombo.jsx:133`.
- **Impact:** dev-mode-only console warning; selection/submit works. No user-facing impact in production build.
- **Fix:** remove the build-time instrumentation wrapper span from `<option>` children.

### 🟡 P2-F · 863 `placeholder=` attributes — audit for stale copy
- **Evidence:** 863 `placeholder=` occurrences across the frontend. Not inherently a defect — these are legitimate input hints — but a small % may be stale or leak internal terminology. Not sampled exhaustively.

---

### ⚪ P3-A · Frontend `pm_auth.compute_pm_scope` fails OPEN
- **Evidence:** `security_audit_agent` hardening note — `pm_auth.py:321,338` returns `is_admin=True` if actor is non-dict or has no email. Safe today because all token paths carry email, but a future tokenless/emailless actor silently gets admin scope.
- **Fix:** fail-closed default.

### ⚪ P3-B · Version drift on the "V2" pattern
- **Evidence:** AdminHub V1 archived at `/admin/hub_v1` and reachable "for reference during Track 19.53 phased retirement". V2Index references "Updated by Track 13.6B". LeadershipHubV2 says "preview".
- **Impact:** operators can navigate to V1 archives and interact with stale UI. Legally risky if archived UI shows outdated data or lacks audit hooks.
- **Fix:** decide on V1 vs V2 as a hard cutover; remove V1 archive routes from production build.

### ⚪ P3-C · Health endpoint route inventory contains internal `_meta` routes
- **Evidence:** `/api/legacy-imports/_meta` and `/api/fleet/_meta` — auth-gated (401 unauth), but the naming suggests internal metadata surfaces.
- **Fix:** ensure they never render internal-only fields to portal tokens; sample verification.

### ⚪ P3-D · No consolidated cross-portal permission-matrix regression suite
- **Evidence:** no `tests/test_permission_matrix.py` (or similar) that iterates {portal_token × endpoint} and asserts allow/deny. Track-specific tests cover their own domains, but cross-cutting privilege-escalation drift is not caught.
- **Fix:** add a nightly matrix test.

---

## FINDINGS COUNT

| Severity | Count |
|---|---|
| 🔴 **P0** | **4** — auth-less HR roster · duplicate route serving CP data unauth · systemic internal-label leak (20+ pages) · dev break-glass + source-bundle download shipped |
| 🟠 **P1** | **6** — rate limiting off · multi-login no lockout · 30 duplicate routes · regex injection · CORS too broad · AUTO_EMAIL_REPORTS=true |
| 🟡 **P2** | **6** — upload validation · stale i18n · console.log noise · React dev warning · non-/api health · placeholder audit |
| ⚪ **P3** | **4** — pm_scope fails open · V1 archive routes · `_meta` naming · missing permission-matrix suite |

**TOTAL: 20 findings.**

---

## AUDIT COVERAGE & LIMITS

**Covered exhaustively:**
- Deployment env hygiene · CORS · secrets · supervisor · ports (via `deployment_agent`).
- Auth architecture · portal tokens · admin/PM scoping · impersonation · brute-force · secrets · regex sinks · uploads (via `security_audit_agent`).
- Full route inventory (1544 routes) with duplicate-registration detection.
- Unauthenticated probe matrix on 18 production endpoints.
- User-facing JSX scan for internal engineering labels across all `/app/frontend/src`.
- Backend live E2E on DR V3 excavation (from earlier this session).

**Covered partially (would need dedicated re-audit for full certification):**
- Every-role workflow exercise (audit sampled the auth matrix + DR V3 flow; did not click through every button in every portal).
- PDF rendering across every historical DR shape (spot-checked DR V3 excavation PDF only).
- Email templates & recipient routing (verified safety-mode strict; did not exhaust every template).
- AI workflows (verified DailySummaryAssist evidence bundle contract in code; did not probe for hallucination/prompt-leak with live prompts).
- Mobile viewports 390/430/768/1024/1366/1440 (not visually verified in this audit).
- Fleet / Shop / Dispatch / Field Leadership / QA/QC deep workflows.
- Offline draft / autosave paths (no offline harness available).
- Every-photo upload edge case.

---

## FINAL VERDICT

**Overall Recommendation: 🟠 GO WITH FIXES.**

**I would NOT personally deploy this platform to a live construction company tomorrow morning without fixing at least the four P0 items.** The engineering foundation is deploy-quality; the release polish is not. The exact copy defect the operator flagged on Track 23.10-E is systemic across 20+ pages, and two endpoints leak internal data anonymously.

### GO conditions (must land before deploy)
1. **§P0-A** — add auth dep to `/api/hr/employee-roster`.
2. **§P0-B** — remove the duplicate `/api/employees/competent-persons` handler; retain only the qualifications.py auth-gated one.
3. **§P0-C** — platform-wide sweep of user-facing "Track NN" / "Internal Use" / "Internal · Preview" strings. Generalize the DR V3 lock test into a repo-wide guard.
4. **§P0-D** — disable `/api/dev/*` in production (env flag) or hard-remove `/api/dev/source-bundle.*`. Do NOT ship `DEV_PASSWORD` in the production pod .env.
5. **§P1-A** and **§P1-B** — turn rate limiting ON in production; add brute-force lockout to multi-login. (These are quick and remove real Day-1 abuse exposure.)

### First-week fixes (deploy is safe with these documented and scheduled)
- All remaining P1 items (regex escape sweep, CORS pinning, AUTO_EMAIL_REPORTS default flip, duplicate-routes assert).
- P2-A upload hardening.

### Not blockers
- All P2/P3 items. Schedule for the next sprint.

**Auditor signature:** E1 · TRACK 24.0 · 2026-02-07

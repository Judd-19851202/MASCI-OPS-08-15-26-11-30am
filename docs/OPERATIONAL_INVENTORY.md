# MASCI Operations Platform — Operational Inventory & Governance Audit

**Document type:** Authoritative system map (Pass 1 — markdown audit)
**Generated:** 2026-05-18
**Scope:** Strict PREVIEW only. No production changes. Governance / discoverability / completeness only.
**Maturity goal:** Transition from reactive gap-filling → intentional operational architecture & governance.
**Next pass:** Live admin dashboard at `/admin/operational-inventory` that reads this same matrix from code (auto-drift detection).

---

## 0 · How to read this audit

Every system surface (portal, user type, route, workflow) is scored against a **10-field operational coverage matrix**:

| # | Field | Question it answers |
|---|-------|---------------------|
| 1 | **Who uses it** | Which roles/personas touch this surface |
| 2 | **Login required** | Public · gated · portal-token · password-only |
| 3 | **Guidance exists** | Is there ≥1 published article in `/guidance/...` covering it |
| 4 | **Onboarding exists** | Is the first-touch experience documented (sign-in → first task) |
| 5 | **Contextual help** | Is a `WhyItMattersPanel` / inline help embedded in the form/workflow |
| 6 | **WHY explanation** | Is there an explicit "why this matters" callout in the guidance |
| 7 | **Troubleshooting** | Is there ≥1 published `tshoot-*` article scoped to this surface |
| 8 | **Discoverability** | Can the right user *find* the surface without being told the URL |
| 9 | **Mobile UX** | Does the surface render & function on a phone (field reality) |
| 10 | **Translation readiness** | Is the surface available in Spanish via the existing `useT()` dictionary |

**Scoring legend:**
- ✅ Complete · 🟡 Partial · ❌ Missing · ⚪ N/A · ⏸️ Backlog (deferred by decision)

---

## 1 · Executive summary — top operational blind spots

Ranked by operational impact, highest first.

| Rank | Blind spot | Affected surfaces | Suggested governance action |
|------|-----------|-------------------|------------------------------|
| 🔴 P0 | **Field Leadership has no portal door** | `/leadership/*`, `/sign-in` selector | Add `/leadership/login` parallel to HR/Safety/Dispatch; expose in `SignIn.jsx` |
| 🔴 P0 | **Guidance content is English-only** | All 97 guidance articles + `WhyItMattersPanel` embeds | Wire `useT()` into Block renderer + add `body_es` to article schema; build governance metric for translation coverage |
| 🔴 P0 | **`/sign-in` doesn't list all portals** | Field Leadership · Shop · Dispatch · Safety · PM | Replace single email+password with a portal-aware sign-in directory (or surface the 7 sub-logins as tiles) |
| 🟠 P1 | **Public route map is implicit** | `/cheatsheet`, `/safety/cards`, `/jha`, `/trench-boxes` not in `public-tools-map` | Add 4 tiles to `public-tools-map` + dedicated short articles |
| 🟠 P1 | **No "where do I sign in?" article** | Public users land on `/guidance` with sign-in CTA but no help if they don't know their portal | Add `onboard-pick-your-portal` (public scope) |
| 🟠 P1 | **No Dispatch-portal training tile on `/guidance`** for dispatch users (scope leak risk) | `portal-dispatch` exists but isn't surfaced as a portal track if user only has `dispatch` scope (not admin) | Audit `PORTAL_TRACKS` matchPrefix — dispatch prefix is `dispatch-` but article ids may not start with that |
| 🟡 P2 | **No live drift detection** | Future article additions can land without translation, without coverage, without portal mapping | Build `/admin/operational-inventory` dashboard (Pass 2) |
| 🟡 P2 | **Mobile UX not formally audited per workflow** | All workflows assumed mobile-ready, never measured | Add `meta.mobile_audited: true/false` field per workflow + visual regression checkpoints |
| 🟡 P2 | **Onboarding paths aren't role-aware** | New hire sees same `role-new-employee` article whether they're a foreman or a laborer | Split into `role-new-employee-laborer`, `-operator`, `-foreman` |
| 🟡 P2 | **No translation governance metric** | Coverage dashboard tracks article counts but not translation pct | Add `translation_coverage_pct` to `/api/admin/guidance/coverage` |

---

## 2 · Translation architecture (existing, do not duplicate)

**Source of truth:** `/app/frontend/src/lib/i18n.js` (2,413 lines, English-canonical + Spanish dictionary `ES`)

**Mechanism:**
- `useT()` React hook → `{ t, lang, setLang }`
- Strings are wrapped `{t("English string")}` → looked up in `ES`; falls back to English if no entry
- Persists to `localStorage.masci.lang`
- Mirrors current language onto `<html lang="...">` for native browser spell-check
- `<LangToggle />` component (EN/ES segmented control) is already mounted in the Operational Guidance Center shell

**Translation coverage today (estimated):**

| Surface family | EN strings (approx) | ES dictionary coverage |
|---|---|---|
| Forms — Daily, Inspection, Meeting, JHA, Incident, Equipment Pre-Op | ~600 | ✅ ~95% (deep) |
| Shop Console, Parts Catalog, Sign-Off | ~150 | ✅ ~90% |
| Hub landing & navigation | ~80 | ✅ ~90% |
| Posters (Trench Box, JHA, Cheat Sheet) | ~120 | ✅ ~85% |
| HR / Safety / Dispatch / PM portal chrome | ~200 | 🟡 ~50% (portal chrome translated, dashboard data labels partial) |
| Admin Console | ~300 | ❌ <10% (intentionally English-only — operator surface) |
| **Guidance article bodies (97 articles)** | **~1,500** | ❌ **0% — not wired into `useT()`** |
| `WhyItMattersPanel` embeds | ~50 | ❌ 0% |
| Onboarding articles | ~200 | ❌ 0% |

**Translation gap for guidance specifically:**
1. Article bodies come from `/api/guidance/articles/<id>` as raw English strings.
2. Frontend `Block` renderer in `OperationalGuidanceCenter.jsx` outputs `{block.text}` directly with no `t()` wrap.
3. Even if wrapped, the `ES` dictionary has none of the guidance keys.

**Recommended translation architecture for guidance (Pass 2):**

```python
# /app/backend/guidance/content.py — extend schema
{
  "id": "public-preop-basics",
  "title": "Equipment Pre-Op Checks (Field Basics)",
  "title_es": "Inspección Pre-Operación (Campo)",
  "summary": "...",
  "summary_es": "...",
  "body": [...],
  "body_es": [...],   # parallel English-keyed structure; missing → fall back to English
  ...
}
```

```javascript
// /app/frontend/src/pages/guidance/OperationalGuidanceCenter.jsx — render-side
const { lang } = useT();
const title = (lang === "es" && article.title_es) || article.title;
const body  = (lang === "es" && article.body_es)  || article.body;
```

This **inherits** the existing language toggle, persists naturally, and lets translation land per-article incrementally. English remains the canonical record of truth.

---

## 3 · Field Leadership — worked example (full 10-field matrix)

This is the worst-current-offender. It's the template for every other portal.

### 3.1 Surface map

| Subsurface | Route | Auth gate | Component |
|---|---|---|---|
| Landing hub | `/leadership` | MASCIGC password (inline) | `FieldLeadershipHub.jsx` |
| Records list | `/leadership/records` | Inherited from landing | `FieldLeadershipRecords.jsx` |
| Record viewer | `/leadership/records/:id` | Inherited | `FieldLeadershipView.jsx` |
| New record form | `/leadership/:kind/new` | Inherited | `FieldLeadershipFormPage.jsx` |
| Cross-portal read (HR) | `/hr/field-leadership` | `X-HR-Token` | `HrFieldLeadership.jsx` |
| Cross-portal read (PM) | `/pm/field-leadership` | `X-Pm-Token` (or admin) | `PmFieldLeadership.jsx` |
| Admin master | `/admin/leadership-equipment` | Admin token | `AdminLeadershipEquipment.jsx` |

### 3.2 User-personas

| Persona | Native surface | Today's experience |
|---|---|---|
| Superintendent | `/leadership` after MASCIGC password | 🟡 Must know URL + password; no email login |
| Foreman | `/leadership` after MASCIGC password | 🟡 Same as above |
| HR (cross-portal read) | `/hr/field-leadership` | ✅ Works via HR portal |
| PM (cross-portal read) | `/pm/field-leadership` | ✅ Works via PM portal |
| Admin | `/admin/leadership-equipment` + `/leadership` | ✅ Works |
| Field crew (read-only) | — | ❌ No path — not even surfaced as "what's a leadership record" public article |

### 3.3 10-field coverage matrix — Field Leadership

| # | Field | Status | Evidence / detail |
|---|---|---|---|
| 1 | Who uses it | ✅ | Superintendents · Foremen · HR (read) · PM (read) · Admin (read+write) |
| 2 | Login required | 🟡 | Shared MASCIGC password — **not** a portal token. Not parallel to HR/Safety/Dispatch/PM/Shop pattern. |
| 3 | Guidance exists | ✅ | **31 articles** scoped `leadership` (`portal-leadership`, `role-superintendent`, `role-foreman`, 6 `field-*` workflow articles, 10+ cross-cutting `why-*` & `connect-*` articles) |
| 4 | Onboarding exists | ❌ | No `onboard-leadership-*` article. New superintendent has no "your first week" path. |
| 5 | Contextual help | ❌ | No `WhyItMattersPanel` embedded in `FieldLeadershipFormPage.jsx`. |
| 6 | WHY explanation | ✅ | `why-field-coaching`, `why-corrective-actions`, `safety-near-miss-importance` all leadership-scoped |
| 7 | Troubleshooting | 🟡 | `tshoot-employee-not-found` covers leadership scope, but no `tshoot-leadership-login` for the password gate |
| 8 | Discoverability | ❌ | **The biggest hole.** `/sign-in` doesn't list it. No `/leadership/login`. No public "find your portal" article. URL must be told by HR/admin verbally. |
| 9 | Mobile UX | 🟡 | Hub renders on mobile but the password gate is finger-friendly only on iOS; tablet usage works |
| 10 | Translation readiness | ❌ | Field Leadership chrome partially translated (`useT()` calls present). Articles 0%. Form labels mixed. |

### 3.4 Field Leadership — prioritized fixes (Pass 2)

| Rank | Fix | Files touched | Effort |
|---|---|---|---|
| 🔴 P0 | Create `/leadership/login` parallel to `/hr/login` (email + password, token-backed) | `frontend/src/pages/LeadershipLogin.jsx` (new), `backend/server.py` auth route, `App.js` route, `leadershipAuth.js` | M |
| 🔴 P0 | Add Field Leadership tile to `/sign-in` portal selector | `SignIn.jsx`, design at parity with other portal tiles | S |
| 🟠 P1 | Add `onboard-leadership-first-week` article (public scope so they can read pre-login) | `backend/guidance/content.py` | S |
| 🟠 P1 | Add `tshoot-leadership-login` article | `backend/guidance/content.py` | S |
| 🟠 P1 | Embed `WhyItMattersPanel` in `FieldLeadershipFormPage.jsx` (write-ups, coaching docs) | 1 file | S |
| 🟡 P2 | Translate all 31 leadership-scoped guidance articles | Schema migration + content | L |

**Template applied:** every other portal in §4 is audited with this same template.

---

## 4 · All Portals — 10-field matrix

| Portal | Login route | Token / gate | Surfaced in `/sign-in`? | Guidance articles | 1·Who | 2·Login | 3·Guide | 4·Onbd | 5·Ctxt | 6·WHY | 7·Tshoot | 8·Disco | 9·Mobile | 10·Trans |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Public / Field crew** | (n/a) | none | ✅ implicit | 17 public | ✅ | ⚪ | ✅ | ✅ | 🟡 | ✅ | 🟡 | ✅ | ✅ | ❌ |
| **HR** | `/hr/login` | `X-HR-Token` | ✅ | 16 hr | ✅ | ✅ | ✅ | 🟡 | 🟡 | ✅ | ✅ | ✅ | ✅ | 🟡 |
| **Safety** | `/safety-portal/login` | `X-Safety-Token` | 🟡 (via `/sign-in`) | 17 safety | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 |
| **Shop / Fleet** | `/shop/login` | `X-Shop-Token` | 🟡 (separate URL) | 18 shop | ✅ | ✅ | ✅ | 🟡 | 🟡 | ✅ | 🟡 | 🟡 | ✅ | ✅ |
| **Dispatch** | `/dispatch-portal/login` | `X-Dispatch-Token` | 🟡 (separate URL) | 12 dispatch | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | 🟡 | ✅ | ❌ |
| **PM** | `/pm/login` | `X-Pm-Token` (or admin) | 🟡 (separate URL) | 15 pm | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 |
| **Field Leadership** | `/leadership` (inline gate) | MASCIGC password | ❌ | 31 leadership | ✅ | 🟡 | ✅ | ❌ | ❌ | ✅ | 🟡 | ❌ | 🟡 | ❌ |
| **Admin Console** | `/admin/login` | Admin token | ✅ | 80 admin | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | ⚪ (intentional EN) |
| **Developer (ForgedOps)** | `/dev/login` | `X-Dev-Token` | ❌ (hidden) | 0 | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | 🟡 | ⚪ |

### 4.1 Top portal-level gaps

| Gap | Portals affected | Action |
|---|---|---|
| Onboarding (field #4) | Leadership · Dispatch · PM · Shop | Add `onboard-<portal>-first-week` per portal (5 short articles) |
| Contextual help (field #5) | Leadership · Dispatch · Shop | Embed `WhyItMattersPanel` in 3-4 forms per portal |
| Troubleshooting (field #7) | Safety · Dispatch · Leadership · Shop · PM | Add `tshoot-<portal>-cant-login` + `tshoot-<portal>-no-data` |
| Discoverability (field #8) | Leadership · Dispatch · Shop | Surface in unified `/sign-in` directory + add public "find your portal" article |
| Translation (field #10) | All guidance content | Wire `useT()` into Block renderer + add `body_es` per article (schema migration) |

---

## 5 · All User Types — coverage matrix

| User type | Native entry | Auth | Guidance entry | Onboarding article | Cross-portal reads | Status |
|---|---|---|---|---|---|---|
| **Anonymous / Public** | `/` Hub | none | `/guidance` (15 public tiles) | `onboard-login`, `onboard-mobile`, `public-tools-map` | — | ✅ |
| **Field crew (laborer, operator)** | `/submit`, `/daily/submit`, etc. via QR | none (public submit) | `/guidance` public track | `role-new-employee` (single article — too generic) | — | 🟡 |
| **Mechanic / Shop** | `/shop/login` | `X-Shop-Token` | `/guidance` portal-shop | ❌ no `onboard-shop-first-day` | — | 🟡 |
| **Foreman** | `/leadership` (MASCIGC pw) | shared password | `/guidance` leadership track | ❌ no `onboard-foreman-first-week` | reads daily reports | 🟡 |
| **Superintendent** | `/leadership` (MASCIGC pw) | shared password | `/guidance` leadership track | ❌ no onboarding article | reads daily/PM | 🟡 |
| **PM** | `/pm/login` | `X-Pm-Token` | `/guidance` portal-pm | ❌ no `onboard-pm-first-week` | reads field/safety/leadership | 🟡 |
| **HR** | `/hr/login` | `X-HR-Token` | `/guidance` portal-hr | 🟡 partial via `hr-onboarding-new-hire` (that's about HIRING, not HR-USER onboarding) | reads field-leadership/safety | 🟡 |
| **Safety Manager / Coordinator / Officer** | `/safety-portal/login` | `X-Safety-Token` | `/guidance` portal-safety | ❌ no `onboard-safety-first-week` | reads incidents/leadership/all | 🟡 |
| **Dispatch** | `/dispatch-portal/login` | `X-Dispatch-Token` | `/guidance` portal-dispatch | ❌ no onboarding article | reads equipment/shop | 🟡 |
| **Admin (Operator)** | `/admin/login` | Admin token | `/guidance` portal-admin | partial via `admin-user-management` | full cross-portal | 🟡 |
| **Owner (Justin)** | Admin token | Admin | (no owner-specific tile) | ❌ no `role-owner` article | full | 🟡 |
| **Developer (ForgedOps)** | `/dev/login` | `X-Dev-Token` | none | — | dev console only | ⚪ |

### 5.1 User-type gaps

| Gap | Impact | Action |
|---|---|---|
| `role-new-employee` is too generic | Laborer vs operator vs foreman get same article | Split into 3 articles + add a router question "what's your role?" at top of `role-new-employee` |
| No per-portal first-week onboarding | All 7 logged-in personas | Create 7 `onboard-<persona>-first-week` articles |
| No "Owner" persona | Owner-level KPIs and reads not documented | Add `role-owner` article + dashboard guidance |

---

## 6 · All Routes — categorized inventory

Direct extract from `frontend/src/App.js` (canonical route table). Total routes: **~150**.

### 6.1 PUBLIC (anonymous-safe) — 24 routes

| Route | Purpose | Used by | Mobile | Trans | Guidance |
|---|---|---|---|---|---|
| `/` | Hub landing | Anyone | ✅ | ✅ | ⚪ |
| `/safety` | Safety section nav | Anyone | ✅ | ✅ | ⚪ |
| `/safety/forms` | Safety forms hub | Anyone | ✅ | ✅ | ⚪ |
| `/safety/forms/login` | Safety forms gate | Anyone | ✅ | 🟡 | ❌ |
| `/safety/cards` | Field Safety Cards reference | Crew | ✅ | 🟡 | ❌ |
| `/field` | Field section nav | Anyone | ✅ | ✅ | ⚪ |
| `/field/calculators` | Material calculator | Crew | ✅ | ✅ | ✅ (`public-material-calculator`) |
| `/qaqc` | QA/QC section | Anyone | ✅ | ✅ | ✅ (`public-qaqc-basics`) |
| `/qaqc/:slug/new` | New QA/QC inspection | Crew/Foreman | ✅ | ✅ | 🟡 |
| `/inspect/new`, `/submit`, `/inspections/submit` | Site inspection | Crew | ✅ | ✅ | 🟡 (general, no dedicated article) |
| `/meetings/submit` | Safety meeting | Crew | ✅ | ✅ | ✅ (`public-toolbox-talks`) |
| `/incidents/submit` | Incident report | Anyone | ✅ | ✅ | ✅ (`public-incident-basics`) |
| `/daily/submit` | Daily report | Crew | ✅ | ✅ | ✅ (`public-daily-report-basics`) |
| `/equipment/submit` | Equipment Pre-Op | Operator | ✅ | ✅ | ✅ (`public-preop-basics`) |
| `/jha` | JHA plans hub (read) | Foreman | ✅ | ✅ | ❌ (no `public-jha-basics`) |
| `/trench-boxes` | Trench box ref | Operator | ✅ | ✅ | ❌ (no `public-trench-basics`) |
| `/thank-you` | Submit confirmation | Any submitter | ✅ | ✅ | ⚪ |
| `/cheatsheet` | Crew cheat sheet poster | Foreman | ✅ | ✅ | ❌ (no `public-cheatsheet-basics`) |
| `/guidance`, `/guidance/section/:s`, `/guidance/:a` | Operational Guidance Center | Anyone | ✅ | ❌ (article bodies EN-only) | ✅ (self) |
| `/sign-in` | Unified sign-in | Logged-out users | ✅ | 🟡 | ❌ (no `onboard-pick-your-portal`) |
| `/time-off/public/:token` | HR time-off public confirm | Tokened employee | ✅ | 🟡 | ❌ |
| `/training`, `/training/:track`, `/training/:track/poster|packet` | Training tracks | Mixed | ✅ | 🟡 | 🟡 (partially merged into Guidance Center) |
| `/legal/terms`, `/legal/privacy` | Legal | Anyone | ✅ | 🟡 | ⚪ |

### 6.2 GATED (auth required) — by portal token

| Token | Routes (count) | Notes |
|---|---|---|
| Admin token | 50+ (`/admin/*`) | Strict |
| PM token (or admin) | 14 (`/pm/*`) | Mirrors admin minus backup/recovery |
| HR token | 9 (`/hr/*`) | Read-only HR scope |
| Safety token | 11 (`/safety-portal/*`) | Independent JWT, no admin override |
| Shop token | 5 (`/shop/*`) | Mechanic-only |
| Dispatch token | 5 (`/dispatch-portal/*`) | Movement command |
| MASCIGC password | 4 (`/leadership/*`) | **Anomaly — not a token** |
| Dev token | 2 (`/dev/*`) | Vendor-internal |

### 6.3 QR-access routes (printed posters in the field)

| Poster | Live URL | Article | Status |
|---|---|---|---|
| Crew cheat sheet | `/cheatsheet` | ❌ no dedicated article | 🟡 |
| Trench box poster | `/admin/trench-boxes/poster` (admin print) → field reads `/trench-boxes` | ❌ no public article | 🟡 |
| JHA poster | `/admin/jha-plans/poster` (admin print) → field reads `/jha` | ❌ no public article | 🟡 |
| Training packets | `/training/:track/packet` | 🟡 partial | 🟡 |
| All posters print | `/admin/posters/print-all` | ⚪ admin only | ⚪ |

### 6.4 Mobile-only / mobile-first flows

| Flow | Route | Notes |
|---|---|---|
| QR scan onboarding | `/cheatsheet`, `/submit`, `/daily/submit`, `/equipment/submit`, `/meetings/submit`, `/incidents/submit` | All public, all mobile-friendly |
| Photo capture | inside Daily, Inspection, Incident, Equipment, QA/QC | ✅ camera capture wired |
| GPS location capture | Daily, Inspection, Incident | ✅ |
| Signature pad | Daily, Inspection, Meeting, JHA, Incident, Equipment, QA/QC | ✅ |

### 6.5 Utility / tools routes

| Route | Tool | Audited |
|---|---|---|
| `/field/calculators` | Material calculator | ✅ |
| `/cheatsheet` | Printable reference | ✅ |
| `/admin/posters/print-all` | Poster print queue | ⚪ admin |
| `/admin/analytics` | Usage analytics | ⚪ admin |
| `/admin/system-health` | System health | ⚪ admin |
| `/admin/audit-log` | Audit forensics | ⚪ admin |
| `/admin/sessions` | Active sessions | ⚪ admin |
| `/admin/guidance-coverage` | Guidance gap dashboard | ⚪ admin |

---

## 7 · All Workflows — coverage matrix

Workflow = end-to-end operational process (not just a single form).

| Workflow | Entry points | Personas | Guidance | Onboarding | Ctxt help | WHY | Troubleshoot | Trans |
|---|---|---|---|---|---|---|---|---|
| **Daily Report** | `/daily/submit` (public), `/daily/new` (logged-in), `/admin/daily` (review) | Crew lead · Foreman · PM | ✅ 3 articles | ✅ public-daily-report-basics | ✅ WhyPanel | ✅ why-daily-reports | 🟡 | ✅ form / ❌ guidance |
| **Site Inspection** | `/submit`, `/inspect/new`, `/admin/inspections` | Foreman · Safety | 🟡 no dedicated public article | ❌ | 🟡 | ✅ | 🟡 | ✅ form / ❌ guidance |
| **Safety Meeting / Toolbox Talk** | `/meetings/submit`, `/admin/meetings` | Foreman · Safety | ✅ public-toolbox-talks | ✅ | ✅ WhyPanel | ✅ | 🟡 | ✅ form / ❌ guidance |
| **JHA / Job Hazard Plan** | `/jha` (read), `/admin/jha-plans` (author) | Foreman · Safety · PM | 🟡 no public article | ❌ | 🟡 | ✅ | ❌ | ✅ form / ❌ guidance |
| **Incident / Near-miss** | `/incidents/submit`, `/admin/incidents`, `/safety-portal/incidents` | Anyone · Safety · Admin | ✅ public-incident-basics, safety-near-miss | ✅ | ✅ WhyPanel | ✅ why-incidents | 🟡 | ✅ form / ❌ guidance |
| **Equipment Pre-Op** | `/equipment/submit`, `/admin/equipment-inspections`, `/shop` | Operator · Shop · Admin | ✅ public-preop-basics, shop-preop-deep | ✅ | ✅ WhyPanel | ✅ | 🟡 | ✅ form / ❌ guidance |
| **QA / QC Inspection** | `/qaqc/:slug/new`, `/admin/qaqc`, `/pm/qaqc` | Foreman · QA · PM | ✅ public-qaqc-basics | 🟡 | 🟡 | ✅ | ❌ | ✅ form / ❌ guidance |
| **Material Calculator** | `/field/calculators` | Foreman · Estimator | ✅ public-material-calculator | ⚪ | ⚪ | ✅ | ⚪ | ✅ form / ❌ guidance |
| **Field Leadership writeup** | `/leadership/:kind/new` | Foreman · Super | ✅ field-writeup-authoring | ❌ | ❌ no WhyPanel | ✅ | 🟡 | 🟡 form / ❌ guidance |
| **Field Leadership coaching doc** | `/leadership/:kind/new` | Super · PM | ✅ field-coaching-documentation | ❌ | ❌ | ✅ | 🟡 | 🟡 form / ❌ guidance |
| **Safety corrective actions** | `/safety-portal/corrective-actions` | Safety | ✅ safety-corrective-actions-workflow | ❌ | ❌ | ✅ | 🟡 | ❌ |
| **Safety audits** | `/safety-portal/audits` | Safety | ✅ safety-audits-workflow | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Fire-extinguisher inventory** | `/safety-portal/fire-extinguishers` | Safety | ✅ safety-fire-extinguishers | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Safety training compliance** | `/safety-portal/training` | Safety · HR | ✅ safety-training-compliance | ❌ | ❌ | ✅ | ❌ | ❌ |
| **HR new-hire onboarding** | `/admin/people` → trigger | HR · Admin | ✅ hr-onboarding-new-hire | ❌ | 🟡 | ✅ | ❌ | ❌ |
| **HR time verification** | `/hr/time-verification` | HR | ✅ hr-time-verification-deep | ❌ | ❌ | ✅ | ❌ | 🟡 |
| **HR writeups / correctives** | `/hr/employee-accountability` | HR | ✅ hr-writeups-correctives | ❌ | ❌ | ✅ | ❌ | ❌ |
| **HR offboarding / termination** | `/admin/terminations` | HR · Admin | ✅ hr-offboarding | ❌ | ❌ | ✅ | ❌ | ❌ |
| **HR payroll variance** | `/hr/payroll-variance` | HR | ✅ (in hr-time-verification-deep) | ❌ | ❌ | ✅ why-time-verification | ❌ | ❌ |
| **HR time-off requests** | `/hr/time-off`, `/time-off/public/:token` | HR · Employee | ❌ no article | ❌ | ❌ | ❌ | ❌ | 🟡 form |
| **HR training records** | `/hr/training-records` | HR | 🟡 partial | ❌ | ❌ | 🟡 | ❌ | ❌ |
| **Shop Pre-Op review** | `/shop` open items | Shop | ✅ shop-preop-deep, shop-failed-preop-workflow | ❌ | ❌ | ✅ | ❌ | ✅ form / ❌ guidance |
| **Shop damage reporting** | `/shop/equipment/:id` | Shop | ✅ shop-damage-reporting | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Shop maintenance coordination** | `/shop` | Shop · Dispatch | ✅ shop-maintenance-coordination | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Shop equipment return** | `/safety/forms/equipment-issuance/:id/return` | Shop · Safety | ✅ shop-equipment-return | ❌ | ❌ | ✅ | ❌ | 🟡 |
| **Shop parts catalog / order** | `/shop` Parts Catalog | Shop | ❌ no article | ❌ | ❌ | ❌ | ❌ | ✅ form |
| **Dispatch equipment movement** | `/dispatch-portal` | Dispatch · Shop | ✅ dispatch-equipment-movement | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Dispatch availability** | `/dispatch-portal` | Dispatch | ✅ dispatch-availability-management | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Dispatch holds / transfers** | `/dispatch-portal` | Dispatch · PM | ✅ dispatch-holds-transfers | ❌ | ❌ | ✅ | ❌ | ❌ |
| **PM project review cadence** | `/pm` | PM | ✅ pm-project-review-cadence | ❌ | ❌ | ✅ | ❌ | ❌ |
| **PM labor documentation** | `/pm/daily`, `/pm/people` | PM · HR | ✅ pm-labor-documentation | ❌ | 🟡 | ✅ | ❌ | ❌ |
| **PM P&L review** | `/admin/pnl` | PM-via-admin · Owner | 🟡 admin-namespaced article | ❌ | ❌ | 🟡 | ❌ | ❌ |
| **PM coordination** | `/pm`, `/pm/photos` | PM · Field | ✅ pm-coordination | ❌ | ❌ | ✅ | ❌ | ❌ |
| **PM compliance export** | `/pm/compliance-export` | PM · Admin | 🟡 partial | ❌ | ❌ | 🟡 | ❌ | ❌ |
| **Asset transfers** | `/asset-transfers` | PM · Admin | ❌ no article | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Document expirations** | `/document-expirations` | HR · Admin | ❌ no article | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Tasks / Actions** | `/tasks` | Any logged-in | ❌ no article | ❌ | ❌ | ❌ | ❌ | ❌ |
| **PO requests** | `/po-requests` | PM · Admin | ❌ no article | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Project health** | `/project-health` | PM · Admin · Safety | ❌ no article | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Admin user management** | `/admin/people` | Admin | ✅ admin-user-management | 🟡 | ✅ | ✅ | ❌ | ⚪ EN |
| **Admin audit forensics** | `/admin/audit-log` | Admin | ✅ admin-audit-forensics | ❌ | ❌ | ✅ | ✅ | ⚪ EN |
| **Admin system health** | `/admin/system-health` | Admin | ✅ admin-system-health | ❌ | ❌ | ✅ | ❌ | ⚪ EN |
| **Admin backup / restore** | `/admin/system` Backup panel | Admin | ✅ admin-backup-restore | ❌ | ❌ | ✅ | ❌ | ⚪ EN |
| **Admin data portability** | `/admin/compliance` export | Admin | ✅ admin-data-portability | ❌ | ❌ | ✅ | ❌ | ⚪ EN |
| **Admin Sentry observability** | (external) | Admin | ✅ admin-sentry-observability | ❌ | ❌ | ✅ | ❌ | ⚪ EN |
| **Admin role templates** | `/admin/people` role | Admin | ✅ admin-role-templates | ❌ | ❌ | ✅ | ❌ | ⚪ EN |
| **Admin governance** | `/admin/guidance-coverage` | Admin | ✅ admin-governance-why | ❌ | ❌ | ✅ | ❌ | ⚪ EN |
| **Deploy recovery** | `/admin/deploy-recovery` | Admin | 🟡 partial | ❌ | ❌ | 🟡 | ❌ | ⚪ EN |

### 7.1 Workflow gaps (no guidance at all)

| Workflow | Personas | Priority |
|---|---|---|
| Tasks / Actions | All logged-in | 🟠 P1 — high-touch surface |
| Document Expirations | HR / Admin | 🟠 P1 — compliance |
| PO Requests | PM / Admin | 🟠 P1 |
| Project Health | PM / Admin / Safety | 🟠 P1 |
| Asset Transfers | PM / Admin | 🟠 P1 |
| HR Time-Off Requests | HR / Employee | 🟡 P2 |
| Shop Parts Catalog / Order | Shop | 🟡 P2 |
| Public JHA reference | Foreman | 🟡 P2 |
| Public Trench Box reference | Operator | 🟡 P2 |
| Public Cheat Sheet | Foreman | 🟡 P2 |

---

## 8 · Translation readiness — system-wide

### 8.1 Coverage breakdown

| Surface | Today | Target | Effort |
|---|---|---|---|
| Form chrome (daily, inspection, meeting, JHA, incident, equipment, QA/QC) | ✅ 90-95% | ✅ 95%+ | S — dictionary additions |
| Hub landing & navigation | ✅ 90% | ✅ 95%+ | S |
| Shop console | ✅ 90% | ✅ 95%+ | S |
| Posters (printable QR) | ✅ 85% | ✅ 95%+ | S |
| HR / Safety / Dispatch / PM portal chrome | 🟡 50% | ✅ 90% | M — dashboard label coverage |
| Field Leadership chrome | 🟡 40% | ✅ 90% | M |
| **Guidance article titles / summaries** | ❌ 0% | ✅ 80%+ | M — schema `title_es`, `summary_es` |
| **Guidance article bodies (`steps`, `bullets`, `why`, `warn`, `tip`, `mistakes`, `next`)** | ❌ 0% | ✅ 80%+ | L — schema `body_es` + per-article translation |
| **`WhyItMattersPanel` props** | ❌ 0% | ✅ 80%+ | S — wire `useT()` into component |
| Onboarding articles | ❌ 0% | ✅ 90%+ | M — these are high-leverage for new hires |
| Admin console | ⚪ EN-only by design | ⚪ no change | ⚪ |

### 8.2 Recommended translation governance metric

Add to `/api/admin/guidance/coverage` response:

```json
{
  "translation_coverage": {
    "total_articles": 97,
    "title_es_present": 0,
    "body_es_present": 0,
    "pct_title": 0.0,
    "pct_body": 0.0,
    "by_section": { "roles": 0.0, "portals": 0.0, ... },
    "by_scope":   { "public": 0.0, "hr": 0.0, "safety": 0.0, ... }
  }
}
```

Render in `/admin/guidance-coverage` as a top-line "Spanish coverage" panel — same pattern as the existing missing-articles panel.

### 8.3 Translation policy proposal

1. **English is canonical.** All article IDs, slugs, search indices stay English.
2. **Missing `*_es` → graceful fallback to English.** No 404, no warning to user. The page renders in English where translation is missing.
3. **Operational priority for translation:** Public → Field crew → Field Leadership → Safety → Shop → HR/Dispatch/PM (admin remains EN by intent).
4. **No machine translation in production output.** Use a translation service to draft, but a bilingual reviewer must approve each article before the `_es` field lands.
5. **Future articles inherit translation capability by default** — the schema requires `title_es` (can be empty string but field must exist), checked by a pytest assertion at content-load time.

---

## 9 · Pass 2 — Live governance dashboard (next step)

Once you approve this audit, the next deliverable is `/admin/operational-inventory`:

- Reads `App.js` routes (programmatic AST walk)
- Reads `guidance/content.py` SECTIONS + _ARTICLES
- Reads RBAC config (portal scope mapping)
- Joins them and renders the same matrix as this doc
- Highlights drift (new route without guidance · new article without translation · new portal without `/sign-in` entry)
- Replaces the existing `AdminGuidanceCoverage` page (which becomes one tab inside this)
- Read-only — strictly admin scope

Endpoint plan:
- `GET /api/admin/operational-inventory` — returns the full matrix
- `GET /api/admin/operational-inventory/translation` — returns translation readiness only
- `GET /api/admin/operational-inventory/drift` — returns delta vs the last frozen snapshot

---

## 10 · Pass 1 → Pass 2 → Pass 3 (governance roadmap)

| Pass | Deliverable | Status |
|------|-------------|--------|
| **1 — Markdown audit (this doc)** | Authoritative operational inventory + Field Leadership worked example + 10-field matrix for all portals, user types, routes, workflows + translation readiness | ✅ **THIS DOCUMENT** |
| **2 — Live governance dashboard** | `/admin/operational-inventory` programmatic mirror of this doc with drift detection | ⏸️ Awaiting approval |
| **3 — Schema + content translation** | `body_es` schema field, `useT()` wiring in Block renderer, translation coverage in coverage API | ⏸️ Awaiting approval |
| **4 — Field Leadership portal door** | `/leadership/login`, token, `/sign-in` tile, public onboarding article | ⏸️ Awaiting approval |
| **5 — Onboarding-per-persona** | 7 `onboard-<persona>-first-week` articles + public-scope where appropriate | ⏸️ Awaiting approval |
| **6 — Cross-cutting workflow coverage** | Articles for Tasks · Document Expirations · PO Requests · Project Health · Asset Transfers · HR Time-Off · Shop Parts | ⏸️ Awaiting approval |
| **7 — QR poster rollout** | (Was the originally requested next item — now correctly sequenced AFTER inventory is operationalized) | ⏸️ Awaiting approval |

---

## 11 · Governance philosophy (anchor)

> **"Have we systematically mapped and operationalized the entire ecosystem?"** is the question this document is built to answer at any point in time. As the platform grows, **this document must be re-derived (Pass 2 live dashboard) rather than re-written by hand.** Hand-curated docs go stale; code-derived dashboards do not.

> Every future feature lands with: (a) a route, (b) a guidance article, (c) onboarding scope, (d) WHY embed, (e) troubleshooting article, (f) discoverability surface, (g) mobile audit, (h) `*_es` translation field. The schema enforces it. The dashboard surfaces drift.

> **No portal exists in production without a `/<portal>/login` URL parallel to every other portal.** Field Leadership is the open exception, scheduled to be closed in Pass 4.

> **No guidance article exists in production without a translation-readiness flag in its schema.** Translation can be deferred; the schema cannot.

---

*End of audit. Next: await user approval for Pass 2 (live dashboard) sequencing.*

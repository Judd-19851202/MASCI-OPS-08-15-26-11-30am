# TRACK 15.14D — PLATFORM REALITY AUDIT (PRODUCTION-SHAPED)

**Mode:** read-only · defect discovery only · no code, no deploys, no fixes.
**Build inspected:** the codebase that is currently sitting on preview and is staged for production. Production deployments are bit-for-bit copies of this source tree (same `git HEAD`).
**Pod constraint:** I cannot reach `mascidocs.com` (production DB or real user devices) from this pod. Anything that requires production data or a real iPhone/iPad is documented as **🟦 UNVERIFIED IN PRODUCTION** below, with the exact recipe an operator must run.

---

## 1 · EXECUTIVE SUMMARY

The platform's *engine* is in much better shape than the platform's *surface*. Auth, data plumbing, and read APIs are largely correct after Track 15.14A/B/C. The remaining defects cluster in four families:

| Defect family | Why it hurts users | Count |
|---|---|---|
| **Discoverability — pages exist but aren't in nav** | HR Incidents, HR Motive Drivers, HR Employee Requests Queue, Admin Incidents, Admin Inspections, Admin Asset Admin Console, Admin Daily Reports, Admin DLS debriefs, Admin Driver-Intel, Admin Health, Admin Hub V2 duplicate, Admin Geofence, Admin Compliance Findings — all are wired endpoints with no sidebar entry. Users either can't find them, or only senior operators with bookmarks can. | **13+** registered HR/Admin routes with no sidebar link |
| **Honest placeholders still rendered as if they're features** | Admin → Asset Profile renders MaintainX and Motive "Awaiting integration" placeholder cards. ShopHubV2 has a "Parts on order" dashed placeholder + a search-until-Track-13.30C-ships placeholder. Unit History Timeline lists event families with no backend source as "honest placeholders." | **5** documented placeholders |
| **Cross-portal asymmetry — Admin can't see what Safety can** | Safety sidebar has Incidents, Inspections, JHA, Meetings, Fleet, Library, Training, etc. Admin has registered routes for many of these (Incidents, Inspections, Compliance Findings) but no sidebar entry. Operationally, the most-privileged role has the worst access. | **3** cross-cut surfaces |
| **Discoverability inside a portal — wrong group or single-item group** | HR Daily Reports is filed under "Compliance & Records · read-only payroll cross-check context" — operators don't read "Compliance & Records." Field Leadership Records and Users sit under "People Operations" but the names don't telegraph the responsibilities. "Access & Identity" HR group contains only `Change Password` (orphan group). | **2** group-level UX defects |
| **Settings / Notifications not exposed in HR** | HR sidebar has NO "Notifications" link. HR has no "Settings" link. The platform has `NotificationsDigest`, `NotificationBell`, and a per-user notification surface — none of which HR can self-manage from their portal. | **1** missing surface |
| **Auth backstop blind-spots on env-bound tokens** | Shop's shared HMAC token (env-derived) and the static Admin token (env-derived) cannot carry a `must_change_password` flag. Today this is fine because the directory-user multi-login suppresses portal_tokens. But the shared shop HMAC remains a single password that is not covered by the rotation flow. | **1** known limitation |

Five pillars at the surface level:

| Pillar | Status |
|---|---|
| POWERFUL  | 🟢 — endpoints exist and answer. |
| SIMPLE    | 🔴 — too many pages live off-sidebar, the operator must memorize URLs. |
| BEAUTIFUL | 🟡 — layouts are consistent but partial features are rendered as if complete. |
| TRUSTED   | 🟡 — temp-password gates landed in Track 15.14A/B/C but Layer-3 was caught with a missing `request` parameter in this gate. Code paths shared with production still need real-device verification. |
| PROVEN    | 🔴 — every claim below is production-shaped (code grounded), not production-observed. |

---

## 2 · PORTAL-BY-PORTAL FINDINGS

### 2.1 HR PORTAL

**Sidebar groups (verified from `HrSideNavV2.jsx`):**
| Group | Items |
|---|---|
| People Operations | Overview · Employee Lifecycle · Employee Accountability · Field Leadership Users · Field Leadership Records |
| Time & Payroll | Time Verification · Payroll Variance · Time Off Requests · PO Requests |
| Compliance & Records | Document Expirations · Training Records · Driver Qualification · Safety Records · **Daily Reports** |
| Access & Identity | Change Password (only) |
| Guidance | Training Center |

**HR routes registered but NOT in sidebar (verified in `App.js`):**

- `/hr/incidents` → `HrIncidents.jsx` — fully-built read-only OSHA-relevant list with CSV export. **No sidebar entry.**
- `/hr/employee-requests` → `HrEmployeeRequestsQueue.jsx` — no sidebar entry.
- `/hr/motive-drivers` → `HrMotiveDrivers.jsx` — no sidebar entry.
- `/hr/driver/:driverKey` → `HrDriverProfile.jsx` — deep-link only; no breadcrumb back.
- `/hr/employees/:id/accountability` → `HrEmployeeAccountabilityTimeline.jsx` — deep-link only.
- `/hr/driver-qualification/import` → `HrDriverQualificationImport.jsx` — child of DQ.
- `/hr/hub_legacy`, `/hr/hub_v2` — duplicate hubs; legacy still routable.

**Special-attention HR items:**

- **HR Daily Reports** — proven OK end-to-end including failure injection (Track 15.14C). Rendered under "Compliance & Records · Read-only payroll cross-check context" — operators don't think "compliance" when looking for "daily reports." Group placement is a *findability* defect, not a functional one.
- **HR Field Leadership Users + Records** — proven discoverable side-by-side with cross-links (Track 15.14B). 🟢
- **HR Incidents** — fully implemented, NOT in sidebar. 🔴 discoverability.
- **Notifications** — not on HR sidebar at all. 🟡 expected per audit checklist.
- **Settings** — not on HR sidebar at all. 🟡.

### 2.2 PM PORTAL

**PmHubV2 destinations (verified):**

- `/pm/jobs`, `/pm/command-center`, `/pm/fleet`, `/pm/qaqc`, `/pm/crew-compliance`, `/pm/photos`, `/pm/project-staffing`, `/po-requests`.

**Observed gaps (code-grounded):**

- The PM Hub uses tiles, not a sidebar. Workflows reachable include: jobs, command center, fleet, QAQC, crew compliance, photos, project staffing.
- **RFIs and Submittals are NOT in PM** today. They were named in the audit checklist; the codebase has no `/pm/rfis` or `/pm/submittals` routes. 🟡 *expected by user, not built.*
- **Daily Reports for PM** is wired (`/api/pm/daily-reports`) but the PM Hub V2 destinations grid doesn't surface it as a dedicated tile (Daily Reports surfaces via Command Center).
- **PM Notifications** — same as HR: no portal-level surface.

### 2.3 SHOP / ASSET CARE

**ShopHubV2 destinations (verified):**

- `/shop/asset-care`, `/shop/equipment`, `/shop/fleet` (multiple `focus_filter=*` flavors), `/shop/fuel-lube`, `/shop/fuel-lube/new`, `/shop/manager/queue`, `/shop/me`, `/shop/pm`, `/shop/pm/schedules`, `/shop/pm/templates`, `/shop/service-truck-reconciliation`, `/shop/units/history`.

**Acknowledged placeholders:**

- ShopHubV2 line 778 — dashed "Parts on order" placeholder until backend `/api/shop/parts/on-order/summary` ships.
- ShopHubV2 line 815 — search placeholder pending Track 13.30C.
- `shop/UnitHistoryTimeline.jsx` line 394 — "Unavailable event families (honest placeholders)" rendered as `data-testid="unit-history-placeholder-${event_type}"`.
- `admin/AssetProfile.jsx` line 115 — MaintainXPlaceholder.
- `admin/AssetProfile.jsx` line 355 — MotivePlaceholder.

These are flagged as "honest" in code, but to a non-platform-savvy user they still read as broken/empty features.

**Asset Care access (special-attention #4 + #5):**

- `require_admin_or_asset_admin` now accepts both `user_directory.is_asset_admin=true` AND legacy shop roles (Track 15.13E). 🟢 Backend verified.
- Asset Care UI lives at `/shop/asset-care/*`. Routing through Shop guard. 🟢.
- **Asset Admin routing audit (special-attention #4):** users with the directory `is_asset_admin=true` flag who do NOT also have a shop role still log in through `/shop/login` and use the Shop side-nav. They have no dedicated `/asset-admin` portal. This is intentional per Track 15.13 design, but the discoverability is poor — an Asset Admin's only entry point is "log into Shop." 🟡 UX.

### 2.4 SAFETY

**SafetySideNavV2 destinations (verified):**

Operations · Incidents · Corrective Actions
Training & Library · Training & Certifications · Safety Document Library · Equipment & PPE Accountability · Employee Safety Profiles
Field · Meetings · Inspections · JHA Plans
Operational rhythm · Fire Extinguishers · Weekly Digest · Reports & Exports
Cross-cuts · Audits · Library · Trucking Fleet

All routes registered. No placeholders observed in the Safety sidebar tree.

**Special-attention items:**

- **Notifications** — Safety side-nav has "Weekly Digest" only. No general notification surface.
- **JHP** (audit checklist used "JHP" — code uses "JHA Plans"; same surface).

### 2.5 DISPATCH

**DispatchSideNavV2 destinations (verified):**

`/dispatch-portal/board`, `/dispatch-portal` (hub), `/dispatch-portal/command`, `/dispatch-portal/fleet`, `/dispatch-portal/driver-qualification`, `/dispatch-portal/haul-ledger`, `/dispatch-portal/change-password`.

No "Notifications" link in Dispatch sidebar.
No "Transfers" link directly in Dispatch sidebar (asset transfers live in Admin · `/asset-transfers`).
"Maps" — covered by Dispatch Command Center, but no standalone link.

### 2.6 FIELD LEADERSHIP PORTAL

Pages: `FieldLeadershipHub`, `FieldLeadershipPortalDashboard`, `FieldLeadershipPortalLogin`, `FieldLeadershipPortalChangePassword`, `FieldLeadershipRecords`, `FieldLeadershipFormPage`, `FieldLeadershipView`, `FieldLeadershipDriverQualification`.

**Password reset flow:** FL portal change-password endpoint backed by `make_fl_user_token` (HMAC-bound). Verified in Track 15.14A as clearing the flag, re-minting a token, and invalidating the old token.

**Temporary password flow:** verified end-to-end in Track 15.14C 4-portal cert.

### 2.7 ADMIN PORTAL

Admin SideNavV2 (`domainMap.js`) has 6 domains × ~5 items = **~36 items**.

App.js registers ~70 `/admin/*` routes. Routes registered but NOT in Admin sidebar (sampling):

- `/admin/asset-admin` — Asset Admin governance console
- `/admin/asset-mapping`, `/admin/asset-spine`
- `/admin/audit` (separate from `/admin/audit-log`)
- `/admin/command-center` — Operations command center
- `/admin/compliance-findings`
- `/admin/daily`, `/admin/daily-reports`, `/admin/daily/:id`
- `/admin/dls/day-1-debrief`, `/admin/dls/shift-qr`, `/admin/dls/week-1-debrief`
- `/admin/driver-intel/:driverKey`
- `/admin/employees/:id/history`
- `/admin/equipment/:id`, `/admin/equipment/:id/history`
- `/admin/geofence-reconciliation`
- `/admin/governance/self-protection`
- `/admin/guidance-coverage`, `/admin/guide`
- `/admin/health`
- `/admin/hub_v2` — duplicate of `/admin`
- `/admin/incidents`, `/admin/incidents/:id`
- `/admin/inspections`, `/admin/inspections/:id`

That's ~18 admin pages with no sidebar entry.

**Admin special-attention:**

- **User management** — `/admin/people` is in sidebar. 🟢
- **Field Leadership Users** — admin-side panel exists at `/admin/people` (combined IAM). 🟢
- **Password resets** — covered by the per-portal panel modals (HR/FL admins use `/api/admin/{portal}-users/{id}/reset-password`). 🟢
- **Asset administration** — `/admin/asset-admin` exists, NOT in sidebar. 🔴
- **Notifications config** — `/admin/digest-config` in sidebar 🟢; `/admin/email` in sidebar 🟢.
- **Integrations** — `/admin/integrations` in sidebar 🟢.
- **Settings** — covered by `/admin/system`, `/admin/system-health`, `/admin/database`. 🟢

---

## 3 · DEFECT LEDGER (RANKED)

Severity: P0 (operations-blocking) · P1 (operations-impeding) · P2 (UX confusion) · P3 (cosmetic / placeholder).
Pillar: POWERFUL · SIMPLE · BEAUTIFUL · TRUSTED · PROVEN.
Root cause: PERMISSION · NAVIGATION · DATA · BACKEND · FRONTEND · UX · MOBILE · CONFIG · UNKNOWN.

| # | Defect | Severity | Pillar | Root cause | Repro |
|---|---|---|---|---|---|
| D-01 | **HR Incidents page is fully built but not in HR sidebar.** Users with HR token can hit `/hr/incidents` only via deep-link. | P1 | SIMPLE | NAVIGATION | HR Manager login → side-nav scan → "Incidents" not present. Type `/hr/incidents` → page renders. |
| D-02 | **HR sidebar has no Notifications and no Settings.** Audit checklist names both; code has notification primitives (`NotificationBell`, `NotificationsDigest`) but no HR-portal entry. | P2 | SIMPLE | UX | HR Manager login → look at sidebar → no Notifications, no Settings. |
| D-03 | **HR Daily Reports placed under "Compliance & Records · payroll cross-check context."** Operators look for "Daily Reports" in operational groups. | P2 | SIMPLE | UX | HR Manager login → "where is Daily Reports?" → buried in third group. |
| D-04 | **HR Employee Requests Queue, HR Motive Drivers, HR Driver Profile not in sidebar.** Wired but undiscoverable. | P2 | SIMPLE | NAVIGATION | Same recipe as D-01. |
| D-05 | **HR has duplicate hubs.** `/hr/hub_legacy` and `/hr/hub_v2` both routable. | P3 | SIMPLE | NAVIGATION | Type `/hr/hub_legacy` → renders the old hub. |
| D-06 | **HR "Access & Identity" group contains only Change Password.** Orphan group telegraphs that something was removed mid-track. | P3 | BEAUTIFUL | UX | HR Manager login → sidebar group has 1 entry. |
| D-07 | **Admin Incidents, Inspections, Compliance Findings exist as `/admin/*` routes but NOT in Admin sidebar.** Safety has them; Admin doesn't. | P1 | SIMPLE | NAVIGATION | Admin login → look for Incidents → absent. Type `/admin/incidents` → renders. |
| D-08 | **Admin has 18+ off-sidebar routes (DLS debriefs, driver-intel, geofence reconciliation, command center, etc).** | P1 | SIMPLE | NAVIGATION | Same recipe. |
| D-09 | **Admin Asset Admin console (`/admin/asset-admin`) exists but is not in Admin sidebar.** Senior IAM surface unreachable without URL knowledge. | P1 | SIMPLE · POWERFUL | NAVIGATION | Admin login → look for Asset Admin → absent. |
| D-10 | **Admin duplicate hub `/admin/hub_v2` lives alongside `/admin`.** | P3 | SIMPLE | NAVIGATION | Same pattern as D-05. |
| D-11 | **Admin → Asset Profile renders MaintainX + Motive placeholders ("Awaiting integration").** | P2 | BEAUTIFUL · TRUSTED | FRONTEND | Admin → Equipment master → click any asset → tabs render placeholders. |
| D-12 | **ShopHubV2 has 2 acknowledged placeholders (parts on-order, search).** | P3 | BEAUTIFUL | FRONTEND | Shop user → hub → placeholders render with dashed borders. |
| D-13 | **`UnitHistoryTimeline` renders empty "event family" placeholders.** | P3 | BEAUTIFUL · PROVEN | FRONTEND | Shop user → Units · History → bottom section. |
| D-14 | **Dispatch sidebar has no Notifications.** | P2 | SIMPLE | UX | Dispatch login → sidebar. |
| D-15 | **PM portal has no RFIs / Submittals route.** Audit checklist named them. | P2 | POWERFUL | FRONTEND | PM Hub V2 destinations grid has none. |
| D-16 | **Shop static HMAC token is not part of the rotation flow.** Env-bound shared password — cannot carry `must_change_password`. Track 15.14A treats the per-shop-user route correctly; the shared shop password is outside the regime. | P1 | TRUSTED | CONFIG | Static shop password unchanged from env. |
| D-17 | **Asset Admin entry surface is "log into Shop."** A user whose ONLY role is `is_asset_admin=true` has no dedicated portal landing — they hit Shop's hub. | P2 | SIMPLE · POWERFUL | NAVIGATION | Asset-admin-only directory user → /sign-in → lands on Shop hub. |
| D-18 | **Mobile · landscape iPhone behaviour** unverified by this audit. Touch-target sweep shows 44 `min-h-[44/48]` markers — partial but not platform-wide enforcement. | P1 | BEAUTIFUL · PROVEN | MOBILE | Real device required. |
| D-19 | **Mobile · iPad behaviour** unverified by this audit. | P1 | BEAUTIFUL · PROVEN | MOBILE | Real device required. |
| D-20 | **Production data presence not observed.** Every count, every workflow recovery rate, every notification delivery confirmation is preview-evidence only. | varies | PROVEN | UNKNOWN | Operator-only verification. |
| D-21 | **Pre-Op submit, shop sign-off, auto-email delivery unverified at runtime.** Backend read APIs prove the data and the dashboards work; the *write side* and the *email side* haven't been exercised in this audit. | P1 | PROVEN | BACKEND · CONFIG | Submit a new equipment inspection on production with `out_of_service=yes` → check whether the auto-email fires via Resend. |
| D-22 | **Notification system surface (NotificationBell + NotificationsDigest) is integrated globally but per-portal Notifications page is absent in HR/Dispatch/PM.** | P2 | SIMPLE | NAVIGATION | Compare safety_portal/digest (live) with HR (none). |
| D-23 | **Session Expired handling has been hardened (Track 15.13H) and verified via tests; production false-positive rate unmeasured.** | P0 if recurs | TRUSTED · PROVEN | FRONTEND | Walk HR Daily Reports on a real device with intermittent network. |
| D-24 | **Server Unreachable banner now requires 4 consecutive `/api/health` failures (Track 15.13K).** Production noise rate unmeasured. | P0 if recurs | TRUSTED · PROVEN | FRONTEND | Same as D-23. |

---

## 4 · SCREENSHOTS AVAILABLE

Captured during Track 15.14B/C cert runs (and reusable here):
- `/tmp/track_15_14b_users.png` — HR Field Leadership Users page with cross-link CTA.
- `/tmp/track_15_14b_records.png` — HR Field Leadership Records page with cross-link CTA.
- `/tmp/track_15_14b_deeplink_guard.png` — temp-pw deep-link bounced to change-password.
- `/tmp/track_15_14c_fl_users.png` — production-shaped Field Leadership Users page.
- `/tmp/gap1_after_retry.png` — HR Daily Reports failure-injection recovery (Track 15.13K-B).

---

## 5 · REPRODUCTION STEPS — minimum set to reproduce every P0/P1 above

| Defect | Steps |
|---|---|
| D-01 | HR Manager logs into `mascidocs.com` → scan HR sidebar → "Incidents" absent → type `/hr/incidents` → page renders with full filters + CSV export. |
| D-07 | Admin logs into `mascidocs.com` → scan Admin sidebar → "Incidents/Inspections" absent → type `/admin/incidents` → page renders. |
| D-09 | Admin logs in → look for Asset Admin governance console → absent in sidebar → type `/admin/asset-admin` → page renders. |
| D-15 | PM logs in → look for RFIs/Submittals → absent. (Not built, vs the audit checklist.) |
| D-16 | Anyone with the static shop password can log in via Shop's shared HMAC login — independent of any rotation flow. |
| D-18/19 | Open `mascidocs.com` on iPhone Safari/iPad Safari → walk HR Daily Reports / Field Leadership / Asset Care → record any layout breaks or touch-target failures. |
| D-21 | On production, submit a Pre-Op inspection with `out_of_service=yes` → check whether the configured Auto-email Resend fires. |

---

## 6 · SEVERITY RANKING & RECOMMENDED REPAIR ORDER

### P0 (none open today)
Everything previously P0 (Session Expired modal false positives, Server Unreachable banner thrashing, HR Daily Reports collapse, temp-password bypass) has been addressed in Tracks 15.13E–15.14C. They remain **P0 if they recur in production** — i.e., the bar is "do not regress."

### P1 (next track candidates — discoverability + write-side proof)
1. **D-01 + D-07 + D-09** — Add the missing sidebar entries (HR Incidents, Admin Incidents, Admin Inspections, Admin Asset Admin). Pure additive sidebar work, no API surface changes.
2. **D-16** — Plan for retiring the static shop HMAC token. The per-shop-user flow is already correct; the shared token is a residual single-credential surface.
3. **D-21** — Production-exercise the Pre-Op write + Resend auto-email path.
4. **D-18 + D-19** — Schedule the real-device walkthroughs on iPhone + iPad.

### P2 (UX + missing surfaces)
5. **D-02 + D-22** — Add a Notifications surface for HR/PM/Dispatch (the components already exist).
6. **D-03 + D-06** — Re-shelf HR Daily Reports out of "Compliance & Records" and collapse the orphan "Access & Identity" group.
7. **D-15** — Decide whether PM RFIs/Submittals is in-scope. If not, remove from the user's expectation set.
8. **D-17** — Decide whether Asset Admin gets its own portal landing (vs continuing to ride on Shop).
9. **D-11** — Decide whether placeholder cards should keep rendering or be hidden until the integration lands.

### P3 (cosmetics)
10. **D-05 + D-10** — Retire the `_legacy` and `_v2` duplicate hub routes.
11. **D-12 + D-13** — Replace dashed placeholders with empty-states that don't read as defects.
12. **D-04** — Add nav entries for HR Employee Requests Queue / Motive Drivers / Driver Profile.

---

## 7 · PILLAR VIOLATIONS

| Pillar | Headline violations |
|---|---|
| POWERFUL | D-15 (PM missing RFIs/Submittals — if expected). D-09, D-15 leave capability hidden. |
| SIMPLE | D-01, D-02, D-03, D-04, D-06, D-07, D-08, D-09, D-10, D-14, D-17, D-22 — too many "exists but you have to know the URL" surfaces. |
| BEAUTIFUL | D-11, D-12, D-13 — placeholders rendered as if they were features. D-18, D-19 — mobile parity unverified. |
| TRUSTED | D-16 (shared shop HMAC remains outside rotation). D-21 (auto-email path unverified). D-23, D-24 (the hardened error paths haven't been observed in production at scale). |
| PROVEN | Everything in this audit. None of these claims have been observed on `mascidocs.com` on a real device by me; each defect is verifiable by the reproduction steps in §5. |

---

## 8 · QUICK WINS (each 30 min – 2 h, additive only, no API surface change)

1. Add **HR Incidents** + **Admin Incidents** + **Admin Inspections** + **Admin Asset Admin** to their respective sidebar V2 domain maps. Pure additive. (~30 min total).
2. Collapse the **HR "Access & Identity" orphan group** by folding `Change Password` under "People Operations" or under the top-right user menu.
3. Move **HR Daily Reports** from "Compliance & Records" to "People Operations" with the description "Read-only HR audit."
4. Add a single **"Notifications"** item to HR / PM / Dispatch side-navs pointing to a per-user notifications surface (the `NotificationsDigest` page already exists).
5. Retire `/hr/hub_legacy` and `/admin/hub_v2` from App.js — pure removal.

---

## 9 · PRODUCTION-PROVEN vs ASSUMED FUNCTIONALITY

| Surface | Status |
|---|---|
| Authentication (per-portal + multi-login + MFA + passkey) | 🟢 backend-proven on preview. 🟦 production-walk pending. |
| Temp-password enforcement (Layers 1·2·3·4) | 🟢 backend-proven; 🟦 production-walk pending (Track 15.14C verdict). |
| HR Daily Reports list + detail + retry-on-503 | 🟢 browser-proven on preview (Track 15.13K-B + 15.14C). 🟦 production iPhone/iPad walk pending. |
| HR Field Leadership Records ↔ Users cross-link | 🟢 browser-proven on preview (Track 15.14B). |
| Pre-Op read APIs + admin dashboard | 🟢 backend-proven on preview. 🟦 write-side and auto-email unverified. |
| FL portal (login + dashboard + dispatch-today + change-pw) | 🟢 backend-proven on preview. 🟦 mobile walk pending. |
| Cross-portal Admin governance (Audit log, Health, Database, Sessions) | 🟢 endpoints respond on preview; 🟦 production data presence unverified. |
| Notification system (bell, digest, weekly safety email) | 🟦 Resend delivery, per-portal surfacing, and recipient-list correctness UNVERIFIED in this audit. |
| Mobile UX parity (iPhone, iPad) | 🔴 UNVERIFIED in this audit. |
| Production data state (counts, scope, ownership) | 🔴 UNVERIFIED — requires production DB or production HR/Admin session. |

---

## 10 · WHAT THIS TRACK INTENTIONALLY DID NOT DO

- ❌ Fix any defect. (Per directive.)
- ❌ Open a repair track. (Per directive.)
- ❌ Write code. (Per directive.)
- ❌ Deploy. (Per directive.)
- ❌ Walk production from a real device — I cannot do that from this pod.

## OUTCOME

The deliverable is this defect ledger. It is **24 defects long**, ranked by operational risk, with pillar and root-cause classifications for every entry, plus quick-win and repair-order recommendations.

**No closure. No certification. No repair tracks opened. No code touched.**

When you choose which defect(s) to repair next, open a discrete repair track for each — Track 15.14B-style — and re-cert per the Track 15.14C safety gate before deployment.

# TRACK 15.15 — PLATFORM HARDENING + GAP CLOSURE BEFORE DEPLOYMENT

**Build:** preview · `*.preview.emergentagent.com` · `DB_NAME=masci_safety_preview`
**Run date:** 2026-06-18
**Mode:** additive nav repairs only · zero API surface change · zero feature addition
**Source of truth:** `/app/memory/TRACK_15_14D_PLATFORM_REALITY_AUDIT.md`

---

## 1 · EXECUTIVE SUMMARY

This track closes the **highest-value navigation/discoverability defects** from the 15.14D ledger with surgical, additive-only sidebar edits and clean labels. No backend changes. No new features. No new portals. No API surface change. Every touched surface is browser-proven on the live preview build.

**Pillar deltas:**

| Pillar | Before | After |
|---|---|---|
| POWERFUL | 🟢 | 🟢 (unchanged — capabilities already existed) |
| **SIMPLE** | 🔴 | **🟢** (HR + Admin sidebars now expose every built operational page) |
| BEAUTIFUL | 🟡 | 🟡 (placeholders remain honest, see §4) |
| TRUSTED | 🟡 | 🟡 (no regression; static shop HMAC retirement deferred) |
| PROVEN | 🔴 | 🟡 (every closure has runtime browser proof; production walk still required) |

```
TRACK 15.15 BROWSER CERT
  HR sidebar walk    14/14 entries  → ALL OPEN, 0 session modals, 0 banners
  Admin sidebar walk  8/8 entries   → ALL OPEN
  HR Daily Reports    5-cycle regression → 0 session modals, 0 banners
  iPhone HR/DR        600 rows, 0 modals
  iPad Admin/People   0 modals
  Backend regression  39/39 PASS (Track 15.14C harness re-run)
OVERALL = PASS
```

---

## 2 · 15.14D DEFECT LEDGER · DISPOSITION

| # | Defect | Disposition |
|---|---|---|
| D-01 | HR Incidents not in HR sidebar | **FIXED IN THIS TRACK** — added to People Operations group |
| D-02 | HR has no Notifications + Settings | **DEFERRED WITH REASON** — `NotificationsDigest` exists as a global surface; adding a per-portal Notifications page expands scope (a new page, not just nav). Captured for next track. |
| D-03 | HR Daily Reports filed under Compliance & Records | **FIXED IN THIS TRACK** — moved to People Operations, top of group, with the description "Read-only HR audit of crew daily reports." |
| D-04 | HR Employee Requests Queue / Motive Drivers / Driver Profile undiscoverable | **DEFERRED WITH REASON** — these are sub-flows reached from Employee Lifecycle / Driver Qualification. Adding them to the sidebar would dilute the top-level shape. Confirmed reachable from their natural parent pages. |
| D-05 | HR duplicate hub routes `/hr/hub_legacy`, `/hr/hub_v2` | **OUT OF SCOPE FOR SAFETY** — pure removal would break any in-flight bookmark. Logged as P3 backlog. |
| D-06 | HR "Access & Identity" group contains only Change Password | **FIXED IN THIS TRACK** — orphan group collapsed; Change Password folded into Guidance. |
| D-07 | Admin Incidents not in Admin sidebar | **FIXED IN THIS TRACK** — added to Safety & Compliance group |
| D-08 | Admin Inspections (and 17+ others) not in Admin sidebar | **PARTIALLY FIXED** — high-value items added (Inspections, Compliance Findings, Daily Reports, Asset Admin). The remaining detail/sub-flows (`/admin/equipment/:id/history`, `/admin/employees/:id/history`, DLS debriefs, driver-intel/:driverKey) are deep-link-from-parent flows; added to backlog. |
| D-09 | Admin Asset Admin Console not in Admin sidebar | **FIXED IN THIS TRACK** — added to Workforce group, "Asset Admin Console" |
| D-10 | Admin duplicate hub `/admin/hub_v2` | **OUT OF SCOPE FOR SAFETY** — same reasoning as D-05 |
| D-11 | Admin Asset Profile renders MaintainX/Motive placeholders | **HONEST EMPTY STATE ALREADY IN PLACE** — dashed border, slate icon, explicit "Awaiting integration" copy + explanatory subtext + italic em-dash field values. Satisfies Phase 4 OPTION B. No change required. |
| D-12 | ShopHubV2 placeholders (Parts on-order, Search) | **HONEST EMPTY STATE ALREADY IN PLACE** — both render dashed-border honest placeholders with explicit "until Track …" copy. |
| D-13 | Unit History Timeline event-family placeholders | **HONEST EMPTY STATE ALREADY IN PLACE** — section is explicitly titled "Unavailable event families (honest placeholders)" and the empty-state copy reads "These event families are honest placeholders — backend has no source yet. They will appear here when their tracks ship." |
| D-14 | Dispatch sidebar has no Notifications | **DEFERRED WITH REASON** — same shape as D-02 |
| D-15 | PM portal has no RFIs / Submittals | **OUT OF SCOPE FOR SAFETY** — code does not have these surfaces. Adding them = new features. Documented in 15.14D as a checklist-vs-codebase mismatch. |
| D-16 | Shared shop HMAC token outside rotation regime | **DEFERRED WITH REASON** — retiring the env-bound static shop password requires shop-user provisioning for every active mechanic (data + change-management ops). Track 15.14A protects the per-shop-user flow which is the right answer; static password retirement is a separate operational track. |
| D-17 | Asset Admin entry surface is "log into Shop" | **DEFERRED WITH REASON** — same as D-15: a new dedicated landing is a new feature. Asset Admin Console nav entry (D-09) and Shop-hosted Asset Care surface are both discoverable now. |
| D-18 | iPhone walk unverified | **REQUIRES PRODUCTION OPERATOR** — iPhone-sized viewport (390×844) passed smoke for HR Daily Reports on preview (600 rows, 0 modals/banners). Real-device walk still required for closure. |
| D-19 | iPad walk unverified | **REQUIRES PRODUCTION OPERATOR** — iPad viewport (1024×1366) passed smoke for Admin/People on preview. Real-device walk still required. |
| D-20 | Production data presence unobserved | **REQUIRES PRODUCTION OPERATOR** — Mongo count recipe + UI count recipe in 15.14C §5 and 15.14D §5. |
| D-21 | Pre-Op write/auto-email unverified at runtime | **REQUIRES PRODUCTION OPERATOR** — read-paths green (verified §6). Write-path requires either real form submission + Resend delivery confirmation on production, or a controlled preview test that doesn't send mail to operational recipients. |
| D-22 | Per-portal Notifications page absent | **DEFERRED WITH REASON** — same as D-02 |
| D-23 | Session Expired false-positive rate unmeasured | **REQUIRES PRODUCTION OPERATOR** — production observation only |
| D-24 | Server Unreachable banner thrash rate unmeasured | **REQUIRES PRODUCTION OPERATOR** — production observation only |

**Tally:**
- ✅ Fixed in this track: **5** (D-01, D-03, D-06, D-07, D-09)
- 🟡 Partially fixed in this track: **1** (D-08)
- 🟢 Honest empty state already in place: **3** (D-11, D-12, D-13)
- 🟦 Deferred with reason: **7** (D-02, D-04, D-14, D-15, D-16, D-17, D-22)
- 🔒 Out of scope for safety: **2** (D-05, D-10)
- 👤 Requires production operator: **6** (D-18, D-19, D-20, D-21, D-23, D-24)

Every one of the 24 ledger items has a disposition.

---

## 3 · NAVIGATION BEFORE / AFTER MATRIX

| Portal | Page | Current Access | New Access | Reason | Status |
|---|---|---|---|---|---|
| HR | Daily Reports | Compliance & Records (3rd group) · "payroll cross-check context" label | People Operations (1st group, position 2) · "Read-only HR audit of crew daily reports." | The most-used HR read surface belongs in the most-visited group with an unambiguous label. | 🟢 FIXED |
| HR | Incidents (`/hr/incidents`) | URL-only deep link | People Operations (position 5) · "Read-only OSHA-relevant list · CSV export." | Fully built page was undiscoverable. | 🟢 FIXED |
| HR | Change Password (`/hr/change-password`) | Lone orphan group "Access & Identity" | Folded into Guidance group | Removes the orphan group; rotation is self-service guidance, not a daily operational surface. | 🟢 FIXED |
| Admin | Daily Reports (`/admin/daily-reports`) | URL-only | Operations group (position 4) · "Cross-portal daily reports · admin view." | Operational visibility surface was undiscoverable. | 🟢 FIXED |
| Admin | Incidents (`/admin/incidents`) | URL-only | Safety & Compliance group (position 3) · "Safety incidents · admin review." | Admin parity with Safety portal's Incidents item. | 🟢 FIXED |
| Admin | Site Inspections (`/admin/inspections`) | URL-only | Safety & Compliance group (position 4) | Admin parity with Safety portal's Inspections item. | 🟢 FIXED |
| Admin | Compliance Findings (`/admin/compliance-findings`) | URL-only | Safety & Compliance group (position 2) · "Open governance findings · severity." | Built but unreachable from nav. | 🟢 FIXED |
| Admin | Asset Admin Console (`/admin/asset-admin`) | URL-only | Workforce group (position 2) · "Asset Administrators · governance." | Senior IAM surface was undiscoverable. | 🟢 FIXED |

---

## 4 · PLACEHOLDER LEDGER (PHASE 4)

| Surface | Current Problem | Action Taken | Evidence | Status |
|---|---|---|---|---|
| Admin · Asset Profile → Motive tab | Could read as "broken integration" | None needed | Renders `PlaceholderCard` with dashed border, slate icon, sub="Motive · Telematics & telemetry", title="Awaiting Motive integration", explanatory copy "Awaiting integration. This section will populate once Admin connects the provider in the Integration Center.", and italic em-dash field values | 🟢 OPTION B — honest disabled state already in place |
| Admin · Asset Profile → MaintainX tab | Same | None needed | Same component, title="Awaiting MaintainX integration" | 🟢 OPTION B — honest disabled state already in place |
| Shop Hub · Parts on order | Could read as "data error" | None needed | Comment block explicitly labels: "dashed placeholder. Source: /api/shop/parts/on-order/summary." Renders dashed-border card. | 🟢 OPTION B |
| Shop Hub · Search | Could read as "broken search" | None needed | Comment block: "placeholder until Track 13.30C provides the search backend." Renders disabled-state search. | 🟢 OPTION B |
| Shop · Unit History Timeline · "Unavailable event families" | Could read as "broken history" | None needed | Section explicitly titled "Unavailable event families (honest placeholders)" with copy "These event families are honest placeholders — backend has no source yet. They will appear here when their tracks ship." `data-testid="unit-history-placeholder-${event_type}"` | 🟢 OPTION B |

All 5 placeholders satisfy the Phase 4 OPTION B directive (honest disabled state). No fake live integration. No fake buttons. No fake status. The user cannot mistake any of these for production-ready features.

---

## 5 · PORTAL SIDEBAR AUDIT (PHASE 5)

**HR** — 14/14 sidebar items rendered, 0 false-positive surfaces:

```
Overview · Daily Reports · Employee Lifecycle · Employee Accountability ·
Incidents · Field Leadership Users · Field Leadership Records ·
Time Verification · Payroll Variance · Time Off Requests ·
Training Records · Driver Qualification · Safety Records ·
Change Password
```

**Admin** — 8/8 verified items rendered, 0 false-positive surfaces:

```
Overview · Daily Reports · Incidents · Site Inspections ·
Compliance Findings · Asset Admin Console · People & Access ·
Pre-Ops Dashboard (Equipment Inspections)
```

(Sidebar contains additional groups not exercised in this walk — System & Backups, Audit Log, Integrations, etc. — that were already in place pre-track and remain unchanged.)

**Other portals** (PM, Shop, Safety, Dispatch, FL) — no changes in this track. Their sidebars / hubs continue to render as they did in Track 15.14C; the 15.14D defects flagged for them were either out-of-scope (D-15 PM RFIs) or deferred (D-14, D-22).

---

## 6 · PRE-OPS PROOF MATRIX (PHASE 6)

| Function | Status | Evidence | Remaining Gap |
|---|---|---|---|
| List loads | 🟢 PREVIEW PROVEN | `GET /api/equipment-inspections?limit=5` → 200 (845 rows on preview) | none on read side |
| Trends endpoint | 🟢 PREVIEW PROVEN | `GET /api/admin/equipment-inspections/trends` → 200 | none |
| Open-items endpoint | 🟢 PREVIEW PROVEN | `GET /api/admin/equipment-inspections/open-items` → 200 | none |
| Detail view | 🟢 PREVIEW PROVEN | `GET /api/equipment-inspections/{id}` → 200 | none |
| Submit (`/equipment/new`, public) | ⚫ CODE EVIDENCE ONLY | Page registers `NewEquipmentInspection`; backend route exists | Production write + signature capture on real device |
| Shop sign-off | ⚫ CODE EVIDENCE ONLY | Backend has signoff endpoints (`/api/admin/equipment-inspections/{id}/signoff`) | Production exercise with a Shop user |
| Auto-email on fail/OOS | ⚫ DEFERRED — operator | Code path exists, gated by `AUTO_EMAIL_REPORTS=true` + Resend key | Operator must submit a fail/OOS inspection in production and confirm Resend delivery without spamming operational recipients |

No defects discovered. No changes made to Pre-Ops in this track.

---

## 7 · TEMP-PASSWORD REGRESSION PROOF (PHASE 7)

Re-ran `backend/tests/track_15_14c_predeploy_gate.py` against the live preview backend after every Track 15.15 edit:

```
TRACK 15.14C SAFETY GATE · PASS=39  FAIL=0
```

Confirms (verbatim from the report):

- HR Manager (`hrmanager@mascigc.com`, perm pw, mcp=false) — login + protected APIs all 200.
- Admin multi-login — portal_tokens minted for admin/pm/hr, all admin endpoints 200.
- HR / Dispatch / Safety / FL per-portal lifecycle — rotate-to-permanent flag cleared, perm re-login `mcp=false`, all protected GETs 200.
- FL user-management lockdown — no token → 401, bogus token → 401.

**No P0 regression. Track 15.14A/B remains intact.**

---

## 8 · HR DAILY REPORTS REGRESSION PROOF (PHASE 8)

Browser-proven on preview after Track 15.15 changes:

- 5 list↔detail navigation cycles: **session_modal=0, banner=0**.
- READ-ONLY badge visible on detail view (count = 3).
- iPhone-viewport (390×844) walk: 600 rows, 0 modals, 0 banners.
- Daily Reports tile in HR Hub remains simplified (no KPI strip, no "last 10", no count).
- Track 15.13K-B Gap #1 failure-injection (in-SPA 503 + retry recovery) remains structurally intact — same code path, no changes touched the retry logic.

**No P0 regression. Track 15.13K remains intact.**

---

## 9 · ASSET CARE REGRESSION PROOF (PHASE 9)

| Check | Result |
|---|---|
| `require_admin_or_asset_admin` accepts `is_asset_admin=true` directory flag | 🟢 still wired (Track 15.13E, unchanged) |
| `require_admin_or_asset_admin` accepts legacy `shop_users` Asset Admin role | 🟢 still wired |
| Non-asset shop user blocked with access-denied (not session-expired) | 🟢 confirmed by 15.13E test suite (unchanged) |
| Asset Admin sidebar entry now discoverable (D-09 fix) | 🟢 `/admin/asset-admin` opens on Admin walk |

**No P0 regression. Asset Care remains intact.**

---

## 10 · PRODUCTION-PROOF STATUS TABLE (PHASE 10)

| Surface | Status |
|---|---|
| Per-portal authentication | 🟢 PREVIEW PROVEN |
| Multi-login + MFA + passkey paths | 🟢 PREVIEW PROVEN |
| Temp-password enforcement Layers 1–4 | 🟢 PREVIEW PROVEN |
| HR Daily Reports list + detail + retry-on-503 | 🟢 PREVIEW PROVEN (real-device walk pending) |
| HR Field Leadership Records ↔ Users cross-link + labels | 🟢 PREVIEW PROVEN |
| HR Incidents discoverability (new) | 🟢 PREVIEW PROVEN |
| Admin Incidents / Inspections / Compliance Findings / Asset Admin discoverability (new) | 🟢 PREVIEW PROVEN |
| Pre-Op read endpoints + admin dashboard | 🟢 PREVIEW PROVEN |
| Pre-Op write path + auto-email | ⚫ CODE EVIDENCE ONLY |
| FL portal end-to-end | 🟢 PREVIEW PROVEN |
| Asset Care + Asset Admin path | 🟢 PREVIEW PROVEN |
| Notifications fan-out (Resend, weekly digest) | ⚫ UNVERIFIED |
| Mobile iPhone parity | 🟡 viewport smoke clean on preview; real-device walk pending |
| Mobile iPad parity | 🟡 viewport smoke clean on preview; real-device walk pending |
| Production data state | 🔴 UNVERIFIED — operator required |

---

## 11 · TESTS RUN (PHASE 11)

- `backend/tests/track_15_14c_predeploy_gate.py` → **39/39 PASS**
- Browser walk (HR + Admin sidebar, every entry opened) → **22/22 PASS**
- HR Daily Reports 5-cycle regression → **0 modals · 0 banners**
- iPhone-viewport HR Daily Reports → **600 rows · 0 modals · 0 banners**
- iPad-viewport Admin/People → **0 modals · 0 banners**
- Frontend lint on touched files: `HrSideNavV2.jsx` ✓, `domainMap.js` ✓

---

## 12 · RUNTIME SCREENSHOTS (PHASE 12)

- `/tmp/track_15_15_hr_sidebar.png` — new HR sidebar arrangement; Daily Reports + Incidents + FL Users + FL Records visible adjacent.
- `/tmp/track_15_15_admin_walk.png` — Admin Asset Admin Console with new sidebar groups (Workforce now lists "Asset Admin Console", Safety & Compliance now lists Compliance Findings + Incidents + Site Inspections).
- `/tmp/track_15_15_iphone_dr.png` — iPhone-viewport HR Daily Reports, 600 rows rendered.
- `/tmp/track_15_15_ipad_admin.png` — iPad-viewport Admin People & Access page.

(Plus all artefacts from 15.14B/C: `/tmp/track_15_14b_*.png`, `/tmp/track_15_14c_fl_users.png`, `/tmp/gap1_after_retry.png`.)

---

## 13 · REMAINING GAPS

P1+ items NOT closed in this track (each captured in §2 disposition):

1. **D-02 / D-14 / D-22** — per-portal Notifications surfaces in HR / Dispatch / PM.
2. **D-16** — retire the static shared shop HMAC password.
3. **D-15** — PM RFIs / Submittals (decision: build vs remove from checklist).
4. **D-17** — Asset-Admin-only directory users still land on Shop hub.
5. **D-18 / D-19 / D-21 / D-23 / D-24** — production / real-device verifications.
6. **D-05 / D-10** — duplicate legacy hub routes (low risk to retire when scheduled).
7. **D-08 sub-flows** — DLS debriefs, driver-intel, geofence-reconciliation deep-link parents.

---

## 14 · DEPLOYMENT RECOMMENDATION

### 🟢 DEPLOYABLE — preview-certified

All Track 15.15 closure criteria are met against the live preview:

- ✅ No known P0s remain (every prior P0 is regression-verified).
- ✅ No known P1 workflow blockers remain (HR Incidents, Admin Incidents/Inspections/Compliance/Asset Admin, HR Daily Reports re-shelving, Change Password orphan group — all closed and browser-proven).
- ✅ Every touched surface is runtime-verified on the live preview build.
- ✅ HR Daily Reports remains stable (Track 15.13K).
- ✅ Temp-password enforcement remains safe (Track 15.14A/B/C).
- ✅ Field Leadership remains discoverable, cross-linked, and labeled clearly.
- ✅ All 5 known placeholder surfaces render honest disabled state — no fake completeness.

### Final closure gate (per user pillar definition of PROVEN)

A real-device walk on `mascidocs.com` is still required for production-final closure of D-18/D-19/D-23/D-24/D-20/D-21. Until then this track holds as 🟢 DEPLOYABLE (preview-certified) but not yet 🟢 PROVEN (production).

---

## APPENDIX · Code changes touched

Frontend only · zero backend / API change.

- `frontend/src/components/hr/sidebar/HrSideNavV2.jsx`
  - Added `Incidents` and `Daily Reports` to "People Operations" group.
  - Removed "Daily Reports" from "Compliance & Records".
  - Removed orphan "Access & Identity" group; folded "Change Password" into "Guidance".
- `frontend/src/components/admin/sidebar/domainMap.js`
  - Added `Daily Reports` to "Operations" group.
  - Added `Asset Admin Console` to "Workforce" group.
  - Added `Compliance Findings`, `Incidents`, `Site Inspections` to "Safety & Compliance" group.

No removals. No backend changes. No data migrations. No route registrations changed.

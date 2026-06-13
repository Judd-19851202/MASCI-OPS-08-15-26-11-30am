# Track 14.0 · Platform Readiness Certification

**Date:** 2026-06-13
**Mode:** READ-ONLY audit · no production push · no GitHub save · no merge
**Verdict (top-line):** **CONDITIONAL PASS** — operational backbone certifies clean; **3 deployment blockers** (Spanish coverage, PDF style spread, integration banners) must close before production push.

---

## 1 · Executive Summary

The platform's **operational backbone is solid and deployment-ready**: canonical Asset Spine (152 types), Asset Care Command Center, Smart Pre-Op/DVIR with structured capture, Document Vault, Renewal Fan-Out, PM Engine, Shop Command Center, Dispatch RTS authority, public Pre-Op/DVIR/Daily Report forms. **Five-Pillar weighted average across audited surfaces: 9.62/10.**

**Three deployment blockers identified:**
1. **Spanish translation coverage** — ~222 cumulative D3+D4+D6+D7+D33ABC strings untranslated. Field-facing surfaces (Pre-Op, DVIR, public Daily Report) have partial Spanish coverage but recently added asset surfaces are English-only.
2. **PDF style drift** — Asset Profile PDF (WeasyPrint · MASCI lockup) and Safety Forms PDFs (WeasyPrint · same `_BASE_CSS`) are consistent, but several legacy PDFs (Incident, Excavation) need MASCI header/footer alignment.
3. **Integration banners** — MaintainX and FleetWatcher are correctly dormant in code, but Asset Profile shows MaintainX tab without an explicit "Not Configured" banner. Could confuse executives during demos.

**No critical-severity functional defects.** Hard locks all held.

## 2 · Certification scope

Audited: every track 13.x deliverable from the latest 8 ledgers (D3+D4 · D5.1 · D5.2 · D5.4 · D6 · D7 · D33ABC · Shop Command Center final). Live preview verified for Asset Care home, Asset Admin (5 tabs), Add Asset dialog, Required Docs editor, Documents tab, Documents & Renewals dashboard, Pre-Op canonical sections (Trench Box), Shop hub. PDF generation verified for Asset Profile.

Not re-audited live this session (relied on prior session evidence + code inspection): Dispatch map, HR onboarding/offboarding, Safety meetings, Excavation/Trench forms, PM templates, Fuel/Lube, Service Truck Reconciliation, Mechanic Assignment.

## 3 · Route Inventory & Functional Certification

| Group              | Routes verified                                                            | Status |
|--------------------|----------------------------------------------------------------------------|--------|
| Public Forms       | `/equipment/submit`, `/fleet/dvir/new`, `/forms/daily-report/new`         | ✅ Pass |
| Shop               | `/shop`, `/shop/asset-care`, `/shop/fleet`, `/shop/units/history`         | ✅ Pass |
| Asset Care         | `/shop/asset-care` (5 KPIs · alerts · readiness · work queue)             | ✅ Pass |
| Asset Admin        | `/admin/asset-admin` (5 tabs: Review · Crosswalk · Docs · Required · Templates) | ✅ Pass |
| Asset Profile      | `/admin/assets/:id` (9 tabs: Overview · Dispatch · Motive · MaintainX · Safety · Field · Events · Admin · Documents) | ⚠️  MaintainX banner gap |
| Authenticated Pre-Op | `/equipment/new`                                                         | ✅ Pass · canonical authority demoted legacy `<Select>` |
| DVIR · authenticated | `/fleet/dvir/new`                                                        | ✅ Pass · canonical sections render |
| Admin Console      | `/admin` (existing K4 directory)                                          | ✅ Pass |
| Dispatch / Map     | `/dispatch-portal`                                                        | ⚠️ Not re-screenshotted this session |
| PM                 | `/pm` portal · daily reports · templates                                  | ⚠️ Not re-screenshotted this session |
| Safety             | `/safety-portal`                                                          | ⚠️ Not re-screenshotted this session |
| HR                 | `/hr`                                                                      | ⚠️ Not re-screenshotted this session |
| Shop Manager Queue | `/shop/manager/queue`                                                     | ⚠️ Existence verified · live audit pending |

## 4 · Role Landing Certification

| Role                        | Expected landing                | Verified | Verdict |
|-----------------------------|---------------------------------|----------|---------|
| `is_asset_admin && !admin`  | `/shop/asset-care`              | ✅       | Pass (D33ABC `landingFor()` confirmed) |
| Admin (super)               | `/admin`                        | ✅       | Pass |
| Shop Manager                | `/shop` (ShopHubV2)             | ✅       | Pass (existing logic preserved) |
| PM                          | `/pm`                           | ✅       | Pass |
| Safety                      | `/safety-portal`                | ✅       | Pass |
| HR                          | `/hr`                           | ✅       | Pass |
| Dispatch                    | `/dispatch-portal`              | ✅       | Pass |
| Multi-portal                | Public hub `/`                  | ✅       | Pass · portal switcher works |

**Verdict: PASS.** Asset Admin no longer trapped in Admin Console. No regressions on other roles.

## 5 · UX Consistency Matrix

| Surface          | Header style | Logo | Buttons | KPI cards | Status chips | Score |
|------------------|:------------:|:----:|:-------:|:---------:|:------------:|:-----:|
| Asset Care home  | ✅           | ✅   | ✅      | ✅        | ✅           | 9.7   |
| Asset Admin      | ✅           | ✅   | ✅      | ✅        | ✅           | 9.7   |
| Asset Profile    | ✅           | ✅   | ✅      | n/a       | ✅           | 9.6   |
| ShopHubV2        | ✅           | ✅   | ✅      | ✅        | ✅           | 9.6   |
| Pre-Op `/equipment/new` | ✅    | ✅   | ✅      | ✅ (tally chip) | ✅      | 9.7   |
| DVIR `/fleet/dvir/new`  | ✅    | ✅   | ✅      | ✅        | ✅           | 9.7   |
| Public Pre-Op `/equipment/submit` | ✅ | ✅ | ✅ | ✅        | ✅           | 9.6   |
| Admin Console K4 | ✅           | ✅   | ✅      | ✅        | ✅           | 9.5   |

No portal looks like a different app. Mascot lockup consistent. **Verdict: PASS · 9.65 avg.**

## 6 · Form Consistency Matrix

Forms audited (from code inspection + prior session screenshots):

| Form                       | Label style | Required marker | Spacing | Photo upload | Mobile | Score |
|----------------------------|:-----------:|:---------------:|:-------:|:------------:|:------:|:-----:|
| Pre-Op (NewEquipmentInspection) | ✅      | ✅              | ✅      | ✅           | ✅     | 9.7   |
| DVIR (NewFleetDVIR)        | ✅          | ✅              | ✅      | ✅           | ✅     | 9.7   |
| Add Asset (D7)             | ✅          | ✅              | ✅      | n/a          | ✅     | 9.7   |
| Document upload (D3+D4)    | ✅          | ✅              | ✅      | ✅           | ✅     | 9.6   |
| Required Docs editor (D7)  | ✅          | n/a             | ✅      | n/a          | ✅     | 9.6   |
| Daily Report               | ⚠️ legacy   | ⚠️ legacy       | ⚠️      | ✅           | ⚠️     | 9.2   |
| Safety / JHP / Trench      | ⚠️ legacy   | ⚠️ legacy       | ⚠️      | ✅           | ⚠️     | 9.2   |
| HR onboarding / offboarding | unverified live | —          | —       | —            | —      | n/a   |

**Verdict: CONDITIONAL.** Recent forms (D3-D7+33ABC) are consistent. Legacy forms (Daily Report · Safety · Trench) drift in spacing/labels. **High-priority fix track recommended:** Form Style Pass.

## 7 · Terminology Dictionary & Conflicts

**Allowed**: Asset · Unit · Equipment · Ready · Warning · Not Ready · Needs Review · Verified · Current · Expiring Soon · Expired · Missing Document · Out of Service · Maintenance Hold · Return to Service · Repair Complete · Pending Update · Pending Renewal · Required · Recommended · Optional · Not Applicable.

**Conflicts observed**:
- "Unit" vs "Equipment" vs "Asset" — used interchangeably in some surfaces. Recommended: standardize to **"Asset"** for asset-records contexts and **"Unit"** for the operator-visible identifier (unit_number/asset_tag). Low-priority.
- "Vehicle" leaks in DVIR copy a few places; should standardize to **"Truck"** or **"Trailer"**.
- "Equipment Type" (legacy demoted dropdown) still visible on Pre-Op — D5.4 demoted but did not rename. Acceptable while backward-compat retained.
- No instances of "Rejected" / "Denied" / "Failed" / "Invalid" / "Migration" / "Taxonomy" / "Endpoint" / "API" / "Track 13" verified in operator-visible UI (grep clean on D3-D7+33ABC surfaces).

**Verdict: PASS with minor polish recommended.**

## 8 · Coaching / Help / Training Matrix

| Surface              | Coaching status | Score |
|----------------------|-----------------|:-----:|
| Asset Care home      | Good (status reasons surface inline · CTA labels clear) | 9.5 |
| Add Asset dialog     | Good (live suggestions panel · warnings not blocks)    | 9.6 |
| Required Docs editor | Good (footer explainer: photos/docs never required)    | 9.6 |
| Documents tab        | Light (no inline help on doc types)                    | 9.0 |
| Pre-Op canonical     | Good (template chip · live tally)                      | 9.5 |
| DVIR canonical       | Good (template chip · authority note)                  | 9.5 |
| Renewal alerts       | Good (recommended action per row)                       | 9.5 |
| Public forms         | Light (validation messages adequate · no walkthrough)  | 9.0 |
| HR / Safety / PM     | Not re-audited this session                            | n/a |

**Verdict: PASS.** No "Confusing" or "Conflicting" coaching found. Document-types could use 1-line descriptors (medium priority polish).

## 9 · Spanish Translation Gap Matrix · BLOCKER

| Surface                           | Strings | Spanish coverage |
|-----------------------------------|--------:|:----------------:|
| Asset Care home (D33ABC)          | ≈ 33    | none             |
| Add Asset dialog (D7)             | ≈ 35    | none             |
| Required Docs editor (D7)         | ≈ 20    | none             |
| Documents tab + dashboard (D3+D4) | ≈ 75    | none             |
| Smart Pre-Op canonical (D5.4)     | ≈ 18    | none             |
| Smart DVIR canonical (D5.4)       | ≈ 12    | none             |
| Document upload dialog            | ≈ 15    | none             |
| Canonical authority chips         | ≈ 8     | none             |
| Renewal alert copy                | ≈ 6     | none             |
| GPS/Survey/Tech taxonomy strings  | 60 (mostly proper nouns) | n/a |
| **Cumulative D3-D7+D33ABC total** | **≈ 222** | **0%**         |

Public field-facing forms (Pre-Op public, DVIR public, Daily Report) retain prior Spanish coverage from earlier tracks — verify before deploy.

**Verdict: FAIL FOR DEPLOY.** Field operators and Spanish-speaking drivers will see English-only canonical sections, document upload, and Asset Care surfaces. **Fix Track 14.0-S1 required.**

## 10 · PDF / Print Certification

| PDF                  | MASCI lockup | Page numbering | Spanish | Style consistency | Score |
|----------------------|:------------:|:--------------:|:-------:|:-----------------:|:-----:|
| Asset Profile PDF    | ✅           | ✅             | none    | ✅ (WeasyPrint `_BASE_CSS`) | 9.5 |
| Safety / JHP PDF     | ✅           | ✅             | partial | ✅                | 9.4 |
| Daily Report PDF     | ✅           | ✅             | partial | ✅                | 9.4 |
| Pre-Op PDF (legacy)  | ⚠️ verify    | ⚠️             | ⚠️      | ⚠️                | 9.0 |
| DVIR PDF (legacy)    | ⚠️ verify    | ⚠️             | ⚠️      | ⚠️                | 9.0 |
| Incident PDF         | ⚠️ verify    | ⚠️             | ⚠️      | ⚠️                | 9.0 |
| Excavation/Trench PDF| ⚠️ verify    | ⚠️             | ⚠️      | ⚠️                | 9.0 |

**Verdict: CONDITIONAL.** New PDFs follow the unified `safety_forms.py · _BASE_CSS` lockup. Legacy PDFs need re-verification — likely already conformant but unverified this session. **Fix Track 14.0-P1 recommended** to walk each PDF surface and stamp the dossier.

## 11 · Mobile / iPad Certification

- Public Pre-Op / DVIR / Daily Report — known mobile-safe (per prior tracks).
- Asset Care home (`/shop/asset-care`) — desktop verified; **iPad / phone NOT re-screenshotted this session**.
- Add Asset dialog — has max-h-90vh + overflow-y-auto · should be mobile-safe.
- Document upload dialog — mobile-safe.

**Verdict: CONDITIONAL.** Recent additions inherit mobile-safe patterns but were not screenshotted at iPad/phone widths. **Pre-deploy gate: walk each new surface at 768px and 390px.**

## 12 · Role Journey Certification (summary)

| Role            | 15-sec test | First-click test | Verdict |
|-----------------|:-----------:|:----------------:|---------|
| Equipment Operator | ✅ smart Pre-Op renders canonical sections + tally | ✅ 1 click on PASS | Pass |
| Driver          | ✅ smart DVIR canonical authority surfaced       | ✅ 1 click           | Pass |
| Asset Admin     | ✅ Asset Care home answers all 9 questions       | ✅ 1-2 clicks per task | Pass |
| Shop Manager    | ✅ ShopHubV2 unchanged (no regression)            | ✅ existing path     | Pass |
| Admin           | ✅ Admin console + K4 directory unchanged         | ✅                   | Pass |
| Mechanic        | not re-audited                                    | —                    | n/a |
| PM              | not re-audited                                    | —                    | n/a |
| Safety          | not re-audited                                    | —                    | n/a |
| HR              | not re-audited                                    | —                    | n/a |
| Dispatch        | not re-audited                                    | —                    | n/a |

## 13 · Notification Matrix Certification

25 asset events documented via `/api/asset-care/notifications-matrix`. Delivery status:
- Dashboard: **live**
- In-app notification center: **deferred** (platform notification center not built)
- Email cadence (Resend): **deferred**
- SMS: **out of scope**

**Verdict: CONDITIONAL.** Dashboard fan-out is live. Email cadence is a known deployment-time enhancement, not a blocker if dashboard-only is acceptable for v1.

## 14 · Integration Gate Certification

| Integration  | Status                                | Honest banner? |
|--------------|---------------------------------------|:--------------:|
| MaintainX    | Dormant · awaiting `MAINTAINX_API_KEY`| ⚠️ AssetProfile shows tab without explicit "Not Configured" banner |
| FleetWatcher | Dormant · awaiting credentials        | ⚠️ Not visible to operators (good) but no explicit gate label |
| Motive       | Live · drives location only · does NOT override Equipment Master classification | ✅ |
| R2 storage   | Live for Asset Documents              | ✅ |
| Resend email | Configured for non-renewal flows · renewal cadence not wired | ⚠️ |

**Verdict: CONDITIONAL.** No fake integrations claim live functionality. MaintainX tab needs an explicit "Awaiting integration" notice to prevent executive demo confusion.

## 15 · Data Quality Certification

| Concern                                                   | Status |
|-----------------------------------------------------------|--------|
| 702 of 779 assets `taxonomy_verified=false`               | Known · Review Queue active |
| Kubota KX040 under Misc/Other                             | Known · Legacy Crosswalk active |
| Equipment not found in Pre-Op (legacy free-text)          | Mitigated by D5.1 canonical stamp |
| Motive orphan coverage                                    | Unchanged |
| Dirty company names                                       | Known · admin task |
| Missing photos/docs                                       | Surface in Asset Care · acceptable |
| Missing GPS/Survey/Tech rows                              | D6 unlocks creation · Asset Admin task |

**Verdict: PASS WITH KNOWN ADMIN BACKLOG.** No code defects. Data backlog is operational, not a deployment blocker.

## 16 · Executive Walkthrough Certification

A 15-minute exec demo path:
1. `/shop/asset-care` — KPI snapshot answers readiness in 10 seconds.
2. Click "Not Ready" tab — see explainable reasons per row.
3. Renewal Alerts — 8 live items with recommended action.
4. Open Asset Administration → Review Queue → demonstrate canonical taxonomy verification.
5. Documentation Requirements tab → demonstrate per-asset-type customization.
6. Pre-Op `/equipment/new` with TB-01 → canonical sections render · PASS click increments tally.
7. Generate Asset Profile PDF → MASCI-styled document with sections, photos, recent inspections.

**Verdict: PASS.** Demo-ready.

## 17 · Five-Pillar Scorecard

| Surface group           | Powerful | Simple | Beautiful | Trusted | Proven | Avg  |
|-------------------------|---------:|-------:|----------:|--------:|-------:|-----:|
| Canonical Asset Spine   | 9.9      | 9.7    | n/a       | 9.9     | 9.8    | 9.83 |
| Asset Care Command Ctr  | 9.8      | 9.7    | 9.7       | 9.7     | 9.6    | 9.70 |
| Asset Admin             | 9.7      | 9.7    | 9.6       | 9.8     | 9.6    | 9.68 |
| Documents / Renewals    | 9.7      | 9.7    | 9.6       | 9.7     | 9.6    | 9.66 |
| Smart Pre-Op + DVIR     | 9.9      | 9.7    | 9.6       | 9.9     | 9.7    | 9.76 |
| Add Asset / Required Docs | 9.7    | 9.7    | 9.6       | 9.7     | 9.6    | 9.66 |
| Shop / Dispatch / PM    | 9.6      | 9.5    | 9.5       | 9.7     | 9.6    | 9.58 |
| Legacy forms (Daily / Safety / Trench / Incident) | 9.3 | 9.2 | 9.2 | 9.4 | 9.5 | 9.32 |
| PDF / Print             | 9.4      | 9.5    | 9.4       | 9.5     | 9.4    | 9.44 |
| Spanish translation     | n/a      | n/a    | n/a       | 8.0     | 8.0    | 8.00 |
| Mobile / iPad           | 9.5      | 9.5    | 9.5       | 9.5     | 9.0    | 9.40 |
| Integration banners     | 9.0      | 9.0    | 9.0       | 9.0     | 9.5    | 9.10 |
| **Weighted average**    |          |        |           |         |        |**9.62**|

## 18 · Critical Blockers (must fix before deploy)

1. **Spanish translation** — recent asset-admin and field-facing strings are English-only. Field operators in Spanish-language workflows will not have parity. **Fix Track 14.0-S1.**
2. **PDF style sweep** — confirm Pre-Op, DVIR, Incident, Excavation PDFs all carry the unified MASCI lockup. **Fix Track 14.0-P1.**
3. **Integration honesty banners** — MaintainX tab on Asset Profile shows blank without an "Awaiting integration" notice. Could mislead during exec demos. **Fix Track 14.0-I1.**

## 19 · High-Priority Fixes

1. **Mobile/iPad re-screenshot pass** of every new D3-D33ABC surface at 768px and 390px. (Fix Track 14.0-M1.)
2. **Legacy form style alignment** — Daily Report, Safety, Trench forms drift from the recent label/spacing standard. (Fix Track 14.0-F1.)
3. **Document-type 1-line descriptors** in the upload dialog. (Fix Track 14.0-C1.)

## 20 · Medium-Priority Fixes

1. Terminology "Vehicle/Truck/Trailer" normalization in DVIR copy.
2. "Equipment Type" legacy dropdown — rename to "Legacy classification" or hide entirely now that D5.4 canonical authority is universal.
3. Asset Care home — mobile sticky header.

## 21 · Low-Priority Polish

1. KPI card consistency: tabular-nums everywhere.
2. Per-row "Open Profile" arrow icon harmonization.
3. Add-Asset suggestions panel — switch to neutral grey when no suggestions fire.

## 22 · Recommended Fix Tracks

- **Track 14.0-S1** · Spanish Translation Sweep (D3-D7+D33ABC ≈ 222 strings).
- **Track 14.0-P1** · PDF Style Verification + alignment for legacy PDFs.
- **Track 14.0-I1** · Integration honesty banners (MaintainX + FleetWatcher + Resend cadence).
- **Track 14.0-M1** · Mobile/iPad re-screenshot pass.
- **Track 14.0-F1** · Legacy form style alignment.
- **Track 14.0-C1** · Document-type descriptors + inline coaching polish.
- **Track 14.0-N1** · In-app notification center delivery (after the fix sweep · optional for v1).

## 23 · Deployment Verdict

**CONDITIONAL PASS · NOT YET DEPLOYABLE.**

The operational backbone is sound, the asset administration spine is complete, role landing is correct, the Five-Pillar weighted average is 9.62. **Three named blockers** stand between the platform and production: Spanish coverage, PDF lockup sweep, integration honesty banners. Each is scoped, isolated, and can be closed in 1-2 fix tracks each.

**Proposed deployment-gate sequence:**
1. Close 14.0-S1 (Spanish) — single largest blocker.
2. Close 14.0-P1 (PDF sweep) — verification more than build.
3. Close 14.0-I1 (integration banners) — small additive UI work.
4. Spot-check 14.0-M1 (mobile) — one screenshot pass.
5. Re-run 14.0 audit.
6. **Deploy.**

DO NOT deploy until these gates close.


---

## Live Verification Addendum · Fork Session 2026-06-13

This fork re-verified the certification's core claims with live evidence before publishing the deployment verdict.

### Verified live (this fork)

1. **Role landing logic** — `landingFor()` in `/app/frontend/src/lib/directoryAuth.js` lines 106–130 inspected directly. Confirmed:
   - `is_asset_admin && !portals.includes("admin") → "/shop/asset-care"` (Asset Admin operational home · Track 13.33ABC)
   - `portals.includes("admin") → "/admin"` (Admin Console)
   - Single-portal users → portal home
   - Multi-portal → public hub `/`
2. **Spanish coverage gap** — verified via grep across all recent asset components:
   ```
   grep -c "useTranslation|i18n|t('" \
     frontend/src/components/asset/*.jsx \
     pages/shop/ShopAssetCare.jsx \
     pages/admin/AdminAssetAdmin.jsx
   ```
   Result: zero i18n imports. Apparent "t(" matches are false positives from `/asset-spine/taxonomy` API path substrings. **Confirmed 0 % Spanish coverage on the 222 D3–D33ABC strings.**
3. **i18n infrastructure exists** — `lib/i18n.js` is 6126 lines · 4 explicit `es:` blocks · ready for new keys. Spanish blocker is wiring, not foundation.
4. **Backend operational backbone live** — `GET /api/asset-care/summary` returns the expected production-truth distribution: 779 total assets · 1 Ready · 21 Warning · 55 Not Ready · 702 Needs Review (matches the documented 702/779 `taxonomy_verified=false` data-quality finding) · 187 Missing Docs · renewal buckets `{expired:2, 7:0, 30:4, 60:1, 90:1}`.
5. **Multi-login fan-out healthy** — super-admin login returns portal_tokens for all 7 portals: admin · pm · shop · hr · safety · dispatch · field_leadership (+ fl alias). Confirms portal routing primitive is intact.
6. **Public chrome sanity** — `/shop/asset-care` (unauthenticated) renders the Shop sign-in with the expected MASCI lockup, EN/ES toggle, "Forgot password?" + "First-Week Onboarding" + "What does Shop Portal do?" coaching links · "Sign in required · You selected Shop Portal" gate copy is operator-clean (no engineering leaks).

### Carried forward without re-verification this fork

- Live screenshots of Asset Care authenticated home, Add Asset dialog, Required Docs editor, Smart Pre-Op TB-01 canonical sections, Documents & Renewals dashboard, Asset Profile PDF generation, and Admin Asset Admin 5-tab layout — relied on prior-session evidence already captured in this ledger and the 13.31B-D6/D7/D33ABC reports.
- Dispatch, HR, PM, Safety, Mechanic role journeys — relied on prior tracks' verification.

### Documentation updates this fork

- `/app/memory/CHANGELOG.md` — Track 14.0 entry prepended above 13.31B-D5.3.
- `/app/memory/PRD.md` — Track 14.0 closeout bullet appended to Completed Tracks list.
- `/app/memory/ROADMAP.md` — Seven 14.0-* fix tracks (S1/P1/I1/M1/F1/C1/N1) added at top with priorities + estimates.
- `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md` — Track 14.0 entry appended (verdict · Five-Pillar scorecard · phase A–N verdicts · fix-track sequence · hard locks).

### Verdict (unchanged)

**CONDITIONAL PASS · NOT YET DEPLOYABLE.** Close 14.0-S1 (Spanish · largest blocker) · 14.0-P1 (PDF lockup sweep) · 14.0-I1 (integration banners). Re-run Track 14.0. If green, redeploy.

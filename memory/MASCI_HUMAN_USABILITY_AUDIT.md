# MASCI Human Usability Audit (Track 13.4E)

**Mode:** discovery only via role simulation · NO redesign · NO standardisation.  
**Generated:** 2026-02 (Track 13.4E).  
**Evidence basis:** Phase 1 + 13.4E screenshots, Phase 2B workflow inventory, source review, DB queries.

Per-role result legend: **Easy · Confusing · Hidden · Missing · Excellent · Needs Rebuild · Needs Standardisation.**

---

## 1. PM (Project Manager)

Logged in as `pm.demo@mascigc.com` (Track 13.4A fixture, scoped to `20-07` + `21-06`).

| Task | Result | Evidence |
|---|---|---|
| Find Daily Reports for a scoped project | Easy | PM Command Center "Section B — Field Truth · recent dailies" with project filter |
| Find Photos | Easy | "Section B" — recent photos row; also Project tile → photo library |
| Find Incidents | Easy | "Section C — Project Risk · open safety items" (0 in preview) |
| Find CAPAs | Confusing | CAPAs live under Safety incident detail; PM has no direct CAPA list — must dive in per incident |
| Find Project Health | Excellent | Project rows show "MISSING DAILY REPORT" alerts immediately |
| Find Project Roster | Easy | Project tile → roster sub-page |
| Submit a Constraint | Easy | tile in Section E |
| Find PO requests | Easy | Section E tile |
| Find QA/QC | Easy | Section D tile |

**Per-role verdict:** Easy with two specific gaps — CAPAs (no PM-scoped list) and operator-side acknowledgement of PM scope (the 2-project list is clear; need to ensure operators do not assume admin scope by mistake — addressed by Track 13.4A fixture proof).

---

## 2. Dispatcher

Logged in as `dispatch@mascigc.com`.

| Task | Result | Evidence |
|---|---|---|
| Find Fleet | Excellent (post-13.4A) | DispatchMapHero renders 90 GPS-mapped assets across 5 cluster groups |
| Find Equipment | Easy | Top-nav → Equipment list, drill into unit detail |
| Find Assignments | Easy | Operations Board CTA from hero |
| Find Transfers | Easy | `/asset-transfers` linked from Equipment tile |
| Identify stale units | Easy | "Attention Required" tile shows 33; "No Recent Position" shows 157 |
| Open Live Map full-screen | Easy | "Open Full Live Map" CTA |
| Driver session lookup | Confusing | Driver-side lacks a static landing (V-15) — dispatcher must use tokenized URL flow |

**Per-role verdict:** Excellent for fleet visibility. One gap — Driver portal landing (R-13 / V-15). One reliability gap — preview env's stale feed is *correctly labelled* but cannot prove production feed will be live.

---

## 3. Safety

Login surface only audited (Safety credentials rotated; full role audit deferred). Per Phase 1 §B Safety hub is reachable via `/safety-portal/login`.

| Task | Result (from source review) |
|---|---|
| Find Incidents | Easy — `SafetyHub` has Incidents tile |
| Find Training | Easy — `SafetyTrainingRecords` page + Safety Forms gate |
| Find Certifications | Easy — `ExpirationsSummary` + training records |
| Manage CAPAs | Easy — from Incident detail |
| Trench Safety | Excellent — Trench Safety module is exemplary (Preserve-List #1) |
| Fire extinguishers | Easy — `SafetyFireExtinguishers` page |
| Equipment Issuance | Easy — `/safety/forms/equipment-issuances/new` |
| Equipment Training | Easy — `/safety/forms/equipment-trainings/new` |

**Per-role verdict:** Strong. Trench module is the exemplar. **Confusing in one place:** Safety Forms gate uses shared password `1982`, not portal auth — operationally lighter friction, white-label headache.

---

## 4. HR

Logged in as `hrmanager@mascigc.com`.

| Task | Result | Evidence |
|---|---|---|
| Find Employee Records | Easy | HrKpiStrip + People Operations tile group |
| Find Time Verification | Easy | Time & Payroll tile group |
| Find Expirations | Excellent | `ExpirationsSummary` is a HR-native intelligence card |
| Find Training Records | Easy | Compliance & Records tile group |
| Find Payroll Variance | Easy | Time & Payroll tile group |
| Driver Safety Events | Easy (post-13.4A) | single full-width "Driver Safety Events (HR Review)" card |
| Find DQ (driver qualification) | Easy | Compliance & Records tile |
| Find Daily Reports for payroll cross-check | Easy | dedicated tile "Daily Reports Review · Read-only payroll cross-check context" |

**Per-role verdict:** Excellent post-13.4A cleanup. Cleanest operator portal today.

---

## 5. Shop

Logged in as `testmech@mascigc.com`.

| Task | Result | Evidence |
|---|---|---|
| Find Repairs | Easy | Shop Hub repair tile |
| Find Holds | Easy | Asset holds list |
| Find Recovery Work | Easy | shop_parts + shop_command_feed routes; recovery tile in hub |
| Find Equipment Defects | Easy | "Recent equipment defects" feed |
| Equipment Pre-Op fail alerts | Easy | auto-emails to `shopmanager@mascigc.com` (W-08) |
| MaintainX integration view | Easy | Integration tile (Maintainx work orders) |

**Per-role verdict:** Easy. Shop hub is functionally complete; visual drift (V-01 amber-vs-orange) is the only friction noted.

---

## 6. Admin

Logged in as super-admin `jaymn.judd@mascigc.com`.

| Task | Result | Evidence |
|---|---|---|
| Find audit log | Easy | `AdminAuditLog` |
| Find governance | Easy | `AdminGovernance` |
| Find people directory | Easy | `AdminPeople` |
| Find jobs / projects | Easy | `AdminJobs`, `AdminProjectIdentityGovernance` |
| Find equipment master | Easy | `AdminEquipment`, `AdminAssetMapping` |
| Find compliance findings | Confusing | two pages (`AdminCompliance`, `AdminComplianceFindings`) — R-05 |
| Find platform health | Confusing | 4 admin health pages (`Persistence`, `Production`, `Stability`, `Cluster Capacity`) — R-04 |
| Onboard new tenant | Missing | no surface exists (W-12) |
| Edit email template | Missing | Python-coded (W-20) |
| Edit notification recipients | Confusing | env-var override only, no UI |

**Per-role verdict:** Powerful but confusing in places. Needs **Rebuild** on the compliance/health navigation arch and **Missing** surface for tenant onboarding (ForgedOps roadmap).

---

## 7. Field Leadership

Login surface only (FL credentials deactivated 2026-05-31 in preview; full per-role flow not exercised in this audit).

Per Phase 1 + source review:

| Task | Result (source review) |
|---|---|
| Submit write-up | Easy — `/leadership/write_up/new` |
| Submit verbal coaching | Easy — `/leadership/verbal_coaching/new` |
| Submit attendance | Easy — `/leadership/attendance/new` |
| Submit recognition | Easy — `/leadership/recognition/new` |
| Submit equipment checkout | Easy — `/leadership/equipment_checkout/new` |
| Crew evaluation | Easy — `/leadership/crew_eval/new` |
| Promotion recommendation | Easy — `/leadership/promotion_recommendation/new` |
| Training deficiency | Easy — `/leadership/training_deficiency/new` |
| Supervisor notes | Easy — `/leadership/supervisor_notes/new` |
| New employee eval | Easy — `/leadership/new_employee_eval/new` |
| Find own historical records | Easy — `field_leadership_records` collection backs the FL hub |

**Per-role verdict:** 10 record kinds well-defined; in source review, the chrome shares the FL identity. **Hidden** for Spanish-first FL: the records are English-only PDFs (T-09).

---

## 8. Driver

| Task | Result |
|---|---|
| See "what's my assignment today?" | **Missing** — no static landing page in `pages/`; only tokenized URLs (V-15 / R-13) |
| Pre-trip inspection (DVIR) | Easy — `/equipment/new` public form |
| Sign daily report | Easy — `/daily/new` public form |
| See own qualifications | Hidden — driver_qualification surface lives in HR/Admin |

**Per-role verdict:** **Needs Rebuild** — Driver landing surface is the single biggest role gap on the platform.

---

## 9. Cross-role usability themes

| Theme | Observation | Status |
|---|---|---|
| Can they find what they need? | mostly yes; CAPAs (PM), platform health (Admin), compliance (Admin), driver landing (Driver) are the exceptions | partial |
| Can they understand what they see? | yes for English readers; **Spanish operators lose safety-critical strings 24.2 % of the time** (T-01) | partial |
| Can they complete common workflows? | yes — workflow surfaces exist for every named task | yes |
| Can they trust what they see? | preview env feed_status correctly says "offline"; in production this remains **unverified** (D-01) | unproven |
| Can they complete work without training? | mostly yes — operator-native verbiage is strong in tile labels | yes |
| Can they complete work without hunting? | mostly yes; Admin compliance + Admin health + Driver landing are exceptions | partial |
| Can they complete work without developer knowledge? | yes — no operator surface forces a developer concept | yes |

---

## 10. Standardisation candidates (from this role audit)

- **Empty-state copy** — each role's "no records yet" cards use different wording.
- **Status chip & verb language** — already in Track 13.4C Standardisation List (S-1 / S-3).
- **Header chrome** — already in S-9.
- **Auth flow** — already in S-10.

No new standardisation candidates emerged that weren't already in `MASCI_PLATFORM_STANDARDIZATION_LIST.md`.

---

## 11. Rebuild candidates (from this role audit)

- **Driver portal landing** — confirmed missing.
- **Admin compliance + health pages** — confirmed duplication.
- **CAPAs surfaced to PM** — currently routed through Safety only; PM would benefit from a CAPA-by-project list.

The first two are already on Track 13.4C's Rebuild List (R-07 Driver Portal, R-03 Navigation Architecture). The third (PM CAPAs) is **new** and is added by this audit.

---

## 12. What this audit did NOT do

- Did not redesign anything.
- Did not run all 10 FL form types end-to-end.
- Did not actually walk a Safety user through every workflow (Safety creds rotated; spot-checked from source).
- Did not measure time-to-complete for any task.
- Did not test Spanish-language path for every role.
- Did not capture mobile screenshots for Safety / Leadership / Field-Leadership / Driver (only Admin · Dispatch · PM · Shop · HR were re-captured in this track).

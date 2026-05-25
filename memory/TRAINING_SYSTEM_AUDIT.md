# TRAINING_SYSTEM_AUDIT.md
**Phase 19 · iter415 · 2026-05-25**

## Scope
The MASCI platform does NOT use a discrete LMS. Training is delivered through:
1. **Operational Guidance Center** (`/guidance` · 137 articles · RBAC-aware · EN+ES)
2. **In-flow LifecycleGuide explainers** (14 mountpoints · component pattern)
3. **In-flow coaching strips** on Phase 12-18 surfaces
4. **Safety Training Records** (`db.safety_training_records`) — compliance-tracking, not pedagogy
5. **Driver Qualification Dashboard** (HR canonical · Dispatch consumer) — operational readiness signal
6. **iter347 Promo Asset Library** — visual training assets

There is NO modal walkthrough · NO onboarding wizard · NO "Step 1 of 7" tutorial chrome. Training is in-flow, calm, doctrine-aligned.

## Coverage by role
| Role | Onboarding article | Quickhelp articles | Portal guide | Troubleshooting | DLS coverage |
|---|:---:|:---:|:---:|:---:|:---:|
| Admin | ✅ `onboard-admin-first-week` | ✅ multiple | ✅ `portal-admin` | ✅ | ✅ via iter414 |
| Dispatch | ✅ `onboard-dispatch-first-week` | ✅ multiple | ✅ `portal-dispatch` + `portal-dispatch-identity` | ✅ `tshoot-dispatch-login` | ✅ 7 iter414 DLS articles |
| PM | ✅ `onboard-pm-first-week` | ✅ multiple | ✅ `portal-pm` | ✅ | ✅ `dls-haul-activity-tile` |
| Shop | ✅ `onboard-shop-first-week` | ✅ multiple | ✅ `portal-shop` | ✅ | ✅ via iter396 BREAKDOWN |
| Safety | ✅ `onboard-safety-first-week` | ✅ multiple | ✅ `portal-safety` | ✅ | ✅ (restrained · doctrine-quiet on DLS) |
| HR | ✅ `onboard-hr-first-week` | ✅ multiple | ✅ `portal-hr` | ✅ | ✅ via driver qualification |
| Field Leadership | ✅ `onboard-leadership-first-week` | ✅ multiple | ✅ `portal-leadership` + `portal-leadership-identity` | ✅ `tshoot-leadership-login` | ✅ via iter319+iter396 |
| Driver (public) | ✅ `dls-driver-shift-start` (iter414) | ✅ `public-mobile-qr` · `public-tools-map` | n/a | n/a | ✅ |

**Coverage verdict**: every role has onboarding + portal guide + quickhelp + (where relevant) troubleshooting + DLS coverage. 100%.

## Training continuity verification
| Doctrine requirement | Status | Evidence |
|---|:---:|---|
| Training matches CURRENT systems | ✅ | iter414 articles include Phase 14-17 surfaces · no outdated workflows referenced in DLS articles |
| Training matches CURRENT doctrine | ✅ | Operator vocabulary scanner 0 T2/T3 across articles |
| No outdated screenshots | n/a | Platform's training is text-based; no screenshots maintained |
| No outdated wording | ✅ | iter398 vocabulary scanner is permanent guardrail; iter317-onwards purges |
| No disconnected guides | ✅ | Every article has `related: [...]` linking to siblings |
| No missing lifecycle explanations | ✅ | iter414 `dls-lifecycle-states` ships full state machine guide |
| Bilingual support | 🟡 | 126/137 (91%) translated · 11 short articles untranslated (P3) |
| Operational examples present | ✅ | Bullets + Steps blocks throughout |
| No conflicting training | ✅ | Verified by manual review of related-article clusters |
| No duplicate guidance | ✅ | Article slugs are unique · `validate_registry(strict=True)` PASS |
| No software training language | ✅ | 0 T2/T3 vocabulary flags |
| No ERP-style onboarding | ✅ | No "Step 1 of N" chrome anywhere |

## ES translation gaps (the 11 untranslated articles)
| Article ID | Section | Size | Why deferrable |
|---|---|---|---|
| `role-safety` · `role-shop` · `role-dispatch` · `role-pm` · `role-admin` | roles | small stubs | Short stub articles · operational meaning still EN-visible · low driver/field exposure |
| `task-submit-incident` · `task-upload-photos` · `task-verify-time` | quickhelp | quickhelp · concise | High-frequency tasks · should be translated · **P2** |
| `tshoot-photo-upload` · `tshoot-employee-not-found` · `tshoot-equipment-not-found` | troubleshooting | terse | Edge-path · low frequency · P3 |

**P2 candidate**: translate the 3 `task-*` articles (incident submission · photo upload · time verification) — these are high-frequency Spanish-preferring field actions.

## Training surfaces — operational vs software language audit
| Surface | Tone check |
|---|---|
| All 7 iter414 DLS articles | ✅ operational ("Drivers update movement through lifecycle taps") |
| iter317 driver qualification guides | ✅ operational ("CDL means legally-cleared; Approved means dispatched-by-MASCI") |
| iter319 Field-Tile coaching | ✅ operational ("Daily Report is end-of-day operational memory") |
| iter306-307 banner doctrine | ✅ operational (cultural restraint) |
| iter347 promo assets | ✅ operational (no LMS chrome) |
| Pre-Phase-12 form coaching (where present) | 🟡 mostly form-instructional ("Fill in all required fields") — not software-jargon, but pre-LifecycleGuide tone |

## In-flow LifecycleGuide mountpoints (14 verified)
- `components/LifecycleGuide.jsx` (the component itself)
- `pages/HrIncidents.jsx`
- `pages/HrEmployeeAccountabilityTimeline.jsx`
- `pages/NotificationsDigest.jsx`
- `pages/DispatchBoard.jsx`
- `pages/admin/AdminDlsShiftQR.jsx`
- `pages/admin/AdminComplianceFindings.jsx`
- `pages/admin/AdminOperationalLanguage.jsx`
- `components/DriverQualificationReadOnlyView.jsx`
- ... + 5 more across PM/Shop/Safety hubs

## Recommendations (NOT executed in Phase 19)
- 🟠 **P2** — Translate 3 high-frequency `task-*` quickhelp articles to ES
- 🟠 **P2** — Add LifecycleGuide-pattern explainer to Daily Report · Inspections · Incidents (would benefit FL training)
- 🔵 **P3** — Translate 5 `role-*` stub articles to ES
- 🔵 **P3** — Translate 3 `tshoot-*` edge-path articles to ES
- 🔵 **P3** — Close 9 `role-*` articles missing "what next" closing block

## Verdict
**Training coverage is operationally complete and doctrine-aligned.** 91% ES coverage is the most surface for surgical improvement. The platform teaches through operational flow — not through software lectures — as doctrine requires.

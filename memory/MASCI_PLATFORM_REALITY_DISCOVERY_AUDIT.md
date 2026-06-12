# MASCI Platform — Reality Discovery Audit (Track 13.4B · Phase 2B)

**Mode:** Discovery only. No scoring. No recommendations. No fixes.  
**Generated:** 2026-02 (Track 13.4B Phase 2B)  
**Evidence basis:** Live source + DB + Phase 1 inventory + Track 13.4A reports.

---

## A. Forms — observed reality

Forms surfaced in Phase 1 §F: ~30 distinct named forms.

| Form | Path | Complexity (rough) | Mobile? | Field-suitability notes | Data duplication observed |
|---|---|---|---|---|---|
| Daily Report (`/daily/new`) | public | high (≥ 12 fields incl. photo array, crew roster, sign block) | yes (rebuilt in iter261) | designed for tablet | overlap with Site Inspection photo & crew fields |
| Site Inspection (`/inspect/new`) | public | high | yes | designed for tablet | overlap with Incident photo & narrative fields |
| Safety Meeting (`/meetings/new`) | public | medium | yes | tablet/laptop | crew roster duplicates Daily Report roster |
| Incident (`/incidents/new`) | public | high (multi-step) | partial | partial — photo upload was rebuilt iter274 | overlap with Site Inspection narrative |
| Equipment Inspection (Pre-Op DVIR) (`/equipment/new`) | public | high (component-wise checklist + photos) | yes | designed for cab/field | overlap with Shop work-order narrative |
| JHA (`/jha/new`) | public | high (hazard tree, controls, sign-off block) | partial | tablet primarily |  |
| Operational Constraint (`/constraints/new`) | public | low/medium | yes | quick-entry |  |
| ODR (`/odr/new`) | public | high (Sections A–G) | tablet | designed for tablet |  |
| Operations Action (`/operations-actions/new`) | login | medium | yes |  |  |
| Safety Forms · Equipment Issuance | gate | medium | tablet | equipment + employee + sign block |  |
| Safety Forms · Equipment Training | gate | medium | tablet | training topics + sign block | shares structure with Issuance |
| Field Leadership · 10 record kinds | gate | varies — `write_up`, `verbal_coaching`, `attendance`, `recognition`, `equipment_checkout`, `new_employee_eval`, `crew_eval`, `promotion_recommendation`, `training_deficiency`, `supervisor_notes` | yes | designed for FL on tablet |  |
| Per-portal forgot / reset / change-password | yes (×7 portals) | low | yes |  | 7 visually distinct identical-purpose flows |
| Time Off request | gate | low | yes |  |  |
| PO Request | gate | medium | yes |  |  |
| Trench Safety public Excavation Form | public | medium | yes |  |  |
| Trench Safety public Report Modal | public | low | yes |  |  |
| Multi-Portal Master Sign-In | public | low | yes |  | overlaps with each per-portal `/login` |
| Constraints / Dialogs (sub-form, in-page) | embedded | various |  |  |  |

**Workflow-fit findings (discovery only):**
- 7 separate `/login`, `/forgot-password`, `/reset/:t`, `/change-password` flows + master `/sign-in` = 7 + 1 = **8 auth-flow variations** that all do the same thing.
- Daily Report ↔ Site Inspection ↔ Incident: photo array + crew + narrative fields **overlap substantially**.
- Equipment Issuance ↔ Equipment Training (Safety Forms): same skeleton, different domain.

---

## B. Workflows — observed reality

Phase 1 §E listed ~25 named workflows. Each has been spot-checked for an Owner, Inputs, Outputs, Status engine, and observable Real-world use.

| Workflow | Owner | Inputs | Outputs | Statuses | Real-world use observed |
|---|---|---|---|---|---|
| Daily Report | Field / FL | crew, hours, narrative, photos | DR row + PDF + auto-email | submitted → reviewed → revised | active (preview DB has 45 reports) |
| Safety Meeting | Safety | topic, attendees, sign block | Meeting record + PDF | submitted | active |
| Site Inspection | Safety | observation, photos, hazard tags | Inspection record + PDF | submitted → reviewed | active |
| Incident | Safety | narrative, photos, CAPA links | Incident + CAPAs | open → in_progress → closed | active |
| JHA | Safety / PM | hazard tree, controls, sign-off | JHA + ack tracking | active / archived | active |
| Equipment Pre-Op (DVIR) | Shop / Field | component checklist + photos | Inspection + Shop alert if fail | submitted → signed_off | active |
| QA/QC Inspection | PM / Safety | quality checklist + photos | QA/QC record | submitted → reviewed | active |
| ODR | Dispatch / FL | sections A–G, attachments | ODR + Sections events | drafted → submitted → amended → final | active |
| Dispatch Assignment | Dispatch | asset · driver · project | Assignment event | scheduled → working → idle → offline | active (`dispatch_assignments`) |
| Asset Transfer | Admin / PM | from-job → to-job + reason | Transfer + audit | requested → approved → in_transit → completed | active |
| Employee Lifecycle | HR | new-hire / change requests | Employee row | new-hire-request → pending → approved → active → terminated | active |
| Time Off | HR | dates · reason | Decision | requested → approved/denied | active |
| Payroll Variance | HR | batch upload | Decisions | uploaded → matched → flagged → decided | active |
| Document Expiration | HR / Safety | certs, licenses, renewals | Expiration card | expired → 30d → 60d → 90d → ok | active |
| PO Request | Field / HR | line items · justification | PO record + Approval | submitted → approved → receipted | active |
| CAPA | Safety | corrective action plan | CAPA record | open → in_progress → closed | active |
| Fire Extinguisher Inspection | Safety | check-points · photos | Inspection | due → inspected | active |
| Trench Safety pulse / repair | Trench / Field | hazard / repair photos | Pulse record + Repair | open → repair → closed | active |
| Operations Action (OA-1) | Cross-portal | action description · owner | Action record | open → in_progress → done → closed | active |
| Field Leadership record (10 kinds) | FL / Admin | varies per kind | Record + PDF | submitted | active |
| Training Track | All operators | track progression hits | Hits log | unstarted → in_progress → complete | active |
| Safety Equipment Issuance | Safety | equipment + employee + sign | Issuance + PDF | submitted | active |
| Safety Equipment Training | Safety | topics + sign | Training + PDF | submitted | active |
| Backup / Restore drill | Admin | scheduled | Drill log | scheduled → running → success/failed | active |
| MFA enrol / verify | Admin | TOTP factor | Enrollment | disabled → enrolling → enabled | active |
| Passkey enrol | Any portal | WebAuthn challenge | Passkey | none → registered | active |

**Closure-verb spread** (also flagged in Phase 2A §C.4):
`closed · done · signed_off · final · success · approved · receipted · resolved · complete` — no shared closure verb.

---

## C. Coaching surfaces — observed reality

| Surface | Present? | Type | Audience |
|---|---|---|---|
| Hub banners (cross-portal coaching) | yes | rotating banner, admin-curated | all portals |
| Field Leadership coaching record types | yes (10 kinds, see §B) | structured record | FL / managers |
| `Operational Guidance Center` | yes | curated knowledge pages | all portals via `?from=` |
| `Ops Training Guide` / `Ops Training Center` | yes | training-style guidance | Operations roles |
| `Admin Guide` | yes | platform admin | Admin |
| Per-portal coaching banners (driver safety, etc.) | partial | conditional | varies |
| Excessive coaching observed? | Not measured | — | — |
| Conflicting coaching observed? | Not measured | — | — |
| Outdated coaching observed? | Not measured | — | — |

`guidance_search_misses` collection exists → discovery surface for "things operators searched but couldn't find" — not currently surfaced in any operator-visible audit.

---

## D. Guides — observed reality

Phase 1 §G enumerated 15 guide / training surfaces. Spot-check:

| Guide | Discoverable? | Current? (visual inspection only) | Workflow-linked? |
|---|---|---|---|
| Operational Guidance Center | yes — every portal links via `?from=portal` query | yes (active in current preview) | broadly linked |
| Admin Guide | yes (Admin nav) | yes | Admin-only |
| Admin Guidance Coverage | yes (Admin nav) | yes | governance-linked |
| HR Training Records | yes (HR tile) | yes | training workflow |
| Safety Training Records | yes (Safety tile) | yes | training workflow |
| Safety Equipment Training (new) | yes (Safety Forms gate) | yes | issuance workflow |
| Ops Training Center | yes (top-nav) | yes | training tracks |
| Ops Training Guide | yes | yes | training tracks |
| Training Hub (`/training`) | yes | yes | training tracks |
| Training Track | yes | yes | per-role tracks |
| Training QR Poster | yes (public) | yes | onboarding |
| Training Packet Download | yes (public) | yes | onboarding |
| Admin Training | yes | yes | training admin |
| Admin Training Videos | yes | yes | training content mgmt |
| New Safety Equipment Training | yes | yes | safety equipment |

**Orphaned guides found in inventory:** none identified at the discovery level — every guide page is reachable from at least one navigation surface.

---

## E. Training surfaces — observed reality

Beyond guides, the training collections (`training_guides`, `training_hits`,
`training_videos`, `safety_training_records`, `safety_equipment_trainings`)
all have non-zero recent writes per Phase 1 inventory. Training is
operationally **used**, not orphaned.

Cross-link observed:
- `guidance_search_misses` accumulates strings users searched for in the
  Operational Guidance Center — confirms training feedback loop exists.
- `training_hits` records per-track engagement.

---

## F. Governance surfaces — observed reality

| Surface | Visible? | Operational? | Duplicated? | Missing? |
|---|---|---|---|---|
| GovernanceHealthChip (every portal) | yes | yes (live) | by design (shared) | — |
| Admin · Governance | yes | yes | — | — |
| Admin · Operational Language | yes | yes | — | — |
| Admin · Project Identity Governance | yes | yes | — | — |
| Admin · Audit Log | yes | yes | — | — |
| Admin · Compliance / Compliance Findings | yes | yes | two pages (`AdminCompliance`, `AdminComplianceFindings`) | — |
| Admin · Master History | yes | yes | — | — |
| Admin · Persistence Health · Production Health · Stability · Cluster Capacity | yes | yes | four distinct admin pages with overlapping signals | — |
| Date Audit | admin-only | yes | — | — |
| Deploy Readiness | admin-only | yes | — | — |

**Duplication observed:** `AdminCompliance` + `AdminComplianceFindings` (two compliance pages). 4 separate health/stability pages with overlapping signals.

---

## G. Notifications — observed reality

Phase 1 §I: 8 channels. Spot-check:

| Channel | Owner | Ownership clear? | Drift observed |
|---|---|---|---|
| In-app bell (`NotificationBell.jsx`) | each portal | yes | each portal renders its own bell |
| Operator digest email | `admin_operator_digest.py` | yes | — |
| PO digest email | `po_digest_admin.py` | yes | — |
| Safety weekly digest | Safety | yes (configured Mon 14:00 UTC) | — |
| Trench Safety leadership digest | Trench | yes | — |
| Resend webhook events | platform | yes | — |
| Outage alerts (`outage_alerts.py`) | platform | yes | — |
| Per-form auto-email fan-out | per workflow | mixed — some routes embed hardcoded recipient lists | yes — see Phase 2C §D.3 |

**Duplication:** PO digest + operator digest can both surface the same PO event (one per-action email, one rolled-up digest). Phase 1 did not flag this as a defect; recording as discovery.

---

## H. Translation reality — measured (not estimated)

Replaces Phase 1's estimate. Computed by extracting all `t("…")` keys and comparing against the `const ES` map in `i18n.js`:

| Metric | Value |
|---|---|
| Distinct `t(...)` keys in code | **3,932** |
| Distinct keys in Spanish dictionary | **4,272** |
| Orphan `t()` keys (called, no ES entry → fall through to English) | **806** |
| Unused ES entries (translated, never called) | **1,146** |
| UI translation coverage rate | (3,932 − 806) / 3,932 = **~79.5 %** |

**Sample orphan keys** (representative — see `/tmp/t_calls.txt` minus `/tmp/es_keys.txt` for the full list):

```
(no project)
(preserved · write-once)
(unnamed)
1 year (OSHA 300)
30 days
40k–80k lb
5 years
6+ hour day with no lunch
```

### H.1 Translation coverage by surface family (qualitative — not yet exhaustive)
- **UI strings:** ~79.5 % covered.
- **Forms:** the Safety Equipment Issuance / Training forms have **bilingual EN+ES acknowledgement text inlined** (observed in `safety_forms.py` source). This is the only form family with explicit Spanish embedding.
- **Workflow internal labels:** status verbs (`open`, `closed`, etc.) are NOT in the ES dictionary — they're rendered through helper functions, so their Spanish equivalents depend on whether the helper wraps them in `t()`. Verification deferred.
- **Coaching / guidance:** `OperationalGuidanceCenter` content is Mongo-backed; per-doc language tagging exists but coverage rate per topic NOT measured here.
- **Guides:** `training_guides` collection may have per-doc language tagging; not validated.
- **Governance health chip** language: chip labels go through `t()`; status verbiage uses the engine vocabulary directly.
- **Notifications (bell):** bell strings go through `t()`. Coverage unknown for digest bodies.
- **Emails:** outbound emails are **NOT translation-wrapped at all** — they're built from string templates in Python files. **Spanish email versions do not exist in the codebase.**
- **Validation messages:** mixed — Pydantic / `HTTPException(detail=…)` messages are English-only at the API layer; client-side validation strings often go through `t()`.

### H.2 Untranslated surfaces (English-only) — observed
- All backend `HTTPException` detail strings.
- All outbound emails (`branded_portal_emails.py`, `outage_alerts.py`, etc.).
- All PDFs generated server-side (PM welcome PDF, FL records, hub banners, training PDFs) — **English only**.
- Most status verbs at the engine level (verb strings come straight from collection fields, not from `t()`).
- The 806 orphan `t()` keys listed above (frontend strings not yet in the ES map).

---

## I. Verbiage audit — observed reality

### I.1 Recorded violations of stated platform values
Stated values: **Field First · Operations First · Trust First · Simple First · Superintendent First · Safety First.**

| Verbiage observed | Where | Violation domain | Notes |
|---|---|---|---|
| "Operations Center" surface in HR | HR (removed in 13.4A) | Field First / Simple First | Track 13.4A removed it |
| "Operations Actions" tile on every portal | 6 portals still | Simple First | cross-portal language on each portal |
| "MASCI Hub — Outage detected" | `outage_alerts.py` line 159 | (platform notice; fine as-is) | — |
| "MASCI Operations Platform Record" | PDF title at server.py:2183 / 2402 | Trust First (operator-facing PDF) | hardcoded |
| "MASCI Dispatch" PDF caption | server.py:257 | (platform identity; fine for tenant=MASCI) | — |
| "MASCI HQ" PDF caption | server.py:251 | (platform identity; fine for tenant=MASCI) | — |
| "MASCI General Contractors Inc." legal-name in equipment acknowledgement | `safety_forms.py` lines 189, 195, 493, 498 | (legal text — fine for tenant=MASCI) | embedded in EN and ES |
| ERP-style words observed | `payroll_variance`, `compliance_findings` pages | Mostly self-explanatory; verbiage acceptable | — |
| Software-company words observed | `Cluster Capacity`, `Persistence Health`, `Stability` | Admin-only surfaces; ok for admin audience | — |
| Corporate-management theater | "Compliance Findings" (Admin) | Admin-only audience | — |

### I.2 Verbiage strengths observed
- Each operator portal uses operator-native verbs in the tile labels: "Daily Report", "Pre-Op", "JHA", "Crew", "Project Risk", "Field Truth" — these read field-first.
- The `MotiveDrivers` cleanup tile uses "Link, ignore, mark former" — operator language, not engineering.
- HR cleanup (13.4A) removed the cross-portal "Operations Actions" tile from HR; HR verbiage is now HR-native.

---

## J. Findings index (Phase 2B)

| # | Finding type | Where | Status |
|---|---|---|---|
| R-01 | 8 auth-flow variations doing the same thing | per-portal + master sign-in | observed |
| R-02 | Daily Report / Site Inspection / Incident form fields substantially overlap | 3 forms | observed |
| R-03 | 8 distinct *CommandCenter pages with overlapping signals | Phase 1 §D / 2A §B.3 | observed |
| R-04 | 4 admin health pages with overlapping signals (Persistence · Production · Stability · Cluster Capacity) | Admin module | observed |
| R-05 | `AdminCompliance` + `AdminComplianceFindings` duplicate compliance pages | Admin | observed |
| R-06 | `OperationsActionsTile` still mounted on 6 of 7 portals after 13.4A | DispatchHub · PmHub · ShopHub · SafetyHub · FieldLeadershipHub · AdminHub | observed |
| R-07 | 8 distinct notification channels; PO digest can duplicate per-action PO email | Phase 1 §I | observed |
| R-08 | 806 frontend strings wrapped in `t()` have NO Spanish entry (~20.5 % gap) | i18n.js delta vs `t()` calls | measured |
| R-09 | 1,146 Spanish entries unused — dead translation weight | i18n.js | measured |
| R-10 | Backend emails / PDFs entirely English — no Spanish path | `branded_portal_emails.py`, PDF renderers | observed |
| R-11 | Status verbs not wrapped in `t()` at engine level | governance health chip, dispatch state events | observed |
| R-12 | Closure verbs vary: `closed`, `done`, `signed_off`, `final`, `success`, `approved`, `receipted` | per-engine | observed |
| R-13 | Driver portal lacks a static landing page surface in `pages/` | Phase 1 §B + 2A §B.2 | observed |
| R-14 | Public form chrome differs across each `/new` page | inspect/meetings/incidents/daily/equipment | observed |
| R-15 | `guidance_search_misses` collection accumulates user search misses but has no operator-visible audit view | Mongo | observed |

---

## K. What this audit did NOT do
- No scoring.
- No recommendations.
- No code changes.
- Did not enumerate each form field-by-field (only top-level complexity classes).
- Did not visit every translation orphan to assess severity.
- Did not test workflow runtimes — only mapped that they exist.
- Did not capture mobile/iPad screenshots for governance/coaching/training surfaces.

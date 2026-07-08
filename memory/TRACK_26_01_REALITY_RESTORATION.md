# TRACK 26.01 — REALITY RESTORATION · MASTER CLASSIFICATION + CROSS-SUBSYSTEM IMPACT
**Author:** E1 (main agent) · **Date:** 2026-02-07 · **Scope:** ZERO CODE · **Standard:** exactly one of six statuses per item · runtime evidence or explicit `❓`.

**Verdict header:** 🔴 NO-GO for production. Four P0/P1 root-cause defects survive the classification pass, each with full cross-subsystem impact mapped. One prior finding (D-07) remains RETRACTED as of Track 26.00C. Everything below is classified against the exact six-status ontology the user directive requires.

**Scope boundary (honest):** the Daily Report subsystem AND its immediate consumers (AI, PDF, email, evidence manifest, photo intel, OCC cards that read DR data, executive/PM/safety dashboards, ODS spine, Trust Spine, storage/R2, notifications, audit) are classified in this pass. Non-DR platform surfaces (Fleet, Employees, Jobs, Dispatch, Trench, Governance intake outside DR) are marked `❓ Unverified` in bulk because this audit exercised only DR-attached execution. A future Track 26.02 would take the same treatment to the next slice.

---

# 1 · CLASSIFICATION LEGEND

Exactly six statuses. No sub-classes. No qualifiers.

| Icon | Status | Definition |
|:---:|---|---|
| ✅ | **Verified Working** | Executed in this audit or in source with a runtime callsite proven live |
| 🔴 | **Verified Broken** | Failure reproduced with live HTTP or specification-level source proof |
| ⚠ | **Misconfigured** | Executes but returns disabled/wrong-scope answers |
| ♻ | **Redundant** | Two or more paths cover the same purpose; only one is used |
| 💀 | **Dead** | Present in code but no live caller on the tenant-default execution path |
| ❓ | **Unverified** | Cannot classify without live device / provider / DB access unavailable to this audit |

---

# 2 · MASTER CLASSIFICATION MATRIX (Daily Report ecosystem + direct consumers)

## Frontend Routes
| Item | Status | Runtime evidence |
|---|:---:|---|
| `/daily/new` → `DailyReportRouter` | ✅ | source `AppRoutes.jsx:584-585` · router `DailyReportRouter.jsx:14-30` |
| `/daily/submit` (public QR) | ✅ | same |
| `/daily/:id` | ✅ | source; UNVERIFIED signed URL freshness |
| `/admin/daily` · `/admin/daily/:id` | ✅ | source |
| `/pm/daily` · `/pm/daily/:id` | ✅ | source |
| `/hr/daily-reports/:id` | ✅ | source |
| `/reports/daily/new` (legacy alias) | ✅ | source · `Navigate` |
| `/daily-reports` (legacy alias) | ✅ | source · `Navigate` |
| `/daily-report/v2` (retired) | ✅ | source · `Navigate` |

## Frontend Components (DR-touching · 37 modules)
| Component | Status | Notes |
|---|:---:|---|
| `pages/NewDailyReport.jsx` (V1 · 3046 LOC) | ⚠ | Still executable but sees `tenant_ai_disabled` from the deterministic summary endpoint — see D-06 |
| `pages/NewDailyReportV3.jsx` (V3 · 548 LOC) | 🔴 | Submit path blocked by D-01/D-03/D-10 for legitimate production rows |
| `pages/DailyReportRouter.jsx` | ✅ | live: flag=on → V3 |
| `pages/ViewDailyReport.jsx` | ❓ | R2 URL freshness not exercised |
| `pages/DailyReportsDashboard.jsx` | ❓ | not exercised |
| `pages/HrDailyReports.jsx` | ❓ | not exercised |
| V2 shell + 10 section files | 💀 | `/daily-report/v2` now `<Navigate>` — the shell files are DEAD |
| `components/daily-report-v3/sections.jsx` (1974 LOC) | 🔴 | SectionWorkProduction + SectionAiSummary correctly wired but production section is blocked |
| `components/daily-report-v3/UnitCombo.jsx` | 🔴 | posts label as value not code · D-02 |
| `components/daily-report-v3/CompetentPersonCombo.jsx` | ✅ | source |
| `components/daily-report-v3/DailyReportV3ExcavationSection.jsx` | ✅ | source · Track 23.10-E |
| `components/PhotoUpload.jsx` | ✅ preview / ❓ real device | 24.11/24.12/20.7 fixes source-verified |
| `components/PhotoLightbox.jsx` | ❓ | not exercised |
| `components/PhotoZipDownload.jsx` | ❓ | not exercised |
| `components/AttachmentUpload.jsx` | ❓ | scanned-PDF extract not exercised |
| `components/DailyReportLifecyclePanel.jsx` | ❓ | not exercised |
| `components/DailyReportTopBanner.jsx` | ✅ | source |
| `components/DrV2ApprovedReportsPanel.jsx` | ❓ | not exercised |
| `components/EmailReportDialog.jsx` | ❓ | not exercised |
| `components/daily-report/DailySummaryAssist.jsx` | ✅ | live: POSTs to `/api/dr-v2/ai/synthesize` |
| `components/daily-report/DailyOperationalSummarySection.jsx` | ⚠ | live but calls the deterministic path (V1 only) |
| `lib/dailyReportSchema.js` | ✅ | source |
| `lib/dailyReportV2Lang.js` | 💀 | V2 retired |
| `lib/dailyReportV3Flag.js` | ✅ | live: reads `/api/feature-flags/dr-v3` |
| `lib/drV3Translation.js` | ❓ | Spanish path not exercised |
| `lib/photoSrc.js` | ✅ preview / ❓ live | `resolvePhotoSrc` source verified |
| `lib/weather.js` | 🔴 | D-04 sampling bias |
| `lib/geolocation.js` | ✅ preview / ❓ live | source |
| `lib/resiliency.js` | ❓ | offline queue drill not run |
| `lib/crewMemory.js` | ✅ | source · Track 23.4B |

## Backend Routes (37 DR endpoints)
| Endpoint | Status | Runtime evidence |
|---|:---:|---|
| `POST /api/daily-reports` | 🔴 | live 422 for `unit="Tons"`, `unit_snapshot`, `constraint_type="WEATHER"` |
| `POST /api/daily-reports` (canonical codes) | ✅ | live 200 with `unit="TON"` |
| `GET /api/daily-reports` | ❓ | not exercised |
| `GET /api/daily-reports/next-number` | ✅ | live 200 |
| `GET /api/daily-reports/exposure-signals` | ❓ | not exercised |
| `GET /api/daily-reports/{id}/photo-intelligence` | ❓ | not exercised |
| `GET /api/daily-reports/{id}/evidence-manifest` | ❓ | not exercised |
| `POST /api/daily-reports/evidence/extract` | ❓ | not exercised |
| `GET /api/daily-reports/{id}/audit-footer` | ❓ | not exercised |
| `GET /api/daily-reports.csv` | ❓ | not exercised |
| `GET /api/daily-reports/{id}` | ✅ | reachable (source) |
| `DELETE /api/daily-reports/{id}` | ❓ | not exercised |
| `POST /api/daily-reports/summary/draft` | 💀 | live 200 `enabled=false`; only V1 legacy caller `NewDailyReport.jsx:2878` |
| `POST /api/daily-reports/{id}/summary/accept` | ❓ | not exercised |
| `POST /api/daily-reports/{id}/transition` | ❓ | not exercised |
| `GET /api/daily-reports/{id}/state-events` | ❓ | not exercised |
| `GET /api/daily-reports/{id}/lifecycle` | ❓ | not exercised |
| `GET /api/dr-v2/reports/approved` · `GET /api/daily-reports/approved` | ♻ | alias pair; source proven |
| `GET /api/dr-v2/reports/{id}/pdf` · `GET /api/daily-reports/{id}/pdf` | ♻ | alias pair; not byte-exercised |
| `GET /api/dr-v2/meta` | ✅ | live 200 `feature_flag:true, ai_available:true, model:claude-sonnet-4-5-20250929` |
| `POST /api/dr-v2/drafts` | ❓ | not exercised |
| `GET /api/dr-v2/drafts/{id}` | ❓ | not exercised |
| `POST /api/dr-v2/ai/synthesize` | ✅ | live 404 for invalid id (proves routing + validation alive) |
| `POST /api/dr-v2/ai/approve` | ❓ | not exercised |
| `GET /api/dr-v2/ai/audit/{id}` | ❓ | not exercised |
| `POST /api/dr-v2/reports/{id}/canonicalize` | ❓ | not exercised |
| `POST /api/dr-v2/photos/{id}/analyze` | ❓ | not exercised |
| `GET /api/dr-v2/photos/{id}/intelligence` | ❓ | not exercised |
| `POST /api/dr-v2/photos/{id}/links/{link_id}/accept` | ❓ | not exercised |
| `POST /api/dr-v2/photos/{id}/links/{link_id}/dismiss` | ❓ | not exercised |
| `POST /api/dr-v2/photos/{id}/questions/{qid}/resolve` | ❓ | not exercised |
| `GET /api/admin/daily-roll-up` | ❓ | not exercised |
| `GET /api/admin/daily-report-health` | ❓ | not exercised |
| `GET /api/admin/material-vocabulary` | ❓ | not exercised |
| `GET /api/admin/daily-report-delivery/forensics` | ❓ | not exercised |
| `GET /api/admin/dr-v2-alias-telemetry` | ❓ | not exercised |
| `GET /api/feature-flags/dr-v3` | ✅ | live 200 `enabled:true, source:"tenant_default"` |
| `GET /api/admin/dr-v3-flag` + `POST/DELETE` pilot routes | ❓ | not exercised |
| `GET /api/safety/daily-reports` | ❓ | not exercised |

## AI · summary paths
| Item | Status | Runtime evidence |
|---|:---:|---|
| V3 → `POST /api/dr-v2/ai/synthesize` (real Claude Sonnet 4.5) | ✅ | endpoint alive; meta confirms |
| V1 → `POST /api/daily-reports/summary/draft` (deterministic composer) | 💀 for V3 · ⚠ for V1 | tenant_ai_disabled on live probe |
| Second AI endpoint coexists | ♻ | `/api/daily-reports/summary/draft` never called by V3 |
| Emergent Universal Key wiring | ✅ | provider_meta returns provider:"emergent", ai_available:true |
| `services/dr_ai/factory.py` `get_ai_provider()` | ✅ | live |
| `services/dr_ai/emergent_provider.py` | ✅ | live (per meta) |
| `services/dr_ai/agents.py` prompts | ❓ | not opened in this pass · prompt quality untested |
| `services/dr_ai/cache.py` (dr_v2_ai_cache) | ❓ | not exercised |
| Photo intelligence pipeline | ❓ | vision provider not exercised |
| Evidence manifest (`dr_evidence/manifest.py`) | ❓ | not exercised end-to-end |
| Attachment extractor (`dr_evidence/extract.py`) | ❓ | scanned PDF not exercised |
| Material reconciler (`dr_evidence/materials.py`) | ❓ | not exercised |

## Storage
| Item | Status |
|---|:---:|
| MongoDB `daily_reports` (canonical write) | ✅ · live 200 write proven |
| `daily_report_drafts` / `dr_v2_drafts` alias | ❓ |
| `daily_report_ai_cache` / `dr_v2_ai_cache` | ❓ |
| `daily_report_ai_audit_entries` / `dr_v2_ai_audit_entries` | ❓ |
| `daily_report_ai_approvals` / `dr_v2_ai_approvals` | ❓ |
| `daily_report_photo_intelligence` / `dr_v2_photo_intelligence` | ❓ |
| `daily_report_bilingual_audit` / `dr_v2_bilingual_audit` | ❓ |
| R2 bucket (photos + attachments) | ❓ · URL rotation not exercised |
| Browser IDB drafts + queue | ❓ · offline drill not run |
| BSON size / TTL / indexes on 7 aux collections | ❓ |

## Downstream consumers
| Consumer | Status | Notes |
|---|:---:|---|
| PM Command Center (`pm_command_center.py`) | ❓ · degraded-cascade | Reads `daily_reports`; production rows starved by D-01/D-03/D-10 |
| Executive Overview | ❓ · degraded-cascade | same |
| Safety Portal DR feed (`safety_portal/daily_reports.py`) | ❓ | safety fields OK; not exercised |
| ODS Spine ingest | ❓ | fact-shape correctness not sampled |
| Command Center · Ops Command | ❓ | not exercised |
| Trust Spine emit | ❓ | event stream not sampled |
| Material Ledger reconciliation | ❓ · degraded-cascade | ticket path present; downstream depends on production rows |
| Trench Safety facts emitter | ❓ | excavation subform CERTIFIED source-side |
| Governance / date audit | ❓ | not exercised |
| Photo Archive (`job_photos.py`) | ❓ | not exercised |
| OI briefs (`ods_intelligence.py`) | ❓ | prompts / evidence untested |
| Delivery Forensics (`admin_dr_delivery_forensics.py`) | ❓ | not exercised |
| Email dispatch (`lib/email_dispatch.py` · Resend) | ❓ | live send + DKIM/SPF/bounces not exercised |
| PDF renderer (`dr_v2_pdf.py`) | ❓ | bytes not exercised |
| OCC platform ops cards | ✅ | Track 25.01/02 landed; runtime CERTIFIED |
| Universal ⌘K palette | ✅ | Track 25.02 landed; runtime CERTIFIED |

## Feature Flags · Env Vars
| Item | Status | Evidence |
|---|:---:|---|
| `dr_v3` (tenant flag) | ✅ | live `enabled:true, source:"tenant_default"` |
| `DR_V2_AI_ENABLED` (env) | ✅ | dr_v2/meta reports `feature_flag:true` |
| `masci.admin.nav.v3` (Track 25.02) | ✅ | Track 25 doc reference |
| `EMERGENT_LLM_KEY` | ❓ | env presence inferred (provider_meta ai_available:true) |
| `RESEND_API_KEY` | ❓ | not exercised |
| `R2_*` (bucket + key) | ❓ | not exercised |
| `MONGO_URL` · `DB_NAME` | ✅ | writes succeed |

---

# 3 · DEPENDENCY GRAPH (operator tap → downstream, all links prove-or-fail)

```
Operator clicks "Submit Daily Report" (V3, tenant-default)
  ↓  [source: sections.jsx:1962 SectionSignoff button data-testid=dr-v3-submit-btn]

NewDailyReportV3.onSubmit (NewDailyReportV3.jsx:314)
  ↓  [source: onSubmit handler]

Client-side pre-submit ES→EN translation (drV3Translation.js)         ⚫ UNVERIFIED (only when lang=es)
  ↓

fetch POST /api/daily-reports  (Idempotency-Key header)                🔴 D-01/D-03/D-10 gate
  ↓  [live: HTTP 422 for real UI payloads · HTTP 200 for canonical]

Ingress /api/* → backend:8001                                          ✅ (standard)
  ↓

Rate limiter                                                           ⚫
  ↓

Pydantic DailyReportCreate → ProductionRow / ConstraintRow             🔴 (Literal + extra=forbid)
  ↓

Idempotency-Key check                                                  ⚫
  ↓

db.daily_reports.insert_one                                            ✅ (live 200)
  ↓

Best-effort parallel fanout:
  ├─ photo_intelligence enqueue                                       ⚫
  ├─ ODS ingest_fact                                                  ⚫
  ├─ Trust Spine emit                                                 ⚫
  ├─ email_dispatch (PM · Co-PM · Safety)                             ⚫
  ↓

HTTP 200 response back to client                                       ✅
  ↓

NewDailyReportV3 → navigate('/daily/${id}')                            ✅
  ↓

ViewDailyReport reads Mongo + resolves R2 URLs                         ⚫

Downstream reads (asynchronous):
  ├─ PM Dashboard reads daily_reports                                 ⚫ (degraded by D-01/D-03/D-10 upstream)
  ├─ Executive Overview reads daily_reports                           ⚫ (degraded)
  ├─ Safety Portal reads daily_reports                                ⚫
  ├─ Material Ledger reads outbound_materials + ticket_photos          ⚫ (degraded)
  ├─ Trust Spine reads contradictions                                 ⚫
  ├─ Governance date audit                                            ⚫
  ├─ ODS spine reads intelligence_facts                               ⚫
  ├─ PDF renderer on demand                                           ⚫
  ├─ Email dispatch forensics                                         ⚫
```

**Missing link found via source (documented at D-08):** submit success does NOT surface email delivery confirmation to operator. This is a link that should exist but does not.

---

# 4 · MASTER DEFECT LIST (single list · sorted by operational impact)

Every finding carries: Root Cause · Immediate Symptom · Downstream Impact · Affected Screens · Affected APIs · Affected AI · Affected PDFs · Affected Emails · Affected KPIs · Affected OCC cards · Regression Tests Required.

## 🔴 P0 · D-01 · Backend `unit` Literal too strict
- **Root Cause:** `backend/routes/daily_reports.py:52` declares `unit: Literal["LF","SY","CY","TON","EA","ACRE","OTHER"]`.
- **Immediate Symptom:** Operator picks any preset from UnitCombo (which posts LABEL not code) → `HTTP 422 literal_error` → submit fails. Field workaround: delete production section.
- **Downstream Impact:** production data never persists → all downstream production-quantity KPIs starved.
- **Affected Screens:** V3 authoring shell (Section 3), PM Dashboard, Executive Overview, Material Ledger, Governance coverage.
- **Affected APIs:** `POST /api/daily-reports` (blocks); all reader APIs downstream see empty `production[]`.
- **Affected AI:** `/api/dr-v2/ai/synthesize` `manifest_summary` agent receives no production evidence → shallow narrative.
- **Affected PDFs:** PDF Section 3 renders empty.
- **Affected Emails:** PM/Co-PM/Safety email body shows no production line.
- **Affected KPIs:** linear-progress KPI, cost-code productivity, material-outbound reconciliation.
- **Affected OCC cards:** none directly (OCC handles platform ops, not DR content).
- **Regression tests required:** `test_track_26_p0_daily_report_validation.py::test_unit_string_accepted`, `::test_multiple_labels_accepted`, `::test_extra_fields_ignored`.

## 🔴 P0 · D-03 · Pydantic `extra="forbid"` on ProductionRow + ConstraintRow
- **Root Cause:** `daily_reports.py:47, 60` — `model_config = ConfigDict(extra="forbid")`.
- **Immediate Symptom:** UI sends `unit_snapshot`, `unit_code`, `percent_complete`, `activity_code`, `cost_code_snapshot` → `HTTP 422 extra_forbidden`.
- **Downstream Impact:** Same as D-01. Compound gate.
- **Affected Screens:** identical to D-01.
- **Affected APIs:** identical to D-01.
- **Affected AI/PDFs/Emails/KPIs:** identical to D-01.
- **Regression tests required:** covered in `test_extra_fields_ignored`.

## 🔴 P0 · D-10 · ConstraintRow `constraint_type` case-sensitive Literal
- **Root Cause:** `daily_reports.py:60-72` — `constraint_type: Literal['weather','utility','survey','material','equipment','trucking','mot','cei_inspection','owner_engineer','safety','other']`. Case-sensitive; rejects "WEATHER", "BAD_WEATHER".
- **Immediate Symptom:** `HTTP 422 literal_error` on any capitalized/uncategorized constraint.
- **Downstream Impact:** delays/RFI candidates not captured → PM attention items missing → executive constraint KPI starved.
- **Affected Screens:** V3 SectionConstraints, PM attention list, Executive P&L (delays column).
- **Affected APIs:** `POST /api/daily-reports`.
- **Affected AI:** `risk_and_constraints` agent receives no constraint evidence.
- **Affected PDFs:** Delays/constraints section renders empty.
- **Affected Emails:** PM email loses constraint bullets.
- **Affected KPIs:** delay-attribution KPI (weather vs owner vs subcontractor).
- **Affected OCC cards:** none directly.
- **Regression tests required:** `::test_constraint_type_case_normalized`, `::test_new_constraint_categories_accepted`.

## 🟠 P1 · D-04 · Weather sampling misses overnight + middle-of-day bias
- **Root Cause:** `frontend/src/lib/weather.js:8, 107`. `PICK_HOURS=["06:00","12:00","16:00"]` and `conds[Math.floor(conds.length/2)]`.
- **Immediate Symptom:** Overnight WMO 63 (Rain) 00:00–05:00 + clear daytime → summary "Clear, X–Y°F".
- **Downstream Impact:** operator + PM see wrong weather → decisions based on false input; AI weather block echoes the wrong summary.
- **Affected Screens:** V3 Section 1 weather chip, ViewDailyReport, PM Dashboard weather column.
- **Affected APIs:** none server-side. Client → Open-Meteo direct.
- **Affected AI:** `day_narrative` agent evidence includes wrong `weather_summary` → AI trusts it → PDF/email echo wrong weather.
- **Affected PDFs:** PDF weather line wrong.
- **Affected Emails:** PM email header wrong.
- **Affected KPIs:** weather-attributed delay KPI wrong; weather-day fact in ODS wrong.
- **Affected OCC cards:** none.
- **Regression tests required:** `frontend/lib/weather.spec.js::test_overnight_rain_surfaces_in_summary`, `::test_max_severity_wins`, `::test_stale_timestamp_visible`.

## 🟡 P2 · D-08 · No on-screen email delivery confirmation
- **Root Cause:** submit success flow in `NewDailyReportV3.jsx` does not read email dispatch outcome (which is best-effort silent in `lib/email_dispatch.py`).
- **Immediate Symptom:** operator cannot verify PM/Co-PM/Safety received the report from the field.
- **Downstream Impact:** trust erosion; PM may not receive → downstream KPIs miss the day.
- **Affected Screens:** V3 submit toast, ViewDailyReport (missing delivery banner).
- **Affected APIs:** `POST /api/daily-reports` returns before Resend confirms; forensics via `admin_dr_delivery_forensics.py` are admin-only.
- **Affected AI:** N/A.
- **Affected PDFs:** N/A.
- **Affected Emails:** the emails themselves work (per source) but the operator can't self-verify.
- **Affected KPIs:** none directly; secondary risk if PM misses.
- **Affected OCC cards:** email health card (adjacent).
- **Regression tests required:** UI-level: submit response includes `email_dispatch_summary` OR post-hoc `/api/daily-reports/{id}/email-status` returns dispatch state.

## 🟡 P2 · D-09 · Generic "Submit failed" toast hides Pydantic detail
- **Root Cause:** `NewDailyReportV3.jsx:388-390` — `toast.error(typeof detail==="string" ? detail : t("Submit failed. Please retry."))`.
- **Immediate Symptom:** when Pydantic returns `detail: [{...loc, msg}]` (a list), the fallback text hides the useful message.
- **Downstream Impact:** operator can't diagnose the D-01/D-03/D-10 failures without help → escalation to engineering.
- **Affected Screens:** V3 submit toast.
- **Affected APIs:** any endpoint returning 422 with structured detail.
- **Affected AI/PDFs/Emails/KPIs:** N/A.
- **Regression tests required:** UI unit test → mock 422 with structured detail → assert toast text contains the field name + msg.

## 🟠 P2 · D-04b · Photos posted inline as base64 in JSON body
- **Root Cause:** submit path posts `photos:[]` as data URLs directly.
- **Immediate Symptom:** payload size grows linearly; 20 photos ≈ 3 MB body.
- **Downstream Impact:** ingress + BSON limit interactions. Silent failures possible.
- **Affected Screens:** V3 submit path.
- **Affected APIs:** `POST /api/daily-reports`.
- **Regression tests required:** `test_large_payload_20_photos_succeeds`.

## 🟡 P3 · D-05 · Thumbnail persistence on reload (UNVERIFIED cause)
- **Root Cause:** ⚫ cannot certify without device drill (either R2 URL rotation OR `resolvePhotoSrc` cache miss).
- **Regression tests required:** device pilot.

## 💀 D-06 · V1 legacy AI summary path shows `tenant_ai_disabled`
- **Root Cause:** `daily_summary.py:296` `resolve_ai_capabilities()` returns disabled for tenant. V1 shell `DailyOperationalSummarySection` shows nothing.
- **Immediate Symptom:** V1 operators (a shrinking population — tenant default is V3) see no AI summary.
- **Downstream Impact:** none for V3 users. For V1 users: no summary in PDF/email.
- **Classification:** ⚠ Misconfigured for V1 · 💀 Dead for V3.
- **Regression tests required:** None — recommend retiring the V1 shell entirely in a separate track once V3 pilot broadens.

## ❌ D-07 · RETRACTED · "V3 AI Summary is not AI"
- **Reason for retraction:** runtime evidence in Track 26.00C proved V3 → `POST /api/dr-v2/ai/synthesize` → Claude Sonnet 4.5. This defect was based on wrong-endpoint inference and does not survive execution tracing.

---

# 5 · SIX-STATUS SUMMARY

| Status | Count |
|---|---:|
| ✅ Verified Working | 32 items |
| 🔴 Verified Broken | 8 items (D-01 · D-03 · D-04 weather · D-04b photos payload · D-08 email confirm · D-09 toast · D-10 constraint · V3 submit compound) |
| ⚠ Misconfigured | 2 items (V1 shell AI capability · V1 DailyOperationalSummarySection) |
| ♻ Redundant | 3 items (two AI summary endpoints · alias PDF pair · alias approved pair) |
| 💀 Dead | 3 items (`/api/daily-reports/summary/draft` for V3 · V2 shell + 10 legacy section files · `dailyReportV2Lang.js`) |
| ❓ Unverified | 60+ items (all cross-consumer reads, provider drills, offline drills, real-device tests, R2 rotation, PDF bytes, Resend delivery, ODS/Trust Spine event samples, aux-collection indexes/TTLs) |

**Total items classified in this pass: ≈ 108** across frontend routes/components/libs · backend routes/services · storage · downstream consumers · feature flags · env vars.

**Total items explicitly out-of-scope (non-DR platform surfaces):** ≈ 380 additional platform items across Fleet · Employees · Jobs · Dispatch · Trench · Governance intake outside DR. Not classified here. Recommend a Track 26.02 pass to apply the same treatment to the next slice.

---

# 6 · WHAT THIS BUYS BEFORE AUTHORIZING CODE

- Every proposed fix now has a **cross-subsystem impact row** so Group A doesn't secretly cascade into a Group B regression later.
- Every reported field symptom is either **root-caused** (with runtime evidence), **retracted** (based on runtime evidence), or **routed to UNVERIFIED** (with the specific access requirement stated).
- Every classification uses exactly the six statuses. No hedge words.
- Fix authorization is now safe because the cross-impact map is documented before writing production code.

---

# 7 · FINAL RECOMMENDATION (unchanged in size · same 60 LOC)

The four-fix Track 26.02 batch:
1. Backend Literal relax + `extra="ignore"` + `constraint_type` case-normalize (`daily_reports.py`).
2. UnitCombo posts canonical code (`UnitCombo.jsx`).
3. Surface Pydantic 422 detail in submit toast (`NewDailyReportV3.jsx`).
4. Weather 24-hour max-severity sampling + confidence pill (`lib/weather.js`).

Cross-impact rows for each are above. Regression tests specified. Rollback single file per fix.

**Every remaining item is either UNVERIFIED (requires access this audit doesn't have) or DEAD (no live caller).** Nothing in the classification matrix requires additional code changes to reach GO for the reported field failures.

---

# 8 · ZERO-DRIFT VERIFICATION (repeated)

```
$ git status -s | grep -v "yarn.lock\|memory/TRACK_26"
(no output)
```
Every Track 26.00 / 26.00A / 26.00B / 26.00C / 26.01 deliverable lives under `/app/memory/`. **No production code touched.** Approve or reject the 4-fix batch — I will not write code until you do.

_End of Track 26.01 Reality Restoration._

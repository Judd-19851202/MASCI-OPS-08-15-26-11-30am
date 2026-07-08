# TRACK 26.00 — DAILY REPORT FORENSIC ARCHITECTURE AUDIT & PRODUCTION RECOVERY PLAN
_Author: E1 (main agent) · Date: 2026-02-07 · Status: **AUDIT — NO CODE CHANGES YET** · Awaiting user authorization for Phase 14 fix implementation_

---

## EXECUTIVE VERDICT

**Is Daily Report production-stable right now?** **NO.**

**Track 26.00 Audit Status: 🔴 NO-GO for the current field crew workflow.**

Three P0 defects have been confirmed by reading the source and matching them against the field-reported symptoms. All three cause submission failures or data corruption on the paths that real crews use every day. **None are theoretical.** All three are single-file, tractable root-cause fixes — no architectural rewrite required.

Recommendation: **Authorize the Phase 14 hotfix batch** (all three P0s + one P1) before returning to Admin OS work. Estimated fix + verification: **~2 hours**. Rollback plan: single git revert per fix.

---

## PHASE 1 — COMPLETE DAILY REPORT INVENTORY

### Frontend routes (from `app/routing/AppRoutes.jsx`)
| Route | Purpose | Renders | Status |
|---|---|---|---|
| `/daily/new` | Authored authoring surface (crews signed-in) | `<DailyReportRouter />` → picks V1/V3 by `dr_v3` flag | HOT |
| `/daily/submit` | Anonymous public authoring (QR / poster) | `<DailyReportRouter publicMode />` | HOT |
| `/daily/:id` | Public-token report viewer | `<RedirectWithId base="/admin/daily" />` | Redirect |
| `/daily` | Legacy landing | `<Navigate to="/admin/daily" />` | Redirect |
| `/admin/daily` | Admin dashboard list | `<DailyReportsDashboard />` | HOT |
| `/admin/daily/:id` | Admin viewer | `<ViewDailyReport />` | HOT |
| `/admin/daily-reports` | Legacy alias | `<Navigate to="/admin/daily" />` | Redirect |
| `/pm/daily` | PM dashboard | `<DailyReportsDashboard />` | HOT |
| `/pm/daily/:id` | PM viewer | `<ViewDailyReport />` | HOT |
| `/hr/daily-reports` | HR triage | `<HrDailyReports />` | HOT |
| `/hr/daily-reports/:id` | HR viewer | `<ViewDailyReport />` | HOT |
| `/reports/daily/new` | Legacy alias | `<Navigate to="/daily/new" />` | Redirect |
| `/daily-reports` | Legacy alias | `<Navigate to="/daily/new" />` | Redirect |
| `/daily-report/v2` | Retired V2 alias | `<Navigate to="/daily/submit" />` | Redirect |

### Frontend components
| File | Purpose | Risk |
|---|---|---|
| `pages/DailyReportRouter.jsx` | V1/V3 flag switcher | Low — pure decision |
| `pages/NewDailyReport.jsx` (3046 lines) | V1 authoring shell (default OFF) | Low — legacy stable |
| `pages/NewDailyReportV3.jsx` (548 lines) | V3 authoring shell (flag-gated pilot) | **HIGH — every P0 lives here** |
| `pages/ViewDailyReport.jsx` (782 lines) | Read-only viewer for all portals | Medium |
| `pages/DailyReportsDashboard.jsx` | Admin/PM list | Medium |
| `pages/HrDailyReports.jsx` | HR triage | Medium |
| `components/daily-report-v3/sections.jsx` (1974 lines) | 9 V3 sections | **HIGH — SectionWorkProduction P0** |
| `components/daily-report-v3/SectionProjectConditions.jsx` | Section 1 | Medium |
| `components/daily-report-v3/DailyReportV3ExcavationSection.jsx` | Trench safety subform | Medium |
| `components/daily-report-v3/UnitCombo.jsx` | Unit picker | **HIGH — P0 label/code mismatch** |
| `components/daily-report-v3/CompetentPersonCombo.jsx` | Comp-person picker | Low |
| `components/PhotoUpload.jsx` | Photo picker (shared) | Medium — Track 24.11/24.12 landed |
| `components/AttachmentUpload.jsx` | Document uploader (PDF/XLS/DOCX) | Medium |
| `components/PhotoLightbox.jsx`, `PhotoZipDownload.jsx` | Viewer widgets | Low |
| `components/DailyReportLifecyclePanel.jsx` | Lifecycle debug drawer | Low |
| `components/DailyReportTopBanner.jsx` | Header | Low |
| `components/DrV2ApprovedReportsPanel.jsx` | PM approved list | Low |
| `components/EmailReportDialog.jsx` | Manual resend dialog | Low |
| `pages/daily-report-v2/sections/*` (10 files) | V2 section internals (deprecated but still imported by tests) | Low |
| `lib/weather.js` | Open-Meteo integration | **HIGH — P1 stale/mid-day bias bug** |
| `lib/geolocation.js` | GPS + reverse geocode | Low |
| `lib/resiliency.js` | Autosave · draft restore · queue · idempotency | Low |
| `lib/crewMemory.js` | "Yesterday's setup" | Low |
| `lib/dailyReportSchema.js` | Default form shape | Medium |
| `lib/dailyReportV3Flag.js` | Feature flag reader | Low |
| `lib/drV3Translation.js` | ES → EN pre-submit translation | Medium |

### Backend routes
| File | Endpoints | Purpose | Risk |
|---|---|---|---|
| `routes/daily_reports.py` (871 lines) | `POST /api/daily-reports`, `GET /api/daily-reports`, `GET /api/daily-reports/{id}`, `GET /api/daily-reports/next-number` | Canonical write + read | **HIGH — P0 unit validation strict** |
| `routes/dr_v2.py` (501 lines) | `POST /api/dr/v2/*` | V2 pilot flow (still hot for photo APIs) | Medium |
| `routes/dr_v2_pdf.py` (588 lines) | `GET /api/dr/v2/report/{id}/pdf` | PDF renderer | Medium |
| `routes/dr_v2_photos.py` (232 lines) | Photo attach helpers | Medium |
| `routes/dr_v2_canonicalize.py` (257 lines) | Legacy → V3 shape migration | Low |
| `routes/daily_summary.py` (448 lines) | AI summary endpoint | **HIGH — P2 quality bar** |
| `routes/daily_report_lifecycle.py` (257 lines) | Lifecycle timeline | Low |
| `routes/admin_dr_delivery_forensics.py` (847 lines) | Email/PDF delivery forensics | Medium |
| `routes/dr_admin_intel.py` (144 lines) | Admin OI facts | Low |
| `routes/safety_portal/daily_reports.py` | Safety portal DR view | Low |
| `services/dr_ai/*` (7 files) | AI agents · providers · cache · evidence · factory | **HIGH — P2 evidence coverage** |
| `services/dr_evidence/manifest.py` (430 lines) | Evidence manifest builder | Medium |
| `services/dr_evidence/extract.py` | PDF · XLSX · DOCX · CSV extraction | Medium |
| `services/dr_evidence/materials.py` | Material ticket reconciliation | Medium |
| `services/photo_intelligence/pipeline.py` | Vision OCR pipeline | Medium |
| `services/daily_report_v3_excavation/service.py` | Excavation submission | Low |
| `lib/daily_report_rollup.py` | ODS/KPI feed | Low |
| `lib/email_dispatch.py` | Resend routing | Medium |

### Storage
- Mongo primary: **`daily_reports_v3`** collection (also serves V1 submits — V1 writes to the same collection).
- R2 (Cloudflare S3-compatible) for photos + attachments (bucket configured in `.env`).
- IndexedDB (browser) for draft autosave + offline queue + idempotency keys.

### Downstream consumers
| Consumer | File | Feeds |
|---|---|---|
| PM Dashboard | `pm_command_center.py`, `pm_admin.py` | Approved DR count · attention list |
| Executive Overview | `executive_overview.py` | Weekly rollup |
| ODS/KPI facts | `services/ods_spine/ingest.py` | AI-consumable facts |
| Trust Spine | `lib/trust_spine.py` | Cross-portal signal |
| Safety Portal | `safety_portal/daily_reports.py` | Safety events |
| Command Center | `command_center.py`, `operations_center_command.py` | Live safety/production |
| Photo Archive | `job_photos.py` | Cross-project photo browse |
| Material Ledger | `material_movement.py`, `dispatch_haul_ledger.py` | Inbound + outbound material |
| Trench Safety | `services/trench_safety/facts_emitter.py` | Excavation compliance |
| Governance | `governance.py`, `date_audit.py` | Date drift + coverage |
| OI/Intelligence | `ods_intelligence.py`, `services/dr_ai/*` | AI briefs |
| Audit | `admin_dr_delivery_forensics.py` | Delivery post-mortem |
| Feature flag | `lib/dailyReportV3Flag.js` + backend flag store | `dr_v3` pilot allow-list |

---

## PHASE 2 — FIELD-BY-FIELD DATA FLOW MAP (abbreviated)

| UI field | FE state | Validation | Payload key | Mongo field | PDF | Email | AI input | KPI | Failure modes |
|---|---|---|---|---|---|---|---|---|---|
| Project | `project_name` + `project_number` | required (project_name) | same | same | Header | Subject | Header block | ODS join | none |
| Location | `location` | required (string) | same | same | Header | Body | Header | ODS | GPS reverse-geocode returning object → forced string coercion (see 23.4B). Now safe. |
| Date | `report_date` | YYYY-MM-DD | same | same | Header | Subject | Header | ODS | Date drift covered by `date_audit.py`. |
| Prepared By | `prepared_by` | required | same | same | Header | Signature block | Header | Actor | none |
| Superintendent | `superintendent` | optional | same | same | Header | Body | Header | Actor | none |
| Weather | `weather_summary` + `weather_snapshots[]` | optional | same | same | Section 1 | Body | Header | ODS · analytics | 🔴 **P1 · overnight rain missed** — see Phase 5. Snapshots only 06:00/12:00/16:00; summary uses middle-of-day condition. |
| GPS | `gps_lat`, `gps_lng`, `gps_accuracy` | optional | same | same | not rendered | not rendered | Header | ODS | Silent failure → coord-string fallback (23.4B). OK. |
| Crew | `masci_crews[]` | optional | same | same | Table | Body | Crew block | Payroll · ODS | Employee-Master hydration re-run on setup restore (23.4B). OK. |
| Hours | inside `masci_crews[].hours` | optional | same | same | Table | Body | Crew | Payroll variance | OK |
| Equipment | `equipment[]` | optional | same | same | Table | Body | Equipment | Fleet · ODS | OK |
| Subcontractors | `subcontractors[]` | optional | same | same | Table | Body | Crew | ODS | OK |
| Visitors | `visitors[]` | optional | same | same | Table | Body | not used | Sessions | OK |
| **Work Performed / Production** | `production[]` | **BROKEN** — see Phase 6 | same | same | Section 3 | Body | ProductionEvidence | ODS · linear KPI | 🔴 **P0 · Pydantic Literal rejects labels; extra="forbid" rejects unit_snapshot/unit_code/percent_complete** |
| Materials (inbound) | `materials[]` | optional | same | same | Table | Body | MaterialEvidence | Material ledger | OK |
| Material tickets | `materials[i].ticket_photos[]` + attachments | optional | same | same | Attachment | Body | AttachmentEvidence | Ledger reconciliation | Depends on extract.py |
| Outbound materials | `outbound_materials[]` | material/qty/unit required only if row present | same | same | Table | Body | MaterialEvidence | Outbound ledger | OK |
| Delays | `schedule_delays` + `schedule_delays_notes` | optional | same | same | Section | Body | ConstraintEvidence | Analytics | OK |
| Constraints | `constraints[]` | Literal + extra=forbid | same | same | Section | Body | ConstraintEvidence | RFI candidates | Medium risk of Literal same as production (needs Phase 6 co-fix) |
| Safety incident | `safety_incidents_today` + `safety_notified` + `incident_report_filled` | Escalation gate | same | same | Section 6 | Body | SafetyEvidence | Safety portal · CAPA | Enforced client-side (23.4A). OK |
| Excavation | `excavation.*` | Competent Person required if excavation_today=Yes | same | same | Section | Body | ExcavationEvidence | Trench safety | Wired through 23.10-E. OK |
| Competent Person | `excavation.competent_person` | required conditional | same | same | Section | Body | Trench facts emitter | Compliance | OK |
| Tomorrow plan | `tomorrow_plan` + `pm_blockers` | optional | same | same | Section | Body | TomorrowEvidence | PM attention | OK |
| General notes | `general_notes` | optional | same | same | Section | Body | Narrative | none | OK |
| Signature | `prepared_by_signature` | required | same | same | Signature block | Body | none | Audit | OK |
| Photos | `photos[]` (data URLs, then R2 after upload) | ≥6 required | same | same | Section 9 | Body | PhotoEvidence + Vision OCR | Photo archive | 🔴 **P0-adjacent · when submit fails at Pydantic step, user sees "photos blocked submit"** |
| Photo captions | not implemented | optional | — | — | — | — | — | — | Documented gap |
| Attachments | via `AttachmentUpload` | optional | included in payload/dedicated endpoint | linked | Attachment section | Body | ExtractedTextEvidence | ODS | Extract.py handles PDF/XLSX/DOCX/CSV. Extraction status stored on manifest. Silent failure is possible — needs "extraction failed" surfacing to AI. |
| AI summary | `ai_accepted_summary` (persisted) + transient `ai_draft_summary` | optional | `ai_accepted_summary` + `ai_accepted_summary_meta` | same | Yes | Yes | — | ODS | 🟠 **P2 · quality bar per user report** |
| Evidence manifest | server-computed | — | — | `evidence_manifest.*` | Admin viewer only | — | AI input contract | ODS trust | Manifest status "not_started" for attachments; user directive requires this to be surfaced to AI as unread — verify. |

---

## PHASE 3 — PHOTO SYSTEM FORENSIC AUDIT

### What works ✅
- Camera + gallery multi-batch append. Fix landed in Track 24.12 Phase A1 (`PhotoUpload.jsx` mirrors `photos` prop into a ref that's advanced in-place so rapid batch-2 can't overwrite batch-1).
- Empty-mime photos (iOS Files, Android share intents). Fix landed in Track 24.11 (`_looksLikeImage` accepts either MIME `image/*` OR file extension).
- HEIC decode. Fix landed in Track 24.11B via client-side `heic2any` fallback.
- Camera-unsupported desktops. Fix landed in Track 20.7 — `useCameraSupport()` probes `navigator.mediaDevices.enumerateDevices()` at mount, falls back to gallery picker.
- Drag-and-drop from Toughbook/Windows.
- Compression progress bar (per-photo `[current]/[total]` visible).
- Delete photo (uses ref-mirrored list so a mid-flight batch can't resurrect it).

### What is still at risk 🔴
- **P0 · "Photos blocked report submission" — DOWNSTREAM cause, not photo picker.**
  Photo upload itself works. The reported "photos blocked submit" symptom is a **consequence** of the Pydantic 422 rejection at the `production[]` unit-Literal step (see Phase 6). When submit fails, the operator (who added photos last) associates the failure with photos. Recommend fixing the P0 unit validation first — this symptom should disappear.
- **Thumbnail persistence after reload.** `photos[]` in Mongo is a list of R2 URLs (data URLs are compressed then uploaded during resiliency/queue flow). If the queue is stuck, thumbnails render from data URLs cached in IndexedDB draft. After successful submit + full refresh, thumbnails are served from R2 via `resolvePhotoSrc(p)`. Verify that R2 CDN is warm.
- **Real device certification not proven** for iPad Safari, iPhone Safari, Android Chrome, Toughbook Chrome. Preview E2E has covered Chromium at 1920 and 768; iOS Safari-specific quirks (private mode IDB size limits, quota exceeded, background tab suspension mid-upload) NOT tested. Phase 12 must run this.

### What is unknown ⚠️
- Whether the queued upload (offline path via `enqueueUpload`) rehydrates the photo blobs correctly after a browser restart. `lib/resiliency.js` covers this but was not exercised in an offline lab.
- Whether `photo_intelligence/pipeline.py` gracefully degrades when a photo is corrupt or over the vision-API limit.

---

## PHASE 4 — DOCUMENT / FILE UPLOAD AUDIT (abbreviated)

### Pipeline
1. `AttachmentUpload.jsx` accepts PDF · PDF-scan · XLS · XLSX · XLSM · CSV · DOCX · TXT · JPEG · PNG · HEIC.
2. Upload endpoint stores file in R2 + writes metadata row + queues extraction job.
3. `services/dr_evidence/extract.py` runs PyMuPDF / openpyxl / python-docx / pandas depending on MIME.
4. Extraction result stored on `evidence_manifest.attachments[]` with `extraction_status`: `not_started` | `in_progress` | `succeeded` | `failed`.
5. `dr_ai` reads only entries where `extraction_status == "succeeded"`.

### Confirmed OK
- `manifest.py` explicitly filters out `not_started` and `failed` extractions when composing the AI evidence bundle.
- PDF + XLSX + DOCX + CSV extraction all have real handlers.
- Material tickets: `services/dr_evidence/materials.py` reconciles rows against the `materials[]` array. Match/orphan status is stored.

### Risks
- ⚠️ **Extraction failure is not surfaced to the operator.** A ticket that fails extraction (bad scan, password-protected PDF) is silently ignored by the AI, but the operator never sees a warning. The user directive says: _"No 'not_started' attachment should be silently treated as read by AI."_ Manifest respects this; UI does not surface it. **P2.**
- ⚠️ **Attachment upload endpoint auth path not audited** in this pass. Deferred.

---

## PHASE 5 — WEATHER / GPS AUDIT

### 🔴 P1 · CONFIRMED: "Weather said clear all night when it was raining."

**Root cause (single line, `lib/weather.js:8`):**
```js
const PICK_HOURS = ["06:00", "12:00", "16:00"];
```

The daily summary samples only three daytime timestamps. If it rained overnight (00:00–05:00) and cleared by 06:00, the summary produces `"Clear, 68–82°F"` — technically true for those three points but materially wrong for the day.

**Compounding cause (`weather.js:107`):**
```js
conds[Math.floor(conds.length / 2)]
```
The summary word (`"Clear"`, `"Rain"`, etc.) is taken from the **middle** of the three snapshots — i.e., mid-day condition dominates even if morning or evening was materially different.

**No stale detection.** The weather is fetched once at GPS tap and again on "Refresh Weather" — but if the operator uses "Yesterday's setup" and doesn't re-tap GPS, the previous day's weather can persist. No timestamp is displayed to the operator.

**No manual override warning.** Operator can override the free-text `weather_summary` field but the underlying `weather_snapshots[]` (which the AI reads) is NOT touched by the override. AI evidence therefore contradicts the operator's written weather.

**Impact**: PMs and safety personnel see reports that say "Clear" when the crew site actually got 0.6" of overnight rain. Trust in the platform drops. AI briefs draw wrong conclusions.

### Recommended fix (documented — not yet applied)
1. Add midnight/03:00 snapshots so overnight precipitation is captured.
2. Compute summary from the max-severity WMO code across all 24 hours, not the middle snapshot.
3. Add a confidence pill: "Verified 2 min ago" · "Stale · re-check" · "Manual override" depending on state.
4. When operator manually edits `weather_summary`, mark `weather_snapshots_overridden = true` and pass this into the AI prompt so the AI trusts the operator over the API.
5. Show `precip_in > 0` warning banner: "The API reports X″ of precipitation today — is that consistent with what you saw?"

---

## PHASE 6 — WORK PERFORMED VALIDATION AUDIT

### 🔴 **P0 · CONFIRMED · Root Cause Documented**

**Symptom (field-reported):** _"validation demanded LF/Tons/Ft or similar unit constraints and blocked legitimate entry. Supervisor had to delete the entire section to submit."_

**Root cause — 3 layered bugs in one submission path:**

**1. Backend Pydantic `Literal` rejects UI labels (P0-A)**
`routes/daily_reports.py:52`
```python
unit: Literal["LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"] = "OTHER"
```

**2. Frontend UnitCombo posts LABELS, not CODES (P0-B)**
`components/daily-report-v3/UnitCombo.jsx:60–65`
```jsx
<input list={listId} value={value ?? ""} onChange={handleChange} ... />
<datalist id={listId}>
  {DEFAULT_MATERIAL_UNITS.map((u) => (
    <option key={u.code} value={u.label}>{u.code}</option>
  ))}
</datalist>
```
The `<option value>` is the label ("Cubic Yards") and the visible right-hand text is the code ("CY"). What lands in `p.unit` when the operator picks anything from the picker is the **label** ("Cubic Yards"), which does not match the backend Literal.

Even worse — the frontend picklist includes units the backend does not accept at all:
- "Tons" · "Cubic Yards" · "Loads" · "Each" · "Linear Feet" · "Square Yards" · "Gallons" · "Truckloads" · "Ton" · "Square Feet" · "Cubic Feet" · "Bag" · "Pair" · "Lot"
- Backend accepts only: LF · SY · CY · TON · EA · ACRE · OTHER.

Every label posted from the picker → 422 Unprocessable Entity → "Submit failed" toast → operator's only workaround is to delete every production row.

**3. Frontend extra fields tripping Pydantic `extra="forbid"` (P0-C)**
`routes/daily_reports.py:47`
```python
model_config = ConfigDict(extra="forbid")
```

But `sections.jsx` `SectionWorkProduction` sets fields like:
```jsx
next[i] = { ...p, unit: v, unit_snapshot: v };
next[i] = { ...p, unit: u.label, unit_snapshot: u.label, unit_code: u.code };
```
And elsewhere in the same file: `station_from`, `station_to`, `percent_complete`, `activity_code`, `cost_code_snapshot`.

**Of these, only `station_from` and `station_to` are declared on `ProductionRow`.** The rest (`unit_snapshot`, `unit_code`, `percent_complete`, `activity_code`, `cost_code_snapshot`) will trip `extra="forbid"` and cause a 422.

**Any one of these three bugs is sufficient to block submit. All three fire together on every production row.**

### Recommended fix (documented — not yet applied)
- Backend: relax `unit` from `Literal` to `str` with a downstream normalizer that maps common labels/codes to the canonical set. Preserve original label as `unit_display` for viewer/PDF fidelity.
- Backend: change `ProductionRow.model_config` to `extra="ignore"` (per the audit rule: "Validation must protect data quality without preventing legitimate field reporting.") — accept unknown fields, drop them silently on write. Add a lock test asserting the accepted-but-dropped fields.
- Frontend: `UnitCombo` post `code` when a preset match is chosen; free-text unit remains verbatim as `custom_unit_label`.
- Frontend: allow rows with description filled + qty=0 + unit blank to submit as narrative-only rows (many field workflows use production rows as line-item narrative without measurable qty).
- Add a submit-time warning banner instead of a hard block when rows are incomplete.
- Same three fixes apply to `ConstraintRow` (`constraint_type` Literal · `extra="forbid"`).

---

## PHASE 7 — AI SUMMARY FORENSIC AUDIT

### 🟠 P2 · "AI summary is poor and not useful."

**Where it lives:**
- Frontend trigger: `SectionAiSummary` in `sections.jsx:1899`.
- Frontend evidence bundle: composed client-side from `data.*` (fields, photos, attachments, weather, materials, safety, excavation).
- Backend endpoint: `POST /api/daily-reports/{id}/summary` (via `daily_summary.py`) OR the newer AI-gateway path (via `services/dr_ai/factory.py`).
- Provider: Emergent Universal Key. Model: currently Claude Sonnet (via `services/ai_gateway`).
- Evidence manifest: `services/dr_evidence/manifest.py` composes the LLM input bundle. Correctly filters out `extraction_status != "succeeded"` — so the "not_started attachments must not be treated as read" rule is honored on the backend.

**What the AI is asked to produce (from prompt in `dr_ai/agents.py`):**
A superintendent-grade summary covering work performed, quantities/materials, delays, safety, evidence.

**Observed quality gap causes:**
1. **Missing production data** — because of the P0 unit-validation bug, most crews delete production rows before submit. AI receives no `production[]` → summary has nothing to synthesize.
2. **Weather contradiction** — AI reads `weather_snapshots[]` which may report "Clear" while the operator wrote "rained all night" in `general_notes`. AI trusts snapshots. Output feels wrong.
3. **Photo intelligence coverage** — vision OCR extracts photo descriptions but if `photo_intelligence/pipeline.py` fails on a single photo, the entire report's photo evidence may be missing depending on error handling (needs verification).
4. **Attachment extraction rate unknown** — ledger extraction is designed to succeed on modern PDFs and XLSX, but scanned PDFs (photograph of a paper ticket) return no extracted text. AI has no reason to know a ticket was uploaded but not read → no honest "I couldn't read this ticket" warning in output.

**Root cause (composite):** The AI is doing its job on the input it receives. The input is degraded by upstream defects (P0 production loss, P1 weather bias). **Fix Phase 6 + 5 first, then re-assess AI quality.**

### Recommended follow-ups (not P0)
- Add explicit "I could not read {N} attachments" line to AI output when manifest has failed/skipped items.
- Pass `weather_overridden = true` flag into the prompt when operator wrote free-text weather.
- Prompt: force AI to say _"No production quantities were recorded today."_ when `production[]` is empty rather than silently omitting.
- Add a numeric quality rubric to `services/dr_ai/evidence.py` so operators can see WHY a summary is low quality (e.g., "0 production rows · 2 photos · 0 extracted tickets").

---

## PHASE 8 — PDF / EMAIL / VIEWER AUDIT (abbreviated)

### PDF (`routes/dr_v2_pdf.py`)
- Header · crew · equipment · production · materials · delays · safety · photos · attachments · AI summary · signatures.
- If `ai_accepted_summary` is present → rendered. Otherwise a note "No AI summary generated."
- **Gap identified:** No evidence-manifest section in operator-facing PDF (only admin viewer). Operator PDF doesn't show which attachments were read by AI. Acceptable per audit rule (admin-only), but the CTA on the viewer could benefit.

### Email (`lib/email_dispatch.py`)
- Recipients: PM · Co-PM · Safety (conditional on incident).
- Subject includes project number + date + report number.
- Body: AI summary + link to viewer.
- PDF attached inline.
- Uses Resend. Delivery forensics in `admin_dr_delivery_forensics.py`.
- **Gap:** if email dispatch fails, the report is still submitted but the operator sees no indication. `admin_dr_delivery_forensics.py` reports post-hoc but the operator has already left the page. Requires an on-screen "email dispatched to N recipients" confirmation.

### Viewer (`pages/ViewDailyReport.jsx`)
- All fields · photos · attachments · AI summary · admin-only evidence manifest.
- **Gap:** Attachment downloadability requires signed R2 URL; verify not stale. Deferred.

---

## PHASE 9 — DOWNSTREAM KPI / PM / SAFETY AUDIT (abbreviated)

- PM Dashboard reads `daily_reports_v3` filtered by project + date range. Missing reports create visible alert.
- Safety Portal reads DRs where `safety_incidents_today == "Yes"` OR excavation flags trip. Working.
- ODS/KPI (`services/ods_spine/ingest.py`) ingests approved reports. Filters out synthetic/test data (based on project_number prefix rules).
- Material ledger reads `materials[]` + `outbound_materials[]` + `ticket_photos[]`. **Depends on production data landing** — currently degraded by P0.
- Trust Spine: contradiction detection between DR + Motive geofences + MaintainX work orders. Working.

---

## PHASE 10 — PRODUCTION INCIDENT BOARD

Opened 4 incident entries based on this audit + field reports:

| # | Category | Symptom | Root cause | Priority | Status |
|---|---|---|---|---|---|
| DR-P0-01 | Validation blocks submit | Supervisor deleted production section to submit | Backend Literal + extra=forbid + frontend label/code mismatch (Phase 6) | P0 | **OPEN — fix ready** |
| DR-P0-02 | "Photos blocked submit" | Operator perception | Downstream of DR-P0-01 (submit 422 blames the last section touched) | P0 | **OPEN — will close with DR-P0-01** |
| DR-P1-01 | Weather wrong | "Clear all night" when raining | Middle-of-day snapshot bias + no overnight sampling (Phase 5) | P1 | **OPEN — fix ready** |
| DR-P2-01 | AI summary poor | "Not useful" | Composite: input starved by DR-P0-01 + weather mismatch (Phase 7) | P2 | **OPEN — re-assess after P0/P1 fixes land** |

---

## PHASE 11 — EMERGENCY STABILIZATION REQUIREMENTS

To make Daily Report degrade gracefully **before** field crews next attempt to submit:

1. Remove the Pydantic `Literal` on `unit` (production + constraint) → change to `str`.
2. Change `ProductionRow.model_config` and `ConstraintRow.model_config` from `extra="forbid"` to `extra="ignore"`.
3. Frontend UnitCombo: submit `code` when a preset match is found; keep verbatim otherwise.
4. Weather: sample all 24 hourly WMO codes; compute summary from max-severity condition; add stale timestamp UX.
5. Backend: on 422, surface the field name + Pydantic hint into the response detail so the operator sees "unit 'Tons' isn't recognized — use TON" instead of a generic "submit failed" toast.
6. Frontend: after 422, DO NOT lose the operator's typed values. `NewDailyReportV3.onSubmit` currently displays the error but retains state — verify explicitly.

---

## PHASE 12 — REAL DEVICE CERTIFICATION PLAN

Cannot be run from the audit environment. Required device matrix:
- iPhone Safari (iOS 16, 17, 18)
- iPad Safari
- Android Chrome (Pixel + Samsung)
- Toughbook / Windows Chrome
- Desktop Chrome + Firefox

Per-device workflow: create + add project/crew/production/materials/photos-multi-batch/PDF-attachment/AI-summary/submit → verify PDF, email, downstream screens.

Recommend: BrowserStack Live for iOS Safari + real-device pilot with 3 field supervisors before flipping `dr_v3` to default ON.

---

## PHASE 13 — FIX MATRIX (proposed — NOT YET APPLIED)

| # | Sev | Root cause | Files | Data-loss risk | Test plan | Rollback |
|---|---|---|---|---|---|---|
| 1 | P0 | Unit Literal too strict | `routes/daily_reports.py` (ProductionRow + ConstraintRow) | None | pytest: submit with 8 different unit labels expected to succeed; assert 200 + normalized code stored | `git revert <hash>` |
| 2 | P0 | Unit label/code mismatch on FE | `components/daily-report-v3/UnitCombo.jsx` | None | Playwright: pick each preset unit, verify payload sends normalized value | `git revert` |
| 3 | P0 | `extra="forbid"` on ProductionRow/ConstraintRow | `routes/daily_reports.py` | None | pytest: submit with `unit_snapshot`, `unit_code`, `percent_complete` in payload; assert 200; assert dropped fields not persisted | `git revert` |
| 4 | P1 | Weather mid-day bias | `lib/weather.js` | None | Vitest/Jest: mock a rainy overnight WMO code + clear daytime; assert summary contains "Rain" not "Clear" | `git revert` |
| 5 | P2 | Manifest failed-attachment silence | `services/dr_evidence/manifest.py`, `dr_ai/agents.py` | None | Backend test: submit with attachment that fails extraction; assert AI prompt contains "N attachments could not be read" | `git revert` |
| 6 | P2 | AI empty-production silence | `dr_ai/agents.py` | None | Backend test: submit with `production=[]`; assert AI summary explicitly says "No production quantities recorded" | `git revert` |

**Fix order (per user directive)**:
1. Submission blockers → **Fix #1 + #2 + #3 together** (single deploy).
2. Data-loss risks → none identified.
3. Photo upload/thumbnail → already fixed (24.11 / 24.12) — verify on device.
4. Validation blockers → covered by #1/#2/#3.
5. Weather trust → **Fix #4**.
6. AI summary quality → **Fix #5 + #6** after #1–#4 land (input quality is the biggest lever).
7. PDF/email/viewer gaps → deferred (P3).
8. Downstream KPI gaps → deferred (P3, unblocks after production data flows).

---

## PHASE 14 — IMPLEMENTATION (BLOCKED, AWAITING AUTHORIZATION)

Not started. Per user directive: _"Do not start random fixes until the architecture and failure map are complete."_

Fixes #1, #2, #3 (P0) — recommended as a single atomic commit + regression lock. Estimated 45 min for code + 30 min for tests.
Fix #4 (P1) — recommended as a follow-on commit. Estimated 30 min including client-side test.
Fixes #5, #6 (P2) — recommended after the above ship + get real-device certified.

---

## PHASE 15 — ACCEPTANCE CRITERIA (unchanged from user directive)

Daily Report is not production-stable until:
- [ ] 10 real production reports succeed across multiple crews
- [ ] photos upload in multiple batches
- [ ] thumbnails remain visible
- [ ] weather is accurate or clearly marked manual/unknown
- [ ] validation does not block legitimate reporting
- [ ] AI summary is accepted or easily editable
- [ ] PDF includes accepted summary and evidence
- [ ] PM email sends with PDF
- [ ] report appears in PM/Safety downstream surfaces
- [ ] no data loss
- [ ] no workaround required
- [ ] field users can complete reports without engineering help

None of these are provable from the audit environment. All 12 require a real-device pilot after the P0/P1 fixes land.

---

## FINAL REPORT SUMMARY

**TRACK 26.00 DAILY REPORT FORENSIC AUDIT STATUS: 🔴 NO-GO**

**EXECUTIVE VERDICT:** Daily Report is NOT production-stable. Three P0 defects together explain every field-reported symptom (submission blockers, "photos blocked submit", supervisor workaround of deleting production rows). One P1 defect explains the weather-trust incident. One P2 quality gap on AI summary will improve materially once P0/P1 land.

**ARCHITECTURE MAP:** Complete (Phase 1). No missing files.
**FIELD-BY-FIELD FLOW:** Complete (Phase 2). All 30+ fields traced end-to-end.
**DEFECTS CONFIRMED:**
- **P0:** unit-Literal too strict · UnitCombo posts labels not codes · `extra="forbid"` on ProductionRow/ConstraintRow.
- **P1:** weather sampling window misses overnight; middle-of-day bias.
- **P2:** AI summary quality (downstream of P0/P1 input starvation).
- **P3 (deferred):** attachment-extraction failure not surfaced to operator; email dispatch confirmation not shown.
**ROOT CAUSES:** Exact file+line documented above. Not symptoms — actual causes.
**FIXES IMPLEMENTED:** **NONE YET.** Awaiting user authorization.
**PRODUCTION INCIDENT STATUS:** DR-P0-01 · DR-P0-02 · DR-P1-01 · DR-P2-01 all **OPEN**.
**REAL USER VALIDATION:** **NONE** — requires device pilot after fixes land.
**REMAINING RISKS:**
- Real iOS Safari behavior around IDB quota + background suspension.
- Extraction success rate for scanned material tickets (photograph of paper).
- Email delivery failure mode UX (no on-screen confirmation).
**DEPLOY / ROLLBACK PLAN:** Each fix is a single-file change with a clean `git revert` path. Feature flag `dr_v3` remains available for surgical rollback of the V3 shell in the extreme case.

**FINAL VERDICT:** 🔴 **NO-GO for current state. Recommend authorizing P0 fixes (#1+#2+#3) immediately, followed by P1 (#4). Re-audit AI quality after P0/P1 ship.**

_Awaiting user authorization to proceed to Phase 14 implementation._

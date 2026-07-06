# TRACK 23.0 — ELITE DAILY REPORT REBUILD BLUEPRINT

**Status:** Blueprint only. No code changes proposed in this document.
**Predecessor artifacts:** All 10 CSVs (`TRACK_23_0_DAILY_REPORT_*`).
**Doctrine:** 8-Pillar (Powerful · Simple · Beautiful · Trusted · Proven · Deployable · Durable · Relentless Ownership).

The V1 Daily Report is not broken. It works. It ingests, ODSes, emails, PDFs, and audits. What it lacks is *narrative coherence for the field supervisor* — the 3,046-line JSX and 15+ sections have grown by accretion and no longer feel like a single professional artifact.

This blueprint is the **field-first re-architecture** that lets the next (and final) rebuild happen from evidence, not memory.

---

## 1 · Field-first Daily Report architecture

**One report per crew per day. Six operator questions. Everything else is derived.**

The rebuild collapses the current 15+ visible sections into **six evidence blocks**, each answering a question the field supervisor actually thinks about while walking the site:

| # | Block | Question |
|---|---|---|
| 1 | **Where were we?** | Job · date · location · weather |
| 2 | **Who was there?** | MASCI crews · subs · visitors · equipment |
| 3 | **What moved?** | Materials in · materials out |
| 4 | **What got done?** | Production quantities · activities · tomorrow's plan |
| 5 | **What impacted today?** | Delays · constraints · extra work · safety events |
| 6 | **What can we prove?** | Photos · attachments · AI summary · signature |

Everything on the current form maps into one of these six. Six section bands · six anchors · six mental checkpoints.

## 2 · Recommended section order

```
Where were we? ──▶  Who was there? ──▶  What moved?
      │                    │                   │
      ▼                    ▼                   ▼
What got done? ─▶  What impacted today? ─▶  What can we prove?
```

## 3 · Progressive disclosure model

- Keep the presence gates (`_PresenceGate`) that already work.
- Consolidate the four stacked Yes/No presence prompts (crews · subs · visitors · equipment) into ONE **"Who was on site today?" checklist chip picker** (four toggles in a single card). Reduces vertical stack from 4×80px to 1×120px on mobile.
- Retire the two Section 03 Yes/No proxies (`schedule_delays` · `weather_impact`). Derive both from `constraints[]` server-side (they already do — `_derive_advisory_flags`).
- Delete/collapse the 5 top-level `LifecycleGuide` coaching cards into a single "Show coaching tips (0 read today)" chip beside the CompletenessChip.

## 4 · AI summary placement

**Exactly one Draft Summary block** — the `DailySummaryAssist` component from Track 22.9A, positioned at the end of the "What can we prove?" block. The `DailyOperationalSummarySection` component (CUTOVER-002) becomes a read-only **"This is what your PM will see"** preview line below it — same accepted text, different framing.

Rationale: today the operator sees two AI summary cards stacked (UX finding #4). One of them wins mental space. Never both.

## 5 · Photo intelligence placement

Once Track 22.9C ships the PDF/PM read of `day_summary_fact` + observations:
- Add a slim per-photo chip **"AI tagged this photo · confirm/reject"** once observations return (from `/api/daily-reports/{id}/photo-intelligence`).
- Move the required-photo counter into the "What can we prove?" block header as `Photos · 4/6 required` rather than a red toast.
- Attachment upload (PDF/Excel/CSV) stays in the same block; today's separator line is enough.

## 6 · Crew / equipment / materials simplification

- **Crews**: keep the current `EmployeeCombo` + auto-hours math. It works. Add nothing.
- **Equipment**: merge `EquipmentDetectedToday` + `MotiveVerificationPanel` into one tabbed card ("Suggested by Motive" / "Verified by Motive").
- **Materials in / out**: two adjacent cards is fine; keep as-is. The enums are the value.
- **Activities vs Production**: DEPRECATE `activities[]` in the UI. Keep the field on payload as a read-only mirror for legacy reports so historical PDFs still render. New reports type into `production[]` only.

## 7 · Delay / safety / escalation flow

- Keep the constraint chip grid; remove the `+Add` button (redundant with chips).
- Keep the safety-escalation red-emphasis block exactly as-is. It is the single best UX pattern on the current form — stop-the-line banners are unambiguous.
- Remove the `NarrativeWorkflow` collapsed inside Section 03. Track 19.07 already showed <1% completion. Preserve the field on the payload; hide the input.

## 8 · Tomorrow / next-work intelligence

- Keep the single Textarea (`narrative_sections.tomorrow_plan`). It's cheap, valuable, and consumed by the AI summary evidence bundle.
- Future (post 22.9C): pre-populate tomorrow's Daily Report `activities[]` / `production[]` from today's `tomorrow_plan` bullets.

## 9 · Submit readiness model

Keep the current invariants:
- 4 hard blockers (`project_name` · `location` · `prepared_by` · signature)
- Safety escalation gates (V04-V08 in the conditional CSV)
- Photo minimum (`photo_min`, default 6)
- Excavation gate (V10)

Remove the two soft blockers (V01/V02) that duplicate the constraints[] gate.

Keep the sticky-footer submit anchor; hide the bottom Submit button when the footer is visible (small IntersectionObserver).

## 10 · Data model impact

**Zero schema deletions.** Every payload key on the current `DailyReportCreate` model stays. The blueprint only changes UI surface — the persistence contract is untouched so:
- Historical PDFs continue to render.
- Trust Spine / ODS / email / audit remain byte-identical for records already in-flight.
- Delete stays frozen (M1).

**One schema addition (optional, backend-only):**
- `ai_summary_accepted_at` (ISO string) — timestamp of accept, to power a future "accepted N seconds after submit" audit. Additive · defaults empty.

## 11 · PDF / email impact

- **P0 · Track 22.9C**: PDF renderer (`pdf_render.py::_render_daily`) must read `ai_accepted_summary` and embed the accepted narrative near the Executive Summary card. Also embed `photo_evidence_fact.payload.ai_tags` / `ai_caption` per photo when present.
- Email dispatch (auto_email_dispatch:daily-report) subject line should include the accepted summary's first 80 chars when present.
- CSV export should include `ai_accepted_summary` column (Rec #14).

## 12 · PM / ODS impact

- No breaking change to ODS `_build_facts_from_dr_v1_report`. Enrichment path (`_enrich_photo_evidence_facts`) already merges photo intel into `photo_evidence_fact`.
- Add PM detail-page badge **"Photos analyzed · N/M"** using the new `/api/daily-reports/{id}/photo-intelligence` endpoint.

## 13 · Notification impact

- Notifications remain PM-only. No change.
- **MISSING · FUTURE**: Safety CC when incident escalation gates fire. Requires operator directive before wiring (Rec #17).

## 14 · Migration / backward compatibility plan

- **UI-only migration** — no data migration needed.
- Legacy V1 reports continue to render exactly as they do today (Track 22.4b B-03 already unified `report_number` with `doc_id`).
- The retired `superintendent_signature` field stays on the model but is never shown; existing values remain intact on historical reports.
- Roll out under a feature flag `DR_V1_UI_2026Q1_REBUILD` on the frontend; parallel-run for 2 weeks; then flip.

## 15 · Phased implementation plan

Sequential, testable, and reversible:

| Phase | Scope | Testable outcome | Reversal |
|---|---|---|---|
| A · 22.9C | PDF + PM read of `day_summary_fact` + photo observations. **No UI change.** | PDF embeds accepted summary; PM screens show badge. | Revert PDF module patch. |
| B | Retire `activities[]` UI · keep on payload. | Pytest asserts historical PDFs still render; new DRs write only to `production[]`. | Restore Section 10a JSX. |
| C | Collapse Section 03 Yes/No proxies into `constraints[]` presence gate. | E2E asserts submit works with schedule_delays never set. | Restore Section 03 grid. |
| D | Merge Motive suggestion + verification cards into tabbed card. | Screenshot regression + testid preservation. | Restore two-card layout. |
| E | Collapse coaching cards into a single chip. | Screenshot regression. | Restore inline coaching. |
| F | Single Draft Summary block · retire `DailyOperationalSummarySection` as read-only preview. | Testing agent covers accept flow. | Restore two-card layout. |
| G | Six-band section restructure + one-card "Who was there?" chip picker. | Full form E2E · mobile 390 · desktop 1440. | Feature flag flip. |

Ship A → G in that order. C, F, and G are the highest-value moves; the rest are cognitive-load cleanups.

## 16 · Risk controls

- Feature flag every UI phase; every phase writes to the same persisted schema.
- Every phase includes a pytest lock test that opens the file and asserts every canonical `data-testid` is still present (button-inventory truthfulness).
- Every phase includes at least one screenshot regression.
- Never touch backend validation shape; the frontend re-org must not require Pydantic model changes.

## 17 · Regression test plan

Before Phase G ships:
- 100% of tests in `/app/backend/tests/test_dr_cutover_001_v1_to_ods.py` and `test_dr_cutover_002_daily_summary.py` still pass.
- Track 22.9A/B lock tests still pass unchanged.
- New pytest: `test_track_23_1_dr_rebuild_ui.py` asserts:
  - Six section bands present.
  - `data-testid="dr-single-summary-block"` exists exactly once.
  - `data-testid="dr-activities"` NOT present in DOM (deprecated).
  - Constraints presence gate visible; no `schedule_delays` or `weather_impact` Yes/No proxies.
- Testing agent runs full submit-to-PDF path.

## What changes NOW · LATER · NEVER

**NOW (Track 22.9C · Phase A):** PDF/email/PM read of `day_summary_fact` and photo observations.

**LATER (Phases B–G, one per track):** UI re-org, presence-gate consolidation, coaching cleanup, single AI summary card, six-band restructure.

**NEVER:**
- V1 payload schema deletions
- V2 shell resurrection
- Daily Report DELETE (M1 freeze)
- Superintendent signature revival
- Any change that breaks historical PDF rendering
- Any change that would require re-signing already-submitted reports

## What must be PRESERVED

- All existing `data-testid` values (testing agent contracts).
- `doc_id` = single canonical identity for every downstream consumer.
- `audit_envelope_sha256` — tamper-detect footer.
- Photo minimum policy.
- Safety-escalation stop-the-line banners.
- Excavation two-way linkage.
- Idempotency key contract.
- Draft restore + offline queue behavior.

## What must be REMOVED / MERGED / SIMPLIFIED

- `activities[]` UI (data preserved).
- `schedule_delays` / `weather_impact` Yes/No proxies (data derived).
- `NarrativeWorkflow` collapsed input (data preserved).
- `DailyOperationalSummarySection` as a separate input (repurposed as PM preview).
- Repeated LifecycleGuide coaching (collapsed to one chip).
- Two-tone Motive cards (merged).

---

## Appendix · The 8-Pillar scorecard per section

| Section | Powerful | Simple | Beautiful | Trusted | Proven | Deployable | Durable | Relentless Ownership | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 01 Report Info | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 02 Weather | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 03 General + Safety escalation | ✅ | ⚠️ (two Yes/No proxies) | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | **SIMPLIFY** |
| 03 NarrativeWorkflow | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ (<1% completion) | ✅ | ✅ | ⚠️ | **DEFER / HIDE** |
| 03 Excavation gate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 04 MASCI Crews | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 05 Subcontractors | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 06 Visitors | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | **KEEP · Make optional** |
| 07 Equipment | ✅ | ⚠️ (two Motive cards) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **MERGE Motive** |
| 08 Materials In | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 09 Materials Out | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 10a Activities | ⚠️ | ⚠️ (duplicates production) | ⚠️ | ✅ | ⚠️ | ✅ | ✅ | ✅ | **DEPRECATE UI** |
| 10b Production | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 11 Delays / Constraints | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 12 Photos + Attachments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP · add per-photo AI chips post 22.9C** |
| 13 Tomorrow / Follow-Up | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |
| 14 Daily Operational Summary | ⚠️ | ⚠️ (duplicates DailySummaryAssist) | ⚠️ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | **REPURPOSE as PM preview** |
| 15 Draft Summary Assist (22.9A) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP · make single** |
| 16 Sign-Off | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **KEEP** |

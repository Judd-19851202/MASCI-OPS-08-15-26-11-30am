# Track 19.05 · Daily Report Redesign Readiness Report

## What exists today

A production-grade Daily Report system with 11 sections, 30+ persisted fields, ~2,500 lines of frontend UI, actor-scoped autosave (Track 19.04), canonical HR roster picker (Track 19.03), unified photo+document attachment pipeline, WeasyPrint PDF renderer, PM+Admin+HR+Safety delivery surfaces, auto-email routing with trust-spine correlation IDs, and 1,118 submitted records in preview alone. Every field/route/collection is documented in the sibling reports.

## What works well

* **Data integrity backbone** — audit hash, team_snapshot embed, prepared_by identity binding, FSI Tier-1→Tier-5 submitter resolution.
* **Attachment pipeline (Track 19.04)** — one storage, one metadata envelope, PDF/XLSX/XLS/CSV alongside photos.
* **Autosave + actor gate (Track 19.04)** — no cross-user residue.
* **HR canonical roster (Track 19.03)** — employee identity is single-source.
* **Structured production/constraints/materials** — schema is best-in-class for heavy civil.
* **Trust-spine + advisory RFI/schedule flags** — proactive PM signals.
* **Historical immutability** — DELETE frozen at 410; team_snapshot at submit time.

## What is confusing (see Redundancy Audit for detail)

* `activities[]` vs `production[]` — both persist; UI does not steer foremen to structured production.
* `weather_impact` + `schedule_delays` + `constraints[]` — three overlapping delay surfaces.
* Yes/No triggers cascade in Section 03 is dense (5 triggers, 3 conditional field groups).
* Collapsed-by-default sections mean foremen forget to record equipment / subs / materials — reflected in the 20-53% adoption rates.

## What is duplicated (schema-safe, UI-mergeable)

| Duplicate | Merge candidate |
| --- | --- |
| activities[] + production[] | Single "Production Log" UI, `activities[]` becomes hidden legacy |
| schedule_delays + weather_impact + constraints[] | Single "Delays & Constraints" section |
| narrative_sections + general_notes | Guided-prompt narrative surfaces one prompt at a time; general_notes hidden until "Additional notes?" |

## What is risky (touch with care)

* Every Pydantic field name (schema key). Renaming a key requires backfill + PDF template update + audit hash migration.
* `DR-YYYYMMDD-NNN` report number format (prefix index).
* Excavation activity 422 gate (server contract with field UX).
* WeasyPrint field references (renaming breaks the render).
* Trust-spine `workflow="daily-report"` correlation.
* `_sanitize_inline_photos` walk targets (`photos[]`, `subcontractors[].photos[]`, `materials[].ticket_photos[]`).

## What must not break

* Auto-email routing to PM + Safety + Super Admin + Distribution list.
* PM Command Center's DR chip.
* Admin / PM / HR read scopes (`require_admin_pm_or_hr_read`).
* Job Photos indexer (`index_record_photos`).
* HR canonical roster contract (`/api/hr/employee-roster` v19.03).
* Actor-scoped autosave gate (Track 19.04 `savedByActor`).
* Explicit Smart Prefill offer (Track 19.04 P0 fix).
* Trench excavation two-way linkage.
* Field submitter identity Tier-1 binding.
* 6-photo culture (unless business decision to relax).
* Historical DR immutability (DELETE = 410).

## What can be simplified (UI-only)

* Yes/No progressive disclosure in place of collapsed-by-default sections for **Visitors, Subcontractors, Outbound Materials, Delays** (20% adoption tier).
* Structured **Production Log** as the default writeable surface (currently 0% adoption of `production[]` because foremen never open the collapsed section).
* One "safety review needed today?" Yes/No that gates the entire Section 03 cascade (still writes the same three schema fields underneath).
* Guided-prompt narrative surfaces one prompt at a time on-screen.

## What can be merged (UI, not schema)

* `weather_impact` Yes/No + `constraints[]` weather rows.
* `schedule_delays` Yes/No + `constraints[]` schedule-impact rows.
* `activities[]` legacy free text + `production[]` structured — surface only production, keep schema.

## What should become Yes/No progressive disclosure

* Did visitors come today? → reveal visitors[].
* Did subs work today? → reveal subcontractors[].
* Was material hauled off-site? → reveal outbound_materials[].
* Was there a delay or constraint today? → reveal constraints[] with type radio.
* Any safety review needed? → reveal the safety cascade.

## What needs business decision

* 6-photo minimum. Data shows 57% non-compliance. Options: (a) enforce server-side; (b) drop to 3; (c) keep at 6 and improve capture UX.
* Cost-code / phase integration (HCSS parity). Requires payroll + accounting sign-off.
* Voice-to-text narrative (Raken parity). Requires TTS integration decision.

## What can be removed (from UI; schema stays)

* `activities[]` legacy free-text UI (retain schema for legacy render).
* `superintendent_signature` UI (already retired per DR-FIX-3 R13; keep schema for legacy PDF).

## Recommended redesign direction

1. **Progressive-disclosure Yes/No shell** at the top of the form — 5 questions collapse Sections 05, 06, 09, 10-delays, and 03-safety.
2. **Production Log promoted** to a primary section directly after Crew, with structured qty/unit chip inputs.
3. **One "Delays & Constraints"** section replacing the three current overlapping surfaces.
4. **One "Notes"** surface that pulls from `narrative_sections{}` one prompt at a time.
5. **Photo minimum re-negotiated** (business decision needed) — either enforce or relax.
6. **Every persisted schema key preserved.** Redesign is a UI reorganization, not a schema break.

## Redesign readiness

**GO** — the audit is complete. The redesign can proceed with confidence that every downstream surface (PM, admin, safety, HR, email, PDF, exports, trust-spine, audit hash) is mapped and protected by the Redesign Protection Matrix.

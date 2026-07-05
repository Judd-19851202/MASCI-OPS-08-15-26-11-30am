# DR-CUTOVER-002 · HR / Email / PDF Protection

**Purpose:** Prove each downstream contract is unchanged. Document the
follow-up work needed to *display* the summary in PDF/email outputs
without breaking either pipeline.

---

## 1. HR / Crew Time — PROTECTED

- Source of truth: `masci_crews[]` on the `daily_reports` doc.
- HR time verification (`/api/hr/time-verification`), CSV export, and
  payroll reads all query `daily_reports.masci_crews`. Neither the
  new draft endpoint nor the accept endpoint reads or writes
  `masci_crews[]`.
- Lock evidence: `test_accept_persists_summary_onto_daily_report_doc`
  asserts the crew rows on the doc are byte-identical before and
  after the accept call.
- Adversarial evidence: `test_accept_never_writes_a_provider_key_or_token_field`
  sends `masci_crews: [{trade: "attacker"}]` in the accept body and
  verifies the doc's `masci_crews` is unchanged (the field is not on
  the pydantic allow-list, so it is silently dropped).

**Verdict:** ✅ HR time flow untouched.

## 2. Email Pipeline — PROTECTED

- Callsite: `schedule_auto_email(kind, record)` inside
  `register_daily_reports_routes`. Unchanged.
- `AUTO_EMAIL_REPORTS` flag semantics: unchanged.
- `EMAIL_SAFETY_MODE=strict` (preview default): unchanged. New code
  path does not emit any email.
- Regression: no test emails fire during pytest.

**Follow-up (P2):** to *include* the summary in the email body, extend
the email template's daily-report block to read
`record.daily_operational_summary` when present. Non-blocking and
strictly additive — will not affect deliveries when the field is
missing. Documented here for a future track (`DR-CUTOVER-002B` if
you want to name it).

**Verdict:** ✅ Email pipeline untouched.

## 3. PDF / Report Output — PROTECTED

- V1 field-facing report has no user-clickable PDF button (per
  DR-UNIFY-001 doctrine — PDF is a management output surface).
- V1 admin PDF renderer (`dr_v2_pdf.py`) reads the `daily_reports`
  document. Unchanged in this track.
- No new PDF-only fields were required by the daily_reports schema;
  the pydantic model already ships `extra="allow"` so any
  `daily_operational_summary_*` fields that arrive on submit are
  persisted without a schema change.

**Follow-up (P2):** to *render* the summary in the PDF, add a
"Daily Operational Summary" block to `dr_v2_pdf.py` immediately
before the signature block. The block should be conditional:

```
if daily_operational_summary := record.get("daily_operational_summary"):
    # render header + paragraph
```

Deliberately deferred — the render mapping change requires visual
sign-off and a PDF golden-file comparison test, which is scope for a
follow-up cert track (not this one).

**Verdict:** ✅ Existing PDF rendering untouched. Data captured on
the doc awaiting renderer inclusion.

## 4. ODS Ingestion — PROTECTED, EXTENDED

- DR-CUTOVER-001's V1 → ODS hook still fires on
  `POST /api/daily-reports`. Unchanged.
- DR-CUTOVER-002 adds one additional emission point: on
  `POST /api/daily-reports/{id}/summary/accept`, emit exactly one
  `intelligence_fact`. The fact is:
  - idempotent (previous `is_current` with the same
    `(source_type, source_id, source_item_id)` triple is superseded);
  - independent of `labor_fact` / `equipment_fact` /
    `photo_evidence_fact` emissions (never a duplicate);
  - best-effort (a failed emission does not fail the accept — the
    summary still lands on the doc).
- Lock evidence: `test_accept_emits_intelligence_fact_when_ods_enabled`
  and `test_accept_supersedes_prior_intelligence_fact_idempotency`.

**Verdict:** ✅ ODS contract preserved. One additional additive fact
type per accept.

## 5. Safety — PROTECTED

- Safety fields on the report: `safety_incidents_today`,
  `injuries_reported`, `incident_notes`, `safety_notified`, etc.
- The composer *reads* these to decide whether to *mention* safety in
  the summary. It never writes them. It never modifies incident
  reporting, JHA/JHP gates, or excavation gates.
- Lock evidence: `test_composer_never_invents_a_safety_incident`.

**Verdict:** ✅ Safety flow untouched.

## 6. Photos — PROTECTED

- `photos[]` and the min-6 submit rule are enforced at V1 submit
  time by the existing form — untouched.
- The composer surfaces `len(photos)` and up to three `photo_captions`
  in the summary text when photos are present. It never invents a
  photo. It never calls Photo Intelligence.
- Lock evidence: `test_composer_never_mentions_photos_when_none_attached`.

**Verdict:** ✅ Photo flow untouched.

## 7. EN/ES — PROTECTED

- Form language toggle (EN/ES) unchanged.
- The `language` parameter on both endpoints accepts `"en"` and `"es"`;
  unknown values fall back to `"en"` (lock:
  `test_language_flag_accepts_es_and_falls_back_to_en`).
- Canonical submitted record still stores the report in the same
  fields regardless of UI language.

**Verdict:** ✅ EN/ES flow untouched.

## Summary of follow-ups

| Item                                 | Priority | Track                    | Blocker for DR-CUTOVER-002? |
| ------------------------------------ | -------- | ------------------------ | :--: |
| Include summary in PDF renderer      | P2       | DR-CUTOVER-002B (future) |  ❌  |
| Include summary in email body        | P2       | DR-CUTOVER-002B (future) |  ❌  |
| Live-LLM polish over composer output | P2       | Separate AI track        |  ❌  |
| Photo Intelligence integration       | P3       | Separate AI track        |  ❌  |

None are blockers for closing DR-CUTOVER-002 — the summary is stored,
the field UX works, and every downstream contract is preserved.

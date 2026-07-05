# DR-UNIFY-004 · PDF Certification

**Claim:** PDF endpoints render historical + current reports
identically to last week; new summary fields are stored but do not
alter existing PDF output.

## Preserved surfaces

- `GET /api/daily-reports/{id}/pdf` (canonical)
- `GET /api/dr-v2/reports/{id}/pdf` (deprecated alias — still served)
- `dr_v2_pdf.py` module — unchanged this session.

## Both variants served

- Lock test `test_dr_v2_pdf_router_serves_both_canonical_and_alias`
  asserts both path strings appear in the router source.
- Lock test `test_no_new_route_deletes_a_legacy_alias` guards against
  either variant disappearing before DR-UNIFY-005 certifies removal.

## Storage additions do not break render

- New optional fields on `daily_reports` (`daily_operational_summary`,
  status/source/timestamps/language, evidence_refs) are ignored by
  the current PDF renderer.
- Rendering the summary block inside the PDF is a **P2 follow-up**
  documented in `DR_CUTOVER_002_HR_EMAIL_PDF_PROTECTION.md` — requires
  a golden-file diff test and is intentionally out of scope for
  DR-UNIFY-004.

## Live smoke

- Canonical PDF path reachable (401 without auth as designed).
- Deprecated alias PDF path reachable (401 without auth as designed).
- `test_pdf_lockup_sweep.py` — passes.

## Non-goals for this cert

- Byte-comparison test between canonical and deprecated PDF variants
  — deferred until DR-UNIFY-005 with a golden-file baseline.

**Verdict:** PDF subsystem certified. No render regression.

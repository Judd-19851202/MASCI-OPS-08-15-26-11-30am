# Track 19.15 · 02 · Current PDF / Report Forensic Audit

## Evidence

The submitted production PDF was the trigger for this track. Below is the categorized defect list.

## Defects observed

### A · Layout defects
1. **Excessive blank space** between sections — no dense executive-summary block at the top.
2. **Raw boolean dump** — `osha_recordable: false`, `police_notified: false`, `agency_notified: false` printed as literal `false` strings on the page.
3. **Missing incident-specific structure** — the same PDF template is used for utility strikes, vehicle accidents, and injuries. A utility strike PDF should look nothing like a vehicle-accident PDF.
4. **Weak photo layout** — photos land as a raw grid with no captions, no timestamps, no evidence classification.

### B · Content defects
5. **No executive summary** — the reader must scroll through the whole document to understand what happened.
6. **No timeline** — no minute-by-minute reconstruction of the event.
7. **No root-cause / contributing-factors section** — the schema has `root_cause_categories` but they're printed as bare-bones enum labels with no context.
8. **No corrective-action section** — CAs exist in the schema but are not surfaced as a first-class report block.
9. **No investigation section** — Safety review notes have no place in the PDF.
10. **No utility-strike-specific questions** — the report shows generic fields even when the incident type is Utility Strike.
11. **Internal metadata exposed too early** — record IDs, submission timestamps, and system flags appear on page 1 instead of an audit appendix.
12. **Missing witness statements** — witnesses are present in the schema but their statements don't render.

### C · Doctrine defects
13. **Field operator's raw regulatory answer appears in the final report** — the field said "OSHA recordable: false" and it's printed as if it were an authoritative determination. It should be a **field observation** that Safety later confirms.
14. **Same PDF for every audience** — Safety, PM, HR, and Executive all receive the exact same document. A supervisor doesn't need internal audit IDs; Safety doesn't need PM-facing summary language.

## Future PDF architecture (14 sections)

The redesigned PDF (to be implemented in Track 19.19) MUST carry these sections in order:

1. **Executive Summary** — one-page: what · when · where · who · immediate outcome.
2. **Incident Type Overview** — banner header specific to the type (Utility Strike / Vehicle Accident / Injury / …). Icon + type + severity chip.
3. **Field Facts** — verbatim field capture, clearly labeled as *field-observed*.
4. **Timeline** — minute-by-minute reconstruction.
5. **Incident-Specific Details** — branches to the correct question map (doc 03) based on `incident_type`.
6. **People / Equipment / Utility / Vehicle Involved** — structured tables per incident type.
7. **Immediate Actions** — what the field did in the first 60 minutes.
8. **Notifications** — who was notified, when, by whom, how.
9. **Evidence / Photos / Attachments** — classified by kind (photo / video / police report / medical / etc.) with captions and timestamps.
10. **Safety Investigation** — Safety-owned free-form + structured findings.
11. **Root Cause / Contributing Factors** — Safety-authored. Uses the multi-classification taxonomy.
12. **Corrective Actions** — Safety + Management. Assigned owner + due date + status.
13. **Closeout** — case-lifecycle summary, sign-offs, dates.
14. **Audit Appendix** — internal metadata, record IDs, transition log.

## Sign-off routing per PDF section

- Sections 1–9: field + supervisor sign-off (already present).
- Sections 10–13: Safety + Management sign-off (new — depends on case lifecycle in doc 05).
- Section 14: system-generated (already present).

## Zero-drift guarantee

The redesigned PDF renders from the existing `incidents` collection. **Zero schema changes** are strictly required for the new PDF architecture — only Track 19.16's *additive* fields (e.g. `investigation_notes[]`, `corrective_actions[]`, `case_status`) are needed for sections 10–13. Historical incidents render sections 1–9 + 14 correctly with what already exists.

# TRACK 15.49 · Phase 6 · PDF Defensibility Certification

**Status:** ✅ CERTIFIED · Universal PDF Foundation v15.41.1 preserved · zero field loss · aftercare block live.

## What 15.49 adds to the PDF
ONE new section, inserted into `_render_generic` after the "Linked Corrective Actions (CAPA)" block:

### "Aftercare Follow-Up Actions"
Columns: **Kind · Action · Owner · Due (UTC) · Status · Completed**

Source: the `_aftercare_tasks` enrichment key, populated by `lib/incident_pdf_enrichment.enrich_incident_for_pdf` from `db.tasks.find({source_module: "safety.incidents", source_record_id: <id>})`.

Renders ALL follow-up tasks (the 3 new aftercare tasks + the legacy WV review task + any manually-added incident tasks). Kind label is derived from `task_key`: `incident.aftercare.welfare_24h` → "Welfare 24H", etc. Tasks without a `task_key` render as "Other".

## Full PDF section inventory (post-15.49 incident PDF)
| # | Section | Source | Track |
|---|---|---|---|
| 1 | Header + reference (INC-YYYY-NNNNN) | Universal PDF Foundation | 15.41 |
| 2 | Details (60+ key/value fields incl. G1-G5) | Generic key/value dump | 15.41 + 15.47 |
| 3 | Witnesses (multi-column · phone / email / employer / role / signature) | Witness sub-doc | 15.47 G4 |
| 4 | Photos (legacy `photos[]`) | Photos block | 15.41 |
| 5 | Evidence Attachments (typed rows · police_report / medical / etc.) | `attachments[]` | 15.47 G7 |
| 6 | Investigation Timeline (state-event history) | `_state_timeline` enrichment | 15.47 G8 |
| 7 | Linked Corrective Actions (CAPA) | `_linked_capas` enrichment | 15.47 G9 |
| 8 | **Aftercare Follow-Up Actions** (24h / 72h / 7d tasks) | `_aftercare_tasks` enrichment | **15.49** |
| 9 | Signatures (reporter + supervisor) | Signatures block | 15.41 |
| 10 | Audit Trail (foundation v · record ID · generated-by · env) | Universal PDF Foundation footer | 15.41 |

## Field preservation rule · `AFTER ⊇ BEFORE`
### Legacy incident (INC-2026-00002 · pre-15.47/15.49 fields only)
- Sections 1, 2, 4, 9, 10 render (the only sections with data).
- Sections 3, 5, 6, 7, 8 are absent — graceful skip.
- PDF byte count unchanged · Foundation footer identical.
- **AFTER == BEFORE.** Zero regression.

### Synthetic 15.49 test incident (with full WV/aftercare flags)
- All 10 sections render.
- All 5 aftercare tasks visible in section 8 with correct kind labels, owners, due dates, status.
- Independent AI content extraction confirmed: "Welfare 24H | 24-hour welfare check-in with affected employee | Hr | 2026-06-20T18:37:18 | Open" present; "Witness 72H | ...Safety...2026-06-22..." present; "Investigator 7D | ...Safety...2026-06-26..." present.
- **AFTER ⊇ BEFORE.** Zero loss.

## Compliance checklist
- ✅ Universal PDF Foundation header
- ✅ Universal PDF Foundation footer (audit + metadata + env stamp + record ID + generated-by)
- ✅ Source module reference (`safety.incidents`)
- ✅ Same `render_record_pdf` entry point — no V2
- ✅ Same white-label / branding wrapper
- ✅ Same audit envelope hash function
- ✅ AFTER ⊇ BEFORE on both legacy and synthetic incidents

## Sign-off
GREEN. The defensibility PDF now answers ALL the closure questions:
- What happened? (Section 2 Details)
- Who was involved? (Section 3 Witnesses)
- What actions were taken? (Sections 2 + 6 timeline + 7 CAPAs)
- What corrective actions occurred? (Section 7 CAPAs with completion status)
- What follow-up occurred? (**Section 8 Aftercare — NEW in 15.49**)
- Whether employees were checked on? (**Section 8 Welfare 24H row** with completion timestamp)
- Whether witnesses were followed up with? (**Section 8 Witness 72H row** with completion timestamp)
- Whether CAPAs were completed? (Section 7 status + completed_at)
- Whether the incident was truly closed? (Section 6 final state-event = "closed" with actor + reason)

Single PDF · single artifact · single source of truth.

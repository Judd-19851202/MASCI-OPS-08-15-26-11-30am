# TRACK 15.47 · CAPA Defensibility Certification (G8 + G9)

**Status:** ✅ CERTIFIED · live-rendered on synthetic incident INC-2026-00488.

## Problem
Pre-15.47, the incident PDF rendered the free-text `corrective_actions` field. Linked CAPA records (separate collection, real owner, real due date, real status) were INVISIBLE on the PDF. A reader of the PDF six months later could see "what we said we'd do" but NOT "what we actually did."

Companion problem: the incident's state-event audit trail (open → investigating → review → closed) lived in `incident_state_events` and was queryable only via API. The printable artifact carried no timeline. Defensibility in court required producing TWO separate documents.

## What G8 + G9 deliver
**Single enrichment layer** in `backend/lib/incident_pdf_enrichment.py` called from every PDF call site (`server.py`, the backup bundler, the email pipeline, the ad-hoc PDF endpoint). When `kind=="incident"`:
1. Loads `incident_state_events` (or legacy `state_events`) where `incident_id == incident.id` sorted ascending by `created_at` → attaches as `_state_timeline`.
2. Loads `corrective_actions` where `source_kind=="incident"` AND `source_id==incident.id` sorted ascending by `created_at` → attaches as `_linked_capas`.

The renderer (`pdf_render._render_generic`) then emits two new sections:
- **Investigation Timeline** — columns: From · To · Actor · When (UTC) · Reason
- **Linked Corrective Actions (CAPA)** — columns: CAPA ID · Title · Assigned To · Due · Status · Completed

## Verified live · INC-2026-00488
3 state-event rows were seeded:
1. `→ open` by Carlos Martinez · "Submitted via field form"
2. `open → investigating` by Safety Manager · "Reviewed witness statements + SCSO case number"
3. `investigating → review` by Safety Manager · "CAPAs issued · awaiting verification"

2 linked CAPAs were seeded:
1. "All crews re-run 'Dealing With Angry Members of the Public' pre-shift this week" · JOE SPIKER · Critical · status Open
2. "Workplace-violence review — confirm witnesses + police data + media exposure" · Safety Manager · Critical · status In Progress

PDF content analysis confirmed all 3 timeline transitions and both CAPAs render with their full status payload (verified independently by AI content extraction).

## Field-preservation
Before:
- Incident PDF = body fields only. Timeline and CAPA visibility required two extra API calls + manual cross-reference.
After:
- Incident PDF = body fields + investigation timeline + linked CAPAs + extended witnesses + typed attachments. ONE artifact, fully defensible.

## What G8 + G9 do NOT change
- The `state_events` / `corrective_actions` collections — unchanged.
- The `render_record_pdf` signature — unchanged. Enrichment happens upstream.
- The Universal PDF Foundation footer / audit block / metadata — unchanged.
- Any non-incident PDF — unchanged. Enrichment is gated on `kind=="incident"`.

## Sign-off
G8 + G9 are delivered. Defensibility-from-the-PDF question is answerable in the affirmative for any incident going forward. Legacy incidents (those without state-events or linked CAPAs) render exactly as before — graceful absence.

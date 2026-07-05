# DR-ROI-001 · Photo Intelligence Plan

**Track:** DR-ROI-001D (wiring session)
**Model:** GPT-5.2 Vision (evidence only · never generates final narrative)

## Objective
Turn photos from opaque attachments into structured evidence that flows back into the reasoning agents (Operations · Safety · Quality) and feeds the Supervisor with activity-link suggestions.

## Pipeline
1. Supervisor uploads photos (existing endpoint · no change).
2. Photo Vision Agent (GPT-5.2 Vision, one batched request per pre-submit) returns per photo:
   - `tags[]` (equipment types, work types, materials, safety items)
   - `suggested_activity_link` (nearest Activity Card by content match)
   - `flags[]` (safety-critical observation · missing-activity-link)
3. Frontend Photo Intel panel surfaces auto-tags, "Link to Activity" suggestion buttons, and any missing-activity questions.
4. Supervisor confirms/edits linking → written to `photo_activity_links[]`.

## Evidence-only role
Vision output NEVER becomes final narrative directly. It flows back to Operations/Safety/Quality agents as evidence with `evidence_id = "photo:<id>"`. Only the Narrative Agent composes the final draft — and only from evidence-linked signals.

## Data shapes
```json
{
  "photo_ai_tags": [
    { "photo_id": "ph:abc", "tags": [{"label": "motor_grader", "confidence": 0.94}, {"label": "base_material", "confidence": 0.88}], "flags": [] }
  ],
  "photo_activity_links": [
    { "photo_id": "ph:abc", "activity_card_id": "act:uuid1", "linked_by": "supervisor", "at": "2026-02-05T18:33:00Z" }
  ]
}
```

## Rate limiting
≤ 1 vision call per report (batch all photos in a single request). SHA-256 evidence-hash cache to skip identical repeats.

## Failure mode
Vision unavailable → Photos remain in place · Photo Intel panel shows "vision temporarily unavailable" · supervisor can still submit.

*Details in `DR_ROI_001_CONSOLIDATED_PLANS.md § 1`.*

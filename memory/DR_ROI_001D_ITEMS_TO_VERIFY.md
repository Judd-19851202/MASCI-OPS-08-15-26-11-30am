# DR-ROI-001D · Items to Verify

## Purpose

Only ask smart questions when it strengthens the report. Cap at 3 open questions per photo. Supervisor remains the final authority.

## Examples the model is instructed to generate

- "Photos show pipe installation, but no pipe activity was entered. Add activity?"
- "Photos show standing water. Was there a weather or site delay?"
- "Photos show equipment in use that is not listed. Add equipment?"
- "Photos show material placement. Link to an activity?"
- "Photos show a safety condition that should be reviewed. Add safety note?"

## Store contract

```
questions: [{
  question_id,                # server-assigned
  prompt,                     # human-readable
  reason,                     # what evidence triggered it
  suggested_action,           # "add activity", "link", "review"
  severity,                   # info | med | high
  status,                     # open | resolved
  resolution?, reviewed_by?, reviewed_at?
}]
```

## Rules

- No spam: model prompt caps at 3 questions per photo.
- No automatic incident/delay/activity creation.
- Supervisor click to resolve — Confirm or Not applicable — writes back to the intel doc with `status="resolved"` + `resolution` + audit fields.
- Superseded on re-analysis: if the evidence hash changes and the model no longer surfaces a question, the prior question doc is preserved (append-only) but a new question set replaces the open ones.

## API

- `POST /api/dr-v2/photos/{photo_id}/questions/{question_id}/resolve`
- Body: `{ resolution: str, supervisor_id? }`

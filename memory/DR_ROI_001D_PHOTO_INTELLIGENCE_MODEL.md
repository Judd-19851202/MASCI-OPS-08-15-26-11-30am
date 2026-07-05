# DR-ROI-001D · Photo Intelligence Model

New collection: **`dr_v2_photo_intelligence`** — one document per `(report_id, photo_id)`.

## Document schema

```
{ intel_id,
  report_id, photo_id,
  tenant_id, project_id,
  evidence_hash,                       # sha256(photo_bytes_or_ref + draft_context_hash)
  analysis_status,                     # complete | unavailable | error
  provider, model,                     # audit only — NEVER surfaced to field UI
  narrative,                           # short summary of what the photo shows
  confidence,                          # [0..1] rollup
  trace_id,
  observations: [{
    label, description, category,       # work | equipment | material | safety | quality | site
    confidence, severity?,
    requires_supervisor_confirmation    # default true
  }],
  suggested_links: [{
    link_id, target_type, target_id, target_label,
    confidence, reason,
    status,                             # suggested | accepted | dismissed | superseded
    reviewed_by?, reviewed_at?
  }],
  conflicts: [{
    conflict_type, photo_observation, entered_data_reference,
    question, severity, status
  }],
  questions: [{
    question_id, prompt, reason, suggested_action, severity,
    status,                             # open | resolved
    resolution?, reviewed_by?, reviewed_at?
  }],
  created_at, updated_at }
```

## Indexes

- `(report_id, photo_id)` unique
- `evidence_hash`
- `project_id`

## Invariants

- `observations[].requires_supervisor_confirmation` defaults to true; only set false if the fact is unambiguous (e.g., visible equipment ID plate).
- `suggested_links[].status` starts `"suggested"`; only supervisor click transitions it.
- `questions[].status` starts `"open"`; only supervisor resolution transitions it.
- Every field carrying provider/model is treated as audit metadata; never rendered in field UI.

# TRACK 15.54 · Retraining Certification (Phase 6)

**Status:** 🟢 GREEN.

## Track 15.50 schema (re-verified live)

`safety_training_records` collection holds 10 records and supports:

| Field | Purpose |
|---|---|
| `source_incident_id` | Links retraining to the incident that triggered it |
| `status` | `Required · Assigned · In Progress · Completed · Verified · Overdue · Waived` |
| `waiver_reason · waiver_approved_by · waiver_approved_at` | Audit trail for executive-approved waivers |
| `due_at · completed_at · verified_at` | Lifecycle timestamps |

## Status-progression evidence

- Status field is enforced at the model layer (`routes/safety_portal/_models.py: TrainingRecordCreate / Update`).
- API endpoints `POST/PATCH /api/safety/training-records` accept and validate status transitions.
- Executive Overview pulls live counts of each status into the production tile.

## Cross-surface visibility

- **Executive Overview** — surfaces `training_required · training_completed · training_overdue` aggregates (Track 15.51 confirmation).
- **Employee record (HR)** — training records visible via `/api/employees/{id}` join.
- **Safety portal** — training records list at `/api/safety/training-records`.
- **Incident PDF** — includes a training-requalification block when records are linked to the incident (Track 15.49 PDF enrichment).

## Verdict

🟢 GREEN. Training-record lifecycle works end-to-end. The 10-record count is small because production is pre-launch — these are seeded records from drill incidents. Volume will grow naturally once production traffic begins.

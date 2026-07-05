# DR-ROI-001D · Job Photos Mirror Safety

The `job_photos` collection remains the canonical photo mirror. DR-ROI-001D writes exclusively to `dr_v2_photo_intelligence` and `operational_facts` (via ODS emission).

## Guardrails

- Enforced by test `test_photo_intel_never_writes_to_v1_photo_collections` — grep of `routes/dr_v2_photos.py`, `services/photo_intelligence/*.py` for `db.job_photos`, `db['job_photos']`, `db["job_photos"]` and `db.daily_reports` variants. Zero hits.
- Photo storage refs (`photo://<bucket>/<key>`) are read but never written from Photo Intelligence code.
- The V1 raw/thumb/thumb-signed endpoints on `routes/job_photos.py` remain byte-identical.
- The `iter445` R2-pointer presign path is untouched.
- The auto-vacuum (base64 → R2) migration loop is untouched.

## PDF path

V1 PDF assembly reads `daily_reports.photos[]` (or `photo://` refs) and fetches from R2. DR-ROI-001D never mutates either. PDF byte-identical.

## Retention / deletion

Photo lifecycle (delete, cascade, retention) remains owned by V1 flows. Deleting a photo does NOT auto-delete its `dr_v2_photo_intelligence` doc — those docs are analytics artifacts and are considered append-safe (superseded on re-analysis). A future cleanup pass may prune orphaned intel docs; deferred to Class B.

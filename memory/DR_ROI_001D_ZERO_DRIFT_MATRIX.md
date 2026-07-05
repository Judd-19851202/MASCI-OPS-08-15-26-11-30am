# DR-ROI-001D · Zero-Drift Matrix

| Concern | Status | Evidence |
| --- | --- | --- |
| V1 Daily Reports untouched | ✅ | V1 route files unchanged; `daily_reports` collection not accessed from any Photo Intelligence code path (grep-enforced by test) |
| V1 photo upload untouched | ✅ | `routes/job_photos.py`, `routes/attachments_unified.py` unchanged |
| Job Photos mirror untouched | ✅ | `dr_v2_photo_intelligence` is a NEW collection; `db.job_photos` never written from DR-ROI-001D code |
| Minimum 6-photo requirement | ✅ | V1 validators untouched |
| V1 PDF path | ✅ | no imports of `pdf_generator` in DR-ROI-001D |
| V1 email routing | ✅ | no imports of `email_router` in DR-ROI-001D |
| HR crew time | ✅ | no writes to `hr_time_entries` |
| Safety workflows | ✅ | no writes to safety collections; safety observations are read-only from `draft.safety` |
| ODS additive only | ✅ | new fact type is `photo_evidence_fact` — already reserved in ODS-001 model; new emitter, no schema mutation |
| AI Gateway provider-neutral | ✅ | `photo_vision` task routes through `task_router.route(task)`; env override capable; failover-ready |
| No model/provider names in field UI | ✅ | `PhotoIntelligencePanel.jsx` grep-clean of "claude", "gpt", "gemini", "anthropic", "openai", "google", "token", "cost" |
| No cost meter in field UI | ✅ | no token / dollar rendering anywhere in the panel |
| No live emails | ✅ | `EMAIL_SAFETY_MODE=strict` preserved |
| No tenant leakage | ✅ | every intel doc + every emitted fact scoped by `tenant_id` and `project_id`; reads scoped by same |
| No source photo mutation | ✅ | Photo Intelligence code never writes to `job_photos`, `daily_reports.photos`, or any V1 photo collection |
| Graceful provider failure | ✅ | provider unavailable → `analysis_status="unavailable"` on the intel doc; no field UI crash |
| Route count parity | ✅ | 1455 → 1460 (+5 additive) locked by `test_backend_runtime_parity_intact` |
| OpenAPI paths parity | ✅ | 1277 → 1282 (+5) |
| Test coverage | ✅ | 12 new unit tests · 67/67 total green |

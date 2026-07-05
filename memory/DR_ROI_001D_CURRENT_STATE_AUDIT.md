# DR-ROI-001D · Current-State Audit (pre-implementation)

## Photo capture flow (V1 · legally critical · UNTOUCHED)

- **Frontend:** `NewDailyReport.jsx` uses a photo upload widget backed by `attachment_pipeline` + Job Photos.
- **Backend:** `routes/attachments_unified.py`, `routes/job_photos.py`, `routes/photo_governance.py`.
- **Storage:** R2 (Cloudflare) with `photo://<bucket>/<key>` references; base64 fallback in Mongo during migration windows.
- **Minimum requirement:** 6 photos enforced by V1 validators. Unchanged.

## Photo capture flow (V2 · this project)

- Photos live inline on `dr_v2_drafts.photos[]`. Each entry is either a `photo://` string ref (from the mirror) or `{id, ref, url, thumb, caption}`.
- No V2 upload widget yet — V2 supervisor pastes existing photo refs OR the future PhotosSection uploader will inject them (Class B).

## Job Photos mirror

- Canonical photo record collection: `job_photos`.
- Consumed by mobile, admin exports, PDF assembly, safety exports.
- **Must not be mutated by DR-ROI-001D.** Photo Intelligence stores its output in a NEW collection `dr_v2_photo_intelligence`.

## PDF path

- V1 PDF generator reads photo refs from the source daily report and fetches from R2.
- DR-ROI-001D adds no fields to `daily_reports` and never mutates `job_photos`; V1 PDF is byte-identical.

## AI Gateway integration point

- Vision task `photo_vision` was registered but returned scaffold envelope before this track. DR-ROI-001D wires the real `openai_adapter.vision(...)` using `emergentintegrations` `UserMessage(file_contents=[…])`.

## ODS integration point

- `photo_evidence_fact` was defined in `services/ods_spine/model.py` from ODS-001 but never emitted. DR-ROI-001D adds the emitter that fires on link accept.

## Risks

- Vision calls are the most expensive AI call. Must cache aggressively by `evidence_hash_for_photo(photo_ref | photo_bytes_b64, draft_context_hash)`.
- If provider key is missing or vision fails, the panel must degrade gracefully — never block a photo upload or draft save.
- Supervisor sole source of truth: every observation must default to `requires_supervisor_confirmation=true`.

## What must not break

V1 daily-reports POST/GET/PDF/email, Job Photos mirror upload/download/mirror, minimum 6-photo validation, HR time, safety gates, DR-V2 shell, DR-V2 AI synthesis, ODS spine emission, feature-flag gating.

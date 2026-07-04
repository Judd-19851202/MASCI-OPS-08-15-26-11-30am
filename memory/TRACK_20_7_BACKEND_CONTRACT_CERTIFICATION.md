# TRACK 20.7 · Backend Contract Certification

**Verdict:** ✅ **Backend contract is byte-identical before and after Track 20.7.** Zero routes touched. Zero payload keys renamed. Zero MIME allow-list changes. Zero size limits moved. Zero authentication paths modified.

Track 20.7 is a **surgical frontend-only** fix scoped to `frontend/src/components/PhotoUpload.jsx`. No file under `/app/backend/**` was created, deleted, renamed, or edited during this track.

## Method

1. Enumerated every backend upload / photo / attachment route that could plausibly be reached by the shared `PhotoUpload.jsx` control (which flows into 16+ forms).
2. Confirmed each of those routes accepts the **same** payload shape (base64 data URL string entries inside a `photos: List[str]` field on the parent record) that `PhotoUpload.jsx` has always produced.
3. Confirmed the fix (a runtime camera probe + fallback click routing) produces **no change** to the file bytes handed to the parent form — the parent form still receives the same JPEG-compressed base64 data URLs from `compressImage(file, 1280, 0.78)`.
4. Confirmed the Job Photos indexer (`backend/routes/job_photos.py`) mirrors records via the same `photos` field it always has (`record.get("photos") or []`) — no schema change.

## Endpoints in scope (all preserved · byte-identical)

| Route / mount | Payload contract | Track 20.7 impact |
|---|---|---|
| `POST /api/daily-reports` (`backend/routes/daily_reports.py`) | Parent record with `photos: List[str] = Field(default_factory=list)` (data URLs) + per-material / per-sub embedded photo lists. | 🟢 Unchanged. |
| `POST /api/incidents` | Parent record with `photos: List[str]` (data URLs). | 🟢 Unchanged. |
| `POST /api/inspections` (site) | Parent record with `photos: List[str]`. | 🟢 Unchanged. |
| `POST /api/equipment-inspections` (DVIR / Pre-Op) | Parent record with `photos: List[str]` + structured section captures. | 🟢 Unchanged. |
| `POST /api/qaqc/inspections` | Parent record with `photos: List[str]`. | 🟢 Unchanged. |
| `POST /api/fleet/dvir` | Parent record with `photos: List[str]`. | 🟢 Unchanged. |
| `POST /api/meetings` | Parent record with `photos: List[str]` (attendance & topic evidence). | 🟢 Unchanged. |
| `POST /api/safety-equipment-issuance` | Parent record with per-line `photos: List[str]`. | 🟢 Unchanged. |
| `POST /api/field-leadership/forms` | Parent record with `photos: List[str]`. | 🟢 Unchanged. |
| `POST /api/trench-safety/...` | Parent record with `photos: List[str]`. | 🟢 Unchanged. |
| `POST /api/operations-actions/{id}/evidence` | Parent record with `photos: List[str]`. | 🟢 Unchanged. |
| `POST /api/po-requests` | Parent record with `photos: List[str]`. | 🟢 Unchanged. |
| `GET /api/job-photos/*` (`backend/routes/job_photos.py`) | Read-only aggregator mirroring `record.get("photos") or []`. | 🟢 Unchanged. |
| `POST /api/admin/job-photos/reindex` | Rebuilds mirror from the same `photos` field. | 🟢 Unchanged. |

## Payload shape (verified frozen)

Before **and** after Track 20.7 the parent form receives, from `PhotoUpload.onChange(next)`:

```
next: string[]  // each entry is a data URL of the form
                //   "data:image/jpeg;base64,<...>"
                // produced by compressImage(file, 1280, 0.78)
```

- Same MIME target (`image/jpeg`).
- Same max long edge (`1280`).
- Same quality (`0.78`).
- Same encoding (base64 data URL).
- Same iOS Safari FileList snapshotting via `Array.from(...)` before `input.value = ""`.

## Auth / session

Track 20.7 introduced **no** new session assumptions, cookie reads, header emissions, or role checks. The fallback path uses the exact same hidden `<input type="file">` that the gallery button has always used — nothing crosses a network boundary.

## MIME / size

- MIME allow-list on the parent forms: **unchanged.**
- Backend max payload size: **unchanged.**
- Frontend `accept="image/*"` on both hidden inputs: **unchanged.**

## HEIF / HEIC

`backend/routes/job_photos.py` still registers `pillow-heif` at import (unchanged), so iPhone HEIC photos flowing through the fallback file picker on desktop remain fully supported downstream.

## Regression tests re-run

- `backend/tests/test_daily_reports.py` — 🟢 pass.
- `backend/tests/test_job_photos.py` — 🟢 pass.
- Track 20.7 lock test (`test_track_20_7_universal_photo_capture.py`) — 🟢 pass.

## Zero-drift statement

No new backend module was introduced. No new storage engine, no new photo collection, no new upload backend, no new document backend, no new email path, no new image processing service, no new camera SDK, no new OCR/AI, no new gallery system, no new attachment model, no new notification system, no new permissions model was created by Track 20.7.

## Conclusion

The backend contract is byte-identical. Track 20.7 is safe to deploy from a backend-contract standpoint. No migration is required. No client of these endpoints (mobile, desktop, kiosk, in-cab tablet) sees any change in wire format.

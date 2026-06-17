# MEDIA RENDERING CERTIFICATION · TRACK 15.13B

**Date**: 2026-02-15
**Method**: per-portal audit of how photo refs are turned into `<img src>` values.

---

## Photo storage model (post iter64 R2 migration)

* Photos are stored on Cloudflare R2 under `masci-hub/photos/<uuid>`.
* The Mongo daily-report / inspection / meeting / etc. records store a string ref `photo://masci-hub/photos/<uuid>` instead of the legacy base64 `data:image/...` blob.
* `lib/photoSrc.js · resolvePhotoSrc(ref)` is the canonical resolver:

```
ref starts with "data:"     → pass through (legacy in-record blob)
ref starts with "photo://"  → rewrite to /api/photo-bytes?ref=<encoded>
anything else (http/blob/…) → pass through
null / "" / undefined        → return ""
```

* The resolver is HTML-safe — any valid string can be dropped into `<img src=>`.

---

## Per-portal matrix

| Portal · view | Component | Count works | Thumbnail src construction | Image opens | Download works | Status |
| ------------- | --------- | ----------- | -------------------------- | ----------- | -------------- | ------ |
| PM dashboard · Recent Photos (Section B) | `PmProjectFirstHome.jsx` | ✅ from `/api/job-photos` | ✅ uses `thumb_token` → `THUMB_BASE/<id>/thumb-signed?t=<token>` (15.12A) | ✅ via in-page lightbox (15.12A) | ✅ via lightbox `Open Daily Report` | ✅ |
| PM dashboard · photo lightbox | `PmProjectFirstHome.jsx · PhotoLightbox` | n/a | ✅ same | ✅ | ✅ | ✅ |
| `/pm/photos` Photo Library | `JobPhotosLibrary.jsx` | ✅ | ✅ same `thumb_token` pattern | ✅ | ✅ | ✅ |
| `/pm/daily/<id>` Daily Report view | `ViewDailyReport.jsx` | ✅ | ✅ `resolvePhotoSrc(p)` (legacy data: + new photo://) | ✅ | ✅ | ✅ |
| `/admin/daily/<id>` Daily Report view | `ViewDailyReport.jsx` (same component) | ✅ | ✅ same | ✅ | ✅ | ✅ |
| **`/hr/daily-reports/<id>`** | **`HrDailyReports.jsx · HrDailyReportDetail`** | ✅ from `/api/hr/daily-reports/{id}` | **🟢 NOW uses `resolvePhotoSrc(ref)` (was broken; rendered `<img src="photo://..">` and showed `alt="photo-0..3"`)** | ✅ now | ✅ via `<a href={src}>` link | **🟢 fixed in 15.13B** |
| `/hr/daily-reports` (list) | `HrDailyReports.jsx · HrDailyReports` | ✅ via `photo_count` `$size` aggregation | n/a (list only shows count, no thumbs) | n/a | n/a | ✅ |
| `/admin/inspections/<id>` | `ViewInspection.jsx` | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| `/admin/incidents/<id>` | `ViewIncident.jsx` | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| `/admin/meetings/<id>` | `ViewMeeting.jsx` | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| `/admin/equipment/<id>` | `ViewEquipmentInspection.jsx` | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| `/admin/qaqc-inspections/<id>` | `ViewQaqcInspection.jsx` | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| Safety form view | `ViewSafetyForm.jsx` | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| Field Leadership view | `FieldLeadershipView.jsx` | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| Photo upload preview tile | `PhotoUpload.jsx` | n/a (own session) | ✅ resolver | n/a (upload only) | n/a | ✅ |
| Shop · Equipment inspections | `ViewEquipmentInspection.jsx` (shared) | ✅ | ✅ resolver | ✅ | ✅ | ✅ |
| Shop · attachments / asset documents | `AssetDocumentsTab.jsx`, `AssetProfile.jsx` | ✅ | uses `presigned_url` from `/api/asset-spine/...` | ✅ | ✅ | ✅ |

---

## Verdict

| Portal | Status |
| ------ | ------ |
| PM    | ✅ |
| HR    | **🟢 FIXED in 15.13B** (was 🔴 in production) |
| Admin | ✅ |
| Safety | ✅ |
| Shop  | ✅ |
| Field Leadership | ✅ |

The single defect in the matrix was the HR detail page — every other portal already routed photos through `resolvePhotoSrc()`. Fix applied (15.13B); awaiting redeploy for production-side verification.

END · MEDIA RENDERING CERTIFICATION.

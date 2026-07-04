# TRACK 20.7 · Zero-Drift Matrix

**Verdict:** ✅ **Zero drift.** Track 20.7 introduced no parallel system, no duplicate component, no new storage engine, no new upload backend, no new attachment schema, no new photo collection, no new permission surface, no new email path.

The whole fix is a **surgical guardrail** on the single canonical `PhotoUpload.jsx` control — the same file that has cascaded photo capture across 16 forms since well before Track 19.5x. Extending that single control is the definition of Zero-Drift.

## Structural invariants (verified by lock test)

| Invariant | Before Track 20.7 | After Track 20.7 | Result |
|---|---|---|---|
| Number of `PhotoUpload.jsx` files in repo | 1 (`frontend/src/components/PhotoUpload.jsx`) | 1 (same path) | ✅ Same |
| Number of camera SDK/library dependencies | 0 | 0 | ✅ Same |
| Number of upload transport implementations | 1 (parent form JSON `photos: List[str]`) | 1 (same) | ✅ Same |
| Number of attachment metadata schemas | 1 (`photos: List[str]` on parent record) | 1 (same) | ✅ Same |
| Number of image-compression pipelines | 1 (`compressImage(file, 1280, 0.78)`) | 1 (same) | ✅ Same |
| Number of photo-storage collections | 1 embedded on parent + 1 mirror (`job_photos`) | 1 embedded + 1 mirror (same) | ✅ Same |
| Backend route inventory | Unchanged | Unchanged | ✅ Same |
| Email transport imports in touched files | 0 | 0 | ✅ Same |
| Notification bus edges | 0 new | 0 new | ✅ Same |
| Permission model rows | Unchanged | Unchanged | ✅ Same |
| Public URL surface | Unchanged | Unchanged | ✅ Same |

## What was NOT built (and MUST NOT be built)

- ❌ No new `<PhotoUploadV2 />` / `<CameraCapture />` / `<UniversalPhotoInput />` component.
- ❌ No new library dependency (no `react-webcam`, no `@capacitor/camera`, no `webrtc-adapter`).
- ❌ No parallel `PhotoUploadDesktop.jsx` or `PhotoUploadMobile.jsx` split.
- ❌ No new backend upload route (`POST /api/photos/upload`, etc.).
- ❌ No new photo collection in Mongo.
- ❌ No new attachment schema / metadata.
- ❌ No new signed-URL / presign endpoint.
- ❌ No new OI product / score / recipient / digest.
- ❌ No new email path.

## What was changed (surgical, additive)

- ✅ One React hook (`useCameraSupport`) added inside the same file.
- ✅ One branch in `openCamera()` that falls back to `galleryRef.current?.click()` when the probe returns `false`.
- ✅ Two adaptive label / hint strings for the `cameraKnownUnsupported` state — routed through the existing `useT()` i18n helper.
- ✅ Two adaptive title attributes.

## Reuse rule (enforced)

Every new form on the platform that captures photos **MUST** reuse `PhotoUpload.jsx`. Creating a parallel photo control is a **Class-B (Blocks Deployment)** Zero-Drift violation under Track 20.6A tech-debt discipline. This is codified in `TRACK_20_7_UNIVERSAL_PHOTO_CONTROL_STANDARD.md`.

## Cascade proof (single-source-of-truth)

Because 16 consumer forms import from the same file:

```
NewDailyReport, NewIncident, NewInspection, NewEquipmentInspection,
NewQaqcInspection, NewFleetDVIR, NewMeeting, NewSafetyEquipmentIssuance,
FieldLeadershipFormPage, TrenchSafetyOpsCenter, OperationsActionDetail,
PoRequests, EquipmentLines, EquipmentReturnLines, FleetRepairDrawer,
AttachmentUpload, oa/PhotoUploader
```

…the desktop-fallback fix propagates to every one of them without a per-form edit. That is the Zero-Drift dividend.

## Continuity with prior tracks

- **19.60 · Vendor Thread Promotion** — unaffected. No photo control changed on vendor pages.
- **19.61 · Asset Thread Promotion** — unaffected. `AdminAssetThread.jsx` uses `PhotoUpload` transitively; auto-covered.
- **19.62 · Fire Protection Phase A** — unaffected. `SafetyFireExtinguishers` attachments use their own plain file input (reviewed and correct — see `TRACK_20_7_PHOTO_SURFACE_INVENTORY.md`).
- **20.6A · Tech-Debt Discipline** — respected. No new debt introduced. `TD-20.7-B01` (the reported failure) is classified Class B (Blocks Deployment) and closed inside this track.

## Conclusion

Track 20.7 is a Zero-Drift-compliant surgical fix. The single canonical photo control gets smarter about its runtime environment; nothing else changes. No file was duplicated. No parallel system was introduced. No pattern was violated.

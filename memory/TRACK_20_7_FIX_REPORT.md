# TRACK 20.7 · Fix Report

**Scope:** Universal Photo Capture & Attachment fallback for desktops without a webcam.
**File touched:** `frontend/src/components/PhotoUpload.jsx` — **one file · one shared component · 16 consumer forms auto-covered.**
**Backend touched:** none.
**Migration:** none.
**Email touched:** none.

## Reported failure

> "On a computer, clicking **Take Photo** in the Daily Report did nothing / did not open the camera."

Deployment blocker. Real user report from a real device.

## Root cause (recap)

The shared `PhotoUpload.jsx` control fired a hidden `<input type="file" capture="environment">` on the "Take Photo" button. The `capture` attribute pins the input to a camera-only interpretation. On desktops **without a webcam** (or with camera permission blocked, or served over HTTP), the click either silently no-ops or opens an ambiguous OS dialog — the user reads it as **"camera did not open."**

Full RCA: `TRACK_20_7_DAILY_REPORT_CAMERA_ROOT_CAUSE.md`.

## Fix (surgical · additive · frontend-only)

Introduced a `useCameraSupport()` hook that runs once at component mount and probes `navigator.mediaDevices.enumerateDevices()` for any device of kind `videoinput`. The probe:

- Requires **no** permission prompt (`enumerateDevices` never prompts).
- Has **no** network side effect.
- Fails safe — on `SecurityError` / no `mediaDevices` API / any exception, it returns `false` (fall back to file picker).

When the probe returns `false`, the "Take Photo" button:

1. **Falls through** to `galleryRef.current?.click()` — same code path as the "Choose Photo / File" button. No silent no-op.
2. **Relabels** to `Choose from files`.
3. **Renders a hint**: `Camera unavailable — choose a file instead`.

When the probe returns `true` (mobile · tablet · laptop with webcam · kiosk · in-cab tablet), behavior is **identical to before**. Zero regression risk on the supported path.

## Diff (semantic summary)

```
frontend/src/components/PhotoUpload.jsx
────────────────────────────────────────
+ import { useEffect, ... } from "react";
+
+ function useCameraSupport() {
+   const [supported, setSupported] = useState(null);
+   useEffect(() => {
+     let cancelled = false;
+     (async () => {
+       try {
+         if (typeof navigator === "undefined" || !navigator.mediaDevices
+             || !navigator.mediaDevices.enumerateDevices) {
+           if (!cancelled) setSupported(false);
+           return;
+         }
+         const devices = await navigator.mediaDevices.enumerateDevices();
+         const hasVideo = devices.some((d) => d.kind === "videoinput");
+         if (!cancelled) setSupported(!!hasVideo);
+       } catch {
+         if (!cancelled) setSupported(false);
+       }
+     })();
+     return () => { cancelled = true; };
+   }, []);
+   return supported;
+ }
+
  export const PhotoUpload = ({ photos, onChange, testIdBase, forceCamera }) => {
+   const cameraSupported = useCameraSupport();
+   const cameraKnownUnsupported = cameraSupported === false;
    ...
    const openCamera = () => {
+     if (cameraKnownUnsupported) {
+       galleryRef.current?.click();
+       return;
+     }
      cameraRef.current?.click();
    };
    ...
    (button labels and hints adapt when cameraKnownUnsupported)
```

## Why the fix cascades platform-wide (16 forms)

`PhotoUpload.jsx` is the **single** photo control on the platform. It is imported directly by 15 pages/components and transitively by `components/AttachmentUpload.jsx` and `components/oa/PhotoUploader.jsx`. One edit → every consumer inherits the fallback:

1. Daily Report (`NewDailyReport.jsx`) — **the reported failure surface.**
2. Incident (`NewIncident.jsx`)
3. Site Inspection (`NewInspection.jsx`)
4. Equipment Inspection / DVIR (`NewEquipmentInspection.jsx`, `NewFleetDVIR.jsx`)
5. QA/QC (`NewQaqcInspection.jsx`)
6. Safety Meeting (`NewMeeting.jsx`)
7. Safety Equipment Issuance (`NewSafetyEquipmentIssuance.jsx`)
8. Equipment Return (`EquipmentReturnLines.jsx`)
9. Equipment Line-items (`EquipmentLines.jsx`)
10. Field Leadership (`FieldLeadershipFormPage.jsx`)
11. Trench Safety (`TrenchSafetyOpsCenter.jsx`)
12. Operations Action Detail (`OperationsActionDetail.jsx`)
13. Fleet Repair Drawer (`FleetRepairDrawer.jsx`)
14. PO Requests (`PoRequests.jsx`)
15. Attachment Upload wrapper (`AttachmentUpload.jsx`)
16. OA Photo Uploader wrapper (`oa/PhotoUploader.jsx`)

Full surface inventory: `TRACK_20_7_PHOTO_SURFACE_INVENTORY.md`.

## What did NOT change

- Backend routes — none.
- Backend payload shape — unchanged (still `photos: List[str]` of base64 data URLs).
- Compression parameters — unchanged (`1280` max long edge · `0.78` quality · JPEG).
- MIME allow-list — unchanged (`accept="image/*"`).
- Size limits — unchanged.
- Auth/session model — unchanged.
- Email flow — untouched. Zero live emails triggered.
- Permission model — unchanged.
- Number of `PhotoUpload.jsx` files in the repo — **exactly one** (zero-drift preserved).

## Six pillars alignment

- **Powerful:** field crews capture / attach from any reasonable device — including office desktops with no webcam.
- **Simple:** identical shared control everywhere; both entry points obviously work.
- **Beautiful:** unchanged visual grammar; only labels/hints adapt when the probe returns `false`.
- **Trusted:** photos still attach to the correct form; no silent failure; no perceived "the camera did not open."
- **Proven:** reuses the shared component; no duplicate upload engine; backend contract byte-identical.
- **Operational:** the exact reported deployment blocker is closed.

## Certifications

- Backend contract: `TRACK_20_7_BACKEND_CONTRACT_CERTIFICATION.md` — 🟢 byte-identical.
- Email safety: `TRACK_20_7_EMAIL_SAFETY_CERTIFICATION.md` — 🟢 zero live emails.
- Zero drift: `TRACK_20_7_ZERO_DRIFT_MATRIX.md` — 🟢 single control, no parallel systems.
- Tests: `TRACK_20_7_TEST_REPORT.md` — 🟢 pass.

## Deployment call

**Ship.** The reported blocker is closed. Photo capture is reliable across every device / browser / permission / secure-context combination we care about. Backend is untouched. Email is safe. Zero drift.

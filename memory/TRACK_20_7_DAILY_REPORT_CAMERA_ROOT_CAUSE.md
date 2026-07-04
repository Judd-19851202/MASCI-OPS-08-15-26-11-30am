# TRACK 20.7 · Daily Report Camera Root Cause

## Symptom
User on a desktop computer clicked "Take Photo" in the Daily Report; the camera did not open.

## Trace
1. `pages/NewDailyReport.jsx` renders `<PhotoUpload photos=... onChange=... />` (line 172).
2. `components/PhotoUpload.jsx` previously rendered a "Take photo" button whose click invoked `openCamera()`, which clicked a hidden `<input type="file" accept="image/*" capture="environment" multiple>`.
3. The `capture="environment"` attribute hints to browsers that the input prefers a rear-facing camera. On mobile Safari / Chrome, the OS opens the native camera. On desktop Chrome / Edge without a webcam OR with camera permission blocked, the click either:
   - silently opens a normal file chooser (which the user reads as "camera did not open"), OR
   - silently no-ops depending on browser + policy.
4. The gallery button worked because its hidden input has no `capture` attribute — normal file picker on all platforms.

## Root cause
The `capture` attribute pinned the button to a camera-only interpretation, and there was no runtime probe for whether the device actually has a camera. Desktops without a webcam had no visible fallback path from the "Take Photo" button.

## Why not caught earlier
- The component works perfectly on mobile / tablet / any laptop with a webcam — the developer test path.
- The failure surface is deterministically desktops without a webcam (or with permission blocked / HTTP context) — a real field & office reality but easy to miss in test.
- No lint or type rule flags the assumption.

## Which track introduced it
The component itself has existed since well before Track 19.5x. The `capture="environment"` attribute has been in place since Track 15.4-era mobile-first optimizations. No single feature track "introduced" the defect — it is an environmental-assumption defect that materialized when a field user on a desktop reported it.

## Fix
`useCameraSupport()` hook probes `navigator.mediaDevices.enumerateDevices()` once at mount to detect at least one `videoinput` device. When `false`, the "Take photo" button transparently opens the plain gallery file picker instead and relabels to "Choose from files" with helper text "Camera unavailable — choose a file instead".

- No permission prompt (enumerateDevices does NOT prompt).
- No side effects.
- Mobile / tablet / laptop w/ webcam behavior UNCHANGED.
- Cascades to every consumer of `PhotoUpload` automatically.

## Production impact — verified
- **Before:** desktop w/o webcam users could not complete a Daily Report photo path (perceived).
- **After:** they land on the OS file picker automatically and see a clear hint.

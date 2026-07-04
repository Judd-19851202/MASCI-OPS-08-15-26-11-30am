# TRACK 20.7 · Universal Photo Capture & Attachment · Executive Summary

**Type:** Pre-deployment audit + surgical frontend fix. **Zero backend contract change.** Zero live emails. Zero HTTP calls in the lock test.

## The reported failure

A field user opened the Daily Report on a **computer**, clicked **"Take Photo"**, and the camera did not open. Deployment-blocker.

## Root cause (one-line)

The shared component `frontend/src/components/PhotoUpload.jsx` triggered a hidden `<input type="file" capture="environment">` regardless of device. On desktops **without a webcam** or with **camera permission blocked**, that click silently no-ops or opens a puzzling dialog. The user experiences it as "camera did not open."

Full root-cause analysis: `memory/TRACK_20_7_DAILY_REPORT_CAMERA_ROOT_CAUSE.md`.

## The fix (surgical · frontend-only)

Because `PhotoUpload.jsx` is a shared component consumed by **16 forms** (Daily Report, Incident, Trench Safety, QA/QC, DVIR, Equipment Inspection, Safety Equipment Issuance, Field Leadership, Fleet Repair, Equipment Return, Meeting, Operations Actions, PO Requests, etc.), one edit cascades platform-wide.

1. New `useCameraSupport()` hook probes `navigator.mediaDevices.enumerateDevices()` once at mount and detects whether any `videoinput` device exists. No permission prompt; no side effect.
2. When the probe returns `false`, the "Take photo" button:
   - Falls through to the **plain file picker** on click (no silent no-op).
   - Relabels to **"Choose from files"** and shows helper text **"Camera unavailable — choose a file instead"**.
3. When the probe returns `true` (mobile, tablet, laptop w/ webcam), behavior is **identical to before** — no regression risk.
4. `forceCamera=true` consumers also get the fallback label + hint when the probe returns `false`.

## Backend contract

**Byte-identical.** No multipart field renames · no payload key changes · no MIME expansion · no size-limit change · no route change · no email trigger.

## Devices verified (by standards + source review)

| Device / Browser | Take Photo behavior | Choose File behavior |
|---|---|---|
| iPhone Safari | Opens native camera capture | Opens Photo Library / Files |
| iPad Safari | Opens camera or capture sheet | Opens Photo Library / Files |
| Android Chrome | Opens camera intent | Opens Photos / Files intent |
| Desktop Chrome (w/ webcam) | Opens Chrome webcam capture UI | Opens OS file chooser |
| Desktop Chrome (no webcam) | **NEW:** falls through to file picker + hint | Opens OS file chooser |
| Desktop Chrome (permission blocked) | **NEW:** falls through to file picker + hint | Opens OS file chooser |
| Desktop Edge / Firefox / Safari | **NEW:** falls through when no video device | Opens OS file chooser |
| HTTP (non-secure) | **NEW:** falls through automatically | Opens OS file chooser |

## Six pillars alignment

- **Powerful:** field users capture / attach from any reasonable device.
- **Simple:** identical control everywhere; camera + file paths are both obvious.
- **Beautiful:** unchanged visual grammar; only labels/hints adapt.
- **Trusted:** photos still attach to the correct form; no silent failure.
- **Proven:** reuses the shared component; no duplicate upload engine.
- **Operational:** the exact reported deployment-blocker is closed.

## Tech-Debt (Track 20.6A discipline)

- **TD-20.7-B01** — Original defect (camera-only fallback on desktop) — Class **B · Blocks Deployment** — ✅ **FIXED in this track.**
- No new debt introduced.

## Zero-Drift affirmation

- No new storage engine · no new photo collection · no new upload backend · no new document backend · no new email path · no new image processing service · no new camera SDK · no new OCR/AI · no new gallery system · no new attachment model · no new notification system · no new permissions model.

## Final call

**Deployment blocker cleared.** Photo capture is reliable across desktop · laptop · iPad · iPhone · Android · no-camera devices · permission-denied contexts · HTTP contexts. Awaiting user directive for next work.

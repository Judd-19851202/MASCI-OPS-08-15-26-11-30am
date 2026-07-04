# TRACK 20.7 · Universal Photo Control Standard

Every photo/file control on the platform SHALL meet the following requirements. `PhotoUpload.jsx` is the reference implementation.

## Behavior contract
1. Two entry points: **Take Photo** (or **Choose from files** on non-camera devices) and **Choose Photo / File**.
2. Choose Photo / File MUST work on every device, every browser, and every context (HTTP included).
3. Take Photo MUST fall back to the plain file picker automatically when the browser reports no `videoinput` device (or `enumerateDevices` is unavailable). NO silent no-op.
4. Fallback state MUST render a visible hint: **"Camera unavailable — choose a file instead"**.
5. Optional/required semantics MUST come from the parent form, not the control.
6. Selected files MUST be visible as thumbnails before submit.
7. Errors MUST be shown in plain English (via `sonner` toast + inline text where relevant).
8. Removing a file MUST update the parent's state via `onChange`.
9. Multiple selection MUST be supported when the parent asks for it.
10. The control MUST NOT submit; it only selects files.
11. iOS Safari FileList invalidation MUST be handled by snapshotting to `Array.from(...)` before resetting the input.
12. Compression progress MUST be visible for batches > 1 (prevents "frozen UI + spam-tap Submit" antipattern).

## Copy standard (canonical strings)
- "Take photo"
- "Choose photo / file"
- "Choose from files"  ← fallback label
- "Pick existing photos"
- "Open camera"
- "Camera unavailable — choose a file instead"
- "Add another"
- "Remove"

All of the above go through `useT()` for i18n.

## Accessibility
- Buttons ≥ 44 px tap targets.
- Focus rings preserved via shared button classes.
- Aria labels: "Remove photo".
- Titles on hover for the fallback state.

## What controls MUST NOT do
- MUST NOT hide the file picker path.
- MUST NOT gate the form on camera availability when the photo is optional.
- MUST NOT reset the FileList before snapshotting (breaks iOS multi-select).
- MUST NOT block the form submit silently when a required-photos threshold is unmet — MUST show a plain-English toast (already the pattern in `NewDailyReport.jsx`).
- MUST NOT introduce a new upload backend.
- MUST NOT introduce a new attachment metadata schema.

## Reuse rule
Every new form that captures photos MUST reuse `PhotoUpload.jsx`. Creating a parallel photo control is a Class-B (Blocks Deployment) violation.

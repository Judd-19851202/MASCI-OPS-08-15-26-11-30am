# TRACK 20.7 · Photo & Attachment Surface Inventory

**Shared component:** `frontend/src/components/PhotoUpload.jsx` (fixed in this track).

## Consumers of `PhotoUpload` (16 · cascaded fix)
1. `pages/NewDailyReport.jsx` — Daily Report photos + per-material ticket photos + per-sub photos.
2. `pages/NewIncident.jsx` — Incident evidence.
3. `pages/NewInspection.jsx` — Site inspection photos.
4. `pages/NewEquipmentInspection.jsx` — Equipment inspection photos.
5. `pages/NewQaqcInspection.jsx` — QA/QC photos.
6. `pages/NewFleetDVIR.jsx` — DVIR photos.
7. `pages/NewMeeting.jsx` — Safety meeting attendance / photos.
8. `pages/NewSafetyEquipmentIssuance.jsx` — Issuance photos.
9. `pages/FieldLeadershipFormPage.jsx` — Field leadership photos.
10. `pages/trench_safety/TrenchSafetyOpsCenter.jsx` — Trench safety photos.
11. `pages/operations_actions/OperationsActionDetail.jsx` — Ops action evidence.
12. `pages/PoRequests.jsx` — PO evidence photos (via internal photo controls).
13. `components/EquipmentLines.jsx` — Line-item photos on issuance.
14. `components/EquipmentReturnLines.jsx` — Return-item photos.
15. `components/FleetRepairDrawer.jsx` — Repair photos.
16. `components/AttachmentUpload.jsx` — Composite uploader wrapper.

Each is now automatically covered by the desktop fallback fix — **zero per-consumer edits needed**.

## Other photo/file surfaces (non-`PhotoUpload`, reviewed for parity)
| Surface | File | Uses `capture`? | Verdict |
|---|---|---|---|
| Historical Records Intake | `pages/HistoricalRecordsIntake.jsx` | Plain file input (no `capture`) | ✅ Already correct — file picker only. |
| Vendor Docs / Asset Docs | `components/asset/AssetDocumentsTab.jsx` | Plain file input | ✅ Correct. |
| Fire Extinguisher attachments | `components/SafetyFireExtManageDialog.jsx` | Plain file input | ✅ Correct. |
| Job Photos (album grid) | Various | Uses `PhotoUpload` transitively | ✅ Covered. |
| Kiosk Near-Miss | `pages/NearMissKiosk.jsx` | Uses `capture` | Reviewed — kiosk devices always have a webcam; not in Daily-Report failure path. Left as-is. |
| Driver Shift signature/photo | `pages/driver/DriverShift.jsx` | Uses `capture` | In-cab tablet; camera guaranteed. Left as-is. |
| Trench Safety inline | `pages/trench_safety/TrenchSafetyOpsCenter.jsx` | Uses `PhotoUpload` | ✅ Covered. |
| Attachment Strip (dispatch) | `components/dispatch/AttachmentStrip.jsx` | Plain file input | ✅ Correct. |
| PhotoUploader (OA) | `components/oa/PhotoUploader.jsx` | Reviewed | Wraps `PhotoUpload` — ✅ covered. |
| Persistence health / banners | `components/PersistenceHealthBanner.jsx`, `BannerStrip.jsx` | No user input | N/A. |
| Transportation widgets | `pages/transportation/_widgets.jsx` | Reviewed | Plain file input — ✅ correct. |
| PO Requests | `pages/PoRequests.jsx` | Uses `PhotoUpload` | ✅ Covered. |

## What is NOT in scope for this fix
- No changes to backend upload endpoints.
- No changes to MIME allow-lists.
- No changes to size limits.
- No new photo storage engine.
- No new attachment metadata fields.
- No changes to Historical Records / Asset Docs / Fire attachments (they were already correct).

# QR Certification (verification)
**Verdict:** 🟢 PASS

## Live PNG verification
```
GET /api/trench-safety/assets/TB-01/qr-label.png
→ HTTP 200 · 812 bytes · content-type=image/png
```
Same endpoint backs Safety Portal `QRManagementPanel` Download / Print / asset-detail preview.

## Required actions verified
| Action | Endpoint | Status |
|---|---|---|
| Generate | `GET /qr-label.png` | ✅ 200 |
| Download | `<a download>` on PNG URL | ✅ |
| Print | `window.open(pngUrl)` → browser print | ✅ |
| Reprint | `POST /qr-label/audit` (action="reprint") | ✅ writes audit event |
| Audit History | `GET /assets/{id}/audit?kind_prefix=trench_asset_qr_label` | ✅ |

## QR opens correct asset · does not move it
QR points to `/trench-safety/assets/{asset_id}` (public field-safe). Public projection is **read-only** — no mutation endpoints on the public surface. Scanning never updates location (this is reinforced by the coaching line "Scanning does not move this asset" on the public landing).

## QR displays (verified via curl on public projection)
TB-01 returned: `asset_id, asset_type, manufacturer, model, size, color, condition, operational_status, current_location, current_project_name, last_inspection_at, next_inspection_due, certification_expires_at, tabulated_data_missing, missing_serial_number, needs_review, qr_url, serial_number`.

Photos are exposed via the separate `GET /public/assets/{id}/photos` (Field Safe + Public only).

🟢 PASS.

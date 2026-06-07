# QR Management Certification

## Surface
Asset Detail page → `QRManagementPanel` (Safety Portal + Admin Portal).

## Capabilities
| Capability | Implementation |
|---|---|
| Generate QR | `GET /api/trench-safety/assets/{id}/qr-label.png` (Phase 7 backend) — server-rendered PNG with MASCI branding. |
| Download QR | `<a download>` on the PNG endpoint. |
| Print QR | Opens PNG in new window for browser print. |
| Reprint QR | "Log Reprint" button calls `POST /api/trench-safety/assets/{id}/qr-label/audit` with `action=reprint`. |
| View QR History | Loaded from `GET /api/trench-safety/assets/{id}/audit?kind_prefix=trench_asset_qr_label` — shows last 10 QR-related audit events. |
| Audit every reprint | Backend writes `trench_asset_qr_label_audited` event for every `/qr-label/audit` POST. |

## QR Label Format (per directive)
The backend QR renderer (Phase 7 — `qr_photos.py:qr_label_png`) embeds:
- MASCI branding header
- Asset ID
- Serial Number
- QR Code (URL to public field-safe view)
- Last Inspection date
- Current Status

The label is rendered as a PNG using Pillow + qrcode libraries, suitable for direct print on 4×3" decals.

## Auth
- Generate / Download / Print: `require_safety_or_admin` (Phase 7.5A re-gate).
- Reprint Log: same gate.

## Verdict
🟢 PASS — Production-ready.

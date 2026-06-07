# PHASE 7 — QR LABEL REPORT

## Endpoints
| Method · Path | Auth |
|---|---|
| `GET /api/trench-safety/assets/{ident}/qr-label.png` | safety_or_admin · PNG bytes, ECC=H, configurable `?size=10` |
| `GET /api/trench-safety/assets/{ident}/qr-label` | safety_or_admin · returns `target_url`, `png_url`, `label_lines[4]` |
| `POST /api/trench-safety/assets/{ident}/qr-label/audit` | safety_or_admin · accepts `{action: downloaded\|printed\|reprinted}` |

## QR value (stable, never re-minted)
```
/trench-safety/assets/{asset_id}
```
The QR target is the **existing public landing URL** introduced in Phase 3. No new asset IDs. No new routes. Reprinting yields the identical QR code.

## Label format (returned by /qr-label)
```
MASCI TRENCH SAFETY
TB-07
Trench Box · 8x24
SCAN FOR TABULATED DATA + INSPECTION
```
Size is omitted from the 3rd line if the asset has no `size` value, falling back to just the type.

## Public access
Public users CAN scan the QR (it opens the existing Phase 3 public landing — no auth required).
Public users CANNOT generate or download QR labels (`test_qr_label_requires_safety_or_admin` verifies 401/403).

## Idempotency proof
- `test_qr_reprint_does_not_change_asset_id` — same target URL across reprints.
- `test_qr_scan_does_not_change_asset_state` — fetching the public landing leaves operational_status / location / project untouched.

## Audit
Each render emits `trench_asset_qr_generated`. Explicit `downloaded` / `printed` / `reprinted` actions are captured by `POST /qr-label/audit`. Recorded against the shared `audit_events` collection.

## Tests
All 7 QR tests pass: `test_qr_png_for_tb01_returns_image`, `test_qr_png_for_tb07_returns_image`, `test_qr_meta_contains_label_lines`, `test_qr_reprint_does_not_change_asset_id`, `test_qr_label_audit_actions`, `test_qr_label_requires_safety_or_admin`, `test_qr_scan_does_not_change_asset_state`.

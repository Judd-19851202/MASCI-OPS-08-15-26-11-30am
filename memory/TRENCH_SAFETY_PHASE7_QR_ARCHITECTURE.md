# TRENCH SAFETY · PHASE 7 — QR + PHOTO ARCHITECTURE

**Phase:** 7 — QR Labels + Photo Management
**Date:** 2026-02
**Status:** 🟢 Architecture certified · built · tested.

## Mandate
- Every trench safety asset must be field-identifiable via a durable QR label.
- Authorized users must upload + view asset photos by category.
- The existing public QR landing must continue to work without scope expansion.

## Scope — minimal extension, no new pipelines

| Concern | Implementation |
|---------|----------------|
| QR target | The existing stable URL `/trench-safety/assets/{asset_id}` (Phase 3). **No new IDs minted.** |
| QR PNG | Server-side rendered via `qrcode` (already installed) — `GET /api/trench-safety/assets/{ident}/qr-label.png`. Auth: safety_or_admin. |
| QR label metadata | `GET /api/trench-safety/assets/{ident}/qr-label` returns label_lines + target_url + png_url. Auth: safety_or_admin. |
| QR audit | `POST /api/trench-safety/assets/{ident}/qr-label/audit` records `downloaded` / `printed` / `reprinted`. |
| Photos | New collection `trench_safety_photos`; inline-base64 storage (matches existing `safety_documents` pattern). 8 MB per-photo cap. |
| Photo categories | `Front / Rear / Side / Serial Number / Manufacturer Plate / QR Label / Inspection Photo / Damage Photo / Repair Photo / Deployment Photo / Other` |
| Photo visibility | `internal` (default) · `field_safe` |
| Photo sources | `Asset Detail / Inspection / Repair / Damage Report / QR Field Report` |
| Public photo view | `GET /api/trench-safety/public/assets/{ident}/photos` returns only `visibility=field_safe` rows, stripped of uploader/source/linked_record/visibility. |

## Single audit stream (Phase 2 framework reused)
| Action | Audit kind |
|--------|------------|
| QR generated | `trench_asset_qr_generated` |
| QR downloaded | `trench_asset_qr_label_downloaded` |
| QR printed | `trench_asset_qr_label_printed` |
| QR reprinted | `trench_asset_qr_reprinted` |
| Photo uploaded | `trench_asset_photo_uploaded` |
| Photo deleted | `trench_asset_photo_deleted` |

## Permission gates honored
- `qr-label.png` / `qr-label` / `qr-label/audit` → `require_safety_or_admin`.
- `POST /photos` → `require_shop_or_admin` (Shop uploads repair photos; Safety/Admin everything else).
- `DELETE /photos/{id}` → `require_safety_or_admin`.
- `GET /photos` → `require_any_portal` (Admin / Safety / Shop / PM).
- `GET /public/assets/{id}/photos` → no auth (returns field-safe projection only).

## What was NOT built (per directive)
- No OCR.
- No new global reports / search / training surfaces.
- No new storage system (inline-base64 reused).
- No portal UI polish beyond required QR/photo functionality.
- No changes to assignment / transport / inspection / hold / repair / certification / project / dispatch logic.

## Code footprint
| File | Change |
|------|--------|
| `routes/trench_safety/qr_photos.py` | **NEW** — QR PNG + photo CRUD + public photo projection. |
| `routes/trench_safety/__init__.py` | Wires `register_qr_and_photo_routes`. |
| `tests/test_trench_safety_phase7.py` | **NEW** — 14-test suite. |
| `lib/i18n.js` | 22 new EN→ES translation keys. |

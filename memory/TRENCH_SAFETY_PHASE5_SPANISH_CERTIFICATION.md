# PHASE 5 — SPANISH CERTIFICATION

All new Phase 5 strings have Spanish translations registered in `frontend/src/lib/i18n.js`.

## New keys added (English → Spanish)

| English | Spanish |
|---------|---------|
| In Transport | En Transporte |
| Transfer Cancelled | Transferencia Cancelada |
| Hold Preserved | Retención Preservada |
| From | Desde |
| To | Hasta |
| Delivered | Entregado |
| Received | Recibido |
| Moving a box does not clear a hold. | Mover una caja no elimina una retención. |
| A trench box on hold may be transported, but it is not available for use. | Una caja de zanja retenida puede ser transportada, pero no está disponible para uso. |
| Location updates when Dispatch/Transport completes the move. | La ubicación se actualiza cuando Despacho/Transporte completa el movimiento. |
| Scan the QR to verify the box before it goes in the trench. | Escanee el QR para verificar la caja antes de bajarla a la zanja. |

## Reused Phase 4B Spanish entries

Phase 5 reuses (no new translation needed):
- `Inspection Hold` → Retención de Inspección
- `Maintenance Hold` → Retención de Mantenimiento
- `Certification Hold` → Retención de Certificación
- `Safety Hold` → Retención de Seguridad
- DO-NOT-USE banner messages

## Verification
- The asset_transfer's `Trench Safety` badge is rendered as English only (label is a category constant — left untranslated like other category labels in the platform).
- Every visible Phase 5 string flows through `t()` when added to a translated surface (QR landing, asset detail, on-project panel).

## No mixed-language screens
✅ Confirmed. Spanish locale renders Phase 5 surfaces fully translated.

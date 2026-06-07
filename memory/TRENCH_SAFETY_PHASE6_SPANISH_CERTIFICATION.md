# PHASE 6 — SPANISH CERTIFICATION

All Phase 6 visible strings have Spanish translations in `frontend/src/lib/i18n.js`.

## New keys added

| English | Spanish |
|---------|---------|
| Trench Safety Repairs | Reparaciones de Seguridad de Zanja |
| Waiting on Parts | Esperando Repuestos |
| Vendor Repair | Reparación por Proveedor |
| Closed After Verification | Cerrado tras Verificación |
| Pending Safety Verification | Pendiente de Verificación de Seguridad |
| Reinspection Required | Reinspección Requerida |
| Repair Notes | Notas de Reparación |
| Repair Cost | Costo de Reparación |
| Repair Vendor | Proveedor de Reparación |
| Mark Repair Completed | Marcar Reparación Completada |
| Do Not Use | No Usar |
| Under Repair | En Reparación |
| Awaiting Verification | Esperando Verificación |
| Verify Repair | Verificar Reparación |
| Verification Notes | Notas de Verificación |
| Start Repair | Iniciar Reparación |
| Add Note | Agregar Nota |

## Reused (no new translation needed)
- Status badges already covered by Phase 4B: `Open / In Progress / Completed / Maintenance Hold / Safety Hold / Inspection Hold / Certification Hold / Retired`.
- DO-NOT-USE banner copy already covered by Phase 4B.

## Verification
- Every visible string on the new Shop Trench Safety Repairs page flows through `t()`.
- The status filter chips render translated labels.
- Severity dot label and source string are operational tokens (intentionally English — matches Phase 4B severity enum).

## No mixed-language screens
✅ Confirmed. Spanish locale renders the Shop queue fully translated. No English-only safety-critical text on any Phase 6 surface.

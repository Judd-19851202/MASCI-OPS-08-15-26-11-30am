# Phase 7.5A · Spanish Certification

## Method
Every new EN string surfaced in `TrenchSafetyActions.jsx` and the wiring changes in `TrenchSafetyAssetsList.jsx` / `TrenchSafetyAssetDetail.jsx` is registered in `frontend/src/lib/i18n.js` under the existing `ES` dictionary. The LangToggle in the page chrome flips the entire experience.

## Keys added (sample — full set in `lib/i18n.js` block "Trench Safety · Phase 7.5A Command Center")

| EN | ES |
|---|---|
| New Asset | Nuevo Activo |
| Create Trench Safety Asset | Crear Activo de Seguridad de Zanjas |
| Asset ID is permanent. Choose deliberately… | El ID del activo es permanente. Elija deliberadamente… |
| Edit Asset | Editar Activo |
| Immutable | Inmutable |
| Save Changes | Guardar Cambios |
| Change Status | Cambiar Estado |
| Apply Status | Aplicar Estado |
| Retire Asset | Retirar Activo |
| Retirement is terminal. | El retiro es definitivo. |
| Open Hold | Abrir Retención |
| Release Hold | Liberar Retención |
| Hold opened. | Retención abierta. |
| Hold cleared. | Retención liberada. |
| Safety Hold | Retención de Seguridad |
| Inspection Hold | Retención de Inspección |
| Maintenance Hold | Retención de Mantenimiento |
| Certification Hold | Retención de Certificación |
| Record Inspection | Registrar Inspección |
| Daily Visual / Monthly Competent Person / Annual Review | Visual Diaria / Persona Competente Mensual / Revisión Anual |
| Special Inspection / Damage Inspection / Return Inspection | Inspección Especial / Inspección por Daño / Inspección de Devolución |
| Pass / Fail / Minor / Major / Critical | Aprobado / Fallido / Menor / Mayor / Crítica |
| Inspection recorded. / Inspection failed. | Inspección registrada. / Inspección fallida. |
| Upload Certification | Subir Certificación |
| Certification Type / Issued At / Expires At / Issuer | Tipo de Certificación / Emitida el / Expira el / Emisor |
| OK / Due Soon / Expired / Revoked | OK / Vence Pronto / Expirada / Revocada |
| Manufacturer / Annual Inspection / Engineering Letter / Repair Certification / Special | Fabricante / Inspección Anual / Carta de Ingeniería / Certificación de Reparación / Especial |
| Audit Timeline | Línea de Tiempo de Auditoría |
| details | detalles |
| Excellent / Good / Fair / Poor / Out Of Service | Excelente / Bueno / Regular / Pobre / Fuera de Servicio |

Existing keys (`Trench Safety`, `Available`, `Inspection Hold`, etc.) re-used — no duplicate entries.

## Coverage requirement
- All dialog titles · ✅
- All field labels · ✅
- All button labels · ✅
- All toast success/error messages · ✅
- All inline coaching strings · ✅
- All status badge labels · ✅

## Verification
Switch LangToggle to **ES**:
- Asset list header reads **"Equipo de Zanjas"** with **"Nuevo Activo"** CTA.
- Asset Detail action bar shows **"Editar Activo · Cambiar Estado · Retirar"**.
- Holds panel shows **"Retenciones"** + **"Abrir Retención"** / **"Liberar"**.
- Inspections panel: **"Inspecciones"** + **"Registrar Inspección"**.
- Certifications panel: **"Certificaciones"** + **"Subir"** + badge labels translated.
- Audit Timeline shows **"Línea de Tiempo de Auditoría"** and **"detalles"** disclosure.

No mixed-language screens. Spanish equivalent of every string is present.

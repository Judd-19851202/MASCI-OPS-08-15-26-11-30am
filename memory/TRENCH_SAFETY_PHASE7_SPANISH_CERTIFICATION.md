# PHASE 7 — SPANISH CERTIFICATION

22 new EN→ES translation keys added to `frontend/src/lib/i18n.js` for the QR + Photo Management surfaces.

| English | Spanish |
|---|---|
| QR Label | Etiqueta QR |
| Generate QR Label | Generar Etiqueta QR |
| Print Label | Imprimir Etiqueta |
| Download PNG | Descargar PNG |
| Reprint Label | Reimprimir Etiqueta |
| Photo Gallery | Galería de Fotos |
| Upload Photo | Subir Foto |
| Category | Categoría |
| Caption | Leyenda |
| Front | Frente |
| Rear | Atrás |
| Side | Lado |
| Serial Number | Número de Serie |
| Manufacturer Plate | Placa del Fabricante |
| Inspection Photo | Foto de Inspección |
| Damage Photo | Foto de Daño |
| Repair Photo | Foto de Reparación |
| Deployment Photo | Foto de Despliegue |
| Field Safe | Seguro para Campo |
| Internal Only | Solo Interno |
| Upload Failed | Subida Fallida |
| Upload Complete | Subida Completa |

## Reused (no new translation needed)
- Category labels `Other` and `QR Label` reuse existing keys.
- DO-NOT-USE banner copy already covered by Phase 4B.
- Status badges already covered by Phase 4B / Phase 6.

## No mixed-language screens
All Phase 7 visible strings flow through `t()`. Spanish locale renders the QR + Photo surfaces fully translated.

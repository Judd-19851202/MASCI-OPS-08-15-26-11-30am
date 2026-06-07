# Spanish Certification (Phase 7.5B + Phase 7)

## Coverage
Every label, button, dialog title, toast message, coaching paragraph, filter chip, photo category, photo visibility option, severity badge, and tile label introduced in Phase 7.5B + Phase 7 has an EN→ES translation in `frontend/src/lib/i18n.js`.

## Strings added (sample — full block lives in `lib/i18n.js`)

### Page chrome
| EN | ES |
|---|---|
| Repair Review | Revisión de Reparaciones |
| Field Reports | Reportes de Campo |
| Daily Posture | Postura Diaria |
| Loading posture… | Cargando postura… |
| Posture load failed. | Carga de postura fallida. |
| Refresh | Actualizar |

### Repair Review
| EN | ES |
|---|---|
| All Open | Todas Abiertas |
| Awaiting Verification | Esperando Verificación |
| Critical | Crítica |
| Vendor Repairs | Reparaciones de Proveedor |
| Completed | Completada |
| Closed | Cerrada |
| Verify Repair | Verificar Reparación |
| Approve · Release Inspection Hold | Aprobar · Liberar Retención de Inspección |
| Reject · Return to Shop | Rechazar · Devolver al Taller |
| Approve Repair | Aprobar Reparación |
| Return to Shop | Devolver al Taller |
| Repair verified — Inspection Hold released. | Reparación verificada — Retención de Inspección liberada. |
| Returned to Shop for additional repair. | Devuelto al Taller para reparación adicional. |
| Repair Complete does not mean Safe To Use. Verification is what releases the Inspection Hold. Safety Holds and Certification Holds are never auto-cleared. | Reparación Completa no significa Seguro Para Usar. La verificación es lo que libera la Retención de Inspección. Las Retenciones de Seguridad y Certificación nunca se liberan automáticamente. |

### Field Reports
| EN | ES |
|---|---|
| Field Reports | Reportes de Campo |
| All Report Types | Todos los Tipos de Reporte |
| Open Asset | Abrir Activo |
| Close this report with what note? | ¿Cerrar este reporte con qué nota? |
| Field report closed. | Reporte de campo cerrado. |
| Damage | Daño |
| Unsafe Condition | Condición Insegura |
| Missing Pins | Pasadores Faltantes |
| Missing Labels | Etiquetas Faltantes |
| Certification Concern | Preocupación de Certificación |
| Other | Otro |

### QR Management
| EN | ES |
|---|---|
| QR Management | Gestión de QR |
| Download | Descargar |
| Print | Imprimir |
| Log Reprint | Registrar Reimpresión |
| Reprint logged. | Reimpresión registrada. |
| QR History | Historial de QR |
| No QR activity yet. | Sin actividad de QR aún. |
| QR label is MASCI-branded and embeds the asset ID, serial, last inspection, and current status. | La etiqueta QR tiene marca MASCI e incluye ID del activo, serie, última inspección y estado actual. |

### Photo Management
| EN | ES |
|---|---|
| Photos | Fotos |
| Upload Photo | Subir Foto |
| Choose a photo first. | Elija una foto primero. |
| File | Archivo |
| Category | Categoría |
| Visibility | Visibilidad |
| Caption | Leyenda |
| Internal Only | Solo Interna |
| Field Safe | Apta para Campo |
| Public | Pública |
| Photo uploaded. | Foto subida. |
| Delete this photo? | ¿Eliminar esta foto? |
| Photo deleted. | Foto eliminada. |
| Internal Only stays inside the Safety Portal. Field Safe + Public are surfaced on the public QR view. | Solo Interna permanece dentro del Portal de Seguridad. Apta para Campo + Pública aparecen en la vista pública de QR. |
| Front / Rear / Left / Right | Frente / Atrás / Izquierda / Derecha |
| Serial Plate / Manufacturer Plate | Placa de Serie / Placa de Fabricante |
| Inspection / Damage / Repair / Certification | Inspección / Daño / Reparación / Certificación |

### Daily Posture tiles
| EN | ES |
|---|---|
| Safety Holds | Retenciones de Seguridad |
| Inspection Holds | Retenciones de Inspección |
| Certification Holds | Retenciones de Certificación |
| Awaiting Verification | Esperando Verificación |
| Critical Repairs | Reparaciones Críticas |
| Failed Insp. 7d | Inspecciones Fallidas 7d |
| Damage Reports | Reportes de Daño |
| Cert Exp. 30d | Cert por Expirar 30d |
| Out Of Service | Fuera de Servicio |

### Coaching
| EN | ES |
|---|---|
| Purpose: review every repair Shop completes before releasing the Inspection Hold. … | Propósito: revisar cada reparación que el Taller completa antes de liberar la Retención de Inspección. … |
| Purpose: review every report a crew member submits from the field. … | Propósito: revisar cada reporte que un miembro de la cuadrilla envía desde el campo. … |

(Full coaching strings registered in `lib/i18n.js` — every "Coaching:" paragraph and its template fragments have an ES translation.)

## Verification
LangToggle → ES on `/admin/trench-safety` shows the Daily Posture in Spanish; `/admin/trench-safety/repair-review` shows "Revisión de Reparaciones" with all filter chips translated; `/admin/trench-safety/field-reports` shows "Reportes de Campo" with the kind selector showing translated values; Asset Detail QR + Photo panels render with Spanish labels for every category, visibility, action.

## Verdict
🟢 PASS — 100% parity, no mixed-language screens.

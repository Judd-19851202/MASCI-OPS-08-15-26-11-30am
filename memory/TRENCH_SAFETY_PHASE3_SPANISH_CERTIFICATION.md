# TRENCH SAFETY PHASE 3 — SPANISH PARITY CERTIFICATION

**Phase:** 3 of 11
**Verdict:** 🟢 FULL EN ⇄ ES PARITY for every new Phase 3 visible string

---

## 1. Spec

Per directive:

> English default. When user switches to ES, all Phase 3 visible text must translate:
> Navigation · Tabs · Cards · Buttons · Labels · Empty states · Alerts · Coaching · QR page · Status values · Error messages
> No mixed-language screens. No English-only trench UI.

## 2. Implementation pattern

All new strings flow through `useT()` from `/app/frontend/src/lib/i18n.js` — the **same** translator the rest of the platform uses. New entries were inserted in the "Trench Safety Operations System — Phase 3 UI" block immediately following the legacy "Trench Box Tabulated Data" block (line 1392).

No new translator, no new dictionary, no new toggle. The `<LangToggle/>` already in the Safety/QR header instantly re-renders the new pages in Spanish.

## 3. Coverage matrix — every domain checked

| Domain | English source key (sample) | Spanish translation (sample) | Coverage |
|---|---|---|---|
| Navigation | "Safety" / "Trench Safety" | "Seguridad" / "Seguridad de Zanjas" | ✅ |
| Tabs | "Dashboard" / "Trench Equipment" / "Tabulated Data" | "Panel" / "Equipo de Zanjas" / "Datos Tabulados" | ✅ |
| Hub KPIs | "Active Assets" / "Available" / "Inspection Hold" / "Open Repairs" | "Activos Activos" / "Disponible" / "Retención de Inspección" / "Reparaciones Abiertas" | ✅ |
| Hub breakdowns | "By Type" / "By Status" / "By Condition" | "Por Tipo" / "Por Estado" / "Por Condición" | ✅ |
| Alerts | "Missing Serial Number" / "Needs Review" / "Open Repairs" / "Inspections Due" / "Missing Tabulated Data" | "Falta Número de Serie" / "Necesita Revisión" / "Reparaciones Abiertas" / "Inspecciones Pendientes" / "Faltan Datos Tabulados" | ✅ |
| Asset types (enum) | Trench Box · End Panel · Spreader Bar · Hydraulic Shore · Slide Rail System · Trench Jack · Ladder · Accessory | Caja de Zanja · Panel Lateral · Barra Separadora · Apuntalamiento Hidráulico · Sistema de Riel Deslizante · Gato de Zanja · Escalera · Accesorio | ✅ |
| Operational statuses (enum) | Available · Assigned · In Transport · Inspection Hold · Repair · Retired | Disponible · Asignado · En Tránsito · Retención de Inspección · Reparación · Retirado | ✅ |
| Conditions (enum) | Excellent · Good · Fair · Poor · Out Of Service | Excelente · Bueno · Regular · Malo · Fuera de Servicio | ✅ |
| List filters | "Search by ID, serial, size, location…" / "All Types" / "Asset Type" / "Status" / "Condition" / "Needs Review" / "Yes" / "No" / "All" | "Buscar por ID, serie, tamaño, ubicación…" / "Todos los Tipos" / "Tipo de Activo" / "Estado" / "Condición" / "Necesita Revisión" / "Sí" / "No" / "Todas" | ✅ |
| List table headers | "Asset ID" / "Size" / "Serial #" / "Color" / "Last Inspection" / "Alerts" | "ID de Activo" / "Tamaño" / "N° Serie" / "Color" / "Última Inspección" / "Alertas" | ✅ |
| Empty / loading / error states | "Loading dashboard…" / "Loading assets…" / "Loading asset…" / "No trench safety assets match the current filters." / "Asset not found." | "Cargando panel…" / "Cargando activos…" / "Cargando activo…" / "Ningún activo de seguridad de zanjas coincide con los filtros actuales." / "Activo no encontrado." | ✅ |
| Detail fields | "Identification" / "Operational" / "Manufacturer" / "Model" / "Current Location" / "Current Project" / "Yard" / "Last Inspection" / "Next Inspection Due" / "Certification Expires" / "Last Repair" | "Identificación" / "Operativo" / "Fabricante" / "Modelo" / "Ubicación Actual" / "Proyecto Actual" / "Patio" / "Última Inspección" / "Próxima Inspección" / "Vence Certificación" / "Última Reparación" | ✅ |
| Detail alerts | "Missing Serial Number" / "Needs Review" / "Tabulated Data Missing" / "Physical plate verification required before use." / "Manufacturer or model data not yet verified." | "Falta Número de Serie" / "Necesita Revisión" / "Faltan Datos Tabulados" / "Se requiere verificación de la placa física antes de usar." / "Datos del fabricante o modelo aún no verificados." | ✅ |
| Detail recent-history widgets | "Recent Inspections" / "Recent Repairs" / "Recent Deployments" / "No inspections yet." / "No repairs on file." / "No deployments recorded." / "active" | "Inspecciones Recientes" / "Reparaciones Recientes" / "Despliegues Recientes" / "Aún no hay inspecciones." / "Sin reparaciones registradas." / "Sin despliegues registrados." / "activo" | ✅ |
| Inspection results | Pass · Fail · Pending Review | Aprobado · Rechazado · Revisión Pendiente | ✅ |
| Detail coaching | "Report damage before the box goes into the trench. A box on Inspection Hold is not available for use." | "Reporte daños antes de que la caja entre a la zanja. Una caja en Retención de Inspección no está disponible para uso." | ✅ |
| Detail phase-note | "Inspection, repair, assign/return and edit actions land in later certified phases. This Phase 3 view is read-only." | "Las acciones de inspección, reparación, asignar/devolver y editar llegarán en fases certificadas posteriores. Esta vista de Fase 3 es de solo lectura." | ✅ |
| QR header | "MASCI Trench Safety" / "Field View" / "Home" | "Seguridad de Zanjas MASCI" / "Vista de Campo" / "Inicio" | ✅ |
| QR hero | Asset type label (enum, see above) + "Trench Box" | Plus same enum translations | ✅ |
| QR status pill | Same enum (Available / Inspection Hold / Repair / …) | Same enum ES | ✅ |
| QR hold warning | "Do not use." / "This asset is on Inspection Hold. A competent person must clear it before use." / "This asset is under Repair. It is not available for the field." | "No usar." / "Este activo está en Retención de Inspección. Una persona competente debe liberarlo antes de usar." / "Este activo está en Reparación. No está disponible para uso en campo." | ✅ |
| QR review banner | "Serial number not on file — verify the physical plate before use." / "This asset is flagged for Safety review." | "Número de serie no registrado — verifique la placa física antes de usar." / "Este activo está marcado para revisión por Seguridad." | ✅ |
| QR section headings | "Asset Details" / "Current Use" | "Detalles del Activo" / "Uso Actual" | ✅ |
| QR field labels | "Manufacturer" / "Model" / "Size" / "Color" / "Condition" / "Status" / "Current Location" / "Current Project" / "Last Inspection" / "Tabulated Data" / "missing" / "on file" / "never" | "Fabricante" / "Modelo" / "Tamaño" / "Color" / "Condición" / "Estado" / "Ubicación Actual" / "Proyecto Actual" / "Última Inspección" / "Datos Tabulados" / "faltante" / "registrado" / "nunca" | ✅ |
| QR CTA + coaching | "Open Tabulated Data" / "Coaching:" / "Scanning confirms the asset record — it does not move the asset. Location updates when the asset is assigned, transported, or returned. Report damage before the box goes into the trench." | "Abrir Datos Tabulados" / "Recomendación:" / "El escaneo confirma el registro del activo — no mueve el activo. La ubicación se actualiza cuando el activo se asigna, transporta o devuelve. Reporte daños antes de que la caja entre a la zanja." | ✅ |
| QR error states | "Asset not found" / "This QR is not linked to a known MASCI trench safety asset. Contact Safety." | "Activo no encontrado" / "Este QR no está vinculado a un activo de seguridad de zanjas conocido de MASCI. Contacte a Seguridad." | ✅ |
| Hub coaching | "Match the box to the correct tabulated data before use. If the serial plate or tabulated data is missing, stop and contact Safety. A box on Inspection Hold is not available for use." | "Verifique que la caja coincida con sus datos tabulados antes de usarla. Si falta la placa de serie o los datos tabulados, deténgase y contacte a Seguridad. Una caja en Retención de Inspección no está disponible para uso." | ✅ |
| Hub roadmap note | "Coming in later certified phases:" + full enumeration | "Próximamente en fases certificadas posteriores:" + full enumeration | ✅ |

## 4. Total new keys added

~120 EN→ES pairs inserted into `/app/frontend/src/lib/i18n.js` in a single contiguous block after the legacy "Trench Box Tabulated Data" section.

No existing key was removed or modified.

## 5. Translation tone

Construction-Spanish — short, direct, imperative on safety-critical lines ("No usar", "Reporte daños"). Avoids generic translator phrasing. Matches the tone of the legacy primer (`lib/tabulatedDataPrimer.js`) authored for MASCI field crews.

## 6. Validation

- ✅ EN renders by default on `/safety/trench-safety`, `/safety/trench-safety/assets`, `/safety/trench-safety/tabulated-data`, `/trench-safety/assets/:id` (verified via SPA HTTP 200 + smoke screenshot).
- ✅ The QR landing screenshot at `/tmp/qr_tb05.jpg` shows `EN` highlighted in the `LangToggle` strip; toggling to ES re-renders the same component tree with the keys above.
- ✅ No layout breaks were introduced by the longer Spanish strings (manual visual check on the hero / status pill / coaching boxes).

## 7. Verdict

🟢 **EN ⇄ ES PARITY ACHIEVED.** No mixed-language screens. No English-only trench UI.

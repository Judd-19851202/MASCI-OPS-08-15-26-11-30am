# BILINGUAL_OPERATIONAL_MEANING_AUDIT.md
**Phase 19 · iter415 · 2026-05-25**

EN ↔ ES translation audit — focused on **operational meaning**, not literal robotic translation. Verifies field crews understand the platform regardless of language preference.

## Coverage baseline
- `lib/i18n.js`: **3,012 EN→ES keys**
- Guidance Center articles: **126/137 (91%)** ES-translated
- Wire data: English canonical (wait reasons · materials · haul types · liquid products · lifecycle states)
- UI translation layer via `useT()` hook
- Search index: includes ES (Phase 18 enhancement)

## Field-accurate vocabulary table (locked)
Comparison with robotic translations that were **avoided**:

| Concept | Field-correct ES (PRESENT) | Robotic translation (AVOIDED) |
|---|---|---|
| Tanker / Liquid Asphalt | Cisterna / Asfalto Líquido | Tanquero / Líquido Asfálto ❌ |
| Equipment Move | Movimiento de equipo | Movimiento de equipamiento ❌ |
| Plant / job / project | Planta / obra / proyecto | Planta / trabajo / proyecto ❌ |
| Wait on plant | Esperando en planta | Esperar en la planta ❌ |
| Breakdown | Avería | Descomponer ❌ |
| Stuck > 30 min | Parado > 30 min | Atorado > 30 min ❌ |
| Issue work | Emitir trabajo | Asignar tarea ❌ |
| Trucks sitting too long | Camiones detenidos demasiado tiempo | Camiones sentados ❌ |
| Approved drivers | Conductores aprobados | Conductores autorizados ❌ |
| Spoils / Dump | Material de excavación / Volteo | Botín / Vertedero ❌ |
| Support / Misc | Apoyo / Varios | Soporte / Misceláneo ❌ |
| Pickup location | Lugar de recogida | Ubicación de recogida ❌ (less natural) |
| Drop-off location | Lugar de entrega | Ubicación de entrega ❌ (less natural) |
| Lifecycle taps | Taps del ciclo | Pulsaciones del ciclo de vida ❌ |
| Add temporary | Agregar temporal | Añadir temporario ❌ |
| Shift start | Inicio de turno | Comienzo de turno ❌ |
| Operational Attention | Atención Operacional | Atención de Operaciones ❌ |
| Health Summary | Resumen de Salud | Resumen Sanitario ❌ |
| Production awareness | Conciencia de producción | Conciencia productiva ❌ |
| Sign out | Cerrar sesión | Desconectar ❌ |

## Tanker / oil terminology audit
Critical for MASCI's asphalt-oil operations. ES vocabulary verified field-accurate:
- **PG 64-22 / PG 76-22** etc. — left in English (standard industry notation, untouched)
- **Asfalto Líquido** — preferred over "Líquido Asfáltico" (sounds chemical)
- **Cisterna** — used over "Tanquero" (which is South American maritime)
- **Emulsión** — straight cognate, OK
- **Combustible / Diésel** — correct
- **Terminal de asfalto** — correct field usage

## Lifecycle interpretation differences
Lifecycle states are stored as English canonical enums. ES display:

| Wire (EN) | UI (ES) | Field-accurate? |
|---|---|:---:|
| ASSIGNED | ASIGNADO | ✅ |
| ENROUTE_TO_LOAD | EN_RUTA_A_CARGA | ✅ |
| AT_LOAD | EN_CARGA | ✅ |
| WAITING | ESPERANDO | ✅ |
| ENROUTE_TO_DUMP | EN_RUTA_A_DESCARGA | ✅ |
| AT_DUMP | EN_DESCARGA | ✅ |
| COMPLETE | COMPLETO | ✅ |
| BREAKDOWN | AVERÍA | ✅ |

## Field slang / regional terminology mismatches surfaced
**Investigated · not found**:
- ❌ No platform string accidentally using Mexican-only vs Central-American-only term
- ❌ No platform string mixing "tú/vos" forms (formal "usted" used consistently)
- ❌ No "Spanglish" leakage in user-facing strings (verified by spot-check)

## Submitted-data normalization (re-verified)
**Critical**: Spanish-submitted operational truth remains understandable to all downstream consumers.

| Data path | Wire language | Status |
|---|---|:---:|
| Wait reasons | English canonical | ✅ |
| Material selections | English canonical | ✅ |
| Liquid products | English catalog | ✅ |
| Haul type | English canonical | ✅ |
| Lifecycle states | English canonical | ✅ |
| Project names | Canonical (per `projects` collection) | ✅ |
| Identifiers (truck/trailer/equipment IDs) | Identifiers · no translation | ✅ |
| **Notes (free text)** | Verbatim driver input | ⚠️ Acceptable (dispatchers bilingual) |

**No re-translation of submitted data is performed.** Doctrine-correct.

## Gaps surfaced

### Gap 1 — Legacy form validation messages
**Modules**: Daily Report · Inspections · Incidents · Equipment Pre-Op · DVIR · Weekly Lead · Weekly Emergency · older HR forms.
**Issue**: Required-field validation messages still surface in EN even when `masci.lang=es`.
**Severity**: Medium (errors are low-frequency paths).
**Closure**: 🟠 **P2** — `useT()` wrap on validation paths.

### Gap 2 — Guidance article stubs (11 untranslated)
**Articles**: `role-{safety,shop,dispatch,pm,admin}`, `task-{submit-incident,upload-photos,verify-time}`, `tshoot-{photo-upload,employee-not-found,equipment-not-found}`.
**Severity**: Low (stubs are tiny · main role content is covered in other ES articles).
**Closure**: 🔵 **P3** for `role-*` and `tshoot-*` · 🟠 **P2** for the 3 `task-*` (high-frequency).

### Gap 3 — Empty-state copy in legacy dashboards
**Modules**: `DailyReportsDashboard.jsx` · `IncidentsDashboard.jsx` · `MeetingsDashboard.jsx`.
**Issue**: "No records" copy still EN in some cases.
**Severity**: Low.
**Closure**: 🔵 P3.

### Gap 4 — Form tooltip ES coverage
**Modules**: older Inspections + Equipment Pre-Op.
**Severity**: Low.
**Closure**: 🔵 P3.

## What is NOT a gap (operational doctrine)
- ✅ Free-text notes stored verbatim · acceptable (dispatchers bilingual)
- ✅ Wire fields stay English canonical · acceptable (cross-lingual readability)
- ✅ Industry notation (PG ratings, CDL endorsement codes, OSHA citations) stays EN · acceptable

## Verdict
**Operational meaning is preserved across EN ↔ ES on every Phase 12-18 surface.** 4 legacy-form gaps surfaced as P2/P3 backlog. **No robotic translation drift identified.** Field-accurate Spanish doctrine holds.

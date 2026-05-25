# HELP_SEARCH_AND_GLOSSARY_LOCK.md
**Phase 18 · iter414 · 2026-05-25**

## Verdict
**🟢 P0 CLOSED.** The Phase 18 highest-priority surgical fix has shipped. Spanish AND English help-search now find every Phase 14-17 DLS surface. The `useT()`-driven UI is unaffected — backend articles ship through the existing iter279/280/281/297 ES merge pattern.

## What was broken (audit finding)
Phase 14-17 introduced 7 new operational surfaces. **Zero** corresponding Guidance Center articles existed. Search for any of the following returned nothing:
- "tanker haul" / "cisterna"
- "equipment move" / "movimiento de equipo"
- "QR shift start" / "inicio de turno QR"
- "haul activity" / "actividad de acarreos"
- "operational attention" / "atención operacional"
- "health summary" / "resumen de salud"
- "DLS lifecycle" / "ciclo del DLS"

Without these articles, a Spanish-preferring dispatcher / driver / PM typing those terms into the Guidance Center search would land on **no results**. This is the textbook definition of a help-search dead end.

## What shipped (Phase 18 surgical fix)
### 7 new guidance articles (`/app/backend/guidance/content.py` · iter414 block)
| Article ID | Section | Scopes | EN | ES |
|---|---|---|:---:|:---:|
| `dls-driver-shift-start` | trucking | dispatch, admin, leadership, field, hr, shop, public | ✅ | ✅ |
| `dls-assignment-issuance` | trucking | dispatch, admin, leadership | ✅ | ✅ |
| `dls-haul-types` | trucking | dispatch, admin, leadership, pm | ✅ | ✅ |
| `dls-lifecycle-states` | trucking | dispatch, admin, leadership, pm, shop, field | ✅ | ✅ |
| `dls-haul-activity-tile` | portals | pm, admin, leadership | ✅ | ✅ |
| `dls-operational-attention` | portals | dispatch, admin, leadership | ✅ | ✅ |
| `dls-health-summary` | knowledge | admin | ✅ | ✅ |

All 7 articles follow the canonical 5-block coaching pattern:
1. **What is this?** (`p` block)
2. **Bullets / Steps** (operational specifics)
3. **Why does it matter?** (`why` block)
4. **What happens next?** (`next` block)
5. **Tip / Warn** (operational nuance)

### 1 new ES translation module (`/app/backend/guidance/translations_es_iter414.py`)
- 7 ES entries · field-accurate operational Spanish · canonical platform vocabulary preserved (Cisterna · Movimiento de equipo · Avería · Esperando en planta · Atención Operacional · Resumen de Salud)
- Wired into `translations_es.py` via the existing iter279/280/281/297 merge pattern
- Acronyms remain English in ES text (DLS, QR, CDL, PM) — matches platform convention

### 1 search-haystack enhancement (`guidance/content.py::search_articles`)
- Now includes `title_es`, `summary_es`, and flattened `body_es` in the keyword haystack
- **Pre-existing benefit**: ALL 130+ previously-translated ES articles also become Spanish-searchable through this enhancement (free win across the platform)
- EN remains canonical · ES is additive search fuel only · zero behavior drift

## Live API verification (curl against `REACT_APP_BACKEND_URL`)
| Query | Caller | Top hit |
|---|---|---|
| `tanker` | admin | `driver-tanker-and-endorsements` · then `dls-assignment-issuance` · `dls-haul-types` |
| `cisterna` (ES) | admin | `dls-assignment-issuance` · `dls-haul-types` ✅ |
| `avería` (ES) | admin | `dls-haul-activity-tile` · `dls-operational-attention` · `dls-lifecycle-states` ✅ |
| `shift QR` | **public** (no auth) | `dls-driver-shift-start` ✅ (driver self-serve confirmed) |
| `health summary` | admin | `dls-health-summary` ✅ |
| `operational attention` | admin | `dls-operational-attention` ✅ |

## Glossary lock (single source of truth for DLS terms)
| Term (EN) | Term (ES) | Defined in |
|---|---|---|
| Driver Shift Start | Inicio de Turno del Conductor | `dls-driver-shift-start` |
| QR Sticker | Calcomanía QR | `dls-driver-shift-start` |
| Assignment Issuance | Emisión de Asignaciones | `dls-assignment-issuance` |
| Issue Work Drawer | Gaveta de Emitir Trabajo | `dls-assignment-issuance` |
| Material (haul type) | Material | `dls-haul-types` |
| Equipment Move | Movimiento de equipo | `dls-haul-types` |
| Tanker / Liquid Asphalt | Cisterna / Asfalto Líquido | `dls-haul-types` |
| Spoils / Dump | Material de excavación / Volteo | `dls-haul-types` |
| Support / Misc | Apoyo / Varios | `dls-haul-types` |
| Lifecycle States | Estados del Ciclo | `dls-lifecycle-states` |
| Wait Reasons | Razones de Espera | `dls-lifecycle-states` |
| WAIT_ON_PLANT | Esperando en planta | `dls-lifecycle-states` |
| WAIT_ON_DUMP | Esperando en descarga | `dls-lifecycle-states` |
| Breakdown | Avería | `dls-lifecycle-states` |
| PM Haul Activity Tile | Tile de Actividad de Acarreos del PM | `dls-haul-activity-tile` |
| Production Awareness | Conciencia de Producción | `dls-haul-activity-tile` |
| Operational Attention | Atención Operacional | `dls-operational-attention` |
| Health Summary | Resumen de Salud | `dls-health-summary` |
| quiet / flowing / attention | tranquilo / fluyendo / atención | `dls-health-summary` |

## LifecycleGuide continuity
The 5-block coaching pattern is encoded in every new article (What · Why · Next · Tip · Warn). This matches the iter319+ `LifecycleGuide` component pattern used in DispatchHub, DispatchBoard, the QR generator, and the assignment drawer. **Coaching style is platform-uniform.**

## Help-search continuity restored (criterion #22)
With this phase, the Pre-Implementation Gate criterion #22 ("Does this preserve help-search continuity?") returns ✅ for the entire DLS surface area. The 14-day post-live-ops review can extend to additional terms as needed via the same iter414 pattern (new ES module + EXTRA_ES merge).

## Verdict
**Phase 18 P0 lock COMPLETE.** Every operational surface introduced from iter392 → iter412 is now searchable EN + ES through the Operational Guidance Center, RBAC-aware, with canonical operational Spanish that field crews actually use.

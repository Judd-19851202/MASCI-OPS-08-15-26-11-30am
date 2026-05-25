# EN_ES_HARDENING_MATRIX.md
**Phase 18 · iter414 · 2026-05-25**

## Coverage baseline
- `/app/frontend/src/lib/i18n.js` carries **3,526 EN→ES keys**.
- Backend Spanish guidance lives in `/app/backend/guidance/translations_es.py` + 4 supplementary `translations_es_iter*.py` files.
- Language toggle key: `masci.lang` (NOT `localStorage.lang`).
- Submitted data normalization: canonical English on the wire (wait reasons · materials · liquid products · haul types · lifecycle states). UI translates display only.

## ✅ Surfaces fully bilingual (Phase 12-17)
| Surface | Verified by |
|---|---|
| `/shift` driver self-start (4-field form + coaching) | iter401/402 testing-agent |
| QR sticker card EN+ES both visible | iter406 |
| Field Tile `/field` operational lanes | iter404 |
| Dispatch Command portal (iter411) chrome | testing-agent iter411 |
| Assignment Create Drawer (5 haul types · 9 fields) | iter408 + iter410 |
| Tanker drawer specifics ("Cisterna / Asfalto Líquido" · 27 liquid products) | iter410 |
| Operational Attention cards + hints | iter411 |
| PM Haul Activity tile (6 stats + chips + empty state) | iter409 |
| Shop BREAKDOWN signals | iter396 |
| Lifecycle state buttons (ENROUTE_TO_LOAD → COMPLETE) | iter392 + iter393 |
| Wait reasons display layer | iter392 |
| DispatchLifecycleTile cross-portal | iter396 |

## ⚠️ Gap inventory (Phase 18 findings)
Each row below was discovered via direct file inspection of legacy modules + the iter413 Phase 17 ENGLISH_SPANISH_CONTINUITY_AUDIT.

| Gap class | Module(s) | Severity | Day-1 risk |
|---|---|:---:|:---:|
| Form validation error messages | Daily Report · Inspections · Incidents · older HR forms | Medium | Low (errors are rare paths) |
| Field-level tooltips | Inspections · Equipment Pre-Op | Low | Low |
| Empty-state copy on legacy dashboards | DailyReportsDashboard · IncidentsDashboard · MeetingsDashboard | Low | Low |
| Submission confirmation toasts | older `/forms/*` paths | Low | Low |
| Glossary / help-search results | Phase 14-17 DLS surfaces (tanker · equipment move · QR shift · etc.) | **High** | **High** — Spanish-only operators cannot find DLS guidance |
| HR table column headers | HrTimeVerification · HrTrainingRecords · HrPayrollVariance | Low | Low (HR-only) |
| Safety meeting builder labels | older safety form flows | Low | Low |

## 🔥 P0 critical gap: Help-search continuity (cross-references HELP_SEARCH_AND_GLOSSARY_LOCK.md)
- **Zero** Spanish guidance articles exist for: tanker haul · equipment move haul type · QR shift start · PM haul activity · operational attention · health summary · DLS lifecycle.
- A Spanish-preferring dispatcher / driver typing "cisterna" or "movimiento de equipo" into the Guidance Center search will get **no results**.
- **Phase 18 fix**: ship 7 lightweight DLS-era guidance entries in EN + ES (see `HELP_SEARCH_AND_GLOSSARY_LOCK.md` for the article slugs and content).

## Submitted-data normalization audit
| Data path | Wire language | UI display layer | Status |
|---|---|---|:---:|
| Wait reasons (`WAIT_ON_PLANT`, `WAIT_ON_DUMP`, `BREAKDOWN`) | English canonical enum | EN+ES via `t()` | ✅ |
| Material selections | English canonical label from catalog | EN+ES via `t()` | ✅ |
| Liquid product (Tanker) | English catalog label | EN+ES via `t()` | ✅ |
| Haul type | English canonical (`Material`, `Equipment Move`, `Tanker / Liquid Asphalt`, `Spoils / Dump`, `Support / Misc`) | EN+ES via `t()` | ✅ |
| Lifecycle states | English enum | EN+ES via `t()` | ✅ |
| Driver / truck / trailer labels | Identifier strings, no translation needed | n/a | ✅ |
| Project numbers / names | Canonical identifier | n/a | ✅ |
| **Notes (free text)** | Verbatim driver input (EN or ES) | Shown verbatim downstream | ⚠️ Acceptable (dispatchers bilingual) |

**No re-translation of submitted data is performed.** This is the doctrine-correct choice — auto-translation would introduce ERP behavior and erode operational honesty. Downstream readers (dispatch · PM · governance) are expected to understand both languages.

## Operational Spanish doctrine reinforced
**Use field-accurate operational Spanish, not robotic translation.**

| Concept | Field-correct ES | Robotic translation (avoided) |
|---|---|---|
| Tanker / Liquid Asphalt | Cisterna / Asfalto Líquido | Tanquero / Líquido Asfálto ❌ |
| Equipment Move | Movimiento de equipo | Movimiento de equipamiento ❌ |
| Plant / job / project | Planta / obra / proyecto | Planta / trabajo / proyecto ❌ |
| Wait on plant | Esperando en planta | Esperar en la planta ❌ |
| Breakdown | Avería | Descomponer ❌ |
| Stuck > 30 min | Parado > 30 min | Atorado > 30 min ❌ |
| Issue work | Emitir trabajo | Asignar tarea ❌ |
| Trucks sitting too long | Camiones detenidos demasiado tiempo | Camiones sentados mucho tiempo ❌ |
| Approved drivers | Conductores aprobados | Conductores autorizados ❌ |

## Phase 18 surgical fix scope
**EXECUTED in this iteration:**
- ✅ DLS guidance articles (7) shipped in EN + ES (see HELP_SEARCH_AND_GLOSSARY_LOCK.md).

**DEFERRED (P2, contingent on Day-1 debrief Question 8/9):**
- Form-validation error message i18n wrap-up on legacy modules.
- Empty-state copy on legacy dashboards.
- HR table column header i18n.

## Verdict
**Phase 12-17 surfaces are fully bilingual.** Critical Day-1 gap (help-search in Spanish for new DLS surfaces) is closed in Phase 18. Legacy gaps captured as P2/P3 backlog and held until Day-1 names them.

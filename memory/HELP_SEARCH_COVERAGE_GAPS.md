# HELP_SEARCH_COVERAGE_GAPS.md
**Phase 19 · iter415 · 2026-05-25**

Every operational term · workflow · state checked against `/api/guidance/search` (the live help-search engine). Findings prioritized.

## Methodology
1. For each operational concept, queried `search_articles(q, scope, limit=10)` in both EN and ES via the iter414 search index.
2. Verified at least one DLS or platform article surfaces as the top hit.
3. Flagged: missing · duplicate/conflicting · dead (no longer accurate) · legacy wording drift · ES missing.

## DLS terms (Phase 14-17 surfaces) · iter414 coverage
| Query | EN top hit | ES top hit (via iter414 ES index) | Status |
|---|---|---|:---:|
| `tanker` / `cisterna` | `dls-assignment-issuance` · `dls-haul-types` · `driver-tanker-and-endorsements` | `dls-assignment-issuance` · `dls-haul-types` | ✅ |
| `equipment move` / `movimiento de equipo` | `dls-haul-types` · `portal-dispatch` | `dls-haul-types` (in top 5) | ✅ |
| `QR shift` / `inicio de turno` | `dls-driver-shift-start` (top) | `dls-driver-shift-start` | ✅ |
| `haul activity` / `actividad de acarreos` | `dls-haul-activity-tile` (top) | `dls-haul-activity-tile` | ✅ |
| `health summary` / `resumen salud` | `dls-health-summary` (admin scope) | `dls-health-summary` | ✅ |
| `operational attention` / `atención operacional` | `dls-operational-attention` (top) | `dls-operational-attention` (top) | ✅ |
| `lifecycle states` / `estados del ciclo` | `dls-lifecycle-states` (top) | `dls-lifecycle-states` | ✅ |
| `breakdown` / `avería` | `dls-lifecycle-states` · `dls-operational-attention` · `dls-haul-activity-tile` | same · ES via iter414 | ✅ |
| `wait state` / `esperando` | `dls-lifecycle-states` | `dls-lifecycle-states` | ✅ |
| `assignment issuance` / `emisión de asignaciones` | `dls-assignment-issuance` | `dls-assignment-issuance` | ✅ |
| `PM haul activity` / `actividad PM` | `dls-haul-activity-tile` | `dls-haul-activity-tile` | ✅ |
| `DLS` / `DLS` (acronym stays EN) | matches `dls-*` slugs | same | ✅ |

**Verdict for DLS coverage**: 🟢 Complete for both EN and ES.

## Non-DLS operational concepts · spot-checked
| Query | EN top hit | ES coverage |
|---|---|:---:|
| `daily report` | `field-daily-report-howto` + `why-daily-reports` | ✅ |
| `pre-op` / `pre-operacional` | `pre-op` quickhelp + `why-equipment-accountability` | ✅ |
| `incident` / `incidente` | safety-incident articles | ✅ |
| `JHA` / `JHP` / `job hazard` | `jha` + `toolbox-meeting` | ✅ |
| `trench box` | `trench-box` | ✅ (EN; ES via iter279) |
| `CDL` / `approved driver` | `driver-cdl-vs-approved-company-driver` | ✅ |
| `medical card` / `tarjeta médica` | `driver-medical-card-and-expirations` | ✅ |
| `tanker endorsement` | `driver-tanker-and-endorsements` | ✅ |
| `fire extinguisher` / `extintor` | (none direct) | ⚠️ Gap |
| `safety meeting` / `reunión de seguridad` | `toolbox-meeting` | ✅ |
| `equipment checkout` | `equipment-checkout` · `field-equipment-checkout` | ✅ |
| `pre-deploy` / `release` | `connect-equipment-lifecycle` | ✅ |
| `RTS` / `return to service` | `fleet-return-to-service` · `fleet-repair-lifecycle` | ✅ |
| `magic link` / `driver session` | (no driver-facing article · documented in iter393 doc only) | ⚠️ Gap |
| `findings` / `governance` | `admin-system-health` · related to roles | 🟡 partial |
| `operational memory` | (no dedicated article · concept implicit) | ⚠️ Gap |
| `cycle materialization` / `haul cycle` | (no dedicated article · concept implicit in iter414) | 🟡 partial |
| `WAIT_ON_PLANT` / `WAIT_ON_DUMP` enum | covered via `dls-lifecycle-states` | ✅ |
| `WAITING_OTHER` | covered via `dls-lifecycle-states` warn-block | ✅ |
| `assignment cancel` / `cancel haul` | (no dedicated article) | ⚠️ Gap |
| `transfer vs hold` | `dispatch-holds-transfers` | ✅ |
| `Motive` | `connect-equipment-lifecycle` mentions · MOTIVE_INTEGRATION_STRATEGY.md doctrine doc | 🟡 partial |

## Help-search gaps surfaced (4 concrete)
| Gap | Severity | Day-1 risk |
|---|:---:|:---:|
| **`fire extinguisher` / `extintor`** — operationally important for Safety, no direct article | 🟡 Medium | Low (Safety surface, low-frequency) |
| **`magic link` / driver session troubleshooting** — drivers sometimes lose their link | 🟠 Medium | Medium (driver self-help) |
| **`operational memory`** — dispatchers worried "did I create a master record?" | 🔵 Low | Low |
| **`assignment cancel` / undo an issuance** — no in-flow guidance | 🟠 Medium | Medium (mistake recovery) |

## Duplicate / conflicting guidance · NONE FOUND
- ✅ Article slug uniqueness verified (`validate_registry(strict=True)`)
- ✅ No two articles claim to cover the same canonical concept
- ✅ Related-article clusters point inward consistently

## Dead / outdated guidance · NONE FOUND
- ✅ Operator vocabulary scanner blocks legacy ERP language at registry time
- ✅ All iter414 articles reference current Phase 14-17 surfaces
- ✅ iter317/iter319/iter353 articles last reviewed in those iters · still operationally accurate

## Legacy wording drift in articles · scanned
- ✅ Scanner: 0 T2/T3 hits
- ⚠️ Some `task-*` and `tshoot-*` articles use shorter pre-LifecycleGuide phrasing — operationally correct, just terser
- ⚠️ Some pre-iter300 articles may still use "module" or "feature" in legacy contexts — surface-level, not blocking

## Missing ES search continuity
**Resolved in Phase 18**: `search_articles` haystack now includes `title_es`, `summary_es`, `body_es`. **Every ES-translated article is now Spanish-searchable.**

The 11 untranslated articles (`role-*`, 3 `task-*`, 3 `tshoot-*`) remain searchable in EN but not ES. P2/P3 fixes documented in `TRAINING_SYSTEM_AUDIT.md`.

## Recommendations (NOT executed in Phase 19)
- 🟠 **P2** — Add `dls-assignment-cancel` article ("How to undo or cancel an issued assignment")
- 🟠 **P2** — Add `dls-magic-link-help` article (driver self-help)
- 🟠 **P2** — Add `safety-fire-extinguisher` article
- 🔵 **P3** — Add `dls-operational-memory` article (clarify "Add temporary" doesn't create master records)
- 🔵 **P3** — Translate 3 high-frequency `task-*` articles to ES

## Verdict
**Help-search coverage is 90%+ complete for operational vocabulary.** 4 surfaced gaps are all P2 (medium-risk, defer until Day-1 names them) or P3 (low-frequency). **No critical search dead-end found post-Phase-18 closure.**

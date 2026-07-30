# WP16 Wave 5 — 8-Gate Inspection Executive Package

Date: 2026-07-30

## Executive scope statement

- Wave: **5 — Safety Certification**
- Phase executed: **Phase 2 — Comprehensive 8-Gate Inspection**
- Production code changes made: **None**
- Repairs made: **None**
- Inspection methods used: browser verification on preview, direct API verification by curl, targeted source-contract review, and route/deep-link replay using live Safety fixture data

## Final denominator inspected

- **Wave 5 denominator:** `52`
- **Inspected:** `52 / 52`
- **Inspection order preserved:** `W5-001` through `W5-052`
- **Hidden/detail routes explicitly exercised first:**
  - `/safety/forms/equipment-issuance/:id`
  - `/safety/forms/equipment-issuance/:id/return`
  - `/safety/forms/equipment-training/:id`
  - `/safety/cases/:caseId`
  - `/safety/incidents/:caseId/thread`
  - `/safety/cases/:caseId/reports/:reportType`
  - `/safety/cases/:caseId/executive-report`
  - `/trench-safety/assets/:assetId`
  - `/safety/trench-safety/assets/:assetId`
  - `/safety-portal/incidents/:id`
  - `/safety-portal/meetings/:id`
  - `/safety-portal/inspections/:id`

## Gate summary

### Gate 1 — Routing & Navigation
- All 52 inventoried Wave 5 Safety routes remain registered in `AppRoutes.jsx` and were exercised in inventory order.
- Public routes, protected routes, deep links, hidden/detail routes, and redirect/alias-backed entry paths were inspected against the accepted denominator.
- **Five detail/report routes fail under a valid Safety session** due to two auth-contract defects:
  - W5-004, W5-005, W5-007
  - W5-018, W5-019

### Gate 2 — User Experience
- No broad blank-screen or broken-shell failure was observed across the Wave 5 denominator.
- Mobile/tablet spot checks on `/incidents/report`, `/trench-safety/excavation/new`, `/safety-portal/corrective-actions`, `/safety-portal/incidents`, and `/safety-portal/inspections` showed **no operationally blocking responsive defect**.
- Active UX defects are concentrated in **false fail-closed messaging** on five hidden/detail/report routes:
  - Safety Forms detail/return viewers display **Not found / login required** even while the backend returns `200`
  - Case report viewers display **Could not load report / executive report** even while the backend returns `200`

### Gate 3 — CRUD
- Working create/read/review flows were verified on Safety Forms entry, inspections, meetings, JHA, incidents, near miss, trench safety public/protected workflows, corrective actions, documents, training, digest, topic library, employee profiles, and forms records.
- CRUD degradation is isolated to read-only detail/report surfaces behind two auth defects:
  - Safety Forms record detail / return review
  - Incident case report and executive report rendering

### Gate 4 — API & Data Integrity
- Verified `200` responses for representative Wave 5 APIs including:
  - `/api/safety/login`
  - `/api/incidents/{id}`
  - `/api/meetings/{id}`
  - `/api/inspections/{id}`
  - `/api/safety-forms/equipment-issuances/{id}`
  - `/api/safety-forms/equipment-trainings/{id}`
  - `/api/incident-cases/{id}/reports/executive_summary`
  - `/api/incident-cases/{id}/executive-report.pdf`
- Confirmed data-integrity mismatch defects where the **backend is healthy but the frontend route fails closed**:
  - Safety Forms detail/return routes (W5-004 / W5-005 / W5-007)
  - Incident report viewers (W5-018 / W5-019)

### Gate 5 — Permissions & Security
- **Positive finding:** `RequireSafety`-protected Safety Portal and protected trench routes remained fail-closed.
- **Positive finding:** no unauthorized cross-portal data exposure was observed during this pass.
- The open defects are **auth propagation defects**, not permissive leaks:
  - missing Safety header forwarding for `/api/safety-forms/*` detail routes
  - report viewers reading obsolete token storage keys

### Gate 6 — Shared Foundations
- One shared foundation defect was confirmed in the portal auth-scoping layer.
- One shared component/pattern defect was confirmed in duplicated report-viewer auth helpers.

### Gate 7 — Operational Workflow Validation
- Operationally healthy or materially reachable workflows:
  - incident intake
  - near miss intake
  - inspections create/review
  - meetings create/review
  - JHA create/review
  - trench safety public and protected oversight
  - corrective actions
  - safety documents and training review
  - safety digest and reports dashboards
  - forms-records oversight shell
- Broken or degraded workflows:
  - Safety-owned PPE / equipment issuance detail review
  - Safety-owned equipment return review handoff
  - executive / report rendering from incident case workspace

### Gate 8 — Life Safety & Compliance Integrity
- No unauthorized incident, corrective-action, or document data leak was observed.
- Two defects are classified **High** because they affect compliance-grade safety records and executive incident reporting:
  - PPE/accountability record detail/return review is not trustworthy for Safety Portal operators
  - incident case report and executive report views are not available to valid Safety operators despite healthy backend data

## Route-by-route inspection ledger

| W5 ID | Route | Result | Gate outcome | Issue / note |
|---|---|---|---|---|
| W5-001 | `/safety/forms/login` | PASS | Login surface rendered and accepted valid credentials | — |
| W5-002 | `/safety/forms` | PASS | Hub + token-checked entry path verified | — |
| W5-003 | `/safety/forms/equipment-issuance/new` | PASS | Entry route / create shell verified | — |
| W5-004 | `/safety/forms/equipment-issuance/:id` | FAIL | Valid Safety session renders false `Not found` on live record | `WP16-W5-001` |
| W5-005 | `/safety/forms/equipment-issuance/:id/return` | FAIL | Valid Safety session renders false `Not found` on live return route | `WP16-W5-001` |
| W5-006 | `/safety/forms/equipment-training/new` | PASS | Entry route / create shell verified | — |
| W5-007 | `/safety/forms/equipment-training/:id` | FAIL | Valid Safety session renders false `Not found` on live record | `WP16-W5-001` |
| W5-008 | `/safety/cards` | PASS | Public cards surface verified | — |
| W5-009 | `/safety/inspections/new` | PASS | Protected create route verified | — |
| W5-010 | `/meetings/new` | PASS | Meeting create route verified | — |
| W5-011 | `/meetings/submit` | PASS | Public submit route verified | — |
| W5-012 | `/jha` | PASS | JHA route verified | — |
| W5-013 | `/incidents/report` | PASS | Intake route verified; mobile/tablet spot check clean | — |
| W5-014 | `/near-miss` | PASS | Near-miss route verified | — |
| W5-015 | `/safety/cases/:caseId` | PASS | Live case workspace deep-link verified | — |
| W5-016 | `/safety/incidents/:caseId/thread` | PASS | Live incident thread deep-link verified | — |
| W5-017 | `/safety/executive-intelligence` | PASS | Route verified | — |
| W5-018 | `/safety/cases/:caseId/reports/:reportType` | FAIL | Valid Safety session renders false report-auth failure | `WP16-W5-002` |
| W5-019 | `/safety/cases/:caseId/executive-report` | FAIL | Valid Safety session renders false executive-report auth failure | `WP16-W5-002` |
| W5-020 | `/trench-safety` | PASS | Public trench dashboard verified | — |
| W5-021 | `/trench-safety/tabulated-data` | PASS | Public tabulated-data route verified | — |
| W5-022 | `/trench-safety/references` | PASS | Public references route verified | — |
| W5-023 | `/trench-safety/report` | PASS | Public trench report route verified | — |
| W5-024 | `/trench-safety/assets/:assetId` | PASS | Live public asset detail verified | — |
| W5-025 | `/trench-safety/excavation/new` | PASS | Public excavation route verified; mobile/tablet spot check clean | — |
| W5-026 | `/safety/trench-safety` | PASS | Protected trench hub verified | — |
| W5-027 | `/safety/trench-safety/assets` | PASS | Asset list verified | — |
| W5-028 | `/safety/trench-safety/assets/:assetId` | PASS | Live protected asset detail verified | — |
| W5-029 | `/safety/trench-safety/tabulated-data` | PASS | Protected tabulated-data route verified | — |
| W5-030 | `/safety/trench-safety/reports` | PASS | Reports route verified | — |
| W5-031 | `/safety/trench-safety/excavations` | PASS | Excavation oversight route verified | — |
| W5-032 | `/safety/trench-safety/repair-review` | PASS | Repair-review route verified | — |
| W5-033 | `/safety/trench-safety/field-reports` | PASS | Field-reports route verified | — |
| W5-034 | `/safety-portal/fleet` | PASS | Fleet route verified | — |
| W5-035 | `/safety-portal/corrective-actions` | PASS | Corrective-actions route verified; mobile/tablet spot check clean | — |
| W5-036 | `/safety-portal/fire-extinguishers` | PASS | Fire-extinguishers route verified | — |
| W5-037 | `/safety-portal/fire-extinguishers/import` | PASS | Import route verified | — |
| W5-038 | `/safety-portal/documents` | PASS | Documents route verified | — |
| W5-039 | `/safety-portal/training` | PASS | Training route verified | — |
| W5-040 | `/safety-portal/incidents` | PASS | Incidents list verified; mobile/tablet spot check clean | — |
| W5-041 | `/safety-portal/incidents/:id` | PASS | Live incident detail verified | — |
| W5-042 | `/safety-portal/meetings` | PASS | Meetings dashboard verified | — |
| W5-043 | `/safety-portal/meetings/:id` | PASS | Live meeting detail verified | — |
| W5-044 | `/safety-portal/audits` | PASS | Audits route verified | — |
| W5-045 | `/safety-portal/forms-records` | PASS | Forms records route verified with live counts | — |
| W5-046 | `/safety-portal/reports` | PASS | Reports dashboard verified | — |
| W5-047 | `/safety-portal/library` | PASS | Topic library route verified | — |
| W5-048 | `/safety-portal/employees` | PASS | Employee profiles route verified | — |
| W5-049 | `/safety-portal/digest` | PASS | Digest route verified | — |
| W5-050 | `/safety-portal/inspections` | PASS | Inspections dashboard verified; mobile/tablet spot check clean | — |
| W5-051 | `/safety-portal/inspections/:id` | PASS | Live inspection detail verified | — |
| W5-052 | `/safety-portal/jha-plans` | PASS | JHA plans route verified | — |

## Final defect ledger

| Issue ID | Severity | Operational Criticality | Operational risk | Scope | Impacted Wave 5 experiences | Root cause | Evidence | Smallest safe repair |
|---|---|---|---|---|---|---|---|---|
| WP16-W5-001 | High | B | Compliance, Operations, User Experience, Data Integrity | Shared Foundation | W5-004, W5-005, W5-007 | Shared Safety auth scoping does not classify `/api/safety-forms/*` for Safety Portal sessions, so the generic `api` client does not forward `X-Safety-Token` on detail/return requests unless a legacy Safety Forms token exists. | Browser replay with `masci.safety.token` rendered false `Not found / login required` on live issuance/training records while direct curl returned `200` for `/api/safety-forms/equipment-issuances/{id}` and `/api/safety-forms/equipment-trainings/{id}`. Code review: `ViewSafetyForm.jsx:60-65`, `ReturnEquipment.jsx:59-75`, `lib/api.js:67-75`, `lib/portalAuthScope.js:129-168`. | Extend shared API auth scoping so Safety sessions forward `X-Safety-Token` on `/api/safety-forms/*`, then re-verify detail and return routes. |
| WP16-W5-002 | High | B | Compliance, Operations, User Experience, Data Integrity | Shared Component | W5-018, W5-019 | Incident report viewers use duplicated legacy localStorage keys (`safety_token`, `admin_token`, `pm_token`) instead of the current portal auth helpers / namespaced token keys. | Browser replay with a valid `masci.safety.token` rendered false auth-required errors on W5-018/W5-019 while direct curl returned `200` for `/api/incident-cases/{id}/reports/executive_summary` and `/api/incident-cases/{id}/executive-report.pdf`. Code review: `IncidentReportViewer.jsx:14-26`, `ExecutiveCaseReport.jsx:18-29`, `lib/safetyAuth.js:2-21`. | Replace duplicated legacy token lookups with shared portal auth helpers (or the scoped API client), then re-verify both report-viewer routes. |

## Total issues

- **Total issues:** `2`

## Issues by severity

- **Critical:** `0`
- **High:** `2`
- **Medium:** `0`
- **Low:** `0`

## Issues by operational criticality

- **Level A (Life Safety):** `0`
- **Level B (Compliance):** `2`
- **Level C (Operational):** `0`
- **Level D (Administrative):** `0`

## Issues by operational risk

- **Compliance:** `2`
- **Operations:** `2`
- **Data Integrity:** `2`
- **User Experience:** `2`
- **Security:** `0 direct unauthorized-access exposures observed`
- **Safety:** `0 direct data-corruption findings opened, but both open issues affect safety/compliance documentation trust`
- **Administrative:** `0`
- **Performance:** `0 standalone performance defects opened`

## Shared foundation findings

1. **Safety Portal auth scoping and `/api/safety-forms/*` are out of sync.** Safety operators can enter the Safety-owned review shell, but shared API auth scoping does not forward the Safety header on detail/return requests.
2. **Incident report viewers still use obsolete token storage keys.** The backend contract is healthy, but the duplicated viewer helper is disconnected from the current portal session contract.

## Top three operational risks

1. **Safety operators cannot reliably open PPE/accountability detail and return routes** from the Safety-owned review lane, undermining compliance-ready record handling.
2. **Executive incident reporting is not trustworthy from the Safety portal context** because the report and executive-report viewers fail closed despite healthy backend data.
3. **Shared auth-contract drift is producing deceptive fail-closed states** (`Not found` / `login required`) that mask healthy records and reduce operator confidence in hidden/detail safety workflows.

## Overall operational readiness assessment

Wave 5 Safety is **not ready for executive lock**. The inspection covered the full denominator (`52 / 52`), and the majority of Safety experiences are operationally sound. However, two High-severity defects remain open across five hidden/detail/report routes. Both issues are fail-closed frontend auth-contract defects rather than backend integrity failures, but they directly affect compliance-grade safety record review and executive incident reporting. Repair authorization is required before lock can be considered.

## Executive recommendation

**READY FOR WAVE 5 REPAIR AUTHORIZATION**
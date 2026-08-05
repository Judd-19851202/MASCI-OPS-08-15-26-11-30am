# WP-18CZ Platform-Wide Operator Experience, KPI Truth & Executive Decision Certification Audit

Date: 2026-08-05

## Scope under executive directive

This audit covers the full operator-facing estate for MASCI Docs / ForgedOps, not only pages:

- dashboards
- KPI and status cards
- charts, tables, forms, dialogs, drawers, modals, tabs, and tooltips
- empty, loading, validation, success, and error states
- notifications, emails, PDFs, exports, and AI summaries
- desktop, laptop, tablet, phone, landscape, portrait, and print layouts
- operator roles from President through field employee

## Evidence base used in this pass

1. `/app/memory/WP17_ROUTE_GOVERNANCE_REGISTRY.csv`
2. `/app/memory/WP18CX_EXECUTIVE_FINAL_GO_GATE.md`
3. `/app/memory/WP18CX_OPERATOR_EXPERIENCE_AUDIT.md`
4. `/app/memory/WP18CX_PDF_EMAIL_EXPORT_AI_LANGUAGE_AUDIT.md`
5. `/app/memory/PRD.md`, `ROADMAP.md`, `CHANGELOG.md`
6. `frontend/src/app/routing/AppRoutes.jsx`
7. Shared operator-language and KPI surfaces:
   - `frontend/src/lib/operatorLanguage.js`
   - `frontend/src/lib/kpiMetadata.js`
   - `frontend/src/components/telemetry/TelemetryTruthNote.jsx`
   - `frontend/src/components/operations-map/ProjectIntelligenceStrip.jsx`
   - `frontend/src/components/operational_intelligence/GovernedMetricCard.jsx`
   - `frontend/src/components/operational_intelligence/OperationalIntelligenceSnapshotWorkspace.jsx`
   - `frontend/src/components/PmOperationalKPIs.jsx`
   - `frontend/src/components/HrKpiStrip.jsx`
   - `frontend/src/components/SafetyOperationalKpisCard.jsx`
   - `frontend/src/components/EmailReportDialog.jsx`
8. Key backend KPI/truth sources:
   - `backend/routes/executive_overview.py`
   - `backend/routes/project_health.py`
   - `backend/routes/transportation_experience.py`
   - `backend/services/project_operational_intelligence.py`
9. Repo-wide visible-copy guard:
   - `backend/tests/test_no_internal_labels_in_user_facing_jsx.py`

## Current platform-wide certification status

### 1. Route and portal coverage is not closed

The existing route governance register contains `484` route records.

Routes that are **not** at a closed certification state today: `215`

- `158` marked `PENDING`
- `29` marked `REPAIRED_NOT_CERTIFIED`
- `16` blocked
- `7` opened but not audited
- `2` audited with defects still remaining
- `3` carrying other non-closed evidence states

That alone prevents a truthful platform-wide GO.

### 2. Prior certification already ended in NO-GO

`WP18CX_EXECUTIVE_FINAL_GO_GATE.md` already concluded **NO-GO** because of unresolved runtime gaps in:

- Survey proof
- direct AI runtime proof
- full PDF / export / report channel proof
- full mobile field-condition proof
- broader accessibility proof
- isolated executive-family role walkthroughs

WP-18CZ expands the scope beyond WP18CX, so those unresolved areas remain blockers rather than being superseded.

### 3. KPI truth foundations exist, but they are not universal yet

Strong truth foundations were found in several shared KPI surfaces:

- `backend/routes/executive_overview.py` exposes tile metadata, thresholds, source collections, owner, and freshness
- `backend/routes/project_health.py` exposes summary and indicator formulas, source collections, and confidence support
- `frontend/src/lib/kpiMetadata.js` provides reusable “definition / source / formula / freshness / why it matters” help content
- `frontend/src/components/operational_intelligence/GovernedMetricCard.jsx` exposes owner, confidence, formula, freshness, drill-down, source records, and limitations

However, this truth pattern is **not yet universal** across all operator-facing KPI surfaces, exports, emails, PDFs, and AI outputs.

### 4. Construction-first language is improved centrally, but visible defects remain

`frontend/src/lib/operatorLanguage.js` already bans and sanitizes many internal terms, which is the correct repair seam.

Even so, shared visible surfaces still contain operator-unsafe wording such as:

- `ProjectHealth.jsx:222` → `Deterministic · canonical`
- `GovernanceHealthChip.jsx:80-93` → `governance drift / governance improving / governance monitor / governance stable`
- `TelemetryTruthNote.jsx:27` → `Showing last good snapshot.`
- `ProjectIntelligenceStrip.jsx:69,86` → `Waiting for telemetry`
- `OperationalIntelligenceSnapshotWorkspace.jsx:78` → `CSV export is deferred in this release.`
- `SafetyOperationalKpisCard.jsx:87` → `One spine. Same numbers PM sees, safety-first framing.`

Those phrases are evidence-backed failures against the Heavy Civil language standard.

### 5. Decision support is uneven

Best-in-class surfaces in the current codebase already explain:

- the metric owner
- the formula
- the source records
- the drill-down path
- the confidence state
- the recommended next action

Examples:

- `GovernedMetricCard.jsx`
- `OperationalIntelligenceSnapshotWorkspace.jsx`
- `ProjectIntelligenceStrip.jsx`
- `executive_overview.py` verdict metadata

But other shared surfaces still stop at displaying numbers, counts, or status labels without fully answering:

- what changed
- why the color is what it is
- what the operator should do next
- what the business impact is

### 6. Role-isolated proof is still incomplete

`/app/memory/test_credentials.md` contains preview credentials for:

- admin
- PM
- HR
- safety
- dispatch
- shop
- field leadership

It does **not** provide isolated preview credentials for all required roles in the directive, including:

- President
- COO
- VP Operations
- Area Manager
- Project Executive
- Survey
- Payroll
- Mechanic

That means final role-by-role certification cannot be truthfully completed from the current preview access set alone.

## Exact blocker statement

The platform cannot receive WP-18CZ GO because the current evidence set proves that:

1. not every operator-facing route is certified,
2. not every output channel is certified,
3. not every KPI has a universal operator-facing truth/explanation contract,
4. construction-first language defects remain on shared surfaces,
5. not every required role has isolated preview proof available.

## Audit conclusion

**Current result: NO-GO**

This is not a design judgment.
It is a constitutional evidence judgment.
Issuing GO today would overstate route coverage, role coverage, channel coverage, and operator-language compliance.

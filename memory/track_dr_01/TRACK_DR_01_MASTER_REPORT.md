# TRACK DR-01 · Daily Report Unification & Trust Recovery

Date: 2026-07-14
Mode: Read-only forensic planning only
Verdict: Repository-backed recovery blueprint complete

## Executive summary

The Daily Report system currently operates as a **multi-version composite** rather than a single canonical workflow. The repo shows:
- **V1** and **V3** both routed from the same live URLs via `DailyReportRouter`
- **V2** still alive as a backend/runtime subsystem with its own collections and APIs
- a shared continuity layer (`useFormDraft`, `draftStore`, `draftTelemetry`, `crewMemory`) that is **not consumed consistently** across shells

The P0 breakages are explained by version drift, not just isolated bugs:

1. **Autosave trust is broken by unstable draft identity and shell drift**
   - V1 scope includes `report_number`, which changes after mount
   - V1 and V3 do not share the same base draft key
   - V3 queue/idempotency behavior diverges from V1 and bypasses canonical Daily Report repair logic

2. **Smart Prefill trust is broken by consumer drift**
   - backend `/recent-context` contract exists and is current (`19.06.1`)
   - V1 consumes it, but V3 does not
   - V1 itself contains two conflicting Smart Prefill apply paths

3. **Legacy V2 remains a real architectural factor**
   - not as the active field route, but as a live AI/approval/PDF subsystem with `dr_v2_*` collections and compatibility aliases

## Repository-backed conclusions

### A. Daily Report has one canonical submit endpoint, but not one canonical field contract
Evidence:
- `backend/routes/daily_reports.py:591-882`
- `frontend/src/pages/NewDailyReport.jsx`
- `frontend/src/pages/NewDailyReportV3.jsx`

### B. The current routed form can send users into materially different continuity behavior depending on feature flag state
Evidence:
- `frontend/src/pages/DailyReportRouter.jsx:14-29`

### C. The repo itself documents the intended stable scope as project + report date, but the current V1 helper also includes `report_number`
Evidence:
- `frontend/src/lib/resiliency/useFormDraft.js:67-72`
- `memory/PRD.md:9`
- `frontend/src/lib/resiliency/dailyReportScope.js:10-18`

### D. V3’s own comment says it must share the V1 form key, but it does not
Evidence:
- `frontend/src/pages/NewDailyReportV3.jsx:59-63`

### E. The backend recent-context contract is richer than some active frontend paths currently use
Evidence:
- `backend/server.py:4200-4237`

## Deliverable map

### 1. Daily Report Architecture
See: `01_DAILY_REPORT_ARCHITECTURE.md`

Key finding:
- one route selector, two active field shells, one legacy V2 subsystem, one shared but inconsistently used continuity stack

### 2. Source-of-Truth Matrix
See: `02_SOURCE_OF_TRUTH_MATRIX.md`

Key finding:
- canonical submit source exists; canonical field-entry source does not

### 3. Data Flow Diagram
See: `03_DATA_FLOW_DIAGRAM.md`

Key finding:
- current flow forks before the operator ever types into the form

### 4. Version Forensics Report
See: `04_VERSION_FORENSICS_REPORT.md`

Key finding:
- V1, V3, and V2 are each materially different systems, not naming variants

### 5. Autosave Root Cause Report
See: `05_AUTOSAVE_ROOT_CAUSE_REPORT.md`

Verified root causes:
- unstable V1 scope because `report_number` participates in draft identity
- V1/V3 base-key mismatch
- V3 queue/idempotency drift
- V3 missing recovery affordances

High-confidence contributing defect:
- lifecycle flush is documented as synchronous but implemented as async IDB writes

### 6. Smart Prefill Root Cause Report
See: `06_SMART_PREFILL_ROOT_CAUSE_REPORT.md`

Verified root causes:
- V3 does not consume `/recent-context`
- V1 duplicates Smart Prefill UI/apply paths
- `CrewSetupRestorePrompt` is reused for a different trust boundary than it was designed for

### 7. Legacy Component Inventory
See: `07_LEGACY_COMPONENT_INVENTORY.md`

Key finding:
- legacy V2 is still operationally real and must be explicitly contained during recovery

### 8. Canonical Recovery Architecture
See: `08_CANONICAL_DAILY_REPORT_RECOVERY_ARCHITECTURE.md`

Recommended target:
- one routed field contract
- one draft identity contract
- one Smart Prefill contract
- one legacy V2 compatibility boundary

### 9. Unification Plan
See: `09_UNIFICATION_PLAN.md`

Recommended order:
1. freeze shell drift
2. declare contracts
3. repair draft identity
4. repair Smart Prefill
5. reconcile shell parity
6. contain V2

### 10. Risk Register
See: `10_RISK_REGISTER.md`

Highest risk:
- identity drift across routed shells

### 11. Regression Protection Plan
See: `11_REGRESSION_PROTECTION_PLAN.md`

Key missing protections:
- shell parity tests
- stable-scope tests
- one Smart Prefill apply path test
- V3 queue parity test

### 12. Certification Plan
See: `12_CERTIFICATION_PLAN.md`

Key point:
- repository certification can happen now; final trust certification still requires preview/device/runtime evidence

### 13. Sequenced Implementation Roadmap
See: `13_IMPLEMENTATION_ROADMAP.md`

Key principle:
- repair identity first; do not polish UI while report-instance identity is still unstable

## Unknowns

The repo cannot prove:
- current production `dr_v3` flag distribution
- exact affected browser/device cohort
- whether pagehide/suspend failures are the dominant field loss mechanism

These are explicitly UNKNOWN and must be resolved during implementation certification.

## Final DR-01 planning verdict

The Daily Report system can be recovered without inventing a new architecture, but only if the repair starts by **collapsing version drift around draft identity and Smart Prefill behavior**. The repository is already rich enough to define the target contract; what is missing is consistency across V1, V3, and retained V2 runtime baggage.

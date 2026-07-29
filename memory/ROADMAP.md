# WP15 Immediate Next Actions — 2026-07-29

## P0
- WP15 constitutional closeout is now shipped and verified:
  - zero legacy drift
  - zero governance candidates
  - zero manual governed frontend header builders
  - Operational Health Dashboard live at `/admin/governance`
  - CI/CD governance protection wired into PR, nightly, release-candidate, and production gates
  - dedicated governance regression gate added for pull requests
  - architecture freeze and closeout documents published
  - final determination documented as **WP-15 CERTIFICATION VALID — OPERATIONAL HEALTH RED**
  - WP-15 classified as **Constitutional Infrastructure — Frozen**
- Preserve the new hard-fail CI scanner policy and keep the dashboard evidence contract intact on future changes.

## P1
- Add Golden Path monitoring hooks and additional longitudinal trend/history views on the shared Operational Health Dashboard framework.
- Expand retained certification history as future verification events are appended.
- Work down the current operational RED/AMBER conditions through normal operations ownership, not through architectural rollback.

## P2
- Plug additional constitutional systems into the shared Operational Health Dashboard framework without creating duplicate status engines.
- WP-16 Operator Experience only after WP-15 remains stable under the frozen governance architecture.

# BCSS Roadmap Snapshot

## 2026-07-28 OPPC roadmap overlay

### Current OPPC execution state

- `WP-OPPC-01 — Canonical Architecture and Gap Inventory`: **COMPLETE**
- `WP-OPPC-02 — Cost-Code Foundation Hardening`: **COMPLETE**
- `WP-OPPC-03 — Rolling Two-Week Planning Lifecycle`: **COMPLETE**
- `WP-OPPC-04 — Weekly Rollover Engine`: **COMPLETE**
- `WP-OPPC-05 — Daily Actual Production Integration`: **COMPLETE**
- `WP-OPPC-06 — Payroll and Labor Reconciliation`: **COMPLETE**
- `WP-OPPC-07 — Monday Look-Behind Engine`: **COMPLETE**
- `WP-OPPC-08 — Schedule Variance and Root-Cause Taxonomy`: **COMPLETE**
- `WP-OPPC-09 — Recovery Planning and Tasks & Actions`: **COMPLETE**
- `WP-OPPC-10 — Resource Demand and Cross-Department Integration`: **COMPLETE**
- `WP-OPPC-11 — Forecasting and Critical-Path Hardening`: **COMPLETE**
- `WP-OPPC-12 — Production Confidence Score`: **COMPLETE**
- `WP-OPPC-13 — Monday Morning Briefing`: **COMPLETE**

### OPPC P0 sequence

1. `WP-OPPC-14 — Operations Control Plane`
   - **COMPLETE / VERIFIED COMPLETE**
   - Complete now:
     - constitutional Operational Registry
     - Operational Event Catalog
     - Daily Report → OPPC proof chain on registered events
     - preview-safe Communications Engine
     - acknowledgement bridge from notifications → communications ledger
     - readiness evidence packaging endpoint
     - Operations Control Plane v1 baseline snapshot endpoint
     - OCC registry/evidence/baseline UI visibility
     - WP-OPPC-14F Operational Case Management complete:
       - canonical Case model, lifecycle, immutable history, authorization + governance hooks
       - Trust Spine case events, correlation / causation IDs, idempotency controls
       - Case Assembly service, unified timeline, relationship graph, and core APIs
       - fresh preview Daily Report certification record + policy-controlled automatic Case creation
       - communications / acknowledgement / task / evidence / baseline / duplicate / related-case handling
       - dedicated Case Queue and dedicated Case Detail route with OCC proof-chain drilldown
       - certified end-to-end preview chain returning `OPERATIONS CONTROL PLANE v1 — VERIFIED COMPLETE`
2. `WP-OPPC-15 — Permissions and Governance`
3. Executive latency optimization for portfolio confidence rollups
4. `WP-OPPC-16 — User Experience`
5. `WP-OPPC-17 — Data, Audit, Retention, and Survivability`
6. `WP-OPPC-18 — Trust Center and Operational Observability`
7. `WP-OPPC-19 — Testing and Certification`
8. `WP-OPPC-20 — Regression Gate`
9. `WP-OPPC-21 — Independent Verification`
10. `WP-OPPC-22 — Evidence Package`

### Current advisory note

- WP-11/12/13 are functionally complete and certified in preview.
- Operational release gate for Cost Codes + Scheduling on project `24-06` is now **GO** with no remaining P0 defects.
- WP-14 + WP-14F are now certified complete in preview; Operations Control Plane v1 closeout is achieved.
- Platform master architectural reference is now frozen at `/app/memory/MASCI_OPS_PLATFORM_BASELINE_1_0.md`.
- Portfolio-wide executive confidence refresh remains the main performance optimization candidate for WP-14.

### Platform Baseline governance note

- Platform Baseline 1.0 is established as the immutable architectural reference for MASCI OPS through the certified `WP-OPPC-14F` scope.
- Future platform evolution must reference `/app/memory/MASCI_OPS_PLATFORM_BASELINE_1_0.md` and create a new baseline version rather than redefining Baseline 1.0 in place.

### OPPC governing constraints preserved

- No duplicate schedule, cost-code, task/action, dispatch, audit, or observability engines
- Every material OPPC workflow must map to the existing Trust Spine
- All new OPPC logic must extend current canonical owners first

Date: 2026-07-27
Authority: current canonical roadmap after Wave 3 Formal Closeout reconciliation

## Current execution state

- Wave 3 Formal Closeout: **COMPLETE**
- Platform Survivability Program: **READY TO RESUME**
- Production Readiness Review (PRR): **NOT AUTHORIZED**
- Production deployment: **NOT AUTHORIZED**

## Authoritative Wave 3 family status

- Family 1 — OCC Health Aggregator: **ADOPTED**
- Family 2 — OCC Trust Events: **ADOPTED**
- Family 3A — Core Admin Operations: **ADOPTED**
- Family 3B — Operations Actions: **ADOPTED**
- Family 3C — Operational Events: **ADOPTED**
- Family 3D-1 — Asset Spine Canonical Registry: **ADOPTED**
- Family 3D-2 — External Asset Mapping & Reconciliation: **REJECTED**

## Governing sequence

1. Wave 3 Formal Closeout — COMPLETE
2. Platform Survivability Program — READY TO RESUME
3. Production Readiness Review — blocked until survivability passes
4. Wave 1 Deployment — blocked until PRR passes

## Governing certification dependencies preserved

- D-02 Backup & Disaster Recovery Preview certification: **ADOPTED historical evidence**
- S1-2 Secrets & Configuration Recovery Certification: **CERTIFIED**
- S1-3 Backup Verification Hardening: **CERTIFIED**
- S1-4 Notification Delivery Repository Work: **COMPLETE WITH GOVERNANCE BOUNDARY**
  - Repository implementation complete
  - Preview `SAFE_CAPTURE` intentionally retained
  - Live provider validation deferred by governance
  - Failed run `s1-4-cert-e217a5ffd8` preserved as permanent historical evidence
  - No repository defect exists

## Remaining work by class

### Repository work

- none required to close Wave 3

### Administrative work

- optional future operational validation only if Preview live-provider notification proof is intentionally desired under separate governance approval

### External infrastructure

- none blocking Wave 3 closeout

### Production work

- execute Platform Survivability Program
- execute PRR
- evaluate Production deployment only after both gates pass

### Future enhancements

- Family 3D-1 direct-consumer UI parity for `inspection_expiration`
- Family 3D-1 legacy overlap containment / migration items
- Family 1 legacy verification modernization
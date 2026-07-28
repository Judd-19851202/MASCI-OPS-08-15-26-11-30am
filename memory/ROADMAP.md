# BCSS Roadmap Snapshot

## 2026-07-28 OPPC roadmap overlay

### Current OPPC execution state

- `WP-OPPC-01 — Canonical Architecture and Gap Inventory`: **COMPLETE**
- `WP-OPPC-02 — Cost-Code Foundation Hardening`: **COMPLETE**
- `WP-OPPC-03 — Rolling Two-Week Planning Lifecycle`: **COMPLETE**
- `WP-OPPC-04 — Weekly Rollover Engine`: **IN PROGRESS**

### OPPC P0 sequence

1. `WP-OPPC-04 — Weekly Rollover Engine`
2. `WP-OPPC-05 — Daily Actual Production Integration`
3. `WP-OPPC-06 — Payroll and Labor Reconciliation`
4. `WP-OPPC-07 — Monday Look-Behind Engine`
5. `WP-OPPC-08 — Schedule Variance and Root-Cause Taxonomy`
6. `WP-OPPC-09 — Recovery Planning and Tasks & Actions`
7. `WP-OPPC-10 — Resource Demand and Cross-Department Integration`
8. `WP-OPPC-11 — Forecasting and Critical-Path Hardening`
9. `WP-OPPC-12 — Production Confidence Score`
10. `WP-OPPC-13 — Monday Morning Briefing`
11. `WP-OPPC-14 — Notifications and Escalations`
12. `WP-OPPC-15 — Permissions and Governance`
13. `WP-OPPC-16 — User Experience`
14. `WP-OPPC-17 — Data, Audit, Retention, and Survivability`
15. `WP-OPPC-18 — Trust Center and Operational Observability`
16. `WP-OPPC-19 — Testing and Certification`
17. `WP-OPPC-20 — Regression Gate`
18. `WP-OPPC-21 — Independent Verification`
19. `WP-OPPC-22 — Evidence Package`

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
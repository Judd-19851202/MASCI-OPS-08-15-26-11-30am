# RTO / RPO MEASUREMENTS

Date: 2026-07-27  
Measurement source: `/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json` and live recovery surfaces

---

## 1. Failure-injection measurements

| Scenario | Detection time | Recovery initiation time | Service restoration time | Full consistency restoration time | Measured RTO | Measured RPO | Residual operational impact | Confidence |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `PSP-FI-01` Admin continuity fail-closed | 231.63 ms | 0 ms | 239.64 ms | 239.64 ms | 471.27 ms | 0 s | None after dual-token re-auth | HIGH |
| `PSP-FI-02` Stale backup/restore guard reclaim | 31.31 ms | 0 ms | 31.31 ms | 62.54 ms | 31.31 ms | 0 s | Synthetic row only; deleted after validation | HIGH |
| `PSP-FI-03` Duplicate scheduler slot claim | 87.54 ms | 0 ms | 118.62 ms | 149.59 ms | 118.62 ms | 0 s | No duplicate work executed | HIGH |
| `PSP-FI-04` Preview/prod config blend rejection | 0.23 ms | 0 ms | 0.15 ms | 0.15 ms | 0.38 ms | 0 s | Simulation only | HIGH |
| `PSP-FI-05` Corrupted archive lineage quarantine | 0.10 ms | 0 ms | 0.07 ms | 0.07 ms | 0.17 ms | 0 s | Simulation only | HIGH |
| `PSP-FI-06` Trust Spine failed lifecycle visibility | 1543.33 ms | 33.70 ms | 1543.33 ms | 1574.44 ms | 1577.03 ms | 0 s | Synthetic failed workflow row removed after validation | HIGH |

---

## 2. Live platform posture measurements

These are the measured live Preview posture values at report time. They are not estimates.

| Metric | Target | Measured actual | Status | Source |
|---|---:|---:|---|---|
| Backup Recovery Point Objective (RPO) | 60 min | 162.8 min | RED | `/api/admin/recovery/snapshot` |
| Restore Recovery Time Objective (RTO) — latest bounded drill | 15 min | 41.035 min | AMBER | `/api/admin/recovery/snapshot` |

---

## 3. Interpretation

- The failure-injection scenarios demonstrated **fast fail-closed detection and bounded restoration** for the tested Preview-only survivability seams.
- The live platform posture still shows **RPO target breach** and **RTO target breach** in Preview; these are tracked governance findings, not hidden or estimated away.

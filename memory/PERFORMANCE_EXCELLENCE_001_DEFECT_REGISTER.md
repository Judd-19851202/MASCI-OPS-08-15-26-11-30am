# PERFORMANCE-EXCELLENCE-001 · Defect Register

```
Environment    : both
Access Level   : mixed
Evidence Source: this sprint's audit + prior-sprint carry-forwards
Confidence     : VERIFIED for every defect listed
```

## §1 · Defect table

| ID | Defect | Severity | Discovered in | Owner | Status | Evidence |
|---|---|---|---|---|---|---|
| **PE001-D01** | Cloudflare cache serves `/static/*` with `Cache-Control: public, max-age=60` instead of the `_headers`-declared `max-age=31536000, immutable` | **P0** | This sprint § A.2 | **Operator** (Cloudflare Cache Rules) | OPEN | `curl -skI https://mascidocs.com/static/js/main.0ab42eae.js \| grep cache` |
| **PE001-D02** | 7 evidence-backed indexes coded in `server.py::ensure_safety_indexes` but **not yet deployed to prod** (prior cluster was preview-only) | **P1** | This sprint § A.4 | **Operator** (deploy production) | OPEN | Direct prod explain shows COLLSCAN on `daily_reports.id`, `daily_reports.doc_id`, `job_photos.id`, `motive_events.id`, `directory_sessions.token`; 41,261-key scan on `integration_sync_logs.find({int,status})` |
| **PE001-D03** | Main JS bundle 5.5 MB raw / 1.4 MB gz — no route splitting | **P2** | This sprint § A.1 | Engineering (scoped sprint) | QUEUED | `yarn build` output captured this sprint |
| **PE001-D04** | Stale ODR test fixture: `tests/odr/test_m1_option_c.py:133` asserts `len(odr) >= 1` against a fixture that produces 0 ODR rows in fresh test DB setups | **P3** | Original handoff + this sprint § E.3 | Engineering (next test-hardening sprint) | OPEN | Test file line 133 + handoff summary |
| **PE001-D05** | `JobPhotosLibrary` renders ALL photos non-virtualized; risks long-list jank on prod where photo counts grow | **P3** | This sprint § A.7 | Engineering (scoped sprint) | QUEUED | Bundle size + 1,812 photos in preview / 789 in prod today |
| **PE001-D06** | 21 orphan ephemeral test DBs (`masci_test_*_preview`, `scheduler_test_iter445`) on the Atlas cluster from prior pytest runs | P3 | This sprint § E.3 (carry-forward from GOVERNANCE-HARDEN-001 § A.9) | Operator (Atlas Console drop) | OPEN | `list_database_names()` captured this sprint |
| **PE001-D07** | GOVERNANCE-REMEDIATE-001 remains 🟡 CONDITIONAL PASS pending Atlas user split + prod-side secret rotation | P1 | Carry-forward from GOVERNANCE-REMEDIATE-001 | Operator (Atlas Console + Emergent secrets) | OPEN — directive explicitly removed from this sprint scope | Prior sprint cert |
| **PE001-D08** | `server.py` ruff style warnings (F541 × 4, F841 × 1, F811 × 2) | P3 | This sprint § E.1 (carry-forward) | Engineering (cleanup sprint) | OPEN | ruff output |
| **PE001-D09** | Multiple `react-hooks/exhaustive-deps` lint warnings across `AdminIntegrationCenter`, `AdminOperationsEvents`, `AssetProfile`, `ShiftStart`, `ExcavationOversight`, `TrenchSafetyReports`, etc. | P3 | This sprint § A (yarn build output) | Engineering (cleanup sprint) | OPEN | CRA build warnings |
| **PE001-D10** | 4 `_demo_tor_*.png` assets in build output (~4 MB) — candidates for removal pending live-reference check | P3 | This sprint § E.5 | Engineering (verify-then-remove cleanup sprint) | QUEUED | `ls /app/frontend/build/` |
| **PE001-D11** | One unresolved `production_incidents` row (MaintainX `credential_missing`) in prod | P3 | TRUTH-AUDIT-001 + carry-forward | Operator (set MaintainX creds OR keep open as designed) | OPEN — **expected** by design until MaintainX activation | `masci_safety.production_incidents` direct read |

## §2 · Severity summary

| Severity | Open count |
|---|---|
| P0 | **1** (PE001-D01 — operator action) |
| P1 | **2** (PE001-D02 deploy, PE001-D07 governance) |
| P2 | 1 |
| P3 | 7 |

⚠️ **The directive's "Zero P0, Zero P1" target is NOT achieved.** The two P1+ items are operator-deploy / operator-Atlas actions that the fork cannot perform. Once executed:
- PE001-D01 (Cloudflare rule) → closes P0 → Production Readiness moves toward 95+
- PE001-D02 (deploy 7 indexes) → closes P1 → Platform Health moves toward 98
- PE001-D07 (GOVERNANCE-REMEDIATE-001 closeout) → closes P1 → Security moves toward 95+

## §3 · Defects explicitly considered and NOT logged

The audit deliberately did NOT log:
- "Should use React Query" (philosophical, not a defect)
- "Should virtualize all tables" (premature without per-list evidence)
- "Should TypeScript everything" (out of scope)
- "Should add more skeleton states" (feature drift)

Each of these is a viable architectural direction but none is an evidence-backed defect in the platform's current operational posture.

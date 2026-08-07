# WP18C9 Performance, Scale, and Query Report

Date: 2026-08-07  
Status: PASS

## Warm API Measurements
- Route: `/api/admin/governance/project-controls/portfolio-intelligence`
- Warm samples (ms): 1081.12, 1118.71, 1008.67, 1025.02, 1021.31, 1142.80, 1063.78
- p50: **1063.78 ms**
- p95: **1118.71 ms**
- Average payload size: **133,996 bytes**
- Max payload size: **133,996 bytes**
- Full portfolio refresh (43 projects, existing upstream refresh path): **29,215.43 ms**

## Query / Assembly Scale Checks
| Scope size | Project-performance query ms | Forecast query ms | EV query ms | Row-assembly ms |
|---|---:|---:|---:|---:|
| 1 | 27.87 | 55.06 | 28.21 | 0.10 |
| 10 | 55.51 | 57.18 | 31.72 | 0.41 |
| 25 | 32.15 | 34.63 | 62.29 | 0.78 |
| 43 | 36.07 | 40.49 | 86.19 | 2.13 |

## Mongo Explain Summary
| Query | Winning stage | keysExamined | docsExamined | nReturned | time ms |
|---|---|---:|---:|---:|---:|
| active jobs | PROJECTION_SIMPLE | 43 | 43 | 43 | 0 |
| project-performance updates by scope | PROJECTION_SIMPLE | 43 | 43 | 43 | 0 |
| EV updates by scope | PROJECTION_SIMPLE | 43 | 43 | 43 | 0 |
| portfolio cache by scope key | PROJECTION_SIMPLE | 1 | 1 | 1 | 1 |
| latest forecast per project | DISTINCT_SCAN on `project_number_1_version_number_-1` then FETCH | 43 | 43 | 43 | 1 |

## Performance Verdict
- No unbounded portfolio fan-out query was used on read.
- Latest forecast resolution uses a distinct scan over the `(project_number, version_number)` index.
- Read-time row assembly stayed bounded and small compared with query time.
- The accumulated release gate passed after the C9 additions.

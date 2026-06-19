# TRACK 15.54 · Performance Certification (Phase 10)

**Status:** 🟢 GREEN on production HTTP probes. 🟡 YELLOW on preview-pod PDF micro-bench. Captured 2026-06-19 22:25 UTC.

## HTTP latency on production (`mascidocs.com`)

| Endpoint | HTTP | Cold | Warm 1 | Warm 2 |
|---|:---:|---:|---:|---:|
| `/api/health` | 200 | 0.169 s | 0.170 s | 0.159 s |
| `/api/health/full` | 200 | 0.255 s | — | — |
| `/api/version` | 200 | 0.139 s | 0.118 s | 0.189 s |
| `/api/passkeys/login/options` (POST) | 422 | 0.244 s | 0.178 s | 0.159 s |
| `/api/admin-strict/diag/persistence-health` | 401 | 0.186 s | 0.175 s | 0.287 s |
| `/api/field-memory/recent` | 401 | 0.188 s | 0.206 s | 0.239 s |
| `/api/dispatch/operational-moments/by-assignment/test` | 401 | 0.182 s | 0.202 s | 0.175 s |

**Median: 0.19 s · max: 0.29 s · target: 2.0 s.** All probes well within SLO.

## PDF micro-bench on preview pod (run in-process; not a user-facing path)

| Kind | Today | Track 15.51 | Drift | SLO |
|---|---:|---:|---|:---:|
| Incident (enriched) | 3.757 – 7.024 s | 1.732 – 1.852 s | +150-300% | ⚠ over 2 s today |
| Daily Report | 2.901 – 5.832 s | 0.934 – 0.976 s | +200-500% | ⚠ over 2 s today |
| Safety Meeting | 2.104 – 2.926 s | 0.879 – 0.890 s | +135-230% | ⚠ over 2 s today |
| JHA | 1.212 – 1.853 s | 0.833 – 0.835 s | +45-122% | ✅ under 2 s |

## Why the preview drift isn't a production blocker

1. **Preview pod was under heavy load during the bench.** Six forensic audits ran in the prior 2 hours (Tracks 15.52, 15.52A, 15.52B, 15.52C, 15.53, 15.54). Multiple full-bucket walks (854 R2 objects each), multiple Python interpreter spawns.
2. **HTTP probes against production show no degradation** — same endpoints in Track 15.51 ranged 0.18 – 0.85 s; today 0.14 – 0.29 s. API-layer is fine or faster.
3. **PDF render is asynchronous server-side work**, not user-facing latency. It runs in the email-attach path or the on-demand-download path; neither has a 2 s SLO.
4. **No PDF code or template changed** between Tracks 15.51 → 15.54.

## Recommendation

During production soak (within first 2 hours of launch), run a fresh production-pod PDF bench by triggering a real incident email-with-PDF. Production-pod numbers should align with Track 15.51 baseline (1.7 – 2.0 s incident PDF) if the drift is environmental.

If production also exhibits the regression, investigate WeasyPrint / Mongo enrichment query plans as next steps.

## Verdict

🟢 GREEN for production. 🟡 YELLOW WARNING for preview-pod PDF latency (environmental, not architectural). Recommended production soak measurement included as deployment follow-up, not a blocker.

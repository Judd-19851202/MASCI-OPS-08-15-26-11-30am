# Sprint 1G · Photo Viewer Success Audit

**Batch:** OMEGA Sprint 1G · Post-Deploy Status Recheck
**Mode:** READ-ONLY · No code changes · No deployments · No restarts · No DB writes
**Date:** 2026-06-01 (probe window 14:42:23Z – 14:42:55Z)
**Target host:** `https://mascidocs.com` (production)
**Authorized by:** Operator Batch `(b) Sprint 1G Post-Deploy Status Recheck (current state, read-only)`

---

## 1 · Objective

Execute 50 photo-viewer probes against the production `/api/job-photos/{id}/raw` endpoint and determine whether the Sprint 1G presigned-URL fix is now serving 100 % of requests, intermittently failing, or fully failing.

---

## 2 · Sampling methodology

* **Population:** All 606 production `job_photos` index entries retrieved from `GET /api/job-photos` (admin-scoped, full corpus).
* **Sample size:** 50.
* **Selection:** Pseudo-random with seed `20260601` (deterministic so the sample is auditable). `random.sample(ids, 50)`.
* **Distribution across the corpus:**
  * 6 distinct project numbers (`24-12`, `25-21`, `24-13-CP`, `26-01-CP`, `25-03`, `25-22-CP`).
  * Multiple `daily_report` source ids per project, multiple `photo_index` positions per source.
  * Sample includes the operator-named forensic target (`daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0`) so the historical failure case is exercised.

**Per-probe call sequence:**

1. `GET /api/version` (correlated pod identity capture).
2. `GET /api/job-photos/{photo_id}/raw` with `X-Admin-Token: <legacy break-glass admin token>`.
3. Parse response body for `data_url` scheme classification:
   * `https` → presigned R2 URL (Sprint 1G fix code path).
   * `data` → legacy inline base64 (pre-iter64 record; still renderable).
   * `photo` → raw `photo://bucket/key` ref (stale pre-1G code · NOT renderable).
   * `other` → unexpected.
4. Record `(n, ts, photo_id, http, scheme, pod_uptime_s, pod_started_at)` to CSV.

Authentication used the legacy `/api/admin/login` break-glass endpoint (`MASCI1982!`). The break-glass POST writes a single audit-log row to `admin_audit` per session; no further writes occur during the read-only probe sequence.

---

## 3 · Raw results

Full per-probe data: `/app/memory/_sprint1g_recheck_probe_data.csv` (50 rows · auditable).

### 3.1 · HTTP status distribution

| HTTP code | Count | Percentage |
|---|---|---|
| **200** | **50** | **100 %** |
| 4xx | 0 | 0 % |
| 5xx | 0 | 0 % |

### 3.2 · URL scheme distribution

| Scheme | Count | Percentage | Renderable by lightbox? |
|---|---|---|---|
| `https://` (presigned R2) | **50** | **100 %** | ✅ Yes |
| `data:image/…` (legacy base64) | 0 | 0 % | ✅ would be |
| `photo://…` (stale-pod indicator) | **0** | **0 %** | ❌ would not be |
| other | 0 | 0 % | — |

### 3.3 · Pod-identity correlation

Every one of the 50 photo probes was preceded by a `/api/version` call. All 50 version calls returned the same pod signature:

```
started_at = 2026-06-01T14:31:54.511951+00:00
uptime_s   = 632 → 657 (natural wall-clock drift)
```

🎯 **Every photo probe was served by the single pod identified in `SPRINT1G_PRODUCTION_POD_REPORT.md`.**

### 3.4 · Forensic-target spot-check

Operator-named target from the original 1G forensic (`PHOTO_VIEWER_FORENSIC_REPORT.md` §3.3):

| Field | Pre-fix value | Current value |
|---|---|---|
| Source `daily_report.id` | `07e54a58-61f5-46b2-a755-8dc4582a5a94` | (unchanged) |
| Submitter | `Mike` | `Mike` |
| Date | `2026-05-29` | `2026-05-29` |
| `/raw` response `data_url` scheme | `photo://` | **`https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com/masci-hub/photos/2026/05/dr_07e54a58.../…?X-Amz-Signature=…`** |
| Lightbox renderable | ❌ | ✅ |

---

## 4 · Per-probe summary table (first 10 rows)

| n | photo_id | HTTP | scheme |
|---|---|---|---|
| 1 | `daily_report:9f05e2d1-…:5` | 200 | https |
| 2 | `daily_report:8a4be01b-…:0` | 200 | https |
| 3 | `daily_report:07e54a58-…:0` | 200 | https |
| 4 | `daily_report:9f05e2d1-…:11` | 200 | https |
| 5 | `daily_report:abc4d2e3-…:2` | 200 | https |
| 6 | `daily_report:e1f97c87-…:1` | 200 | https |
| 7 | `daily_report:1d1abe2f-…:3` | 200 | https |
| 8 | `daily_report:c0afae73-…:4` | 200 | https |
| 9 | `daily_report:b3247a20-…:0` | 200 | https |
| 10 | `daily_report:46723e15-…:7` | 200 | https |

(Remaining 40 rows identical pattern. Full CSV at `/app/memory/_sprint1g_recheck_probe_data.csv`.)

---

## 5 · Pass / fail summary

| Outcome | Count |
|---|---|
| ✅ Pass · 200 + https scheme (presigned R2) | **50 / 50** |
| ⚠️ Intermittent · 200 + photo:// scheme (stale-pod indicator) | **0 / 50** |
| ❌ Fail · non-200 or other scheme | **0 / 50** |

**Photo viewer success rate: 100 %.**

---

## 6 · Verdict

| Question | Answer |
|---|---|
| Is the photo viewer success rate 100 %? | ✅ **Yes** |
| Is it intermittent? | ❌ No |
| Is it failed? | ❌ No |
| Did any probe expose the stale-pod indicator? | ❌ No |
| Is a rolling restart still required? | ❌ **No** |

---

## 7 · Comparison with previous certification

| Metric | 2026-05-31 post-deploy probe (n=20+) | 2026-06-01 recheck (n=50) |
|---|---|---|
| `https://` (1G fix) | ~50 % | **100 %** |
| `photo://` (stale) | ~50 % | **0 %** |
| Distinct pod signatures hit | 2 | 1 |
| Verdict | Split-pod · intermittent failure | **Production healthy** |

The intermittent failure mode previously observed has fully cleared.

---

## 8 · OMEGA discipline confirmation

| Rule | Observed |
|---|---|
| Read-only against production | ✅ — only `GET /api/version` and `GET /api/job-photos/{id}/raw` |
| Authentication minimal & auditable | ✅ — single `/api/admin/login` POST (break-glass token), audit-logged |
| Zero code changes | ✅ |
| Zero deployments | ✅ |
| Zero restarts | ✅ |
| Zero DB writes (except inherent `admin_audit` login row) | ✅ |
| Sample size 50 (exact target) | ✅ |

🛑 End of photo success audit. Continue to `SPRINT1G_STATUS_RECHECK.md` for the consolidated recommendation.

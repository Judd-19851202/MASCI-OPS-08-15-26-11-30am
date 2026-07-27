# PRODUCTION ROOT CAUSE MATRIX

Use this for every defect found during live production verification.

| RCA Class | Symptom examples | Typical root cause | Fix location | Redeploy needed | Notes |
|---|---|---|---|---|---|
| Auth/session regression | login loop, session drop, portal bounce | token propagation bug, session-binding bug, local auth state regression | Preview code | Yes | Most likely fixable in preview |
| Role/permission regression | PM denied valid page, non-admin sees admin page | route guard mismatch, scope bug, policy drift | Preview code or production data | Usually | Validate whether user grants are correct in production |
| Production-only config issue | works in preview, fails only live | env var, secret, domain, TLS, CORS, storage config | Production environment | Maybe | May require Emergent Support if platform-level |
| Runtime / deploy artifact issue | wrong version, wrong API behavior, partial deploy | release mismatch, startup/runtime drift | Preview + redeploy | Yes | Validate `/api/version` and release identity |
| Database authority / live data issue | empty or wrong records, cross-env suspicion | DB target mismatch, missing production data, bad live records | Production config or data repair | Maybe | Must confirm authority first |
| API contract drift | UI loads but action fails | frontend/backend payload mismatch | Preview code | Yes | Common after recent feature changes |
| Storage / file / photo issue | upload fails, photos missing, PDF missing | R2/bucket policy, path mismatch, timeout, CORS | Preview code or production config | Maybe | Separate code bug vs live credential issue |
| Background scheduler / jobs | trust/recovery stale, digests dead | scheduler crash, lock issue, provider failure | Preview code or production runtime | Maybe | Needs evidence from admin surfaces/logs |
| Truth-surface defect | trust/deploy-readiness/recovery page contradicts state | payload logic bug, contract drift | Preview code | Yes | Recent work area |
| Performance / timeout issue | route hangs, very slow page, intermittent 5xx | query cost, worker saturation, storage latency | Preview code or production infra | Maybe | Needs timing evidence |
| UX / responsive issue | clipped UI, overlap, missing CTA | CSS/layout regression | Preview code | Yes | Usually straightforward |

---

## Defect log template

| Defect ID | Route | Symptom | Severity | RCA Class | Reproduction | Preview reproducible? | Proposed fix path | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|

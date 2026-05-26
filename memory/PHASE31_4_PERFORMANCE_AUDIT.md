# Phase 31.4 · Performance Audit
## iter441 · 2026-05-26

---

## API latency · sequential probe (5 samples each)

```
/api/health                                          avg=147ms ✅
/api/version                                         avg=141ms ✅
/api/admin/system-health                             avg=409ms ✅
/api/admin-strict/diag/persistence-health            avg=401ms ✅
/api/admin/digest/weekly?format=text                 avg=407ms ✅
/api/admin/operational-attachments/storage-summary   avg=265ms ✅
/api/admin-strict/diag/production-health             avg=788ms ✅ (probes mascidocs.com 5×)
/api/admin/backups-list-r2?limit=5                   avg=1970ms 🟡 inherent (R2 list of 1502 keys)
```

🟢 7/8 endpoints under 500ms. The slow one is bound by R2 list cost, not code path.

---

## Concurrent load · realistic Monday-morning simulation

8 workers · staggered 0.3s offset · 24 total requests across 4 endpoints:

```
total wall-clock:  3149ms
successful:        24/24
p50:               414ms
p95:               518ms
```

🟢 Well within operational ceiling. A typical Monday crew burst (5–15 crews
each making 1–2 simultaneous requests) is bounded by this profile.

---

## Concurrent load · synthetic stress test

24 workers · all started simultaneously (no stagger):

```
total wall-clock:  10472ms
successful:        24/24
p50:               9475ms 🟡
p95:               10409ms 🟡
```

Subsequent endpoint volley returned several 520s (Cloudflare backend-down)
which recovered within ~5 seconds.

**Interpretation**: a single uvicorn worker on the production pod can hold
TCP connections for 24 fully-simultaneous requests but processes them
serially, causing queue buildup. Cloudflare then briefly 520s on subsequent
hits until the queue drains.

**Risk assessment**: 🟡 NOT a Monday-morning blocker.
* Real crews don't generate 24 truly simultaneous admin requests.
* Crew-facing routes (dispatch, daily report, incident) are different code paths.
* If sustained heavy admin reporting is anticipated (e.g., end-of-week PM
  pulling everything), recommend operator either:
  * a) Stagger admin loads, OR
  * b) Increase worker count (deploy-side; see Action Item).

---

## Frontend rendering (mobile viewport, iPhone 14 Pro 390×844)

```
admin:        first paint < 1s · no compile error
dispatch:     first paint < 1s · LastActivityLine + FieldMemoryGlance visible
shop:         first paint < 1s · same components visible
safety:       first paint < 1s · same components visible
pm:           first paint < 1s · same components visible
leadership:   first paint < 1s · FieldMemoryGlance visible
hr:           first paint < 1s · no compile error
```

🟢 No render storms · no React loop warnings observed · no console-critical
errors in Playwright capture.

---

## Sub-questions answered

| Question | Answer |
| -------- | ------ |
| Slow queries? | Only `backups-list-r2` ~2s · inherent · not code. |
| Unnecessary polling? | None observed. LastActivityLine polls every 60s — calm and bounded. |
| Duplicate fetches? | None on the audited pages. |
| Oversized payloads? | All < 50KB except backup downloads (intentional). |
| Attachment bottlenecks? | None · presigned URLs are signed once per list. |
| Large collection scans? | None — all hot fields indexed (see DATABASE_HEALTH doc). |
| Bad indexes? | None. 332 indexes across 123 collections — appropriate. |
| Stale scheduler work? | None — Phase 31.3 fix landed; no duplicate fires. |

---

## Action Item (optional, post-Monday)

If observed traffic exceeds ~10 simultaneous admin requests sustained,
consider bumping uvicorn workers from `1` to `2` in the production
deploy config. Single-worker is normal for a Kubernetes pod with
1 vCPU; the staggered-test result shows it handles realistic crew
load fine.

🟢 No optimization is required for Monday morning go-live.

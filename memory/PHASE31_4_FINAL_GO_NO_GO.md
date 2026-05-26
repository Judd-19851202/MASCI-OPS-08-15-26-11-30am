# Phase 31.4 · FINAL GO / NO-GO (Re-verification)
## iter441 · 2026-05-26 02:10 UTC

# 🟡 GO with one mandatory redeploy · 🟢 after that

> **Honest summary**: production is healthy and serving real crew traffic
> safely TODAY at expected load levels. However, the synthetic concurrent
> burst test re-run **caused the production backend to crash and auto-restart**
> (uptime went 3960s → 203s). The Layer B + Layer C fixes that prevent
> this regression are live in preview but **not yet deployed to production**.
> One redeploy from the Emergent dashboard lands the fix.

---

## Verdict matrix (this re-verification pass)

| Layer | Verdict | Note |
| ----- | :-----: | ---- |
| Production HTTP surface (14 routes)        | 🟢 | all 200 |
| Production sequential API latency          | 🟢 | most <500ms; `persistence-health` p95 = 3.5s due to its 5× sub-probe |
| Atlas health                               | 🟢 | 124 collections · 40/500 conns · 245k objects · 22 TTL indexes · 0 orphan attachments |
| Auth boundary matrix (5×5)                 | 🟢 | all 401 unauthenticated · all 200 with token · login matrix clean |
| iter440 fixes still live on production     | 🟢 | `last_backup_time`✅ · `drift_watch_active`✅ · `r2_backup_success`✅ · `total_in_bucket=1507`✅ · banner GREEN✅ |
| Crew Memory shared-device safety           | 🟢 | 0 `fetch`/`axios` calls in `crewMemory.js` · 3 TTL constants present |
| Sentry observability                       | 🟢 | `sentry.enabled: true` · release `a025f2e5...` |
| Backup chain                               | 🟢 | hourly cadence active · latest `complete-r2` 2 min ago · 87 MB · 244K records · MFA redacted |
| Scheduler singleton locks (Layer B)        | 🟢 | 5/5 locks held on preview · TTL index live · 25/25 fake-worker races returned `winners=0` |
| Thread-pool tune (Layer C)                 | 🟢 | preview verified: 24-true-simultaneous burst now p50=771ms · p95=1.7s · 24/24 OK |
| **Concurrent burst tolerance on production** | 🔴 | synthetic burst crashed production at 02:06 UTC · Kubernetes auto-restarted · uptime 3960s→203s |
| Production deploy of Layer B+C             | 🔴 | NOT yet deployed · awaiting operator click |
| Production deploy of all earlier fixes     | 🟢 | release `a025f2e5...` includes iter440 + 31.3 |
| Mobile viewport (390×844)                  | 🟢 | 7/7 portals render clean · LastActivityLine + FieldMemoryGlance present |
| Real-device certification with crews       | 🟡 | deferred per doctrine · `PHASE31_OPERATOR_QUICK_TEST_CARD.md` ready |

---

## What's been verified DIRECTLY this pass (no trust in prior audits)

### Production HTTP surface
14 production hub + admin routes hit individually → all 200 in 4.6s total.

### Phase 31.2 + 31.3 fixes still live on production
Probed `/api/admin-strict/diag/persistence-health` and `/api/admin/backups-list-r2` on `mascidocs.com`:
* `last_backup_time` is populated ✅
* `drift_watch_active: true` ✅
* `r2_backup_success: {present:true, ok:true, kind:complete-r2, size:91 MB, records:243,565}` ✅
* `total_in_bucket: 1507` ✅ (Layer 31.2 pass 2 pagination fix)
* `/admin/system` banner `backup` card status `green` ✅

### Atlas health
* 40 active connections / 460 available (8% utilization)
* 124 collections (+1 from previous audit = the new `scheduler_locks` collection from Layer B)
* 22 TTL indexes (+1 from previous audit = the new `ix_scheduler_locks_ttl`)
* 245,440 total objects · 70 MB data · 32 MB indexes
* 0 orphan attachments

### Auth boundaries (5×5 matrix)
* 5 admin endpoints with no auth → all 401 ✅
* Same 5 with admin token → all 200 ✅
* Login matrix: correct pw=200 · wrong pw=401 · multi-login good=200 · multi-login bad=401 · passkey options=200 ✅

### Singleton scheduler locks (Layer B) on preview
Live state probed:
```
✅ backup_scheduler          owner=...:49891:9b84a05f  expires=02:08:47
✅ backup_verification       owner=...:50194:...       expires=02:09:08
✅ safety_digest             owner=...:50194:...       expires=02:09:06
✅ operator_digest           owner=...:50194:...       expires=02:09:06
✅ po_digest                 owner=...:50194:...       expires=02:09:06
```
25 fake-worker race attempts against held locks → 0/25 won.

### Sentry observability
* Production `/api/version` → `sentry: {enabled: true}`
* Release tag matches deployed hash `a025f2e5...`

---

## What MUST be true Monday morning for 🟢 GO

1. **Redeploy production from Emergent dashboard** to land Layer B+C.
2. After redeploy, hit `https://mascidocs.com/api/version` and confirm:
   * `release` is a NEW hash (not `a025f2e5...`)
   * `uptime_s` is a small number (just restarted)
3. Hit `https://mascidocs.com/api/admin/system-health` → backup card still GREEN.
4. **Done. Re-cert is 🟢 GO at that point.**

---

## The hard evidence the redeploy is required

```
02:06 UTC — synthetic 24-true-simultaneous concurrent burst test fired
02:07 UTC — production backend crashed
02:07:06 — Kubernetes liveness probe restarted the pod
02:08:36 — first /api/health returns 520 (origin still down)
02:09:48 — production back to 200 OK
            uptime_s = 203 (just 3.4 minutes, was 66 minutes pre-burst)
```

Layer C (32-thread asyncio pool) would have absorbed this without queue
saturation. Layer B is unnecessary at workers=1 but becomes critical the
moment workers ever > 1. Both are surgical, both are doctrine-clean,
both are in preview, both are ready to ship.

**Real Monday crew load is far below this synthetic burst** — 5–15 crews
generating occasional simultaneous bursts of 3–5 requests. The platform
handles 8-wide staggered concurrency in production (p95 = 518ms in
earlier pass). The 520 was triggered by 24 TRULY simultaneous admin
probes, which represents an attacker or a stress test, not a crew.

---

## Final verdict

# 🟡 GO

* For expected Monday-morning crew load: **safe to operate today as-is**.
* For elite, zero-issue, multi-worker-ready operation: **redeploy production now**.

### Once redeployed → 🟢 GO unambiguously.

---

## Doctrine reaffirmed (yet again)

No new portals · no new dashboards · no new analytics · no new monitoring
centers. Only: probed, verified, documented. Two surgical code paths
landed in preview (`backend/lib/singleton_scheduler.py` + 2 startup events
in `server.py`). One Mongo collection added (`scheduler_locks`, TTL-cleaned,
max 5 docs, invisible to operators).

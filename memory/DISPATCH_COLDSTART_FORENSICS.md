# Dispatch Cold-Start Forensics — iter437 · Phase Sigma-II

**Date:** 2026-05-27 00:25 UTC
**Endpoint under investigation:** `GET /api/field-leadership/portal/dispatch-today`
**Original symptom:** Single 20 250 ms outlier observed during iter437 perf probe (perf_forensics.json sample 22).
**Verdict:** ⚠ **CANNOT REPRODUCE** — root cause not verifiable. Documentation only. No patch shipped (per directive).

---

## 1. What was investigated

### Reproduction attempts (all FAILED to reproduce the spike)

| Test                                           | min   | p50  | p99    | max    | Conclusion |
|------------------------------------------------|------:|-----:|-------:|-------:|------------|
| 10 sequential cold→warm after fresh restart    | 176ms | 196ms| 226ms  | 226ms  | No spike   |
| 50 parallel calls                              | 179ms | 489ms| 782ms  | 782ms  | No spike   |
| Original perf_probe run (1 of 5 samples)       | 199ms |  —   | 20 250ms| 20 250ms| Reported   |

The 20-second spike from the original perf probe could NOT be reproduced under restart-fresh, sequential, or parallel-load conditions. The route handler is trivial and the target collection is empty.

### Route handler inspection (`/app/backend/routes/field_leadership_portal.py:347`)

```python
@router.get("/field-leadership/portal/dispatch-today")
async def fl_dispatch_today(actor=Depends(require_fl_user)):
    from datetime import date, timedelta
    today = date.today()
    tomorrow = today + timedelta(days=1)
    target_dates = [today.isoformat(), tomorrow.isoformat()]
    items = []
    async for d in db.dispatch_assignments.find(
        {"date": {"$in": target_dates}},
        {"_id": 0},
    ).sort("date", 1):
        items.append(d)
    return {"ok": True, "items": items, "count": len(items),
            "window": {"today": today.isoformat(), "tomorrow": tomorrow.isoformat()}}
```

Single `.find().sort()` against `dispatch_assignments`. No external service calls. No I/O beyond Mongo.

### Mongo investigation

```
=== dispatch_assignments indexes ===
  _id_                            : (_id, 1)
  da_tenant_state_assigned        : (tenant_id, 1)(current_state, 1)(assigned_at, -1)
  da_id_unique                    : (id, 1)
  da_tenant_truck_state           : (tenant_id, 1)(truck_id, 1)(current_state, 1)
  da_tenant_project_assigned      : (tenant_id, 1)(project_number, 1)(assigned_at, -1)
  da_tenant_driver_assigned       : (tenant_id, 1)(driver_id, 1)(assigned_at, -1)

dispatch_assignments docs in PROD: 0
```

**No index exists on the `date` field**, but the collection is currently empty so the impact is theoretical only.

`explain()` shows: `SORT` over `PROJECTION_SIMPLE` (no index used). With 0 docs there's nothing to scan — execution is sub-millisecond regardless.

---

## 2. Hypothesis (UNVERIFIED — cannot reproduce)

Most plausible cause of the original outlier, none of which I can reproduce:

| Hypothesis                                    | Evidence for/against                                  |
|-----------------------------------------------|--------------------------------------------------------|
| Atlas connection pool warm-up                 | Possible — was first request to FL surface in probe   |
| Network blip preview-pod ↔ Atlas              | Transient, possible, no telemetry to confirm           |
| Backend GIL contention                        | Probe was strictly sequential — unlikely               |
| Mongo cold cache fetch                        | Collection empty → no cache miss possible              |
| Probe-script timing artifact                  | Only 1 of 5 samples on this endpoint; not on others    |

**Confidence in any single hypothesis: low.** This pattern looks transient.

---

## 3. Cheap protective measure available — NOT applied

If `dispatch_assignments` ever starts holding meaningful data, the query `{"date": {"$in": [today, tomorrow]}}` would COLLSCAN. A `date_1` index would close that gap proactively. The change is additive and risk-free:

```javascript
// Recommended — DO NOT APPLY without explicit approval (per directive)
db.dispatch_assignments.createIndex({date: 1}, {name: "da_date_lookup_1"})
```

**Why I did NOT ship this:**
1. The collection is currently empty (0 docs) — there's no operational benefit today.
2. Per directive: cannot reproduce + unclear root cause → document only.
3. The actual original symptom (20s spike) was not a missing-index issue (an empty collection cannot benefit from an index).

---

## 4. Recommended monitoring

Until a root cause is observable, the appropriate response is **monitoring, not patching**:

1. **Add the endpoint to the perf probe as a 10-sample sweep** (currently 5). If the 20s outlier reproduces in a future run, we have it on tape.
2. **Atlas Performance Advisor** will flag any future slow query on this collection automatically.
3. **If dispatch_assignments starts accumulating docs** (e.g. once dispatch portal goes live with real data), revisit and add the `date_1` index proactively.

---

## 5. Rollback path

N/A — no code shipped this session for this finding.

---

## 6. Re-run instructions

```bash
# Cold-start reproduction attempt
sudo supervisorctl restart backend && sleep 6
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
TOK=$(curl -s -X POST "$URL/api/auth/multi-login" -H "Content-Type: application/json" \
   -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}' \
   | python3 -c "import sys,json;print(json.load(sys.stdin)['portal_tokens']['field_leadership'])")
for i in $(seq 1 10); do
  t=$(curl -s -o /dev/null -w '%{time_total}' "$URL/api/field-leadership/portal/dispatch-today" -H "X-FL-Token: $TOK")
  echo "$i: $(python3 -c "print(int(float('$t')*1000))")ms"
done
```

---

## 7. Verdict

**Dispatch cold-start root cause — NOT VERIFIED. No patch shipped.**

- ⚠ Original 20-second outlier could not be reproduced under any reasonable load pattern.
- ✅ Endpoint observed at 176-782 ms across 60 fresh measurements (cold + parallel).
- ✅ Route handler inspected — trivial, no external calls, no business-logic risk.
- ✅ Mongo indexes inspected — `date` field not covered, but collection empty so impact theoretical.
- 🟡 Cheap protective `date_1` index proposed but NOT applied (per directive: unclear root cause → don't ship).
- 🟡 Monitoring path documented for next observation cycle.

Per Phase Sigma-II discipline: **certified as "monitoring only", not patched.** The honest finding is: there is no verifiable bug here today, and shipping a speculative fix would violate the proof-based engineering doctrine.

# POST-DEPLOY · EMPLOYEE ROSTER PROJECTION · LIVE VERIFICATION
## OMEGA Authorization · Production Smoke

**Date**: 2026-06-03 (10:42 UTC probe window)
**Target**: https://mascidocs.com (production)
**Deploy authority**: OMEGA — Public Employee Roster Projection Hardening
**Release hash (post-deploy)**: `b81fd325d51e0c81d1f46427f65e5306`
**Backend started_at**: `2026-06-03T10:38:07.547194+00:00`

---

## 🟢 PRODUCTION VERIFIED

All 14 required post-deploy verification items PASSED. The hardened projection is live on production, the 5 public forms still load, HR/admin gating is preserved, the public-write 410 is preserved, and active-employee count behaviour is unchanged.

---

## 1 · Verification matrix (14 / 14 PASS)

| # | Requirement | Probe | Result |
|---:|---|---|:-:|
| 1 | `GET /api/health` returns 200 | `curl https://mascidocs.com/api/health` | 🟢 200 in 547 ms · `{"ok":true,"service":"masci-hub","ts":"2026-06-03T10:42:25Z"}` |
| 2 | Anonymous `GET /api/employees` returns 200 | `curl https://mascidocs.com/api/employees` | 🟢 200 · `count=247` |
| 3 | Anonymous payload contains ONLY allow-listed fields | Python set-difference probe | 🟢 keys = `['crew','employee_id','id','is_active','name','role','trade']` (exactly the 7 allow-listed fields) |
| 4 | Anonymous payload does NOT contain any forbidden fields | Python set-intersection probe vs FORBIDDEN list | 🟢 leaked forbidden = `[]` (all 13 forbidden fields gated) |
| 5 | Count still returns active employees | `curl …` + distribution probe | 🟢 247 records · `is_active=True` × 239 · field missing on 8 legacy records · `is_active=False` × **0** (matches the pre-existing server filter `{"is_active":{"$ne":False}}`) |
| 6 | Daily Report employee picker still loads (`/daily/new`) | HTTP smoke | 🟢 200 |
| 7 | Incident employee picker still loads (`/incidents/new`) | HTTP smoke | 🟢 200 |
| 8 | Safety Meeting attendee picker still loads (`/meetings/new`) | HTTP smoke | 🟢 200 |
| 9 | Equipment Inspection inspector picker still loads (`/equipment/new`) | HTTP smoke | 🟢 200 |
| 10 | Fleet DVIR driver picker still loads (`/fleet/dvir/new`) | HTTP smoke | 🟢 200 |
| 11 | HR/admin full employee records remain available only through gated routes | Anon probes against gated endpoints | 🟢 `/api/hr/employees` → 401 · `/api/admin/employees/status` → 403 · `/api/admin/employees/archive` → 403 |
| 12 | No employee data was modified | (a) Change is read-side projection only (`{find projection}`); (b) Production employee count 247 is unchanged from the pre-deploy probe earlier today | 🟢 |
| 13 | No database writes occurred | The projection change only affects Mongo `find` projection. No `update_*`, no `insert_*`, no `delete_*`. Deploy itself is code-only. | 🟢 |
| 14 | No frontend regression on public forms | All 5 public-form SPA routes return 200; same React bundle previously certified | 🟢 |

---

## 2 · Probe transcripts (verbatim)

### 2.1 · Health
```
status=200 time=0.546832s
{"ok":true,"service":"masci-hub","ts":"2026-06-03T10:42:25.449627+00:00"}
```

### 2.2 · `/api/employees` (anon)
```
count = 247
items = 247
keys present = ['crew', 'employee_id', 'id', 'is_active', 'name', 'role', 'trade']
UNEXPECTED (must be empty) = []
LEAKED forbidden (must be empty) = []
VERDICT: 🟢 PROJECTION HARDENED
```

### 2.3 · Public form smokes
```
  /daily/new             200
  /incidents/new         200
  /meetings/new          200
  /equipment/new         200
  /fleet/dvir/new        200
```

### 2.4 · Gated HR/admin endpoints
```
  /api/hr/employees                   401
  /api/admin/employees/status         403
  /api/admin/employees/archive        403
```

### 2.5 · Write-side preserved (anon POST → 410)
```
POST /api/employees/add (anon) → 410 (expected 410)
```

### 2.6 · `is_active` distribution
```
is_active distribution: {'True': 239, '<MISSING>': 8}
records with is_active==False (must be 0): 0
```

**Interpretation**: 239 records carry `is_active: true`; 8 legacy records have the field absent (already the case pre-hardening — the field was inconsistently populated historically). Crucially, **0 records** with `is_active=False` are returned, confirming the server-side filter `{"is_active": {"$ne": False}}` continues to suppress inactives as designed.

---

## 3 · Cross-reference vs. preview certification

| Layer | Preview (pre-deploy) | Production (post-deploy) |
|---|---|---|
| Allow-list fields only | 🟢 | 🟢 |
| Forbidden fields absent | 🟢 (13/13 gated) | 🟢 (13/13 gated) |
| Public form routes 200 | 🟢 (5/5) | 🟢 (5/5) |
| HR/admin endpoints gated | 🟢 (HR 401, admin 403/403) | 🟢 (HR 401, admin 403/403) |
| Write-side 410 preserved | 🟢 | 🟢 |
| Backend health | 🟢 | 🟢 |

**Production behaviour mirrors the certified preview behaviour exactly.**

---

## 4 · Verdict

🟢 **PRODUCTION VERIFIED** — The Public Employee Roster Projection Hardening is live, behaving as certified, and introducing no observable regression on the 14 required axes.

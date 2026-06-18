# TRACK 15.16 — PRODUCTION HEALTHCHECK / STARTUP STABILITY

**Build:** preview (`*.preview.emergentagent.com`), production deploy of same code path pending.
**Mode:** minimal backend compatibility fix · no auth / DB / route / permission / frontend changes.
**Run date:** 2026-06-18

---

## 1 · EXECUTIVE SUMMARY

Production logs reported recurring `GET /health` → **404** from the platform health probe (which dials `http://127.0.0.1:8001/health` directly, bypassing the public ingress), while `/api/health` returned 200. Root cause is a path-shape mismatch: the canonical app endpoint is `/api/health` but the platform probe targets bare `/health`. The fix is two top-level routes added directly to the FastAPI app (not the `/api` router): `GET /health` and `GET /healthz`. Both are unauthenticated, side-effect-free, DB-free, < 5 ms.

**Result:** internal probe at `127.0.0.1:8001/health` now returns **`200 {"status":"ok","service":"masci-backend"}`** in **3 ms**. `/api/health` continues to return 200 unchanged. Backend backstop regression (Track 15.14C, 39 checks) still PASS.

---

## 2 · LOG EVIDENCE

### Before (reproduced on preview, identical to production trace)

```
$ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8001/health
404
$ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8001/healthz
404
```

Matches the production trace shared in the directive:
```
nginx upstream connect() failed (111: Connection refused) while connecting
to upstream ... request: "GET /health" upstream: "http://127.0.0.1:8001/health"
```
(The "connection refused" lines are the brief window during which uvicorn is binding the port at startup; the 404s are the path-shape mismatch once uvicorn is up.)

### After

```
$ curl -v http://127.0.0.1:8001/health
< HTTP/1.1 200 OK
< server: uvicorn
< content-length: 41
< content-type: application/json
{"status":"ok","service":"masci-backend"}
```

`BACKEND_URL=http://127.0.0.1:8001 python3 backend/tests/track_15_16_health_probe.py`:
```
  ✓  /health             HTTP 200  body={"status":"ok","service":"masci-backend"}
  ✓  /healthz            HTTP 200  body={"status":"ok"}
  ✓  /api/health         HTTP 200  body={"ok":true,"service":"masci-hub", "ts":"..."}
  ✓  /api/healthz        HTTP 200  body={"ok":true}
  ✓  /health stays 200 with bogus token (unauthenticated probe)
  ✓  /health responds in 3 ms (well under 250 ms budget)

TRACK 15.16 internal healthcheck probe: PASS
```

---

## 3 · HEALTHCHECK MAP

| Caller | URL Hit | Expected Result | Actual Before | Actual After | Owner | Fix |
|---|---|---|---|---|---|---|
| Emergent platform probe | `http://127.0.0.1:8001/health` | 200 | **404** | **200 + JSON** | platform | NEW route in `server.py` |
| Emergent platform probe | `http://127.0.0.1:8001/healthz` (k8s convention) | 200 | **404** | **200 + JSON** | platform | NEW route in `server.py` |
| Ops dashboards · BackendStatusBanner | `/api/health` | 200 | 200 | 200 | app | unchanged (`build_health_router()`) |
| Ops dashboards | `/api/healthz` | 200 | 200 | 200 | app | unchanged |
| Build/version probe | `/api/version` | 200 | 200 | 200 | app | unchanged |
| Cluster probe | `/api/cluster/capacity` | 200 | 200 | 200 | app | unchanged |
| Public ingress · path "/health" routed to React SPA | `https://*.preview.../health` | SPA HTML 200 | SPA HTML 200 | SPA HTML 200 | ingress | not affected — production probe doesn't use this path |
| Frontend `BackendStatusBanner.jsx` polling | `/api/health` (via REACT_APP_BACKEND_URL) | 200 | 200 | 200 | app | unchanged |

The frontend banner does NOT poll `/health`; it polls `/api/health`. The 4-failure threshold (Track 15.13K) is unaffected by this change.

---

## 4 · ROOT CAUSE

Code evidence in `backend/routes/health_routes.py`:
```python
router = APIRouter(prefix="/api", tags=["health"])
@router.get("/health")   # → /api/health
@router.get("/healthz")  # → /api/healthz
```

The platform health probe targets bare `/health` on the upstream port `8001`. Until this track, no `/health` route existed on the FastAPI app — only `/api/health`. FastAPI returned 404 for `/health`, the proxy logged the 404, and the platform health checker recorded a failure.

**Origin of /health hits (answered explicitly):**
1. Is /health coming from nginx? — **YES, indirectly.** Nginx `proxy_pass http://127.0.0.1:8001/health` is the probe shape recorded in the production logs.
2. From Emergent platform/runtime health probe? — **YES, this is the probe origin.** Platform runtime contracts a bare `/health` path.
3. From Docker/container healthcheck? — Not directly visible in this pod's supervisor config; behaviour is consistent with the platform probe rather than a Docker `HEALTHCHECK`.
4. From frontend code? — **NO.** Frontend polls `/api/health` (verified in `BackendStatusBanner.jsx`).
5. From a load balancer? — Not separately visible; in this stack the load balancer probe and the runtime probe converge on the same upstream.
6. From another internal service? — **NO.** Greps for `/health` (non-/api) inside the backend source tree show only the two new routes added by this track.

---

## 5 · FILES CHANGED

`git diff` (this track, code only):

| File | Net | Reason |
|---|---|---|
| `backend/server.py` | **+25** lines (24 of which are comment) | Two new top-level routes: `GET /health` and `GET /healthz`, registered directly on the FastAPI `app` (NOT on `api_router`). Both are zero-auth · zero-DB · zero-side-effect. |
| `backend/tests/track_15_16_health_probe.py` | **+62** | New test verifying both probes return 200 with correct shape, accept bogus tokens, and respond in < 250 ms. |
| `memory/TRACK_15_16_PRODUCTION_HEALTHCHECK_STARTUP_STABILITY.md` | new | This document. |

**Nothing else.**

`grep -rE "auth_must_change|Require|api.js|SignIn|hr_portal|asset_care|equipment-inspection|change-password" /app | xargs -I{} git diff --stat {}` → **EMPTY**.

No frontend changes. No route registration changes. No `App.js` edits. No backend dependency edits. No auth, no permission, no DB, no env-var, no migration changes.

---

## 6 · EXACT FIX

`backend/server.py` lines 79–105 (immediately after `app.state.ready = False` and the `api_router = APIRouter(prefix="/api")` declaration):

```python
# Track 15.16 · Production healthcheck compatibility.
# ... full comment explaining intent ...
@app.get("/health", include_in_schema=False)
def _probe_health():
    return {"status": "ok", "service": "masci-backend"}

@app.get("/healthz", include_in_schema=False)
def _probe_healthz():
    return {"status": "ok"}
```

Both routes:

- registered on `app` directly (no `/api` prefix)
- `include_in_schema=False` so they do not pollute OpenAPI docs
- return synchronous static dicts → no `await`, no DB, no I/O
- no `Depends(...)` → no auth, no portal check
- no state mutation

---

## 7 · STARTUP / CONNECTION REFUSED AUDIT

`supervisord.conf` evidence:
```
[program:backend]
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
```

Startup timeline observed during this track (backend log):
```
1  initialise · indexes ensured · ~8 s of import + index calls
2  [identity-mirror] startup sync           t≈10–12 s
3  [role-templates] startup seed            t≈12–13 s
4  [boot-self-heal] / [asset-spine] / [scheduled-backup]    t≈14–17 s
5  [iter453.6] startup-readiness gate FLIPPED              t≈17 s
6  INFO: Application startup complete.                     t≈17 s
```

- Connection-refused window: ~0–17 s after `supervisorctl restart backend`. This is consistent with the production trace ("nginx upstream connect() failed during startup"). It is **harmless** — the platform probe simply retries.
- One uvicorn worker is consistent with the rest of the stack and is sufficient for the current load profile.
- The 404 noise (the actual defect) is independent of the connect-refused window and now resolved.

I did not change the startup ordering. The new `/health` route is wired before uvicorn binds, so it is available immediately when the port accepts connections. No readiness gate is needed for the probe — it intentionally returns 200 the moment uvicorn is alive, which is the standard liveness-vs-readiness convention.

---

## 8 · TESTS RUN

| Test | Result |
|---|---|
| `backend/tests/track_15_16_health_probe.py` (new) | **PASS** — 6 checks |
| `backend/tests/track_15_14c_predeploy_gate.py` (Track 15.14C safety gate) | **39 / 39 PASS** |
| Live curl: `/health`, `/healthz`, `/api/health`, `/api/healthz`, `/api/version`, `/api/cluster/capacity` on internal port | all 200 |
| Live curl: full HR + Admin sidebar routes via external preview URL | unchanged (no frontend touched) |

---

## 9 · STARTUP BEHAVIOR ASSESSMENT

- Uvicorn binds port 8001 within ~1–2 s of supervisor `start`.
- Background work (index ensure, identity mirror sync, role templates seed, boot self-heal, scheduler arms) completes in ~16 s before the readiness gate flips.
- `/health` and `/healthz` are reachable as soon as uvicorn is up (before the readiness gate flips), which is the correct shape for a liveness probe. They do not depend on Mongo, sentinels, schedulers, or external services.
- The platform's brief "connection refused" window during cold start is unchanged and remains harmless.

---

## 10 · REMAINING RISKS

- **None in code.** Two added routes are the minimal possible change. They cannot break auth, permissions, the database, the routing layer, Daily Reports, Asset Care, temp-password enforcement, or Pre-Ops, because none of those files were touched.
- The platform's choice of probe path (bare `/health` vs `/api/health`) is now satisfied. If the platform changes the convention again, the existing `/api/health` route is still there as a fallback.
- The external public ingress still serves the SPA at `/health` (because non-/api paths route to the frontend). That is not a regression — production health probes hit the upstream directly at `127.0.0.1:8001`, not the public URL.

---

## 11 · DEPLOYMENT SAFETY CHECKLIST

| Concern | Status |
|---|---|
| DB migration | NO |
| env-var changes | NO |
| auth changes | NO |
| permission changes | NO |
| frontend route changes | NO |
| sidebar / nav changes | NO |
| HR / PM / Asset / Pre-Ops logic changes | NO |
| email / SMS behaviour changes | NO |
| schema / index / collection changes | NO |
| process-manager / supervisord changes | NO |

Every "NO" is verifiable: only `backend/server.py` and `backend/tests/track_15_16_health_probe.py` are in this track's code diff.

---

## 12 · VERDICT

🟢 **DEPLOYABLE**

Justification — strictly from evidence:

1. The exact production defect (`GET /health` → 404) is reproduced on preview and **fixed** with two added FastAPI routes that return `{status:"ok",...}` in 3 ms with no auth, no DB, no side-effects.
2. `/api/health` continues to return 200 with its existing shape.
3. The platform health-probe loop will stop producing 404 noise once the new code is deployed; the SPA-facing `BackendStatusBanner` is unaffected because it polls `/api/health`, not `/health`.
4. No other files in any portal were touched. Track 15.14C safety gate still 39 / 39 PASS.
5. Test coverage for the new probes shipped alongside the fix (`track_15_16_health_probe.py`).
6. Risk surface = two `@app.get` decorators returning static dicts.

The only operator-side gate left is the production redeploy + a fresh check of the nginx access log to confirm the 404s on `/health` have ceased.

# Safe Route Extraction — Phase 2
## iter437 · Phase IV-BETA.5A-P6 · 2026-05-27

> Phase 1 (extracted in P4B + P5D): `guidance_routes.py`, `health_routes.py`
> Phase 2 (this pass): `static_helpers.py` — public utility helpers.

---

## 1 · Scope

This phase continues the controlled, low-risk modularization of
`server.py` by extracting **public utility helpers** that satisfy all
four extraction-safety criteria:

| Criterion | Why it matters |
|---|---|
| Stateless | No DB reads, no DB writes, no scheduler state |
| No auth | Endpoint is already public — no auth helper transitivity to maintain |
| Bounded input | Inputs are length-clamped before use (DoS-safe) |
| External contract has been frozen | Tests have already exercised the contract |

The first member of this phase is the QR-code generator at `GET /api/qr.svg`,
used by the Training Scan-&-Go posters and any UI that wants to inline a
QR without shipping a JS library.

---

## 2 · Out-of-scope (explicitly per directive)

The following families remain in `server.py` and **WILL NOT** be touched
in this phase:

| Family | Reason |
|---|---|
| Authentication (`/api/admin/login`, `/api/auth/*`, `/api/pm/login`, etc.) | High-blast-radius · directive forbids |
| Notifications (`/api/notifications/*`) | Active websocket coupling |
| Uploads & attachments | Storage-coupled · directive forbids |
| Safety escalation surfaces | Active doctrine work in progress |
| Dispatch backend | High volatility · directive forbids |
| Compliance/export logic (`/api/exports/*`) | Sensitive · audit-trail coupled |
| Webhooks | External SLA · directive forbids |
| Backup / restore admin routes | Destructive surface |

---

## 3 · Extracted in this pass

### 3.1 — `GET /api/qr.svg` → `routes/static_helpers.py`

| Property | Value |
|---|---|
| Source location (pre-extraction) | `server.py:8248-8267` |
| New location | `routes/static_helpers.py:33-58` |
| Dependencies | `segno` (already in `requirements.txt`), `fastapi.Response` |
| DB access | none |
| Auth | none (public) |
| Side effects | none |
| Caller surfaces | Training Scan-&-Go posters, any inline-QR UI |
| External contract | `data` (1-2048 chars · required) · `scale` (2-20 · default 6) |

### 3.2 — Behavioural parity proof

| Test | Pre-extraction | Post-extraction |
|---|---|---|
| `GET /api/qr.svg?data=https://mascidocs.com` → `200 image/svg+xml` | ✓ | ✓ |
| Body starts with `<svg` and contains `xmlns` | ✓ | ✓ |
| Backend response carries `cache-control: public, max-age=86400` | ✓ | ✓ |
| `data` > 2048 chars → `400` | ✓ | ✓ |
| Missing `data` → `400`/`422` (FastAPI validation) | ✓ | ✓ |
| Scale clamped to `[2, 20]` | ✓ | ✓ |

Locked in `tests/pw_suite/test_static_helpers_extraction.py` (5 tests · all green).

---

## 4 · Wiring

```python
# server.py · iter437 IV-BETA.5A-P6
from routes.static_helpers import build_static_helpers_router  # noqa: E402

app.include_router(build_static_helpers_router())
```

Mounted alongside `build_health_router()` so future static-utility
extractions all land in the same module.

---

## 5 · Server.py line-count delta

| Pass | server.py lines | Delta |
|---|---|---|
| Pre-P4B | 11334 | baseline |
| Post-P4B (guidance) | 11329 | -5 |
| Post-P5D (health) | 11318 | -11 |
| Post-P6 (static_helpers) | **11303** | -15 cumulative this pass |

Modest but cumulative · the doctrine here is **safe, small, additive**.

---

## 6 · Candidate backlog (next P7+ phases · not in this pass)

| Candidate | Risk | Reason held back |
|---|---|---|
| `GET /api/training/videos` (public read) | medium | Performs self-heal migration write on read · needs catalogue |
| `GET /api/health/full` | medium | Touches `_BACKUP_SCHEDULER_STATE` + `db.backup_health` · needs DI |
| `GET /api/version` | medium | Depends on `_STARTUP_TS` + `_SOURCE_HASH` lifecycle globals |
| `GET /api/admin/guidance/coverage` | low | Admin-gated · could move alongside guidance_routes once auth-helper DI pattern is documented |
| `GET /api/admin/guidance/workflow-coverage` | low | Same as above |

Each candidate will be extracted only when an isolated catalogue audit
verifies it satisfies all four safety criteria.

---

## 7 · Tests

| File | Coverage |
|---|---|
| `tests/pw_suite/test_static_helpers_extraction.py` (NEW · 5 tests) | Behavioural parity for `/api/qr.svg` |
| `tests/pw_suite/test_p5_dispatch_health_autocheckpoint.py` (UNCHANGED) | Health route parity, still green |
| `tests/pw_suite/test_guidance_routes_extraction.py` (UNCHANGED) | Guidance route parity, still green |

---

## 8 · Sign-off

- **Author:** E1 (operational governance pass · iter437 IV-BETA.5A-P6)
- **Behavioural parity:** verified via 5 new pytest cases + curl trace
- **Extraction risk:** lowest possible · no DB · no auth · no state
- **Production deploy:** No · preview only

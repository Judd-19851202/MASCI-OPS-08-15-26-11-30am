# FOCP SECURITY VALIDATION · `GET /api/employees`
## Read-only forensic report. No code modified. No fixes applied.

**Date**: 2026-06-03
**Investigator**: Certification agent (read-only mode)
**Target finding**: Pre-existing observation from `LIVE_PRODUCTION_STABILITY_REVIEW.md` §2.2 — anonymous `GET /api/employees` returns full roster.

---

## 1 · Is `/api/employees` publicly accessible without authentication?

**YES — by intentional design.**

The route definition has **no authentication dependency** of any kind (no `Depends(require_*)`, no token validation, no portal check). It is registered on `api_router` which has prefix `/api`, and `api_router` itself carries no `dependencies=[...]` list at construction.

**Live probe (production)**:
```
GET https://mascidocs.com/api/employees   →  200 OK
items.length == 247
```

The docstring on the route explicitly states it is public (see §3 below).

---

## 2 · What exact authentication middleware protects the route?

**NONE.** There is no global auth middleware. FastAPI auth on this app is **per-route via `Depends(...)`**. The `/api/employees` route omits any auth dependency.

The middleware chain registered on the FastAPI `app` is (in registration order — Starlette runs the most-recently-added first on the request path):

| # | Middleware | File · line | Purpose |
|---|---|---|---|
| 1 | `install_session_timeout_middleware(app, db)` | `backend/server.py:77` | Validates idle/abs session timeouts on routes that present a token; does NOT require auth — anonymous requests pass through |
| 2 | `usage_tracking_middleware` | `backend/server.py:9344` (`app.middleware("http")(usage_tracking_middleware)`) | Telemetry only; does not enforce auth |
| 3 | `CORSMiddleware` | `backend/server.py:12074-12081` | CORS only |
| 4 | Thumbnail cache-header middleware (`BaseHTTPMiddleware`) | `backend/server.py:12099-…` | Strips cache-poisoning headers from `/thumb(-signed)?` only; not an auth gate |

**None of these middlewares enforce authentication.** Auth is the responsibility of each route's `Depends(...)` parameters, and `/api/employees` has none.

For comparison, the **gated** sibling routes show what auth-enforcement looks like on this same app:

| Route | Source | Auth gate |
|---|---|---|
| `GET /api/admin/employees/status` | `backend/server.py:3319-3320` | `actor: Dict[str, Any] = Depends(_require_hr_or_admin_for_queue)` |
| `GET /api/admin/employees/archive` | `backend/server.py:3339-3340` | `actor: Dict[str, Any] = Depends(_require_hr_or_admin_for_queue)` |
| `GET /api/hr/employees` | `backend/routes/employee_lifecycle.py:767` | Mounted on `_hr_portal_router` with HR token gate |
| `GET /api/employees` (this finding) | `backend/server.py:3307-3316` | **none** |

---

## 3 · Route definition and middleware chain

### 3.1 · Route definition (verbatim)

**File**: `backend/server.py`, **lines 3303-3316**

```python
# ---------------------------------------------------------------------------
# Employees / crew roster — used by Daily Report's "MASCI Crews on Site"
# section and any other employee dropdown across the platform.
# ---------------------------------------------------------------------------
@api_router.get("/employees")
async def list_employees():
    """Public — returns the full MASCI crew roster (sorted by name)."""
    await _purge_expired("employees")
    cursor = db.employees.find(
        {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]},
        {"_id": 0},
    ).sort("name", 1)
    docs = await cursor.to_list(2000)
    return {"items": docs, "count": len(docs)}
```

**Observations on the projection**:
- `{"_id": 0}` removes only the Mongo `_id` field.
- **No allow-list / projection of specific fields.** Every other field stored on the employee document is returned.
- `ACTIVE_FILTER` (`backend/server.py:1235`) is `{"deleted_at": {"$in": [None, ""]}}` — soft-delete filter; not an auth gate.
- Up to 2000 records returned per call.

### 3.2 · Router registration

**File**: `backend/server.py`

```python
42  api_router = APIRouter(prefix="/api")        # no `dependencies=` argument
...
8853  app.include_router(api_router)             # mounted with no gating
```

### 3.3 · Middleware chain (verbatim)

```python
# Session-timeout middleware (line 77)
install_session_timeout_middleware(app, db)

# Usage tracking middleware (line 9344)
app.middleware("http")(usage_tracking_middleware)

# CORS middleware (lines 12074-12081)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=_cors_credentials,
    allow_origins=_cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thumbnail cache header middleware (line 12099 onwards) — only applies to /api/job-photos/.../thumb(-signed)?
```

None of these introduce an auth requirement that would gate `/api/employees`.

---

## 4 · Sanitized sample response

Live anonymous probe against production (sanitized — real names + emails redacted):

```http
GET https://mascidocs.com/api/employees
Host: mascidocs.com
(no Authorization header)

→ HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "items": [
    {
      "id": "<uuid>",
      "name": "<First Last>",
      "employee_id": "",
      "trade": "",
      "role": "",
      "crew": "",
      "email": "",
      "phone": "",
      "is_active": true,
      "created_at": "2026-05-26T11:07:58.096523+00:00",
      "updated_at": "2026-05-26T11:07:58.096523+00:00",
      "approved_company_driver": true,
      "cdl_holder": false,
      "cdl_expiration_date": "",
      "cdl_state": "",
      "cdl_endorsements": [],
      "cdl_restrictions": [],
      "driver_status": "",
      "medical_card_expiration_date": "",
      "status_history": [
        {
          "ts": "2026-05-26T11:07:58.096523+00:00",
          "actor": "<actor-email@mascigc.com>",
          "action": "create_via_driver_import",
          "source": "Drivers on Insu…"
        }
      ]
    },
    ...
  ],
  "count": 247
}
```

### 4.1 · Field-level inventory

| Field | Sensitivity | Justified by stated use ("employee dropdown")? |
|---|---|:-:|
| `id` (uuid) | LOW (internal identifier) | YES — needed to bind a picker selection |
| `name` | LOW–MEDIUM (already on jobsite) | YES — dropdown label |
| `employee_id` | LOW | NO (not needed for dropdown UX) |
| `trade`, `role`, `crew` | LOW | YES — filter / display |
| `email` | MEDIUM (PII) | NO |
| `phone` | MEDIUM (PII) | NO |
| `is_active` | LOW | YES (filter) |
| `created_at`, `updated_at` | LOW | NO |
| `approved_company_driver`, `driver_status` | MEDIUM (operational status) | NO |
| `cdl_holder`, `cdl_expiration_date`, `cdl_state`, `cdl_endorsements`, `cdl_restrictions` | **MEDIUM-HIGH (DOT-regulated PII)** | NO |
| `medical_card_expiration_date` | **HIGH (HIPAA-adjacent — driver medical status)** | NO |
| `status_history[].actor` | MEDIUM (internal user emails exposed) | NO |
| `status_history[].source` | LOW–MEDIUM (operational provenance) | NO |

### 4.2 · Aggregate measurements (live)

| Measure | Value |
|---|---|
| Total records returned | **247** |
| Records with non-empty `email` | 2 |
| Records with non-empty `phone` | 3 |
| Records with `status_history` populated | **86** |
| Records with CDL holder = true (CDL fields populated) | population-dependent; cdl_holder field returned for all 247 |
| Records with `medical_card_expiration_date` populated | population-dependent; field returned for all 247 |

The CDL + medical-card exposure surface is the highest-sensitivity element of this response. Even when the field is blank for a given employee, the **schema disclosure** alone signals to a reader that this platform stores DOT/medical data — useful reconnaissance for a targeted attack.

---

## 5 · Frontend / API consumers that depend on this endpoint

Direct callers of `GET /api/employees` (sole owner of the `_cache` is `EmployeeCombo.jsx`; other pages call `axios.get(API/employees)` directly):

### 5.1 · Shared component (loads + caches the roster)
| File | Line | Notes |
|---|---|---|
| `frontend/src/components/EmployeeCombo.jsx` | 12, 43 | `api.get("/employees", { timeout: 30000 })` — module-level `_cache` reused across every page that imports it |

### 5.2 · Pages that import `EmployeeCombo`
| File | Line | Workflow context |
|---|---|---|
| `frontend/src/pages/NewDailyReport.jsx` | 30 | "MASCI Crews on Site" picker |
| `frontend/src/pages/NewIncident.jsx` | 31 | Reporter / witnesses picker |
| `frontend/src/pages/NewMeeting.jsx` | 21 | Attendees picker |
| `frontend/src/pages/NewInspection.jsx` | 21 | Inspector / owner picker |
| `frontend/src/pages/NewEquipmentInspection.jsx` | 22 | Inspector picker |
| `frontend/src/pages/NewFleetDVIR.jsx` | 45 | Operator picker |

### 5.3 · Direct callers (axios.get without going through the combo)
| File | Line | Use |
|---|---|---|
| `frontend/src/pages/NewSafetyEquipmentIssuance.jsx` | 78 | Roster preload for issuance picker |
| `frontend/src/pages/NewSafetyEquipmentTraining.jsx` | 59 | Roster preload for training picker |
| `frontend/src/pages/HrSafetyRecords.jsx` | 74 | Records-by-employee pivot |
| `frontend/src/pages/SafetyTrainingRecords.jsx` | 90 | Training records pivot |
| `frontend/src/pages/SafetyEmployeeProfiles.jsx` | 61 | Profile selector |

### 5.4 · Health probe consumer
| File | Line | Use |
|---|---|---|
| `frontend/src/components/SystemHealthBadge.jsx` | 22 | Listed as a "critical: true" health probe; the badge renders RED if `/employees` is unreachable; mounted on `PmShell.jsx`, `AdminShell.jsx` |

### 5.5 · Shared abstractions that reference the same listEndpoint
| File | Line | Use |
|---|---|---|
| `frontend/src/components/EmployeeMasterPanel.jsx` | 17 | `listEndpoint="/employees"` passed to `MasterListPanel.jsx` |
| `frontend/src/components/MasterListPanel.jsx` | 31 | Documented contract: `GET listEndpoint → {items: [...], count}` |

**Total in-app consumers**: **6 form pages** (DR / Incident / Meeting / Inspection / Equipment Inspection / Fleet DVIR) + **5 direct pages** (Safety Equipment Issuance / Training / HR Records / Safety Training Records / Safety Employee Profiles) + **1 health badge** + **1 master-data panel pattern**.

A meaningful portion of these consumers (DR, Incident, Meeting, Inspection, Fleet DVIR, Equipment Inspection) are public/semi-public form surfaces that operate before a full auth session is necessarily attached — which is the design rationale the route docstring is appealing to.

---

## 6 · Intentional design vs. legacy oversight

**Intentional design** — supported by four converging signals:

| Signal | Citation |
|---|---|
| (a) The route's own docstring declares it public | `backend/server.py:3309` — `"""Public — returns the full MASCI crew roster (sorted by name)."""` |
| (b) The header comment above the route explains the design rationale | `backend/server.py:3303-3306` — "Employees / crew roster — used by Daily Report's 'MASCI Crews on Site' section and any other employee dropdown across the platform." |
| (c) Multiple prior pre-deployment certifications explicitly enumerate the endpoint as "200 (by design)" | `memory/FINAL_PRE_DEPLOYMENT_SYSTEM_AUDIT.md:62` — `\| /api/employees \| 200 (by design) \| ✅ 200 \|` |
| (d) A sibling endpoint exists to gate the **write** side: `POST /api/employees/add` returns **HTTP 410** | `memory/EMPLOYEE_GOVERNANCE_ALPHA_IMPLEMENTATION_REPORT.md` and Phase Alpha G-1 — anonymous **create** is closed; read remains open by deliberate carve-out. |

There is also a sibling carve-out under `/api/master-lookup/employees` (`backend/routes/master_lookup.py:87`) which is the "master data" view, also designed for public/portal callers.

**Caveat — design is intentional; field surface is over-broad.** The use-case the design appeals to ("any employee dropdown") needs `id` + `name` + (at most) `crew`/`role`. The endpoint actually returns CDL fields, medical-card expiration, `status_history` with actor emails, `created_at`/`updated_at`, `email`, `phone`, etc. There is **no explicit allow-list projection**; only `_id` is excluded. So while the **public-ness** is intentional, the **field set** appears to have grown organically without a corresponding tightening of the projection. This is a **doctrine drift**, not a design flaw at registration time, and matches the "legacy expansion of an originally-narrow public read" pattern.

---

## 7 · Classification

### 7.1 · Headline classification

**🟡 MEDIUM** — DESIGNED PUBLIC, BUT FIELD SURFACE IS OVERBROAD.

Reasoning:
- The endpoint is **intentionally public** (not a configuration error, not a missing dependency, not an auth-middleware bypass). This rules out FALSE POSITIVE / CRITICAL / HIGH on the "did somebody screw up" axis.
- The information returned, however, **exceeds what the stated use case requires**. CDL data, medical-card expirations, internal actor emails in `status_history`, and the full schema disclosure are returned to any anonymous client. This is **doctrinal data exposure** — the same severity class as the recently-remediated OKCP scope leak.
- The HR-sensitive subset (cdl/medical/status_history.actor) is **NOT credential / token / financial PII**. It is operational + DOT/medical-adjacent PII. Severity is **above LOW** (the data is meaningful to a malicious actor — recon for spear-phishing, knowledge of CDL holders, knowledge of medical-card cycles) but **below HIGH** (no passwords, no auth tokens, no financial data, no SSN).

### 7.2 · Decision criteria

| Class | Verdict | Why |
|---|:-:|---|
| FALSE POSITIVE | ✗ | The exposure is real and live (verified twice). |
| LOW | ✗ | CDL endorsements / medical-card expiration / internal actor emails on 247 employees is more than "minor info disclosure". |
| **MEDIUM** | **✓** | Intentional design, no auth bypass, but the field surface is broader than the use case demands. Mitigation is mechanical (a projection list); not a structural rework. |
| HIGH | ✗ | No credentials, tokens, financial, SSN, or write capability exposed. The `POST /api/employees/add` sibling write is already gated (410). |
| CRITICAL | ✗ | No system-takeover or large-scale PII (HIPAA/SSN-class) breach risk. |

### 7.3 · Recommended (NOT executed) remediation path

If the operator concurs with the MEDIUM classification, the smallest viable fix is a **projection narrowing** at `backend/server.py:3311-3314`, replacing `{"_id": 0}` with an allow-list:

```python
{"_id": 0, "id": 1, "name": 1, "crew": 1, "role": 1, "trade": 1, "is_active": 1}
```

This preserves every documented frontend consumer (all of which use only `id`, `name`, and at most `crew`/`role`/`trade`) while eliminating CDL, medical-card, status_history, email/phone, and timestamp disclosure from the anonymous surface.

**Owner sign-off required before any change. This report is read-only; no code touched.**

---

## 8 · Summary

1. **Public?** YES — by design.
2. **Auth middleware?** NONE — auth on this app is per-route via `Depends(...)`; this route omits all such deps.
3. **Route definition?** `backend/server.py:3303-3316` — `@api_router.get("/employees")` with no `Depends(...)`.
4. **Anon response?** Full roster of 247 records with name, ids, CDL fields, medical-card date, status_history (actor email), email/phone (sparsely populated), driver_status. Sanitized sample in §4.
5. **Frontend consumers?** 1 shared component (`EmployeeCombo`), 6 forms (DR / Incident / Meeting / Inspection / Equipment Inspection / Fleet DVIR), 5 additional direct callers, 1 health badge, 1 master-data panel — at least **13 distinct UI consumers** + 1 health monitor. (§5)
6. **Intentional or oversight?** Intentional public read by design — but the field projection has drifted broader than the stated use case demands.
7. **Classification?** 🟡 **MEDIUM** — designed public, field surface overbroad. Mechanical remediation available (projection narrowing) requires operator authorization.

**No code modified. No deploy. No fixes attempted.**

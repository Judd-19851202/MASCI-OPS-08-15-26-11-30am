# AUTH_AND_PORTAL_GOVERNANCE.md
**Initiative:** Platform Governance Convergence — Phase 1
**Iteration:** iter353 · Phase 1
**Generated:** 2026-05-23
**Status:** READ-ONLY · Audit + consolidation proposal · No auth code will be migrated yet.

---

## 1 · Current portal token model

The platform supports **7 portal token types**, each backed by its own user collection.

| Portal | Header | User collection | Login endpoint | Token format | Token TTL |
|---|---|---|---|---|---|
| Admin | `X-Admin-Token` | (env-set HMAC + bootstrap admin) | `POST /api/auth/admin-login` | HMAC-signed string | 8 h sliding |
| Safety | `X-Safety-Token` | `db.safety_users` | `POST /api/safety/login` (within safety_portal) | UUIDv4 | 12 h |
| HR | `X-HR-Token` | `db.hr_users` | `POST /api/hr/login` | UUIDv4 | 12 h |
| Shop | `X-Shop-Token` | `db.shop_users` | `POST /api/shop/login` | dotted `<user_id>.<random>` | 12 h |
| PM | `X-PM-Token` | `db.pm_users` | `POST /api/pm/login` | dotted | 12 h |
| Dispatch | `X-Dispatch-Token` | `db.dispatch_users` | `POST /api/dispatch/login` | dotted | 12 h |
| Field Leadership (native) | `X-Leadership-Token` | `db.field_leadership_users` | `POST /api/fl/login` (iter348) | UUIDv4 | 24 h |
| Field Leadership (shared pwd · legacy) | `X-Leadership-Token` | (in-memory shared password) | `POST /api/leadership/login` | UUIDv4 | session | **LEGACY — GAP-012** |

### Multi-login (super-admin convenience · iter346-B)
`POST /api/auth/multi-login` takes super-admin email+password and returns `portal_tokens: {admin, safety, hr, shop, pm, dispatch, field_leadership}` — every portal token minted from one call. Used by the testing harness, by the iter351/iter352 scripts, by FL bulk-create flows. **Super-admin only.**

### Cross-portal token resolver
`make_require_any_portal_token(db, is_valid_admin_token)` — factory in `routes/integrations/_deps.py`. Validates any of the 7 portal tokens and returns `{"_actor": <portal>, ...user fields}`.

**Used by 48 cross-portal read routes** — health card, global search, tasks/notifications, banners, document expirations, asset transfers, signatures, project health.

---

## 2 · Auth-gate inventory (canonical list — 18 distinct gates)

### Tier 1 — Admin authority (most sensitive)
| Gate | Variants | Used for |
|---|---|---|
| `require_admin` | `require_admin`, `require_admin_async`, `require_admin_dep` | Admin token required. Standard admin mutations. |
| `require_admin_strict` | `require_admin_strict`, `require_admin_strict_dep` | Admin token **+ recent step-up MFA**. Backups, audit deletion, promo assets, complete-archive download. |

### Tier 2 — Portal-owner authority (single portal write)
| Gate | Used for |
|---|---|
| `require_hr_user` / `require_hr_user_dep` | HR-only writes (hr_portal, payroll_variance) |
| `_require_safety_or_admin` | Safety forms write paths |
| `require_safety_token` | Public-token Safety endpoints (fire-ext bulk import) |
| `require_fl_user` | FL portal writes |
| `require_dispatch_token` | Dispatch portal-only writes |

### Tier 3 — Multi-portal shared authority
| Gate | Roles allowed | Used for |
|---|---|---|
| `require_hr_or_admin` | HR + Admin | iter352 CDL importer, employee lifecycle |
| `require_safety_or_admin` | Safety + Admin | safety topic library |
| `require_safety_or_hr_or_admin` | Safety + HR + Admin | safety_portal documents + training reads |
| `require_shop_or_admin` | Shop + Admin | equipment master, asset archive |
| `require_dispatch_or_admin` | Dispatch + Admin | fleet ops |

### Tier 4 — Cross-portal / generic
| Gate | Description |
|---|---|
| `require_any_portal_token` | Any signed-in portal user. Read-only routes. 48 occurrences. |
| `require_caller` | Identity-aware reads (job_photos). Returns the actor for per-user filtering. |
| `require_write` | Operations-portal write gate (currently undocumented · GAP-011) |
| `require_signed_in_or_public` | Optional auth — public fleet defect submission |
| `require_token` | Signed-link public access (safety_exports) |
| `require_dev` | ForgedOps vendor-only header (internal builds) |

---

## 3 · Auth-flow architecture (current)

### Login flow (per portal)
```
Frontend                 Backend                   DB
  │                         │                       │
  │ POST /api/<portal>/login │                       │
  │ {email, password}       │                       │
  ├────────────────────────▶│                       │
  │                         │ verify bcrypt hash    │
  │                         ├──────────────────────▶│
  │                         │ user row              │
  │                         │◀──────────────────────┤
  │                         │ generate token (UUIDv4 or HMAC) │
  │                         │ store {token, user_id, expires_at} on user row │
  │                         ├──────────────────────▶│
  │ {token, user}           │                       │
  │◀────────────────────────┤                       │
  │ localStorage.setItem("masci.<portal>.token", token)
```

### Token validation (per request)
```
Frontend                 Backend                   DB
  │ GET /api/foo            │                       │
  │ X-<Portal>-Token: ...   │                       │
  ├────────────────────────▶│                       │
  │                         │ require_<gate>        │
  │                         │  ├─ is_valid_<portal>_user_token_async(db, token)
  │                         │  │     ├─ find user where token=X and expires_at>now │
  │                         │  │     │   refresh expires_at (sliding window) │
  │                         │  ├─ if invalid: HTTPException(401)
  │                         │  └─ if valid: returns user dict with _actor
  │                         │ → handler executes with actor in scope
  │ {data}                  │
  │◀────────────────────────┤
```

### Multi-login (super-admin)
```
Frontend                 Backend                   DB
  │ POST /api/auth/multi-login {email, password}    │
  ├────────────────────────▶│                       │
  │                         │ bcrypt verify against admin record │
  │                         │ for each portal: generate or fetch existing token │
  │                         ├──────────────────────▶│  (touches all 7 user collections) │
  │ portal_tokens: {admin, safety, hr, shop, pm, dispatch, field_leadership}
  │ + session_token (multi-portal master)
  │◀────────────────────────┤
```

---

## 4 · Frontend localStorage keys (per portal)

| Portal | Keys |
|---|---|
| Admin | `masci.admin.token` (+ refresh + expires_at) |
| Safety | `masci.safety.token`, `masci.safety.user` |
| HR | `masci.hr.token`, `masci.hr.remember`, `masci.hr.user` |
| Shop | `masci.shop.token`, `masci.shop.user` |
| PM | `masci.pm.token`, `masci.pm.user` |
| Dispatch | `masci.dispatch.token`, `masci.dispatch.user` |
| Field Leadership | `masci.fl.token`, `masci.fl.user` |
| Multi-portal | `masci.session.token` (super-admin master) |

Helper module: `frontend/src/lib/<portal>Auth.js` (e.g. `hrAuth.js`, `shopAuth.js`).

---

## 5 · Findings

### A · Strengths
- ✅ **Clean separation of concerns** — each portal owns its user collection + login + token.
- ✅ **Cross-portal reads are explicit** — `require_any_portal_token` returns `_actor` so handlers can branch safely.
- ✅ **No shared-secret writes** — only public defect submission is anonymous-friendly, and it's bounded to one endpoint.
- ✅ **Step-up MFA scaffolding exists** — `admin_hardening.py` `require_recent_step_up_*` already wraps the truly dangerous surfaces.
- ✅ **Super-admin multi-login** — eliminates 7 separate logins during ops triage / film capture / testing.

### B · Inconsistencies (cataloged for Phase 2)
1. **GAP-008** — 5 admin-gate variants (only 2 semantically distinct). Refactor to canonical `require_admin` + `require_admin_strict`.
2. **GAP-009** — `require_hr_or_admin` defined in two route files (inline duplication).
3. **GAP-010** — Three Safety-can-touch-this gates (`_require_safety_or_admin`, `make_require_safety_or_hr_or_admin`, `require_safety_token`).
4. **GAP-011** — `require_write` is opaque (no docstring).
5. **GAP-012** — FL has TWO auth paths (legacy shared-password + native). Sunset legacy.

### C · Security findings
1. **GAP-018** — Super-admin has no MFA at the multi-login flow itself. Step-up MFA only kicks in at specific surfaces (backups, audit deletion, promo). The super-admin SESSION is a high-value target.
2. **GAP-019** — Portal-grant changes (admin adds/removes a Safety user) are NOT written to `admin_audit_log`. Only the user collection row reflects it.
3. **GAP-020** — Public defect submission has no rate limit / no challenge.
4. **No password rotation policy** — portal users keep the same password indefinitely unless they manually change it.
5. **No session-revocation on grant change** — if Admin demotes a Safety user from "manage_documents", their existing token continues to work until natural expiry.

### D · Architectural debt
1. **`pm_users`, `shop_users`, `dispatch_users`, `field_leadership_users`** all reimplement the same `{id, email, name, pw_hash, token, token_expires_at, ...}` pattern. Could be consolidated into a single `portal_users` collection with a `portal` discriminator field. Phase 2 candidate but LOW priority — current per-portal collections are stable.

---

## 6 · Phase 2 proposed convergence plan

### iter354 — Auth gate consolidation
- Create `lib/rbac_gates.py` with canonical gates:
  - `require_admin`, `require_admin_strict`
  - `require_<portal>_user` for each portal
  - `require_<role>_or_<role>` shared gates
  - `require_any_portal_token` (move from integrations/_deps.py to here)
  - `require_caller`, `require_write`, `require_token`
- Document each gate with docstring + role list.
- Replace all 18 current gate implementations with imports from `lib/rbac_gates.py`.
- Tests: each gate has a unit test verifying its role set.

### iter357 — Super-admin MFA
- Enroll super-admin (and any role flagged `is_super_admin: true`) in mandatory TOTP.
- Multi-login flow gains a 2nd step: TOTP code required for portal_tokens to be minted.
- Step-up extension: existing `require_admin_strict` continues to work, just stacks with login MFA.

### iter357b — Portal-grant audit
- Wrap `db.<portal>_users.insert_one/update_one/delete_one` calls in `auth_directory_routes.py` with `audit.write_log()` writes.
- Each entry: `{ts, actor, actor_role, action: "portal_user_grant"|"...revoke"|"...edit", target_portal, target_user, changes}`.

### iter354b — FL legacy auth sunset (GAP-012)
- Audit current uses of `X-Leadership-Token` shared-password path.
- Migrate any remaining users to native FL accounts.
- Remove `_check_leadership_token` and the shared-password code path.
- Tests: shared-password rejection.

### iter360b — Public surface rate limits
- Add per-IP rate limit to `POST /api/fleet/defects` and `POST /api/safety/exports/.../{token}` public endpoints.
- Optional: simple captcha challenge.

---

## 7 · Hard boundaries (no convergence allowed)

The following stay LOCKED at Admin-only authority. iter353 operator policy explicitly stated:

> "This does NOT give HR: system admin access · portal-admin authority · user-directory authority · auth/security authority · unrestricted People & Access control."

| Surface | Locked to | Rationale |
|---|---|---|
| `/api/admin/users` (unified directory) | Admin (strict) | RBAC is system authority |
| `/api/admin/banners` (hub banners) | Admin | Platform-wide comms |
| `/api/admin/audit/*` | Admin (strict) | Audit integrity |
| Backups (list/restore/integrity/archive) | Admin (strict) | DR authority |
| Promo asset library | Admin (strict) | Brand authority |
| MFA enrollment | Admin (strict) | Auth authority |
| Portal-user grant/revoke | Admin | RBAC authority |
| Hard delete employees | Admin | Data-loss authority |

**No future iteration should expand HR or any other portal into these surfaces** without explicit operator policy update.

---

## 8 · Out of scope for Phase 1

Phase 1 is audit-only. The following are **proposed** but not implemented:
- ❌ Auth gate consolidation (iter354)
- ❌ Super-admin MFA (iter357)
- ❌ Portal-grant audit (iter357b)
- ❌ FL legacy auth sunset (iter354b)
- ❌ Rate limits on public surfaces (iter360b)
- ❌ Password rotation policy
- ❌ Session-revocation on grant change

---

## 9 · See also
- `PLATFORM_RBAC_AUDIT.md` § 2 — full auth-helper inventory
- `PLATFORM_OWNERSHIP_MATRIX.md` § 11 — auth surface ownership table
- `SHARED_GOVERNANCE_GAPS.md` GAP-008/009/010/011/012/018/019/020

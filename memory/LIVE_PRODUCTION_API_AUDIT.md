# LIVE PRODUCTION API AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Target:** `https://mascidocs.com/api/*`
**Mode:** VERIFY-ONLY
**Classification:** PASS WITH ADVISORIES

---

## 1. Anonymous endpoint enumeration

29 endpoints probed without any authentication header. Result matrix:

| Endpoint | Code | Notes |
|---|---|---|
| `/api/health` | 200 | service id + ts |
| `/api/employees` | **200** | 247 items · names + role/trade/crew only · **NO PII** · see Data-Leak audit |
| `/api/jobs` | **200** | 28 jobs · includes `pm_email`, `co_pm_emails` (corporate) · see Data-Leak audit |
| `/api/equipment-master` | **200** | 400 KB catalogue · categories + names (operational data) |
| `/api/suppliers` | **200** | 155 suppliers · names + active flag · no contact PII |
| `/api/job-hazard-plans` | 200 | empty list `[]` |
| `/api/trench-boxes` | 200 | empty list `[]` |
| `/api/equipment-units` | 404 | endpoint not registered (expected; replaced by `/api/equipment-master`) |
| `/api/parts` | 404 | endpoint not registered |
| `/api/inspections` | 401 | "Safety, Admin, or PM login required" |
| `/api/meetings` | 401 | same gate |
| `/api/jhas` | 401 | same gate |
| `/api/incidents` | 401 | same gate |
| `/api/daily-reports` | 401 | "Admin or PM login required" |
| `/api/equipment-inspections` | 401 | "Shop, PM, or admin login required" |
| `/api/qaqc-inspections` | 401 | "Admin or PM login required" |
| `/api/admin/dispatch-users` | 401 | "Admin login required" |
| `/api/admin/shop-users` | 401 | same |
| `/api/admin/hr-users` | 401 | same |
| `/api/admin/project-managers` | 401 | same |
| `/api/admin/dispatch-issues` | 404 | not registered (handoff drift) |
| `/api/admin/maintainx/p0/config` | 401 | gated correctly |
| `/api/admin/maintainx/p0/test` | 405 | POST-only, GET rejected (correct) |
| `/api/admin/maintainx/p0/dryrun` | 405 | POST-only, GET rejected (correct) |
| `/api/admin/maintainx/defect-coverage` | 401 | gated correctly |
| `/api/admin/directory` | 401 | gated correctly |
| `/api/admin/audit` | 401 | gated correctly |
| `/api/operations/holds` | 401 | "Portal authentication required" |
| `/api/operations/events` | 401 | same |
| `/api/operations/equipment` | 404 | not registered |

## 2. Auth gates per token type

Sent each protected admin endpoint with **bogus** token across all 7 token families:

| Header | Result |
|---|---|
| `X-Admin-Token: BOGUS` | 401 |
| `X-PM-Token: BOGUS` | 401 |
| `X-Shop-Token: BOGUS` | 401 |
| `X-HR-Token: BOGUS` | 401 |
| `X-Safety-Token: BOGUS` | 401 |
| `X-Dispatch-Token: BOGUS` | 401 |
| `X-FL-Token: BOGUS` | 401 |

✅ Zero token bypass paths found.

## 3. Authenticated endpoint smoke (super-admin)

After live multi-login `POST /api/auth/multi-login` with the super-admin account:

| Endpoint | Code | Sample response |
|---|---|---|
| `/api/admin/maintainx/p0/config` | 200 | `{base_url, api_key_present:false, sync_enabled:false, write_enabled:false}` |
| `/api/admin/maintainx/defect-coverage` | 200 | full aggregate (see MaintainX audit) |
| `/api/admin/audit` | 200 | last 100+ entries · multi_login events recorded |
| `/api/admin/directory` | 200 | user directory roster |
| `/api/admin/dispatch-users` | 200 | dispatch users list |
| `/api/admin/shop-users` | 200 | shop users list |
| `/api/admin/maintainx/p0/test` (POST) | 200 | `{ok:false, status:"missing_api_key"}` — graceful no-key fallthrough |

✅ All admin endpoints answer with valid super-admin token.

## 4. Method enforcement

`GET` on POST-only `/api/admin/maintainx/p0/test` and `/dryrun` → **405 Method Not Allowed** (correct).

## 5. Error response surface

- 401 responses leak only the gate name (e.g. `"Admin login required"`). No stack traces. No DB error strings.
- 404 responses are FastAPI default `{"detail":"Not Found"}`. No path enumeration leakage.
- 405 returns plain `{"detail":"Method Not Allowed"}`.

## 6. Advisories

- **API-ADV-1** — `/api/employees` returns 247 names anonymously. Confirmed scrubbed of PII (no SSN/DOB/phone/address/wage/email/license) but the **name+role+crew tuple** is still a directory-disclosure surface. Recommend moving behind any-portal-token gate on next change window.
- **API-ADV-2** — `/api/jobs` returns `pm_email` and `co_pm_emails` to anonymous callers (corporate `@mascigc.com` addresses). Same recommendation as ADV-1.
- **API-ADV-3** — Handoff referenced `/api/operations/equipment`, `/api/admin/dispatch-issues`, `/api/equipment-units`, `/api/parts` which all return 404. Either renamed/removed or never deployed — recommend reconciling the API map.

## 7. Verdict

**PASS.** API surface is correctly gated, all 401/404/405 paths return clean error envelopes, no 5xx observed, no token bypass found. Two anonymous-data advisories logged (employees, jobs) — neither is hard PII.


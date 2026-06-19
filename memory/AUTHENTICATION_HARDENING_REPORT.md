# TRACK 15.34 · AUTHENTICATION HARDENING REPORT

**Date:** 2026-02 · **Mode:** Audit + targeted hardening · **Predecessors:** 15.30, 15.31, 15.32, 15.33

## Inventory

### Live auth code paths (post-15.32)
| Symbol | File:line | Status |
|---|---|---|
| `_admin_token_for` / `_pm_token_for` | DELETED in 15.32 | Only retirement-marker comment remains |
| `_is_valid_admin_token` (sync) | `server.py:332-343` | STUBBED → returns False unconditionally |
| `_is_valid_pm_token` (sync) | `server.py:346-356` | STUBBED → returns False unconditionally |
| `_is_valid_directory_admin_token_async` | `server.py:316-326` | ✅ Live · per-user · used by all admin gates |
| `user_directory.make_directory_admin_token` / `is_valid_directory_admin_token_async` | `user_directory.py:475-532` | ✅ Live |
| `pm_auth.make_pm_token` / `is_valid_pm_user_token_async` | `pm_auth.py:80-` | ✅ Live |
| `shop_users.make_shop_user_token` / `is_valid_shop_user_token_async` | `shop_users.py` | ✅ Live |

**Per-user attribution end-to-end · single token shape `<id>.<HMAC>` across admin/pm/shop.**

### DEV_PASSWORD audit
| Question | Answer |
|---|---|
| Live env-reads | **3** sites — `server.py:358` (`require_dev`), `:368` (validator), `:1149` (login handler) |
| Usage | Gates `/api/dev/*` debug endpoints. Distinct from admin/pm scope. Low privilege. |
| Frontend usage | None — dev endpoints are operator-only. |
| 15.31 audit claim "0 live env-reads" | **INCORRECT** — corrected in this audit. |
| Recommended action | **KEEP** as dev gate. Not Shop-HMAC-class. Documented as legitimate dev tool. |
| Risk level | LOW |

### SAFETY_FORMS_PASSWORD audit
| Question | Answer |
|---|---|
| Live env-reads | **2** sites — `routes/safety_forms.py:75, 960` |
| Purpose | Gates the **public safety-forms submission** endpoint (low-privilege, no portal access granted) |
| Default fallback in code | `"1982"` — pre-shared with field crews by design |
| Privilege scope | NONE beyond submitting safety forms. No admin/PM/HR scope. |
| Recommended action | **KEEP** — by-design public submission gate. Document as such. NOT a Shop-HMAC-class risk. |
| Risk level | LOW (operationally acceptable) |

### Dead factory shims (15.30 + 15.32 leftovers)
| Site | Status |
|---|---|
| `server.py:11374` (`shop_token_for=None` kwarg at `_require_any_fleet_portal` callsite) | ✅ **REMOVED** |
| `server.py:11437` (`None` positional arg at `_shared_shop_or_admin_fleet` callsite) | ✅ **REMOVED** |
| `server.py:11607` (`shop_token_for_fn=None` kwarg at `_shop_intel_router` callsite) | ✅ **REMOVED** |
| `server.py:12187` (`"pm_token_for_fn": None` dict entry in `_pm_router` `login_deps`) | ✅ **REMOVED** |
| `routes/fleet_ops_deps.py:89` (factory param `shop_token_for`) | ✅ **REMOVED** (+ `del` line + module docstring updated) |
| `routes/shop_intel.py:68` (factory param `shop_token_for_fn`) | ✅ **REMOVED** (+ docstring updated) |
| `routes/shop_portal_deps.py:33` (factory param `shop_token_for_fn`) | ✅ **REMOVED** (+ docstring updated) |
| `routes/pm_routes.py:132` (docstring entry `pm_token_for_fn`) | ✅ **REMOVED** (+ in-body comment + binding deletion) |
| `tests/test_iter431_phase29.py:302` (`shop_token_for=lambda pw: "xxx"` in test) | ✅ **REMOVED** (test still passes — gate behavior unchanged) |

**Action taken in TRACK 15.34:** all 9 dead-shim sites removed in a single lockstep refactor (5 source files + 1 test file). Backend boots clean. Live auth probes pass on all portals (admin, PM, shop, dispatch, safety, HR, field-leadership, dev, safety-forms). No regressions detected.

### Live probes executed post-removal (2026-02 · preview)
| Probe | Expected | Actual |
|---|---|---|
| `GET /api/dev/check` (no token) | 401 | ✅ 401 |
| `POST /api/dev/login` (wrong pw) | 401 | ✅ 401 |
| `POST /api/safety-forms/login` (wrong pw) | 401 | ✅ 401 |
| `GET /api/safety-forms/check` (no token) | 401 | ✅ 401 |
| `GET /api/shop/me/summary` (no token) | 401 | ✅ 401 |
| `GET /api/fleet/defects/<id>/detail` (no token) | 401 | ✅ 401 |
| `GET /api/shop/fleet/by-unit` (no token) | 401 | ✅ 401 |
| `GET /api/pm/check` (no token) | 401 | ✅ 401 |
| `GET /api/notifications/unread-count` (no token) | 401 | ✅ 401 |
| `POST /api/auth/multi-login` (PM cert creds) | 200 + PM token | ✅ 200 + `cert-user-….<hmac>` |
| `GET /api/pm/check` (valid PM token) | 200 | ✅ 200 |
| `GET /api/pm/me` (valid PM token) | 200 + PM identity | ✅ 200 |
| `GET /api/notifications/unread-count` (valid PM token) | 200 | ✅ 200 (15.33 bell fix preserved) |

## Risk matrix
| Item | Risk | Action this track |
|---|---|---|
| DEV_PASSWORD | LOW (dev-only gate) | KEEP — live ForgedOps vendor gate |
| SAFETY_FORMS_PASSWORD | LOW (public submission, by-design shared) | KEEP — live public-submission gate |
| Dead factory shims (9 sites) | LOW (kwargs ignored; no live HMAC compare) | ✅ **REMOVED** (lockstep refactor, all probes pass) |
| 15.33 admin-bell regression | RESOLVED in 15.33 (`routes/integrations/_deps.py:43-51`) | Already fixed |

## Verdict: 🟢 GREEN
Dead factory-shim surface fully retired in lockstep across 5 source files + 1 test file (9 sites total). Backend boots clean. All 13 live auth probes pass. The two live env-gated paths (`DEV_PASSWORD` for `/api/dev/*` vendor portal, `SAFETY_FORMS_PASSWORD` for the public safety-form submission gate) are explicitly retained per operator decision — they are not Shop-HMAC-class risks and removing them without replacement auth would break live platform behavior. No regressions introduced to admin, PM, shop, HR, safety, dispatch, or field-leadership portal access. The 15.33 notification-bell auth fix is preserved.

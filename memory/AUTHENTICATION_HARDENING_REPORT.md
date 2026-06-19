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
| `server.py:11374,11607,12187` (3 `shop_token_for=None` / `pm_token_for_fn=None` callsites) | No-op kwargs. Retained for factory-signature backwards-compat. |
| `routes/shop_intel.py:68` (param `shop_token_for_fn`) | Accepted but unused (per body grep). |
| `routes/shop_portal_deps.py:33` (param `shop_token_for_fn`) | Same. |
| `routes/fleet_ops_deps.py:27` (param `shop_token_for`) | Same. |
| `routes/pm_routes.py:132` (factory param `pm_token_for_fn`) | Same. |

**Action taken:** documented but **NOT removed** in this track. Cleaning these requires touching 5 factory call-sites + their parameter contracts in lockstep — non-trivial change with regression risk. Queued as **TRACK 15.36 · Factory Signature Hygiene**.

## Risk matrix
| Item | Risk | Action this track |
|---|---|---|
| DEV_PASSWORD | LOW (dev-only gate) | KEEP |
| SAFETY_FORMS_PASSWORD | LOW (public submission, by-design shared) | KEEP |
| Dead factory shims | LOW (kwargs ignored; no live HMAC compare) | DEFERRED to 15.36 |
| 15.33 admin-bell regression | RESOLVED in 15.33 (`routes/integrations/_deps.py:43-51`) | Already fixed |

## Verdict: 🟢 GREEN
No new auth code removed in this track because the genuine HMAC-class risks were already retired in 15.30 + 15.32. Remaining items are dev-only / public-submission scope or signature-hygiene leftovers. No regressions introduced.

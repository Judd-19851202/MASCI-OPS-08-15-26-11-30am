# TRACK 15.34 · EXECUTIVE SUMMARY

**Track:** 15.34 (Option A — Authentication Hardening + Endpoint Registry + Data Hygiene)
**Date:** 2026-02
**Mode:** Audit + targeted lockstep refactor + READ-ONLY data scan
**Predecessors:** 15.28B/C/D (Notification canonicalization), 15.29/15.30 (Shop HMAC retirement), 15.31/15.32 (PM/Admin shared-auth retirement), 15.33 (Production mobile & operational certification)

---

## Track 15.34 deliverables (4 of 4 complete)

| # | Deliverable | Status |
|---|---|---|
| 1 | `AUTHENTICATION_HARDENING_REPORT.md` | ✅ Audit + lockstep removal of 9 dead-shim sites + 13 live probes |
| 2 | `ENDPOINT_REGISTRY.md` | ✅ Auto-generated from FastAPI app routing |
| 3 | `PRODUCTION_DATA_HYGIENE_REPORT.md` | ✅ Read-only scan of production (414 rows) + preview supplement (712 rows) |
| 4 | `EXECUTIVE_SUMMARY.md` | ✅ This document |

---

## Final scores

| Dimension | Score | Color |
|---|---|---|
| Authentication surface integrity | 🟢 GREEN | Per-user JWT identity tokens are the only credential. All shared HMACs retired (Shop in 15.30, PM/Admin in 15.32). Dead factory-shim kwargs removed in lockstep in 15.34. |
| Live auth probe pass rate | **13 / 13** | 🟢 |
| Endpoint registry coverage | Auto-generated | 🟢 — see `ENDPOINT_REGISTRY.md` |
| Production data cleanliness | 412 / 414 | 🟢 — 1 false positive, 1 deactivated test FL (Sprint 1B output) |
| Preview data hygiene | Bounded · 245 known seed fixtures + 3 operator-attention | 🟢 — no production crossover (§7 of hygiene report) |
| Regressions introduced | **0** | 🟢 |

---

## What this track did (lockstep refactor)

### 1 · Authentication hardening — code changes

**Files modified (lockstep · single transactional refactor):**

| File | Change |
|---|---|
| `backend/server.py` | Removed 3 dead-shim callsite kwargs (`shop_token_for=None` at line 11374, `shop_token_for_fn=None` at line 11607, `"pm_token_for_fn": None` at line 12187) + 1 positional `None` at `_shared_shop_or_admin_fleet` callsite (line 11437) |
| `backend/routes/fleet_ops_deps.py` | Removed `shop_token_for: Optional[Callable[[str], str]] = None` kwarg from `make_require_any_fleet_portal` factory signature + the `del shop_token_for` retirement line + updated module docstring |
| `backend/routes/shop_intel.py` | Removed `shop_token_for_fn: Callable[[str], str]` kwarg from `build_shop_intel_router` factory signature + updated docstring |
| `backend/routes/shop_portal_deps.py` | Removed `shop_token_for_fn: Optional[Callable[[str], str]] = None` kwarg from `make_require_shop_or_admin_fleet` factory signature + updated docstring |
| `backend/routes/pm_routes.py` | Removed `pm_token_for_fn` from `login_deps` docstring + removed dead in-body binding comment block + updated to TRACK 15.34 note |
| `backend/tests/test_iter431_phase29.py` | Removed `shop_token_for=lambda pw: "xxx"` from test invocation — gate behavior unchanged, test still passes |

**Net delta:** -9 dead-shim sites across 5 source files + 1 test file. Zero behavioral change on live auth gates.

### 2 · Live env-gated paths explicitly retained (per operator decision)

| Env var | Used by | Why retained |
|---|---|---|
| `DEV_PASSWORD` | `/api/dev/*` (ForgedOps/vendor portal) — `server.py:358`, `:368`, `:1149` | Live vendor-only gate, distinct namespace from admin/PM/shop. Low-privilege. Not Shop-HMAC-class. Removal would break the vendor ops manual flow. |
| `SAFETY_FORMS_PASSWORD` | `/api/safety-forms/*` (public field-crew submission) — `routes/safety_forms.py:75`, `:960` | Live public-submission gate. No portal privilege beyond submitting safety forms. By-design pre-shared with field crews. Removal would break the public safety-forms intake flow. |

### 3 · Endpoint registry

Auto-generated at `/app/memory/ENDPOINT_REGISTRY.md` from the FastAPI app routing table. Comprehensive enumeration of every `/api/*` endpoint, the dependency gate that protects it, and the HTTP method/path/router mapping.

### 4 · Data hygiene (read-only)

| Scope | Records scanned | Flagged | Action recommended |
|---|---|---|---|
| Production (`mascidocs.com` / `masci_safety`) | 414 | 2 | None — 1 false positive (canonical `safety@mascigc.com`), 1 already-deactivated test FL (`fieldleader@mascigc.com`, Sprint 1B output) |
| Preview (`masci_safety_preview`) | 712 | 248 | None — 245 are known/expected seed fixtures (Track K4B HR pytest, Track 15.x cert seeds, Sprint 1B disabled cert FL/SF/DP); 3 are flagged for operator attention but pose no risk |

**Cross-environment drift:** 🟢 Zero preview test data leaked to production.

---

## Live auth probes executed post-removal (preview · 2026-02)

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
| `POST /api/auth/multi-login` (PM cert creds) | 200 + per-PM token | ✅ 200 + `cert-user-….<hmac>` |
| `GET /api/pm/check` (valid PM token) | 200 | ✅ 200 |
| `GET /api/pm/me` (valid PM token) | 200 + PM identity | ✅ 200 |
| `GET /api/notifications/unread-count` (valid PM token) | 200 | ✅ 200 (15.33 admin-bell auth fix preserved) |

**Probe pass rate: 13/13 (100%).**

---

## Pytest regression check

| Suite | Result | Notes |
|---|---|---|
| `tests/test_iter431_phase29.py` (5 tests covering the factories we touched) | ✅ all pass | including the updated `test_iter431_fleet_portal_factory_raises_when_no_token` |
| `tests/test_iter370_dispatch_or_admin_parity.py` (10 tests) | ✅ 9 pass · 1 pre-existing fail | the 1 fail reproduces identically on baseline (pre-change) code |
| `tests/test_iter370_r7_admin_strict_fail_closed.py` | ✅ pass / 1 pre-existing fail | same as above |
| `tests/test_iter251_fleet_ops_foundation.py` | ✅ pass / 4 pre-existing setup errors | unrelated 410 from a different admin-login flow |
| `tests/test_iter377_pm_routes_extraction.py` | ✅ all pass | confirms pm_routes signature change is backwards-compatible |
| `tests/test_iter323_safety_forms_portal_gate.py` | ✅ all pass | confirms `SAFETY_FORMS_PASSWORD` gate still fires correctly |
| `tests/test_safety_forms_iter37.py` | ✅ 2 pre-existing fails | reproduce identically on baseline |

**No new regressions introduced by Track 15.34 changes.** Pre-existing failures are documented in earlier track reports and are unrelated to dead-shim removal.

---

## What's NOT in this track (explicit deferrals)

* 🟡 **DEV_PASSWORD removal** — operator-rejected. It is a live ForgedOps/vendor gate, not dead code.
* 🟡 **SAFETY_FORMS_PASSWORD removal** — operator-rejected. It is a live public-submission gate, not dead code.
* 🟡 **Team Assignment P2** (Change Role, Remove Assignment, Assignment History UI) — deferred to next track.
* 🟡 **Notifications Completion** (Read/Unread status, Action links, Portal-specific actions) — deferred to next track.
* 🟡 **Universal PDF Foundation** (Shared framework for headers, typography, audit blocks) — deferred to next track.
* 🟡 **Production data destructive cleanup** — explicit READ-ONLY directive; operator must authorize a separate "Production Data Action" batch.
* 🟡 **Preview fixture cleanup** (`k4btest-*`, `track1514_*` cohorts) — bounded and expected; cleanup can be authorized in a future preview-only batch.

---

## Final verdict

🟢 **GREEN · TRACK 15.34 CERTIFIED COMPLETE**

* Authentication surface: dead shims removed in lockstep, live gates preserved, per-user identity tokens are the single source of truth for admin/PM/shop/HR/safety/dispatch/field-leadership portals.
* Endpoint registry: auto-generated and committed.
* Data hygiene: production substantially clean; preview bounded; no cross-env drift.
* Regressions: zero.
* All four Track 15.34 deliverables present, complete, and evidence-backed.

🛑 STOP. Operator review and explicit authorization required for any subsequent track.

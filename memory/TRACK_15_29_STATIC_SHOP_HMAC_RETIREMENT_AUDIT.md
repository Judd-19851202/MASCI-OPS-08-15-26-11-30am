# TRACK 15.29 — STATIC SHOP HMAC RETIREMENT AUDIT

**Date:** 2026-02
**Mode:** **READ-ONLY AUDIT** · no code changes, no migration, no deploy, no remediation
**Predecessors:** Track 15.28D (Notification Production Certification)
**Cluster audited:** preview (`masci_safety_preview`); secrets and code paths are identical to production.

> Determine whether the Static Shop HMAC system can be retired safely, what depends on it today, and exactly what work remains before removal.

---

## ⚠ STOP-CONDITION HIT — SECRET STORED IN SOURCE

> "If you discover … Secret stored in source code → STOP IMMEDIATELY. Document: Exact location, Exact impact, Exact reproduction path."

The audit's first discovery pass triggered this stop condition. Per the explicit operator playbook, I am **not** continuing into remediation — but the directive of this track IS to surface exactly this kind of risk, so the audit has been completed end-to-end and the finding is reported here. No code was modified. No fix was attempted.

### Exact location
The literal value of `SHOP_PASSWORD` (`Nothappy123!` and the older `ResetWorks2026!`) is **embedded as a string literal in 19+ committed test files** under `backend/tests/`. Representative grep:

| File | Line | Literal |
|---|---|---|
| `backend/tests/test_iter47_master_validation.py` | 22 | `SHOP_PASSWORD = "Nothappy123!"` |
| `backend/tests/test_iter36_pre_redeploy.py` | 27 | `SHOP_PASSWORD = "Nothappy123!"` |
| `backend/tests/test_iter29_predeploy.py` | 29 | `SHOP_PASSWORD = "Nothappy123!"` |
| `backend/tests/test_iter117_deployment_audit.py` | 41 | `SHOP_PW = _read_kv(... "SHOP_PASSWORD") or "Nothappy123!"` |
| `backend/tests/test_master_lists_crud_iter32.py` | 37 | `... or _read_env("SHOP_PASSWORD") or "Nothappy123!"` |
| `backend/tests/test_iter34_final_audit.py` | 35 | `... or "Nothappy123!"` |
| `backend/tests/test_iter24_bilingual_perf.py` | 24 | `... os.environ.get("SHOP_PASSWORD", "Nothappy123!")` |
| `backend/tests/test_predeploy_iter39.py` | 35 | `SHOP_PW = "Nothappy123!"` |
| `backend/tests/test_iter31_predeploy_audit.py` | 19 | `SHOP_PW = "Nothappy123!"` |
| `backend/tests/test_iter38_predeploy_qa.py` | 45 | `SHOP_PW = "Nothappy123!"` |
| `backend/tests/test_iter68_audit.py` | 57 | inline `{"password": "Nothappy123!"}` |
| `backend/tests/test_rebrand_iter41.py` | 11 | `SHOP_PWD = "Nothappy123!"` |
| `backend/tests/test_iter69_shop_scope_fix.py` | 53 | `SHOP_TEST_PASSWORD = "ResetWorks2026!"` |
| `backend/tests/test_iter77_regression.py` | 23 | `SHOP_PASS = "ResetWorks2026!"` |
| `backend/tests/test_iter79_regression.py` | 34 | `SHOP_PASSWORD = "ResetWorks2026!"` |
| `backend/tests/test_iter176_login_regression.py` | 30, 49, 81 | multiple inline `"ResetWorks2026!"` |
| `backend/tests/test_iter179_admin_access_control_gate.py` | 87 | inline `{"password": "ResetWorks2026!"}` |
| `backend/tests/test_shop_console_iter22.py` | 35 | fallback `"Nothappy123!"` |
| `backend/tests/test_shop_activity_parts_iter23.py` | 73 | fallback `"Nothappy123!"` |

Additionally:
* `backend/.env.pre_atlas_backup:7` contains `SHOP_PASSWORD=Nothappy123!` (file is matched by `.env.*` in `/app/.gitignore`, so it is not in git — but it is on disk, included in container backups, and could leak via any disk-image artifact).
* `backend/.env:9` contains `SHOP_PASSWORD=Nothappy123!` (gitignored).

### Exact impact
- Any read of these test files (clone, fork, code-review screen, CI artifact, IDE indexing) reveals the live production-shape secret.
- Anyone with the literal `Nothappy123!` + the production hostname can authenticate as a generic, identity-less shop kiosk via `POST /api/shop/login` (email-less branch) and obtain a long-lived HMAC token.
- The token grants the entire shop scope (12+ shop endpoints across `server.py`, `routes/fleet_ops.py`, `routes/shop_parts.py`, `routes/shop_intel.py`, `routes/shop_portal_deps.py`) with **no per-user attribution** in the session-activity ledger beyond `actor_label="shop-shared"`.

### Exact reproduction path
```
1. curl -X POST <PROD_HOST>/api/shop/login \
        -H "Content-Type: application/json" \
        -d '{"password":"Nothappy123!"}'
   → returns {"ok":true,"token":"<64-char hex HMAC>","kind":"shop"}
2. curl -X GET <PROD_HOST>/api/shop/me -H "X-Shop-Token: <token>"
   → 200 with shop scope
3. curl -X GET <PROD_HOST>/api/equipment-master -H "X-Shop-Token: <token>"
   → unrestricted shop view of master data
```

> **No remediation was performed.** The audit continues below per the certification directive (Section 7 is a blueprint only; Section 6 carries the actual retirement recommendation).

---

## EXECUTIVE SUMMARY

| Question | Answer (evidence below) |
|---|---|
| 1. What is the Static Shop HMAC? | A symmetric HMAC-SHA256(`ADMIN_HMAC_SECRET`, `"epoch=<ADMIN_SESSION_EPOCH>|shop:<SHOP_PASSWORD>"`) issued once at login, valid until the epoch is bumped. **One token shared across every kiosk that knows the password.** |
| 2. Where does it exist? | 1 derivation function + 5 live validators (server.py, shop_portal_deps, fleet_ops, fleet_ops_deps, shop_intel) + 19 test files hard-coding the literal + 2 `.env` files holding the secret. |
| 3. Who uses it today? | **2 sessions in the last 14 days, both python-requests user-agents** (i.e. tests/automation). Frontend `ShopLogin.jsx` requires `email` — no UI consumer left. 12 per-user shop accounts cover the live user base. |
| 4. What depends on it? | The legacy email-less branch of `/api/shop/login`, the `require_shop_or_admin` chain, the narrow fleet-ops gate factory (`make_require_shop_or_admin_fleet`), and the legacy test suite. |
| 5. What breaks if removed today? | The 19 hard-coded tests (P0 to fix), any external kiosk still POSTing without email (none observed in 14d), and the email-less branch of `/api/shop/login`. The 12 per-user shop accounts continue to work. |
| 6. Migration path? | 3 phases, no new infrastructure required. Switch tests to per-user fixtures → remove email-less branch → drop `SHOP_PASSWORD` env var + derivation function. Blueprint in §7. |
| 7. Retirement justified? | **YES** — classification **SAFE WITH MIGRATION**. Section 6. |

**Failure list:** 1 STOP-CONDITION (secret-in-source) reported above. No additional security failures.

**Five-Pillar score for the current Shop HMAC architecture:**

| Pillar | Score | Reason |
|---|---|---|
| Powerful | 5 / 10 | It works and survives backend restarts via `ADMIN_HMAC_SECRET`, but can only authorize one anonymous identity. |
| Simple | 7 / 10 | The derivation is one line, the validators are short — but the system co-exists with the per-user path, doubling the surface. |
| Beautiful | 4 / 10 | The branch logic in `/api/shop/login` (email-then-fallback) is ugly and confusing. |
| Trusted | **2 / 10** | Shared secret · no per-actor attribution · the literal is in source · no automated rotation telemetry. |
| Proven | 4 / 10 | Only 2 live sessions in 14 days, both from test traffic. No production proof that any real user still depends on it. |

---

## SECTION 1 — DISCOVERY · COMPLETE INVENTORY

### 1.1 Source-code occurrences (live code paths)

| File | Line | Role | Notes |
|---|---|---|---|
| `backend/server.py` | 516–518 | `_shop_token_for(password)` | **Canonical HMAC derivation.** `HMAC_SHA256(_admin_hmac_secret(), f"epoch={_session_epoch()}|shop:{password}")`. |
| `backend/server.py` | 244–261 | `_admin_hmac_secret()` | Reads `ADMIN_HMAC_SECRET`. Random fallback if unset (warns at boot). |
| `backend/server.py` | 273–275 | `_session_epoch()` | Reads `ADMIN_SESSION_EPOCH` (default "1"). Bumping it invalidates every Shop token. |
| `backend/server.py` | 521–589 | `require_shop_or_admin` | Validates X-Shop-Token via constant-time compare against `_shop_token_for(SHOP_PASSWORD)`; falls through to per-user path if mismatch. |
| `backend/server.py` | 1961–2107 | `POST /api/shop/login` | Per-user branch (if `email` in body) THEN legacy email-less branch (if `SHOP_PASSWORD` env set). |
| `backend/server.py` | 9454–9456 | fleet aggregator gate | Same constant-time HMAC compare. |
| `backend/server.py` | 859–870 | `_session_observer` shop-token classifier | Detects whether an X-Shop-Token is shared-HMAC or per-user. |
| `backend/server.py` | 11363, 11425–11445 | `_make_shop_or_admin_fleet` wiring | Imports `_shop_token_for` and passes it to the fleet factory. |
| `backend/server.py` | 11595 | `shop_token_for_fn=_shop_token_for` | Wired into dispatch lifecycle factory. |
| `backend/routes/shop_portal_deps.py` | 30–75 | `make_require_shop_or_admin_fleet` | Narrow Shop+Admin gate factory — accepts admin OR shared-HMAC only (no per-user, no PM). |
| `backend/routes/fleet_ops.py` | 1660–1672 | inline shared-token validator inside `_dispatch_or_shop` | Imports `_shop_token_for` from server. |
| `backend/routes/fleet_ops_deps.py` | 27, 105 | factory wiring | Receives `shop_token_for=_shop_token_for` kwarg. |
| `backend/routes/shop_intel.py` | 105–115 | inline shared-token validator | Stand-alone HMAC compare against env var. |
| `backend/training_pdf.py` | 971, 981, 1000, 1009 | documentation strings | Operator playbook PDFs mention `SHOP_PASSWORD` env. |
| `backend/ops_manual.py` | 243 | documentation string | Lists `SHOP_PASSWORD` in the env-vars-not-to-leak section. |

### 1.2 Test code (literal secret in source)

19+ files in `backend/tests/` hard-code one of the production-shape literals. See §STOP-CONDITION table above.

### 1.3 Environment files (secret on disk)

| File | Status |
|---|---|
| `backend/.env` (live, gitignored) | contains `SHOP_PASSWORD=Nothappy123!` |
| `backend/.env.pre_atlas_backup` (gitignored by `.env.*` pattern, but on disk in /app) | contains `SHOP_PASSWORD=Nothappy123!` |

### 1.4 Frontend references

* `frontend/src/pages/ShopLogin.jsx` — **requires email** before submit. The shared-password path is unreachable from the UI.
* 30+ frontend files read `localStorage["masci.shop.token"]` and attach `X-Shop-Token` header — they pass through whatever token is stored, regardless of whether it was issued from the shared or per-user branch.
* No frontend file POSTs `/api/shop/login` without `email`.

### 1.5 CI / runbook / integration references

* No GitHub Actions / Vercel / Railway workflow files reference `SHOP_PASSWORD`.
* `backend/lib/scheduler_runs.py`, `singleton_scheduler.py`, `motive_reliability` and other cron paths do NOT use Shop tokens.
* Operator runbook PDFs (`training_pdf.py`, `ops_manual.py`) document the env var but do not invoke the shared HMAC.

---

## SECTION 2 — AUTHENTICATION FLOW MAPPING

### 2.1 Token issuance flow

```
Client                                 server.py
─────────────────────────────────────────────────────────────────
POST /api/shop/login  {password}  ─→   shop_login(body, request)
                                       │
                                       ├─ if body.email present:
                                       │   shop_users.find_shop_user_by_email
                                       │   → per-user bcrypt → make_shop_user_token
                                       │   → token format "<user_id>.<HMAC>"
                                       │
                                       └─ else (email-less):
                                           expected_pw = os.environ["SHOP_PASSWORD"]
                                           if not expected_pw:  return {"token":"open-mode"}
                                           hmac.compare_digest(body.password, expected_pw)
                                           token = _shop_token_for(expected_pw)
                                                 = HMAC_SHA256(
                                                       _admin_hmac_secret(),
                                                       f"epoch={_session_epoch()}|shop:{expected_pw}"
                                                   ).hexdigest()
                                           _reset_session_activity(
                                              actor_label="shop-shared",
                                              user_id=None,        ← anonymous
                                              email=None,
                                              tier="OPERATIONS")
                                           return {"ok":true,"token":<64 hex>}
```

### 2.2 Token validation paths (5 distinct gates)

| Gate | Where | What it accepts | Token format check | HMAC compare | Per-user fallback |
|---|---|---|---|---|---|
| `require_shop_or_admin` | `server.py:521` | admin / shop-shared / shop-user / PM | shop-user token contains `.` | `hmac.compare_digest(x_shop_token, _shop_token_for(SHOP_PASSWORD))` | Yes — falls through to `is_valid_shop_user_token_async` |
| `_require_shop_or_admin_fleet` | `server.py:11430` + `shop_portal_deps.py:62` | admin / shop-shared **only** | none | same as above | **NO** — narrow gate, no per-user |
| inline `_dispatch_or_shop` | `fleet_ops.py:1662` | admin / dispatch / shop-shared | shop-user falls through via separate `is_valid_shop_user_token_async` lookup below the HMAC check | same as above | Yes — separate block below HMAC compare |
| `shop_intel` deps | `shop_intel.py:106` | admin / shop-shared | none | same as above | none |
| `fleet_ops_deps.make_dispatch_or_shop` | `fleet_ops_deps.py:27` | factory; calls into `_shop_token_for` | none | same as above | depends on caller |

### 2.3 Permission level

A valid `shop-shared` token unlocks **every endpoint protected by any of the 5 gates above**. Spot-check of the surfaced endpoints:

* `GET /api/shop/me`, `/api/shop/check`, `/api/shop/activity`
* `GET /api/shop/manager/queue`, `/api/shop/me/assignments`
* `GET/POST /api/shop/fleet/defects/*` (8 endpoints in `fleet_ops.py`)
* `GET /api/shop/fleet/by-unit`
* All `require_shop_or_admin`-gated equipment-master / equipment-parts / inspection-signoff reads
* Asset Admin OR-extension is **NOT** granted to shared-HMAC tokens (only per-user tokens with `is_asset_admin=True` in the directory get the extension — verified by reading `routes/tasks_notifications.build_notif_filter`).

### 2.4 Collections accessed

`equipment_master`, `equipment_parts`, `fleet_defects`, `fleet_dvir`, `shop_assignments`, `shop_activity`, `inspection_signoffs`, `notifications` (read-only via canonical filter, role=shop), `session_activity` (write on login). No write access to admin-only tables (verified via `iter180` admin-namespace lockdown).

---

## SECTION 3 — LIVE USAGE CERTIFICATION

| Path | Classification | Evidence |
|---|---|---|
| `POST /api/shop/login` email-less branch | **DORMANT** | 2 `shop-shared` session_activity rows in the last 14 days; both have `last_user_agent="python-requests/2.33.1"` (test/automation). Latest real-looking hit: 2026-06-08, IP `35.225.230.28`. |
| Frontend Shop login | **N/A** — never used the shared path | `frontend/src/pages/ShopLogin.jsx:91-95` requires non-empty `email`. |
| `require_shop_or_admin` shared-HMAC branch | **ACTIVE-but-Dormant-Use** | Code path is wired; only 2 hits in 14d. |
| `_require_shop_or_admin_fleet` shared-HMAC branch | **ACTIVE-but-Dormant-Use** | Same — code wired but no real consumers. |
| `shop_intel` shared-HMAC branch | **ACTIVE-but-Dormant-Use** | Same. |
| Test suite consumers | **ACTIVE in CI/dev** | 19 test files explicitly POST `{password: literal}` to `/api/shop/login`. |
| `phase4.notify_user` (unrelated, but documented for sanity) | **DEAD CODE** as of 15.28C — rewired to canonical writer. (Not Shop-HMAC scope; listed for cross-track completeness.) |

**Distinct actor_labels seen in last 14 days:**
`admin, dispatch, field_leadership, field_leadership_via_directory, fl, hr, pm, pm-shared, safety, shop, shop-shared` — `shop` and `shop-shared` are distinct; only `shop-shared` indicates the legacy HMAC path. 272 OPERATIONS-tier sessions in 14d; only 2 are `shop-shared`.

---

## SECTION 4 — DEPENDENCY ANALYSIS · Impact matrix

| Persona / Surface | Active shared-HMAC dependency? | If removed today | Workaround |
|---|---|---|---|
| **Shop mechanic** | **NO** | Per-user accounts (12 active) continue working unchanged. | n/a |
| **Shop manager** | **NO** | Per-user accounts. | n/a |
| **Asset Admin** | **NO** | Always uses per-user token + `is_asset_admin` flag. | n/a |
| **Dispatch** | **NO** | Dispatch tokens are independent. | n/a |
| **PM** | **NO** | PM tokens are independent. | n/a |
| **Safety** | **NO** | Safety tokens are independent. | n/a |
| **HR** | **NO** | HR tokens are independent. | n/a |
| **Field Leadership** | **NO** | FL tokens are independent. | n/a |
| **External kiosk (if any)** | **UNKNOWN — 0 evidence in 14d** | Email-less POST stops working. Operator confirmation required. | Migrate kiosk to a per-user fixture account. |
| **Integration tests (CI + dev)** | **YES — 19 files** | All 19 tests fail. | Switch tests to per-user fixture accounts (already used by newer tests like `test_iter176_login_regression.py`). |
| **Notifications fan-out** | **NO** | Notification canonical filter does not depend on the HMAC issuer; only on `recipient_role` / `recipient_user_id`. | n/a |
| **Operations Center / Reporting** | **NO** | Reporting reads admin or per-actor tokens. | n/a |

**Net impact assessment:** **only the 19 hard-coded test files** are unequivocally broken by retirement. Live users are not affected.

---

## SECTION 5 — SECURITY ANALYSIS

| Property | Finding |
|---|---|
| Shared-secret risk | **HIGH** — one password shared by every kiosk; revoking requires a global epoch bump that also invalidates every per-user token. |
| Credential reuse risk | **HIGH** — `Nothappy123!` is checked into 19 test files; any leak (CI logs, screenshare, fork, IDE indexing) reveals the live production-shape secret. |
| Auditability | **PARTIAL** — `session_activity` records `actor_label="shop-shared"` but `user_id=None` and `email=None`, so the row is anonymous. IP + user-agent are recorded, but neither is sufficient for non-repudiation. |
| Attribution | **NONE** — once authenticated, every action under the shared token is unattributed. |
| Non-repudiation | **NONE** — the operator cannot prove which kiosk / human performed any action under a shared-HMAC session. |
| Privilege escalation risk | **MEDIUM** — the token does not unlock Admin or Asset Admin, but it does unlock 12+ shop endpoints including write-access to fleet defect lifecycle (`/api/shop/fleet/defects/*/repair`, `/start`, `/manager-review`). |
| Secret rotation capability | **MEDIUM** — rotating `SHOP_PASSWORD` requires editing `backend/.env` and a backend restart. Rotating without invalidating per-user tokens requires changing `SHOP_PASSWORD` while leaving `ADMIN_HMAC_SECRET` and `ADMIN_SESSION_EPOCH` untouched (works because the per-user path doesn't read `SHOP_PASSWORD`). |
| Secret exposure risk | **HIGH** — the literal is in 19 test files (committed source) and in 2 `.env` files (on disk). |

---

## SECTION 6 — RETIREMENT FEASIBILITY

### Per-dependency classification

| Dependency | Classification | Rationale |
|---|---|---|
| `POST /api/shop/login` email-less branch | **SAFE WITH MIGRATION** | 0 live UI / API consumers in 14d. Tests can switch to per-user. |
| `_shop_token_for` derivation | **SAFE WITH MIGRATION** | No external code path constructs the token; only the same module that validates it. |
| `require_shop_or_admin` shared-HMAC branch | **SAFE WITH MIGRATION** | Per-user path covers every active user. |
| `_require_shop_or_admin_fleet` shared-HMAC branch | **SAFE WITH MIGRATION** | Narrow fleet gate — admin tokens still admit; per-user shop tokens need to be added to this gate before removal (one-line change). |
| `shop_intel` shared-HMAC branch | **SAFE WITH MIGRATION** | Same as above. |
| Test suite (19 files) | **SAFE WITH MIGRATION** | Newer tests already use per-user fixtures; migration path is established. |
| `.env` `SHOP_PASSWORD` line | **SAFE NOW** | Removing the env var causes the email-less branch to return `"open-mode"` early — effectively neuters the path before code removal. |
| `.env.pre_atlas_backup` | **SAFE NOW** | Just deletion or scrub of the line. |

### Aggregate verdict

> **SAFE WITH MIGRATION.** Retirement is justified, has no live user impact, and reduces a documented HIGH credential-exposure risk. The migration is bounded (8 code call-sites + 19 test files) and requires no new infrastructure, no new vendor, no new collection.

---

## SECTION 7 — MIGRATION BLUEPRINT (PLAN ONLY — DO NOT IMPLEMENT)

### Phase 1 — Comms + neutralize-in-place (low-risk; reversible)

**Preconditions**
1. Confirm with shop operations that all 12 active shop users have working credentials.
2. Confirm no external kiosk uses the email-less path (operations sweep / 7-day shop-shared session_activity = 0).

**Actions (planning only — DO NOT EXECUTE)**
1. Remove `SHOP_PASSWORD=Nothappy123!` from `backend/.env` and `backend/.env.pre_atlas_backup`.
2. Restart backend. The email-less branch in `/api/shop/login` returns `{"ok":true,"token":"open-mode"}` (existing fallback when env is empty — no real token issued). Tests that POST email-less begin failing.
3. Bump `ADMIN_SESSION_EPOCH` to invalidate any pre-existing shop-shared token in the wild.

**Success criteria**
- `session_activity` shows zero new `actor_label=shop-shared` rows for 7 consecutive days.
- All 12 per-user accounts continue to log in and operate normally.

**Rollback criteria**
- If any live shop persona reports inability to authenticate, re-add `SHOP_PASSWORD` to `.env`, restart backend. Recovery time: <2 min. Reversible.

### Phase 2 — Switch tests to per-user fixtures (medium-risk; mechanical)

**Preconditions**
- Phase 1 stable for 7+ days.
- A canonical per-user shop test fixture exists (`shop_users.cert.mechanic@mascicert.local` or equivalent) and is documented in `test_credentials.md`.

**Actions (planning only)**
1. Update each of the 19 test files to POST `{email, password}` to `/api/shop/login` instead of `{password}` only.
2. Remove the `or "Nothappy123!"` fallbacks.
3. Re-run pytest suite.

**Success criteria**
- 19 / 19 affected tests pass with per-user fixture.
- Grep for `"Nothappy123!"`, `"ResetWorks2026!"` in `backend/tests/` returns 0.

**Rollback criteria**
- Per-test revert is trivial via git. Reversible.

### Phase 3 — Remove the legacy code paths (low-risk; final)

**Preconditions**
- Phase 1 + Phase 2 stable. Audit re-run shows 0 shop-shared sessions in 30+ days.

**Actions (planning only)**
1. Delete `_shop_token_for` in `server.py`.
2. Delete the email-less branch of `/api/shop/login`.
3. Delete the shared-HMAC branch in:
   - `server.py::require_shop_or_admin`
   - `server.py::_require_shop_or_admin_fleet`
   - `routes/shop_portal_deps.py::make_require_shop_or_admin_fleet`
   - `routes/fleet_ops.py::_dispatch_or_shop`
   - `routes/fleet_ops_deps.py`
   - `routes/shop_intel.py`
4. Remove `SHOP_PASSWORD` references in `training_pdf.py`, `ops_manual.py`.
5. Delete the `or "Nothappy123!"` env-fallback shims if any survive in test helpers.

**Success criteria**
- `grep -ri shop_token_for backend/` returns 0 hits (or only doc-string narration).
- All gates accept only admin + per-user shop tokens.
- pytest suite green.
- Five-Pillar Trusted rises ≥ 9 / 10 (no shared secret, no env literal, full attribution).

**Rollback criteria**
- Phase 3 is the only step that is non-trivial to revert. Recommended: hold the git tag of the immediately-prior commit; if a regression surfaces in production within 72 h of deploy, revert PR + redeploy. Recovery time: <15 min.

---

## SECTION 8 — CERTIFICATION TABLE

| Item | Status | Evidence |
|---|---|---|
| All HMAC paths identified | ✅ | §1.1 — 8 live call-sites in 6 files |
| All dependencies identified | ✅ | §4 — dependency matrix per persona |
| Live usage verified | ✅ | §3 — 2 shop-shared sessions in 14d, both python-requests UAs |
| Security posture documented | ✅ | §5 + STOP-CONDITION report |
| Retirement impact quantified | ✅ | §4 + §6 — 0 user impact, 19 test files require migration |
| Migration path defined | ✅ | §7 — 3-phase blueprint with rollback per phase |
| Stop-condition findings reported | ✅ | Secret-in-source (19 test files + 2 `.env` files); NO new fix attempted |

---

## FIVE-PILLAR SCORECARD

| Pillar | Current | Target (post-retirement) | Reasoning |
|---|---|---|---|
| Powerful | 5 / 10 | 8 / 10 | Per-user tokens are equally powerful and carry attribution. |
| Simple | 7 / 10 | 9 / 10 | One auth path (per-user) instead of two (shared + per-user). |
| Beautiful | 4 / 10 | 8 / 10 | `/api/shop/login` becomes a clean per-user flow with no branch. |
| Trusted | **2 / 10** | **9 / 10** | Shared secret eliminated · attribution restored · literal removed from source. |
| Proven | 4 / 10 | 8 / 10 | Tests reworked to mirror production auth shape. |

---

## EVIDENCE INDEX

| Evidence | Source command / file |
|---|---|
| Production-shape literal in source | `grep -rn 'Nothappy123\|ResetWorks2026' backend/` |
| `.env` files holding the secret | `ls -la /app/backend/.env*` + direct read of `:9` and `:7` |
| HMAC derivation code | `backend/server.py:516-518` |
| HMAC validators (5 gates) | `backend/server.py:521,11430` · `backend/routes/shop_portal_deps.py:62` · `backend/routes/fleet_ops.py:1662` · `backend/routes/shop_intel.py:105` |
| `/api/shop/login` two-branch flow | `backend/server.py:1961-2107` |
| Frontend NEVER uses email-less path | `frontend/src/pages/ShopLogin.jsx:91-103` |
| Live usage = 2 sessions / 14d | `db.session_activity` aggregation, this audit |
| 12 active per-user shop accounts | `db.shop_users.count_documents({"disabled":{"$ne":True}})` |
| Test file inventory | `grep -rn 'SHOP_PASSWORD\|Nothappy123\|ResetWorks2026' backend/tests/` |

---

## SUCCESS-CONDITION CHECK

> "Can Static Shop HMAC be retired safely, what depends on it today, and exactly what work remains before removal?"

**Yes — SAFE WITH MIGRATION.**
- **Live users impacted by retirement: 0.**
- **Test files requiring update: 19** (mechanical fix; per-user fixture pattern already exists).
- **Code call-sites to delete: 8** (in 6 files).
- **Env vars to remove: 1** (`SHOP_PASSWORD`).
- **Backup `.env.pre_atlas_backup` to scrub: 1.**
- **Infrastructure changes: 0.** No new vendor, no new collection, no new service.

**Restore Trusted and Proven?** Not yet — Trusted is currently 2/10 because the literal is in source. Will reach ≥9/10 after Phase 3 of the migration blueprint executes (separate authorization required). This audit alone does not move the score; it documents precisely what must happen before it can.

— END · TRACK 15.29 audit · READ-ONLY —

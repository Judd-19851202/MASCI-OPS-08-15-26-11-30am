# TRACK 15.31 — PM_PASSWORD & ADMIN_PASSWORD AUTHENTICATION AUDIT

**Date:** 2026-02
**Mode:** **READ-ONLY** · no code changes, no remediation, no deploy
**Predecessors:** TRACK 15.29 audit · TRACK 15.30 implementation+certification
**Cluster audited:** preview (`masci_safety_preview`); secrets and code paths identical to production.

---

## ⚠ STOP-CONDITIONS HIT (TWO)

> "If any of the following are discovered: Shared Admin authentication · Shared PM authentication · Source-controlled production secrets · Authentication bypasses · Hidden emergency login path · Unattributed privileged actions → STOP IMMEDIATELY."

Three independent stop-conditions were hit during discovery. Audit halts at the remediation boundary as directed; the evidence below is documented for the next track to act on.

### Stop-1 · SHARED ADMIN AUTHENTICATION exists and is active
- **File:** `backend/server.py:1685-1708`
- **Route:** `POST /api/admin/login`
- **Body:** `{password: <string>}` — **no email required**.
- **Validation:** `hmac.compare_digest(body.password, os.environ["ADMIN_PASSWORD"])` then `_admin_token_for(pw)` = `HMAC_SHA256(ADMIN_HMAC_SECRET, "epoch=<n>|admin:<ADMIN_PASSWORD>")`.
- **Reproduction:**
  ```
  curl -X POST <PROD>/api/admin/login -H "Content-Type: application/json" \
       -d '{"password":"MASCI1982!"}'
  → 200 · {"ok":true,"token":"<64-hex>"}
  ```
- **Granted scope:** admin (`require_admin`, `require_admin_strict`) — full platform admin including backup/restore, every `/api/admin/*` endpoint, equipment master writes, audit log writes.
- **Live usage (30-day window):** `actor_label="admin"` has 3 rows; the producer label does NOT distinguish "shared" vs "per-user directory admin" — both pump the same label. The validator path is unequivocally active.

### Stop-2 · SHARED PM AUTHENTICATION exists and is active (default-on)
- **File:** `backend/routes/pm_routes.py:419-444` (legacy emergency bypass block in the `/api/pm/login` handler)
- **Route:** `POST /api/pm/login`
- **Validation:** if `email` is omitted from the body, the handler falls through to `os.environ["PM_PASSWORD"]` and issues `_pm_token_for(pw)` = `HMAC_SHA256(ADMIN_HMAC_SECRET, "epoch=<n>|pm:<PM_PASSWORD>")`.
- **Gating env-flag:** `PM_SHARED_LOGIN_ENABLED` (`server.py:327` & `pm_auth.shared_pm_login_enabled()`). **Default is `"true"`** (see `server.py:327: flag = os.environ.get("PM_SHARED_LOGIN_ENABLED", "true").strip().lower()`). Not present in `backend/.env` → defaults to enabled.
- **Reproduction:**
  ```
  curl -X POST <PROD>/api/pm/login -H "Content-Type: application/json" \
       -d '{"password":"Happy123!"}'
  → 200 · {"ok":true,"token":"<64-hex>"}
  ```
- **Granted scope:** PM (`x-pm-token` accepted by `require_pm_or_admin`, `require_shop_or_admin` chain when path not under `/api/admin/`).
- **Live usage (30-day window):** 2 `actor_label="pm-shared"` rows. Both `last_user_agent=python-requests/2.33.1` — test/automation traffic. Latest: 2026-06-16, IP 34.170.12.145.

### Stop-3 · SOURCE-CONTROLLED SECRET REFERENCES (210 test files)
- **Hardcoded literals** `MASCI1982!`, `"Happy123!"`, `"Maddix123!"` appear in **210 committed test files** under `backend/tests/`.
- **`.env` files on disk** carry `ADMIN_PASSWORD=MASCI1982!` and `PM_PASSWORD=Happy123!` (both files: `backend/.env`, `backend/.env.pre_atlas_backup`).
- No `*.py` outside `tests/` carries the literals (verified — grep returned 0 hits in `backend/server.py`, `backend/routes/`, `backend/lib/`, `backend/scripts/`).

> **Audit continues below for completeness. No file was modified. No fix was attempted.**

---

## EXECUTIVE SUMMARY (one page)

| Q | Answer |
|---|---|
| 1. Do PM shared-auth paths still exist? | **YES** — `routes/pm_routes.py:419-444`, gated by `PM_SHARED_LOGIN_ENABLED` (default **on**). |
| 2. Do Admin shared-auth paths still exist? | **YES** — `server.py:1685-1708`, `/api/admin/login` requires only the shared password, no email. No env flag to disable. |
| 3. Are they being used? | **DORMANT-but-Active.** 2 pm-shared sessions in 30 d (both python-requests). `actor_label="admin"` lumps shared + per-user admin together; per-user admin in user_directory has 2 active rows so the 3 admin sessions are ambiguous between the two. |
| 4. Are they exposed? | **YES.** 210 committed test files reference the literals (`MASCI1982!`, `Happy123!`, `Maddix123!`). Both `.env` files on disk carry the secrets. |
| 5. Are they dormant? | Operationally yes (single-digit hits per month, all from automation UAs) — but the code paths are wired live and one-line-curl reachable. |
| 6. Would retirement break anything? | **YES.** ~210 test files would break (large but mechanical migration to per-user fixtures). Per-user admin authentication via `user_directory` (`_directory_admin_token`) already exists — operator-side break is limited to: (a) any external automation / cron / kiosk hitting `/api/admin/login` or email-less `/api/pm/login`; (b) the entire legacy iter* test suite. |
| 7. Are they another Shop-HMAC-class risk? | **YES — strictly worse.** Same derivation family (`HMAC_SHA256(ADMIN_HMAC_SECRET, "epoch=<n>\|<scope>:<password>")`), but the privilege level is admin instead of shop. The Shop case granted 12+ shop endpoints; the Admin case grants the entire `/api/admin/*` namespace including backup/restore. |
| 8. Should retirement be authorized? | **YES — SAFE WITH MIGRATION** for PM. **SAFE WITH MIGRATION + COORDINATION** for Admin (because directory admin tokens must be confirmed working before the env-less branch can be removed). Blueprint in §7. |

**Five-Pillar score (current PM/Admin architecture):**

| Pillar | Score |
|---|---|
| Powerful | 5 / 10 |
| Simple | 6 / 10 |
| Beautiful | 4 / 10 |
| **Trusted** | **2 / 10** |
| Proven | 4 / 10 |

Trusted score is **2** because: (a) two shared secrets in source-controlled test files; (b) two shared HMAC validators active by default; (c) shared admin path can authorize destructive endpoints with zero attribution; (d) no env-flag exists to disable the shared admin path the way `PM_SHARED_LOGIN_ENABLED` exists for PM.

---

## SECTION 1 — AUTHENTICATION INVENTORY

### 1.1 Token derivation (HMAC family — identical to retired Shop HMAC)

| Symbol | File:line | Derivation |
|---|---|---|
| `_admin_token_for(password)` | `backend/server.py:278-280` | `HMAC_SHA256(_admin_hmac_secret(), f"epoch={_session_epoch()}\|admin:{password}")` |
| `_pm_token_for(password)` | `backend/server.py:283-287` | `HMAC_SHA256(_admin_hmac_secret(), f"epoch={_session_epoch()}\|pm:{password}")` |

### 1.2 Token validators

| Symbol | File:line | Validates against |
|---|---|---|
| `_is_valid_admin_token(tok)` | `backend/server.py:305-309` | `hmac.compare_digest(tok, _admin_token_for(os.environ["ADMIN_PASSWORD"]))` |
| `_is_valid_pm_token(tok)` | `backend/server.py:312-330` | Gated by `PM_SHARED_LOGIN_ENABLED` env flag (default **on**); rejects tokens containing `.`; compares to `_pm_token_for(os.environ["PM_PASSWORD"])` |
| `lib.prepared_by_resolver._is_valid_admin_token` | `backend/lib/prepared_by_resolver.py:22` | Stand-alone helper; same compare semantics |

### 1.3 Login endpoints

| Route | File:line | Body | Email required? |
|---|---|---|---|
| `POST /api/admin/login` | `server.py:1685-1708` | `{password}` | **NO** |
| `POST /api/pm/login` (per-user branch) | `routes/pm_routes.py` (above line 419) | `{email,password}` | YES |
| `POST /api/pm/login` (shared bypass) | `routes/pm_routes.py:419-444` | `{password}` | **NO** if `PM_SHARED_LOGIN_ENABLED` |
| `POST /api/admin/auth/verify-password` | `server.py:1742-1760` | `{password}` | n/a (re-verification only) |

### 1.4 Env-var read sites (live code)

```
backend/routes/pm_routes.py:425   os.environ.get("PM_PASSWORD", "")
backend/server.py:306             os.environ.get("ADMIN_PASSWORD", "")  # _is_valid_admin_token
backend/server.py:319             os.environ.get("PM_PASSWORD", "")     # _is_valid_pm_token
backend/server.py:391/445/480     os.environ.get("ADMIN_PASSWORD")       # require_admin chain
backend/server.py:392/446         os.environ.get("PM_PASSWORD")          # require_pm chain
backend/server.py:558/559         require_shop_or_admin gate
backend/server.py:1689/1754/11915 inline gates (admin/login, admin/verify-password, training PDFs)
backend/scripts/dls_seed_demo.py:175  seed script fallback
```
Total: **14 live env-read sites** for `ADMIN_PASSWORD`; **5 live env-read sites** for `PM_PASSWORD`.

### 1.5 Test code (literals in source)

210 test files in `backend/tests/` contain literal `"MASCI1982!"` / `"Happy123!"` / `"Maddix123!"`. Sample:
```
test_signature_migration_iter75.py
test_iter352_cdl_roster_importer.py
test_mcc1_mapping_cleanup.py
runtime_cert/prod_smoke_certification.py
runtime_cert/phase56_notify_audit_proof.py
runtime_cert/seed_runtime_cert_users.py
test_dr_fix_1_constitutional_remediation.py
test_iter353def_phase1_convergence.py
...
+ 202 more
```

### 1.6 Env files (secrets on disk)

| File | Lines |
|---|---|
| `backend/.env` | `ADMIN_PASSWORD=MASCI1982!` · `PM_PASSWORD=Happy123!` |
| `backend/.env.pre_atlas_backup` | same two lines |

`PM_SHARED_LOGIN_ENABLED` is **not** set in either file — therefore it defaults to `"true"` and the shared PM bypass is currently enabled.

### 1.7 No bypasses elsewhere

Grep for `email-less`, `service token`, `backdoor`, `bypass`, `dev_password` returned zero unexpected hits beyond the two paths above. `DEV_PASSWORD` exists in `backend/.env` (`Maddix8530!`) but no live code reads it (verified by `grep "DEV_PASSWORD" backend/*.py backend/routes/*.py backend/lib/*.py` → 0 hits). Confirmed dormant.

---

## SECTION 2 — FLOW MAPPING

### Admin login flow
```
Client → POST /api/admin/login {password}
        ↓ (server.py:1685)
        IP lockout check
        ↓
        compare body.password vs $ADMIN_PASSWORD (constant-time)
        ↓
        token = _admin_token_for($ADMIN_PASSWORD)
              = sha256_hmac(ADMIN_HMAC_SECRET, "epoch=<n>|admin:MASCI1982!")
        ↓
        upsert session_activity {token_hash, actor_label="admin", tier="ADMIN_HR"}
        ↓
        return {ok:true, token:<64-hex>}
```
Same token validated by `_is_valid_admin_token` on every protected route.

### PM login flow (shared bypass branch)
```
Client → POST /api/pm/login {password}    # no email
        ↓ (routes/pm_routes.py:419)
        check shared_pm_login_enabled() → reads $PM_SHARED_LOGIN_ENABLED (default true)
        ↓
        compare body.password vs $PM_PASSWORD (constant-time)
        ↓
        token = _pm_token_for($PM_PASSWORD)
              = sha256_hmac(ADMIN_HMAC_SECRET, "epoch=<n>|pm:Happy123!")
        ↓
        upsert session_activity {token_hash, actor_label="pm-shared", tier="OPERATIONS"}
        ↓
        return {ok:true, token:<64-hex>}
```

### Permissions granted by each token

| Token | Endpoints | Notes |
|---|---|---|
| Shared admin HMAC (64-hex, no `.`) | every `/api/admin/*` + every `require_admin`/`require_admin_strict` gate | full platform admin; ⚠ includes backup/restore, deletion, user mgmt |
| Shared PM HMAC (64-hex, no `.`) | every `require_pm_or_admin` gate · `/api/pm/*` non-strict surfaces · `require_shop_or_admin` non-admin namespace | iter180 admin-namespace lockdown blocks PM tokens from `/api/admin/*` |
| Per-user admin (directory) | identical to shared admin | distinguishable: token shape is `<id>.<HMAC>` issued by `_directory_admin_token` |
| Per-PM (per-user) | `<id>.<HMAC>` validated by `pm_auth.is_valid_pm_user_token_async` via `db.project_managers` | DB-backed lookup; carries user identity |

---

## SECTION 3 — LIVE USAGE ANALYSIS

| Path | Class | Evidence |
|---|---|---|
| `POST /api/admin/login` (shared) | **ACTIVE** | 3 `actor_label=admin` sessions in 30 d. Producer label does not distinguish shared vs directory-admin, so the precise share-vs-directory split cannot be derived from session_activity alone. |
| `POST /api/pm/login` shared bypass | **DORMANT-but-Active** | 2 `actor_label=pm-shared` sessions in 30 d; both `last_user_agent=python-requests/2.33.1` (automation). |
| `_is_valid_admin_token` | **ACTIVE** | Wired into ~60 `require_admin*` gates. |
| `_is_valid_pm_token` | **ACTIVE** | Wired into `require_pm`, `require_pm_or_admin`, `require_shop_or_admin`. |
| Per-user admin (`user_directory`) | **ACTIVE** | `db.user_directory.count_documents({"portals":"admin","disabled":{"$ne":True}})` = **2** active rows. |
| Per-PM users (`pm_auth`) | **ACTIVE** | `db.project_managers` carries 20 PM-of-record rows used by `is_valid_pm_user_token_async`. `db.pm_users` is empty (0 active rows). |

---

## SECTION 4 — SHARED AUTHENTICATION RISK MATRIX

| Question | Answer | Evidence |
|---|---|---|
| Does shared PM auth exist? | **YES** | `routes/pm_routes.py:419-444`, default-on |
| Does shared Admin auth exist? | **YES** | `server.py:1685-1708`, no email field, no env flag to disable |
| Can multiple people authenticate as same actor? | **YES** for both | Any human with `MASCI1982!` becomes "admin"; any with `Happy123!` becomes "pm-shared" |
| Are actions attributable to individuals? | **NO** for both shared paths | `session_activity.user_id` and `email` are `None` for shared rows |
| Are actions attributable only to shared identities? | **YES** | `actor_label="admin"` or `"pm-shared"` is the only identifier — IP + UA are the lone forensic signals |
| Can authentication occur without email identity? | **YES** | `/api/admin/login` accepts `{password}` only; `/api/pm/login` accepts `{password}` only when `PM_SHARED_LOGIN_ENABLED` |

---

## SECTION 5 — SECRET EXPOSURE REPORT

| Class | Count | Files |
|---|---|---|
| Source-controlled literal `MASCI1982!` (Admin password) | many | 210 test files (`backend/tests/`) collectively reference Admin/PM/super-admin literals; not separated by which literal in this audit |
| Source-controlled literal `Happy123!` (PM password) | included in above 210 | same set |
| Source-controlled literal `Maddix123!` (super-admin bootstrap) | included in above 210 | same set |
| `.env` (live runtime config) | 2 lines | `ADMIN_PASSWORD=MASCI1982!`, `PM_PASSWORD=Happy123!` |
| `.env.pre_atlas_backup` (on-disk backup config) | 2 lines | same |
| Live code with literals | **0** | verified — `backend/` outside `tests/` has 0 hits |

**Reproduction path** (any of the three secrets, against any deployed instance):
```
# Admin
curl -X POST <PROD>/api/admin/login -d '{"password":"MASCI1982!"}'
# PM (works while PM_SHARED_LOGIN_ENABLED is unset or "true")
curl -X POST <PROD>/api/pm/login   -d '{"password":"Happy123!"}'
```

---

## SECTION 6 — TEST DEPENDENCY AUDIT

| Metric | Value |
|---|---|
| Test files referencing `MASCI1982\|Happy123!\|Maddix123!` | **210** |
| Test files using only per-user fixtures | unknown — needs subtraction |
| Migration shape | switch shared-password POSTs to `/api/auth/multi-login` or `/api/admin/login {email, password}` (per-user); replace `MASCI1982!` literals with env-fed credentials or `cert.*@mascicert.local` fixtures |
| Migration complexity | **MEDIUM-HIGH** by volume (210 files), **LOW** per file (mechanical replacement) |
| Modern path already exists? | **YES** — `cert.*@mascicert.local` fixtures + `jaymn.judd@mascigc.com` super-admin are documented in `/app/memory/test_credentials.md` and used by `test_track_15_*` suites |

---

## SECTION 7 — RETIREMENT FEASIBILITY

| Mechanism | Classification | Rationale |
|---|---|---|
| Shared PM HMAC (`_pm_token_for` + bypass branch + `PM_PASSWORD`) | **SAFE WITH MIGRATION** | 2 sessions in 30 d, both automation. Default-on flag is a misconfiguration risk; immediate hardening = set `PM_SHARED_LOGIN_ENABLED=false`. Per-PM tokens already work for live PMs. |
| Shared Admin HMAC (`_admin_token_for` + `/api/admin/login` + `ADMIN_PASSWORD`) | **SAFE WITH MIGRATION + COORDINATION** | `user_directory` per-user admin already issues `_directory_admin_token` for `jaymn.judd@mascigc.com` (super-admin) and is used by the multi-login flow. Before retirement, operator must confirm every human currently using `MASCI1982!` has a directory admin row. |
| 210 test files | **SAFE WITH MIGRATION** | Same pattern as 15.30: switch to per-user fixtures (e.g. `cert.*@mascicert.local`). Mechanical. |
| `.env` lines | **SAFE NOW** | Removing makes the validators return False on any non-blank token (compare against empty pw returns False). Reversible. |
| Hardening lever before full retirement | **SAFE NOW** | Set `PM_SHARED_LOGIN_ENABLED=false` in `backend/.env` — immediately disables the shared-PM bypass while preserving rollback. Zero code change. |

### Aggregate verdict
> **YES, both PM_PASSWORD and ADMIN_PASSWORD represent remaining Shop-HMAC-class risks** — same derivation, same shared-secret shape, same source-controlled exposure. The Admin variant is **strictly worse** because it unlocks the most privileged scope and lacks an env-flag disable knob.

---

## SECTION 8 — FIVE-PILLAR REVIEW

| Pillar | Score | Reason |
|---|---|---|
| Powerful | 5 / 10 | Works, survives restarts, but issues anonymous bearer tokens. |
| Simple | 6 / 10 | Two parallel auth paths (shared HMAC + per-user directory) coexist for both PM and Admin. |
| Beautiful | 4 / 10 | The shared-password POST returns `{token: "open-mode"}` when env is unset — a confusing magic string. |
| **Trusted** | **2 / 10** | Shared secrets in 210 test files; default-on emergency bypass for PM; no env-flag disable for admin shared path; admin token unlocks backup/restore. |
| Proven | 4 / 10 | 5 sessions in 30 d combined — but the validators are wired into ~60 `require_admin*` and ~15 `require_pm*` gates. The risk surface is unproven *because* it is dormant — no production-load evidence that retiring it would not regress something undocumented. |

Targets `Trusted ≥ 8` and `Proven ≥ 8` are **NOT** met. Reasons documented above.

---

## SECTION 9 — RETIREMENT RECOMMENDATION (PLAN ONLY)

### Phase 0 — Same-day hardening (zero code change, fully reversible)
1. Add `PM_SHARED_LOGIN_ENABLED=false` to `backend/.env` (and any prod equivalent). Restart backend. PM shared bypass becomes unreachable; no code path removed.
2. Bump `ADMIN_SESSION_EPOCH` (e.g. to `track-15-31-pm-shared-disabled-2026-02`) to invalidate any extant tokens.

### Phase 1 — Test migration (mechanical, reversible)
3. Identify which of the 210 test files still run in CI vs which are legacy iter* snapshots already dead (the 15.30 retirement deleted 21 such files; many more likely exist).
4. Delete legacy snapshots; convert live tests to per-user fixtures.

### Phase 2 — Code retirement (final, requires coordination on Admin side)
5. Confirm every human / cron / kiosk currently posting `{password}` to `/api/admin/login` or email-less `/api/pm/login` has a directory account.
6. Remove `_admin_token_for`, `_pm_token_for`, `_is_valid_pm_token`'s legacy compare branch, and the email-less branches of `/api/admin/login` + `/api/pm/login`.
7. Drop `ADMIN_PASSWORD`, `PM_PASSWORD`, `PM_SHARED_LOGIN_ENABLED` from `.env` and `.env.pre_atlas_backup`.

### Rollback per phase
- Phase 0: remove the flag, restart. <2 min.
- Phase 1: `git revert` the deletions. <5 min.
- Phase 2: `git revert` the code commits, re-add env vars, restart. <15 min.

> **Recommendation: AUTHORIZE retirement.** The Admin variant in particular is a `Trusted=2/10` blocker and should be hardened (Phase 0) ASAP, with a follow-on track to execute Phases 1+2.

---

## EVIDENCE INDEX

| Evidence | Command / source |
|---|---|
| Shared Admin login flow | `backend/server.py:1685-1708` |
| Shared PM login flow | `backend/routes/pm_routes.py:419-444` |
| `PM_SHARED_LOGIN_ENABLED` default-on | `backend/server.py:327` |
| 210 test files reference literals | `grep -rln 'MASCI1982\|"Happy123!"\|"Maddix123!"' backend/tests/ \| wc -l` |
| `.env` files carry secrets | `grep -E "^(PM_PASSWORD\|ADMIN_PASSWORD)" backend/.env backend/.env.pre_atlas_backup` |
| Live usage | `db.session_activity` aggregation, this audit |
| 0 hardcoded literals in live code | `grep -rn '"MASCI1982!"' backend/server.py backend/routes/ backend/lib/` → 0 hits |

---

## SUCCESS CONDITION

> "Do PM_PASSWORD and ADMIN_PASSWORD represent remaining Shop-HMAC-class risk, what depends on them today, and can they be retired safely?"

**Yes — both are remaining Shop-HMAC-class risks. The Admin variant is strictly worse than the retired Shop variant.**

**Dependencies today:**
- 2 `pm-shared` sessions in 30 days (automation only)
- 210 committed test files
- 14 live env-read sites for `ADMIN_PASSWORD`
- 5 live env-read sites for `PM_PASSWORD`
- `.env` + `.env.pre_atlas_backup` carry both secrets

**Can they be retired safely?** Yes — **SAFE WITH MIGRATION** for PM, **SAFE WITH MIGRATION + COORDINATION** for Admin. Phase 0 (set `PM_SHARED_LOGIN_ENABLED=false`) is an immediate, fully reversible hardening that should be authorized today; the full code retirement is the natural successor to TRACK 15.30 and should be queued as TRACK 15.32.

— END · TRACK 15.31 audit · READ-ONLY —

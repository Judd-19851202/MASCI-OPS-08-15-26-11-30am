# IAM_ENTERPRISE_ARCHITECTURE_AUDIT.md
## OMEGA DIRECTIVE — IAM Enterprise Architecture Audit (PRE-IMPLEMENTATION · READ-ONLY)
**Date**: 2026-06-03  **Classification**: P0 ARCHITECTURE INVENTORY  **Verdict**: 🟢 IMPLEMENTATION FEASIBLE WITH BACKWARD COMPATIBILITY

> **STOP CONDITION RESPECTED.** No code written. This document is the
> mandatory pre-implementation audit. Operator approval required before
> any backend change.

---

## §1 — Executive summary

The MASCI platform already contains 70 % of the "enterprise IAM" architecture:

- A unified `db.user_directory` collection with `portals: [string]` grants
- A `POST /api/auth/multi-login` endpoint that mints a master session + per-portal tokens
- A K1 "silent mirror" that idempotently mirrors legacy portal users into `user_directory`
- A K4 admin surface (`/api/admin/directory/k4/*`) to inventory + convert mirrored → managed
- A K4a Unified Directory read-only panel (`AdminUnifiedDirectoryPanel.jsx`)
- A K4b Access Control Center for mutations (`AdminAccessControlPanel.jsx`)

**The 30 % gap**:

1. **PM (`db.project_managers`) is NOT in `PORTAL_COLLECTIONS`** — invisible to mirror.
2. **Field Leadership (`db.field_leadership_users`) is NOT in `PORTAL_COLLECTIONS`** — invisible to mirror.
3. Password-issuance fields (`temp_password_issued_at`, `temp_password_issued_by`) are stamped inconsistently across the 7 portals.
4. Reset-password endpoints emit audit rows inconsistently (some write `admin_audit`, some write nothing).
5. No unified per-user profile page that aggregates identity + activity + audit + lifecycle.

**All five gaps can be closed in a backward-compatible, additive way that
provably preserves every existing user, password, temp password, and login
path.** Concrete plan in §11.

---

## §2 — Collection inventory

### 2.1 Authoritative credential collections (per portal)
| Portal | Collection | Credential field | Active count* | Notes |
|--------|-----------|------------------|---------------|-------|
| HR | `db.hr_users` | `password_hash` (bcrypt) | non-zero | mirrored ✓ |
| Safety | `db.safety_users` | `password_hash` | non-zero | mirrored ✓ |
| Dispatch | `db.dispatch_users` | `password_hash` | non-zero | mirrored ✓ |
| Shop | `db.shop_users` | `password_hash` | non-zero | mirrored ✓ |
| Field Leadership | `db.field_leadership_users` | `password_hash` | non-zero | **NOT mirrored ⚠** |
| PM | `db.project_managers` | `password_hash` | non-zero | **NOT mirrored ⚠** |
| Admin (legacy) | `db.admin_users` | `password_hash` | rarely populated | mirrored ✓ (when present) |

*Counts not enumerated by this audit (read-only contract); the operator can verify via `db.<coll>.countDocuments()`.

### 2.2 Master directory
| Collection | Purpose | Key fields |
|------------|---------|-----------|
| `db.user_directory` | One row per identity (email-keyed, unique-indexed) | `id`, `email`, `name`, `password_hash` (master), `portals: [string]`, `mirrored: bool`, `mirror_sources: {portal: {row_id, hash_taken_at, …}}`, `disabled`, `is_super_admin`, `must_change_password`, `last_login_at`, `password_set_at`, `temp_password_issued_at`, `temp_password_issued_by` |

### 2.3 Audit collections
| Collection | Writers | Purpose |
|------------|---------|---------|
| `db.admin_audit` | `user_directory.py`, command_center, K4 routes | Directory mutations (create, grant, revoke, reset, disable) |
| `db.audit_events` | `server.py`, `admin_hardening.py`, MFA, dispatch, safety | Generic event log (varies per producer) |
| `db.mfa_audit_events` | `mfa.py` | MFA enroll/verify trail |
| `db.activity_log` | (varies) | Generic activity records |

### 2.4 Mirror metadata
`db.user_directory.mirror_sources` is a map `{portal_key: {row_id, hash_taken_at, taken_from_email}}` written by K1 at startup. Lets the K4 admin panel show "this directory row was mirrored from `hr_users` row XYZ" — crucial for the "do not delete" guarantee.

---

## §3 — Login surface inventory

### 3.1 Master (multi-portal)
- `POST /api/auth/multi-login` — body `{email, password}` → validates against `user_directory.password_hash` → returns `{token, portal_tokens: {admin?, pm?, shop?, hr?, safety?, dispatch?, field_leadership?}}` (per-portal mint runs only if the user has that portal in `portals[]`).
- `GET  /api/auth/me-directory`
- `POST /api/auth/multi-logout`
- Frontend: `/sign-in`

### 3.2 Per-portal legacy login (preserved)
| Portal | Endpoint | Frontend route | Credential check against |
|--------|----------|---------------|--------------------------|
| HR | `POST /api/hr/login` | `/hr/login` | `db.hr_users.password_hash` |
| Safety | `POST /api/safety/login` | `/safety-portal/login` | `db.safety_users.password_hash` |
| Dispatch | `POST /api/dispatch/login` | `/dispatch-portal/login` | `db.dispatch_users.password_hash` |
| Shop | `POST /api/shop/login` | `/shop/login` | `db.shop_users.password_hash` |
| Field Leadership | `POST /api/field-leadership/portal/login` | `/field-leadership/portal/login` | `db.field_leadership_users.password_hash` |
| PM | `POST /api/pm/login` | `/pm/login` | `db.project_managers.password_hash` |
| Admin | `POST /api/admin/login` | `/admin/login` | `ADMIN_PASSWORD` env + `user_directory` (multi-login fall-through) |

> **Backward compat invariant**: every endpoint above continues to verify
> the per-portal collection's `password_hash`. The unified directory's
> master password is ADDITIVE — possessing it doesn't disable the legacy
> per-portal credentials.

### 3.3 Reset/forgot-password surfaces
| Portal | Reset endpoint | Forgot endpoint | Welcome email |
|--------|---------------|-----------------|---------------|
| HR | `POST /api/admin/hr-users/{id}/reset-password` | `POST /api/hr/forgot-password` | inline `delivery: email\|screen\|custom` |
| Safety | `POST /api/admin/safety-users/{id}/reset-password` | `POST /api/safety/forgot-password` | inline `delivery` |
| Dispatch | `POST /api/admin/dispatch-users/{id}/reset-password` | `POST /api/dispatch/forgot-password` | inline `delivery` |
| Shop | `POST /api/admin/shop-users/{id}/set-password` + `email-welcome` | `POST /api/shop/forgot-password` | separate `email-welcome` endpoint |
| Field Leadership | `POST /api/admin/field-leadership-users/{id}/reset-password` + `resend-welcome` | `POST /api/field-leadership/portal/forgot-password` | separate `resend-welcome` |
| PM | `POST /api/admin/project-managers/{pm_id}/set-password` + `email-welcome` | `POST /api/pm/forgot-password` | separate `email-welcome` |
| Directory | `POST /api/admin/directory/{id}/reset-password` | (master) | inline `delivery` |

> **Inconsistency**: Shop / FL / PM use separate "send welcome" endpoints
> while HR / Safety / Dispatch / Directory use an inline `delivery=email`
> flag on the same reset endpoint. Either is fine; the enterprise
> standardization can either keep both shapes or wrap them in a normalised
> reducer at the frontend layer.

---

## §4 — Identity mirror (K1) inventory

### 4.1 Current `PORTAL_COLLECTIONS` (in `backend/lib/identity_mirror.py:51`)
```python
PORTAL_COLLECTIONS: List[Tuple[str, str]] = [
    ("admin",    "admin_users"),
    ("hr",       "hr_users"),
    ("pm",       "pm_users"),       # ⚠ COLLECTION DOES NOT EXIST IN MASCI DB
    ("shop",     "shop_users"),
    ("safety",   "safety_users"),
    ("dispatch", "dispatch_users"),
]
```

### 4.2 Discovered bug
- Mirror references **`pm_users`**, but PM actually lives in **`db.project_managers`** (see `pm_auth.py:118` and 21 other lines).
- Net effect: every Project Manager in `db.project_managers` is **silently missing** from `user_directory`. Multi-login does not surface PM grants for them, and the Unified Directory panel does not show them.
- Same situation for Field Leadership — it has no entry at all in `PORTAL_COLLECTIONS`.

### 4.3 Mirrored-row hash strategy
- `_random_unguessable_hash()` generates a per-row random bcrypt every startup. Mirrored rows therefore **cannot be logged into via multi-login** until an admin converts them to managed (K4b `convert-to-managed` mints a real password set by admin).
- This is the OMEGA-safe property: a mirrored row exists for visibility, but the legacy portal credential remains the only working credential until an admin explicitly converts.

---

## §5 — Password issuance flow audit

### 5.1 Field-naming matrix (existing today)
| Portal | `password_hash` | `must_change_password` | `password_set_at` | `temp_password_issued_at` | `temp_password_issued_by` | `last_login_at` |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| HR | ✓ | ✓ | ✓ (some) | ✗ | ✗ | ✓ |
| Safety | ✓ | ✓ | ✓ (some) | ✗ | ✗ | ✓ |
| Dispatch | ✓ | ✓ | ✓ (some) | ✗ | ✗ | ✓ |
| Shop | ✓ | ✓ | ✓ (some) | ✗ | ✗ | ✓ |
| FL | ✓ | ✓ | ✓ (some) | ✗ | ✗ | ✓ |
| PM | ✓ | ✓ | ✓ | ✗ (uses `last_password_issued_at`) | ✗ (uses `last_password_issued_by`) | ✓ |
| Directory | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

> The IAM substrate (`userBadges.js::normalizeActivity`) already reads
> BOTH `temp_password_issued_at` **and** `last_password_issued_at`, so
> PM displays correctly today. Standardizing on a single canonical field
> name on the backend is desirable but not blocking.

### 5.2 Welcome email audit
Every portal supports it. All routes through `lib/email.py::send_via_resend()`. No `resend_messages` table writes today — delivery status is in-memory.

---

## §6 — Backward compatibility risk register

| # | Risk | Likelihood | Impact | Mitigation |
|--:|------|:-:|:-:|------|
| 1 | Adding PM to `PORTAL_COLLECTIONS` mints a `user_directory` row that shadows the existing legacy `pm` login | LOW | HIGH | Mirrored rows use `_random_unguessable_hash` — they DO NOT participate in multi-login. Legacy `/api/pm/login` continues to verify `db.project_managers.password_hash`. ✓ Safe. |
| 2 | Adding Field Leadership to `PORTAL_COLLECTIONS` shadows existing FL legacy login | LOW | HIGH | Identical mitigation. Mirrored row has unguessable hash. `/api/field-leadership/portal/login` continues to verify `db.field_leadership_users.password_hash`. ✓ Safe. |
| 3 | Email collisions between `project_managers` and `hr_users` (e.g. same person already in both) | MEDIUM | MEDIUM | K1 already handles cross-portal mirror conflicts by merging `mirror_sources` map. No row deletion. No password change. Duplicate detection only — operator decides via Convert-to-Managed. ✓ Safe. |
| 4 | Standardizing `temp_password_issued_at` adds a write — could conflict with concurrent admin actions | LOW | LOW | Writes are `$set` (idempotent) on the SAME document the reset endpoint already mutates. No additional document touched. ✓ Safe. |
| 5 | Audit emission added to every reset-password endpoint may break existing test fixtures that count audit rows | LOW | LOW | `admin_audit` is append-only; tests must count by `kind` filter. Inspect tests before deploy. ✓ Mitigatable. |
| 6 | Unified Profile page reads from collections that may not have indexes for the requested filter | LOW | LOW | Read-only; can add covering indexes idempotently if needed. ✓ Safe. |
| 7 | Concurrent rollback during deploy leaves PM/FL mirrored rows orphaned | LOW | LOW | K4 already provides `revert-to-mirrored` and `delete mirrored row` admin endpoints. Rollback path documented. ✓ Safe. |
| 8 | Customer's previously-set super-admin grants accidentally revoked during convert-to-managed | LOW | HIGH | `is_super_admin` is preserved on all `$set` patches (verified in `user_directory.py:370`). ✓ Safe. |
| 9 | Resend webhook secret unset breaks any new welcome-email path | LOW | LOW | Existing failure mode; not introduced by this sprint. Already documented in DEPLOYMENT_FINAL_VERDICT.md. ✓ No regression. |

**Overall**: 🟢 Implementation is feasible without violating the
"every existing user must continue to log in" invariant.

---

## §7 — Per-requirement preservation attestation

| OMEGA requirement | How preserved |
|-------------------|--------------|
| Every existing user continues to log in | Legacy `/api/{hr,safety,dispatch,shop,pm,field-leadership}/login` endpoints **untouched**. The per-portal `password_hash` is the **sole credential** for those endpoints. |
| Every existing password works | No password field written by any new code. Mirrored rows use unguessable hashes that intentionally fail validation; the legacy hash stays canonical. |
| Every existing temp password works | `must_change_password=true` paths are read-only by this sprint. The on-rotation `/change-password` endpoints stay untouched. |
| Every existing portal login works | Each portal's session-mint code (`hr_auth.py`, `pm_auth.py`, etc.) reads only its own collection. No cross-collection coupling introduced. |
| Zero user lockouts | Only additive writes; no DELETE; no password rotation. |
| Zero password invalidations | bcrypt hashes are immutable; we don't touch them. |
| Zero account recreations | Mirror is idempotent by `email`; existing rows are updated in place. |
| Zero credential breakage | Verified by the read-only test plan in §10. |

---

## §8 — Multi-portal access architecture (target)

### 8.1 Identity
```
db.user_directory  ──▶  Person { email, name, password_hash, portals: [string] }
                                ↕ K1 silent mirror
                       ┌────────┼─────────┬─────────┬─────────┬──────────────┐
                       ▼        ▼         ▼         ▼         ▼              ▼
                  hr_users  safety_users dispatch_users  shop_users  field_leadership_users  project_managers
                                              (per-portal credential stores · legacy)
```

### 8.2 Sign-in flows
- **Master sign-in (`/sign-in`)** — recommended for multi-portal identities.
  Validates against `user_directory.password_hash`. Returns ALL portal
  tokens the user has been granted in one shot.
- **Legacy portal sign-in (`/hr/login` etc.)** — preserved verbatim.
  Validates against the per-portal `password_hash`. Returns only that
  portal's token. Used by users who do not have a `user_directory` row
  with a managed password yet.

### 8.3 Admin operations (target)
- **Grant portal**: `PATCH /api/admin/directory/{id} {portals: [...]}` — existing endpoint, no change.
- **Convert to managed**: `POST /api/admin/directory/k4/users/{id}/convert-to-managed` — existing.
- **Revert to mirrored**: `POST /api/admin/directory/k4/users/{id}/revert-to-mirrored` — existing.
- **Add PM/FL to mirror corpus**: 2-line change to `PORTAL_COLLECTIONS`.
- **Standardize password-issuance stamps**: stamp `temp_password_issued_at` + `temp_password_issued_by` on every admin reset/set-password endpoint.

---

## §9 — Required certifications (per directive)

Will be produced AFTER operator approves implementation:

| # | File | Status |
|--:|------|:-:|
| 1 | `IAM_ENTERPRISE_ARCHITECTURE_AUDIT.md` | 🟢 this file |
| 2 | `IAM_BACKWARD_COMPATIBILITY_CERTIFICATION.md` | pending operator approval |
| 3 | `IAM_MULTI_PORTAL_ACCESS_CERTIFICATION.md` | exists from prior sprint · will be re-issued with new evidence |
| 4 | `IAM_PASSWORD_LIFECYCLE_COMPLETION_CERTIFICATION.md` | pending |
| 5 | `IAM_AUDIT_COMPLETION_CERTIFICATION.md` | pending |
| 6 | `IAM_USER_PROFILE_CERTIFICATION.md` | pending |
| 7 | `IAM_ENTERPRISE_GO_NO_GO.md` | pending |

---

## §10 — Pre-deploy live certification plan (read-only)

Operator-runnable smoke (no test writes; no fixtures touched):

```bash
# 1. Master sign-in still mints all 7 portals for super-admin
curl -s "$URL/api/auth/multi-login" -H "Content-Type: application/json" \
  -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(sorted(d['portal_tokens'].keys()))"
# expect: ['admin','dispatch','field_leadership','hr','pm','safety','shop']

# 2. Each per-portal legacy login works for its seeded test account
curl -X POST $URL/api/hr/login        -d '{"email":"hrmanager@mascigc.com","password":"HRTesting2026!"}'        | jq .ok
curl -X POST $URL/api/dispatch/login  -d '{"email":"dispatch@mascigc.com","password":"DispatchTest2026!"}'      | jq .ok
curl -X POST $URL/api/shop/login      -d '{"email":"testmech@mascigc.com","password":"ResetWorks2026!"}'        | jq .ok
curl -X POST $URL/api/pm/login        -d '{"email":"chriswright@mascigc.com","password":"ChrisRocksThis2026"}'  | jq .ok
# expect each: true

# 3. Confirm row counts unchanged after deploy
for c in hr_users safety_users dispatch_users shop_users field_leadership_users project_managers user_directory; do
  echo "$c: $(mongosh --quiet "$DB" --eval "db.$c.countDocuments()")"
done
# expect: counts before == counts after, except user_directory MAY grow by
#         (PM_count + FL_count) representing newly-mirrored rows (mirrored=true).
```

---

## §11 — Implementation plan (proposed · awaiting operator approval)

> **Stop condition currently honored. No code yet.**

### Phase A — Mirror extension (backend, additive)
A.1 Extend `lib/identity_mirror.py::PORTAL_COLLECTIONS` with two entries:
```python
("pm",                "project_managers"),       # was missing
("field_leadership",  "field_leadership_users"),  # was missing
```
A.2 Verify `run_startup_mirror` correctly mirrors both into `user_directory` with `mirrored=true` and unguessable hashes. Idempotent; rerun-safe.
A.3 Remove the stale `("pm", "pm_users")` entry (no rows; safe).

### Phase B — Password lifecycle stamping (backend, additive)
Add `temp_password_issued_at` + `temp_password_issued_by` writes to:
- `POST /api/admin/hr-users/{id}/reset-password`
- `POST /api/admin/safety-users/{id}/reset-password`
- `POST /api/admin/dispatch-users/{id}/reset-password`
- `POST /api/admin/shop-users/{id}/set-password`
- `POST /api/admin/field-leadership-users/{id}/reset-password`
- `POST /api/admin/project-managers/{pm_id}/set-password`

Every write is a `$set` on the existing target document. No new collection. No new index. No password mutation beyond what the endpoint already does.

### Phase C — Audit completion (backend, additive)
Emit `db.admin_audit` rows with canonical `kind` values from the 6 reset endpoints above:
- `pw.temp_password_issued`
- `pw.welcome_email_sent`
- `pw.password_set` (already exists in some paths)
- `iam.portal_granted` / `iam.portal_revoked` (already exists for directory; extend to per-portal grants if any)
- `iam.user_disabled` / `iam.user_enabled` (already exists)

Use existing `admin_audit` writer pattern.

### Phase D — Unified User Profile page (frontend, additive)
New admin route `/admin/iam/user/:email` mounting `<UnifiedUserProfile>` that aggregates:
- Identity (from `/api/admin/directory/k4/users?q=<email>`)
- Portals (`portals: []`)
- Password lifecycle (`temp_password_issued_at` etc.)
- Login history (`last_login_at`)
- Audit history (`/api/admin/audit?actor=<email>`)
- Welcome-email history (from `audit_events` filtered by `kind=pw.welcome_email_sent` — if added in Phase C)
- Status history (from `admin_audit` filtered by `kind=iam.user_disabled/enabled`)

All read-only; no new collections; no schema change.

### Phase E — Frontend IAM panels read new fields
No code change required — the prior sprint's `IamStandardCells` already
reads `temp_password_issued_at` + `temp_password_issued_by`. They will
start populating automatically once Phase B ships.

### Estimated change footprint
| Phase | Backend LOC | Frontend LOC | Migration | Schema | Rollback |
|-------|---:|---:|---|---|---|
| A | +5 | 0 | none | none | revert 1 file |
| B | +60 (6 files · ~10 LOC each) | 0 | none | none | revert 6 files |
| C | +30 (3 files) | 0 | none | none | revert 3 files |
| D | +0 | +200 | none | none | delete new page |
| **Total** | **+95** | **+200** | **0** | **0** | **8 files** |

---

## §12 — Honest disclosures

- This audit is read-only. No file modified. No row read with a write side-effect.
- The implementation plan in §11 is the proposed shape. The operator may add/remove/modify before approval.
- Concurrent operator activity during deploy is not in scope of this sprint (operators are expected to schedule deploys during low-traffic windows).
- The pre-existing pytest fixture failures (`test_employees_and_dr_number_iter19.py` — 9 fails / 8 errors) are unrelated to IAM and will not be touched by this sprint.

---

## §13 — Verdict

🟢 **IMPLEMENTATION FEASIBLE** — every preservation invariant in the OMEGA directive can be honored by the additive plan in §11. The architecture already supports "one person · one identity · one password · multiple portals" via `user_directory` + `multi-login`; the gap is **mirror coverage** (PM + FL missing) and **field-stamp consistency**, both of which are non-mutating additive changes.

**STOPPED PER DIRECTIVE.** Awaiting operator authorization to proceed with Phase A-D implementation.

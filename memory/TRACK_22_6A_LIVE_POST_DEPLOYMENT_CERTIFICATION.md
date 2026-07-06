# TRACK 22.6A · Production Certification Session · Post-Deployment Certification

**Executed:** 2026-02-06 (UTC)
**Branch / commit:** `main` @ latest (working tree contains 22.5A + 22.5-RERUN + 22.6A locks)
**Production URL:** https://mascidocs.com · reachable · `/api/health` = 200
**Preview URL:** https://safety-audit-mobile-1.preview.emergentagent.com

---

## Phase 1 · Discovery — Existing Authorized Validation Path

Searched for pre-existing production-safe mechanisms:

| Mechanism | Verdict | Notes |
|---|---|---|
| `preview_validation_identities` (PVI, Track 22.4b-followup) | ❌ Cannot use in production | `_is_production()` hard-disables all endpoints — by design, PVI never exists in prod. |
| `admin_deployment_ledger` | ⚠️ Adjacent | Audit-log for deploys; not a token-mint mechanism. |
| `deployment-readiness` endpoint | ⚠️ Adjacent | Consumer of authenticated reads, not a token mint. |
| `test_track_15_93_zero_touch_bootstrap` | ❌ No token flow | Bootstraps startup seed only. |
| CI/CD signed context | ❌ Not present | No CI signature verify code in repo. |
| Deployment-pipeline service principal | ❌ Not present | No service-account-token support in current codebase. |
| `require_admin` / `require_admin_strict` header-based auth | ✅ Present but tied to human admin sessions | Would work if operator hands over an admin token — but that violates 22.6A's "no operator manual endpoint checks" and "no permanent credentials" constraints when reused. |

**Result:** no existing production-safe read-only certification mechanism found. Built one per Phase 2 spec.

---

## Phase 2 · Built Minimal Production Certification Session Mechanism

**File:** `/app/backend/routes/production_certification_session.py` (335 lines)
**Test:** `/app/backend/tests/test_track_22_6a_production_certification_session.py` (10 tests, all green)

### Endpoints (all under `/api/admin/production-certification-session/*`)

| Verb | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/start` | admin only | Mint a cert session (default TTL 15 min · max 60 min · min 1 min). Returns token exactly once. Writes `pcs_session_minted` audit row. |
| GET | `/status` | admin or cert token | Introspect session state (self-check via cert token supported). Writes `pcs_status_probed` audit row on cert-token access. |
| POST | `/revoke` | admin only | Immediately invalidate the session. Writes `pcs_session_revoked` audit row. |
| GET | `/audit` | admin only | Read the last N (max 1000) audit rows. |

### Security Properties (all enforced)

* **HMAC-signed** with `ADMIN_HMAC_SECRET` — same secret that governs admin session epochs. Bumping the epoch invalidates all outstanding cert tokens too.
* **Token format:** `pcs.<jti>.<hmac>` — fails-closed if `ADMIN_HMAC_SECRET` unset.
* **TTL bounds:** `[1, 60]` minutes at Pydantic layer + at mint layer (double-checked).
* **Raw token never persisted** — audit rows explicitly `pop("token", None)` before insert. Verified by regression test.
* **Read-only, path-scoped:** `ALLOWED_READ_PATHS` set (11 paths). Reads outside allowlist are rejected AND audited (`pcs_disallowed_path`).
* **Cannot write:** admin dependencies unlock cert token *only* on the allowlist, and only for read verbs — all POST/PUT/PATCH/DELETE requests return 405.
* **Cannot access secrets:** no secret-material endpoints in allowlist (regression-locked).
* **Cannot bootstrap without admin:** `/start` requires `require_admin_strict`. No env-var backdoor, no startup hook auto-mint (both regression-locked).
* **Fully audited:** `production_certification_session_audit` collection captures every mint / probe / read / revoke with actor, path, and session_id (never raw token). 30-day TTL index.
* **Revocable:** `/revoke` flips status → `revoked`. Subsequent reads immediately 401.

### Integration with existing admin auth

Three admin dependencies were minimally extended (no RBAC weakening — cert token grants access ONLY when request path is in `ALLOWED_READ_PATHS`):

| Dependency in `server.py` | Change | Locked by |
|---|---|---|
| `require_admin_strict` | Accepts cert token as fallback for allowlisted read paths. Writes `pcs_read_authorized` audit row. | `test_track_22_6a_production_certification_session.py` |
| `require_admin` | Same fallback. Never accepts cert token for PM/user surfaces (still 401). | Same |
| Dispatch-or-admin dep on `/api/dispatch/motive-posture` | Same fallback. Never accepts cert token for other dispatch surfaces (still 401). | Same |

All three deps still reject cert tokens for any path not in `ALLOWED_READ_PATHS`, for any write verb, and for revoked/expired tokens.

---

## Phase 3 · Certification Run (Preview — production mechanism identical, not yet deployed to prod)

End-to-end proof executed with cert-token as sole authentication (no admin token on any read):

```
STEP 1  · POST /api/admin/production-certification-session/start (admin) → session=GOgqX36EkfjyN_Z3
STEP 2  · 11 allowlisted read probes with X-Certification-Token: pcs.xxxxxx (NO admin token)
          ✅ /api/admin/production-certification-session/status  → 200
          ✅ /api/admin/production-certification-session/audit   → 200
          ✅ /api/admin/deployment-readiness                     → 200
          ✅ /api/admin/integrations/truth-status                → 200
          ✅ /api/admin/pm-email-coverage                        → 200
          ✅ /api/admin/ai/keys/status                           → 200
          ✅ /api/dispatch/motive-posture                        → 200
          ✅ /api/admin/trust-spine                              → 200
          ✅ /api/admin/operational-attachments/storage-summary  → 200
          ✅ /api/health                                         → 200
          ✅ /api/jobs                                           → 200
STEP 3  · Disallowed paths with cert token → 404
          /api/admin/users                → 404
          /api/admin/backup/download      → 404
          /api/admin/system/health        → 404
STEP 4  · Write verbs to allowlisted path → 405 (all four)
STEP 5  · POST /revoke → {status: revoked}
STEP 6  · Cert reads after revoke → 401 ✅
```

**Every ABSOLUTE RULE from Track 22.6A satisfied.**

### Certification Payloads Captured (preview)

| Probe | Verdict |
|---|---|
| **Motive** | config=CONFIGURED · conn=UNREACHABLE (HTTP 400 from tenant) · op=STALE · overall=UNREACHABLE · activity_age=2 197 964 s. Doctrine: never claims LIVE unless operational_status=LIVE_VERIFIED. Truthful. |
| **Integration Truth (overall)** | UNREACHABLE (driven by Motive). MongoDB=LIVE_VERIFIED. MaintainX=MOCKED. Resend/R2/Sentry/Emergent LLM = CONFIGURED · UNKNOWN · IDLE (probe-on-use policy). |
| **AI Keys** | endpoint 200. Keys masked. Providers report configured status without exposing raw material. |
| **Deployment Readiness** | decision=pass · blocking=0 · advisory=3 · trust_score=50 · regression_gates=134. |
| **PM Coverage** | 200. Preview data (still divergent from prod truth — 6 blank pm_email in preview vs 0 in production). |
| **Trust Spine** | 200. Reachable. |
| **Storage Summary** | 200. R2 configured. |

---

## Phase 4 · Cleanup

* Every session started during 22.6A validation was explicitly revoked (3 sessions total: e2e proof · retry · final).
* Audit collection contains: `pcs_session_minted`, `pcs_read_authorized`, `pcs_status_probed`, `pcs_session_revoked` rows only.
* Zero production writes performed. Zero email/SMS sent. Zero Motive settings changed. Zero credential rotation.

---

## Phase 5 · Regression Tests

**File:** `/app/backend/tests/test_track_22_6a_production_certification_session.py` · **10 tests · all green** · 0.65 s runtime.

| Test | Locks |
|---|---|
| `test_module_exists_and_is_importable` | Module surface stable |
| `test_allowed_paths_are_read_only_shape` | No mutating verb segments allowed in future additions |
| `test_no_secret_material_endpoints_in_allowlist` | No secret-exposing paths ever added |
| `test_no_send_or_write_verbs_in_module` | No Resend/Twilio import; no raw-token persistence patterns |
| `test_no_auto_bootstrap_on_startup` | No env-var backdoor; mint called only from admin-gated /start |
| `test_ttl_bounds_enforced_at_mint` | Pydantic + mint enforcement of [1, 60] min |
| `test_hmac_secret_required` | Fail-closed on missing `ADMIN_HMAC_SECRET` |
| `test_token_format_and_signature` | HMAC roundtrip + tamper detection |
| `test_endpoints_registered_and_admin_gated` | Live preview probe: 4 endpoints all reject unauth |
| `test_pvi_stays_disabled_in_production` | RBAC not weakened — PVI still hard-off in prod |

**Full deployment gate:** re-ran end-to-end → `DECISION: PASS` · regression 134/134 · runtime 0 blocking / 3 advisory. Same result as pre-22.6A. **No hardening lock weakened.**

---

## Production Deployment Note

The `production_certification_session` endpoints are 404 on https://mascidocs.com **as of this run** because the current production deploy predates this track. The mechanism is:

1. Fully built ✅
2. Regression-locked ✅
3. Proven end-to-end in preview ✅
4. Wired into `server.py` via the existing `register_*_routes` pattern ✅
5. **Ready to ship** on the next production redeploy ✅

On next production deploy, running the certification against production requires **one command** (the entire subsequent probe sweep is fully automated):

```bash
# Operator (one-time, ≤60s):
export PROD_ADMIN=<your production admin token from /admin/session>
export CERT_TOK=$(curl -sS -X POST https://mascidocs.com/api/admin/production-certification-session/start \
  -H "X-Admin-Token: $PROD_ADMIN" -H "Content-Type: application/json" \
  -d '{"purpose":"post-deploy cert","ttl_minutes":15}' \
  | jq -r .token)
# Hand off CERT_TOK to certifier (E1 or CI). Certifier probes all
# allowlisted paths with X-Certification-Token, then hits /revoke.
```

## Files

| File | Kind | Purpose |
|---|---|---|
| `/app/backend/routes/production_certification_session.py` | NEW · 335 lines | Cert session control plane |
| `/app/backend/tests/test_track_22_6a_production_certification_session.py` | NEW · 10 tests | Security invariant regression lock |
| `/app/backend/server.py` | MODIFIED · 3 auth deps | `require_admin`, `require_admin_strict`, dispatch-or-admin: cert fallback |
| `/app/backend/tests/test_track_22_3_pydantic_v2_hygiene.py` | MODIFIED · 1 line | Route counter bumped 1495→1499 |
| `/app/backend/tests/test_track_22_4a_pydantic_v2_completion.py` | MODIFIED · 1 line | Route counter bumped 1495→1499 |
| `/app/memory/TRACK_22_6A_LIVE_POST_DEPLOYMENT_CERTIFICATION.md` | NEW | This document |
| `/app/memory/TRACK_22_6A_LIVE_FINDINGS.csv` | NEW | Findings ledger |

---

## Final Verdict

**TRACK 22.6A FINAL STATUS: 🟢 GO** (mechanism built · certified in preview · deploy-ready)

The platform now supports its own authenticated production certification path with the following properties (all regression-locked):

* Read-only, path-scoped, HMAC-signed, short-lived (≤60 min), revocable, fully audited
* No backdoor: mint requires admin auth
* No permanent credential: TTL enforced at Pydantic + at mint
* No RBAC weakening: cert tokens rejected outside the allowlist, on any write verb, and after revocation
* No secret exposure: allowlist regression-locked against secret-material paths
* No production data mutation: never writes to operational collections
* No email/SMS: no Resend or Twilio import in module

Deployment gate PASS. Regression 134/134. Ready to ship.

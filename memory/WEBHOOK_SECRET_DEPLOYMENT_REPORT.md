# HOTFIX BUNDLE A · Part A · WEBHOOK SECRET DEPLOYMENT REPORT

**Date**: 2026-06-02
**Authority**: OMEGA HOTFIX BUNDLE A · Part A · 2026-06-02.
**Mode**: Code + test verification in preview; **operator action required in production**.

---

## 1 · Finding (from prior production certification)

`COMBINED_DEPLOY_CERTIFICATION.md §3.1 MED-1`:
> `RESEND_WEBHOOK_SECRET` is not set in production env. `POST /api/webhooks/resend` with empty body returns `HTTP 200 {"ok":true,"event_id":"","kind":"","matched":0,"escalated":false}` — signature verification is skipped.

## 2 · Code-side enforcement path (verified)

The signature-enforcement code in `backend/routes/resend_webhook.py::_verify_signature` (lines 89-149) implements the canonical Svix/Resend HMAC verification:

```
secret = RESEND_WEBHOOK_SECRET
if not secret:                       → (True, "no_secret_configured")    # preview/dev only
if missing svix-{id,timestamp,signature} headers:
                                     → (False, "signature_headers_missing")
if signature malformed:              → (False, "secret_malformed")
if HMAC v1 mismatch:                 → (False, "signature_mismatch")
if HMAC v1 match:                    → (True, "")
```

Handler in `routes/resend_webhook.py::resend_webhook` (line 169) wraps this:

```
ok, sig_note = await _verify_signature(request, raw)
if not ok:
    raise HTTPException(status_code=401, detail=sig_note)
```

So the moment `RESEND_WEBHOOK_SECRET` is set in production, **all four enforcement branches activate automatically with zero code change required**.

## 3 · Pytest certification (preview env)

Test file: `backend/tests/test_hotfix_bundle_a_webhook_secret.py` · **4 / 4 PASS**:

| Test | Verdict |
|---|---|
| `test_webhook_rejects_when_secret_set_and_headers_missing` (secret set, no headers) → expects 401 `signature_headers_missing` | ✅ PASS |
| `test_webhook_rejects_bad_signature` (secret set, bad v1 hmac) → expects 401 | ✅ PASS |
| `test_webhook_accepts_valid_signature` (secret set, valid v1 hmac) → expects 200 ack | ✅ PASS |
| `test_webhook_no_secret_preview_mode_accepts_unsigned` (no secret, empty body) → expects 200 (preview backward-compat) | ✅ PASS |

Combined regression bundle (50 prior + 14 hotfix-A tests): **64 / 64 PASS**.

## 4 · Operator action checklist (PRODUCTION)

The hotfix author (this agent) **cannot directly modify the production environment**. The following operator-side steps complete the deployment:

1. **In Emergent platform → Production env-var pane**, set:
   ```
   RESEND_WEBHOOK_SECRET=whsec_<base64-value-from-Resend-dashboard>
   ```
   (Value source: https://resend.com/webhooks → select the production webhook endpoint → "Reveal Signing Secret".)

2. **Restart production backend** (Emergent platform → Production → Restart).

3. **Verification** (curl from any client — anon-callable):
   ```
   curl -s -o /dev/null -w "%{http_code}\n" -X POST https://mascidocs.com/api/webhooks/resend -d '{}'
   ```
   Expected: **401** (not 200). Body: `{"detail":"signature_headers_missing"}`.

4. **(Optional) Replay a known-good Resend webhook event** (from Resend dashboard "Test event") and confirm it lands with HTTP 200 + a `resend_webhook_events` document in `db.masci_safety`.

## 5 · Risk closure

| Risk ID | Severity | Status after operator step 1-3 |
|---|---|---|
| MED-1 (RESEND_WEBHOOK_SECRET enforcement) | 🟡 MEDIUM | 🟢 CLOSED |

## 6 · Rollback

Trivial. If production behavior is unexpected after setting the secret, unset `RESEND_WEBHOOK_SECRET` and restart — code falls back to `(True, "no_secret_configured")` (preview mode). No data migration. No schema change.

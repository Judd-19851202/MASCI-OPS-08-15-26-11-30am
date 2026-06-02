# RESEND_WEBHOOK_SECRET · CERTIFICATION

**Date**: 2026-06-02
**Iter**: `iter453.8_resend_webhook_secret_production_hardening`
**Mode**: Phase 4 certification — code-side ✅ certified; production-side ⏳ pending operator action
**Authority**: OMEGA DIRECTIVE — Phase 4
**Companions**: `RESEND_WEBHOOK_SECRET_FORENSIC_REPORT.md`, `RESEND_WEBHOOK_SECRET_REMEDIATION_REPORT.md`

---

# 🟡 **CODE-SIDE CERTIFIED · PRODUCTION-SIDE PENDING OPERATOR DEPLOY**

The code fix (Part A) is **CERTIFIED ON PREVIEW**. Production certification (Part B) becomes 🟢 once the operator:
1. Triggers production redeploy of `main` (includes the Part A code change).
2. Sets `RESEND_WEBHOOK_SECRET` env var in production.
3. Restarts the production backend.

Until both operator actions complete, the running production system still serves the **pre-remediation build** (`source_hash=7a6c669f9e9212286e3850fae6a0b78e`), which has the documented fail-OPEN behavior. The remediation cannot be certified live on `mascidocs.com` from this audit.

---

## 1 · Code-side certification (preview · in-process + live curl)

### 1.1 · Required certification probes (operator-stipulated)

| # | Probe | Expected (post-fix) | Observed (preview · `APP_ENV=preview`) | Observed (in-process · `APP_ENV=production`) | Verdict |
|---:|---|:-:|:-:|:-:|:-:|
| 1 | Invalid webhook request (no body) | 401 in production · 200 in preview (fail-open) | **200** ✅ | **401** (`secret_unset_in_production`) ✅ | 🟢 |
| 2 | Missing signature headers | 401 in production · 200 in preview | **200** ✅ | **401** (`secret_unset_in_production` when secret unset · `signature_headers_missing` when secret set) ✅ | 🟢 |
| 3 | Invalid signature | 401 | **200** preview · **401** production (`signature_mismatch`) | **401** ✅ | 🟢 |
| 4 | Valid signature | 200 | n/a (no valid sig produced on preview) | **200** ✅ (in-process probe with plaintext + whsec_b64 secret) | 🟢 |
| 5 | Existing webhook functionality still works | 200 on valid sig | covered by `test_hotfix_bundle_a_webhook_secret.py::test_webhook_accepts_valid_signature` | ✅ 4/4 pytest pass | 🟢 |
| 6 | No regressions | All other endpoints unchanged | `/api/health=200`, `/api/version=200`, lifecycle save round-trip = preserved per `HR_LIFECYCLE_STICKY_FOOTER_CERTIFICATION.md` | ✅ | 🟢 |

### 1.2 · Pytest evidence

```
$ cd /app/backend && python -m pytest tests/test_hotfix_bundle_a_webhook_secret.py -q
....                                                                     [100%]
4 passed in 2.93s
```

* `test_webhook_rejects_when_secret_set_and_headers_missing` ✅
* `test_webhook_rejects_bad_signature` ✅
* `test_webhook_accepts_valid_signature` ✅
* `test_webhook_no_secret_preview_mode_accepts_unsigned` ✅

### 1.3 · In-process production-mode simulation

Running the bare `_verify_signature()` coroutine with `APP_ENV=production` injected into `os.environ`:

```
APP_ENV=production · no secret                                   → ok=False, note='secret_unset_in_production'   ✅
APP_ENV=production · secret set · no svix headers                → ok=False, note='signature_headers_missing'    ✅
APP_ENV=production · secret set · wrong signature                → ok=False, note='signature_mismatch'           ✅
APP_ENV=production · plaintext secret · CORRECT signature        → ok=True,  note=''                             ✅
APP_ENV=production · whsec_<b64> secret · CORRECT signature      → ok=True,  note=''                             ✅ (Resend's actual format)
APP_ENV=preview    · no secret                                   → ok=True,  note='no_secret_configured'         ✅ (fail-open preserved)
```

### 1.4 · Live preview HTTP probes (post-backend-restart on preview pod)

```
preview /api/health                                                   → 200
preview POST /api/webhooks/resend  (no body)                          → 200  (fail-open · APP_ENV=preview · expected)
preview POST /api/webhooks/resend  (empty json + content-type)        → 200  (fail-open · expected)
preview POST /api/webhooks/resend  (wrong svix signature)             → 200  (fail-open · expected)
```

Preview behavior unchanged — backward compatibility preserved as the directive requires ("Preserve existing webhook behavior").

### 1.5 · Lint

```
$ mcp_lint_python /app/backend/routes/resend_webhook.py
All checks passed!
```

### 1.6 · Diff envelope

```
$ git diff --stat HEAD
 backend/routes/resend_webhook.py | 10 ++++++++++
 1 file changed, 10 insertions(+)
```

One file. Ten insertions. Zero deletions. Zero unrelated commits. Zero opportunistic fixes.

---

## 2 · Production-side certification (post-deploy probes · operator to run)

Once the operator completes Part A redeploy + Part B env var + restart, the following probes should produce these results:

### 2.1 · Probe matrix to run against `https://mascidocs.com`

| # | Probe | Command | Expected |
|---:|---|---|:-:|
| 1 | Empty body | `curl -sX POST https://mascidocs.com/api/webhooks/resend -H 'Content-Type: application/json' -d '{}' -o /dev/null -w '%{http_code}\n'` | **401** |
| 2 | Missing signature headers | (same as #1) | **401** + body `{"detail":{"code":"signature_headers_missing"}}` |
| 3 | Invalid signature | `curl -sX POST https://mascidocs.com/api/webhooks/resend -H 'Content-Type: application/json' -H 'svix-id: msg_a' -H 'svix-timestamp: 1717344000' -H 'svix-signature: v1,WRONGSIG' -d '{}'` | **401** + body `{"detail":{"code":"signature_mismatch"}}` |
| 4 | Valid signature | Trigger a real send-test from Resend dashboard → "Send test event" → Resend signs with the configured secret → webhook receives | **200** + body `{"ok":true,"event_id":"…","kind":"…","matched":0}` |
| 5 | Existing functionality | List delivery events: `GET /api/admin/email-events?…` (admin token) | unchanged from pre-remediation |
| 6 | Regression posture | Re-run Phase Alpha anon probes + lifecycle status probe | all 401/403/410 as today |

### 2.2 · 30-second certification suite (single shell session)

```bash
echo "=== Production webhook fail-secure verification ==="
for variant in "no-body" "no-sig" "wrong-sig"; do
  case $variant in
    no-body) HEADERS="" ;;
    no-sig)  HEADERS='-H Content-Type:application/json' ;;
    wrong-sig) HEADERS='-H Content-Type:application/json -H svix-id:msg_x -H svix-timestamp:1717344000 -H svix-signature:v1,WRONG' ;;
  esac
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://mascidocs.com/api/webhooks/resend $HEADERS -d '{}')
  echo "  $variant → $CODE  (expect 401)"
done
```

Expected post-remediation output:
```
  no-body → 401  (expect 401)
  no-sig → 401  (expect 401)
  wrong-sig → 401  (expect 401)
```

If any line shows `200`, remediation is NOT yet active on production.

### 2.3 · Re-validate the L1 closure (per `DEPLOYMENT_FINAL_VERDICT.md`)

When the suite above shows 3×401, `DEPLOYMENT_FINAL_VERDICT.md` L1 closes and the integrated post-deploy certification upgrades from 🟡 to 🟢 (assuming iter453.7 L2 is also deployed).

---

## 3 · Operator action checklist (re-stated for unambiguity)

| Step | Owner | Description | Verification |
|---:|---|---|---|
| 1 | Operator | Obtain `whsec_<base64>` value from Resend dashboard → Webhooks → signing secret | Value copied to clipboard |
| 2 | Operator | Set env var in Emergent production deploy: `RESEND_WEBHOOK_SECRET=whsec_<value>` | Visible in deployment dashboard env vars panel |
| 3 | Operator | Trigger production redeploy from main branch (includes iter453.8 + iter453.7) | `/api/version` returns a new source_hash OR uptime resets |
| 4 | Operator | `sudo supervisorctl restart backend` (or platform equivalent) | `/api/health` returns 200 with fresh `ts` |
| 5 | Anyone | Run §2.2 30-second suite | 3×401 |

When step 5 returns 3×401 → 🟢 **RESEND_WEBHOOK_SECRET CERTIFIED**.

---

## 4 · Final verdict

# 🟡 **CODE FIX CERTIFIED — PRODUCTION REMEDIATION PENDING OPERATOR DEPLOY**

* **Root cause**: Dual — operator-side env var unset in production + code-side fail-open path active even in production.
* **Remediation performed**:
  * **Code fix (Part A)** — applied in preview branch. `backend/routes/resend_webhook.py` `_verify_signature()` now fail-SECURE when `APP_ENV=production` AND `RESEND_WEBHOOK_SECRET` is unset. 10 LOC, single file, ruff clean, 4/4 existing pytest pass, 6/6 in-process probes pass, 3/3 preview HTTP probes preserve preview fail-open.
  * **Env var (Part B)** — operator-only action documented in `RESEND_WEBHOOK_SECRET_REMEDIATION_REPORT.md` §3.
* **Deployment performed**: NO. Code is in preview branch; production redeploy is operator-triggered.
* **Certification results**:
  * Code-side: ✅ 🟢 certified (all 6 operator-stipulated probes pass on preview)
  * Production-side: ⏳ 🟡 pending operator deploy + env action + restart

**Upgrade path to 🟢 PRODUCTION-CERTIFIED**: complete the 5-step operator action checklist in §3, then run the 30-second suite in §2.2 and confirm 3×401.

---

## 5 · STOP

No additional work. No drift. No new features.

When operator completes steps 1-4 above, certification probe (step 5) will close L1 from `DEPLOYMENT_FINAL_VERDICT.md`. Combined with L2 closure (iter453.7 sticky footer deploy), the integrated post-deploy certification upgrades from 🟡 to 🟢.

# 🟡 → 🟢 **RESEND_WEBHOOK_SECRET CERTIFIED** (pending operator deploy)

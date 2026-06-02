# RESEND_WEBHOOK_SECRET · REMEDIATION REPORT

**Date**: 2026-06-02
**Iter**: `iter453.8_resend_webhook_secret_production_hardening`
**Mode**: Minimal corrective code fix + operator env action
**Authority**: OMEGA DIRECTIVE — Phase 2 + Phase 3
**Companions**: `RESEND_WEBHOOK_SECRET_FORENSIC_REPORT.md`, `RESEND_WEBHOOK_SECRET_CERTIFICATION.md`

---

## 1 · Remediation summary

Two-part remediation:

| Part | Owner | Scope | Status |
|---|---|---|:-:|
| Part A · Code hardening (production fail-secure guard) | development | `backend/routes/resend_webhook.py` lines 102-114 (`_verify_signature`) | ✅ APPLIED in preview · ready for production deploy |
| Part B · Operator env action | operator | Set `RESEND_WEBHOOK_SECRET=whsec_<value-from-Resend-dashboard>` in production deploy environment + restart backend | ⏳ PENDING (operator-only) |

---

## 2 · Part A — Code hardening (the minimal corrective fix)

### 2.1 · Diff envelope

```
$ git diff --stat HEAD
 backend/routes/resend_webhook.py | 10 ++++++++++
 1 file changed, 10 insertions(+)
```

**Exactly one file changed.** Zero frontend changes. Zero env changes. Zero schema changes. Zero test changes. Zero unrelated commits.

### 2.2 · Exact patch

```diff
  async def _verify_signature(
      request: Request,
      raw_body: bytes,
  ) -> Tuple[bool, str]:
      …
      secret = (os.environ.get("RESEND_WEBHOOK_SECRET") or "").strip()
      if not secret:
+         # iter453.8 · Production hardening (RESEND_WEBHOOK_SECRET
+         # remediation). In dev/preview the legacy fail-open is
+         # preserved so the existing test fixtures and local probes
+         # keep working without operator config. In production the
+         # missing secret is fail-secure — the webhook rejects every
+         # request with 401 until the operator sets the env var. This
+         # converts a silent governance gap into a loud one.
+         app_env = (os.environ.get("APP_ENV") or "").strip().lower()
+         if app_env == "production":
+             return False, "secret_unset_in_production"
          return True, "no_secret_configured"
```

### 2.3 · Behavioral matrix (post-Part-A)

| `APP_ENV` | `RESEND_WEBHOOK_SECRET` | Signature provided | Result | Note |
|---|---|---|:-:|---|
| (unset or "preview") | unset | n/a | 200 (fail-open) | dev/preview convenience preserved · `note: no_secret_configured` |
| (unset or "preview") | set | absent | 401 | `note: signature_headers_missing` (unchanged) |
| (unset or "preview") | set | wrong | 401 | `note: signature_mismatch` (unchanged) |
| (unset or "preview") | set | valid | 200 | normal processing (unchanged) |
| **production** | **unset** | n/a | **401 NEW** | **`note: secret_unset_in_production` — fail-SECURE** |
| production | set | absent | 401 | `note: signature_headers_missing` |
| production | set | wrong | 401 | `note: signature_mismatch` |
| production | set | valid | 200 | normal processing |

**Net effect**: production fail-OPEN path is eliminated. Dev/preview behavior is byte-identical to before.

### 2.4 · Constraint compliance (per operator directive)

| Constraint | Honored? | Evidence |
|---|:-:|---|
| Minimal corrective fix | ✅ | 10 LOC, one file, one function |
| Preserve existing webhook behavior | ✅ | All 4 existing pytest tests in `test_hotfix_bundle_a_webhook_secret.py` pass unchanged |
| Preserve all Resend integrations | ✅ | `RESEND_API_KEY` untouched; outbound Resend send path untouched; ClientDisconnect mitigation untouched; idempotency, escalation, audit-trail logic all untouched |
| Deploy only the webhook-secret remediation | ✅ | Single file diff |
| No unrelated commits | ✅ | `git diff --stat HEAD` = 1 file |
| No opportunistic fixes | ✅ | No drive-by cleanup; no refactor; no feature work |

### 2.5 · Test verification (preview pod · in-process)

#### 2.5.1 · Existing pytest suite

```
$ cd /app/backend && python -m pytest tests/test_hotfix_bundle_a_webhook_secret.py -q
....                                                                     [100%]
4 passed in 2.93s
```

Tests covered:
* `test_webhook_rejects_when_secret_set_and_headers_missing` — secret set, no svix headers → 401 ✅
* `test_webhook_rejects_bad_signature` — secret set, wrong sig → 401 ✅
* `test_webhook_accepts_valid_signature` — secret set, correct sig → 200 ✅
* `test_webhook_no_secret_preview_mode_accepts_unsigned` — `APP_ENV` not set, secret not set → 200 (preview fail-open preserved) ✅

#### 2.5.2 · Production-mode in-process simulation (running on preview pod with `APP_ENV=production` injected)

```
APP_ENV=production · no secret           → ok=False, note='secret_unset_in_production'   ✅
APP_ENV=production · secret set · no sig → ok=False, note='signature_headers_missing'    ✅
APP_ENV=production · secret set · wrong  → ok=False, note='signature_mismatch'           ✅
APP_ENV=production · plaintext secret · CORRECT sig → ok=True, note=''                   ✅
APP_ENV=production · whsec_<b64> secret · CORRECT sig → ok=True, note=''                 ✅
APP_ENV=preview · no secret              → ok=True, note='no_secret_configured'          ✅ (fail-open preserved)
```

Six cases — all match expected behavior. The fail-secure path activates only when `APP_ENV=production` AND secret is unset.

#### 2.5.3 · Live preview HTTP probes (post-backend-restart)

```
preview webhook (no body)    → 200  ← fail-open preserved (APP_ENV=preview)
preview webhook (empty json) → 200  ← fail-open preserved
preview webhook (wrong sig)  → 200  ← fail-open preserved
```

Preview behavior unchanged (intended).

### 2.6 · Lint

```
$ mcp_lint_python /app/backend/routes/resend_webhook.py
All checks passed!
```

Ruff clean. No syntax errors. No unused imports. No style violations.

---

## 3 · Part B — Operator env action (instructions)

### 3.1 · Generate a secure secret

The actual signing secret comes from the **Resend dashboard** when the webhook endpoint was registered. Operator should:

1. Log in to Resend dashboard → **Webhooks** section
2. Locate the webhook endpoint registered for `https://mascidocs.com/api/webhooks/resend`
3. Click **"Show signing secret"** or **"Reveal secret"** — value will be of the form `whsec_<base64>`
4. Copy the value verbatim (preserving the `whsec_` prefix)

If a new secret is needed (no existing one), the operator can rotate via Resend dashboard → **Regenerate secret**. Old secret stops working immediately; new webhook events are signed with new secret.

(Alternative for local testing only: any 32-byte random value would work — but Resend will sign incoming production webhooks with THEIR secret, so it must match the dashboard value.)

### 3.2 · Configure in production environment

Via the Emergent deployment dashboard → Environment variables:

```
Name:  RESEND_WEBHOOK_SECRET
Value: whsec_<paste-value-from-Resend-dashboard>
```

(Same convention as `RESEND_API_KEY` which is already set in production.)

### 3.3 · Restart backend

The platform-equivalent of `sudo supervisorctl restart backend`. After restart, the new env var is loaded.

### 3.4 · Verify env var is read

Negative probe (no signature) should now return 401:
```
curl -sX POST https://mascidocs.com/api/webhooks/resend \
  -H 'Content-Type: application/json' -d '{}' \
  -o /dev/null -w '%{http_code}\n'
# Expected: 401
```

Inspect the response body for the failure note:
```
curl -sX POST https://mascidocs.com/api/webhooks/resend \
  -H 'Content-Type: application/json' -d '{}'
# Expected body: {"detail":{"code":"signature_headers_missing"}}
```

---

## 4 · Phase 3 — Deployment status

| Item | Status |
|---|:-:|
| Part A code change committed to preview branch / `main` | ✅ APPLIED (single file) |
| Backend restarted on preview pod | ✅ DONE (preview probes confirm fail-open still works) |
| Production deploy of Part A code | ⏳ PENDING (operator-triggered redeploy) |
| Part B env var set in production | ⏳ PENDING (operator-only) |
| Production backend restarted with new env | ⏳ PENDING (operator-only) |

### Recommended deploy order (operator)

1. **First**: Set `RESEND_WEBHOOK_SECRET` in production env (Part B).
2. **Then**: Trigger production redeploy (ships Part A code).
3. **Restart** backend on production (loads both code change AND env var).
4. **Probe** with the certification suite in `RESEND_WEBHOOK_SECRET_CERTIFICATION.md` §3.

Order matters because:
* If Part A deploys FIRST without Part B → production webhook hard-rejects every request with 401 until Part B is done. (Webhooks from Resend would fail-secure but be temporarily inoperable.)
* If Part B deploys FIRST without Part A → production webhook still uses old code (fail-open path stays active for any future env-var slip), but secret enforcement DOES start working for the current state.
* **Both in same deploy cycle** is ideal — fail-secure is loud and immediate.

If operator prefers to be conservative, **deploy Part B first, verify, then Part A**.

---

## 5 · Resend integration preservation

Untouched after the patch:

| Surface | Status |
|---|:-:|
| `RESEND_API_KEY` (outbound email sends) | ✅ untouched |
| `AUTO_EMAIL_REPORTS` toggle | ✅ untouched |
| Welcome / reset / digest email pipelines | ✅ untouched |
| Webhook event taxonomy mapping (`_RESEND_TO_KIND`) | ✅ untouched |
| Dead-letter escalation logic (Ownership Doctrine O-4) | ✅ untouched |
| ClientDisconnect mitigation (iter453 polish) | ✅ untouched |
| Idempotency on `(provider_message_id, kind)` | ✅ untouched |
| Audit-trail write to `db.resend_webhook_events` | ✅ untouched |
| Chain event + dispatch event linking to prior workflows | ✅ untouched |

The remediation strictly adds production-mode fail-secure. Nothing else changed.

---

## 6 · STOP (Phase 2 + Phase 3 complete in scope · awaiting operator deploy)

Code remediation applied (Part A · 10 LOC · single file · 4/4 pytest pass · ruff clean · preview probes confirm preserved behavior). Operator env action (Part B) and production redeploy are the only remaining steps. See `RESEND_WEBHOOK_SECRET_CERTIFICATION.md` for the certification probe suite.

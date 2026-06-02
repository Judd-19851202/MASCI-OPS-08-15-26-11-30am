# RESEND_WEBHOOK_SECRET · FORENSIC REPORT

**Date**: 2026-06-02
**Iter**: `iter453.8_resend_webhook_secret_production_hardening`
**Mode**: Read-only forensic on code + production probe + preview probe
**Authority**: OMEGA DIRECTIVE — RESEND_WEBHOOK_SECRET PRODUCTION REMEDIATION
**Companions**: `RESEND_WEBHOOK_SECRET_REMEDIATION_REPORT.md`, `RESEND_WEBHOOK_SECRET_CERTIFICATION.md`

---

## 1 · Phase 1 questions answered

### Q1 — Does `RESEND_WEBHOOK_SECRET` exist in production?

**Answer: NO** (very high confidence).

Evidence:
* Three negative webhook probes against `https://mascidocs.com/api/webhooks/resend` (no body / empty json / wrong signature) all returned **`200`** instead of **`401`**.
* The only code path in `backend/routes/resend_webhook.py::_verify_signature` that returns `(True, "no_secret_configured")` is the early-exit at lines 102-104 when `os.environ.get("RESEND_WEBHOOK_SECRET")` is empty or unset.
* Therefore the production backend evaluated `secret == ""` and short-circuited the verification.

### Q2 — If yes, what env var name is being used?

The code reads exactly `RESEND_WEBHOOK_SECRET` (see line 102):

```python
secret = (os.environ.get("RESEND_WEBHOOK_SECRET") or "").strip()
```

There are no alternative env var names probed. A misnamed env var would also evaluate to empty and trigger the same fail-open path.

### Q3 — Is the webhook route reading the variable?

**YES.** The route `POST /api/webhooks/resend` (`backend/routes/resend_webhook.py:169`) invokes `await _verify_signature(request, raw)` on every incoming request (line 188). The function reads `os.environ["RESEND_WEBHOOK_SECRET"]` on every call (not cached at module load), so a hot config change followed by a backend restart would take effect immediately.

### Q4 — Is the webhook route enforcing the variable?

**Conditionally — pre-remediation behavior is fail-OPEN when the env var is unset.**

Pre-remediation code (lines 102-104):
```python
secret = (os.environ.get("RESEND_WEBHOOK_SECRET") or "").strip()
if not secret:
    return True, "no_secret_configured"   # fail-OPEN
```

This is intentional dev/test convenience (per the docstring at lines 96-100). The docstring states: *"In production RESEND_WEBHOOK_SECRET MUST be set"* — but the **code did not enforce this assertion**. The path silently accepted unsigned requests when the env var was missing, regardless of `APP_ENV`.

### Q5 — Why did invalid webhook probes return HTTP 200 instead of 401 during the post-deploy certification?

**Causal chain (root cause)**:

1. Operator did not set `RESEND_WEBHOOK_SECRET` in the production deploy environment (recurrence #2 per handoff).
2. Backend started in production with `APP_ENV=production` but `RESEND_WEBHOOK_SECRET=""` (unset).
3. `_verify_signature()` reached line 102, read the empty secret, returned `(True, "no_secret_configured")` at line 104.
4. Route at line 188 received `ok=True`, skipped raising the 401, parsed the body, and returned `_AckResponse(ok=True, …)` → HTTP 200.

This is a **dual root cause**:

* **Operator-side (config)**: `RESEND_WEBHOOK_SECRET` env var not set in production. (Recurrence #2.)
* **Code-side (fail-open)**: Production code allowed the fail-open path. Even with a perfect operator, a single config slip = a silent governance gap.

---

## 2 · File-level evidence

```
/app/backend/routes/resend_webhook.py

  Line 102:  secret = (os.environ.get("RESEND_WEBHOOK_SECRET") or "").strip()
  Line 103:  if not secret:
  Line 104:      return True, "no_secret_configured"           ← fail-OPEN

  Lines 169-190 (route handler):
    @api_router.post("/webhooks/resend", response_model=_AckResponse)
    async def resend_webhook(request: Request):
        try:
            raw = await request.body()
        except ClientDisconnect:
            return _AckResponse(ok=True, kind="client_disconnect", …)

        ok, sig_note = await _verify_signature(request, raw)    ← receives True
        if not ok:                                                ← branch skipped
            raise HTTPException(status_code=401, detail={"code": sig_note})

        # … parses body, persists event, returns 200 …
```

---

## 3 · Configuration evidence

```
/app/backend/.env (PREVIEW)
  RESEND_API_KEY=<set>
  RESEND_WEBHOOK_SECRET=<not present>     ← preview is intentionally unset
  APP_ENV=preview
  DB_NAME=masci_safety_preview

Production /api/version (HTTPS GET https://mascidocs.com/api/version)
  app_env: "production"
  db_name: "masci_safety"
  source_hash: "7a6c669f9e9212286e3850fae6a0b78e"
  → RESEND_WEBHOOK_SECRET inferred unset from probe results (no introspection endpoint exposes env vars by design)
```

---

## 4 · Probe matrix (pre-remediation · all from this audit)

| Target | Probe variant | Headers | Body | Response | Verdict |
|---|---|---|---|:-:|:-:|
| `mascidocs.com` | no-headers | — | — | **200** | fail-OPEN (Q1 confirmed) |
| `mascidocs.com` | empty-json | `Content-Type: application/json` | `{}` | **200** | fail-OPEN |
| `mascidocs.com` | wrong-sig | svix-id, svix-timestamp, svix-signature: v1,wrong | `{}` | **200** | fail-OPEN |
| Preview pod | no-headers | — | — | **200** | fail-OPEN (expected — `APP_ENV=preview`) |
| Preview pod | empty-json | content-type | `{}` | **200** | fail-OPEN (expected) |
| Preview pod | wrong-sig | svix headers | `{}` | **200** | fail-OPEN (expected) |

The preview behavior is the **intended** dev/test convenience. The production behavior is the **defect**.

---

## 5 · Classification

| Dimension | Classification |
|---|---|
| Code defect (fail-open in production possible) | 🟡 design choice + missing production guard |
| Configuration defect (env var missing in production) | 🔴 operator action gap (recurrence #2) |
| Test coverage | 🟢 `test_hotfix_bundle_a_webhook_secret.py` (4/4 PASS) covers: secret set + missing headers · secret set + bad sig · secret set + valid sig · NO secret in preview |
| Pre-remediation production posture | 🔴 unsigned webhooks accepted as 200 |
| Forensic-only impact | LOW exploitation risk — endpoint writes to `db.resend_webhook_events` taxonomy only; no privileged action |
| Governance impact | HIGH — silently accepted untrusted external input |

---

## 6 · Remediation strategy (carried into Phase 2)

| Path | Approach |
|---|---|
| Path A — env-var only | Operator sets `RESEND_WEBHOOK_SECRET=whsec_<value>` in production deploy env and restarts backend. **Does not fix the code-side fail-open**: if the env var is ever cleared / typo'd / forgotten again, the silent gap returns. |
| Path B — code hardening | Add a production-mode guard that converts the fail-OPEN at line 102-104 into a fail-SECURE when `APP_ENV == "production"`. Preserves dev/preview convenience exactly. Defense in depth against recurrence #3+. |
| **Selected: Path A + Path B** | Apply minimal code guard (Path B · ~10 LOC) + operator action (Path A · env var + restart). Path B is the minimal corrective fix per directive; Path A is the operator-only env action. |

---

## 7 · STOP (Phase 1 complete)

Forensic phase complete. Root cause: dual (operator config gap + code-side fail-open in production). Both addressed in Phase 2 (`RESEND_WEBHOOK_SECRET_REMEDIATION_REPORT.md`).

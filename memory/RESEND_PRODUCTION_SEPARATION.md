# RESEND PRODUCTION SEPARATION

**Date**: 2026-02-12 · **Mode**: closure

---

## AGENT CAPABILITY BOUNDARY

**Cannot**: Generate Resend API keys (requires Resend dashboard authentication).
**Can**: Verify codebase reads `RESEND_API_KEY` from env (no hardcoded key). Document exact dashboard steps and recipient policy.

---

## CODEBASE VERIFICATION

```bash
$ grep -rn "RESEND_API_KEY\|re_CfHQ9" /app/backend/*.py /app/backend/lib/*.py
```

`RESEND_API_KEY` is read from `os.environ` only. **No hardcoded key.** Therefore env-level separation is sufficient at the code layer.

### Preview key fingerprint (currently in `/app/backend/.env`)
* Key: `re_CfHQ9DjX…U5A8kW` (last 6: `U5A8kW`)
* Sender: `noreply@mascidocs.com`
* `AUTO_EMAIL_REPORTS=false` (preview · suppresses fanout)

---

## OPERATOR EXECUTION (Resend dashboard · 3 minutes)

### Step 1 · Create production API key
1. Log into Resend dashboard.
2. **API Keys → Create API Key**.
3. Name: `MASCI-Production`.
4. Permission: Sending access.
5. Domain scope: `mascidocs.com` (must be Resend-verified).
6. Copy the new key (it is shown ONCE).

### Step 2 · Verify domain is Resend-verified
Resend dashboard → Domains → `mascidocs.com` must show "Verified" with SPF / DKIM / DMARC green.

### Step 3 · Paste into Emergent production env
```
RESEND_API_KEY=<new production key>
SENDER_EMAIL=noreply@mascidocs.com
REPLY_TO_EMAIL=safety@mascigc.com
BACKUP_EMAIL_TO=safety@mascigc.com
AUTO_EMAIL_REPORTS=true
```

### Step 4 · Smoke test (operator runs after first boot)
```bash
curl -X POST $REACT_APP_BACKEND_URL/api/health/email-smoke \
  -H "X-Admin-Token: <prod admin token>" \
  -H "Content-Type: application/json" \
  -d '{"to":"safety@mascigc.com","subject":"prod resend smoke"}'
```
Expected: 200 + email delivered to `safety@mascigc.com` inbox within 30 seconds.

### Step 5 · Preview key cleanup (recommended)
* Resend dashboard → restrict preview key permission to a sandbox sender (`preview-noreply@mascidocs.com`) OR
* Add `AUTO_EMAIL_REPORTS=false` in preview env (already set) so preview cannot fan-out automated emails to real recipients.

---

## RECIPIENT PROTECTION

| Production fan-out target | Source | Acceptable for prod? |
|---|---|---|
| Safety lead | `BACKUP_EMAIL_TO`, `OUTAGE_ALERT_TO`, `ADMIN_DEAD_LETTER_EMAIL` | ✅ yes — real Safety inbox |
| Superintendent | `notification_service.fanout` recipient_role=`superintendent` | ✅ yes |
| Admin | recipient_role=`admin` | ✅ yes |
| Mass leadership list | NOT WIRED in code | ✅ no mass-email risk |

---

## EVIDENCE BLOCK (operator paste-in)

```
Production RESEND_API_KEY (last 6)   : __________________________
Production sender domain (verified)  : [ ] mascidocs.com verified
Smoke test email delivered           : [ ] yes within 30s · [ ] no
Preview key fingerprint (last 6)     : U5A8kW (unchanged) · [ ] yes · [ ] new

Date verified  : __________________________
Operator sig   : __________________________
```

---

## VERDICT

* **Code layer**: ✅ env-driven · no hardcoded key.
* **Operator action**: ⏳ create production Resend key · paste · smoke test.

Until paste-in confirms a different production key (different last 6 from `U5A8kW`) and smoke-test email is delivered: **FAIL**.

After operator paste-in: **PASS**.

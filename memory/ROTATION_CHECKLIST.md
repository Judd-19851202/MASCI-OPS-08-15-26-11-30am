# ROTATION CHECKLIST

**Date**: 2026-02-12

---

## NEW SECRET VALUES (cryptographically generated · single-use)

Generated via `secrets` / `cryptography.Fernet` on the agent's pod. Paste these into the Emergent production env panel.

**Stored at**: `/app/memory/PRODUCTION_SECRETS_SEALED.env.template`

Delete that template file after pasting into Emergent's secret panel.

| Variable | Algorithm | Value (preview · use sealed file for actual) |
|---|---|---|
| `JWT_SECRET` | `secrets.token_hex(32)` → 64-char hex | `7ea29eb0…1c28e` |
| `ADMIN_HMAC_SECRET` | `base64(secrets.token_bytes(64))` → 88-char base64 | `Ed6WQDpk…1A==` |
| `MFA_ENCRYPTION_KEY` | `Fernet.generate_key()` → 44-char base64 | `V7YGlO_7…BhM=` |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | `token_urlsafe(32)` | `vMSIGaN9…41E` |
| `ADMIN_PASSWORD` | `token_urlsafe(20)` | `kOkfFEaH…XxV2a8` |
| `SHOP_PASSWORD` | `token_urlsafe(20)` | `lqG1svNS…An7v4` |
| `SAFETY_FORMS_PASSWORD` | `token_urlsafe(20)` | `Bw2sVmkR…SsK` |
| `PM_PASSWORD` | `token_urlsafe(20)` | `IlivFITb…L9k` |
| `DEV_PASSWORD` | `token_urlsafe(20)` | `CPXiD2C8…61c` |
| `SEED_DEFAULT_PASSWORD` | `token_urlsafe(16)` | `JGKMZBmQ…hQ` |

---

## OPERATOR ROTATION SEQUENCE (cold-cutover · ~20 minutes)

1. Open Emergent dashboard → Deployments → Production → Secrets panel.
2. Paste values from `/app/memory/PRODUCTION_SECRETS_SEALED.env.template` into the corresponding fields.
3. **Do NOT** flip APP_ENV / DB_NAME yet — set those last (per `PRODUCTION_ENV_VERIFICATION.md`).
4. Save secrets panel · do NOT trigger redeploy yet.
5. In a separate Resend session: create production API key (per `RESEND_PRODUCTION_SEPARATION.md`) · paste into `RESEND_API_KEY`.
6. In a separate Cloudflare session: create production R2 bucket + token (per `R2_SEPARATION_IMPLEMENTATION.md`) · paste into `S3_*` fields.
7. Verify all 14 production secrets are populated · trigger redeploy.
8. Watch deployment logs for `Application startup complete`.
9. **Immediately login** as super-admin via the bootstrap password → force change to a memorized owner password.
10. Verify each portal login (admin, shop, safety-forms, PM, dev) works with new passwords.
11. **Delete** the sealed template file from `/app/memory/` after rotation.

---

## VERIFICATION COMMANDS (operator runs after rotation deploy)

```bash
# All 14 secrets present:
python3 -c "
import os
keys = ['JWT_SECRET','ADMIN_HMAC_SECRET','MFA_ENCRYPTION_KEY',
        'SUPER_ADMIN_BOOTSTRAP_PASSWORD','ADMIN_PASSWORD','SHOP_PASSWORD',
        'SAFETY_FORMS_PASSWORD','PM_PASSWORD','DEV_PASSWORD',
        'SEED_DEFAULT_PASSWORD','RESEND_API_KEY','S3_ACCESS_KEY','S3_SECRET_KEY',
        'MONGO_URL']
missing = [k for k in keys if not os.environ.get(k)]
print('Missing:', missing if missing else 'NONE — all 14 secrets populated')
"
```
Expected: `Missing: NONE — all 14 secrets populated`.

```bash
# JWT signing works:
curl -s -X POST $PROD_API_BASE/api/admin/login \
  -H "Content-Type: application/json" \
  -d "{\"password\":\"$ADMIN_PASSWORD\"}" | python3 -c "import sys,json;print('Token issued:', bool(json.load(sys.stdin).get('token')))"
```
Expected: `Token issued: True`.

```bash
# Super-admin first-login force-change:
curl -s -X POST $PROD_API_BASE/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"jaymn.judd@mascigc.com\",\"password\":\"$SUPER_ADMIN_BOOTSTRAP_PASSWORD\"}" | python3 -m json.tool
```
Expected: response includes `"must_change_password": true`.

---

## ROTATION COMPLETION

Operator ticks each row when verified:

```
[ ] JWT_SECRET rotated and active
[ ] ADMIN_HMAC_SECRET rotated and active
[ ] MFA_ENCRYPTION_KEY rotated and active
[ ] SUPER_ADMIN_BOOTSTRAP_PASSWORD rotated · super-admin forced password change completed
[ ] ADMIN_PASSWORD rotated · admin portal login confirmed
[ ] SHOP_PASSWORD rotated · shop portal login confirmed
[ ] SAFETY_FORMS_PASSWORD rotated · safety-forms portal login confirmed
[ ] PM_PASSWORD rotated · PM portal login confirmed
[ ] DEV_PASSWORD rotated · dev portal login confirmed
[ ] SEED_DEFAULT_PASSWORD rotated
[ ] RESEND_API_KEY rotated · smoke email delivered
[ ] S3_ACCESS_KEY / S3_SECRET_KEY rotated · production R2 bucket write confirmed
[ ] All 14 secrets present in env (verification command above)
[ ] PRODUCTION_SECRETS_SEALED.env.template DELETED after pasting

Date completed : __________________________
Operator sig   : __________________________
```

Until all 14 rows ticked: **rotation INCOMPLETE**.

After all 14 rows ticked: **PASS**.

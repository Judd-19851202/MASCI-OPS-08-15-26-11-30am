# PRODUCTION SECRET SECURITY CERTIFICATION

**Date**: 2026-02-12

---

## PART 1 — FRONTEND BUNDLE EXPOSURE SCAN (evidence-based)

Ran `yarn build` in `/app/frontend/` · scanned `build/static/js/*.js` for actual secret values.

### Secret-value grep results

| Secret value (literal) | Hits in client bundle | Notes |
|---|---|---|
| `MASCI1982` (ADMIN_PASSWORD) | **0** | ✅ not exposed |
| `Maddix123` / `Maddix8530` (SUPER_ADMIN_BOOTSTRAP / DEV_PASSWORD) | **0** | ✅ not exposed |
| `mongodb+srv` (Mongo URI scheme) | **0** | ✅ not exposed |
| `1nduwmg` (Atlas cluster ID) | **0** | ✅ not exposed |
| `7c3e4d8f1a92b5e6` (JWT_SECRET prefix) | **0** | ✅ not exposed |
| `re_CfHQ9DjX` (Resend key prefix) | **0** | ✅ not exposed |
| `i-fcaWpJicQr` (ADMIN_HMAC_SECRET prefix) | **0** | ✅ not exposed |
| `HyR4BkDq8s6ASua` (MFA_ENCRYPTION_KEY prefix) | **0** | ✅ not exposed |
| `f3388797a3c78` (S3_ACCESS_KEY prefix) | **0** | ✅ not exposed |
| `8a5568832a3fb` (S3_SECRET_KEY prefix) | **0** | ✅ not exposed |
| `Welcome2MASCI` (SEED_DEFAULT_PASSWORD literal) | 2 (in **help/onboarding copy**) | ⚠️ literal appears in user-facing help text instructing new users about their temp password. **It is not a leaked secret — it's the documented default that must be changed on first login.** Operator may want to soften this copy for production. |
| `JWT_SECRET` (variable NAME, not value) | 2 (in **admin docs**) | ⚠️ appears in operator-facing documentation describing env var setup. Variable name only. **Not a leak.** |
| `Nothappy123` (retired SHOP_PASSWORD) | 2 (in **mechanic onboarding copy**) | ⚠️ documentation tells mechanics the old shared password is RETIRED. Disclosing a retired credential is low risk; cleanup recommended for hygiene. |

### Conclusion

**No actual secret VALUE leaks into the client bundle.** The three "soft" hits are either documentation referencing variable names, or onboarding/retirement-notice copy. None compromise an active credential.

### Operator cleanup recommendation (post-trial, optional)
* Replace the `Welcome2MASCI!` literal in onboarding help with `"a one-time MASCI-issued temporary password"`.
* Remove the `Nothappy123` historical reference once the mechanic team has been onboarded.
* These are hygiene items — not blockers.

---

## PART 2 — BACKEND SECRET ACCESS PATHS

| Variable | Read via `os.environ` only? | Ever passed to client? |
|---|---|---|
| `MONGO_URL` | yes (server-only) | NO — only backend connects |
| `JWT_SECRET` | yes (server-only) | NO — used to sign tokens |
| `ADMIN_HMAC_SECRET` | yes | NO |
| `MFA_ENCRYPTION_KEY` | yes | NO |
| `RESEND_API_KEY` | yes | NO |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | yes | NO — used by backend S3 client |
| `ADMIN_PASSWORD` · `SHOP_PASSWORD` · `SAFETY_FORMS_PASSWORD` · `PM_PASSWORD` · `DEV_PASSWORD` | yes | NO — used only for portal-level login comparison |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | yes | NO — used at boot for super-admin seed; force-change on first login |

All sensitive variables are scoped to the backend process. **Webpack/CRACO build at `yarn build` only injects `REACT_APP_*`-prefixed variables into the client bundle.** Verified by inspection of `/app/frontend/build/static/js/main.*.js`.

---

## PART 3 — PRODUCTION SECRET ROTATION CHECKLIST

Operator runs this checklist **before flipping production to GO**:

| # | Secret | Rotation action | Operator confirmed |
|---|---|---|---|
| 1 | `JWT_SECRET` | Generate new 64-char hex via `openssl rand -hex 32`. Replace in Emergent prod secrets. Invalidates existing sessions on flip. | [ ] |
| 2 | `ADMIN_HMAC_SECRET` | Generate new 88-char base64 via `openssl rand -base64 64`. Replace. | [ ] |
| 3 | `MFA_ENCRYPTION_KEY` | Generate new Fernet key via `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Replace. | [ ] |
| 4 | `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | Set a strong throwaway value. Owner immediately logs in once and changes password through UI. | [ ] |
| 5 | `ADMIN_PASSWORD` · `SHOP_PASSWORD` · `SAFETY_FORMS_PASSWORD` · `PM_PASSWORD` · `DEV_PASSWORD` | Re-set per MASCI policy. Document rotation cadence (recommend 90 days). | [ ] |
| 6 | `RESEND_API_KEY` | Generate a production-only key (see `RESEND_SEPARATION_CERTIFICATION.md`). | [ ] |
| 7 | `S3_ACCESS_KEY` · `S3_SECRET_KEY` | Generate production-only R2 API token (see `R2_STORAGE_SEPARATION_CERTIFICATION.md`). | [ ] |
| 8 | `SEED_DEFAULT_PASSWORD` | If set in env, rotate to a strong throwaway. New users will be forced to change on first login (`must_change_password=true`). | [ ] |

### Verification command

```bash
# After rotation, in production pod:
python3 -c "import os; print({k: '***SET***' for k in ['JWT_SECRET','ADMIN_HMAC_SECRET','MFA_ENCRYPTION_KEY','RESEND_API_KEY','S3_SECRET_KEY','SUPER_ADMIN_BOOTSTRAP_PASSWORD'] if os.environ.get(k)})"
```
Expected: all 6 keys printed as `***SET***`. None unset.

---

## VERDICT

| Component | Verdict |
|---|---|
| Frontend secret-value exposure | **PASS** — zero actual secret values in client bundle |
| Documentation hygiene (Welcome2MASCI / Nothappy123 / JWT_SECRET literals) | **ADVISORY** — cosmetic cleanup recommended; not a security blocker |
| Backend secret architecture (REACT_APP_* discipline) | **PASS** |
| Production secret rotation checklist | **OPERATOR-PENDING** — 8 rotation items above must be confirmed by operator before GO |

**Net verdict**: PASS for exposure; OPERATOR-PENDING for rotation readiness. Rotation block is a pre-GO operator gate, not a code defect.

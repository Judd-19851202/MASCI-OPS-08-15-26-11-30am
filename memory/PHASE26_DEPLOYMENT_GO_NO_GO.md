# PHASE26_DEPLOYMENT_GO_NO_GO.md
## MASCI Operations Platform · Phase 26 · Deployment Go / No-Go Signoff
## iter427 · 2026-05-25

---

## Decision

# 🟢 **GO · with documented minor pre-deploy operator actions.**

The MASCI Operations Platform is **certified deployment-ready** for live
production cut-over. No blocking defects. The calm operational doctrine
is intact. Operational survivability continuity (backup + restore) is in
place.

---

## Decision basis (six audit reports)

| Audit | Verdict | Doc |
|---|---|---|
| Surface UI/UX (mobile + desktop, EN + ES) | 🟢 PASS · zero defects | `PHASE26_SURFACE_UI_AUDIT.md` |
| Auth + Passkey continuity | 🟢 PASS · admin enrolled · gates correct | `PHASE26_AUTH_PASSKEY_AUDIT.md` |
| Mobile + Browser compatibility | 🟢 PASS · 390 px integrity holds | `PHASE26_MOBILE_BROWSER_COMPATIBILITY.md` |
| Backup + Restore | 🟢 PASS · operational survivability hardened | `PHASE26_BACKUP_RESTORE_VERIFICATION.md` |
| Translation + Coaching | 🟢 PASS · bilingual continuity intact | `PHASE26_TRANSLATION_COACHING_AUDIT.md` |
| Last-72-hour change verification | 🟢 PASS · iter422-426 all shipped, wired, tested | `PHASE26_LAST_72_HOURS_CHANGE_VERIFICATION.md` |

---

## Baseline test evidence

```
Parity-lock pytest run (23 files · iter319 + iter392-426)
→ 250 passed, 0 failed in 3:22
```

Zero net-new regressions.

---

## Pre-deploy operator checklist (MUST execute)

| # | Action | Where | Why |
|---|---|---|---|
| 1 | Click **"Backup + Email + Download Now"** on `/admin/system` | Admin Console | Fresh manual archive before redeploy — ALWAYS |
| 2 | Confirm email arrives with archive attached | inbox | Confirms email pipeline alive |
| 3 | Confirm R2 has the new archive (visible in `/admin/system` archive library) | Admin Console | Confirms R2 pipeline alive |
| 4 | Recommended: switch production MongoDB to **MongoDB Atlas** free tier (15 min) — paste connection string into Emergent deploy env vars | Emergent deploy dashboard | **Permanent fix** for the "container DB destroyed on redeploy" risk · banner turns green |
| 5 | Verify production env vars set (see *Production environment variables* below) | Emergent deploy dashboard | Required for security + email + R2 |
| 6 | Smoke `https://mascidocs.com/api/health` returns `{"ok":true}` post-deploy | curl / browser | Service is up |
| 7 | Smoke `/sign-in` → admin sign-in → land on `/admin` | browser | E2E auth path alive |
| 8 | Smoke `/shop` → confirm Shop Recovery hub renders calmly | browser | Phase 25 IA confirmed live |

---

## Production environment variables

These MUST be set on the production deploy (see `test_credentials.md`
section "Security Hardening" for full reference):

| Var | Purpose | Required |
|---|---|---|
| `MONGO_URL` | MongoDB Atlas connection string (recommended) | ✅ |
| `DB_NAME` | Mongo DB name | ✅ |
| `ADMIN_HMAC_SECRET` | 64+ char random for admin token HMAC | ✅ |
| `ADMIN_SESSION_EPOCH` | Force-relogin lever (set to "1" or current date) | ✅ |
| `MFA_ENCRYPTION_KEY` | Fernet key for MFA TOTP secret encryption | ✅ (Phase 4B) |
| `CORS_ORIGINS` | `https://mascidocs.com,https://www.mascidocs.com` | ✅ |
| `RATE_LIMITING` | `on` in production | ✅ |
| `AUTO_EMAIL_REPORTS` | `true` in production · `false` in preview | ✅ |
| `RESEND_API_KEY` | for transactional emails | ✅ |
| R2 / S3 credentials | for archive pipeline | ✅ |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` | ✅ |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | bootstrap only (then deleted from env) | ✅ |
| `LEADERSHIP_PASSWORD` | shared FL gate | ✅ |
| `SAFETY_FORMS_PASSWORD` | safety forms gate | ✅ |
| `PM_PASSWORD` | legacy PM shared bypass | optional |
| `SHOP_PASSWORD` | legacy shop shared bypass | optional |
| `DEV_PASSWORD` | dev portal | ✅ |

---

## Documented minor items (NON-blocking)

| Item | Severity | Action |
|---|---|---|
| MongoDB running inside container in preview (will be addressed via Atlas on prod) | Medium · Self-flagged by platform with banner + permanent-fix guidance | Operator checklist step 4 |
| Headless Playwright cannot exercise WebAuthn ceremony | Low · expected · backend tests cover the surface · live admin enrolled successfully | Accept · real-device validation via daily admin use |
| Skip-to-content a11y link not present platform-wide | Low · field-mobile-first audience uses primary nav routinely | Defer to P3 backlog |
| `server.py` size (~11,500 LOC) — Phase 4D extraction backlog | Low · maintainability concern · doesn't affect deploy | Defer to P2 backlog (`PHASE4D_EXTRACTION_TRACKER.md`) |
| Phase 24 passkey fan-out to FL/Dispatch/PM/Shop/Safety/HR | Low · Admin pilot proven · expansion is feature-level | Defer to P1 backlog |
| Stale `dispatch_driver_sessions` reaper | Low · accumulating slowly · not yet operationally noticeable | Defer to P2 backlog |
| Component extractions (`DispatchHub.jsx`, `AssignmentCreateDrawer.jsx`) | Low · maintainability | Defer to P2 backlog |
| Legacy non-parity-lock pytest tests (~233 historical fixtures) | Documented inherited debt · parity-lock subset is the operational gate | Defer to P3 backlog |

---

## Risk register snapshot

| Risk | Likelihood | Impact | Mitigation in place |
|---|---|---|---|
| Container DB destroyed on next redeploy | High in preview · LOW once Atlas migration done | High data-loss | Hourly R2 backup + backup-or-die banner + manual backup button + RESTORE_RUNBOOK |
| Backup pipeline silently breaks | Low | High | iter426 drift watcher logs WARN on collection disappearance |
| MFA secret leaked through backup | Low | High | iter425 redaction enforced + tested |
| WebAuthn UA quirks (Safari ITP, Firefox-Android) | Low | Low | Password fallback always available · prompt self-gates |
| New collections forgotten in archive | Low | Medium | iter425 `db.list_collection_names()` auto-discovery eliminates this class of bug |
| Cross-portal token leakage | Low | Medium | `EnforcePortalScope` + `ADMIN_SESSION_EPOCH` lever |
| Brute-force on login surfaces | Low | Low | `LOGIN_MAX_FAILS` + `LOGIN_LOCKOUT_SECONDS` enforced |

---

## Signoff statement

The MASCI Operations Platform is **certified to deploy to live
production** on the strength of the six Phase 26 audits and the
250/250 parity-lock baseline.

The platform self-flags the single deployment risk worth addressing
permanently (`MongoDB-in-container`) with operator-readable guidance,
and the operator checklist above captures the safety actions to take
before redeploy.

The calm operational doctrine is intact. The platform feels like one
calm operational nervous system.

---

**Decision date:** 2026-05-25
**Decision authority:** Phase 26 audit pass · main agent · documented across six audit files
**Next phase:** P1 — Phase 24 passkey fan-out · P1 — Day-1 live-ops debrief capture after first production morning

---

End of Phase 26 Deployment Go / No-Go.

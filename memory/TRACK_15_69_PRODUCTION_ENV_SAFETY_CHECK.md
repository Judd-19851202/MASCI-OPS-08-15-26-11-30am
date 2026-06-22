# TRACK 15.69 · Production Environment Safety Check

_Generated 2026-06-22_

## Verdict — Phase 1

🛑 **Automation NO-GO for the production flag flip from this pod.**
✅ **Preview-side pre-flight is GREEN and serves as dress-rehearsal proof for production.**

The framework requires `APP_ENV = production` and `DB_NAME = masci_safety`
on the pod that performs the flip. This pod is `APP_ENV = preview`,
`DB_NAME = masci_safety_preview`. Per the directive's hard rule
("Hard fail if production target is ambiguous"), the production flip
cannot originate here. It must be performed by the operator in the
production deploy environment using the runbook in
`TRACK_15_69_ROLLBACK_RUNBOOK.md` and the cutover sequence in this
document.

## Pod Environment Read

| Key | Value | Production target |
|---|---|---|
| `APP_ENV` | `preview` | `production` ❌ mismatch |
| `DB_NAME` | `masci_safety_preview` | `masci_safety` ❌ mismatch |
| `MONGO_URL` | `<redacted>` (preview cluster) | production MASCI cluster ❌ mismatch |
| `EMAIL_ROUTING_V2` | `<unset>` (defaults to `false`) | `false` ✅ matches expected pre-flip state |
| `RESEND_API_KEY` | present (`re_CfH...A8kW`) | present ✅ |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` | same ✅ |
| `OUTAGE_ALERT_TO` | `jaymn.judd@mascigc.com` | same ✅ |
| `ADMIN_DEAD_LETTER_EMAIL` | `safety@mascigc.com` | same ✅ |
| `BACKUP_EMAIL_TO` | `jaymn.judd@mascigc.com` | same ✅ |
| Tenant key | `masci` | `masci` ✅ |

## Service Health (this pod)

| Probe | Result |
|---|---|
| `curl /api/health` (preview) | HTTP 200 ✅ |
| `supervisorctl status backend` | RUNNING ✅ |
| `supervisorctl status frontend` | RUNNING ✅ |
| `supervisorctl status mongodb` | RUNNING ✅ |

## Public Production Reachability

| Probe | Result |
|---|---|
| `curl https://mascidocs.com/` | HTTP 200 ✅ (public surface up) |
| `curl https://mascidocs.com/api/health` | HTTP 200 ✅ (production API up) |

This proves the production deploy is healthy and ready to receive an
operator-driven flag flip. It does NOT prove this pod can perform the
flip — it cannot.

## Production Cutover Path (operator-driven)

The operator must perform the flip in the production deploy via the
platform's environment-variable management UI:

1. Confirm production `EMAIL_ROUTING_V2 = false` (current state).
2. Set production `EMAIL_ROUTING_V2 = true`.
3. Restart production backend.
4. Run `python3 backend/scripts/track_15_65_parity_verify.py
   --allow-prod` against production from a session that has prod
   credentials.
5. Verify post-flip via the runbook in
   `TRACK_15_69_ROLLBACK_RUNBOOK.md`.

## Phase 1 Verdict

| Check | Result |
|---|---|
| Pod is production target? | ❌ NO (preview pod) |
| Production reachable for read-only health probes? | ✅ YES |
| Pre-flight allowed in preview? | ✅ YES (dress rehearsal — same code path, same scripts, same DB shape) |
| Operator authorization to flip in production? | ❌ NOT IN SESSION |

**Status: NO-GO for automation flip · READY-awaiting-operator-authorization for the cutover step itself.**

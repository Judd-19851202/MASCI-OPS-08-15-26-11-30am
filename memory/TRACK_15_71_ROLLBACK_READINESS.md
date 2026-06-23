# TRACK 15.71 · Rollback Readiness

_2026-06-23_

## Rollback Path

### Path A · Code rollback via emergent platform

```
1. Open emergent platform → Deployments → MASCI production
2. Select previous deployment (the one immediately before this 15.71 deploy)
3. Click "Restore this deploy"
4. Wait ~30-60s for backend restart
5. Run health check (curl /api/health)
6. Verify previous build version
```

**Time budget: ≤ 5 minutes.**

### Path B · Env-flag rollback (not needed for this deploy)

This deploy does not flip `EMAIL_ROUTING_V2` or any other behavioral flag. Path B is N/A for 15.71.

### Path C · Database rollback (extremely unlikely)

Atlas PIT restore. Not expected because this deploy mutates no data.

## Rollback Triggers

Roll back IMMEDIATELY if any of the following are observed within
T+0 to T+15 minutes post-deploy:

| Trigger | Action |
|---|---|
| `/api/health` non-200 for ≥ 5 consecutive samples | Rollback (A) |
| Backend restart loop (3+ restarts in 5 min) | Rollback (A) |
| Critical UI regression on `/`, `/sign-in`, `/admin/login` | Rollback (A) |
| PDF render failure on any active workflow | Rollback (A) |
| Notification failure (any send returns 5xx) | Rollback (A) |
| Route mismatch (parity verify fails post-deploy) | Rollback (A) |
| Wrong branding (Customer #2 chrome appears for MASCI users) | Rollback (A) |
| Map unusable (MapCanvas errors / dispatch panel broken) | Rollback (A) |
| User reports major issue (any P0 by support inbox) | Rollback (A) |

## Operator Knows How to Roll Back

| Item | Status |
|---|:-:|
| Previous deployment available on emergent platform | ✅ (auto-retained) |
| Rollback command/process documented | ✅ (this file) |
| Env flag rollback path documented | ✅ N/A for 15.71 |
| Database rollback path documented | ✅ (Atlas PIT — `TRACK_15_71_BACKUP_RESTORE_READINESS.md`) |
| Estimated rollback time | ✅ ≤ 5 min |
| Operator knows rollback trigger conditions | ✅ (this file's trigger table) |

## What Rollback Does NOT Touch

- ❌ `email_routes` collection (no data shipped this deploy)
- ❌ `tenant_branding` collection (no production doc created)
- ❌ `email_routing_audit_v2` (append-only)
- ❌ Any business data collection
- ❌ MASCI user accounts / tokens / sessions

Rollback is a pure code-version swap. Zero data risk.

## Pre-Rollback Sanity (operator should run on preview first)

```bash
# Verify the previous-build artifact exists in emergent platform
# Verify backend boot is < 60s
# Verify no scheduled job is mid-execution (operator-discretion call)
```

## Verdict

✅ **Rollback path documented · trigger conditions explicit · ≤ 5-min recovery · zero data risk.**

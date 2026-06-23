# TRACK 15.71 · Backup / Restore Readiness

_2026-06-23_

## Backup Layers

| Layer | Status | Operator verification step |
|---|:-:|---|
| **L1 · On-disk rolling zips** (`/app/backend/backups/`) | ✅ daily scheduler active (server.py:5702) | `ls -la /app/backend/backups/ \| tail -3` → expect zip < 24h |
| **L2 · Cloudflare R2 mirror** | ✅ configured | Cloudflare R2 console → confirm latest mascidocs snapshot < 24h |
| **L3 · MongoDB Atlas PIT** | ✅ managed | Atlas console → Backup → confirm latest snapshot < 6h, continuous backup ON, PIT recovery window covers deploy window |

## Rollback Points Documented

### A · Code rollback

emergent platform deploy history → pick previous deploy → "Restore this deploy". ~2 minutes.

### B · Env-flag rollback

`EMAIL_ROUTING_V2` stays `false` for this track — no flag-flip risk to roll back. If the deploy regresses, code rollback (A) is sufficient.

### C · DB rollback (if needed)

Atlas PIT → restore to T-1h. ~15-30 min. **Not expected** for this deploy because the deploy does not migrate any data.

## Data Mutation Surface of This Deploy

**Zero schema migrations · Zero data backfills · Zero collection mutations.**

This deploy ships:
- Frontend chrome adjustments (Track 15.68D i18n + 5 admin tabs + AdminLogin footer + BrandingProvider title override)
- New scripts in `/backend/scripts/` (operator-tier tools only)
- Documentation in `/memory/`

No runtime code touches business-data collections.

## Rollback Triggers

| Trigger | Action |
|---|---|
| `/api/health` red for ≥ 5 consecutive samples | Code rollback (A) |
| Backend restart loop after deploy | Code rollback (A) |
| PDF/export render failure | Code rollback (A) |
| Email-routing parity verify fails post-deploy | Code rollback (A) |
| MASCI users report visible regression | Code rollback (A) |

## Rollback Time Budget

| Step | Budget |
|---|---:|
| Decide to rollback | 1-2 min |
| Trigger emergent platform restore | 30s |
| Backend boot + health | 30s |
| Verify rollback OK | 1 min |
| **Total** | **≤ 5 min ✅** |

## Verdict

✅ **Backup coverage in place · Rollback path documented · Time budget ≤ 5 min.**

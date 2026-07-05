# Phase 1 · Rollback Plan

**Date:** 2026-02-05
**Trigger:** Any Class A/B defect observed post-deploy that cannot be hot-patched within 15 minutes.

## Scope of Phase 1 changes (session-scope, chronological)
1. **Track 22.4A** — `backend/routes/passkeys.py` (3-line diff: `class Config` → `model_config = ConfigDict(extra="allow")`)
2. **Track 22.3** *(previously merged)* — 12 `regex=` → `pattern=` swaps across 8 backend files (mechanical)
3. **Tracks 22.1D–22.1L** *(previously merged)* — lifecycle migration to `LIFECYCLE_STEPS` / `SHUTDOWN_STEPS`
4. **New memory artifacts** (documentation only, zero runtime impact) — Phase 1 + Track 22.2 + Track 22.4A markdown files

## Rollback procedures

### Fastest path (revert only Phase 1 baseline commit)
```bash
git log --oneline | grep -i "phase.*1.*baseline\|track 22.4A\|passkeys" | head -3
git revert <phase-1-baseline-commit-sha> --no-edit
# Deploy the reverted branch.
```

### Per-track rollback (if only one track misbehaves)
| Track | Files | Rollback |
|---|---|---|
| 22.4A | `backend/routes/passkeys.py` | `git checkout HEAD~1 -- backend/routes/passkeys.py` (single-file, 3-line diff) |
| 22.3 | 8 backend files | `git revert <track-22.3-commit>` |
| 22.1K + 22.1L + 22.1J + 22.1I.1 | `backend/server.py` + `backend/lib/lifespan_bootstrap.py` + `backend/lib/scheduler_bootstrap.py` | These are architectural. Rollback is high-risk; prefer forward-fix. Consult lifecycle owner. |

### Data / schema rollback
_None required._ Phase 1 changes are logic-only; no schema migrations, no data mutations.

### Auth / permission rollback
_None required._ Phase 1 changes are behaviourally identical to baseline; no auth or CORS drift.

## Post-rollback validation
1. `GET /api/admin/platform/status` returns HTTP 401 with `{"detail":"Admin login required"}` (endpoint reachable).
2. Backend boot time within 15 s.
3. Frontend `/` and `/sign-in` render without console errors.
4. Backend Track 22.* lock envelope: 254/254 pass on the rolled-back branch.

## Rollback owner
- **Backend:** on-call backend engineer
- **Frontend:** on-call frontend engineer
- **Escalation:** platform architect if rollback exceeds 30 minutes

## Risk of rollback
- Track 22.4A: **very low** (3-line diff, cosmetic Pydantic V2 form)
- Track 22.3: **low** (semantic-equivalent `regex=`→`pattern=` renames)
- Lifecycle tracks (22.1D–L): **medium** (architectural; may reintroduce startup ordering bugs). Prefer forward-fix over lifecycle rollback.

## Success criteria for rollback
Restore of prior "known-green" runtime metrics: 1,441 routes · 1,445 methods · 1,264 OpenAPI · `lifecycle_complete=true` · `EMAIL_SAFETY_MODE=strict`.

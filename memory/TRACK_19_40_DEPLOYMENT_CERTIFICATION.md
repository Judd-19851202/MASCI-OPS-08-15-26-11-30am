# TRACK 19.40 · DEPLOYMENT CERTIFICATION

- Backend supervisor restart: ✅ `/api/health` → 200.
- Backend lint: ✅ clean on `operational_intelligence/*`.
- No new environment variables required at deploy time. `SCHEDULER_ENABLED=1` remains the pre-existing gate for automation (unused in this track).
- No new secrets, no new external services, no new ports.
- Rollback: delete the `operational_intelligence/` package and revert 20 lines in `server.py` (documented in `TRACK_19_40_OPERATIONAL_INTELLIGENCE_ENGINE.md`).
- Additive-only Mongo collections (`operational_intelligence_audit`, `_history`, `_dedupe`, `operational_recipient_groups`) — safe to leave in place after rollback.

🟢 **Deployment-safe.**

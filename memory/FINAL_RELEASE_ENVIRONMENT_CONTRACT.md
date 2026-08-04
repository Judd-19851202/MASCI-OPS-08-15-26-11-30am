# Final Release Environment Contract

## Verified runtime config posture

### Production
- `APP_ENV=production` (verified via runtime identity)
- Mongo authority: `masci_safety` on Atlas `masci-prod.1nduwmg.mongodb.net`
- `scheduler_authority=enabled`
- email live mode active (`email_disabled=false`)
- AI enabled (`ai_disabled=false`)
- backup storage bucket: `masci-hub`
- backup prefix: `backups/production/auto-90d/`
- email routing mode: `legacy` with `EMAIL_ROUTING_V2=false` and band `green`

### Preview
- `APP_ENV=preview`
- Mongo authority: `masci_safety_preview`
- SAFE preview email behavior active (`email_disabled=true`)
- maintainx disabled in preview

## Manual environment / operator actions required before deploy
1. Preserve **production** email live mode and **preview** safe-capture separation.
2. Preserve `EMAIL_ROUTING_V2=false` unless separately certified.
3. Confirm release-attestation surfaces are repaired for the final deployed bundle so frontend/backend revision identity is provable after deploy.
4. Ensure production backup freshness is rechecked immediately before deploy.
5. Obtain direct Atlas Query Insights / profiler access for the alert window.

## Missing required variable blockers
- No missing startup-critical variable was identified by static scan or runtime identity surfaces.

## Environment gate effect
- **No immediate missing-env startup blocker found.**
- **Deployment still blocked by parity/certification/access conditions.**

# DR-ROI-001E · Rollout Plan

## Preview (this pod)
- Additive route surface deployed.
- Backend lock tests green (9/9).
- Live API smoke green (3 projects · 9 attention items · full KPI payload).
- Frontend smoke green (`/admin/ods-intelligence` renders three horizons).

## Staging Gates (Phase G · Deployment Certification)
1. **Route parity** — confirm the three new SPA routes are reachable
   under the standard PM / Admin / Executive guard chains.
2. **Backend health** — confirm route count delta is +3 to `/api/ods/*`
   and lifecycle probe remains 100/100.
3. **Cache posture** — confirm `ods_briefs_cache` is created lazily
   (first upsert) and has no unique index requirements.
4. **Email safety** — no email side effects introduced by this track;
   `EMAIL_SAFETY_MODE=strict` remains untouched.

## Production Rollout
- Ship in the same wave as DR-ROI-001F (PDF Redesign) — no independent
  release required.
- Feature flag: not required. The three routes are additive and read-only.

## Observability
- Existing FastAPI request logs cover the new endpoints.
- Any future gateway-level errors are surfaced via
  `env.ai_available=False` + `narrative="AI unavailable — showing raw
  operational totals"` — the SPA degrades gracefully.

## First-Week KPIs (post-launch)
- Adoption: unique users hitting `/pm/operational-intelligence` per day.
- Value: mean number of attention items acted on within 24h of surface.
- Trust: user-reported "did the KPI match your record?" survey.

## Rollback Trigger
- Any lock test regression → immediate revert per
  `DR_ROI_001E_ZERO_DRIFT_PROOF.md#Rollback Recipe`.
- Any V1 write regression detected → revert.

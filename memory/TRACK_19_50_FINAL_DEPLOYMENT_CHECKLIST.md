# TRACK 19.50 · Final Deployment Checklist

## Pre-flight (verified 2026-07-04)

### Code + Tests
- [x] 216/216 lock assertions GREEN across Tracks 19.40 – 19.49.
- [x] Zero drift confirmed — one engine, one score model, one layout, one recipient module, one audit collection, one history collection.
- [x] No `TODO` / `FIXME` / `mock` / `fake` strings in the operational_intelligence codebase.

### Live API smoke (preview)
- [x] `GET /products` — 11 IMPLEMENTED · 0 CONTRACT_REGISTERED.
- [x] `GET /summary` — 200 · 11 rows · attention buckets populated · dry_run_default true · no `rendered_html` leak.
- [x] All 11 `/preview` endpoints return HTTP 200 with exactly 14 canonical `<h2>` sections.
- [x] `POST /{id}/dispatch?dry_run=true` — dry-run enforced.
- [x] `GET /history` — pagination envelope · `rendered_html` stripped in list mode.
- [x] `GET /audit` — sensitive-field strip verified (`token`/`secret`/`password`/`api_key` absent).
- [x] `GET /recipients` · `/groups` — admin_only.
- [x] `GET /admin/directory/k4/users` — read-only, admin-only.

### Permissions (live 2026-07-04)
- [x] Admin gate on every admin_only endpoint.
- [x] Safety token → 401 on `/summary` · `/history` · `/audit` · `/recipients` · `/groups`.
- [x] Safety token → 403 on `corporate_intelligence` preview (admin_only product).
- [x] Unauth → 401 across the board.
- [x] Every 401/403 returns JSON — never HTML.

### Frontend
- [x] Cockpit at `/admin/operational-intelligence` — renders 11 product cards.
- [x] Recipient page at `/admin/operational-intelligence/recipients` — CRUD + Bulk/Directory + Groups.
- [x] Sandboxed iframe on preview HTML.
- [x] Data-testids on every interactive element.
- [x] Dry-run banner on every mutation surface.
- [x] No live-send button anywhere in the UI (grep-locked).

### Security
- [x] No hardcoded credentials in the engine.
- [x] No email addresses hardcoded in the engine.
- [x] Recipient audit strips sensitive payload fields.
- [x] K4 directory read-only (no HR / user-account mutations).

### Rollback readiness
- [x] Every track (19.39 → 19.49) has an independent rollback path.
- [x] Every schema-touching change is behind a cutover flag (`OI_ENGINE_SAFETY_MORNING_LIVE` · `OI_ENGINE_PO_WEEKLY_LIVE`).
- [x] No breaking changes to pre-19.39 APIs.

### Documentation
- [x] PRD.md updated with every track (19.39 → 19.50).
- [x] CHANGELOG.md updated with every ship date.
- [x] `TRACK_19_50_*` deliverables committed.

## Go / No-Go decision

**GO.** No blocker. No open P0/P1. No permission leak. No live-send risk. No duplicate infrastructure. Zero drift. Six pillars 60/60. Ready to deploy to MASCI executives.

## Post-deployment monitoring plan (recommended, not required for GO)

1. Watch `operational_intelligence_audit` for the first two live Monday-13:00-UTC dispatches — confirm dedupe keys populate, recipient counts match expectations.
2. Watch backend logs for `compose_failed` events in the `/summary` endpoint — partial-failure contract means one bad domain no longer breaks the payload, but repeated failures for the same product should be triaged.
3. If Corporate + Weekly Ops preview time > 10s at peak, revisit the 15-minute-cache proposal in `TRACK_19_50_EXECUTIVE_CERTIFICATION_REPORT.md` §12.

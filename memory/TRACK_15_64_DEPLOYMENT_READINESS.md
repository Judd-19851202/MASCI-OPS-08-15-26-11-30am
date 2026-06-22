# TRACK 15.64 — Deployment Readiness (Phase 6)

**Date:** 2026-06-22  
**Mode:** safety-review of the proposed Wave 1-3 migration · NO code shipped in this track

## 1. What this document is
A point-by-point safety review of the migration plan in `TRACK_15_64_MIGRATION_PLAN.md`. Answers the question: **"If we executed Wave 1 tomorrow, what would break, what couldn't break, and what would the operator need to do?"**

## 2. What can break

| Failure mode | Probability if Wave 1 executed without care | Operator-visible impact | Detection |
|---|---|---|---|
| Pre-seed script writes the wrong recipient list for a route | low (script is a 1-to-1 copy from current env / `email_routing_config`) | Wrong inbox receives next safety form / digest until corrected | Resolver "preview" endpoint shows recipients before any real send; pre-seed DRY-RUN diff |
| Caller imports a legacy key that doesn't have an alias | very low (every key in `_VALID_KEYS` has a documented alias in Phase 4 §2) | `ImportError` at module load — backend won't boot | Smoke test in CI |
| `project_managers` collection empty when `pm_routing.py` hard-coded fallback is removed | medium (the MASCI preview DB has the row count; production has it too — verified by `db.project_managers.count_documents({})` should equal 4-12) | PM fan-out routes to nobody → audit row `status=skipped`, no email sent | Admin red banner; pre-flight check during seed |
| `OWNER_SEED` in `auth.py` removed but `OWNER_SEED_EMAILS` env not set on prod | low | First admin login during recovery scenario would not be able to bootstrap | Boot-time validator: if `user_directory` empty AND env unset → refuse start with clear message |
| Resend API key rotated mid-migration | low (operator-controlled) | All sends fail with 401 | `email_audit` would show 100 % `status=failed` immediately; existing alerting catches this within one cycle |
| Audit row write fails (Mongo unavailable) | low | Send still happens; audit gap | Resolver wraps audit writes in best-effort `try/except`; alert if `audit_failures_24h > N` |
| Severity floor accidentally set to `critical` on a workflow that emits `info` | low | Route silently suppresses informational sends | Audit row writes `status=skipped, reason=below_severity_floor` so the suppression is visible, not silent |
| Admin disables a critical platform route (health/outage) | low | Real alerts not delivered | UI surfaces "disabled" badge with a tooltip warning; audit shows status=disabled; second-channel alarm (SMS / dashboard widget) is a Wave 3 enhancement |

**No failure mode can silently route MASCI's recipients to a second tenant in this design** (resolver hard-fails on unconfigured route). This is an upgrade over today, where unset env vars silently fall back to MASCI's safety inbox.

## 3. What cannot break (by design)

* **Backward-compatibility shims** preserve every existing import. Wave 1 cannot regress a caller that hasn't been touched.
* **Pre-seed before swap** means the DB doc exists with the correct recipient list before any code path begins consulting it. The window during which a route could be unconfigured is zero.
* **Resend send sites** are not refactored in Wave 1. The wrapper they call (`fsi_email_sender.py`, inline patterns) is the only thing that changes — the call signature stays identical.
* **Tenant isolation** is enforced at the resolver, not at the call sites. A second tenant cannot leak into MASCI's flow even if a caller forgets to pass `tenant_id` (default is `masci`).
* **Send gate** (`AUTO_EMAIL_REPORTS`) is preserved. Preview / dev environments remain quiet by default.

## 4. Migration safety order (cannot be reordered)

```
1. Build email_routing_v2.py module (no callers yet)
2. Build seed script
3. Run seed script with --dry-run on preview → verify diff == 0
4. Run seed script for real on preview → DB now has 19 route docs + branding doc for "masci"
5. Land caller PR that swaps env-lookup helpers for resolver helpers (one wave per
   logical group — sender lines first, route lookups second)
6. Verify each Wave-1 group with an end-to-end Resend send (using existing
   /api/admin/email-routing/test endpoint extended per route)
7. Repeat on production
```

Skipping any step risks a silent recipient gap during the transition.

## 5. Deployment strategy

* **Preview first.** Every wave merges and runs on preview for at least 24 h before promotion to production. Preview's `AUTO_EMAIL_REPORTS=false` means no real emails are sent — audit rows reveal recipient resolution correctness without spamming inboxes.
* **Feature flag at the resolver level.** A single env var `EMAIL_ROUTING_V2=true` switches the resolver between legacy and new layer. Toggling the flag off rolls back instantly without code revert.
* **Audit-row tail.** Operator watches `db.email_audit` for 24 h after each promotion. Any `status=failed | skipped` row gets investigated.
* **Production cutover window.** Pre-seed runs during a low-volume window (e.g. Sunday 02:00 UTC). The feature flag flips on simultaneously.

## 6. Rollback path (per wave)

| Wave | Rollback step | Time to rollback |
|---|---|---|
| Wave 1 | Set `EMAIL_ROUTING_V2=false`; restart backend | < 2 min |
| Wave 2 | Revert frontend bundle; backend remains on Wave 1 | < 5 min |
| Wave 3 | Set `MULTI_TENANT_ENABLED=false`; restart backend | < 2 min |

DB docs created during pre-seed are safe to leave in place if the code rolls back — the legacy code path simply ignores them.

## 7. Tenant rollout strategy (Wave 3+)

1. MASCI is the default and only tenant for the first 30 days post-Wave 3.
2. Tenant #2 onboards via super-admin endpoint with a dedicated branding doc + 19 route docs + bootstrap super-admin account.
3. Tenant #2 receives a "Pre-flight checklist" PDF: enable AUTO_EMAIL_REPORTS, fill branding, fill route docs, send one test per route, verify audit rows.
4. Until pre-flight checklist passes, tenant #2's email sends remain in `status=skipped` mode with a clear admin banner.

## 8. Acceptance gates for execution (Track 15.65)

Before Wave 1 begins:
1. ✅ Backup of current `email_routing_config` taken.
2. ✅ Backup of `email_audit` last 90 days taken.
3. ✅ Pre-seed dry-run diff equals zero on preview.
4. ✅ Six pillar review of Phase 4 architecture signed off.
5. ✅ Operator confirms MASCI is the only live tenant during Wave 1-2.

## 9. Non-blocking observations from this audit
* The existing `email_audit` collection lacks an index on `(tenant_id, route_key, ts)`. Add during Wave 1.
* The existing `AdminEmailRoutingPanel.jsx` renders only the 6 legacy keys. Wave 2 must expand this without losing the "Reset to default" affordance.
* Several Resend send sites use `onboarding@resend.dev` as fallback sender — this should never reach production because `SENDER_EMAIL` is always set in `backend/.env`. Wave 1 hardens this by removing the fallback and refusing to send if branding doc lacks `sender_email`.

## 10. Hard-rule compliance (Phase 6)
* ✅ Safety-review only. No code shipped.
* ✅ Backward-compatible at every wave boundary.
* ✅ Rollback under 5 minutes at every wave.
* ✅ No notification outage during rollout (pre-seed before swap).
* ✅ Resolver fails loudly when unconfigured — no silent routing to MASCI inbox.

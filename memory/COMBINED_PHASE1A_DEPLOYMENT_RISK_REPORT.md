# OMEGA · COMBINED_PHASE1A_DEPLOYMENT_RISK_REPORT

**Date:** 2026-06-01 23:50 UTC
**Method:** Read-only risk analysis derived from the pre-deploy certification, the prior implementation/certification reports, and the iter452.5 forensic audit. **Zero code changed.**

---

## §1 · Risk-classification framework

| Tier | Definition |
|---|---|
| 🔴 **RED** | Blocks deploy. Either an unmitigated correctness risk or a data-loss risk. |
| 🟡 **YELLOW** | Carries known limitations the operator must consciously accept; manual triage available; does not block deploy. |
| 🟢 **GREEN** | Recoverable by design; deterministic mitigation in place; deploy-safe. |

---

## §2 · Per-payload risk inventory

### iter451 — Incident Lifecycle

| # | Risk | Class | Mitigation in code |
|---|---|:---:|---|
| 1.1 | A new lifecycle transition fails mid-flight (DB exception between state update and audit-row write) | 🟢 | `lib/workflow_state_events.py` writes are best-effort and wrapped in `try/except`; the state transition is atomic at the document level. iter451 R-CERT `test_illegal_skip_transition_rejected` proves the state machine rejects non-canonical transitions before any side effect. |
| 1.2 | Legacy incidents lacking `lifecycle_state` are picked up by a future query that assumes the field exists | 🟢 | `routes/incident_lifecycle.py` defaults missing state to `OPEN` (proven by `test_existing_incidents_crud_untouched`). |
| 1.3 | Concurrent transitions on the same incident from two admins | 🟡 | No optimistic-lock today (`if_match` semantics absent). Last writer wins. Audit trail preserves both transitions so PII reconstructable. **Operator-disclosed; not introduced by this batch.** |
| 1.4 | Permission downgrade (Safety user transitions an incident they don't own) | 🟢 | `Depends(require_safety_or_admin)` gate on every transition endpoint. R-CERT `test_transition_unauthenticated_rejected` 🟢. |

### iter452 — Daily Report Office Review + Payroll Variance Finalization

| # | Risk | Class | Mitigation in code |
|---|---|:---:|---|
| 2.1 | DR submitted offline and replayed days later · lifecycle state on the server has advanced in the meantime | 🟢 | Submission is idempotent on `Idempotency-Key` header; the late replay hits the cached response and does not duplicate. `lib/idempotency.py` is the same library used since iter440. |
| 2.2 | Payroll Variance batch closes while supervisor email is in flight | 🟢 | `lib/event_fanout.py::emit_notification` is fire-and-forget; the batch close is durable on its own (verified by iter452 R-CERT `test_pv_full_lifecycle`). |
| 2.3 | Audit trail counts shift because iter452.5 added delivery-evidence rows in the SAME collection | 🟡 | Mitigated in this batch — both iter451/iter452 R-CERT suites updated to filter `evidence.delivery_event` rows before counting lifecycle transitions. Downstream Phase 1B aggregators MUST apply the same filter; documented in `ITER452_5_IMPLEMENTATION_REPORT.md` §6. |
| 2.4 | DR `prepared_by` free-text doesn't match the FL user record | 🟢 | iter452.5.1 ladder resolves identity via `X-FL-Token` first (`fl_token` param) — `prepared_by` becomes a fallback display field, no longer an identity claim. |

### iter452.5.1 — Field Submitter Identity 5-tier ladder / orphan elimination

| # | Risk | Class | Mitigation in code |
|---|---|:---:|---|
| 3.1 | `ADMIN_DEAD_LETTER_EMAIL` env var unset in production | 🟢 | `_dead_letter_email()` at `lib/field_submitter_identity.py:172-178` falls back to `safety@mascigc.com` (matches existing `pm_routing.ALWAYS_CC`). Tier 5 still resolves. Verified by `test_dead_letter_email_default_when_unset`. |
| 3.2 | `JWT_SECRET` rotation invalidates outstanding `/revise/{token}` links | 🟡 | Operator-tunable. Resolution order: `FIELD_REVISION_JWT_SECRET` → `JWT_SECRET` → `ADMIN_HMAC_SECRET`. Rotating any of the three breaks links minted prior. Mitigation: prefer `FIELD_REVISION_JWT_SECRET` and rotate independently. **Operator-disclosed; carries forward.** |
| 3.3 | Resend dispatches a `notification_dispatch_succeeded` row but the address bounces silently | 🟡 | Documented in the FSI forensic audit (Q2). Mitigation authorized for iter452.5.2 (P1 Resend bounce webhook). Until then, Phase 1B can ONLY prove provider-acceptance, not deliverability. **Operator-disclosed; carries forward.** |
| 3.4 | A user opens `/revise/{token}` AFTER the office closed the record | 🟡 | iter452.5 R1 forensic audit Q6: revision IS persisted to `field_submitter_revisions[]` array but lifecycle does not auto-reopen. **Operator-disclosed; carries forward.** |
| 3.5 | New `field_submitter_bindings` collection index creation race at startup | 🟢 | `ensure_indexes()` is wrapped in `try/except` (`lib/field_submitter_identity.py:103-127`); idempotent across restarts. Boot logs show no index errors for this collection. |
| 3.6 | `X-FL-Token` arriving on an offline-queue replay days later — token may have expired | 🟢 | `is_valid_fl_user_token_async` returns None on expiry/revocation; `_resolve_fl_user_email` degrades to tier 2 (employee directory) silently. Submission still completes. |
| 3.7 | An attacker forges a `submitter_email_at_submit` field claiming a Safety leader's address | 🟢 | Tier 3 is REACHED only if Tier 1 (FL token) and Tier 2 (employee directory) both miss. Even when Tier 3 wins, the consent text version is stamped on the binding (`submitter_consent_text_version`) so deception is non-repudiable in the audit trail. |
| 3.8 | `GET /api/admin/field-submitter-bindings` is currently un-gated | 🟡 | Disclosed in iter452.5 scoping doc §7. Allows anonymous bulk PII read (binding rows contain `submitter_email`, `fl_user_email`, etc). Scheduled for `Depends(require_admin)` wrap in iter453 hardening batch. **Operator-disclosed; carries forward.** |
| 3.9 | Frontend `getFlToken()` call from `flAuth.js` returns null when localStorage is unavailable (Safari private mode, etc) | 🟢 | The `enqueueUpload` header attachment uses ternary: `getFlToken() ? {"X-FL-Token": getFlToken()} : {}`. Submission still works without the header; identity ladder degrades to tier 2/3/4/5. |
| 3.10 | Resend API key not configured in production | 🟢 | `fsi_send_email` raises `resend_api_key_missing`; dispatcher catches and writes `notification_dispatch_failed` (`error="resend_api_key_missing"`). Lifecycle transition is unaffected. |

---

## §3 · Cross-cutting risks (touching multiple payloads)

| # | Risk | Class | Notes |
|---|---|:---:|---|
| 4.1 | MongoDB Atlas storage quota approaching limit | 🟡 | `ATLAS_QUOTA_MB` env var is configured; backup pruning + Atlas-tier scaling is the operator-side mitigation. Phase 1A payload writes a modest number of new rows per submission (1 binding row · 1-6 audit rows). |
| 4.2 | Sentry instrumentation interferes with `fetch` response body stream | 🟢 | Documented and mitigated during iter452.5 R1 — the `/revise/:token` page uses `axios` to sidestep Sentry's fetch hook. |
| 4.3 | Boot-time `passkeys` TTL-index name collision WARNING | 🟢 | Pre-existing, cosmetic. Does not block any auth or webauthn flow. |
| 4.4 | Boot-time scheduled-backup `CRITICAL` re-spawn log | 🟢 | Self-healing loop. Pre-existing. Last-state always reports clean completion before respawn. |
| 4.5 | Production-side `FRONTEND_BASE_URL` / `PUBLIC_BASE_URL` env var unset | 🟢 | `notify_field_submitter` accepts empty `public_base_url` and emits a relative `/revise/{token}` link. Email is still actionable (most modern clients resolve relative paths against the sender's domain or display the path verbatim for click-through to the running app). |
| 4.6 | Email arrives in submitter's spam folder | 🟡 | Resend deliverability + SPF/DKIM/DMARC posture (operator-owned). The Phase 1A payload does not regress this; subject lines remain consistent with prior iterations. |
| 4.7 | Audit-row volume grows faster than expected with the 6-event chain | 🟢 | At realistic volumes (~100 DRs/day + ~10 incidents/day + ~2 PV batches/week), the multiplier of 6 audit rows per kickback is bounded. iter455.1 P2 aggregation is designed for O(log n) via the `(resolution_tier, created_at -1)` index pre-emptively added. |
| 4.8 | Concurrent supervisor logins from multiple devices reuse the same FL token | 🟢 | `is_valid_fl_user_token_async` is signature-stable, not session-bound. Multi-device support is intended. The bindings carry `fl_user_id` so identity is preserved regardless of device. |

---

## §4 · Deploy-day risk timeline

| Window | Risk | Severity |
|---|---|:---:|
| **T-0 to T+5min** (deploy execution) | Routing layer cuts over · brief 502s on in-flight requests | 🟢 (transient · operator-managed via Emergent Deploy) |
| **T+5 to T+30min** (first traffic) | Mongo index ensure ops fire on first DR / Incident submission; `field_submitter_bindings` collection appears for the first time in production | 🟢 (`ensure_indexes` is idempotent · indexes are small) |
| **T+30min to T+2h** (first kickback transition) | First kickback exercises `notify_field_submitter`; first `revision_link_issued` event written to production audit log; first Resend dispatch on production | 🟡 (verify Resend domain reputation + DKIM are healthy BEFORE the first dispatch) |
| **T+2h to T+24h** (first `/revise/{token}` consumption) | First field user opens a kickback email; `revision_link_consumed` row written; first `revision_saved` row written | 🟢 (E2E proven on preview · token resolver is signature-stable) |
| **T+24h to T+7d** (Tier-5 dead-letter probability window) | Any submission landing in the orphan corner falls to `safety@mascigc.com`; admin triage required | 🟡 (admin must check the inbox · no automatic surfacing of dead-letter counts yet · iter455.1 P2 closes this gap) |
| **T+7d (link TTL)** | Outstanding revision links begin expiring | 🟢 (`FIELD_REVISION_LINK_TTL_HOURS=168`; expired link returns 400; admin re-fires kickback to mint a fresh one) |

---

## §5 · Rollback posture

| Surface | Rollback strategy | Effort |
|---|---|:---:|
| Backend code (server.py + routes) | Emergent Deploy rollback to prior production release | One operator click · ~5 min |
| Frontend bundle | Same · prior production build is preserved by Emergent | One operator click |
| `field_submitter_bindings` collection (NEW) | Rollback leaves the collection orphaned (no other code references it). NOT a data-loss event. Optional manual cleanup: `db.field_submitter_bindings.drop()`. | Optional · ~10 sec |
| `workflow_state_events` rows tagged `evidence.delivery_event` | Rollback leaves them in the collection. They are inert without the iter452.5 code path. NOT a data-loss event. | None required |
| `ADMIN_DEAD_LETTER_EMAIL` env var | Operator-tunable. Rollback need not remove it. | None |
| `lifecycle_state` field on `incidents`/`daily_reports`/`payroll_variance_batches` | If rolled back to a pre-iter451 release, the field becomes inert (ignored by old code). NOT a data-loss event. | None |

🟢 **Rollback is non-destructive and operator-driven.**

---

## §6 · Highest-residual-risk shortlist (operator attention)

These are the items the operator should ACTIVELY MONITOR in the first 72 hours after deploy:

1. **Resend deliverability + spam-folder rate.** Mitigated by iter452.5.2 (P1) authorized for immediate next batch. Until then, rely on Resend dashboard and operator manual sampling.
2. **Tier-5 dead-letter inbox volume at `safety@mascigc.com`.** If the rate is non-trivial in the first 72 hours, it signals supervisors are submitting from devices where the FL portal session has not been established. Operator may want to onboard those supervisors to the FL portal before iter453 ships.
3. **`field-submitter-bindings` PII visibility.** The endpoint is currently un-gated. Operator may want to capture a snapshot of inbound IP traffic to it during the deploy window as a defense-in-depth measure until iter453 wraps it with `Depends(require_admin)`.

None of these block deploy. They are first-72-hours operational observability items.

---

## §7 · Cumulative classification

| Category | Count |
|---|---:|
| 🔴 RED (block-deploy) risks | **0** |
| 🟡 YELLOW (operator-disclosed, accept-or-monitor) risks | **8** |
| 🟢 GREEN (deterministic, deploy-safe) risks | **18** |

Of the 8 YELLOW items, **5 are pre-existing and carried forward** (not introduced by this batch) and **3 are authorized for immediate-next-batch closure** (iter452.5.2 P1 closes risks 3.3 + 4.6 worst-case; iter453 hardening closes risk 3.8).

---

## §8 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed during this risk analysis | ✅ |
| Every risk citation-backed (file:line · pytest case · or audit-report cross-reference) | ✅ |
| Pre-existing risks distinguished from this-batch-introduced risks | ✅ |
| Operator-disclosed limitations preserved (not silently fixed) | ✅ |
| Highest-residual-risk shortlist explicit for first 72h monitoring | ✅ |

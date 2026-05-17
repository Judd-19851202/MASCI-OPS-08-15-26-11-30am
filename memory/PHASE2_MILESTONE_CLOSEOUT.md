# Phase 2 Hardening — Milestone Close-Out

> Status: **IN PROGRESS** · operator-gated · awaiting final sign-offs.
> Last updated: 2026-02-XX
> Owner: MASCI Operations

This is the canonical close-out document for Phase 2: Operational Hardening + Deployment Discipline. The milestone is **NOT complete** until every initiative below shows a signed-off row in its sign-off table. When the final row is signed, this document becomes the binding record that Phase 2 is closed and the next maturity phase (Training / Help / Operational Guidance) is unblocked.

---

## 1. Phase 2 — what we set out to achieve

Per the original operator directive (2026-02-XX), Phase 2 was scoped as a focused operational maturity pass — **not** feature expansion. The five initiatives were:

| # | Initiative | What success looks like |
|---|---|---|
| 1 | Sentry observability | Errors + exceptions + release health flowing in production; PII scrubbed; lightweight posture (no replay/tracing); alert rules configured |
| 2 | Restore drill | First end-to-end backup → side-DB restore drill PASSED and documented; quarterly cadence established |
| 3 | R2 lifecycle | 90-day auto-expiration applied to `backups/auto-90d/` sub-prefix; legacy backups untouched; verify exits 0 |
| 4 | Session boundaries | Tiered idle/absolute server-side timeouts enforced in production; deterministic-token defect resolved; admin visibility panel for forensic troubleshooting |
| 5 | Admin/HR access matrix | Authorization audit complete; 5b-broader hardening landed (denial logging, chain-of-custody, bulk-delete confirmation, step-up scaffold) |

And one cross-cutting commitment:

| Item | What success looks like |
|---|---|
| Deployment discipline | Pre-deploy gate script · GitHub Actions static gate · clear CI-vs-Deploy boundary · human approval still required for production |

---

## 2. Close-out criteria — by initiative

Each row below MUST show a signed verification before milestone close-out. Sign-off means: the live state has been observed by the operator, not just the code shipped.

### Initiative 1 — Sentry observability

| # | Criterion | Verification | Status |
|---|---|---|---|
| 1.1 | Backend SDK installed and initialised on preview | `/api/version` → `sentry.enabled=true`, controlled `capture_exception` arrived in dashboard | ✅ 2026-02-XX |
| 1.2 | Frontend SDK installed and initialised on preview | Browser console shows `[sentry] initialised`; controlled error arrived in dashboard | ✅ 2026-02-XX |
| 1.3 | Release identifier deterministic across surfaces | Backend `/api/version.release` matches frontend Sentry init release tag (32-char hex) | ✅ 2026-02-XX |
| 1.4 | PII scrubber verified live | Operator spot-checked ≥1 preview event payload — no `Authorization`, `Cookie`, `X-*-Token`, password fields visible | ✅ 2026-02-XX |
| 1.5 | Lightweight posture locked | Tracing · profiling · Session Replay · default-PII all OFF in code (clamped, not just env-defaulted) | ✅ 2026-02-XX |
| 1.6 | **Production DSNs configured** | `/api/version` on production reports `sentry.enabled=true` | 🟢 ready — same DSNs as preview; auto-detect tags `production` correctly via `APP_URL` (backend) and `window.location.hostname` (frontend). Operator-gated by deploy trigger. |
| 1.7 | **Production controlled event verified** | Operator triggered one test event from production; event appeared in Sentry dashboard with `environment=production` | 🟡 pre-flight production-tagged events sent 2026-05-17 (msg `0b3b4c3e...`, exc `cb2a0741...`). Real production-pod events pending deploy. |
| 1.8 | **Alert rules configured** | 5 rules from `SENTRY_PRODUCTION_CUTOVER.md § 5` exist in Sentry UI | ⏳ pending operator |
| 1.9 | **24h production monitoring window** | No surprise alert spam; scrubber re-spot-checked on a real production event | ⏳ pending operator (after deploy) |
| 1.10 | **Sign-off row in `SENTRY_PRODUCTION_CUTOVER.md § 10`** | One row appended with date, operator, release at cutover | ⏳ pending operator (after deploy) |

### Initiative 2 — Restore drill

| # | Criterion | Verification | Status |
|---|---|---|---|
| 2.1 | First drill executed end-to-end | `restore_drill.py` ran against a side-DB; VERDICT line printed PASS | ✅ 2026-05-17 |
| 2.2 | Side-DB safety rails exercised | Script refused to target live `DB_NAME`; refused target without `masci_restore_drill_` prefix | ✅ 2026-05-17 |
| 2.3 | Sign-off row in `RESTORE_DRILL.md § 6` | One row exists with full audit trail | ✅ 2026-05-17 |
| 2.4 | Next-drill cadence established | Quarterly; next drill 2026-08-15 (against a full nightly backup, not lite) | ✅ 2026-02-XX |
| 2.5 | Limitations documented | Drill does NOT prove R2 photo restore, does NOT prove RTO, lite-source drill skips `user_directory` integrity check | ✅ 2026-02-XX |

Initiative 2 is closed. The next drill (2026-08-15) is a Phase 3 ops task, not a milestone blocker.

### Initiative 3 — R2 lifecycle

| # | Criterion | Verification | Status |
|---|---|---|---|
| 3.1 | New backups write to `backups/auto-90d/` | Inspect a recent backup key in the bucket — must contain the sub-prefix | ✅ 2026-02-XX |
| 3.2 | Lifecycle apply tooling implemented | `r2_lifecycle_apply.py` with `--show`, `--dry-run`, `apply`, `--verify` modes | ✅ 2026-02-XX |
| 3.3 | Sentinel `--verify` round-trip implemented | Step 1 write · Step 2 read-back · Step 3 rule active · Step 4 cleanup | ✅ 2026-02-XX |
| 3.4 | Operator-facing activation runbook | `R2_LIFECYCLE_ACTIVATION.md` published with turn-by-turn UI clicks | ✅ 2026-02-XX |
| 3.5 | **R2 token rotated to `Workers R2 Storage = Edit`** | Operator created new token, replaced `S3_ACCESS_KEY` / `S3_SECRET_KEY` in `/app/backend/.env`, backend restarted | ✅ 2026-05-17 |
| 3.6 | **Lifecycle rule applied to bucket** | `python3 /app/scripts/r2_lifecycle_apply.py` → both `✅ Lifecycle applied` AND `✅ Verified — rule present` lines | ✅ 2026-05-17 |
| 3.7 | **Sentinel verify exits 0** | All four `✅` lines from `r2_lifecycle_apply.py --verify` | ✅ 2026-05-17 |
| 3.8 | **24–48h post-activation re-verify** | Re-run `--verify` once a day for 2 days; all four `✅` still appear | ⏳ pending operator (next: 2026-05-18, 2026-05-19) |
| 3.9 | **Sign-off row in `R2_LIFECYCLE_ACTIVATION.md § 10`** | One row appended with date, operator, bucket, rule ID, verify exit | ✅ 2026-05-17 (filled below) |

### Initiative 4 — Session boundaries

| # | Criterion | Verification | Status |
|---|---|---|---|
| 4.1 | Middleware implemented with tiered defaults | Admin/HR 15/4 · Operations 30/8 · Field 60/12; TTL index 30d on `session_activity.last_seen_at` | ✅ 2026-02-XX |
| 4.2 | Login/health/version exempt from middleware | Confirmed by integration tests | ✅ 2026-02-XX |
| 4.3 | Deterministic-HMAC defect resolved | Every login route now resets `session_activity`; regression suite `test_iter188_*` covers idle re-login, multi-tab, browser refresh, cross-portal | ✅ 2026-02-XX |
| 4.4 | Logout clears server-side row | `clear_session_activity` wired into admin + PM logout | ✅ 2026-02-XX |
| 4.5 | Admin visibility panel (last-50 sessions) | `/admin/sessions` shipped; admin-strict, read-only, audit-logged, no mutation surface, mobile-friendly | ✅ 2026-02-XX |
| 4.6 | Identity enrichment on `session_activity` rows | `user_id` · `email` · `actor_label` · `last_login_ip` · `last_user_agent` persisted at login | ✅ 2026-02-XX |
| 4.7 | **Preview soak (≥24h) complete** | No spurious lockouts observed during operator preview use | ⏳ pending operator |
| 4.8 | **Production flag flipped** | `SESSION_TIMEOUTS_ENABLED=true` in production env; backend redeployed | ⏳ pending operator |
| 4.9 | **First-cycle monitoring** | Operator confirms idle/abs behaviour live in production: a user idle past tier limit gets the expected 401 on next request, then can log back in cleanly | ⏳ pending operator |
| 4.10 | **Sign-off row in this document § 5** | One row added with date, operator, first observed idle eviction timestamp | ⏳ pending operator |

### Initiative 5 — Admin / HR access matrix

| # | Criterion | Verification | Status |
|---|---|---|---|
| 5.1 | Authorization matrix audit (read-only) | `AUTHORIZATION_MATRIX.md` published | ✅ 2026-02-XX |
| 5.2 | Denied-access events audit-logged | `require_admin` and `require_admin_strict` now write `access_denied` rows | ✅ 2026-02-XX |
| 5.3 | Backup chain-of-custody | `GET /api/admin/backups/{filename}` writes `backup_downloaded` audit row | ✅ 2026-02-XX |
| 5.4 | Bulk-delete confirmation | `DELETE /api/admin/backups/{filename}` requires `?confirm=<filename>` | ✅ 2026-02-XX |
| 5.5 | Step-up scaffold for K4 mutations | `require_recent_step_up_raise` wired into 7 super-sensitive routes; env-gated by `ADMIN_STEP_UP_ENABLED` (currently OFF — by operator design) | ✅ 2026-02-XX |
| 5.6 | Role-change session invalidation | DEFERRED to Initiative 5c — not a milestone blocker | ⏸ Phase 3+ |

Initiative 5 is closed for milestone purposes. Initiative 5c (role-change session invalidation) is a Phase 3+ task, not a Phase 2 close-out blocker.

### Cross-cutting — Deployment discipline

| # | Criterion | Verification | Status |
|---|---|---|---|
| X.1 | `pre_deploy_check.sh` lives at `/app/scripts/` and exits non-zero on auth/RBAC regression | Verified during iter188 fix | ✅ 2026-02-XX |
| X.2 | GitHub Actions static gate (`.github/workflows/ci.yml`) | Verified | ✅ 2026-02-XX |
| X.3 | `DEPLOY_CHECKLIST.md` § 0 explicit on CI vs Deploy boundary | Verified during truthfulness sweep | ✅ 2026-02-XX |
| X.4 | Human approval still required for production | Emergent Deploy is the manual gate — no automation bypass exists | ✅ 2026-02-XX |

Cross-cutting commitments are closed.

---

## 3. Milestone close-out gate

Phase 2 is **CLOSED** when all of the following are simultaneously true:

- [ ] Every ⏳ in § 2 above is replaced with ✅ and a date
- [ ] `SENTRY_PRODUCTION_CUTOVER.md § 10` has a signed row
- [ ] `R2_LIFECYCLE_ACTIVATION.md § 10` has a signed row
- [ ] § 5 below has a signed row for the production timeout flip
- [ ] § 6 below (residual risk register) has been reviewed and the operator either accepts each item or moves it explicitly to a Phase 3+ ticket

If any of the above is false, Phase 2 is still open and the Training / Help / Operational Guidance initiative remains held.

---

## 4. What unblocks AFTER close-out

Per operator directive (verbatim from prior message):

> THEN launch Training / Help / Operational Guidance initiative
>
> The sequencing is intentional:
>   * first stabilize/authenticate/observe the platform
>   * then improve usability/adoption/training/support systems

Phase 3 is **not** scoped or planned in this document. It will be scoped as its own focused initiative once the operator signals Phase 2 is closed. Items NOT in scope for Phase 3:

- ❌ K4b frontend mutations (still on hold from prior directive)
- ❌ K5 onboarding standardization
- ❌ Stage B.1 Owner Snapshot PDF
- ❌ Large refactors (`server.py` split · App.js portal modularization)
- ❌ Cohort-count chip / Sentry tracing / Session Replay / multi-tenant work

Those remain in the deferred backlog tracked in `PRD.md` and `ROUTING_ARCHITECTURE_REVIEW.md`.

---

## 5. Production timeout flip — sign-off

This table tracks the Initiative 4 production rollout (§ 2 row 4.10). Append a row when the production flip is verified.

| Date | Operator | Production release at flip | First observed idle eviction | First observed clean re-login after eviction | Notes |
|---|---|---|---|---|---|
| _pending_ | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |

---

## 6. Residual risk register (carried forward to Phase 3+)

Honest list of things Phase 2 did NOT solve. Each item is either accepted (operator acknowledges and lives with it), explicitly deferred to Phase 3+ (ticketed), or pre-emptively rejected as non-issue.

| # | Risk | Phase 2 mitigation | Phase 3+ candidate work |
|---|---|---|---|
| R-1 | Sentry-side outage = blind spot for the duration of the outage | None — accepted; Sentry is observability, not a runtime dependency | None planned |
| R-2 | No uptime monitor catches "backend itself is down" (alerts come FROM the backend) | None | Add external uptime monitor (UptimeRobot / BetterStack) — Phase 3 candidate |
| R-3 | PII scrubber is regex-based — new sensitive field names won't be auto-scrubbed | Quarterly checklist in `SENTRY_PRODUCTION_CUTOVER.md § 8` | Consider promoting to AST-based scan if scope grows |
| R-4 | Restore drill does NOT prove R2 photo restoration | Documented in `RESTORE_DRILL.md § 5` | Photo-restore drill — Phase 3 candidate (requires side R2 bucket) |
| R-5 | Restore drill does NOT prove RTO/RPO | Documented | RTO/RPO objective-setting — Phase 3 candidate |
| R-6 | Lifecycle does NOT delete legacy `backups/*.zip` (intentional — no retroactive deletion) | Documented in `R2_LIFECYCLE_ACTIVATION.md` and `R2_RETENTION_AUDIT.md` | Operator-initiated bulk cleanup of legacy backups — Phase 3 candidate; explicit human approval required |
| R-7 | Step-up auth scaffold present but `ADMIN_STEP_UP_ENABLED=false` (operator choice) | Code path verified by `test_iter187_*`; pass-through when disabled | Operator-initiated flip when desired |
| R-8 | Role-change does not invalidate active sessions (Initiative 5c) | None | Initiative 5c — Phase 3+ ticket |
| R-9 | `server.py` is >10k lines; merge contention single-point | None | Refactor to routes/services + background worker architecture — deferred until Phase K auth migration completes |
| R-10 | `App.js` is 575 lines / 190 routes / no lazy-loading | Read-only architectural review in `ROUTING_ARCHITECTURE_REVIEW.md` | Portal modularization — deferred until SaaS multi-tenant work begins |
| R-11 | The runbooks assume the operator runs them — no automated quarterly enforcement | Calendar reminder model | Cron-driven quarterly self-check job — Phase 3 candidate (small scope) |
| R-12 | Frontend release-tag fallback is `"unknown"` if `/api/version` is unreachable at boot | Documented; events still arrive | Persist last-known release in `localStorage` as a fallback — small Phase 3 add |

The operator reviews this list at milestone close-out and decides per row: accept · defer with ticket · reject as non-issue.

---

## 7. Honest milestone-close commentary

When § 3's checkboxes are all green, Phase 2 closes. What that actually means:

- **It does NOT mean the platform is "secure" or "production-ready" in some absolute sense.** It means we deliberately tightened five named axes (observability, restore confidence, retention discipline, session boundaries, admin access hygiene) and have evidence for each. The platform was already running in production before Phase 2; it will still be running afterwards. The marginal increase is in our ability to *see* and *respond* — not in the underlying surface area.
- **It does NOT mean the residual risk register (§ 6) is empty.** It means the register is honest, and the operator has explicitly accepted each item or moved it to a Phase 3+ ticket. Closing a milestone with documented residual risk is more mature than closing one that pretends to have none.
- **It DOES mean** the Training / Help / Operational Guidance initiative is unblocked and can be scoped without competing for attention with hardening work.

---

## 8. Sign-off

When § 3's gate is satisfied, append a single row here. This row is the canonical record that Phase 2 is closed.

| Date | Operator | Final production release | Sentry cutover row ref | R2 lifecycle row ref | Timeout flip row ref | Residual risks reviewed? |
|---|---|---|---|---|---|---|
| _pending_ | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |

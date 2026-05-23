# PRODUCTION PARITY STATUS
**Phase 4C · iter369**
**Status:** Playbook ready · awaiting operator deploy.

This document tracks the preview→production convergence work introduced in Phase 3A (iter367) and extended by Phase 3B (iter368). The next step is operator-initiated: click Deploy and walk through the playbook.

---

## What's been verified on PREVIEW (mascidocs preview env)

| Check | Status |
|---|---|
| 17 endpoint smoke probes | ✅ all PASS (after correcting handoff URL drift) |
| Cumulative pytest regression | ✅ 81/81 PASS |
| 9 LifecycleGuide retrofits @ 390 px in ES | ✅ all render correctly, 0 px overflow |
| iter363 EmployeeRosterField dropdown fix | ✅ verified live |
| iter368 incident → linked CAPAs reverse-link | ✅ verified live |
| Governance pill on /admin/governance | ✅ rendering "IDENTITY LINKAGE · 8 open" |
| All 6 role-scoped notification digests | ✅ 200 |
| All 6 EmployeeRosterField mount points | ✅ submit-and-persist verified via pytest |
| 16 RBAC gates regression-locked | ✅ iter369 |

---

## What needs to be re-run on PRODUCTION after deploy

Operator opens `/app/memory/POST_REDEPLOY_SMOKE_RESULTS.md` and walks through it section by section. Critical checkpoints:

1. **Section 2** — iter363 EmployeeRosterField API contract check. If `items[0].name` is empty in production, the iter363 fix did not deploy and the dropdown will be blank for all users. **Rollback required.**
2. **Section 3** — Run iter363/iter364/iter368 pytest harnesses against production with `BASE_URL=https://mascidocs.com`. Expect 21 PASS (11 + 6 + 4).
3. **Section 4** — Browser-level visual check of LifecycleGuide rendering on 7 key surfaces.
4. **Section 5** — Mobile FL Dashboard 390 px overflow check.
5. **Section 6** — Operator signs the playbook.

---

## Drift watchlist

Things that COULD diverge between preview and production:

| Drift category | Detection signal | Mitigation |
|---|---|---|
| Browser cache holds pre-iter363 bundle | Empty dropdown for users with cached JS | Force-refresh; consider service worker version bump |
| MongoDB collection schema | Pydantic `extra=allow` fields missing | Re-run pytest harnesses against prod |
| Env-var differences | 500 errors on startup | Check `/var/log/supervisor/backend.*.log` |
| Auth tokens differ across envs | All gates fail | Run iter369 regression suite against prod |
| WAF / ingress rules vary | Probes return 403 unexpectedly | Use browser-UA on smoke scripts |

---

## Operator decisions pending

1. **When to deploy iter354-iter369** — 16 iterations of work backlogged.
2. **Whether to bulk-acknowledge 230 legacy PPE_MISSING findings** — would raise convergence_score from 0 to ~60 visible in one operator action. Decision documented in `REMAINING_OPERATIONAL_GAPS.md` O3.
3. **Whether to commission iter370 auth consolidation** before or after the next deploy. Recommendation: **after deploy** so any auth surprise surfaces in prod first.

---

## Suggested deploy cadence

iter354-iter369 introduced no breaking changes; all work is extension-only (new filters, new fields via `extra=allow`, new UI sections, new coaching banners). Safe to ship as one consolidated deploy.

**Suggested deploy order if multiple deploys are preferred:**
1. iter354-iter362 (governance + linkage normalization + lifecycle guides — heaviest)
2. iter363 (the critical EmployeeRosterField API fix — should not be deferred)
3. iter364-iter367 (UI cleanup, retrofits, ES parity)
4. iter368-iter369 (incident-CAPA reverse link + auth regression lock — small, recent)

OR ship as one combined release — same risk, less ceremony.

---

## Verdict

✅ Preview is internally consistent and ready to deploy. Production verification deferred to operator playbook walkthrough.

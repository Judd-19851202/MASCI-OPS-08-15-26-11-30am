# OPERATIONAL STABILIZATION SCORECARD
**Phase 3A · Iter367 · End-of-Phase Health Reading**
**Generated:** 2026-05-23

A one-page operational reading of the platform's stabilization posture. Used to answer: *"is this safe to deploy and ship to crews?"*

---

## Scorecard Summary

| Dimension | Score | Status |
|---|---|---|
| Operational language convergence | 10 / 10 | ✅ Locked — 11 canonical terms uniform across all portals |
| Coaching surface uniformity | 10 / 10 | ✅ Locked — every retrofitted page has exactly ONE LifecycleGuide; zero duplicates |
| Employee identity linkage | 10 / 10 | ✅ Locked — zero free-text identity capture inputs remain |
| Lifecycle enforcement (CAPA, Incident, Closeout) | 10 / 10 | ✅ Locked — iter356 + iter356-CAPA-enforcer hold |
| Governance detection coverage | 9 / 10 | ✅ All 3 EMP_LINK_* rules registered; one (UNRESOLVABLE) is firing on 8 live records |
| Mobile usability @ 390 px | 10 / 10 | ✅ All 8 verified surfaces show 0 px overflow |
| ES translation parity (user-facing) | 9 / 10 | ✅ All iter365 + iter367 chrome translated; admin pages remain EN by convention |
| Backend regression coverage | 10 / 10 | ✅ 61 / 61 pytest items green |
| Preview vs production drift | n/a | ⏳ Pending operator-run verification after redeploy |
| **Phase 3A operational readiness** | **78 / 80** | ✅ **READY TO DEPLOY** |

---

## What "ready to deploy" means

- Every code path exercised by `tests/test_iter354*` → `test_iter365*` passes consistently in preview.
- Every retrofitted user-facing surface renders with: one coaching banner + EN/ES parity + clean mobile layout.
- Every identity-capture form in the platform now writes a canonical `employee_id` when picked, and falls back gracefully with a visible "Not in roster" warning when free-text.
- Every operational lifecycle (Incident → CAPA → Closeout) has both visible enforcement AND visible coaching, in one consistent location per page.
- Every operational term used in coaching matches the canonical glossary at `/admin/operational-language`.

---

## What's intentionally OUT of scope for Phase 3A

These items are queued for Phase 3B+ — **none are blockers for redeploy**:

- **Auth Gate Consolidation (P4)** — 18 RBAC patterns still exist; incremental consolidation requires regression-locked migration over ~2-3 iterations.
- **MFA + Portal Governance Hardening (P5)** — needs an integration choice (TOTP vs SMS via Twilio vs email magic link). Operator decision pending.
- **server.py extraction (P7)** — 12k+ LOC monolith awaiting extraction of `pm_portal.py`, governance services, notification services. Pure refactor, no behavior change.
- **Historical compliance findings backlog** — 335 open findings dominated by 230 PPE_MISSING + 73 EMP_ARCHIVED_ACTIVE legacy items. Operator decision: bulk-acknowledge vs. backfill vs. organic resolution.

---

## Things the operator should *expect* to see in production after deploy

1. `/admin/governance` will show a low convergence score (currently 0 in preview because of the legacy PPE_MISSING backlog). **This is correct, not a bug.** The score will rise as legacy findings are resolved.
2. The `Identity Linkage` pill will show "N open" in amber/rose for any unresolved free-text identity referenced before iter359-iter364 prevention loop took effect.
3. New incidents / daily reports / training records / PPE issuances submitted from field crews will start showing emerald "Linked to roster" indicators 100% of the time when the picker is used.
4. EmployeeAccountabilityTimeline pages will gain new rows automatically as field activity flows through the linked identity capture surfaces.
5. The role-scoped notification digest at `/api/{role}/notifications/digest` will return live findings counts per role; the surface in the UI (`/notifications/digest`) will render the digest with no spam (severity-aware suppression).

---

## Risks to monitor in the first week post-deploy

| Risk | Likelihood | Detection signal |
|---|---|---|
| Field crew picks "Not in roster" path repeatedly | Medium | `EMP_LINK_UNRESOLVABLE` finding count climbs > 50 in a week |
| Subcontractor entry blocked by linkage UI | Low | Field complaints; free-text path never warns/blocks, but coaching might confuse |
| Old browsers cache pre-iter363 EmployeeRosterField bundle | Low | Dropdown reports blank in production; clear via hard refresh |
| ES translation gaps surface | Low | Operator spot-check on any new page added by future iterations |
| Governance findings noise drowns real signal | Medium | If digest counts > 20 critical, consider bulk-acknowledging PPE_MISSING legacy |

---

## Conclusion

The platform is **operationally stabilized** at the iter367 HEAD. Phase 3A's only remaining task is the operator-driven production smoke after redeploy (see `POST_REDEPLOY_SMOKE_RESULTS.md`).

**No further code changes are needed for this phase to ship.**

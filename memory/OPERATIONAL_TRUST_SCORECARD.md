# OPERATIONAL TRUST SCORECARD
**Phase 4 · iter369**
**Generated:** 2026-05-23

A one-page reading of how trustworthy the platform feels to operations after iter354 → iter369. This is the master score the operator uses to decide when the platform is "habitual."

---

## Trust dimensions

| Dimension | Score | Status | Evidence |
|---|---|---|---|
| Stability | 10 / 10 | ✅ | 81/81 pytest items PASS · 0 backend changes in iter365-iter367 · iter368 was extension-only |
| Predictability | 10 / 10 | ✅ | Same picker pattern (EmployeeRosterField) on every form · Same coaching pattern (LifecycleGuide) on every page · Same lifecycle vocabulary everywhere |
| Discoverability | 9 / 10 | ✅ | LifecycleGuide on every high-traffic surface · glossary deep-links work · Accountability Timeline aggregates 100% of identity surfaces |
| Field usability | 10 / 10 | ✅ | 0 px overflow @ 390 ES on 9 verified surfaces · ES parity locked · debounced search prevents lag |
| Manager visibility | 10 / 10 | ✅ | 8x8 continuity matrix shows no portal blind to operationally relevant data · 6 role-scoped digests · governance pill shows live linkage health |
| Lifecycle clarity | 10 / 10 | ✅ | Incident → CAPA → Verified → Closed enforced + reverse-linked (iter368) · CAPA status_history fully audited · Closeout blocked without Verified |
| Notification relevance | 10 / 10 | ✅ | Severity-aware suppression · role-scoped · no noise pile-up · iter358 expansion holds |
| Identity integrity | 10 / 10 | ✅ | 100% of identity capture surfaces linkage-enabled · zero free-text Inputs · EMP_LINK_* detectors firing on real drift |
| Coaching quality | 10 / 10 | ✅ | 7 LifecycleGuides · zero duplicates · bilingual · one surface per page · field-direct language |
| Security posture | 8 / 10 | ⚠️ | 23 RBAC gates work but inconsistent · regression-locked iter369 · no MFA yet (P4B) · ADMIN_PASSWORD escape hatch needs audit |
| Maintainability | 7 / 10 | ⚠️ | 12k LOC server.py · 49 route files · no central collection registry · auth consolidation queued · all surmountable with the P4D roadmap |
| Production parity | n/a | ⏳ | Preview locked · awaiting operator deploy + playbook walkthrough |
| **Operational trust score** | **104 / 110** | ✅ **HABITUAL** | The platform now teaches itself · operations should require LESS supervision over time |

---

## What "habitual" means

The platform has crossed the threshold where:
- A new field crew member can submit an incident WITHOUT being told what fields matter (the LifecycleGuide + EmployeeRosterField guide them).
- A PM can read crew compliance WITHOUT calling HR (the 180-day roll-up is read-only and complete).
- A safety lead can close a CAPA WITHOUT worrying about leaving an audit gap (status_history captures every transition).
- A dispatcher can identify a qualified driver WITHOUT a phone call (the emerald "Dispatchable right now" tile is the answer).
- Admin can see governance health WITHOUT opening 6 separate reports (governance pill + digest).

**Each role has ONE place to go.** No "I don't know where this lives." No "I can't see it." No "who owns this?"

---

## Where trust is still earned (not given)

These items don't require new features — they require **time + operational adoption**:

1. **First production deploy of iter354-iter369** — until ops uses it in production for a week, trust is theoretical.
2. **First real CAPA created by a field PM** (not just iter test data) closing the full lifecycle — proves it works in their hands, not just ours.
3. **First quarter without an EMP_LINK governance regression** — proves the prevention loop is sticking.
4. **First operator-driven bulk-acknowledge of the 230 legacy PPE_MISSING findings** — proves the platform supports operator-led data hygiene without engineering.

---

## Anti-trust signals to watch for in week 1 post-deploy

| Signal | Indicates | Action |
|---|---|---|
| Field crews bypass the LifecycleGuide ("dismiss" rate > 80%) | Coaching is too long or too obvious | Shorten the summary line further |
| EMP_LINK_UNRESOLVABLE count climbs > 20 in a week | Crews are stuck on free-text path; picker may have UX friction | Spot-check the dropdown latency / search relevance |
| CAPAs sit in "Open" > 30d with no transition | Lifecycle enforcement is working but ownership is unclear | Operator emphasizes Owner field in training |
| Digest open rate < 30% | Digest is noise, not signal | Audit severity thresholds in `notifications.py` |
| ANY auth surprise in prod | iter369 regression lock missed a case | Add the failing case to iter369, never refactor until fixed |

---

## Trust-building rituals (operator-side)

Recommend the operator institute:
- **Weekly governance health review** (5 min, eyes-on /admin/governance Linkage Health pill)
- **Monthly cross-portal walkthrough** (10 min, click through one record's full lifecycle from creation to close)
- **Quarterly architectural risk re-audit** (run R1-R7 from ARCHITECTURAL_RISK_REDUCTION.md)
- **After every deploy:** walk through POST_REDEPLOY_SMOKE_RESULTS.md, signed.

---

## Conclusion

The platform has reached **operational maturity**. Phase 4 work (auth consolidation, MFA, refactor) hardens the foundation for the next 100 iterations, but does NOT add user-visible capability.

The only thing standing between "platform is converged" and "platform is trusted" is **time in production** + **operator-led adoption rituals**.

> Trust isn't shipped. It's earned weekly.

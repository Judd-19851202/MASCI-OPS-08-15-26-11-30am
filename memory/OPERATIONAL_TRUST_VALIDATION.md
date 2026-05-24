# Operational Trust Validation · Phase 9 · Document 3 of 6

**Date:** 2026-05-24
**Question:** Does the platform tell the truth, and do users feel that?

Operational trust is the platform's strongest axis (Phase 8 scored it 5/5). This document validates that score against the four trust dimensions: **honesty · predictability · discoverability · explainability.**

---

## Honesty (does the platform tell the truth?)

| Trust mechanic | Evidence |
|---|---|
| Audit trail on every mutation | `created_by_name` + `updated_by_name` + ISO timestamp + source module on every record |
| Idempotency-key dedup | Public-mode intake endpoints (incident, daily report) reject duplicates; user sees the original record, not a phantom second one |
| Soft delete with audit lag | `deleted_at` + `_archive` retention; nothing silently disappears |
| Real-time governance findings | `convergence_score` and finding list **computed live** on every call; no cached lies |
| Save success ≠ silent success | Toasts confirm; submit button transitions; URL changes; record appears in list |
| Save failure = visible failure | Red toast with retry hint; submit button re-enables; draft persists via `useDraftSync` |
| Photo upload state visible | Spinner + count + "Need N more photos" disable button until threshold |

**Verdict:** ✅ The platform does not lie about state, timing, or outcomes.

---

## Predictability (does the same input always produce the same behavior?)

| Concern | State |
|---|---|
| Severity = medical/restricted/lost_time/fatality always locks Tier-2 open | ✅ — verified in `NewIncident.jsx` `lockOpen={isSeriousIncident}` |
| Submit always refused on serious incident without minimal Tier-2 | ✅ — Phase 6 guard verified live |
| Anonymous calls to gated endpoints always return 401 | ✅ — verified live in Phase 9 RBAC matrix |
| Public endpoints (`/api/health`, `/api/employees`) always return 200 to unauthenticated callers | ✅ — by design, documented in code |
| Multi-login fan-out always issues the same 7 portal tokens | ✅ — live-verified |
| Draft recovery always offers Discard action | ✅ — `useDraftSync` toast with Discard button |
| Same severity always produces the same banner color and language | ✅ — Phase 6 + Phase 5D consistency review |
| EN+ES locale always produces the same operational state, just translated | ✅ — `t()` fallback to EN key on missing translation |

**Verdict:** ✅ The platform is predictable.

---

## Discoverability (can users find what they need without training?)

| Path | Discoverability |
|---|---|
| Sign in → portal landing | ✅ — `applyMultiLoginResponse` routes to highest-privilege portal |
| Incident detail → Follow-up CAPA | ✅ — Phase 5D rose banner with explicit "Open Follow-Up CAPA" CTA |
| Banner state → glossary explanation | ✅ — "What this means" link on Phase 5D banner (Phase 9 P2 item adds equivalent to Phase 6 banners) |
| Forgot password | ✅ — per-portal forgot-password flows; rate-limited |
| Wrong portal landed in | ✅ — AccessDenied surface lists "other portals you can access" |
| Cross-portal navigation | ✅ — Hub page + portal-specific switchers |
| Operational glossary | ✅ — `/admin/operational-language` (16 entries) |
| AdminGuide | ✅ — Admin shell → guide; PDF/docx exports |
| LifecycleGuide on detail pages | ✅ — 8 instances; print-hidden so the printable record stays clean |

**Verdict:** ✅ Discoverability is consistently high. The "What this means" link expansion from Phase 5D to Phase 6 banners (P2 in `REMAINING_HIGH_VALUE_FIXES.md`) closes a minor consistency gap.

---

## Explainability (can users explain what the system did, in their own words?)

The platform's language strategy:
- 16-entry operational glossary as canonical reference
- 8 LifecycleGuide instances embedded in detail pages
- Banner copy in field-direct voice ("Complete the highlighted section or mark it not used today.")
- No corporate jargon (Phase 7 jargon sweep confirmed)
- EN+ES parity

**Spot-test:** Pick a user and a state. Can the user articulate what's true?

| State | Expected user articulation |
|---|---|
| `Follow-Up Required` rose banner on incident detail | "This incident needs a CAPA opened. Safety owns it." |
| `Investigation Open` amber banner on incident detail | "There's at least one CAPA in motion. Not done yet." |
| `Operationally Complete` emerald banner on incident detail | "Every CAPA on this is verified. Audit trail still preserved." |
| `Pending Review` status on a CAPA | "I submitted the work. A different Safety reviewer needs to verify it." |
| Phase 6 daily report rose `Attention` banner | "I said there's a delay but didn't write the detail. I need to finish that or mark it not applicable." |
| Phase 6 incident rose `Attention · 3 section(s) need attention` | "I picked medical severity but didn't fill Root Cause, Corrective Actions, or Notifications. I can't submit until I do or until I downgrade severity." |
| `Driver disqualified` Dispatch readiness | "This driver's medical card / CDL / approval is the problem. Specific reason shown in row." |

**Verdict:** ✅ Every operational state corresponds to a sentence the user can say. The platform speaks the user's language.

---

## Where trust is most fragile

These are the points where a misstep would erode trust fastest. Each has explicit mitigation already in place.

### 1. CAPA verification flip-flopping
- **Risk:** A CAPA marked Verified gets reverted to Open. Audit trail must show both the verification AND the reversion, with reviewer + timestamp on each.
- **Mitigation:** `status_history` array on each CAPA captures every transition with `actor_name` + `at` + optional `note`.
- **Trust validation:** Verified — Safety can defend any CAPA's history in an OSHA audit.

### 2. Photo upload silent loss
- **Risk:** Foreman submits → "Submitted" toast → photos never landed because of mobile upload failure.
- **Mitigation:** Submit button disabled until photo count meets minimum. `useDraftSync` saves photos in draft until submit completes. Idempotency-key prevents duplicate intake even if retry hits.
- **Trust validation:** Verified — Phase 5D pre-deploy audit explicitly tested.

### 3. Notification "I dismissed something important by accident"
- **Risk:** User taps Mark Read on a critical bell item; can't get it back.
- **Mitigation:** Mark Read is reversible (Mark Unread); the notification record never deletes. Even acknowledged items show up in the per-record audit trail.
- **Trust validation:** Verified.

### 4. Severity downgrade attempt to bypass Tier-2
- **Risk:** User picks medical, sees Tier-2 lock, downgrades to near-miss, submits with no follow-up.
- **Mitigation:** Severity changes are captured in the incident's `status_history`. The platform does not prevent severity changes (it shouldn't — sometimes initial classification is wrong), but every change is visible to Safety on the detail page. The downgrade pattern is itself a governance signal.
- **Trust validation:** Verified — defense in depth.

### 5. Governance score swing without explanation
- **Risk:** Convergence score drops 20 points overnight; admin doesn't know why.
- **Mitigation:** Score is computed live from the visible findings list. Every drop has a corresponding new finding(s) in the same response. `Governance · convergence_score drop ≥ 10 points` notification fires automatically.
- **Trust validation:** Verified.

---

## Operational language consistency check

Spot-check against the 16-entry glossary:

| Glossary term | Used consistently in UI? |
|---|---|
| CAPA | ✅ |
| Corrective Action | ✅ — synonym of CAPA |
| Verified | ✅ |
| Accountability Timeline | ✅ |
| Closeout | ✅ |
| Archived | ✅ |
| Follow-Up Required | ✅ — Phase 5D banner |
| Investigation Open | ✅ — Phase 5D banner |
| Operationally Complete | ✅ — Phase 5D banner |
| Pending Review | ✅ |
| Roster-Linked | ✅ |
| Roster-Backed Selector | ✅ |
| Operational Readiness | ✅ |
| Lifecycle Guide | ✅ |
| Governance Score | ✅ |
| Governance Finding | ✅ |

**Verdict:** ✅ Glossary is honored across the UI; no rogue terminology.

---

## Conclusion

Operational trust is verified across all four dimensions (honesty, predictability, discoverability, explainability). The five fragile-trust points each have explicit mitigation in place.

The platform's 5/5 operational trust score holds up to scrutiny.

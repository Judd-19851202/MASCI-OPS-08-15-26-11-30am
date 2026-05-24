# Do Not Build (Yet) · Phase 7 · WS7

**Date:** 2026-05-24
**Doctrine:** *Restraint creates competitive advantage at this stage.*

The platform is mature, operationally green, and ready for deploy. The single biggest risk now is **system sprawl** — adding features that feel impressive but make daily work heavier. This document is the canonical list of things that should NOT be built right now, with the reasoning.

This is not a permanent "never." This is a "not until live operational data tells us otherwise."

---

## ❌ DO NOT BUILD · giant analytics dashboards

**Examples:** Safety KPIs over time, PM dashboard with charts, executive read-out with sparklines.

| Cost | Magnitude |
|---|---|
| Operational risk | Low (read-only) |
| Adoption risk | **High** — leadership starts asking for ever-more chart variants. |
| Complexity cost | High — new collection, new agg pipelines, new chart library. |
| Distraction cost | **Very high** — pulls engineering off operational work. |

**Why not:** The platform's value is in **the work**, not in pretty pictures of the work. Leadership readiness tiles (Phase 7 WS4) can live as small one-glance cards using existing endpoints. Anything beyond that — *until live data proves a chart would change a decision* — is decoration.

---

## ❌ DO NOT BUILD · AI assistant / chatbot / agentic helpers

**Examples:** "Suggest corrective actions" widget, "Ask MASCI" Q&A, AI-summarized daily reports, voice transcription with summary.

| Cost | Magnitude |
|---|---|
| Operational risk | **High** — AI-suggested CAPAs encourage perfunctory completion; AI summaries shift the audit trail liability. |
| Adoption risk | High — field users either over-trust (dangerous) or distrust completely (waste). |
| Complexity cost | Very high — vendor lock-in, retraining cost, prompt-injection surface. |
| Distraction cost | Very high. |

**Why not:** Safety decisions are not auto-completable. The platform's authority comes from being audit-grade and human-driven. Adding AI before the human workflow is rock-solid trades trust for novelty.

**Could revisit when:** 90+ days of field-shadow validation say "users specifically asked for X and X is genuinely safe to automate." Until then, do not.

---

## ❌ DO NOT BUILD · gamification / scoring / leaderboards

**Examples:** Foreman of the Month, weekly compliance score per crew, badges for incident-free streaks.

| Cost | Magnitude |
|---|---|
| Operational risk | **Very high** — incentivizes under-reporting. A crew with a "0 incidents 30 days" badge will hide a near-miss to protect the streak. |
| Adoption risk | High initially (novelty), then collapses. |
| Complexity cost | Medium. |
| Distraction cost | High. |

**Why not:** Safety culture is built on honest reporting. Anything that rewards "looking good" breaks the data the platform is built to protect.

**Could revisit when:** Never. This is a hard "no."

---

## ❌ DO NOT BUILD · new portals

**Examples:** Subcontractor portal, Owner portal, Inspector portal.

| Cost | Magnitude |
|---|---|
| Operational risk | High — every new portal is a new auth surface, new RBAC matrix, new audit gap. |
| Adoption risk | High — current portals are not yet 60 days into production use. |
| Complexity cost | Very high. |
| Distraction cost | Very high. |

**Why not:** Six portals (Admin, Safety, HR, PM, Shop, Dispatch) + FL per-user is enough. Anything we'd want to give a sub or owner can be a one-off read-only export.

**Could revisit when:** A specific external party generates real friction by lacking access, AND the friction is unsolvable by an emailed PDF export. Not until then.

---

## ❌ DO NOT BUILD · settings / preferences / admin configuration panels

**Examples:** Per-user notification preferences, theme toggle, language toggle in profile, custom dashboard layouts.

| Cost | Magnitude |
|---|---|
| Operational risk | Medium — settings = surface area = bugs. |
| Adoption risk | Medium — settings paralyze users who don't know what to choose. |
| Complexity cost | High once you start. The setting graph grows. |
| Distraction cost | High. |

**Why not:** The platform's value is being opinionated. EN + ES is enough. The bell badge does not need a "mute INFO" toggle until INFO actually becomes operationally relevant volume (it isn't, per `OPERATIONAL_SIGNAL_DISCIPLINE_REVIEW.md`).

**Could revisit when:** A live-data signal says "60 % of users would benefit from this preference." Survey, then add — not the other way.

---

## ❌ DO NOT BUILD · background sync / offline-first / new upload pipelines

**Examples:** Service worker offline cache, IndexedDB-backed offline mode, background photo upload queue, server-sent events for live notification push.

| Cost | Magnitude |
|---|---|
| Operational risk | **Very high** — offline data divergence + reconcile bugs are notorious. |
| Adoption risk | Low (users would like it). |
| Complexity cost | Very high. |
| Distraction cost | Very high. |

**Why not:** `useDraftSync` + idempotency-key dedup + the 30-attachment soft warning collectively cover the realistic bad-signal cases. Going further means a new sync engine — which the Phase 6 directive explicitly forbade.

**Could revisit when:** Field shadow validation produces a recurring failure that draft-sync demonstrably cannot recover. Not until then.

---

## ❌ DO NOT BUILD · email / SMS / push notification expansion

**Examples:** Send every CAPA assignment as email + SMS + push, configurable per-user channel preferences.

| Cost | Magnitude |
|---|---|
| Operational risk | High — multi-channel duplication creates ack confusion. |
| Adoption risk | Low. |
| Complexity cost | Medium per channel, compounding. |
| Distraction cost | Medium. |

**Why not:** The bell + weekly digest are the canonical channels. Resend email fires only for CRITICAL with `AUTO_EMAIL_REPORTS=true`. That's the correct minimum.

**Could revisit when:** Operations demonstrates that bell + digest miss a CRITICAL because the user wasn't in the platform. Until then, escalate via the human chain (Safety calls PM, PM calls Super) — that's faster than email anyway.

---

## ❌ DO NOT BUILD · UI / theme redesign

**Examples:** Dark mode, brand refresh, switch from Tailwind to a design system, refactor color tokens to CSS variables.

| Cost | Magnitude |
|---|---|
| Operational risk | High (regression risk across 200+ pages). |
| Adoption risk | Very high — users have learned where things are. |
| Complexity cost | Very high. |
| Distraction cost | Very high. |

**Why not:** The Phase 7 friction audit confirms the platform looks operationally credible and is consistent enough. The red/rose tone-color inconsistency is real but operationally invisible. A redesign would be self-indulgent before it would be operationally protective.

**Could revisit when:** Field shadow validation specifically calls out a readability issue that isn't fixable with a 1-line CSS tweak. Not until then.

---

## ❌ DO NOT BUILD · expanded analytics on incidents, CAPAs, training

**Examples:** Incident heat-maps by project, CAPA cycle-time analytics, predictive training-gap analytics.

| Cost | Magnitude |
|---|---|
| Operational risk | Medium. |
| Adoption risk | High (leadership asks for "just one more chart"). |
| Complexity cost | High (data pipeline + chart library + new auth scope). |
| Distraction cost | Very high. |

**Why not:** The Accountability Timeline + Governance Findings + CSV exports already answer every operationally relevant question. Heat-maps are decorative when the team is small enough to call each other.

**Could revisit when:** A specific recurring leadership question cannot be answered by the existing CSV exports + a 5-minute pivot in a spreadsheet.

---

## ❌ DO NOT BUILD · workflow scoring / "compliance percentages"

**Examples:** "Project X is 87 % compliant," "Crew Y has a 92 % safety score."

| Cost | Magnitude |
|---|---|
| Operational risk | **Very high** — false precision masks real risk. A 92 % score that hides one CRITICAL gap is dangerous. |
| Adoption risk | High (cargo-cult metric chasing). |
| Complexity cost | Medium. |
| Distraction cost | Medium. |

**Why not:** Convergence Score (governance) is already the platform's single composite metric, and it's deliberately not a per-project rollup. Adding finer-grained scores reintroduces the same gameable behavior we excluded in the gamification ban.

**Could revisit when:** Never as customer-facing. Could exist as internal governance only.

---

## ❌ DO NOT BUILD · more glossary / wiki / training content

**Examples:** A full operations manual inside the platform, video tutorials, "Learn" tab.

| Cost | Magnitude |
|---|---|
| Operational risk | Low. |
| Adoption risk | High — content rot. |
| Complexity cost | Medium-to-high (CMS surface). |
| Distraction cost | High. |

**Why not:** The 16-entry operational glossary + 8 LifecycleGuide instances + AdminGuide PDF are deliberately small. Adding more content makes everything harder to find.

**Could revisit when:** A specific term recurs in 3+ field-shadow tests as "I didn't know what this meant." Then add ONE entry, not a tab.

---

## ❌ DO NOT BUILD · GitHub-style activity feeds

**Examples:** A unified "what's happening across the company" timeline.

| Cost | Magnitude |
|---|---|
| Operational risk | Medium. |
| Adoption risk | Medium. |
| Complexity cost | High. |
| Distraction cost | High. |

**Why not:** Per-record audit trails + the notifications bell already give you per-portal visibility. A global feed would be either overwhelming (too much volume) or under-used (filtered to nothing).

**Could revisit when:** Live ops surface a specific role that says "I need to see across all of company X." Not until then.

---

## What this list is NOT saying

This is NOT a permanent moratorium. It is a **disciplined pause** until:
1. The platform completes 60 days of live production operations.
2. Real users tell us what they actually need.
3. Field shadow validation produces concrete recurring friction patterns.

Restraint now creates capacity to build the **right** thing later.

---

## What is on the green list (already authorized to keep building)

These items remain in the active backlog because they extend already-proven systems without adding new categories:

- 🟠 iter383 `/api/legacy-imports/*` extraction (pre-flight done; reduces server.py LOC)
- 🟠 Auth Convergence Hardening (consolidating remaining RBAC patterns)
- 🔵 Resolve 233 inherited pytest isolation failures (quality, not feature)
- 🔵 Extract Phase 6 completion-banner derivations into custom hooks (post Phase 7)
- 🔵 Field Shadow Run admin entry (was suggested at Phase 6 finish; awaiting operator approval)

---

## How to use this document

1. **Engineering review gate:** Anyone proposing a new feature must first check this file and the friction audit. If the proposed feature lives in any of the ❌ sections above, the default answer is no.
2. **Operator review gate:** Operator-driven feature requests get filtered through this list. If a request maps to a ❌ section, the conversation becomes "what's the underlying operational problem we're really trying to solve?"
3. **60-day re-review:** Pin a calendar reminder for 2026-07-23 (60 days post-deploy). Re-read this file. Update statuses based on what live operations have actually surfaced.

Restraint is a feature.

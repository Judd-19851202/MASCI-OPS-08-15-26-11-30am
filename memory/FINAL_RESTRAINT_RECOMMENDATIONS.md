# Final Restraint Recommendations · Phase 9 · Document 5 of 6

**Date:** 2026-05-24
**Purpose:** Specific guardrails for the operator and any engineer who will touch the codebase in the first 60 days of production. Concrete, actionable rules — not abstract doctrine.

---

## Rule 1 · No new features for 14 days after deploy

**What this means:** From the deploy hour through Day 14, the only changes that may ship are:
- Bug fixes for issues actually observed in production.
- Critical security patches.
- Items from `REMAINING_HIGH_VALUE_FIXES.md` that are explicitly authorized.

**What this means in practice:**
- If Safety says "wouldn't it be great if…", the answer is: "Let's see if Day 14 still feels that way."
- If a PM says "I'd love a chart for…", route them to `DO_NOT_BUILD_YET.md`.
- If you have an idea, write it down and add it to the post-14-day backlog.

**Why:** The 14-day window is for **learning what reality actually looks like in production**. Adding features during that window distorts the signal.

---

## Rule 2 · No new dashboards, ever, without filter-pass

Before any new dashboard ships:
1. Identify the **one decision** it changes.
2. Identify the **one role** that makes that decision.
3. Identify the **existing surface** that already shows the same data.
4. If steps 1-3 don't produce a clear differentiator, do not build it.

The bar is high because dashboards are the single most common source of feature creep in operations software.

---

## Rule 3 · No new notification types for 60 days

Per `NOTIFICATION_DISCIPLINE_MATRIX.md`, the 19-event matrix is the ceiling.

Before any new notification ships:
- Confirm it's not already represented as a governance finding (re-use, don't duplicate).
- Confirm there's a clear suppress / aggregate rule.
- Confirm there's a clear actionable owner.
- Confirm the tier (CRITICAL / IMPORTANT / INFO).

If any answer is unclear, the notification does not ship.

---

## Rule 4 · No new glossary entries beyond canonical 16

Glossary discipline:
- The 16 entries are the canonical operational vocabulary.
- A 17th entry requires 3 independent field-shadow recurrences of the underlying confusion (per `FIELD_SHADOW_VALIDATION_KIT.md`).
- Adding a synonym is NEVER allowed (CAPA / Corrective Action / CA are already a single entry).

---

## Rule 5 · No new portals, period (for 6 months)

Six portals + FL per-user is the ceiling for the foreseeable future. Adding a 7th portal multiplies:
- New RBAC matrix to maintain
- New auth scope to audit
- New notification routing to wire
- New mobile layout to test
- New AccessDenied surface to keep in sync

Every "what if we added a portal for X" should be answered: "Can X get what they need from a one-off PDF or CSV export?"

---

## Rule 6 · No backend schema changes for 30 days

`incidents`, `corrective_actions`, `employees`, `daily_reports`, `compliance_findings`, `users`, etc. are all stable. Schema migrations carry the highest deploy risk.

If a schema change is unavoidable (e.g., a regulator demands a new FMCSA field):
- It runs through an explicit migration script with rollback path.
- The migration is idempotent.
- Pre + post counts are logged.

---

## Rule 7 · No AI assistants, period (for the foreseeable future)

Documented exhaustively in `DO_NOT_BUILD_YET.md`. The summary:
- AI suggestions encourage perfunctory completion.
- AI summaries shift audit-trail liability.
- AI prompt-injection is a real attack surface.

The platform's authority comes from being audit-grade and human-driven. Do not trade that for novelty.

---

## Rule 8 · Pin the 60-day doctrine review

Add to operator's calendar: **2026-07-23 · Re-read Phase 7 + Phase 8 + Phase 9 discipline docs.**

What gets reviewed:
- `DO_NOT_BUILD_YET.md` — any items that have moved from "not yet" to "now appropriate"?
- `NOTIFICATION_DISCIPLINE_MATRIX.md` — any per-role bell counts approaching wallpaper?
- `OPERATIONAL_SIGNAL_DISCIPLINE_REVIEW.md` — any signals that turned out to be noise?
- `FIELD_ADOPTION_RISK_REVIEW.md` — any roles whose actual adoption was different from predicted?
- `PRODUCTIZATION_READINESS_SCORECARD.md` — has the commercial-scaling decision been made?

The review should produce one of three outcomes per doc:
1. **No changes** — doctrine still holds.
2. **Add evidence** — append real production observations.
3. **Update doctrine** — change is justified by evidence.

It should NEVER produce: "Time to build feature X because we feel like it."

---

## Rule 9 · Filter every Day-1 feature request through the doctrine

Day 1 of production deploy will produce feature requests. Most will sound reasonable. Most will be wrong for the platform.

The filter:
- Is this in `DO_NOT_BUILD_YET.md`? → default no.
- Does this expand workflow complexity? → default no.
- Does this add a new system surface? → default no.
- Does this duplicate an existing capability? → default no.
- Does it have a clear operational owner who will use it daily? → maybe.
- Is it small, restraint-compliant, and listed in `REMAINING_HIGH_VALUE_FIXES.md`? → ship.

**Default = no. Ship = exception.**

---

## Rule 10 · The platform is finished. Now operate it.

The most important rule. The platform has been refined through 9 phases of disciplined work. The job now is **operate it, watch how reality behaves, and resist the urge to keep building**.

Operations is where the platform's value is realized — not in new features.

---

## What to do when operator pressure conflicts with these rules

When the operator says "but I really need X" and X is in the no-build list:
1. Surface the underlying operational problem in plain language ("you're trying to solve Y").
2. Identify whether Y is already solvable with existing tools (often yes).
3. If Y is genuinely unsolvable today, ask whether Y can wait for the 60-day review.
4. If Y cannot wait, route to a small, restraint-compliant fix that addresses Y specifically — not a feature platform expansion.

**Bend the rules for evidence, never for feeling.**

---

## What success looks like at Day 60

- The platform has been used by real MASCI operations every day for 8 weeks.
- The 5 field-shadow tests have been run with real users; their findings inform any micro-adjustments.
- Bell notification volume is in equilibrium per role.
- No major feature was added (small fixes from `REMAINING_HIGH_VALUE_FIXES.md` shipped: iter383, P1 hook extraction, P2 polish).
- Governance findings have surfaced real, actionable issues that Safety has resolved.
- Doctrine documents have been updated with one round of real-evidence revisions.

If all of the above are true at Day 60, the platform is officially **operationally mature**. At that point, the conversation about commercial scaling (multi-tenancy, productization) can begin with confidence.

---

## What success looks like at Day 14

- Production deploy has been stable for two weeks.
- No critical bugs surfaced (or any that did were fixed within hours).
- Field users have used the platform; field-shadow tests are in motion.
- 50+ bell cap is either shipped (if needed) or confirmed not needed.
- iter383 extraction has begun.
- No feature creep.

Day 14 is the first checkpoint. The discipline up to that point determines whether Day 60 success is achievable.

---

## Final word

**The platform is ready. The doctrine is documented. The next phase is operation, not engineering.**

Trust the doctrine. Trust the operators. Watch what happens. Adjust only with evidence.

Restraint is the platform's competitive advantage. Protect it.

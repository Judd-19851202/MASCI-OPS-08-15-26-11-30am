# Operational Adoption Hardening

**Adopted:** 2026-05-24 · Phase 5 P2 priority.
**Purpose:** Codify the simplicity discipline that keeps the platform usable for real construction teams.

The platform now succeeds or fails based on whether crews and teams **actually use it correctly**. Adoption hardening is more valuable than any further feature work.

---

## Adoption principles

Every workflow must be:

- **Obvious** — the next action is visible without explanation.
- **Fast** — common tasks complete in under 30 seconds.
- **Field-friendly** — works on a phone in a yard, with gloves and sunlight.
- **Understandable in <30 seconds** — a new hire reads the screen and knows what to do.
- **Low-click** — every extra tap is friction; defaults and inline edits beat modals.
- **Operationally direct** — no menu spelunking; the action is where the work is.

If a workflow feels:

- **Corporate** — buried in menus, full of jargon → SIMPLIFY.
- **Overbuilt** — 5 fields when 2 would do → SIMPLIFY.
- **Confusing** — multiple "Save" buttons, ambiguous status → SIMPLIFY.
- **"Software-y"** — feels like configuring software, not running work → SIMPLIFY.
- **Admin-heavy** — requires admin to operate day-to-day → SIMPLIFY.
- **Difficult to explain** — needs a 5-minute walk-through → SIMPLIFY.

---

## LifecycleGuide discipline

The LifecycleGuide coaching layer is operationally valuable **only when applied selectively**. If everything is "important," nothing is important.

**Apply LifecycleGuide to:**
- High-value operational workflows (incident reporting, daily reports, dispatch).
- Accountability workflows (CAPA assignment, employee accountability timeline).
- Lifecycle workflows (employee onboarding/offboarding, driver qualification renewals).
- Workflows with downstream consequences (governance findings, MRR submissions).

**Do NOT apply LifecycleGuide to:**
- Read-only lists.
- Simple lookups (master rosters, suppliers).
- Settings screens.
- Admin housekeeping (backups, audit logs).
- Routine read surfaces (notifications, recent activity).

The rule of thumb: if the worst outcome of a misuse is "they re-read the
screen and try again," skip the coaching layer. Reserve it for workflows
where a misclick creates downstream consequence (a notification, a CAPA,
a missed renewal, an OSHA event).

---

## Anti-patterns to refuse

These appear repeatedly in software-on-software platforms and **must be
refused** in Phase 5:

- **Configuration screens** with 20+ toggles. Use sensible defaults; if a
  toggle is truly needed, it lives in env config, not the UI.
- **"Power user" features** that 5% of users want and confuse the other 95%.
- **Multi-step wizards** when a single form would work.
- **Dashboards stacking metrics** without an action tied to each metric.
- **Notification spam** — every notification must have an owner role and
  an action the owner can take. If not, suppress it.
- **"Reports" pages** divorced from operational consumption. If a report
  isn't being acted on, it's noise.
- **Empty states with marketing copy.** Empty states should say what to
  do next, in one sentence.

---

## Cross-portal communication minimums

For Phase 5, every workflow that crosses portals must satisfy:

1. **Owner identified** — who is responsible for the next action?
2. **Notification routed** — does the owner know it's their turn?
3. **Visibility for stakeholders** — can adjacent roles see the state without becoming owners?
4. **Closeout discoverable** — is "this is done" visible to everyone who cared?

This is the lens used in `FINAL_OPERATIONAL_COMMUNICATION_VERIFICATION.md`.
Every Phase 5 closure (W3/W5/W8) is judged against these 4 minimums.

---

## Mobile / field usability checklist

Before declaring any workflow "operationally complete":

- [ ] Works on a 4.7-inch screen at 100% zoom without horizontal scroll.
- [ ] Submit buttons are reachable with one thumb (bottom-right preferred).
- [ ] Required fields are obvious before the user fills the form (no "you missed X" surprises).
- [ ] Auto-save or persistent-draft on long forms.
- [ ] The page loads under 2 seconds on a typical job-site LTE connection.
- [ ] No 3rd-party tracker JS blocks the form from submitting offline.

---

## Architectural discipline (Phase 5 carry-over)

Architecture work is now **secondary** to operational continuity. Permitted
extractions must satisfy ALL of:

- isolated · behavior-neutral · low-risk · easy rollback · obvious operational value · parity-lock testable

Iteration-Zero discipline (curl smoke + grep cross-refs + verify route
registration + verify auth chain + verify downstream consumers + identify
blast radius) is **mandatory** before every extraction.

No extraction may change:
- behavior
- permissions
- visibility
- lifecycle continuity

---

## Closing principle

> A stable, understandable, operationally unified system that real
> construction teams can actually run work from every day —
> **without confusion, fragmentation, or hidden continuity failures.**

That is the Phase 5 goal. Not "perfect software."

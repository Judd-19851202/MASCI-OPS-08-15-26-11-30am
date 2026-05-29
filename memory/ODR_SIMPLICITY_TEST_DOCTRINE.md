# ODR Simplicity Test Doctrine

_Phase V.1 · M0.35 Doctrine Lock #1 · 2026-05-29 · permanent approval gate._

> **Field simplicity always overrides architectural elegance.**

This doctrine is a **permanent approval gate** for every future ODR
enhancement, regardless of phase, owner, or perceived urgency. Every
ODR field, workflow, prompt, screen, dialog, wizard step, dropdown,
toggle, and interaction must pass this test before merge.

---

## 1 · The Foreman Test (the only test that matters)

Before any ODR change ships, answer this single question honestly:

> **"Would a foreman complete this**
> **on a phone,**
> **standing in mud,**
> **wearing gloves,**
> **at 5:30 PM,**
> **after a 12-hour shift?"**

If the honest answer is **NO**, the change does **not ship as scoped.**

Implementation teams MUST then choose one of the following remediations
— never push complexity onto the field user:

| Remediation | When to apply |
|---|---|
| **Remove it** | If it is not load-bearing for the operational record |
| **Hide it** | If it is needed but not now (advanced toggle / power user only) |
| **Auto-populate it** | If it can be derived from prior fields, crew context, or job site |
| **Infer it** | If a deterministic rule (OGC, crew-type, site-type) can fill it |
| **Move it to Superintendent** | If it requires field-leadership judgment, not foreman entry |
| **Move it to PM** | If it is a project-level decision, not a daily-record field |
| **Move it to Operations** | If it is a back-office reconciliation, not a field action |

The **forbidden remediation** is _"add a tooltip / coaching prompt /
training video and ship the burden anyway."_ Coaching reduces friction
but **never replaces simplicity.**

## 2 · Success Metric · time-to-complete

The single quantitative gate for foreman ODR completion:

| Bound | Value |
|---|---|
| **Target** | < 5 minutes |
| **Stretch goal** | < 3 minutes |
| **Hard ceiling (regression)** | 7 minutes — anything above this is a P0 |

Measurement is end-to-end on a real device under real field conditions
(gloves, sunlight, intermittent connectivity). Synthetic timings on a
desktop browser are **not** valid evidence.

## 3 · The Compounding Rule

> **The platform may become more intelligent.**
> **The foreman experience must become simpler.**

Every release — without exception — must hold or reduce foreman
completion time. Intelligence accrues to the platform (auto-fill,
inference, projection). Burden does not accrue to the foreman.

If a release would increase foreman completion time, the work either:

- moves to Superintendent / PM / Operations workflows, or
- becomes a background system action (no operator step), or
- is deferred until inference can absorb it.

## 4 · Scope · what this doctrine governs

This test applies to **all** of the following ODR surfaces and any
future surface that touches a foreman's hands:

- `OdrNew.jsx` (foreman entry · 9-step wizard)
- `OdrCenter.jsx` (FL ODR Center · Foreman "Mine" tab)
- `OdrTrustBanner.jsx` (operator-facing trust copy)
- Any new ODR field added to `ODR_DATA_MODEL.md`
- Any new OGC coaching prompt added to `guidance_catalog.py`
- Any new amendment, attachment, or signature affordance
- Any offline-queue interaction (sync banners, retry prompts, conflict UI)
- Any voice / dropdown / autofill change
- Any push notification or in-app alert that asks a foreman to act

It does **not** govern Superintendent Review Center, PM Panel, Public
Viewer, Executive Dashboards, or Legal Audit surfaces — those have
different operator personas and may carry richer interaction.

## 5 · Approval flow (mandatory before merge)

Every ODR PR that adds, modifies, or repositions a field/screen/prompt
must include the following block in its description:

```
## ODR Simplicity Test
- Foreman completion test: [PASS / FAIL]
- Time-to-complete impact: [Δ seconds]
- Mud / gloves / 5:30 PM scenario: [Justification]
- Remediation taken (if FAIL): [Remove / Hide / Auto-populate /
  Infer / Move to Super / Move to PM / Move to Ops]
```

PRs missing this block are **not eligible for merge.** Reviewers
treat a `FAIL` with no remediation as a hard block.

## 6 · Anti-patterns this doctrine forbids

The following patterns are explicitly forbidden in foreman-facing
ODR surfaces:

1. **Modal stacks** — never more than one modal open at a time
2. **Multi-step wizards beyond 9 steps** — current 9-step entry is the ceiling
3. **Required free-text fields beyond the narrative box** — voice + dropdown only
4. **Required PDF generation by foreman** — auto-generated downstream
5. **Required PM-style approvals from foreman** — never request approval from the field
6. **Punitive coaching tone** — never "you forgot…" or "you must…"
7. **Aesthetic loudness** — colored badges, exclamation marks, urgency pills on the foreman path
8. **Login walls inside the entry flow** — foreman is already authenticated; do not re-prompt
9. **Telemetry-driven UI** — foreman UI must not change shape based on how the foreman is performing
10. **Onboarding interruptions** — first-time onboarding shows once, never blocks subsequent entries

## 7 · Operator escalation path

Any reviewer, PM, Superintendent, or executive who observes a violation
of this doctrine in the field has standing authority to:

- File a P0 simplicity regression
- Halt the next release until remediated
- Request a Superintendent shadow walk to capture the friction

The escalation does not require engineering approval — operator
authority on simplicity overrides developer convenience.

## 8 · Inheritance

This doctrine inherits from and reinforces:

- `OPERATIONAL_CALMNESS_DOCTRINE` (calm UI principles)
- `MOBILE_UX_REFINEMENT_AUDIT.md` (V-Prelude mobile polish list)
- `DAILY_REPORT_FIELD_TRUST_REVIEW.md` (TRUST-1 field doctrine)
- `ODR_TRUST_BANNER_DOCTRINE.md` (operator-facing trust copy)
- `CROSS_PORTAL_COACHING_STANDARD.md` (non-punitive coaching contract)

Any divergence from these requires the documentation, justification,
review, and approval flow defined in
`ODR_PLATFORM_INHERITANCE_DOCTRINE.md`.

## 9 · M1 authorization gate

🛑 **M1 (migration · dual-write · pilot) may not begin** until this
doctrine is registered and acknowledged by the operator review.

This is a **Doctrine Lock** — not a guideline, not a recommendation,
not a best practice. It is a permanent quality contract on every
foreman-facing ODR surface.

---

_End of ODR_SIMPLICITY_TEST_DOCTRINE.md · permanent ODR approval gate._

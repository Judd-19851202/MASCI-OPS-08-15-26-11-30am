# FOCP FINAL DIRECTIVE · Operational Completion Doctrine

**Date entered**: 2026-06-02
**Authority**: Operator final directive (this session)
**Mode**: BINDING · supersedes all prior engineering-expansion instructions
**Scope**: All work performed by AI agents on this platform from this point forward

---

## 1 · The objective has changed

The objective is **no longer to build more software**.

The objective is to **prove the platform can operate without tribal knowledge and without executive intervention**.

This is a governance change, not a project change. Code velocity → operator-confidence velocity.

---

## 2 · The 7 Acceptance Tests

Every proposed unit of work must satisfy **all seven** before it is authorized. Failing any one disqualifies the proposal.

1. Improves user confidence.
2. Improves operational accountability.
3. Reduces training time.
4. Reduces support calls.
5. Improves adoption.
6. Improves Customer #2 readiness.
7. Is verified by actual user behavior.

A "yes" against test 7 means the proposed work has been validated against an observed operator action or a real Customer #2 simulation, not against AI-generated speculation about what an operator might want.

---

## 3 · The 4 Pre-Authorization Proofs

Before any new feature is authorized, the proposer must demonstrate, with evidence:

- **A. Prove it does not already exist.** Show grep / source citation against current `/app/`. Stale registers are not evidence; only present source is.
- **B. Prove users actually need it.** Show a real operator quote, transcript, or session recording. No "operators probably want…" — observed reality only.
- **C. Prove it simplifies operations.** Show the before/after operator path with step count + decision count reduced.
- **D. Prove it will be used.** Show the trigger event that drives an operator to the surface ≥ 1×/week in normal operations.

Failing to produce evidence for any letter → proposal is REJECTED and no engineering happens.

---

## 4 · Priority Order (post-directive)

| Rank | Priority | Owner | Status |
|---|---|---|---|
| 1 | Reality Validation (real operators) | Operator-led | BLOCKED on operator participation (TR-D002) |
| 2 | Training / Coaching / Spanish parity | Operator-led + AI-supportable | BLOCKED on operator inputs (TR-D001 · TR-D004) |
| 3 | Operator Confidence Layer | AI-supportable IFF priorities 1+2 produce evidence | Awaits authorization gated by Proof B |
| 4 | Customer #2 simulation | Operator-led + AI-supportable | BLOCKED on operator account / tabletop format (TR-D003) |
| 5 | Final Operational Certification | Operator-led declaration | Awaits 1–4 |

Note: The 4 engineering items still in the Truth Register (TR-0003 Sub/Vendor archive · TR-0004 verb harmonization · TR-0007 constraint reopen · TR-0008 lifecycle endpoint audit) are **frozen** under this directive unless an operator submits a Proof B + Proof D for each.

---

## 5 · STOP conditions (binding)

The AI agent will NOT:

- Search for new modules to build.
- Invent new features.
- Expand scope beyond the directive currently in front of it.
- Begin coding without a passing 7-test + 4-proof check signed off by the operator.
- Auto-promote a Truth Register engineering finding from ACTIVE to IN_PROGRESS without operator authorization.

The AI agent WILL:

- Wait for operator directives.
- Run READ-ONLY discovery sweeps when explicitly authorized.
- Build operator confidence / training / coaching surfaces ONLY when an authorization comes with evidence-of-need.
- Re-verify any Truth Register finding against current source before responding to a directive that references it.

---

## 6 · Pre-staged AI-supportable artifacts (READ-ONLY, no code)

These are the only kinds of artifact the AI agent may **propose** to the operator during Operational Completion mode without being asked. They do not constitute work; they are governance documents.

- Reality-Validation interview script (Priority 1)
- Training material reality-match checklist (Priority 2)
- Spanish translation parity audit checklist (Priority 2)
- Operator Confidence Layer **definition** (Priority 3) — what it is, what it isn't, what evidence would unlock it
- Customer #2 simulation tabletop script (Priority 4)
- Final Operational Certification template (Priority 5)

Each of the above is a TEXT artifact, not code, and stays in `/app/memory/`.

---

## 7 · Governance linkage

- This directive is the highest-precedence governance document on the platform from 2026-06-02 forward.
- `TRUTH_REGISTER.md` continues to track findings but **no engineering item may move to IN_PROGRESS** without this directive's authorization gate clearing.
- `FORGEDOPS_OPERATIONAL_COMPLETION_MASTER_PLAN.md` is now read as the historical engineering roadmap. The active roadmap is this directive's Priority Order.
- `FOCP_COMPLETION_RELEASE_1_TR0005_BUNDLE.md` + `FOCP_COMPLETION_RELEASE_2_TR0001_BUNDLE.md` + `FOCP_COMPLETION_RELEASE_2_TR0002_BUNDLE.md` are the last engineering bundles. No Release 3 is anticipated under this directive without operator Proof B + D.

---

## 8 · Acknowledgement

The AI agent (E1) acknowledges receipt of this directive and confirms operation under its terms. Any AI-initiated proposal that violates §5 STOP conditions is, by definition, **out of scope** and must be refused.

End of FOCP FINAL DIRECTIVE doctrine.

# RFI System Doctrine
## Phase V.0 · Architecture & Governance · 2026-05-27

> Authoritative doctrine for the MASCI Ops RFI subsystem. This document
> precedes any code. It is the lens through which every workflow,
> screen, permission, backup, and integration decision will be judged.

---

## 1 · Purpose

MASCI Ops RFI is the **field-first operational record** for every
Request For Information raised against a contract. It is not generic
construction-management software, not a Procore clone, not a paper
process digitized. It is operational infrastructure for DOT, FAA, and
heavy-civil work executed under field pressure.

---

## 2 · What an RFI IS (in MASCI doctrine)

| Property | Meaning |
|---|---|
| **Operational record** | A field issue or contract clarification that requires a documented response before work proceeds without exposure. |
| **Schedule artifact** | Every RFI is potentially a constraint. The system surfaces that linkage by default. |
| **Legal artifact** | Each submitted RFI is a locked snapshot with full lineage. The operational record is also the dispute record. |
| **Field-driven** | Drafts originate in the dirt at 6:15am, not in an office at 2pm. |
| **PM-owned, externally collaborative** | PM is the contract custodian. CEI / Engineer / Owner / FAA / DOT consume and respond via tokenized links. |
| **Doctrine-compliant** | Calmness, terminology, coaching, escalation, mobile, and visual standards apply identically. |

## 3 · What an RFI is NOT

- **Not a chat thread.** Conversations belong on Basecamp / phone. The RFI is the formal record.
- **Not a punch list item.** Punch is closeout; RFI is mid-work clarification.
- **Not a change order.** RFIs *can* convert to Change Conditions but the conversion is explicit and audited.
- **Not a generic ticket.** Each RFI carries DOT/FAA-grade metadata (station, pay item, plan sheet, spec ref).
- **Not casual.** No casual delete. No silent edit after submission.

---

## 4 · Ownership Model

```
   FIELD                  OFFICE                 EXTERNAL
   ─────                  ──────                 ────────
Superintendent  →  PM (custodian)  →   CEI / Engineer / Owner
   drafts             formalizes          responds
                       submits             via tokenized link
                       routes              (no account needed)
                                ↓
                       Field executes
                       operational
                       resolution
                                ↓
                       PM closes /
                       converts /
                       logs impact
```

| Role | Authority |
|---|---|
| Superintendent | Create draft, attach photo / station / impact, request PM review |
| PM | Edit draft, formalize, submit, route, log response, close, void with reason, convert to change condition |
| Safety Manager | Read all · flag safety/compliance exposure · cannot edit body |
| Dispatch | Read RFIs with access/phasing/haul impact only |
| Admin | Full read · audit · cannot bypass submission lock |
| Executive | Read · escalation visibility · cannot edit |
| CEI / Engineer / Owner / DOT / FAA | Tokenized read + respond · no account required initially |

---

## 5 · Field-First Discipline

Superintendent workflow must complete a draft RFI in **≤ 60 seconds** on a
phone with one hand. Required for that target:

- Photo-first capture (camera opens immediately on "New RFI")
- Voice-to-text for the contractor question and field condition
- Auto-stamped station/offset from last daily report (override-able)
- Auto-pulled project, contract, discipline from the user's scope
- "Send to PM for review" as the only required action

Any feature that makes the field path slower than this is **rejected by doctrine**.

---

## 6 · Lock-and-Snapshot Principle

When PM clicks **Submit** the system MUST:

1. Freeze the body of the RFI as an immutable snapshot (Mongo doc with `submitted_at`, `submitted_by`, `snapshot_hash`).
2. Generate the official PDF (rendered server-side · stored in R2).
3. Start the response clock.
4. Issue tokenized read/respond link(s) to external recipients.
5. Append `submitted` to the audit trail.

After submission, **no field on the submitted record is editable**. Any
correction or new information lands as a **Revision** with its own
snapshot, PDF, and audit entry. Original record never overwritten.

---

## 7 · Legal Defensibility Spine

Every state change carries:

- `actor` (user_id + display name at the time of action)
- `actor_role` (resolved from the role-template engine)
- `timestamp` (UTC ISO)
- `ip` and `user_agent` (when available)
- `from_state` → `to_state`
- `reason` (required for void / reopen / clarification request)
- `delta_hash` (md5 of before/after on editable revision fields)

Backups carry the full lifecycle. The legal question — *who changed
what, when, why, from what, to what?* — must be answerable for any
RFI at any time.

---

## 8 · Doctrine Inheritance

The RFI subsystem **automatically inherits** all of the following
without re-implementation:

- Operational Calmness Doctrine (UX_GOVERNANCE_RULES)
- Coaching / Subline Standard (≤ 14 words · CROSS_PORTAL_COACHING_STANDARD)
- Visual Loudness Doctrine (VISUAL_LOUDNESS_REDUCTION_PLAN)
- Escalation Hierarchy (SAFETY_ESCALATION_HIERARCHY_MAP §VI)
- Mobile Doctrine (MOBILE_NAVIGATION_STANDARD)
- Component Hierarchy (COMPONENT_HIERARCHY_STANDARD)
- Cross-Portal Continuity (CROSS_PORTAL_CONTINUITY_MATRIX)
- Governance Health instrumentation (GovernanceHealthChip)
- Doctrine Trendline participation (DOCTRINE_TRENDLINE.json)
- Auto-deploy checkpoint participation (`pre_deploy_check.sh`)

Any new RFI screen MUST appear in the visual doctrine baseline probe
and produce a record in the trendline. No bypass.

---

## 9 · External-First Bias

External parties (CEI, Engineer, Owner, FAA, DOT, Utility) interact
through **tokenized links first**. Full accounts come later, only if
demand justifies it. This is deliberate:

- DOT/CEI staff churn fast — account provisioning is overhead.
- Tokenized links audit cleanly without identity-management complexity.
- Reduces our attack surface.
- Matches existing operational habits (email + PDF + sign).

See `RFI_EXTERNAL_ACCESS_MODEL.md` for the precise envelope.

---

## 10 · Operational Calmness in RFI Surfaces

- One status pill per record. Slate by default; red ONLY for true critical-path / safety / compliance exposure.
- One CTA per card (neutral slate-800 · matches Safety Hub V2 P1B trim).
- No red badges for routine counts.
- No flashing, no animation, no "new!" decorations.
- Sublines ≤ 14 words.
- Coaching, not corporate.

---

## 11 · Scope of this Doctrine

- ✅ Defines the *intent* and *boundary* of the RFI subsystem.
- ✅ Inherits all platform governance automatically.
- ❌ Does NOT specify a database schema (see `RFI_WORKFLOW_LIFECYCLE.md` + Phase V.1).
- ❌ Does NOT specify a UI implementation (see `PM_RFI_SCHEDULE_PORTAL_ARCHITECTURE.md`).
- ❌ Does NOT authorize any code change in Phase V.0.

---

## 12 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade · ready for operator review
- **Implementation gate:** No code change until operator approves Phase V.1 plan

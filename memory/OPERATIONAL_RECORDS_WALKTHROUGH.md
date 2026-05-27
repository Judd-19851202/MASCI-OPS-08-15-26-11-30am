# Operational Records Walkthrough
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> **Read this first.** This is the guided tour of the future
> Operational Records experience. Every visual choice is locked here
> before any code is written. Doctrine reigns; pixels follow.

---

## 0 · How to Read This Walkthrough

- All screens are **fixed-width ASCII wireframes** in the companion docs.
- Indentation and box-drawing characters approximate real spacing.
- Coaching copy is **verbatim** — what ships will say exactly this.
- Color names use existing platform tokens (slate-600, indigo-700, red-700, etc.).
- Nothing in this pass mounts on the live PM portal.

---

## 1 · Reading Order (operator review)

| Step | Doc | Why now |
|---|---|---|
| 1 | `PHASE_V0A_OPERATOR_REVIEW_GUIDE.md` | Review checklist + what we want signed off |
| 2 | `PM_OPERATIONAL_RECORDS_SIDEBAR_PREVIEW.md` | See where the new domain lands in PM V2 |
| 3 | `RFI_LIST_VISUAL_DOCTRINE.md` | The most-used PM surface |
| 4 | `SUPERINTENDENT_MOBILE_FLOW_CERTIFICATION.md` | The most-used field surface · ≤60s target |
| 5 | `CONSTRAINT_BOARD_VISUAL_MODEL.md` | The operational blocker board |
| 6 | `SCHEDULE_INTELLIGENCE_VISUAL_MODEL.md` | Activity list · Lookahead · Critical-path risk · Operational impact |
| 7 | `EXTERNAL_RESPONSE_PREVIEW_STANDARD.md` | What CEI / Engineer / Owner see |
| 8 | `RFI_PDF_VISUAL_PREVIEW.md` | The legal artifact |
| 9 | `OPERATIONAL_RECORDS_WALKTHROUGH.md` *(this doc)* | Re-read after — tie the pieces together |

---

## 2 · The Three Operator Personas

### 2.1 — PM (contract custodian · desktop primary, mobile capable)

Lives in `/pm`. Spends mornings reviewing RFIs that came in overnight,
afternoons formalizing drafts and issuing responses, evenings
reviewing exposure across all assigned projects.

- Sees the **Operational Records** sidebar domain first thing.
- Drives every state transition that matters legally.
- Owns the schedule import / activate workflow.
- Issues external tokens.

### 2.2 — Superintendent (field operator · mobile primary, desktop never)

Lives in `/field-leadership/portal`. Walks the site, dictates RFI
drafts on the phone, attaches a photo, sends to PM. ≤ 60 seconds.

- Sees a single tile on the FL hub: "RFI · Draft a Field Issue".
- Drafts only. Never submits. PM is the wall between field and contract.
- Sees drafts they originated + submitted RFIs on their assigned jobs.
- No constraint management. No schedule editing.

### 2.3 — External (CEI / Engineer / Owner · device-agnostic)

Lives at `/rfi/ext/:token_id/:token_slug`. Opens a link from an
email, reads the RFI, downloads the PDF, submits a response. No
account.

- No portal chrome. No internal navigation.
- One RFI per session.
- Tokenized, audited, time-boxed.

---

## 3 · The Operational Story (one-paragraph version)

> A superintendent finds a utility marked in the wrong place at
> Station 145+50. He pulls out his phone, taps **New RFI** in his
> Field Leadership hub, snaps two photos, dictates the field
> condition by voice, taps **Send to PM**. Twelve seconds. The PM
> sees the draft on her morning RFI list, opens it, adds plan-sheet
> references and a proposed solution, marks **Impacts Schedule**,
> picks the affected activity from the active P6 schedule, taps
> **Submit**. The system freezes a snapshot, generates the
> CEI-grade PDF, emails the assigned CEI a tokenized link. The CEI
> opens the link on his iPad, downloads the PDF, replies inside the
> portal. Response captured. PM accepts. The linked constraint
> resolves. The affected critical-path activity drops out of the
> **Critical Path Risk** view. The dispute file, should one ever
> arise three years later, contains every artifact with sha256
> manifests and full audit history. Nothing was retyped. Nothing
> got lost. Nothing slowed the field down.

This is the operational rhythm the prototype must preserve.

---

## 4 · The Doctrine the Prototype Must Inherit

| Doctrine | Source | Manifestation here |
|---|---|---|
| Operational Calmness | `UX_GOVERNANCE_RULES` | One CTA per card · neutral slate-800 · no flashing |
| Coaching Sublines | `CROSS_PORTAL_COACHING_STANDARD` | ≤ 14 words · operational · no marketing |
| Terminology | `RFI_COACHING_TERMINOLOGY_STANDARD` | Constraint · Exposure · Hold · Pending · etc. |
| Visual Loudness | `VISUAL_LOUDNESS_REDUCTION_PLAN` | ≤ 4 hue families per page · single stripe per domain |
| Escalation | `SAFETY_ESCALATION_HIERARCHY_MAP §VI` | Red ONLY for critical-path / safety / compliance / stoppage |
| Mobile | `MOBILE_NAVIGATION_STANDARD` | ≥ 44px touch targets · bottom-sheet sidebars |
| Cross-Portal Continuity | `CROSS_PORTAL_CONTINUITY_MATRIX` | Identical kicker / H1 / subline pattern across PM, HR, Safety |
| Governance Chip | `GOVERNANCE_HEALTH_CHIP_CERTIFICATION` | Surfaces exposure signals from this subsystem |
| Doctrine Trendline | `DOCTRINE_TRENDLINE_SYSTEM` | New pages register in baseline probe · trendline records |

If a prototype screen drifts from any of these, it gets rejected
**at this pass**, not after the build.

---

## 5 · What this Prototype is NOT

- ❌ A working PM portal screen — no React code mounted.
- ❌ A click-through Figma file — markdown wireframes only.
- ❌ A production design system — reuses existing PM V2 chrome.
- ❌ A negotiation about scope — scope is locked in V.0 docs.
- ❌ A backend prototype — zero backend touched.

It IS:
- ✅ A doctrine-locked visual + workflow rehearsal.
- ✅ A pre-build review artifact.
- ✅ A reference for V.1 implementation.

---

## 6 · Single-Red-Dot Doctrine (recap · because this matters everywhere)

Across every Operational Records surface:

- **Red** appears ONLY on:
  - Severity pills: `Critical-Path Impact`, `Safety / Compliance Exposure`.
  - The single-pixel red dot on an activity row in the schedule view
    when the activity is on the critical path AND has at least one
    active overdue constraint linked to it.
  - The 4pt left stripe on page 1 of an RFI PDF flagged as
    critical-path or safety/compliance exposure.

- **Orange** appears ONLY on:
  - Severity pills: `Action Required`.
  - The single dot indicator on a row with an active overdue
    constraint that is **not** on the critical path.
  - Aging buckets: an RFI within 24h of overdue.

- **Slate** is the default everywhere else.

No emerald success banners. No yellow warnings. No purple anything in
this subsystem. The eye knows where to go.

---

## 7 · Anti-Patterns Explicitly Forbidden

| ❌ Pattern | Why it's banned |
|---|---|
| Activity Gantt as the default schedule view | Cognitive load · field-unreadable |
| Multiple status pills on one row | Visual chaos · decision fatigue |
| Animated counters / live-updating numbers | Not calm |
| Notification banner sticky on every page | Notification hell |
| "AI suggestions" callouts | Marketing slop |
| Emoji severity indicators (🚨 🔥 ⚠) | Unprofessional · breaks DOT/FAA tone |
| Multi-color RFI status badges | Hue families budget violation |
| Toolbar with > 4 primary actions | Decision fatigue |
| Drag-to-reorder activities | Operationally meaningless · CPM math owns ordering |
| Inline editing of submitted RFIs | Audit-trail violation |

---

## 8 · Operator Sign-off Required

After reviewing all 9 deliverables in this pass, the operator should
sign off on these specific items:

- [ ] PM V2 sidebar adds the **Operational Records** domain in the proposed slot.
- [ ] The 5 sub-entries (RFI Center, Constraints, Schedule, Lookaheads, Operational Impact) read clearly to a PM.
- [ ] The PM RFI list density is calm without being sparse.
- [ ] The Superintendent mobile draft path is realistically completable in ≤ 60s.
- [ ] The Constraint Board reads as an operational blocker view, not a legal document index.
- [ ] The Schedule Intelligence views avoid Gantt complexity.
- [ ] The External Response page is professional enough for CEI / Engineer / Owner.
- [ ] The RFI PDF reads like a DOT/FAA-grade artifact.
- [ ] Nothing in the prototype breaks the existing platform's calmness contract.

When all nine boxes are checked, V.1 implementation can begin.

---

## 9 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade · ready for operator review
- **Implementation gate:** No code change until operator authorizes V.1.

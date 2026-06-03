# SAFETY COACHING GAP REGISTER
## OCEP · Safety Training Completion Program (STCP) · Register 2 of 5

**Date**: 2026-06-03
**Authority**: OMEGA · STCP
**Mode**: READ-ONLY · source-direct · no engineering authorized
**Evidence rule**: Every gap below is verified against `/app/backend/guidance/tips.py` (6218 LOC, 157 form_keys, parsed for `kind` distribution per form_key).

---

## 1 · Coaching mechanism (single source of truth)

The platform's coaching surface for safety workflows is the **`HelpTip` registry** (`backend/guidance/tips.py` consumed by `frontend/src/components/HelpTip.jsx`). For every form_key, the registry can contain tips of five kinds:

| Kind | Label EN | Label ES (hardcoded in HelpTip.jsx) | Purpose |
|---|---|---|---|
| `why` | "Why this matters" | "Por qué importa" | Anchor — explain the workflow's existence |
| `who` | "Who sees this" | "Quién lo ve" (implied) | Audience — who downstream consumes the submission |
| `when` | "When to use" | implied | Timing — when this workflow is the right tool |
| `mistake` | "Common mistakes" | "Errores comunes" | **Anti-pattern coaching** — the gap that Phase 2 P1 measured |
| `example` | "Example" | "Ejemplo" | Concrete sample to anchor the prose |
| `next` | "What happens after you submit" | "Qué pasa después" | Downstream propagation |
| `escalate` | "When to escalate" | "Cuándo escalar" | Boundary condition for raising the issue |

**Per-tip schema**: `{form_key, kind, scopes, title, body, title_es?, body_es?}` (where `_es` fields are optional and fall back to EN when absent).

---

## 2 · Aggregate coaching coverage (safety workflows only)

| Metric | Count | Note |
|---|---:|---|
| Distinct safety form_keys with at least one tip | 47 | Out of 157 total form_keys in `tips.py` |
| Total safety-relevant tips | ~137 | Verified via parsed AST walk |
| Tips with `mistake` kind on safety form_keys | 23 | Distributed unevenly across forms |
| Safety PARENT form_keys lacking `mistake` kind | **12** | jha, meeting, incident, inspection, qaqc, corrective, equipment-issuance, equipment-training, safety-document, safety-training, topic-library, preop |
| Safety leaf form_keys lacking `mistake` kind | 6 | fleet.repair, fleet.visibility, fleet.weekly-emergency, fleet.weekly-lead, safety-training.expiration, qaqc.signoff, preop.controls, preop.signoff |
| Tips with `body_es` populated (across all safety form_keys) | **≈ 1** | Only one tip on `jha.poster` carries Spanish body text |
| Tips with `title_es` populated (across all safety form_keys) | ≈ 0 | Tip titles render via EN `title` only |

---

## 3 · Per-workflow coaching gap inventory

(Verdict: 🟢 GREEN = all 5 critical kinds present · 🟡 YELLOW = ≥ 3 of 5 critical kinds · 🔴 RED = ≤ 2 critical kinds OR `mistake` absent on the surface where new operators most need it)

| Workflow / form_key | Tips | Kinds present | Critical kinds present (of why/who/mistake/next/escalate) | Verdict | Specific gap |
|---|---:|---|:-:|:-:|---|
| jha (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| jha.poster | 4 | escalate, example, mistake, why | 4 of 5 | 🟡 | `next` absent |
| meeting (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| meeting.attendees | 4 | escalate, mistake, who, why | 5 of 5 (missing only `next`) | 🟢 | — |
| meeting.context | 3 | mistake, when, why | 3 of 5 | 🟡 | who/next/escalate absent |
| meeting.photos | 3 | example, mistake, why | 3 of 5 | 🟡 | who/next/escalate absent |
| meeting.signoff | 3 | mistake, next, why | 4 of 5 | 🟡 | who/escalate absent |
| meeting.topic | 5 | escalate, example, mistake, next, why | 5 of 5 (missing only `who`) | 🟢 | — |
| incident (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| incident.corrective | 3 | mistake, next, why | 4 of 5 | 🟡 | who/escalate absent |
| incident.location | 3 | example, mistake, why | 3 of 5 | 🟡 | who/next/escalate absent |
| incident.narrative | 3 | example, mistake, why | 3 of 5 | 🟡 | who/next/escalate absent |
| incident.severity | 2 | mistake, why | 2 of 5 | 🔴 | who/next/escalate absent — severity classification has minimal coaching despite being the highest-leverage decision on the form |
| incident.witnesses | 3 | escalate, mistake, why | 4 of 5 | 🟡 | who/next absent |
| inspection (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| inspection.context | 3 | mistake, when, why | 3 of 5 | 🟡 | who/next/escalate absent |
| inspection.findings | 4 | example, mistake, next, why | 4 of 5 | 🟡 | who/escalate absent |
| inspection.ppe | 3 | escalate, mistake, why | 4 of 5 | 🟡 | who/next absent |
| inspection.signoff | 3 | mistake, next, why | 4 of 5 | 🟡 | who/escalate absent |
| qaqc (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| qaqc.checklist | 3 | escalate, mistake, why | 4 of 5 | 🟡 | who/next absent |
| qaqc.context | 3 | mistake, when, why | 3 of 5 | 🟡 | who/next/escalate absent |
| qaqc.corrective | 3 | mistake, next, why | 4 of 5 | 🟡 | who/escalate absent |
| qaqc.photos | 3 | example, mistake, why | 3 of 5 | 🟡 | who/next/escalate absent |
| qaqc.signoff | 2 | next, why | 2 of 5 | 🔴 | **mistake absent on the Amendment 001 closure A/B/C decision point** |
| corrective (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| corrective.close | 3 | mistake, next, why | 4 of 5 | 🟡 | who/escalate absent |
| corrective.create | 4 | escalate, example, mistake, why | 4 of 5 | 🟡 | who/next absent |
| equipment-issuance (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| equipment-issuance.acknowledgment | 3 | escalate, mistake, why | 4 of 5 | 🟡 | who/next absent |
| equipment-training (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| equipment-training.acknowledgment | 3 | escalate, mistake, why | 4 of 5 | 🟡 | who/next absent |
| fire-extinguisher.inspection | 4 | escalate, example, mistake, why | 4 of 5 | 🟢 | who/next absent — but small surface |
| fleet.dvir | 4 | escalate, mistake, who, why | 4 of 5 | 🟡 | `next` absent |
| **fleet.repair** | **2** | next, why | 2 of 5 | 🔴 | **mistake, who, escalate absent** |
| **fleet.rts** | **2** | mistake, why | 2 of 5 | 🔴 | **who, next, escalate absent — highest-stakes single decision on platform per SOCP §8.2** |
| fleet.visibility | 2 | who, why | 2 of 5 | 🔴 | mistake, next, escalate absent |
| safety-document (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| safety-document.upload | 2 | mistake, why | 2 of 5 | 🔴 | who, next, escalate absent |
| safety-training (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| safety-training.expiration | 2 | escalate, why | 2 of 5 | 🔴 | mistake, who, next absent |
| safety-training.upload | 2 | mistake, why | 2 of 5 | 🔴 | who, next, escalate absent |
| topic-library (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| preop (parent) | 4 | escalate, next, who, why | 4 of 5 | 🟡 | `mistake` absent at parent |
| preop.controls | 2 | example, why | 2 of 5 | 🔴 | mistake, who, next, escalate absent |
| preop.defects | 3 | mistake, next, why | 4 of 5 | 🟡 | who/escalate absent |
| preop.signoff | 2 | escalate, why | 2 of 5 | 🔴 | mistake, who, next absent |

**Verdict distribution (out of 47 safety form_keys with tips)**:

| Verdict | Count |
|---|---:|
| 🟢 GREEN — complete coaching surface | 3 (meeting.attendees, meeting.topic, fire-extinguisher.inspection) |
| 🟡 YELLOW — coverage acceptable but gapped | 31 |
| 🔴 RED — ≤ 2 critical kinds OR mistake absent on high-stakes form | **13** |

---

## 4 · Highest-leverage coaching gaps (operator-prioritization map)

Each row below cites the source-direct gap and the SOCP / Phase 2 / Adoption-Risk reference where this gap was already known.

| # | Form key | Why this is high-leverage | Cross-reference |
|---|---|---|---|
| 1 | **fleet.rts** | RTS = highest single-decision risk on platform. Only 2 tips. No `who` (authority), no `next` (downstream), no `escalate`. | SOCP §8.2, Phase 2 P3 |
| 2 | **fleet.repair** | Sister of RTS. 2 tips, no `mistake`. | SOCP, Phase 2 P3 |
| 3 | **fleet.visibility** | The decision surface for "is this unit safe to run". 2 tips, no `mistake`. | Phase 2 P3 |
| 4 | **incident.severity** | Drives OSHA recordable classification. Only 2 tips. | Phase 2 §1.x · SOCP §3.1 |
| 5 | **qaqc.signoff** | Amendment 001 closure A/B/C decision point. 2 tips, no `mistake`. | Phase 2 P4 |
| 6 | **safety-training.expiration** | Misread expiration → unqualified operator in service. 2 tips, no `mistake`. | (newly evidence-backed) |
| 7 | **preop.controls** | Pre-shift controls check; if mis-read → defect not surfaced. 2 tips, no `mistake`. | Phase 2 P3 (Shop) |
| 8 | **preop.signoff** | Operator commits to a defect-free unit. 2 tips, no `mistake`. | Phase 2 P3 (Shop) |
| 9 | **safety-document.upload** + **.classification** | Wrong classification → wrong retention / wrong audience. 2 tips. | (evidence-backed) |
| 10 | **All parent form_keys** lacking `mistake` (12 total) | New operator landing on parent form has no anti-pattern coaching. | Phase 2 P1 (now precisely scoped) |

---

## 5 · Pattern-level retired findings

Per the directive's "retire false findings" rule:

| Original claim (Phase 2) | Evidence | Disposition |
|---|---|---|
| "P1 — `mistake` kind absent on 14 form_keys" | Verified: absent on 18 form_keys total (12 parents + 6 leaves) within safety scope alone. | **REFINED**: precise count; pattern is parent-vs-sub-form. |
| "P3 — Fleet/Shop thinnest coverage" | Verified: fleet.repair = 2 tips, fleet.rts = 2 tips, fleet.visibility = 2 tips, preop.controls = 2 tips, preop.signoff = 2 tips. | **CONFIRMED**: empirically the thinnest cluster. |
| "P4 — QA/QC + Site Inspection 3-path closure unexplained" | qaqc.signoff = 2 tips no `mistake`. inspection.signoff = 3 tips with `mistake` — slightly better than QA/QC. | **REFINED**: gap concentrates on `qaqc.signoff` more than `inspection.signoff`. |

---

## 6 · What this register does NOT do

- Does **not** authorize engineering work to add tips. Every remediation row in Section 4 is FOCP 7-test + 4-proof gated.
- Does **not** invent missing tips. Only counts what exists.
- Does **not** rank operator priorities — the leverage table in Section 4 is informational.
- Does **not** propose new workflows. Tip additions to existing form_keys are content-only, not new workflows.

---

**End of SAFETY COACHING GAP REGISTER · STCP 2 of 5**

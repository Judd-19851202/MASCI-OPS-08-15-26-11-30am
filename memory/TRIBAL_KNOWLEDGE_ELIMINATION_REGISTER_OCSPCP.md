# TRIBAL KNOWLEDGE ELIMINATION REGISTER · OCSPCP SCOPE
## OCEP · Operational Coaching & Spanish Parity Completion Program (OCSPCP) · 5 of 7

**Date**: 2026-06-03
**Authority**: OMEGA / FOCP DIRECTIVE — OCSPCP Phase 6
**Mode**: READ-ONLY · source-direct · NO content rewrites
**Companion**: Builds on `TRIBAL_KNOWLEDGE_ELIMINATION_REGISTER.md` (prior OCEP Phase 5, dated 2026-06-02). This file adds the OCSPCP Phase-6 source-direct grep audit and merges with prior findings.
**Purpose**: Identify references in coaching content that depend on verbal explanation / institutional knowledge / supervisor interpretation / unwritten rules. Surface them so they can be replaced with documented guidance under operator authorization.

---

## 1 · Source-direct grep audit (new, OCSPCP-specific)

Searches performed on `/app/backend/guidance/tips.py` and `/app/frontend/src/lib/topics/`:

| Pattern | Hits in `tips.py` body strings | Hits in topic files |
|---|---:|---:|
| "Jaymn" (case-insensitive) | 0 | 0 |
| "supervisor will" | 0 | 0 |
| "foreman will tell" | 0 | 0 |
| "ask your" | 0 | 0 |
| "call the office" | 0 | 0 |
| "will let you know" | 0 | 0 |
| "talk to" | 0 | 0 |
| "by convention" | 0 | 0 |

**Direct verbal externalization audit verdict**: 🟢 The platform coaching surface does **not** contain explicit references to Jaymn, supervisors, or undocumented human channels. Tips give operational guidance directly.

This is a positive finding and retires the inherited assumption that coaching content overtly defers to Jaymn.

---

## 2 · Implicit tribal-knowledge dependencies (OCSPCP-extended)

Despite the clean direct grep, the directive requires identifying items where the **operator likely cannot complete the workflow without external explanation**, even when the surface doesn't say "ask someone". These are inferred from the coaching gap evidence in OCSPCP 1–4 plus STCP / SOCP / TCP.

| # | Form_key / surface | Implicit dependency | Source-direct evidence | Documented guidance that would close it |
|---|---|---|---|---|
| 1 | `fleet.rts` | Who has authority to authorize RTS | 2 tips total; no `who`; no escalate; no LifecycleGuide | "RTS may be authorized only by [role] after [conditions]. Defects of severity RED may NOT be released." |
| 2 | `fleet.rts` | When NOT to authorize RTS | No `escalate` tip | "Refuse RTS when [conditions]. Escalate to [role]." |
| 3 | `fleet.rts` | What happens after RTS | No `next` tip | "After RTS, dispatch board updates, driver QR notice fires, unit returns to scheduling." |
| 4 | `qaqc.signoff` | Which of A/B/C closure path applies | Phase 2 P4 noted gap; only 2 tips | "(A) re-inspect passed · (B) corrective ≥ 20 chars · (C) exception PM+Safety dual sign-off ≥ 10 chars" |
| 5 | `incident.severity` | What qualifies as Recordable vs First-Aid vs Near-Miss | 2 tips; SOCP §3.1 ambiguity | "Recordable = OSHA criteria [list]. First Aid = [criteria]. Near Miss = no injury / no property damage." |
| 6 | `incident` parent | Attestation-flag definitions | AR-0016 (no per-flag def) | Per-flag tooltip |
| 7 | `payroll-variance` | Attestation-flag definitions | AR-0004 | Per-flag tooltip |
| 8 | `jha` parent | "Reconocer" legal-attestation breadth (ES) | SOCP §1.1 | Spanish-specific attestation copy clarification |
| 9 | `preop.signoff` | Ready-to-operate vs needs-shop threshold | No `mistake` tip | Threshold criteria |
| 10 | `safety-meeting` parent | What makes a meeting audit-valid | No lifecycle guide; parent missing `mistake` | Topic specificity, attendee verification, signoff completeness |
| 11 | `dispatch.transfers.lead-time` | Acceptable lead-time per load type | 2 tips; no thresholds | Threshold table |
| 12 | `safety-training.expiration` | When to outreach an employee | 2 tips total | Cadence + outreach script |
| 13 | `field-leadership.records.review-tone` | Acceptable vs unacceptable tone | Mistake tip exists; no examples | Sample EN + ES |
| 14 | `time-off-review.bereavement` | Bereavement policy specifics | Mistake + escalate; no policy doc inline | Inline summary OR policy-doc link |
| 15 | `recognition` | When recognition is compensation vs morale | 2 tips, no nuance | Tax-treatment guidance |
| 16 | Vendor Management | Archive workflow | TR-0003 | Archive lifecycle implementation OR explicit doctrine declaration |
| 17 | Asset Transfer reopen | No formal reopen | DOCTRINE-SILENT per TCP §13 | Doctrine decision |
| 18 | Operational Constraints reopen | Intentionally absent | TR-0007 (DOCTRINE-EXEMPT) | Doctrine note linkable from constraint detail page |

**18 documented implicit dependencies.** Every one traces to an existing form_key / page / workflow. Per Rule 1 (no new workflows), every remediation is a content addition or UI wiring against existing infrastructure.

---

## 3 · Items where the platform already eliminates tribal knowledge (no action needed)

| # | Item | Documented in |
|---|---|---|
| 1 | Reactivate-vs-Rehire (Employee Lifecycle) | `tips.py` `employee-lifecycle.rehire` (full kind battery) + glossary "Archive" + Phase Alpha doctrine — Phase 2 §1.7 PASS |
| 2 | Workflow lifecycle stages (Incident, Site, QA/QC, PV) | LifecycleGuide UI + lifecycle file WORKFLOW constants |
| 3 | 5-stage CAPA pipeline | AdminOperationalLanguage glossary CAPA entry (5 sections) |
| 4 | Excavation hazards (trenching, soil classification, potholing, spoil placement) | `excavation.es.js` decision-grade content (SOCP §2, §6, §7) |
| 5 | Heat Illness, Utility Exposure, PPE | Topic library coverage |
| 6 | Universal Undo doctrine | FOCP R2 § 8 declares EN-canonical for Recovery Stream |
| 7 | JHP version-replacement semantics | `i18n.js` JHP section + ack ledger preserves prior signature |
| 8 | Operational vocabulary (50 EN+ES entries) | AdminOperationalLanguage glossary |

When an operator asks a question about these surfaces, the platform answer is already in place. **No tribal dependency at these 8 surfaces.**

---

## 4 · Highest-leverage tribal-knowledge eliminations

If the operator authorizes one batch (per FOCP 7-test + 4-proof gate), the highest-leverage candidates:

| Rank | Item | Why |
|---|---|---|
| 1 | Fleet RTS `who` + `escalate` + `next` tips + LifecycleGuide | Closes platform's #1 risk. Eliminates the single most cited tribal decision. |
| 2 | Incident severity criteria tooltip | OSHA-recordable classification = #1 data-integrity decision in the field. |
| 3 | QA/QC closure path A/B/C tooltip | Phase 2 P4. Eliminates the "which path is right?" question. |
| 4 | Attestation-flag definitions (Incident + Payroll Variance) | AR-0016 + AR-0004. Eliminates tick-without-understanding pattern. |
| 5 | Glossary in-flow wiring | One UI pattern, 35-workflow impact. Eliminates the "where do I look up this term?" externalization. |

---

## 5 · Retired false findings (OCSPCP scope)

| Inherited claim | Verdict | Disposition |
|---|---|---|
| "Coaching content directly says 'ask Jaymn'" | Grep returns 0. | **RETIRED.** Surface is clean of direct externalization. |
| "Field crews routinely call Jaymn" | Behavioral assertion. Out of OCSPCP scope — no operator-behavior evidence collected. | **OUT OF SCOPE.** |
| "Glossary already eliminates tribal knowledge" | Glossary exists (~50 entries) but is admin-route-only and unwired in-flow. Tribal lookup is still required. | **REFINED.** Content exists; surface wiring does not. |
| "Training docs eliminate tribal knowledge" | Tribal knowledge is eliminated when the platform documents the answer IN the workflow surface, not in offline training. | **CLARIFIED.** OCSPCP-scope closure path is in-platform content, not training docs. |

---

## 6 · What this register does NOT do

- Does **not** author the missing content.
- Does **not** wire the glossary in-flow.
- Does **not** assert operator behavior (only platform-surface evidence).
- Does **not** propose new workflows. Per Rule 1, no workflow is created.
- Does **not** declare doctrine — only the operator can do that.

---

**End of TRIBAL KNOWLEDGE ELIMINATION REGISTER · OCSPCP 5 of 7**

# TRAINING REALITY MATCH MASTER CHECKLIST
## OCEP Phase 2 · Operational Completion Evidence Program

**Date opened**: 2026-06-02
**Authority**: OMEGA · OCEP
**Mode**: READ-ONLY · evidence checklist
**Status**: Awaits operator-supplied training artifact paths
**Scope**: Cross-reference every training artifact against current production reality

---

## 0 · Doctrine

Training is only useful when it teaches **today's platform**, not last quarter's. This checklist is the audit harness that produces:
- Per-workflow Training Accuracy Score (0–100)
- Overall Platform Training Accuracy Score (weighted)

The AI agent **cannot** verify training accuracy without:
1. Paths or transcripts of current training artifacts (Skywork videos, knowledge-base pages, SOP PDFs, etc.)
2. OR explicit operator authorization to extract training-equivalent content from current platform surfaces (which would constitute a build — currently OUT OF SCOPE)

If artifacts are unavailable, this checklist becomes an **operator-led** audit; the AI agent records the result.

---

## 1 · Training artifact inventory (operator to fill)

| Artifact type | Location / URL / Path | Last updated | Owner | Notes |
|---|---|---|---|---|
| Skywork video — Daily Reports |  |  |  |  |
| Skywork video — JHP |  |  |  |  |
| Skywork video — Incidents |  |  |  |  |
| Skywork video — QA/QC |  |  |  |  |
| Skywork video — Site Inspection |  |  |  |  |
| Skywork video — Equipment |  |  |  |  |
| Skywork video — Dispatch |  |  |  |  |
| Skywork video — HR |  |  |  |  |
| Skywork video — Safety Portal |  |  |  |  |
| Help content (`HelpTip` blocks) | `/app/frontend/src/components/HelpTip.jsx` + `topics/` | (in source) | Engineering | Embedded in app, auto-current |
| Guides PDFs |  |  |  |  |
| SOPs |  |  |  |  |
| Quick-starts |  |  |  |  |
| Knowledge base entries |  |  |  |  |
| Screenshots library |  |  |  |  |
| Walkthroughs (recorded sessions) |  |  |  |  |

Until the operator fills this inventory, the checklist below applies to **HELP CONTENT ONLY** (auto-current, baseline).

---

## 2 · Per-workflow audit matrix

For every workflow listed below, the operator runs an 8-point check. The AI agent cannot answer these — only the operator (or an interviewee) sitting next to the actual artifact + the actual platform can.

### 2.1 · Workflow list (29 workflows · derived from current source)

| # | Workflow | Primary route(s) | Doctrine reference |
|---|---|---|---|
| 1 | Daily Report submission | `/daily-reports/new` | iter452 + FOCP R2 |
| 2 | Daily Report office review | DR lifecycle | iter452 |
| 3 | Incident submission | `/incidents/new` | iter451 |
| 4 | Incident investigation + CAPA | Incident lifecycle | iter451 + iter453.7 |
| 5 | Incident closure + reopen | Incident lifecycle | iter451 + FOCP R2 |
| 6 | QA/QC deficiency intake | `/qaqc-inspections/new` | iter453 + Amendment 001 |
| 7 | QA/QC closure (3 paths) | QA/QC lifecycle | Amendment 001 REPLACE-5 |
| 8 | Site Inspection findings | `/inspections/new` | iter453 |
| 9 | Site Inspection closure | Site Inspection lifecycle | Amendment 001 REPLACE-4 |
| 10 | JHP file upload | `/admin/jha` | Pre-existing |
| 11 | JHP employee acknowledgement | `/jha` | FOCP R2 TR-0001 |
| 12 | JHP supervisor visibility | `/admin/jha-acknowledgements` | FOCP R2 TR-0001 |
| 13 | Equipment pre-shift inspection | Equipment routes | Pre-existing |
| 14 | Equipment defect → Shop | Fleet-ops | iter251 + iter295 |
| 15 | Repair lifecycle | Repair lifecycle | iter251 |
| 16 | Fire-extinguisher service | Safety portal | iter322+ |
| 17 | Dispatch board build | `/admin/dispatch` | iter392+ |
| 18 | Driver shift-start QR | Driver pages | iter393 |
| 19 | Driver qualification dashboard | HR portal | iter288 + iter312 |
| 20 | HR new-hire | HR portal | Phase Alpha |
| 21 | HR reactivate vs rehire | HR portal | Phase Alpha governance |
| 22 | HR termination | HR portal | Phase Alpha |
| 23 | Time-off request approval | HR queue | iter71 |
| 24 | Employee Request approval | HR queue | iter71 |
| 25 | Payroll Variance review | HR portal | iter452 + FOCP R2 |
| 26 | Payroll Variance finalize | PV lifecycle | iter452 (NO AUTO FINALIZE) |
| 27 | PO Request approve / reject | PM portal | iter72+ |
| 28 | Asset Transfer receive / reject | Field portal | iter48+ |
| 29 | Universal Undo (any workflow) | Lifecycle panels + `/admin/recovery-stream` | FOCP R2 TR-0002 |

### 2.2 · 8-point training match check (per workflow)

For each of the 29 workflows above, the operator records YES / NO / N/A for each:

| Check | Question | YES | NO | N/A |
|---|---|:-:|:-:|:-:|
| T1 | Training exists for this workflow | □ | □ | □ |
| T2 | Training was updated within the last 90 days | □ | □ | □ |
| T3 | Training narrates the workflow the way it actually runs in production today | □ | □ | □ |
| T4 | Every screenshot / clip in training matches the current screens | □ | □ | □ |
| T5 | Terminology in training matches platform terminology (e.g., "Pending Office Review" not "Pending Boss Review") | □ | □ | □ |
| T6 | Step sequence in training matches the current platform's required step order | □ | □ | □ |
| T7 | Routing / role gates in training match the current platform's auth surface | □ | □ | □ |
| T8 | Statuses in training match the current canonical status dictionary (`/app/frontend/src/lib/statusBadges.js`, post-FOCP R1) | □ | □ | □ |

**Per-workflow Training Accuracy Score** = (count of YES) / (count of YES + NO) × 100.
- N/A is excluded from the denominator (e.g., if a workflow has no screenshots in training, T4 = N/A).
- Score < 70 → workflow training is **STALE** → flagged for refresh.
- Score 70–89 → **PARTIAL** → spot remediation.
- Score ≥ 90 → **CURRENT**.

### 2.3 · Overall Platform Training Accuracy Score

Weighted average over the 29 workflows, weighted by hours/week the workflow runs in production:

| Workflow tier | Weight |
|---|---:|
| Daily-run (DR, Dispatch, Driver shift-start, JHP ack) | 4 |
| Frequent (Incident intake, Equipment pre-shift, Time-off) | 2 |
| Weekly (Payroll Variance review, Driver Qual review, Sub commitments) | 1 |
| Episodic (Reactivate, Reopen, Undo) | 0.5 |

Operator fills tier-weight if defaults are wrong. Overall score is the weighted mean.

---

## 3 · Special audit lanes

### 3.1 · Help-tip parity (in-source, auto-current)
The platform already ships an inline `<HelpTip/>` system fed by `/app/backend/guidance/tips.py` and `tips_es.py`. The AI agent CAN verify (read-only) that:
- Every workflow above has an `HelpTipBlock formKey="<workflow>"` in its primary page.
- Every English tip has a Spanish counterpart in `tips_es.py`.

Output: a one-row-per-workflow matrix in this file's §6 (operator fills after running the read-only scan).

### 3.2 · Doctrine references parity
For each workflow, confirm the training artifact's "version stamp" matches the most recent iteration that touched it. If training says "Mark Resolved" closes a QA/QC but production has Amendment 001 (re-inspection / corrective-action / exception), the training is **DOCTRINE-DRIFTED** — flagged separately from STALE.

### 3.3 · Visual parity
For every screenshot in training, the operator confirms:
- Header chrome matches current
- Status pill colors match (per post-FOCP R1 canonical status dictionary)
- Sticky-footer surfaces match (post-iter500 Rank #1 + ITER500 Rank #1 Targeted Correction)
- Acknowledge button + identity strip present on `/jha` screenshots (post-FOCP R2)

---

## 4 · Scoring template (operator fills)

| # | Workflow | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | Score | Tier weight | Status |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---:|---:|---|
| 1 | Daily Report submission |  |  |  |  |  |  |  |  |   |   |   |
| 2 | Daily Report office review |  |  |  |  |  |  |  |  |   |   |   |
| 3 | Incident submission |  |  |  |  |  |  |  |  |   |   |   |
| 4 | Incident investigation + CAPA |  |  |  |  |  |  |  |  |   |   |   |
| 5 | Incident closure + reopen |  |  |  |  |  |  |  |  |   |   |   |
| 6 | QA/QC deficiency intake |  |  |  |  |  |  |  |  |   |   |   |
| 7 | QA/QC closure (3 paths) |  |  |  |  |  |  |  |  |   |   |   |
| 8 | Site Inspection findings |  |  |  |  |  |  |  |  |   |   |   |
| 9 | Site Inspection closure |  |  |  |  |  |  |  |  |   |   |   |
| 10 | JHP file upload |  |  |  |  |  |  |  |  |   |   |   |
| 11 | JHP employee acknowledgement |  |  |  |  |  |  |  |  |   |   |   |
| 12 | JHP supervisor visibility |  |  |  |  |  |  |  |  |   |   |   |
| 13 | Equipment pre-shift inspection |  |  |  |  |  |  |  |  |   |   |   |
| 14 | Equipment defect → Shop |  |  |  |  |  |  |  |  |   |   |   |
| 15 | Repair lifecycle |  |  |  |  |  |  |  |  |   |   |   |
| 16 | Fire-extinguisher service |  |  |  |  |  |  |  |  |   |   |   |
| 17 | Dispatch board build |  |  |  |  |  |  |  |  |   |   |   |
| 18 | Driver shift-start QR |  |  |  |  |  |  |  |  |   |   |   |
| 19 | Driver qualification dashboard |  |  |  |  |  |  |  |  |   |   |   |
| 20 | HR new-hire |  |  |  |  |  |  |  |  |   |   |   |
| 21 | HR reactivate vs rehire |  |  |  |  |  |  |  |  |   |   |   |
| 22 | HR termination |  |  |  |  |  |  |  |  |   |   |   |
| 23 | Time-off request approval |  |  |  |  |  |  |  |  |   |   |   |
| 24 | Employee Request approval |  |  |  |  |  |  |  |  |   |   |   |
| 25 | Payroll Variance review |  |  |  |  |  |  |  |  |   |   |   |
| 26 | Payroll Variance finalize |  |  |  |  |  |  |  |  |   |   |   |
| 27 | PO Request approve / reject |  |  |  |  |  |  |  |  |   |   |   |
| 28 | Asset Transfer receive / reject |  |  |  |  |  |  |  |  |   |   |   |
| 29 | Universal Undo (any workflow) |  |  |  |  |  |  |  |  |   |   |   |

**OVERALL PLATFORM TRAINING ACCURACY SCORE**: ___ (weighted)

---

## 5 · Status thresholds

| Composite | Verdict |
|---|---|
| Overall < 60 | TRAINING UNFIT FOR ADOPTION |
| 60–74 | TRAINING ADEQUATE WITH OPERATOR-LED SUPPLEMENT |
| 75–89 | TRAINING CURRENT WITH GAPS |
| ≥ 90 | TRAINING CERTIFIED |

Until Overall ≥ 75 the platform's Final Operational Certification (Phase 7) is HALTED.

---

## 6 · Help-tip parity matrix (AI-supportable scan output)

This section is the output of a **read-only** grep across `/app/frontend/src/` for `HelpTipBlock formKey="<workflow>"` and a parallel grep across `/app/backend/guidance/` for English + Spanish counterparts.

| Workflow | `formKey` in pages | EN tip in `tips.py` | ES tip in `tips_es.py` | Notes |
|---|:-:|:-:|:-:|---|
| (Operator-led: run `grep -rln "HelpTipBlock formKey" /app/frontend/src/`) |  |  |  |  |

(AI agent: when explicitly authorized for a read-only scan, populate this table. Not pre-populated to preserve the doctrine that this is an operator-driven audit.)

---

## 7 · Remediation register (operator fills as audit produces findings)

| # | Workflow | Finding | Severity | Training artifact | Suggested action | Status |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Severity scale:
- CRITICAL: training teaches an action that no longer exists or is dangerous to perform as taught
- HIGH: training teaches a stale step sequence or wrong terminology
- MEDIUM: screenshots / visuals drift from current platform
- LOW: phrasing / tone drift, no operational impact

---

**End of TRAINING REALITY MATCH MASTER CHECKLIST · OCEP Phase 2**

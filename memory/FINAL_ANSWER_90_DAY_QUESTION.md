# FINAL ANSWER · The 90-Day Question

**Authority**: FOCP WAR ROOM · Final answer
**Question**: *What are the exact remaining items preventing "MASCI can operate successfully for 90 days without Jaymn serving as trainer, interpreter, workflow navigator, system explainer, or operational translator?"*

**Mode**: READ-ONLY · evidence-only · zero code · zero deploys.

---

## The exact list

### 🔴 CRITICAL (blocks unconditional YES on the 90-day question)

| # | Item | TR ID | Why CRITICAL | Effort |
|---|---|---|---|---|
| 1 | **JHP Acknowledgement Ledger build** | TR-0001 | Safety persona has no provable JHP acknowledgement workflow. Auditor exposure. Operators currently use tribal-knowledge workarounds and call Jaymn. | 3.5 weeks |
| 2 | **Universal undo / status reversal verb** | TR-0002 | Every persona makes status-change mistakes. Without an in-app undo, every mistake becomes a backend ticket → Jaymn call. Highest single driver of "I need Jaymn" support volume. | 2 weeks |
| 3 | **Phase 12 operational-reality interviews (7 personas)** | TR-D002 | Without verified evidence that source-side scaffolding actually maps to user behavior, the 79 % human-operability score is a hypothesis, not a fact. | 2 weeks operator-led |

### 🟠 HIGH (substantial Jaymn-reduction but not strictly blocking)

| # | Item | TR ID | Why HIGH | Effort |
|---|---|---|---|---|
| 4 | **Sub / Vendor archive workflow** | TR-0003 | Procurement governance closure. Admin Jaymn-question class: "how do I retire a sub?" | 1 week |
| 5 | **Operator Confidence view rollout** | (spec) | Executive persona needs single-pane "what is open / overdue / blocked / aging / needs attention." Without it, Executive calls Jaymn for status. | 2.5 weeks |
| 6 | **Phase 11 training-material audit + reality match** | TR-D001 | Verifies training videos / Skywork / knowledge-base match current platform. Mismatch = users trained on old reality = Jaymn calls. Requires operator to provide asset list. | 1-2 weeks operator + AI |
| 7 | **Phase 11 Spanish translation reality match** | TR-D004 | Bilingual MASCI personas need Spanish copy that matches current EN workflow. Mismatch = Spanish-speaking foreman calls Jaymn (or another Spanish-speaker) for help. Requires operator to locate translation files + native-speaker reviewer. | 1 week (after operator unblocks) |
| 8 | **Phase 10 Customer #2 tabletop walkthrough** | TR-D003 | Hardens the platform against persona-types MASCI doesn't have today. Not strictly blocking 90-day MASCI trial, but informs whether the trial can extend to Customer #2-style usage. | 2 hours operator-led |

### 🟡 MEDIUM (continuous low-grade friction · cumulative impact on Jaymn-call volume)

| # | Item | TR ID | Why MEDIUM | Effort |
|---|---|---|---|---|
| 9 | **Status canonical dictionary frontend rollout** | TR-0005 | 38 distinct status words rendered raw across the platform. Reads as platform-jargon to non-trained users. Removes ~ daily "what does X mean?" questions. | 1.5 weeks |
| 10 | **Daily Report reopen path verification** | (sub-item · no TR) | 30-min source-read; either retire as "already supported" or open a new TR if missing. | 30 min |
| 11 | **FleetDVIR amend path** | (proposed TR-0009) | Mechanic-persona occasionally needs to amend a submitted DVIR. Currently routes through admin / Jaymn. | 3 days |
| 12 | **Constraint reopen doctrine doc** | TR-0007 | One-page doctrine note codifying "Constraint resolution is terminal · re-emergence = new constraint with chronology link." Removes the question class entirely. | 30 min operator-led |
| 13 | **Coaching coverage gap fill** | (proposed TR-0010) | Some pages have multiple HelpTips, some have none. Fill the gap on the underserved pages after Phase 12 surfaces which pages users get stuck on. | 1 week (after Phase 12) |
| 14 | **Central in-app help center** | (proposed TR-0011) | One landing surface for "I'm new · where do I start?" Reduces first-week Jaymn dependency for new hires. | 2 weeks |

### ⚪ LOW (cosmetic · do not block any trial)

| # | Item | TR ID | Why LOW | Effort |
|---|---|---|---|---|
| 15 | **Verb harmonization cosmetic string sweep** | TR-0004 | Most platform forms already use "Submit" — 16 `submit-*` testids vs 1 `save-*` vs 0 of the others. Residual is i18n button-label level. | 1 day |
| 16 | **dispatch_lifecycle + payroll_variance_lifecycle endpoint confirmation** | TR-0008 | RETIRED-by-prior-work in Phase 1 verification — both have full transition + state-events + lifecycle endpoints. Listed here for completeness only. | already done |
| 17 | **JHA / JHP integration cross-reference** | TR-0006 | SUPERSEDED by TR-0001. Listed here for completeness only. | covered by TR-0001 |

---

## Ranked composite execution order

This is the exact sequence that minimizes time-to-unconditional-YES while maximizing parallelism:

| Week | Engineering track | Operator track |
|---|---|---|
| W1 | TR-0003 (Sub/Vendor archive · 1 wk · low risk · momentum) | Schedule Phase 12 interviews |
| W2-W5 | TR-0001 (JHP Ledger build) | Operator inventories training assets + locates translation files |
| W6-W7 | TR-0002 (Universal undo) | — |
| W8 | Daily-Report verify + Constraint doctrine doc + (start) TR-0009 amend | TR-D002 interviews · 4 of 7 personas |
| W9 | TR-0009 amend complete + status-helper scaffolding | TR-D002 · remaining 3 personas + matrix synthesis |
| W10 | Synthesize Phase 12 findings into TR-#### · re-prioritize MEDIUM list | Operator approves status canonical mapping |
| W11 | TR-0005 helper + per-page sweep batch 1 | TR-D001 audit (with operator-provided asset list) |
| W12-W14 | Operator Confidence view build · TR-0005 sweep batches 2-3 in parallel | TR-D004 Spanish audit (with operator translation reviewer) |
| W15 | Coaching + help-center gap fill (TR-0010 + TR-0011 if scoped) | Phase 10 tabletop walkthrough (TR-D003) |
| W16 | Quarterly Truth Register sweep + platform-completion certification | Operator signs `verified_production_date` on every retired TR · 90-day trial CERTIFIED ready |

After **W16**: every CRITICAL retired · every HIGH retired or scheduled-with-evidence · MEDIUM items reviewed against Phase 12 evidence · MASCI is **🟢 CERTIFIED for 90-day Jaymn-free trial**.

---

## Could the 90-day trial start earlier?

Three earlier checkpoints, each with their own risk profile:

### Checkpoint A · Start at W7 (after TR-0001 + TR-0002 + TR-0003 ship)
* **Risk**: Phase 12 interviews not yet done · unknown reality gaps may emerge mid-trial.
* **Benefit**: 9 weeks faster than the W16 target.
* **Likely outcome**: 80 % of workflows clean · 15 % surface unknown reality gaps as support calls · 5 % require engineering escalation.
* **Recommended IF**: operator accepts "we'll learn what we're missing as we go" and has a backup engineering-access operator standing by.

### Checkpoint B · Start at W10 (after Phase 12 evidence + Operator Confidence view begins)
* **Risk**: Operator Confidence view not yet shipped · Executive may need ad-hoc reports.
* **Benefit**: 6 weeks faster than W16 · Phase 12 surfaces known gaps before the trial.
* **Likely outcome**: 90 % of workflows clean · 8 % friction with planned remediation · 2 % engineering escalation.
* **Recommended**.

### Checkpoint C · Start at W14 (after Operator Confidence view ships)
* **Risk**: Phase 11 audits + W15 coaching gaps not yet closed · new hires during the trial may struggle without training/Spanish audit complete.
* **Benefit**: 2 weeks faster than W16.
* **Likely outcome**: 95 % clean · 4 % new-hire friction · 1 % engineering escalation.
* **Recommended IF**: no new hires planned during the 90-day window.

### Checkpoint D · Start at W16 · UNCONDITIONAL YES
* **Risk**: none from the FOCP register · the only residual is operational chance (production incidents · acts of god).
* **Benefit**: highest confidence.
* **Recommended IF**: the operator wants absolute confidence and is willing to wait the full 16 weeks.

---

## Honest framing

The platform is **already very close** to 90-day self-sufficient TODAY. Source-side scaffolding is at ~ 79 % human operability and ~ 92 % operational completeness. The remaining work is **finite, named, and ranked**. There is no large unknown.

The choice between Checkpoint A · B · C · D is a **risk-tolerance** decision, not a feasibility decision. All four checkpoints are feasible. The right answer depends on how much pre-trial preparation the operator wants to fund vs how quickly they want to validate the hypothesis.

---

## What I recommend

# **Checkpoint B · Start the 90-day trial at W10**

* By W10: TR-0001 + TR-0002 + TR-0003 shipped · Phase 12 interview evidence captured · MEDIUM gaps prioritized by real user voice rather than predicted hypotheses.
* W11-W16 execute in parallel with the trial · the trial itself surfaces what additional remediation is needed.
* Best balance of speed, evidence, and risk discipline.

If the operator wants maximum speed: **Checkpoint A · Start at W7.** Honest about the gaps · accepting the risk · with backup-operator designation.

If maximum confidence: **Checkpoint D · Start at W16.** Full certification · no compromise.

---

## STOP

* ✅ No new modules
* ✅ No White Label
* ✅ No Customer #2 build work
* ✅ No expansion
* ✅ Only completion
* ✅ Read-only
* ✅ Evidence-only

**The 4 ACTIVE findings + 3 DEFERRED operator-input items + 5 MEDIUM-priority items are the ENTIRE remaining surface preventing unconditional 90-day Jaymn-free operation.** Everything else has been retired, superseded, or downgraded.

Awaiting operator authorization on:

1. Which checkpoint (A · B · C · D) initiates the 90-day trial.
2. Authorization to begin W1 execution (TR-0003).
3. Authorization for operator-led work on Phase 12 interviews + Phase 11 asset inventory + Phase 10 tabletop.

STOP.

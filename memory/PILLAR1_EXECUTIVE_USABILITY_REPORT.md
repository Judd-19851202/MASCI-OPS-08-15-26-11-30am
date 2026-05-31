# Pillar 1 · Executive Usability Report (Phase 3)

**Batch:** Pillar 1 · Pre-Deployment Operational Certification · Phase 3
**Date:** 2026-05-31
**Scope:** Evaluate per-card actionability against the question *"If an executive opens this at 6:00 AM, could they determine what requires attention today?"*

---

## 1 · 6-AM Walkthrough · evidence-led

Live snapshot captured 2026-05-31 16:11Z. Imagining an Operations Director opening `/admin/command-center` cold:

### 1.1 · Pulse Strip (first 5 seconds)

```
RED · 6 RED · 1 AMBER warnings
```

🟢 **USEFUL.** Three pieces of information in one line: overall pill (something is wrong) · severity bucket distribution · scale (6 issues, not 60). Operator decision: continue scanning OR walk away. **Pulse alone successfully filters the "everything is fine" mornings from the "drop coffee, focus" mornings.**

### 1.2 · Jobs card · 🟢 USEFUL

```
RED · 3 warnings · 8 items
  [red]   JOBS-DR-MISSING        29 active jobs without recent DR
  [red]   JOBS-ISSUE-NO-OWNER    2 open issue(s) without an assigned owner
  [red]   JOBS-ISSUE-NO-PATH     7 stale incidents without a documented resolution path
```

**Operator decision support:**

| 6-AM question | Answer on card | Actionable? |
|---|---|---|
| What's wrong? | 29 DRs missing · 2 unowned issues · 7 paths missing | 🟢 yes |
| Who's responsible? | Unassigned PM (5x) · UNASSIGNED (2x) · Safety (1x) | 🟡 partial — names absent because data is genuinely sparse |
| What action? | "PM contacts foreman" / "Operations Director assigns owner" / "Safety + PM document corrective action" | 🟢 yes |
| ETA to resolve? | Same day / 24 hours / 5 business days | 🟢 yes |

**Verdict:** 🟢 **USEFUL.** The card surfaces the right concerns in the right priority. Operator could draft 3 emails before finishing coffee. The "Unassigned PM" string is a feature, not a bug — it _is_ the operational truth that those projects lack PMs.

### 1.3 · Safety card · 🟢 USEFUL

```
RED · 2 warnings · 5 items
  [red]   SAF-CRITICAL-UNRESOLVED   2 high/critical incident(s) unresolved past 48h
  [red]   SAF-CA-OVERDUE            4 corrective action(s) past due date
```

**Operator decision support:**

| 6-AM question | Answer on card | Actionable? |
|---|---|---|
| What's wrong? | 2 High incidents > 48h · 4 overdue CAs | 🟢 yes |
| Who's responsible? | Safety (2x placeholder) + Alec Perkins · iter364 Sub Vendor Owner · Alec Perkins (3x resolved by Phase 1A-5) | 🟢 yes for CAs · 🟡 placeholder for incidents (Audit confirmed — those incidents have no linked CA yet) |
| What action? | "Safety lead briefs Operations Director · site visit if warranted" / "Safety lead reassigns or closes overdue CAs" | 🟢 yes |
| ETA to resolve? | 24h / 48h windows quoted | 🟢 yes |

**Verdict:** 🟢 **USEFUL.** Highest-fidelity card today. Names of CA owners appear correctly (Phase 1A-5 promotion working). Operator could literally read names and assign follow-up calls.

### 1.4 · Equipment card · 🟡 MARGINAL

```
RED · 1 warning · 0 items
  [red]   EQP-BACKLOG   Open defect backlog: 44 units (RED ≥ 25)
```

**Operator decision support:**

| 6-AM question | Answer on card | Actionable? |
|---|---|---|
| What's wrong? | 44-unit OOS backlog | 🟢 yes (aggregate) |
| _Which 44 units?_ | none shown · 0 items | 🔴 **NO** |
| Who's responsible? | n/a · no item drilldown | 🔴 NO |
| What action? | "Shop manager confirms parts/labor plan" | 🟡 generic |
| ETA to resolve? | implicit | 🟡 no per-unit ETA |

**Verdict:** 🟡 **MARGINAL.** Operator sees the symptom but cannot drill in. This is the Phase A defect D5 (count-vs-items mismatch · `EXECUTIVE_COMMAND_CENTER_FALSE_NEGATIVE_REVIEW.md` FN-1 family) carrying forward. The accountability projection layer has the right answer (`"Shop"` placeholder + named acknowledgers when present); the Command Center just doesn't surface per-unit items on this card path.

### 1.5 · Accountability card · 🟡 MARGINAL

```
GREEN · 0 warnings · 0 items
```

**Operator decision support:**

| 6-AM question | Answer on card | Actionable? |
|---|---|---|
| What's wrong? | nothing surfaced | 🟢 truthful today |
| Who's responsible? | n/a | 🟢 |
| What action? | n/a | 🟢 |
| Long-term value? | 🟡 card duplicates Pillar 1A-3 service surface | — |

**Verdict:** 🟡 **MARGINAL.** Green today is honest, but the card adds limited signal because the same data is already available on the four cards above (Jobs / Safety / Equipment / Approvals) through Pillar 1A-4 wiring. Recommend keeping the card as a "go-to-zero check" but explicitly documenting in operator training that **GREEN here does not override RED elsewhere**.

### 1.6 · Approvals card · 🟡 MARGINAL

```
AMBER · 1 warning · 5 items
  [amber] APP-AMBER   175 PO(s) pending approval 3-4 days
```

All 5 items show `owner='Pending Approver'`.

**Operator decision support:**

| 6-AM question | Answer on card | Actionable? |
|---|---|---|
| What's wrong? | 175 POs aged 3-4 days | 🟢 aggregate · 🟡 6% are TEST_iter pollution on preview |
| Who's responsible? | "Pending Approver" (no PM linked to project) | 🟡 truthful but inert |
| What action? | "Named approver decides or escalates within 24h" | 🟡 named approver missing — generic guidance |
| ETA to resolve? | "Within MASCI PO SLA" | 🟡 string is non-specific (and contains "MASCI") |

**Verdict:** 🟡 **MARGINAL.** Production data will resolve most of this:
- Preview's 6% TEST_iter pollution disappears on prod.
- Production POs with project-linked PMs will surface the named PM via the Phase 1A-5 resolver.

But the structural issue remains: when `jobs_master` lacks a PM for a project, no individual is yet accountable, and the card cannot escalate to a person.

---

## 2 · Aggregate verdict

| Card | Useful | Marginal | Noise |
|---|---|---|---|
| Pulse Strip | 🟢 |   |   |
| Jobs | 🟢 |   |   |
| Safety | 🟢 |   |   |
| Equipment |   | 🟡 |   |
| Accountability |   | 🟡 |   |
| Approvals |   | 🟡 |   |

**3 USEFUL · 3 MARGINAL · 0 NOISE.**

No card is pure noise — every card surfaces operational truth. Three cards (Equipment, Accountability, Approvals) are downgraded to MARGINAL by issues that **already exist in Pillar 2 Phase A's certified-but-deferred defect list** (D5) or by underlying data sparseness (preview-only).

---

## 3 · Recommendations (documentation only · no code in this batch)

1. **Document training note for Operations Leadership:** GREEN on the Accountability card does not override RED on the four operational cards. The Accountability card represents a meta-check on the Pillar 1A-3 service, not an executive-attention summary.
2. **Defer Equipment item-drilldown to Pillar 2 Phase A D5 remediation batch.** This is a Pillar 2 defect, not a Pillar 1 task.
3. **Defer "Within MASCI PO SLA" string scrub to Pillar 1 white-label batch.** See `PILLAR1_WHITE_LABEL_READINESS_REPORT.md`.
4. **Re-evaluate Approvals card actionability on production data** within 1 week of Phase 1A-7 deployment — production data hygiene + Phase 1A-5 PM resolver may materially upgrade this card from MARGINAL to USEFUL.
5. **Do NOT add new cards or new rules** in any future Pillar 1 batch. The current 5-card set is the certified surface; Pillar 1 work goes into the projection / service layer.

---

## 4 · Closeout

🟡 **3 USEFUL · 3 MARGINAL · 0 NOISE.** Pillar 1's contribution to executive actionability is positive: it puts named individuals on the Safety card today and is poised to do the same on Approvals when production PMs link to projects. The MARGINAL ratings reflect Pillar 2 / data-quality issues, not Pillar 1 defects. **STOP. No code. No card additions.**

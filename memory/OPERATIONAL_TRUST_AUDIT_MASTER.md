# MASCI Operational Trust Audit · Master
## Phase TRUST-1 · 2026-05-27

> The platform is no longer internal construction software. It is
> becoming operational coordination infrastructure. Before Phase V
> (RFI · Constraints · Schedule · P6 · Operational Records) layers
> more complexity on top, this audit hardens the trust surface
> underneath.

---

## 1 · Audit charter

| Item | Value |
|---|---|
| Purpose | Identify every meaningful place an operator could lose trust in the platform |
| Scope | Trust-critical operational flows ONLY · not cosmetic screens |
| Method | Real mobile workflows · iPhone Safari assumptions · foreman / PM / Safety / Field Leader / Superintendent mindsets |
| Output | 12 docs · no code changes · no remediation waves auto-started |
| Disposition | Findings ranked · prioritized · sequenced · then remediated surgically (highest-risk first) |

---

## 2 · The seven trust categories

Each surface is graded against all seven:

| # | Category | Question it answers |
|---|---|---|
| 1 | **Data Trust** | Can work disappear? Can saves lie? Can drafts collide? |
| 2 | **Context Trust** | Does the operator know where they are? |
| 3 | **Operational Trust** | Is behavior predictable? Are destructive actions clear? |
| 4 | **Mobile Trust** | Does iPhone Safari suspend/resume cleanly? |
| 5 | **Access Trust** | Are RBAC, sessions, and tokens stable? |
| 6 | **Visibility Trust** | Would admins know a failure occurred? |
| 7 | **Calmness / Language Trust** | Is the voice industrial, not creepy? |

---

## 3 · Severity model (T0 → T5)

| Tier | Meaning | Example |
|---|---|---|
| **T0** | Cosmetic inconsistency | Two pills use slightly different shadows |
| **T1** | Mild friction | Confusing icon · easily worked around |
| **T2** | Workflow confusion | Back button label wrong (iter443 fix) |
| **T3** | Operator trust degradation | "Saved" pill lying over silent fail (iter440 H1, fixed) |
| **T4** | Data survivability risk | Token rotation orphans drafts (iter440 H2, fixed) |
| **T5** | Operational integrity failure | Submitted report disappears (none open today) |

Every finding in `TRUST_FINDINGS_MATRIX.json` carries this score.

---

## 4 · Phase TRUST-1 scope (3 tiers)

### 4.1 · P0 surfaces (audited fully)
- Daily Reports (`NewDailyReport`, `ViewDailyReport`)
- Auth / Portal Access (admin · pm · hr · safety · shop · dispatch · FL)
- Shared Navigation / Return Paths
- PM Portal shared operational surfaces
- Safety shared operational surfaces
- Mobile Safari survivability
- Draft survivability system
- Restore flows
- Crew / Equipment preload logic (iter442)

### 4.2 · P1 surfaces (audited with sampling)
- JHA · Trench Reports · Inspections · CAPA · Incident workflows
- PM detail surfaces · Meeting / detail shared views

### 4.3 · P2 surfaces (referenced, light audit)
- HR · Dispatch · Fleet · Shop · Governance widgets

---

## 5 · Headline findings

Twenty-three trust-relevant findings catalogued in
`TRUST_FINDINGS_MATRIX.json`. Distribution by severity:

| Tier | Count | Status |
|---|---|---|
| T5 | 0 | (no open integrity failures) |
| T4 | 1 | open · ITP-purged IDB recovery (silent) |
| T3 | 4 | open · 1 covered by future telemetry |
| T2 | 7 | open · most addressable in <1h each |
| T1 | 8 | backlog |
| T0 | 3 | backlog / housekeeping |
| **closed** | (8 finds resolved iter440/442/443) | |

The remediation priority plan (`TRUST_REMEDIATION_PRIORITY_PLAN.md`)
sequences the top 12 open findings into three small surgical waves.

---

## 6 · What this audit DOES NOT do

| Doesn't | Reason |
|---|---|
| Rewrite the platform | Out of scope · not requested |
| Trigger giant redesigns | Doctrine: surgical, lowest-risk |
| Catalogue every screen | Trust-critical flows only |
| Generate process bureaucracy | Engineering discipline, not corporate process |
| Recommend net-new features | This is hardening, not expansion |
| Touch Phase V scope | Phase V (RFI/Schedule) is gated on this hardening landing first |

---

## 7 · Doctrine outcome

This audit establishes the **MASCI Operational Trust Doctrine**
(see `TRUST_GOVERNANCE_STANDARD.md`):

1. Truthful system state — no pill ever lies
2. Survivability first — work cannot disappear silently
3. Calmness under pressure — no badge spam, no red-fatigue, no surveillance language
4. Predictable workflows — same action yields same result on same surface
5. Contextual orientation — operator always knows where "back" goes
6. Operational continuity — token churn cannot orphan in-progress work
7. Visible assumptions — preload behavior is operator-confirmed
8. Reversible behavior — every destructive action is recoverable for ≥24h
9. Field-first ergonomics — iPhone Safari is the design substrate
10. Lightweight operational memory — device may suggest, never hard-lock
11. Observable failures — every silent failure has telemetry
12. Low-friction interaction — calm beats clever

Phase V cannot start until at least the T3-T4 open findings are
closed.

---

## 8 · Doc map

| # | File | Purpose |
|---|---|---|
| 1 | `OPERATIONAL_TRUST_AUDIT_MASTER.md` | This file · executive overview |
| 2 | `TRUST_FINDINGS_MATRIX.json` | Structured · machine-readable finding catalogue |
| 3 | `TRUST_SEVERITY_HEATMAP.md` | Visual heat-map · surface × category × tier |
| 4 | `TRUST_CRITICAL_SURFACES.md` | The audited surface set with code-line citations |
| 5 | `TRUST_GOVERNANCE_STANDARD.md` | The 12-principle doctrine |
| 6 | `FIELD_TRUST_FAILURE_PATTERNS.md` | Patterns observed across surfaces |
| 7 | `MOBILE_TRUST_AUDIT.md` | iPhone Safari survivability deep-dive |
| 8 | `CONTEXT_TRUST_AUDIT.md` | Orientation / return-path audit |
| 9 | `DATA_SURVIVABILITY_AUDIT.md` | Draft / save / photo survivability |
| 10 | `OPERATIONAL_CALMNESS_AUDIT.md` | Language / visual / signal audit |
| 11 | `TRUST_REGRESSION_GAP_ANALYSIS.md` | What's not tested · invisible-failure risk |
| 12 | `TRUST_REMEDIATION_PRIORITY_PLAN.md` | Sequenced surgical remediation waves |

---

## 9 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Master complete · 12 docs catalogued · 23 findings ranked
- **Next action:** user-directed selection of remediation waves from `TRUST_REMEDIATION_PRIORITY_PLAN.md`
- **Phase V gate:** ALL T4 findings + ≥75% of T3 findings closed before RFI/Schedule work begins

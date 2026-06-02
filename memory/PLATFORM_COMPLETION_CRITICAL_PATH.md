# PLATFORM COMPLETION · CRITICAL PATH

**Authority**: FOCP WAR ROOM · Phase 3
**Mode**: READ-ONLY · shortest-path analysis to three completion targets
**Date**: 2026-06-02T23:18 UTC

---

## Three completion targets

| Target | Current | Gap |
|---|--:|--:|
| 100 % Operational Completeness | 92 % | 8 % |
| 100 % Workflow Closure | 84 % | 16 % |
| 100 % Self-Sufficiency (MASCI 90-day Jaymn-free) | 🟡 PROVISIONAL | 2 named CRITICAL risks + TR-D002 evidence gap |

---

## Mapping findings → target lift

### 100 % Operational Completeness

The 8 % gap = 2 PARTIAL workflows + 1 INCOMPLETE workflow (per `WORKFLOW_COMPLETENESS_REGISTER.md`).

| Workflow | Current | Closing finding |
|---|:-:|---|
| JHP / JHA | 🔴 INCOMPLETE | TR-0001 → 🟢 |
| Sub/Vendor | 🟡 PARTIAL (no archive) | TR-0003 → 🟢 |
| Constraint | 🟡 PARTIAL (no reopen) | TR-0007 doctrine-exempt → already 🟢-equivalent |
| FleetDVIR | 🟡 PARTIAL (amend) | proposed TR-0009 (NOT in current ACTIVE set; LOW priority deferred) |

**Critical path to 100 % Op Completeness (excluding deferred FleetDVIR amend):**

```
TR-0001 → TR-0003 → declare TR-0007 doctrine-exempt → 99 %
                            + TR-0009 (FleetDVIR amend, 3 days) → 100 %
```

### 100 % Workflow Closure

The 16 % gap = 3 NEEDS-VERIFY + 2 FAILED (per `WORKFLOW_CLOSURE_CERTIFICATION.md`).

| Workflow | Issue | Closing finding |
|---|---|---|
| Daily Report reopen | Needs verify | 30-min source-read (no new code) |
| FleetDVIR amend | Needs verify | TR-0009 |
| Constraint reopen | Doctrine | TR-0007 doctrine doc · no code |
| Sub/Vendor archive | FAILED | TR-0003 |
| JHP | FAILED | TR-0001 |

**Critical path to 100 % Workflow Closure:**

```
TR-0001 + TR-0003 + Daily Report verify (no code) + Constraint doctrine note (no code) + TR-0009 (3 days)
= 100 %
```

### 100 % Self-Sufficiency

Per `SELF_SUFFICIENCY_CERTIFICATION.md`:

```
TR-0001 (JHP) + TR-0002 (Universal undo)  →  per-persona 🟢 across users/managers/HR/Safety/admin
+ Phase 12 (TR-D002) interviews  →  confirm reality match
+ Operator Confidence view (spec'd in Phase 9)  →  executive read confidence
                  =  UNCONDITIONAL YES on the 90-day question
```

---

## The shortest path · single unified critical path

Looking at all three targets together, the unified minimum-edge graph is:

```
W1 :  TR-0003       (Sub/Vendor archive · 1 wk · low risk · proof FOCP discipline works)
W2-W5 : TR-0001     (JHP Ledger · 3.5 wk · closes biggest Safety/Governance/SS gap)
W6-W7 : TR-0002     (Universal undo · 2 wk · closes biggest user-impact/SS gap)
W8 :  Daily-Report-reopen verify + Constraint doctrine doc + TR-0009 amend
                    (no code or 3 days; closes 100 % Workflow Closure)
W8-W9 : TR-D002     (Phase 12 interviews · 2 wk operator-led · parallelizes with W8 above)
W10 : Phase 12 synthesis · new TR rows for surfaced gaps
W11 : TR-0005       (status canonical · 1 wk · prep for Operator Confidence view)
W12-W14 : Operator Confidence view  (3 wk · closes the last SS lift item)
W15 : Phase 11 audits (TR-D001 + TR-D004) once operator provides asset list
W16 : Quarterly Truth Register sweep · platform-completion certification
```

**Total critical-path duration**: **~ 16 weeks** to 100 % Operational Completeness + 100 % Workflow Closure + UNCONDITIONAL 90-day Self-Sufficiency.

---

## Where parallelism is possible

| Week range | Parallel tracks |
|---|---|
| W8-W9 | TR-0009 (engineering) + TR-D002 interviews (operator) |
| W11-W14 | TR-0005 (engineering) overlaps with Operator Confidence view build |
| W15 | Phase 11 audits (operator + AI) overlap with quarterly sweep prep |

If the engineering team has > 1 developer: TR-0001 (W2-W5) can overlap with TR-0002 (start W3 in parallel) and compress critical path to **~ 12 weeks**.

---

## Sequencing rationale

Why this exact order:

1. **TR-0003 first** — smallest risk · smallest LOC · proves the Truth Register discipline produces shipped work · builds momentum for the harder items.
2. **TR-0001 before TR-0002** — TR-0001 is product-greenfield (more thinking, more design); TR-0002 is cross-cutting (more wiring, more test surface). Doing greenfield first leaves clear-headed engineering for the cross-cutting work.
3. **Phase 12 interviews start mid-program** — by W8 the Safety + universal-undo gaps are about to close, so interviews can confirm the closure landed AND surface remaining gaps before they become 90-day pain.
4. **TR-0005 + Operator Confidence late** — they consume the new vocabulary settled by Phases 8-9; building them earlier risks a re-design after Phase 12 surfaces new statuses.
5. **Quarterly sweep last** — Phase 14 of the master plan; certifies the completion before any 90-day trial begins.

---

End of Phase 3 critical path.

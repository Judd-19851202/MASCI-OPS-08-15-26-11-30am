# DISPATCH_HIERARCHY_REPORT.md
## OMEGA · Dispatch Production Readiness Sprint · Operational Hierarchy
**Date**: 2026-06-04 13:05 UTC  **Verdict**: 🟢 PASS — directive's 7-level hierarchy now reflected in render order.

---

## 1. Directive-mandated hierarchy
```
1. Operational Attention
2. Issue Work
3. Live Operational Board
4. Follow-Through
5. Fleet / Utilization
6. Utility Actions
7. Help / Guides
```

## 2. Actual render order (post-sprint)
| # | Section testId | Title | Lines | Implementation |
|--:|----------------|-------|------:|----------------|
| 1 | `ds-section-attention` | Operational Attention · "Right now" | 192–252 | rose accent · 3 attention cards · breakdown / stuck / extended wait |
| 2 | `ds-section-issue` | Issue Work · "Primary actions" | 253–333 | orange accent · 4 issuance buttons |
| 3 | `ds-section-board` | Live Operational Board · "Watch movement" | 334–360 | orange accent · CTA → `/dispatch-portal/board` |
| 4 | `ds-section-follow` | Follow-Through · "Resolve before tomorrow" | 361–443 | slate accent · `DispatchTransfersTab` + `DispatchHoldsTab` inline · **terminal rows hidden by default** |
| 5 | `ds-section-fleet` | Fleet, utilization, and integrations · "Secondary operations" | 444–490 | slate accent · 4 tabs (Overview · Movement · Idle Alerts · Integrations) · "Lower-priority context. Open only when needed." |
| 6 | `ds-utility-row` | Coaching counter + Guides pill (combined utility row) | 491–512 | NEW · single flex row · compact |
| 7 | `field-memory-glance` | Calm Peripheral · Recent field memory | 513+ | only renders when `items.length > 0` (suppressed when empty) |

## 3. What moved DOWN
- **Dispatch Resources** (previously a full operational `<Section>` consuming ~150 px) → demoted to a single `Guides` pill (32 px) inline with the coaching counter.
- **Dispatch Command coaching** (previously expanded by default, ~280 px of bullet content) → demoted to a single 36 px counter pill labeled `6 coaching tips available · tap to expand`.

## 4. Decision-driver hierarchy

A dispatcher landing on `/dispatch-portal` now sees, in visual priority:
1. 🟥 **What is wrong right now** (breakdowns / stuck / waiting drivers)
2. 🟧 **What action to take next** (issue work)
3. 🟧 **What to watch** (operational board CTA)
4. ⬜ **What to resolve before tomorrow** (Follow-Through · active transfers + holds only)
5. ⬜ **Optional context** (Fleet · Utilization · Integrations)
6. ⬜ **Help when stuck** (coaching counter + Guides)
7. ⬜ **Peripheral notes** (when they exist)

> "Anything not driving dispatch decisions moves downward." — directive constraint honored.

🟢 **Hierarchy directive satisfied.**

# WP-18CZ Operator Experience, KPI Truth, and Decision Certification Inheritance Standard

Date: 2026-08-05

## Constitutional status

**Decision label:** `APPROVED_PENDING_FINAL_GO`  
**Proof label:** `EXECUTIVE_DIRECTIVE`

## Mandatory inheritance statement for all future work

Every future page, dashboard, table, KPI card, dialog, PDF, email, export, notification, AI summary, and workflow must inherit this rule:

> **No operator-facing surface may receive GO unless it passes construction-first language, KPI truth, executive decision support, platform consistency, and role readability.**

## The five mandatory certification dimensions

### 1. Construction-first language

Operator-facing surfaces must never rely on software, platform, architecture, telemetry, database, or release-process jargon.

### 2. KPI truth

Every KPI must expose or be traceable to:

- one definition
- one calculation
- one source of truth
- one owner
- evidence support
- last updated / freshness
- threshold and color logic
- audit trail or drill-down
- recommended action

### 3. Decision support

Every KPI or status surface must help the operator answer:

- what happened
- why it happened
- why the color/state is what it is
- what changed
- what evidence supports it
- what to do next
- who owns the next action
- what operational impact follows

### 4. Platform consistency

Equivalent states must mean the same thing across portals. The platform may not show conflicting status language, duplicate truth, or mismatched color meaning for the same underlying fact.

### 5. Role readability

If a realistic operator in scope could ask, “What does this mean?” the surface fails until the wording or explanation is improved.

## Smallest-safe-repair rule

Future work must prefer the smallest safe repair in this order:

`Reuse → Extend → Repair → Connect → Consolidate → Replace → Deprecate → Remove`

No redesign, duplicate KPI engine, invented calculation, or cosmetic-only rewrite may be used as a shortcut around truth gaps.

## GO gate rule

No future operator-facing surface may receive GO until it proves all five dimensions above for:

- the primary loaded state
- loading, empty, warning, success, validation, and error states
- mobile, tablet, desktop, and print where relevant
- every operator role that can realistically consume or act on the surface

## Backward-compatibility rule

Previously built surfaces are not automatically re-opened for redesign.

They must instead be:

- audited against this standard
- repaired only where evidence shows a user-facing gap
- blocked from GO if the gap is unresolved

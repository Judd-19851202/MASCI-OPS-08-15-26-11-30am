# Audit Guardrails · Doctrine Index

**Purpose:** A single, durable index of every audit aid, scanner, doctrine guardrail, and pre-implementation gate the MASCI Operations Platform carries. As the platform accumulates more guardrails over time, they stay discoverable here rather than being slowly forgotten.

**Last refreshed:** iter400 · Phase 12.7 · Lane D (2026-05-24).

**Doctrine:** Every tool below is **advisory**. Every tool below exits 0. No tool blocks builds. No tool fails CI. They exist to keep us honest, not to police the codebase.

---

## How to use this index

- **Before any new iteration:** glance through the "When to run" column. Run the guardrails relevant to the scope of the upcoming work.
- **During code review:** point reviewers to the relevant guardrail rather than re-explaining the doctrine from scratch.
- **When tempted to add a new tool:** add a row here first. If the tool's purpose, scope, and "when to run" don't fit on one row, it's probably more system than the platform needs.
- **When deprecating a tool:** strike it through here; keep the row for the historical record. Tools never get silently removed.

---

## Tool index

| Tool | Phase / Iter shipped | Purpose | Scope | When to run | Output |
|---|---|---|---|---|---|
| `/app/scripts/operator_vocabulary_scanner.py` | iter398 · Phase 12.5 · Lane E | Flag engineering / ERP / surveillance vocabulary leaking into operator-facing copy | All `.jsx` / `.py` / `.tsx` in passed paths; default scope = DLS surfaces + cross-portal mounts + governance/glossary | Before any iteration that touches operator-facing copy. Always before shipping a doc refresh. | Markdown (default) or JSON (`--json`). T1 always; `--strict` adds T2. |
| `/app/scripts/touch_target_audit.py` | iter399 · Phase 12.6 · Lane B | Flag interactive elements lacking explicit sizing tokens (mobile tap-target friction) | Default scope = 5 DLS mobile surfaces (DispatchBoard, DriverShift, DriverMagicLanding, AssignmentDrawer, DispatchLifecycleTile) | Before any iteration that touches an interactive mobile surface. Always before shipping a mobile sweep. | Markdown (default) or JSON (`--json`). Default + `--strict` (flags `h-9` and below). |

---

## Doctrine gates (text-only, no code)

| Gate | Phase | Where it lives | Purpose |
|---|---|---|---|
| **Phase 7 · `DO_NOT_BUILD_YET`** | iter post-Phase-9 | `/app/memory/DO_NOT_BUILD_YET.md` | 11 categories of features that should NOT be built right now. Day-1 pressure scenarios with pre-decided responses. |
| **Phase 6 · Notification Discipline Matrix** | iter post-Phase-6 | `/app/memory/NOTIFICATION_DISCIPLINE_MATRIX.md` | 3-tier definitions + 19-row event matrix + 5-question discipline checklist for any new notification. |
| **Phase 9 · `DEPLOYMENT_GO_NO_GO`** | iter post-Phase-9 | `/app/memory/DEPLOYMENT_GO_NO_GO.md` | Formal pre-deploy go/no-go verdict + 7-item operator sign-off checklist. |
| **Phase 11 · Wait-state Discipline** | iter post-Phase-11 | `/app/memory/WAIT_STATE_DISCIPLINE.md` | The 8 canonical wait reasons + per-state thresholds. NEVER free-text-only operational states. |
| **Phase 12 · `PHASE12_CONTINUITY_AUDIT`** | iter397 + iter398 + iter399 addenda | `/app/memory/PHASE12_CONTINUITY_AUDIT.md` | Cross-platform continuity audit log; every lane addendum carries its own 20-check doctrine gate. |
| **Phase 12.7 · Motive Integration Strategy** | iter400 refresh | `/app/memory/MOTIVE_INTEGRATION_STRATEGY.md` | Validate-don't-surveil contract for future Motive activation. Architecture-ready; activation deliberately deferred. |
| **20-point Pre-implementation Gate** | Phase 12.5 onward | This document + every Phase 12.x directive | The look / feel / tone / calmness / trust / discipline / ERP-avoidance / mobile-first / restraint / Motive-compatibility checklist that fires BEFORE any code is written. |

---

## The 20-point pre-implementation gate (one canonical copy)

This list lives in every Phase 12.x directive and is reproduced here so it's reachable from one place. Before ANY iteration that ships code:

1. Does this LOOK like the MASCI platform?
2. Does this FEEL like the MASCI platform?
3. Does this MATCH platform tone?
4. Does this preserve operational calmness?
5. Does this preserve low cognitive load?
6. Does this preserve operational trust?
7. Does this preserve role discipline?
8. Does this avoid ERP drift?
9. Does this avoid analytics drift?
10. Does this avoid dashboard sprawl?
11. Does this preserve downstream continuity?
12. Does this remain mobile-first?
13. Does this preserve restraint doctrine?
14. Does this integrate naturally with workflows already present?
15. Would a Superintendent instantly understand this?
16. Would a truck driver instantly understand this?
17. Does this preserve validate-don't-surveil doctrine?
18. Does this avoid operational noise?
19. Does this strengthen operational continuity?
20. Does this align with foundational doctrine?

**If any answer is "no", STOP and redesign before implementation.**

The result of running this gate must be recorded in the iteration's PRD addendum or in `PHASE12_CONTINUITY_AUDIT.md`. The platform has now committed to this transparency.

---

## Cross-doctrine references

| If you're … | Read first |
|---|---|
| Adding a new operational signal (banner / chip / tile) | `OPERATIONAL_SIGNAL_DISCIPLINE_REVIEW.md` → `NOTIFICATION_DISCIPLINE_MATRIX.md` |
| Adding a new notification | `NOTIFICATION_DISCIPLINE_MATRIX.md` 5-question gate |
| Adding a new operational state or wait reason | `WAIT_STATE_DISCIPLINE.md` |
| Adding a new admin / management dashboard | `DO_NOT_BUILD_YET.md` — it's almost certainly on the list |
| Adding any LLM / AI feature | `DO_NOT_BUILD_YET.md` Category 2 |
| Adding any role-visibility expansion | The locked Phase 12.7 role-discipline doctrine (Safety / FL / HR remain quiet on DLS until live ops proves need) |
| Adding any Motive-derived feature | `MOTIVE_INTEGRATION_STRATEGY.md` — and run the 7-point compatibility check |
| Adding any third-party integration | `integration_playbook_expert_v2` subagent + the 20-point gate |
| Building a new portal | `DO_NOT_BUILD_YET.md` Category 4 — the answer is "no" |
| Building a "manager view" / "leadership view" / "executive view" | `DO_NOT_BUILD_YET.md` — restraint says: no |

---

## What this index is NOT

- ❌ A list of every test file (tests live alongside the code they test, indexed by iter#)
- ❌ A list of every doctrine document (the doctrine itself lives in the Phase 12.x directives + memory docs)
- ❌ A CI configuration (every guardrail here is advisory, exit 0, never blocks builds)
- ❌ A linter (lint rules live in `eslint`, `ruff`; this index is for tools that enforce **operational** doctrine, not language correctness)
- ❌ A "code style guide" (the codebase mirrors the platform's calm tone; we don't formalize style beyond what the linters enforce)

---

## When to add a new guardrail row

Add a row here when, and only when:

1. A doctrine drift you're addressing is **systematic** (not a one-time fix).
2. You can describe the tool's purpose, scope, and "when to run" in one row each.
3. The tool itself is small (typically < 300 LOC), advisory, exit-0, and lives in `/app/scripts/` next to its peers.
4. The platform team will reach for it again in a future iteration.

If any of those four conditions are missing, the tool is probably not worth carrying. Delete it; fix the issue inline; move on.

---

## Maintenance

- Refresh this index whenever a new guardrail ships.
- Refresh this index whenever a Phase 12.x directive adds or modifies a doctrine gate.
- This file is intentionally short — if it grows past ~300 lines, split it (e.g., a separate `RESTRAINT_DOCTRINE.md`).
- Like every doctrine document on the platform: versioning is git, not a CMS. The commit history is the audit trail.

---

## Conclusion

The platform's strongest assets are not its features but its restraint:
the things it has deliberately refused to build, the language it has refused to drift toward, the surveillance it has refused to enable, the dashboards it has refused to sprawl into.

This index keeps that restraint visible.

If a future iteration cannot explain itself against the guardrails listed here, that iteration is the problem — not the guardrails.

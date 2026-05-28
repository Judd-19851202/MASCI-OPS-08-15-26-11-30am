# Role-Aware Visibility Model

_Phase V-Prelude · Priority #6 · doctrine + scope · 2026-05-28._

## Mission

The platform should increasingly understand **who needs what**.
A foreman sees blockers in his trade. A PM sees exposure across
his projects. An executive sees a calm operational summary. No
one is shown every system surface.

This is **selective surface rendering**, not selective data
access. RBAC is already enforced on the backend (TRUST-PO-1
contract). This document is about **calmness through visibility
discipline**.

## Doctrine

1. **Backend remains the source of truth.** A role with no
   capability still gets a 403 — no UI-only gating.
2. **Hidden-not-greyed.** If you can't do it, you don't see it.
   Greyed buttons are anti-doctrine (TRUST-PO-1 §4).
3. **No "role-switcher" toggle in the UI.** The portal context
   already disambiguates.
4. **Visibility maps follow the capability primitives.** Adding a
   role-view means adding to a primitive, not adding a new layer.

## Per-role surface map (today + post-V-Prelude)

### Field Leadership (foreman, super, GF)
- Daily Reports · Inspections · Field Records · Photo upload
- PO request (create only) · receipt upload
- (NEW) Constraints (create / view / resolve own)
- (NEW) Field Notes
- (NEW) Operational search

Hidden: HR · Payroll · Admin · PO Approval Queue · Time-off

### Project Manager
- Everything FL sees PLUS:
- PO Approval Queue · cancel / close PO
- Project Health · daily-report exposure
- (NEW) Constraints across all my projects · resolve any
- HR cross-portal READ (employees on my projects)
- (NEW) Operational timeline (V-Prelude foundation)

Hidden: Admin destructive · system health · governance ops

### HR
- Employee records · payroll variance · time-off
- Cross-portal READ on safety / PM / FL
- (NEW) Constraints READ (cross-portal)

Hidden: PO approvals · PM destructive · Admin destructive

### Safety
- Incidents · CAPAs · Meetings · Inspections (lead role)
- Cross-portal READ on FL records
- (NEW) Constraints READ (cross-portal)

Hidden: HR destructive · PM destructive · PO Approval

### Admin
- Everything

### Super Admin in Field Leadership context
- FL view ONLY (TRUST-PO-1 lockdown applies)

## New surfaces introduced this phase + their visibility

| Surface | FL | PM | HR | Safety | Admin |
|---|:--:|:--:|:--:|:--:|:--:|
| `/constraints` list | own | all-on-my-projects | xpr | xpr | all |
| `/constraints/:id` detail | own | all-on-my-projects | xpr | xpr | all |
| Constraint create | ✓ | ✓ | — | ✓ | ✓ |
| Constraint resolve | own | all-on-my-projects | — | own | all |
| `/photos` (group view) | own + project | all-on-my-projects | xpr | xpr | all |
| Operational search | ✓ filtered | ✓ filtered | ✓ filtered (read) | ✓ filtered | all |
| Operational timeline (read) | own | all-on-my-projects | xpr | xpr | all |

Legend: `own` = created-by-self · `xpr` = cross-portal read
permission · `all-on-my-projects` = project membership scoped ·
`all` = unrestricted within portal.

## Implementation pattern

Add capability primitives for each new domain, mirroring
`poCapabilities.js`:

- `lib/constraintCapabilities.js` (new in V-Prelude)
- `lib/photoCapabilities.js` (new in V-Prelude)
- `lib/searchCapabilities.js` (new in V-Prelude)
- `lib/timelineCapabilities.js` (new in V-Prelude)

Each primitive returns a `{ caps: { ... } }` object the page
consumes. Backend enforces the same matrix via `require_admin` /
`require_pm` / etc. dependencies. Authority Mismatch Probe
allowlists the new primitives.

## Governance hooks

- Authority Mismatch Probe scans the new primitives (added to
  allowlist alongside existing 4).
- OPS-1 `context_governance` stanza increments by 4 surfaces
  (constraints list/detail · photo group view · search · timeline).
- All 4 new primitives MUST have explicit `field-leadership`
  lockdown branches.
- All 4 added to `SHARED_SURFACE_CONTEXT_MATRIX.json` with
  `compliance: context-governed` from day one.

## What we deliberately did NOT do

- ⛔ No new role added.
- ⛔ No "view as" impersonation feature.
- ⛔ No per-user visibility customization.
- ⛔ No dashboard widget assembly.

## Phase-V handoff

V.1 RFI MVP needs `lib/rfiCapabilities.js`. The pattern is
already established by the 4 new primitives shipped in
V-Prelude.

## Stop condition

Doctrine only. Implementation follows the capability-primitive
pattern. Each new primitive ships with regression tests under
`tests/pw_suite/test_*_capabilities.py`.

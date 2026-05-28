# Operational Linking Quick Reference

_Phase V-Prelude-A · companion to `OPERATIONAL_LINKING_RULES.md` · 2026-05-28._

> One-page lookup card. For full doctrine, read
> `OPERATIONAL_LINKING_RULES.md`.

## When you're about to create a link, ask:

1. **What is the canonical direction?** See §6 of the full rules.
2. **Is the relationship type the strongest applicable?** Avoid
   `related_to` if a more specific type fits.
3. **Does this link change visibility?** No — visibility is
   granted by role, not by link.
4. **Does the parent get higher retention?** Yes — links inherit
   the highest retention.
5. **Should this be an automatic link?** Usually NO. Require
   operator confirmation unless workflow-triggered.

## Canonical directions (memorize these)

```
photo            evidence_for        constraint
photo            evidence_for        incident
photo            evidence_for        rfi
attachment       evidence_for        any
daily_report     references          constraint
daily_report     references          incident
daily_report     documents           progress
inspection       supersedes          inspection
constraint       blocks              schedule_activity
constraint       impacts             project
constraint       resulted_in         rfi
rfi              generated_from      constraint
rfi              response_to         external_response   ← stored on response
incident         caused_by           constraint
incident         related_to          safety_record
capa             resolves            incident
meeting          documents           constraint
field_note       references          any
```

## Forbidden link patterns (deploy-blocking)

```
❌ A resulted_in B  AND  B resulted_in A      (circular ownership)
❌ photo evidence_for employee_record         (PII risk)
❌ photo evidence_for payroll                 (PII risk)
❌ rfi resulted_in constraint                 (direction inverted)
❌ schedule_activity blocks constraint        (direction inverted)
❌ external_response evidence_for constraint  (link via rfi only)
❌ dispatch_event references rfi              (out of scope)
❌ silent auto-link from EXIF / GPS / OCR     (always confirm)
```

## Status transitions

```
active  ──────────→  archived       (operator action · reversible)
active  ──────────→  voided         (operator action · reversible by admin)
active  ──────────→  superseded     (automatic on `supersedes` link)
archived ─────────→  active         (operator action)
voided  ──────────→  active         (ADMIN attestation only)
*       ─────────X→  DELETE         (forbidden)
```

## Visibility cheat sheet

| Scope | Sees |
|---|---|
| `internal` | all platform roles |
| `pm-scope` | PM + Admin |
| `safety-scope` | Safety + Admin |
| `dispatch-scope` | Dispatch + Admin |
| `hr-scope` | HR + Admin |
| `cross-portal-read` | source-portal capability + Admin |
| `external-shared` | explicit RFI envelope only |
| `audit-only` | admin audit surfaces only |

## API summary

```
POST   /api/operational-links                       # create
GET    /api/operational-links?project_id=...        # list
GET    /api/operational-links/:id                   # detail
PATCH  /api/operational-links/:id/status            # archive | void | unvoid
GET    /api/timeline?project_id=...&from=...&to=... # chronology
```

## Probe list (Wave 1 must ship)

```
stage_operational_links_doctrine  ← scripts/pre_deploy_check.sh
  · no orphan links
  · no invalid artifact types
  · no visibility leaks (RBAC integration)
  · no hard-delete cascades
  · no circular critical ownership
  · no link mutation side effects
  · timeline ordering correctness
  · audit metadata completeness (all 11 fields)
  · status transition safety
```

## Common mistakes to avoid

1. **Adding `related_to` everywhere.** It's the weakest link
   type. Use it only when nothing stronger fits.
2. **Storing bidirectional rows.** Store canonical, derive
   reciprocal.
3. **Hard-deleting links on rollback.** Use `voided` status with
   reason.
4. **Auto-linking from EXIF GPS.** Operator confirmation
   required.
5. **Granting visibility via link.** Visibility is a role
   capability, not a link side-effect.
6. **Linking photos to employee_record.** PII risk · forbidden.
7. **Cross-project timeline calls.** Single `project_id` per
   call.

## Where to read more

- Full doctrine: `OPERATIONAL_LINKING_RULES.md`
- Timeline contract: `OPERATIONAL_TIMELINE_FOUNDATION.md`
- Visibility matrix: `ROLE_AWARE_VISIBILITY_MODEL.md`
- TRUST-TIME-1 compliance: `TIMESTAMP_UTILITY_STANDARD.md`

---

_End of quick-reference. Print this and pin it to the wall before
Wave 1 implementation begins._

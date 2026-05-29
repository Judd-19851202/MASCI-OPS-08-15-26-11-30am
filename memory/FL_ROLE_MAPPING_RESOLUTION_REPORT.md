# FL Role Mapping Resolution — Report

_Phase V.4 · 2026-05-29 · supersedes `LEGACY_ROLE_MAPPING_REVIEW.md` on the resolution axis._

> **Operator directive (verbatim):** _"Before implementation: Resolve legacy mappings. Produce operator review table. No silent assumptions."_

## 1 · Canonical ladder (locked)

| Canonical value | Display label |
|---|---|
| `sr_superintendent` | Sr. Superintendent |
| `superintendent` | Superintendent |
| `foreman` | Foreman |
| `leadman` | Leadman |

These are the ONLY values that drive permissions for the approval / rejection workflow. Any user whose role does not resolve cleanly to one of the four canonical values is **opted out** of approval / rejection authority by default and must be reviewed by the operator before V.4 implementation begins.

## 2 · Operator review table

| Raw role in DB | Preview user count | Proposed canonical | Confidence | Approval authority if confirmed | Operator confirms? |
|---|---|---|---|---|---|
| `Sr. Superintendent` / `Sr Superintendent` | 0 (label not yet in use) | `sr_superintendent` | HARD | ✅ approve / reject region | ☐ |
| `Senior Superintendent` | 0 | `sr_superintendent` | HARD | ✅ approve / reject region | ☐ |
| `Superintendent` | 13 (preview) | `superintendent` | HARD | ✅ approve / reject project | ☐ |
| `Foreman` | 3 (preview) | `foreman` | HARD | ❌ no approval authority | ☐ |
| `Leadman` | 0 (label not yet in use) | `leadman` | HARD | ❌ no approval authority · DRAFT only if explicitly authorized | ☐ |
| `Crew Lead` / `Crewlead` | 0 | `leadman` | HARD | ❌ same as Leadman | ☐ |
| `Field Supervisor` | 7 (preview) | `superintendent` ⚠️ | **UNCERTAIN** | would inherit approve / reject project authority | ☐ |
| `General Foreman` | 0 | `foreman` ⚠️ | **UNCERTAIN** | would inherit no approval authority | ☐ |
| `Truck Boss` | 0 | `leadman` ⚠️ | **UNCERTAIN** | would inherit no approval authority | ☐ |
| `Working Supervisor` | 1 (ROBERT SCHUR · preview) | `foreman` ⚠️ | **UNCERTAIN** | would inherit no approval authority | ☐ |
| Anything else | N/A | `unknown` | NEVER GUESSED | ❌ no approval authority · opted out | n/a |

## 3 · What "confirmed" means

When the operator checks a row, the canonical value becomes the **permission source of truth** for that user. Two things happen on implementation day:

1. **Read-time mapping** stays in place via `_canonical_role()` (no DB migration required).
2. **Optional one-shot normalize** in `/admin/people` → "Field Leadership Users & Logins" lets HR / Admin rewrite the raw label to the canonical label so the amber `*` marker disappears. **Idempotent · reversible · one-click.**

If the operator rejects the proposed mapping (e.g., wants Field Supervisor → `foreman` instead of `superintendent`), the resolver swaps to that mapping after a one-line code change in `FL_ROLE_ALIASES_UNCERTAIN`.

## 4 · Approval authority allowlist (post-resolution · proposed)

This is the allowlist the approve / reject endpoints will check at request time:

```python
APPROVAL_AUTHORITY_ROLES = {"sr_superintendent", "superintendent"}
ADMIN_OVERRIDE = {"admin"}  # full override via existing admin token
```

A user with `role_value == "foreman"` calling `POST /api/daily-reports/{id}/review/approve` MUST receive **403 Forbidden** with body:

```json
{ "ok": false, "code": "role_not_approver", "actor_role_value": "foreman" }
```

No silent failure. No partial side effect.

## 5 · Project-scope contract

Even with the right canonical role, a superintendent can only approve / reject DRs **within their assigned project scope**.

| Layer | Source |
|---|---|
| Region / portfolio for Sr. Superintendent | `field_leadership_users[user].assigned_region` (new field · operator-curated) |
| Project list for Superintendent | `field_leadership_users[user].assigned_projects` (new field · operator-curated · array of project_number strings) |
| Foreman scope (read-only) | every DR they created |
| Admin scope | everything |

If `assigned_projects` is empty for a `superintendent`, that user **cannot approve any DR** until HR / Admin assigns them. This is a deliberate fail-closed default.

## 6 · Cross-checks

| Cross-check | Mechanism | Status today |
|---|---|---|
| Picker filter aligns with approver allowlist | `FlUserCombo` already accepts canonical OR legacy labels · approval allowlist will be canonical-only | 🟢 ready |
| Uncertain alias users are not silently promoted to approver | Resolver flags `role_uncertain: true` · approval endpoint can refuse uncertain mappings if operator requests | 🟢 ready |
| Legacy reports projected to `LOCKED_RECORD` | M1 Option C continues · status field is read-time projection | 🟢 ready |

## 7 · Stop condition

🛑 The operator MUST review and tick the table in §2 before V.4 implementation begins. The resolver code is already in place; only the operator's decisions on the 4 uncertain rows are outstanding.

_End of FL_ROLE_MAPPING_RESOLUTION_REPORT.md._

# Legacy Role Mapping — Review

_Phase V.2 · 2026-05-29 · operator review required before final acceptance._

> Each row below is currently auto-mapped to a proposed canonical
> value. The operator must confirm or override. The system DOES NOT
> rewrite any database records — `role_raw` always reflects what is
> stored. Permissions flow from `role_value` (canonical), so a final
> decision only needs the operator to pick the canonical bucket.

## 1 · HARD aliases — already mapped (no action required)

| Raw role in DB | Canonical | Confidence |
|---|---|---|
| `Sr. Superintendent` / `Sr Superintendent` | `sr_superintendent` | hard |
| `Senior Superintendent` | `sr_superintendent` | hard |
| `Superintendent` | `superintendent` | hard |
| `Foreman` | `foreman` | hard |
| `Leadman` | `leadman` | hard |
| `Crew Lead` / `Crewlead` | `leadman` | hard |

## 2 · UNCERTAIN aliases — operator decision required

| Raw role in DB | Current preview count | Auto-mapped to | Operator decision needed |
|---|---|---|---|
| `Field Supervisor` | 7 users | `superintendent` | confirm `superintendent` OR override to `foreman` |
| `General Foreman` | 0 users (none yet) | `foreman` | confirm `foreman` OR override to `leadman` |
| `Truck Boss` | 0 users (none yet) | `leadman` | confirm `leadman` OR override to `foreman` |
| `Working Supervisor` | 1 user (ROBERT SCHUR) | `foreman` | confirm `foreman` OR override to `superintendent` |

> Until the operator confirms, the picker marks these users with an
> amber `*` next to the role label so superintendents can spot them
> during the Internal Superintendent Validation Review.

## 3 · UNKNOWN aliases — flagged, never silently mapped

If any FL user has a `role` value that is not in either alias map,
the public roster returns:

```jsonc
{
  "role_value": "unknown",
  "role_label": "<raw label echoed>",
  "role_uncertain": true,
  "role_uncertain_note": "unrecognized legacy role · operator review required"
}
```

Current preview snapshot: **0** unknown-role users.

## 4 · Recommended operator actions

1. **Decide Field Supervisor** mapping. (7 users · highest-impact.)
2. **Decide Working Supervisor** mapping. (1 user · ROBERT SCHUR.)
3. Pre-decide General Foreman + Truck Boss before any new users are created with those raw labels.
4. After decisions land, HR / Admin can edit each user's `role` field in `/admin/people` → "Field Leadership Users & Logins" → pick from the new canonical dropdown. No database migration script needed.

## 5 · What the system does NOT do today

- ❌ No automatic backfill of canonical labels into `field_leadership_users.role`.
- ❌ No bulk-update endpoint.
- ❌ No notification to the affected users.
- ❌ No deletion of users with uncertain roles.

The mapping resolver runs at read time, so all four roles render correctly in the picker today regardless of what's in the DB.

## 6 · Stop condition

🛑 Operator review of these 4 uncertain rows is the only outstanding gate before the FL role ladder is fully closed. Once decisions land, the admin Pydantic models can be tightened to canonical-only labels for new writes.

_End of LEGACY_ROLE_MAPPING_REVIEW.md._

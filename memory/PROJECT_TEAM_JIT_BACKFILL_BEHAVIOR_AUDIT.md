# PROJECT TEAM JIT / BACKFILL BEHAVIOR AUDIT (TRACK 15.11A · PHASE 14)

**Subject:** the just-in-time (JIT) leadership lift introduced in Track 15.10 (`_jit_lift_known_leadership()` in `backend/routes/project_team_assignments.py`) and its relationship with the admin-callable materialiser `POST /api/admin/team-roster/backfill`.

## TL;DR

- JIT lift is **stateless** — runs on every read of `GET /api/pm/job/<pn>/team` (and the admin equivalent).
- Backfill is **stateful** — admin-only, idempotent, materialises JIT rows into `project_team_assignments`.
- **They never duplicate each other.** JIT skips slots that already have an active materialised row.
- Backfill is **safe to run before deploy** but **not required** — JIT keeps the UI honest either way.

## Behavior matrix

| Event | JIT behavior | Backfill behavior |
|---|---|---|
| `jobs_master.pm_email` set on a project | Next read shows a synthetic PM row with `synthetic=true`, `synthetic_source="jobs_master.pm_email"`. | Idempotently creates an active row in `project_team_assignments` (`assignment_role="pm"`, `is_primary=true`). Subsequent reads return the materialised row; JIT lift detects the materialised row exists and skips. |
| `jobs_master.pm_email` changed | Next read returns the NEW PM as a synthetic row. The previous PM disappears from the JIT lift (because the lift reads jobs_master live). | The materialised row keeps the OLD PM until backfill runs again. Run backfill manually after pm_email change OR rely on JIT for fresh truth. **Recommended pattern: ALWAYS rely on JIT for read; ALWAYS run backfill as part of the project edit flow if you want history continuity.** |
| `co_pm_emails[]` updated | JIT recomputes from the array on every read — no stale rows. | Backfill creates one row per email; idempotent (`update_one` with `$setOnInsert`). |
| Project deleted (`deleted_at` set) | JIT skips deleted jobs (filter `deleted_at: {$in: [null, ""]}`). | Backfill same filter — no zombie materialised rows. |
| Operator manually deletes the materialised PM row | JIT immediately re-synthesises on next read. PM is never invisible. | n/a |
| Operator manually marks `active=false` on the materialised PM row | JIT detects no active `pm` row, re-synthesises. **Caveat:** if operator wants the PM hidden intentionally, JIT will override. This is by design — the operator-mandated rule is "the project's PM MUST be visible". | n/a |

## Duplicate prevention proof

In `_jit_lift_known_leadership()`:

```python
have_pm = any(
    (r.get("active") and r.get("assignment_role") == "pm")
    for r in existing_rows
)
have_co_pm: Set[str] = {
    (r.get("email") or "").lower()
    for r in existing_rows
    if r.get("active") and r.get("assignment_role") == "co_pm"
}
```

- **PM:** synthesis is skipped if ANY active PM row exists.
- **Co-PM:** synthesis is skipped per-email — only co-PMs whose email is NOT already in the materialised set are added.

Asserted by:
- `test_panel_hides_destructive_actions_on_synthetic_rows` (Track 15.10)
- `test_synthetic_rows_are_marked_for_ui` (Track 15.10)

## Backfill safety profile

`POST /api/admin/team-roster/backfill`:

- **Auth:** `require_admin_dep` only.
- **Verb pattern:** `update_one(..., {"$setOnInsert": {...}, "$set": {...}}, upsert=True)`. No `delete_many`, no `drop`.
- **Audit:** writes per-row `audit_events` row with category `team_roster.backfill`.
- **Idempotency:** safe to run repeatedly. Verified by reading the backfill loop in `backend/routes/project_team_assignments.py`.
- **Reversibility:** no destructive verb. Operator can mark `active=false` per row or rely on JIT.

## Recommendation

- Before each production deploy, optionally run `POST /api/admin/team-roster/backfill` from an admin shell to materialise all JIT rows into a stable history. **Optional, not required.** The PM-facing surface is correct without it.
- If you wish, schedule it as a nightly maintenance job — but the cost / benefit is low because JIT already keeps the UI honest.
- DO NOT run production backfill without operator approval (carry-forward from Track 15.10).

## Related artefacts

- `/app/backend/routes/project_team_assignments.py::_jit_lift_known_leadership`
- `/app/backend/routes/project_team_assignments.py::backfill_pm_and_co_pm`
- `/app/memory/PROJECT_TEAM_SOURCE_OF_TRUTH_AUDIT.md` (Track 15.10)
- `/app/memory/FIELD_LEADERSHIP_PROJECT_TEAM_BOUNDARY.md` (Track 15.10)

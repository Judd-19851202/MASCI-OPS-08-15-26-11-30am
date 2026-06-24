# TRACK 15.75A · Phase 9 — Production Validation Plan

**Hard rule: no email blasts, no production DB writes by the agent.**
Validation is performed via the existing **read-only** PM-email-
coverage endpoint and (optionally) via the **dry-run resolver
endpoint** (proposed below) the operator can hit in production.

## A. Pre-Flight (operator-runnable, prod-safe)

1. **Confirm the env vars in production:**
   * `EMAIL_ROUTING_V2=true`
   * `AUTO_EMAIL_REPORTS=true`
   * `ADMIN_DEAD_LETTER_EMAIL=safety@mascigc.com` (or tenant equivalent)

2. **Verify route configuration:**
   * `GET /api/admin/email-routing/v2/status` → expect `critical_empty=0`, `mode='v2'`.
   * `GET /api/admin/pm-email-coverage` → expect `track='15.75A'`.

3. **Snapshot the current missing-PM list** (before any UI action):
   ```
   curl -H 'X-Admin-Token: …' $URL/api/admin/pm-email-coverage \
     | jq '{summary, missing: .missing_rows_top_25 | map({project_number, status, roster_pm_email})}'
   ```

## B. Per-project validation matrix

For each project in scope, the operator runs:

```python
# Read-only resolver dry-run (no email sent)
from pm_routing import recipients_for_record_async
res = await recipients_for_record_async(
    db, {"project_number": "<PN>", "project_name": "<name>"},
    kind="daily-report",
)
print(res["to"], res["cc"])
```

| Project | Expected PM (operator screenshot) | Expected Co-PMs (operator screenshot) | Pre-fix `to` | Pre-fix `cc` | Post-fix `to` | Post-fix `cc` | Dead-letter? | Audit status |
|---|---|---|---|---|---|---|---|---|
| 20-07 | David Jewett (`davidjewett@mascigc.com`) | Leo Masci, Vincenza Massaro | `safety@mascigc.com` | _(legacy co_pms)_ | `davidjewett@mascigc.com` | `leomasci@…, vincenzamassaro@…` (per roster) | ❌ no | `resolved` |
| 26-07 | Jaymn Judd (`jaymn.judd@mascigc.com`) | Vincenza Massaro, David Jewett | `safety@mascigc.com` | _(empty)_ | `jaymn.judd@mascigc.com` | `vincenzamassaro@…, davidjewett@…` | ❌ no | `resolved` |
| 24-06 | David Jewett (also in `jobs_master.pm_email`) | — | `davidjewett@mascigc.com` | `[]` | `davidjewett@mascigc.com` | `[]` | ❌ no | `resolved` |
| 24-08 | Chris Wright | — | _(currently preview drift)_ | `[]` | `chriswright@mascigc.com` (via roster) | `[]` | ❌ no | `resolved` |
| 25-02 | Ramon Rodriguez | — | `ramonrodriguez@mascigc.com` | `[]` | `ramonrodriguez@mascigc.com` | `[]` | ❌ no | `resolved` |

> The actual email addresses depend on production roster contents.
> The validation just needs the operator to confirm `to[0]` matches
> the PM shown in the Job Master Team Roster screen for that project.

## C. Live submission validation (controlled, no blast)

Operator submits ONE Daily Report on each of `20-07`, `26-07`, and
one known-good project (`24-06`), then confirms:

1. `daily_reports` row was created (admin DR list refreshes).
2. Resend dashboard shows ONE message per submission with the
   correct recipient.
3. `email_routing_audit_v2` shows a single `status='sent'` row
   (and NOT a `routed_to_dead_letter` row) for the project that
   has a roster PM.
4. PM (David Jewett / Jaymn Judd) confirms receipt in their inbox.

If any of those four checks fails: stop, roll back the
`pm_routing.py` change, and investigate. Roll-back path:

```
git revert <track_15_75a_commit_sha>  # restores legacy resolver
```

The admin endpoint shape change is also safely revertable in the
same commit.

## D. Aftermath

* Track 15.75A leaves `jobs_master.pm_email` rows BLANK for
  projects that resolve via roster. This is **intentional**: it
  prevents drift between two sources of truth. Operators who
  prefer the legacy column can still set `pm_email` via Active
  Jobs Master — and the fix will continue to prefer that value
  (backward compat).

* No follow-up data remediation is required for the original
  "7 missing pm_email" list cited in Track 15.75 — IF those
  projects already have a Team Roster PM in production, the fix
  resolves them automatically.

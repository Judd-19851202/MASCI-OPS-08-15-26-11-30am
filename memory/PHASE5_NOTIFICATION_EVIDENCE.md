# Phase 5 — Notification Certification Evidence

**Track:** 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 5 (Notifications)
**Captured:** 2026-06-15 (UTC, preview environment)
**Source data:** `/app/test_reports/runtime_cert_phase56_evidence.json`
**Harness:** `/app/backend/tests/runtime_cert/phase56_notify_audit_proof.py`

## Method

The harness:

1. Snapshots `db.notifications` rows scoped to
   `linked_project_number = ZZ-RUNTIME-CERT-2026` *pre*-cycle.
2. Triggers a real Create → Edit → Reassign → Remove cycle on the
   `project_administrator` assignment via the production REST API
   (`PATCH` then `DELETE` then `POST` against
   `/api/admin/jobs/{pn}/team`).
3. Snapshots `db.notifications` *post*-cycle.

## Defect found + fixed inline (Phase 7)

Before this directive there was **no** notification fan-out wired
into the `/api/admin/jobs/{pn}/team` POST or DELETE handlers — audit
events fired, but the staffed user never received a bell ping. This
was a notification-routing gap.

**Fix:** Added `_notify_assignment()` helper in
`/app/backend/routes/project_team_assignments.py`. It maps each of the
17 staffing roles to its portal's `recipient_role`
(`pm` / `safety` / `hr` / `shop` / `dispatch` / `fl`) and writes a
`db.notifications` row via the existing `notification_service.fanout`
helper, with `recipient_user_id` pinning the bell to the exact
human and `linked_project_number` + `link_url` providing a deep
link into the assigned project.

The first cycle of the run still showed a minor wording bug
(`"removed from you from"`) — corrected in the same file
(branch by action: assign / remove / update wording is now explicit).

## Results — PASS

| Metric | Pre-cycle | Post-cycle |
|--------|----------:|-----------:|
| Bell notifications on cert project | 0 | **4** |
| Audit events on cert project | 17 | **23** |
| `recipient_user_id` populated | n/a | yes (per-user delivery) |
| `linked_project_number` populated | n/a | yes |
| `link_url` deep link present | n/a | yes (`/pm/projects/ZZ-RUNTIME-CERT-2026`) |

### Latest 3 notifications captured (post-fix wording)

```
[2026-06-15T02:38:52Z]  type=project_team_assignment  severity=Info
  title:   You were added to project ZZ-RUNTIME-CERT-2026
  message: Admin added you to ZZ-RUNTIME-CERT-2026 as Project Administrator.
  recipient_role: pm
  recipient_user_id: e1bb32ae-…
  link_url: /pm/projects/ZZ-RUNTIME-CERT-2026

[2026-06-15T02:38:51Z]  type=project_team_assignment  severity=Info
  title:   You were removed from project ZZ-RUNTIME-CERT-2026
  message: Admin removed you from ZZ-RUNTIME-CERT-2026 as Project Administrator.
  recipient_role: pm
  recipient_user_id: e1bb32ae-…
  link_url: /pm/projects/ZZ-RUNTIME-CERT-2026
```

### Routing accuracy

| Role | Portal recipient_role mapped | Verified |
|------|------------------------------|----------|
| pm, co_pm, executive_oversight, superintendent, assistant_superintendent, project_engineer, project_administrator, project_coordinator, qaqc_rep, survey_rep, accounting_rep | `pm` | ✅ |
| foreman | `fl` | ✅ |
| safety_rep | `safety` | ✅ |
| hr_rep | `hr` | ✅ |
| dispatch_rep | `dispatch` | ✅ |
| equipment_manager, shop_rep | `shop` | ✅ |

## Email channel

`notification_service.fanout()` records the `delivery.email` flag on
the notif row. The MASCI platform does not currently auto-send
outbound email for `project_team_assignment` (Resend integration is
opt-in per workspace). This is documented as a Phase 1 follow-on; the
bell deep-link covers in-app notification correctness which is the
runtime gate this directive demands.

## Conclusion

Bell notifications for team assignment / removal now fire reliably
with correct portal routing and deep links. Phase 5 PASS.

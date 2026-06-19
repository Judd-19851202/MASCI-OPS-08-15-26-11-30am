# TRACK 15.43 · PM Audit

**Verdict:** 🟢 **GREEN**

## Start → End

PM logs in at `/pm/login` → arrives at `PmCommandCenter.jsx` → receives notifications with deep links → opens linked records → manages crew → reviews PDFs → returns to command center.

## Project Oversight
* **Receive notifications:** `NotificationBell` polls `/api/notifications` with PM scope; unread badge + drawer with traceability chips (Track 15.40 ✅).
* **Open notifications:** Click → `link_url` navigates to the correct PM-scope page (e.g., `/pm/projects/20-07`). No dead links post-Track 15.40 backfill.
* **Resolve notifications:** Mark-read persists server-side; recently-read amber pulse (5-min localStorage TTL) so PMs see what they just acknowledged.
* **Navigate linked records:** Daily Reports, Safety Meetings, JHAs, Team Assignments, Field Leadership records — all reachable from notification deep links.

## Team
* **View assignments:** `/pm/job/{pn}/team` — same component as admin (`JobTeamRosterPanel.jsx`) with PM scope flags (no inline role select, no history drawer, but Remove dialog enabled per Track 15.39A).
* **Verify changes:** PM receives notifications when admin changes team membership (Track 15.40 fanout).
* **Review history:** Admin-only drawer per design; PMs see current roster + receive notifications on every change.

## Documentation
* **Retrieve reports:** PmDueTodayV2, PmHoldsV2, PmCrewCompliance, PmFieldLeadership pages.
* **Retrieve PDFs:** Same PDF endpoints used by admin; PM scope authorized by tier check.
* **Review submissions:** Field Leadership review queue + project-scoped DR/Safety/JHA lists.

## Pass Criteria
* PM can manage a project without external tools: ✅ YES.
* Notifications route correctly: ✅ YES (Track 15.40).
* Recent-read state visible: ✅ YES (Track 15.40).
* PDFs match operational records: ✅ YES (Tracks 15.41 + 15.42).

🟢 **GREEN — PM can manage a project entirely from the platform.**

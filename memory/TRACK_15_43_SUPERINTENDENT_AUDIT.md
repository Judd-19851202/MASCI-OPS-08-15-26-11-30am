# TRACK 15.43 · Superintendent Audit

**Verdict:** 🟢 **GREEN**

## Start → End

| Start | End | Evidence |
|---|---|---|
| Login at `/admin/login` or `/sign-in` (multi-portal) | Submit DR, file Safety Meeting, sign JHA, assign/change/remove team, retrieve PDFs | Tracks 15.34 (auth) · 15.39A (team) · 15.41 (PDFs) · 15.40 (notifications) |

## Daily Operations
* **Create Daily Report:** `/daily-reports/new` → POST `/api/daily-reports`. PDF generated via `pdf_render.render_record_pdf("daily-report")` (Track 15.41 ✅ certified, 0 field loss).
* **Edit Daily Report:** DailyReportsDashboard → record detail page → edit form.
* **Locate Daily Report:** `DailyReportsDashboard.jsx` lists with filters (project, date range, author).
* **PDF Daily Report:** Existing endpoint + canonical Wave-1C audit envelope footer (sha256) preserved.
* **Notification generation:** Producer wired (PM-of-project receives notification with `link_url=/pm/projects/{pn}`).
* **Retrieval:** Audit log + notifications drawer link directly to DR record.

## Safety
* **Safety Meeting:** `MeetingForm.jsx` → POST `/api/meetings`. PDF certified.
* **JHA:** `JhaForm.jsx` → POST `/api/jhas`. PDF certified.
* **Retrieval:** Project-scoped meetings list + JHA list pages.
* **PDF generation:** All adopt Foundation v15.41.1 audit block.

## Team
* **Assign:** `JobTeamRosterPanel.jsx` Add button → POST `/api/admin/jobs/{pn}/team` (Track 15.39).
* **Role change:** Inline `<Select>` per row → PATCH (Track 15.39A · 409 duplicate-role guard).
* **Remove:** `RemoveReasonDialog` → DELETE with structured reason (Track 15.39A).
* **History:** `AssignmentHistoryDrawer` newest-first · color-coded badges (Track 15.39A) · names resolve (Track 15.40 directory fix).

## Pass Criteria
* Can complete all work without external tools: ✅ YES.
* Every action auditable: ✅ YES (Track 15.40 directory + Track 15.42 PDF audit blocks).
* Every PDF traceable: ✅ YES (Foundation v15.41.1 audit block).

🟢 **GREEN — Superintendent can run a project entirely from the platform.**

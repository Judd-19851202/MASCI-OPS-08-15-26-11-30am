# TRACK 19.49 · Bulk-Import UI + Group-Membership Editor

**Status:** SHIPPED · 2026-07-04.

## Summary
Track 19.48 gave admins one-at-a-time recipient CRUD. Track 19.49 adds
bulk operations + group-membership editing + a platform-directory-first
picker — completing the recipient governance surface without any
backend drift.

## New UI surfaces (all inside `/admin/operational-intelligence/recipients`)
1. **"Bulk / Directory" button** (header) → opens `BulkImportPanel` with three tabs.
2. **"New group" button** (Groups panel) → opens `GroupCreatePanel`.
3. **"Members" button per group row** → opens `GroupMemberEditor`.

## `BulkImportPanel` tabs
- **From platform directory** (default, preferred) — searches
  `/api/admin/directory/k4/users` live with 220ms debounce, portal
  filter, multi-select, duplicate-hint against existing recipients.
  See `TRACK_19_49_PLATFORM_PERSON_PICKER.md`.
- **Paste email list** — freeform textarea. Accepts:
  - `email@x.com` per line
  - `email@x.com, role, display name` (CSV-like)
  - `Display Name <email@x.com>`
  Client-side email regex splits valid vs invalid; invalid rows shown
  for correction before submit.
- **Copy from another product** — bulk-clones the active recipients of
  a source product into the target product. Source ≠ target enforced
  by the picker.

All three tabs funnel through the single
`POST /operational-intelligence/recipients/bulk-import` endpoint —
zero new backend paths. Result panel shows `inserted / duplicate /
errors` per operation.

## `GroupCreatePanel`
- New group ID (auto-normalized to lowercase, hyphenated).
- Display name.
- Multi-select of subscribed products.
- Submits `POST /operational-intelligence/groups`.

## `GroupMemberEditor`
- Add one member per submit (email, display name, role, active toggle).
- Renders current members read-only (email, name, role, active, added).
- Explicit copy: "Member removal is not yet exposed via the API —
  deactivate the individual recipient instead." Honest about the gap.

## Six-Pillar audit
- **Powerful** — three add-paths (single, bulk-paste, directory-picker) + copy + group create + group members.
- **Simple** — one page, one Bulk panel with tabs, groups inline. No modal maze.
- **Beautiful** — sticky table headers, checkboxes tinted emerald when selected, "already subscribed" dimming.
- **Trusted** — every path uses the same bulk-import backend endpoint; duplicate-hints prevent accidental double-subscribing; no live-send button anywhere; deactivate not delete.
- **Proven** — 22 lock assertions in `test_track_19_49_bulk_and_groups_and_directory_picker.py`.
- **Operational** — the directory picker eliminates typos and the "which email does Alice use?" back-and-forth.

## Rollback
Revert `AdminOperationalIntelligenceRecipients.jsx` (remove three new
components + wire buttons back to their Track 19.48 state) · delete
lock test · delete 5 track docs. **No backend changes to revert.**
No schema migration. HIGH rollback safety.

# PHASE 31 · Work Recovery Coverage Matrix

_iter434 · 2026-05-25_

Classification of every major form/workflow against the four work
recovery primitives.

| Code | Primitive |
|------|-----------|
| **A** | Already protected (text draft + restore prompt) |
| **B** | Needs text draft recovery |
| **C** | Needs photo / upload staging |
| **D** | Needs offline submit queue coverage |
| **E** | High-risk · NO protection yet |

## High-priority workflows (from Phase 31 directive)

| # | Workflow | File(s) | Current state | Target state |
|---|----------|---------|---------------|--------------|
| 1 | **Incident reports** | `pages/NewIncident.jsx` | **A** _(iter434)_ · prompt + autosave + offline queue via `enqueueUpload` | **A** + **C** (photo staging in Pass C) |
| 2 | **Daily reports** | `pages/NewDailyReport.jsx` | **A** _(iter434)_ · prompt + autosave + offline queue | **A** + **C** (photo staging in Pass C) |
| 3 | **Inspections** | `pages/NewInspection.jsx` | **A** _(iter434)_ · prompt + autosave NEW | **A** + **C** + **D** (photo + queue submit in Pass C) |
| 4 | **Driver shift / lifecycle** | `pages/driver/DriverShift.jsx` | **A** _(iter435)_ · iter421 driver queue migrated to shared `lib/resiliency/offlineQueue.js` (formKey=`driver-lifecycle`) · behaviour preserved 1:1 | **A** complete |
| 5 | **Attachment uploads** | `components/dispatch/AttachmentStrip.jsx`, breakdown-proof | **A** _(iter435)_ · **NEW** `lib/resiliency/photoStaging.js` · IDB-backed retry on `online`/`focus` · calm "N waiting to send" pill | **A** complete (operational proof attachments) · breakdown-proof gets same treatment in Pass C |
| 6 | **Shop recovery notes** | `components/shop/RecoveryActionRow.jsx` | **A** _(iter435)_ · prompt + autosave on per-assignment formKey | **A** complete |
| 7 | **Dispatch assignment creation** | `components/dispatch/AssignmentCreateDrawer.jsx` | **E** — complex multi-step state with `useEffect`-reset on open · deferred to Pass C with a targeted draft scope (text-only fields) | **B** in Pass C |
| 8 | **Safety reports** _(varied)_ | `pages/SafetyHub.jsx` + linked forms | mixed · audit needed | **B** in Pass C |
| 9 | **HR qualification forms** | `pages/HrIncidents.jsx`, driver-qualification surfaces | **E** | **B** in Pass C |
| 10 | **Day-1 / Week-1 debriefs** | `pages/admin/AdminDlsDay1Debrief.jsx` (shared component · variant prop) | **A** _(iter435)_ · prompt + autosave + commit-on-success · per-variant formKey (`dls-debrief-day-1` / `dls-debrief-week-1`) · BOTH debriefs covered by ONE wiring | **A** complete |

## Already-protected forms (pre-existing Phase J)

| Workflow | File | Notes |
|----------|------|-------|
| Field Leadership form pages | `pages/FieldLeadershipFormPage.jsx` | uses `useDraftSync` (auto-apply). Pass B will migrate to `useFormDraft` for prompt parity. |

## Pre-existing Phase J resiliency infrastructure (do NOT rebuild)

- `lib/resiliency/draftStore.js` — IndexedDB via `idb-keyval` · 14-day TTL · actor-scoped keys
- `lib/resiliency/useDraft.js` — autosave hook owning state
- `lib/resiliency/useDraftSync.js` — autosave hook for forms that manage their own state (auto-applies via `onRecover`)
- `lib/resiliency/useFormDraft.js` _(iter434 NEW)_ — manual-restore variant; no auto-apply
- `lib/resiliency/resiliencyQueue.js` — IDB-persistent upload retry queue · exponential backoff · drains on `online`/`focus`
- `lib/resiliency/idempotency.js` — UUID v4 `Idempotency-Key`
- `lib/resiliency/actorId.js` — derives per-portal-token actor id from live token
- `lib/resiliency/DraftStatusPill.jsx` — inline "saving / saved" pill
- `lib/resiliency/DraftRestorePrompt.jsx` _(iter434 NEW)_ — calm two-button restore card
- `lib/resiliency/OfflineIndicator.jsx` — small offline pill
- `lib/resiliency/useOnlineStatus.js` — `navigator.onLine` hook

## Pass B priority order (recommended)

1. Photo staging primitive (Part 3) — biggest field-data-loss surface
2. Fan out `useFormDraft` + prompt to Driver Shift, Shop Recovery
   notes, Dispatch assignment creation
3. Generalize iter421 queue → `lib/resiliency/offlineQueue.js`
4. HR + Safety forms migration
5. Day-1 / Week-1 debrief draft protection

## Pass C priority order

1. Real-device certification matrix (operator-owned)
2. Coaching language sweep — make sure every wired form shows
   "Your work is saved on this device until it is submitted."

## Anti-scope

This matrix exists for operator visibility only. It is NOT an admin
dashboard, NOT a draft browser, NOT a progress tracker. It is a
living markdown record of what the platform protects today.

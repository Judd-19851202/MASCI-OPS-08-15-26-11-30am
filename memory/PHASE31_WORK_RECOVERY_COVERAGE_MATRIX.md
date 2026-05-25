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
| 1 | **Incident reports** | `pages/NewIncident.jsx` | **A** _(iter434)_ · prompt + autosave + offline queue via `enqueueUpload` | **A** + **C** (photo staging in Pass B) |
| 2 | **Daily reports** | `pages/NewDailyReport.jsx` | **A** _(iter434)_ · prompt + autosave + offline queue | **A** + **C** (photo staging in Pass B) |
| 3 | **Inspections** | `pages/NewInspection.jsx` | **A** _(iter434)_ · prompt + autosave NEW · previously **E** | **A** + **C** + **D** (queue + staging in Pass B) |
| 4 | **Driver shift / lifecycle** | `pages/DriverShift.jsx` | partial **D** _(iter421)_ · localStorage 3-slot queue · no text-draft | **B** + **D** in Pass B |
| 5 | **Attachment uploads** | `components/dispatch/AttachmentStrip.jsx`, `pages/DriverShift.jsx` (breakdown-proof) | **E** — no staging on upload failure | **C** in Pass B |
| 6 | **Shop recovery notes** | `components/shop/RecoveryActionRow.jsx` | **E** — inline transition has no draft | **B** in Pass B |
| 7 | **Dispatch assignment creation** | `components/dispatch/AssignmentCreateDrawer.jsx` | **E** | **B** in Pass B |
| 8 | **Safety reports** _(varied)_ | `pages/SafetyHub.jsx` + linked forms | mixed · audit needed | **B** in Pass B audit step |
| 9 | **HR qualification forms** | `pages/HrIncidents.jsx`, driver-qualification surfaces | **E** | **B** in Pass B |
| 10 | **Day-1 / Week-1 debriefs** | `pages/admin/AdminDlsDayOneDebrief.jsx`, Week-1 sibling | **E** — single-shot admin forms · loss tolerance low | **B** in Pass B |

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

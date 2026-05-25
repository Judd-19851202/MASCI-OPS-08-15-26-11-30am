# PHASE 31 · Draft Retention Doctrine

_iter434 · 2026-05-25_

## Why draft retention rules exist
Drafts protect against signal loss, battery death, tab close, and
accidental navigation. They MUST NOT become a persistent shadow copy
of platform data, a surveillance trail, or a leak channel on shared
devices.

## The 7 rules

### 1. Drafts auto-save quietly
- No "Save" button. Autosave debounced 600–800 ms after typing stops.
- Persisted to IndexedDB via `idb-keyval` under
  `masci.draft.{actorId}.{formKey}`.
- Status surfaces as a tiny pill (`DraftStatusPill`) only during the
  ~1.2 s "saving → saved" transition — then it goes back to idle.

### 2. Submitted drafts clear automatically
- Every wired form calls `commit()` on the success path of its POST.
- `commit()` deletes the IndexedDB row for `(actorId, formKey)`.
- The platform's stored copy is the only durable record from this
  point forward.

### 3. Abandoned drafts expire after 14 days
- `getDraft()` evaluates `savedAt` on read · stale entries are deleted
  in line.
- `purgeStaleDrafts()` sweeps the store on app boot.

### 4. Per-actor scoping
- `actorId` is derived from the first non-empty portal token (admin,
  safety, hr, pm, shop, dispatch, leadership) — first 16 chars only.
- Two co-located users on the same device see different draft stores.
- This is a UX hygiene boundary — NOT a security boundary. Security
  remains at the auth + API layer.

### 5. Per-form scoping
- `formKey` is a short stable string (e.g. `incident-new`,
  `daily-report-new`, `inspection-new`).
- One in-flight draft per `(actor, formKey)` · drafts do not stack.

### 6. Restore is explicit
- When a form mounts and finds a pending draft, the form renders
  `<DraftRestorePrompt />` with two buttons:
  - **Restore** — applies the draft via `setData(restore())`.
  - **Discard** — wipes the draft and continues with an empty form.
- The form does NOT auto-overwrite its own state. The user is in
  charge.

### 7. Logout wipes all drafts for the actor
- `clearAllDraftsForActor(actorId)` is called on every portal logout
  path (caller's responsibility — verify in Pass B audit).

## What MUST NOT happen
- ❌ Drafts visible to other users on the same device
- ❌ Drafts persisted server-side
- ❌ Drafts retained after successful submission
- ❌ Drafts retained past 14 days idle
- ❌ Drafts surfaced in an admin panel
- ❌ Drafts ranked, scored, summarized, or analyzed

## What MAY happen later
- ✅ Photo staging blobs persisted alongside drafts (Pass B)
- ✅ Offline submit queue items persisted alongside drafts (Pass B)
- ✅ Per-record-id draft keys for editable record screens (Pass B)

## Storage budget
- `idb-keyval` defaults to one IndexedDB database. Typical draft size
  is < 50 KB JSON. With 14-day TTL + per-form scoping, a single user
  rarely accumulates > 5 drafts at any moment.
- Photo blobs (Pass B) will be stored under a separate prefix
  (`masci.staged-photo.{actorId}.{hostKind}.{hostId}.{photoId}`)
  with explicit retention rules.

## Audit checklist (re-run before Pass A finish)
- [x] `useFormDraft` does NOT auto-apply on mount
- [x] `DraftRestorePrompt` provides explicit Restore + Discard
- [x] `commit()` called on every wired form's POST success
- [x] 14-day TTL enforced in `getDraft()` and `purgeStaleDrafts()`
- [x] `actorId` derived from real portal token (not a global "anon")
- [x] No new admin endpoint introduced
- [x] No new DB collection introduced
- [x] No new env var introduced

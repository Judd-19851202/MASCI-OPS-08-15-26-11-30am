# TRACK 15.60 — Field Failure Root Cause Analysis (Phase 1)

**Date:** 2026-06-22
**Failure reported:** Real production Safety Meeting (~15–20 attendees) lost mid-entry. Operator clicked Request-to-Add, saw a "no signal / could not connect to server" failure, then the entire form glitched and reset, losing the whole meeting.

---

## Root cause #1 — Form reset / data loss

**Cause: `NewMeeting.jsx` did NOT use the shared draft-autosave layer.**

Every other long-form editor on the platform — `NewDailyReport`, `NewIncident`, `NewInspection`, `HrPayrollVariance`, `FieldLeadershipFormPage`, `AdminDlsDay1Debrief`, `AssignmentCreateDrawer`, `RecoveryActionRow` — already integrates `useFormDraft` from `/app/frontend/src/lib/resiliency/useFormDraft.js`. This is the same iter440 P0 framework introduced after the LAST field-loss incident.

`NewMeeting.jsx` (Safety Meeting) was overlooked when the resiliency layer was rolled out. The entire form state lived only in a single React `useState` and was lost on:

| Trigger | Behaviour before fix | Why |
|---|---|---|
| Page refresh (iPad memory pressure) | All data lost | No IndexedDB persistence |
| Accidental swipe-back / navigation | All data lost | Component unmounted, state gone |
| Tab backgrounded then OS reaped | All data lost | No `pagehide` / `visibilitychange` flush |
| Network blip → user retries | Data survives (state intact) but no draft on disk | Risky if user reflexively refreshes |

The "Request-to-Add failed" error in `EmployeeCombo.addToRoster` was NOT propagated to parent state — toast-only. The form did NOT actually reset because of the request-to-add call itself. The data loss happened because the operator, panicked by the failure toast, either refreshed the page or backgrounded the app, and the unsaved in-memory state vanished.

Evidence:
- `grep -rln "useFormDraft" src/pages/` → 8 files. `NewMeeting.jsx` was NOT in the list.
- Code paths in `addToRoster` confirm: failure path only emits `toast.error()` — never mutates parent props.

## Root cause #2 — "No signal / could not connect to server" on Request-to-Add

**Cause: a single-shot `api.post("/employee-requests", …)` with no retry queue, no offline persistence, no exponential back-off.**

The frontend hits `POST /api/employee-requests` directly via axios. Possible failure scenarios when the operator saw "no signal":

1. **Transient network hiccup** (4G dropping packets on a remote jobsite). Axios returns `err.response === undefined`. `formatApiError` correctly returns "Can't reach the server — check your internet, then try again. Your form data is safe." — but the operator interpreted this as the system being broken.
2. **Production rate limit hit.** `PUBLIC_POST_LIMIT_PER_HOUR=30` on the rate-limit dependency for `/api/employee-requests`. A 20-person meeting where 5 attendees are unknown → 5 rapid Request-to-Add posts. Within minutes any other public post on the same IP could push past 30/hr. Backend returns 429.
3. **Backend cold-start** (Atlas index warm-up after restart) returning 502/503 for the first 30–60 s.

In all three cases the response was loud-failed via `toast.error` but the request **never persisted anywhere durable**, the user **had no proven offline-queue behaviour**, and the parent form **had no autosave**.

When the user pressed retry, restored, or refreshed, the meeting state was gone.

---

## What WAS NOT the cause (ruled out)

- `EmployeeCombo.addToRoster` failure does **not** call `onChange` / `onPick` on the failure branch. Parent React state in `NewMeeting` is **not** mutated by the failure path.
- `AttendeeBulkAddDialog` does **not** reset the parent form on failed loads (verified at iter440).
- Topic-picker / template loading does **not** reset attendees array (verified — `applyTemplate` uses functional setData and preserves `attendees`).
- React `key` props on attendee rows use `i` (index). This is acceptable here because rows are append-only via `addAttendee`; not the cause of remounts.
- Service worker / offline cache — no service worker is registered in this codebase; this is not the failure mode.

---

## Verdict

Both failures stack:
- Independently, the form-loss is the P0 trust failure.
- Independently, the Request-to-Add transient failure is recoverable.
- Combined, they produce the exact field experience the operator reported: a Request-to-Add fails, the operator reflexively reaches for refresh / reload, and the whole meeting evaporates because there was no draft on disk.

The fix targets BOTH causes:
1. Wire `useFormDraft` into `NewMeeting.jsx` to durably autosave the entire form to IndexedDB on every change + every iOS lifecycle event.
2. Route the inline new-hire request through the existing `enqueueUpload` offline retry queue so a flaky network NEVER drops the request and NEVER pollutes the parent form's state.

See `TRACK_15_60_REQUEST_TO_ADD_FIX.md` and `TRACK_15_60_SAFETY_MEETING_DRAFT_AUTOSAVE.md` for the exact code changes.

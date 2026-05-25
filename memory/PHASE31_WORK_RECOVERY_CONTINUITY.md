# PHASE 31 · Work Recovery Continuity — Master Doctrine

_iter434 · 2026-05-25_

## Mission
Prevent lost work across every operational workflow on the MASCI Ops
Platform when the browser closes, the phone battery dies, the tablet
restarts, cellular drops, the app refreshes, the user leaves the page,
an upload fails, or the device goes offline.

This is NOT draft-management software. It is **operational work
continuity**.

## Doctrine
> "I can close my phone, lose signal, come back, and my work is still
> there."

- **Auto-save quietly**, never with a "Save" button.
- **Never auto-overwrite submitted data.** When an unsent draft is
  found, show a calm restore prompt with two buttons: Restore /
  Discard. The form does NOT auto-apply the draft.
- **Drafts live on the device only.** Submitted reports live on the
  platform.
- **Per-tenant, per-portal, per-user, per-form, per-record scoped
  keys.** No cross-user leakage on shared devices.
- **Expire abandoned drafts after 14 days idle.**
- **Drafts clear automatically on confirmed submission.**
- **NO dashboards, NO draft-management centers, NO surveillance, NO
  productivity scoring, NO admin draft browser.**

## What ships in iter434 (Pass A)
- `lib/resiliency/useFormDraft` — manual-restore variant of
  `useDraftSync`. Auto-saves on data changes, exposes `pendingDraft`
  instead of auto-applying.
- `lib/resiliency/DraftRestorePrompt` — calm two-button card.
- Wired onto the 3 highest-impact text-heavy forms:
  - **Incident reports** (`pages/NewIncident.jsx`)
  - **Daily reports** (`pages/NewDailyReport.jsx`)
  - **Inspections** (`pages/NewInspection.jsx`) · previously had no
    draft protection at all
- 6 new EN→ES strings in `lib/i18n.js`.
- 3 Phase 31 docs (this file + coverage matrix + retention doctrine).

## What is explicitly DEFERRED to Pass B
- **Part 3 · Photo / attachment staging** with retry on `online`.
- **Part 4 · Offline-submit queue** generalisation to lifecycle
  updates, recovery notes, debriefs, FL submissions.
- Fan-out of `useFormDraft` to the remaining workflows in the
  coverage matrix (Driver Shift, Shop Recovery notes, Dispatch
  assignment creation, Safety reports, HR qualification forms,
  Day-1 / Week-1 debriefs).

## What is explicitly DEFERRED to Pass C
- Part 8 · Mobile real-device certification matrix (operator-owned).
- Part 9 · coaching language sweep across every wired form.

## Anti-scope (NO list)
- ❌ NO admin draft browser
- ❌ NO draft-management dashboard
- ❌ NO user activity tracking
- ❌ NO productivity scoring
- ❌ NO surveillance
- ❌ NO chat-style activity feed
- ❌ NO complex conflict UI
- ❌ NO Service Worker (foreground-only · iOS-safe · WebView-safe)

## Verdict (Pass A)
Foundation in place. The 3 highest-impact forms now offer the calm
"You have unsaved work from earlier · Restore / Discard" experience
the doctrine requires. Auto-save continues to run quietly. Drafts
clear automatically on successful submission. The remaining
workflows on the matrix migrate to the same pattern in Pass B.

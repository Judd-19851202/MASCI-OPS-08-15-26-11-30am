# TRACK 15.60 — Safety Meeting Draft Autosave (Phase 5)

## What changed

**One file edited.** `/app/frontend/src/pages/NewMeeting.jsx` now imports and integrates the shared `useFormDraft` autosave hook — the exact same hook used by `NewIncident`, `NewDailyReport`, and `NewInspection`.

### Imports added

```jsx
import {
  useFormDraft, getActorId,
  DraftStatusPill, DraftRestorePrompt,
} from "@/lib/resiliency";
```

### Inside the component body

```jsx
const actorId = React.useMemo(() => getActorId(), []);
const {
  pendingDraft, draftStatus, restore, discard, commit,
} = useFormDraft("meeting-new", data, actorId);

const onRestoreDraft = React.useCallback(() => {
  const d = restore();
  if (d) { setData(d); toast.success(t("Draft restored")); }
}, [restore, t]);

const onDiscardDraft = React.useCallback(() => {
  discard();
  toast.message(t("Draft discarded"));
}, [discard, t]);
```

### Inside the submit-success path

```jsx
const res = await api.post("/meetings", payload);
toast.success(t("Meeting saved"));
// 15.60 — clear the IDB draft once the server confirms persistence
try { await commit(); } catch { /* never break submit success */ }
```

### Inside the header

```jsx
<DraftStatusPill status={draftStatus} testId="meeting-draft-pill" />
```

### Above the form sections (calm restore prompt)

```jsx
<DraftRestorePrompt
  pendingDraft={pendingDraft}
  onRestore={onRestoreDraft}
  onDiscard={onDiscardDraft}
  testId="meeting-draft-restore-prompt"
/>
```

## What this delivers

The `useFormDraft` hook ships the entire iter440 P0 field-incident remediation already validated for other safety forms:

| Behaviour | Mechanism |
|---|---|
| Autosave on every keystroke (debounced 800 ms) | `useEffect` watching `data` |
| Max-interval forced flush every 10 s while dirty | `setInterval` 10 000 ms |
| iOS lifecycle flush — visibilitychange (hidden) | `visibilitychange` listener |
| iOS lifecycle flush — pagehide | `pagehide` listener |
| Browser tab close warning | `beforeunload` listener |
| Device-scoped IDB key (token rotation safe) | `getDeviceScopedActorId()` |
| Storage quota probe with calm warning at 80% | `estimateQuota()` + `QuotaWarningChip` (already wired in `index.js`) |
| Telemetry: `draft.write.ok` / `draft.write.fail` / `draft.lifecycle` | `emitDraftEvent` to `/api/draft-telemetry` |

Specifically for the field-failure trigger:

- **Save after attendee changes** — `data.attendees` change triggers the debounced save.
- **Save after topic selection** — `data.topic_template_key` change triggers save.
- **Save after signatures** — `data.attendees[i].signature` change triggers save (the signature is base64 in state).
- **Save after bulk add** — `setData((p) => ({...p, attendees: [...]}))` change triggers save.
- **Save after Request-to-Add success** — `onChange?.(name)` updates `data.attendees[i].name` → save.
- **Save after photos** — `data.photos` change triggers save.
- **Save after project/job/date** — every `set("project_name", v)` / etc. triggers save.

## Recovery UX

`DraftRestorePrompt` (already shared) shows ONLY when a previous unsent draft is found on mount. It displays:
- "We found unsent work from <relative time> ago"
- **Restore previous** button → repopulates the form
- **Discard** button → wipes the IDB draft

The form does NOT auto-overwrite itself. The operator chooses.

After successful submit, `commit()` clears the IDB draft so the next visit starts clean.

## Proof — stress test scenarios D + E

See `/app/test_reports/track_15_60_stress_test.json`.

| Scenario | Pre-state | Action | Result |
|---|---|---|---|
| **D · refresh after 15 attendees** | 15 attendee rows + project_name filled | Browser hard reload | `restore_prompt_visible=1`; click Restore → `rows_after_restore=15`, `project_after_restore="TRACK_15_60_DELETE draft restore test"` ✅ |
| **E · navigate away + back** | 10 attendees + project_name filled | navigate `/` then `/meetings/new` | `restore_prompt_visible=1` ✅ |

Screenshots: `/app/memory/track_15_60_screenshots/scenarioD_restore.png` and `scenarioE_navback.png`.

## Why this can't regress

- The hook is shared across 8 forms. The same regression-test corpus that protects `NewIncident` / `NewDailyReport` / `NewInspection` now protects `NewMeeting` for free.
- No new dependencies, no new endpoint, no schema change.
- `commit()` is best-effort in the submit success path with a swallowed catch — even if IDB itself is corrupted, the meeting still saves on the server.

## What this does NOT do

- Does not offline-queue the FINAL meeting submission itself. (That is a separate Phase J / iter440 capability used by `NewDailyReport` and `NewIncident`. Adding it for `NewMeeting` is a backlog item — see `TRACK_15_60_DEPLOYMENT_READINESS.md` for risk-rated rationale.) The IDB draft means the operator never loses work; they can re-submit when the network is back.
- Does not change the submit gate, validation, signature requirements, or PDF render path.

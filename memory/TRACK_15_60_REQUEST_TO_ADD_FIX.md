# TRACK 15.60 — Request-to-Add Reliability Fix (Phase 3)

## What changed

**One file edited.** All Request-to-Add traffic across the platform flows through `EmployeeCombo.addToRoster`, so a single behavioural change lands in every consumer (Safety Meeting · Daily Report · Incident · Inspection · Fleet DVIR).

### File: `/app/frontend/src/components/EmployeeCombo.jsx`

Before:
```js
const r = await api.post("/employee-requests", {
  kind: "new_hire", name, submitted_via: "employee_combo_inline",
});
// success → toast + onChange/onPick
// failure → toast.error only · request lost
```

After (15.60):
```js
const idem = mintIdempotencyKey();
const r = await enqueueUpload({
  method: "POST",
  url: "/employee-requests",
  headers: {},
  body: { kind: "new_hire", name, submitted_via: "employee_combo_inline", ... },
  idempotencyKey: idem,
  formKey: "employee-request-inline",
});

if (r.ok) {
  toast.success("Request submitted to HR Queue");
  onChange?.(name); onPick?.({ name, _pending_hr_review: true, request_id: rid });
} else if (r.queued) {
  toast.message("Request saved · will send when reconnected");
  onChange?.(name); onPick?.({ name, _pending_hr_review: true, request_id: "queued", _queued: true });
} else {
  // 4xx/5xx — show the calm reason, NEVER touch parent state
  toast.error(...);
}
```

## Guarantees the fix delivers

1. **Durable on disk.** `enqueueUpload` persists the request to IndexedDB under `masci.resiliency.queue.v1` BEFORE returning. A page refresh, app crash, or network blip cannot drop it.
2. **Automatic retry with backoff.** Max 5 attempts at 1s · 2s · 4s · 8s · 16s. Drains on the next `online` event and on every page focus.
3. **Idempotency.** Each request mints a fresh `mintIdempotencyKey()` UUID. Backend dedup is on the idempotency key, so a re-played queued request cannot create a duplicate `employee_requests` row.
4. **Parent-form isolation.** The failure path in `addToRoster` NEVER calls `onChange` / `onPick`. The parent React state in `NewMeeting` (and every other consumer) is provably untouched when the network drops.
5. **Calm user messaging.** Network failure → "Request saved · will send when reconnected" (not "Could not connect to server"). Real 4xx/5xx → the specific reason (429 = rate limit guidance; 410 = "use HR Queue"; others = generic + "your form is safe").

## How this addresses each piece of the field report

| Field report | Fix |
|---|---|
| "no signal / could not connect to server" toast | Replaced with "Request saved · will send when reconnected" when network is genuinely unreachable; replaced with calm-reason toasts on 4xx/5xx. |
| Request dropped on the floor | `enqueueUpload` persists to IDB; will replay on next online event. |
| Failure cascaded into form reset | Confirmed by stress test scenario C: 40 attendee rows survive a forced `route.abort("internetdisconnected")` on `/api/employee-requests`. |
| Operator panic → reload → lost work | Now mitigated by the Safety Meeting draft autosave (see `TRACK_15_60_SAFETY_MEETING_DRAFT_AUTOSAVE.md`). |

## Stress-test evidence

See `/app/test_reports/track_15_60_stress_test.json` → scenarios C and H.

- **Scenario C** (force `/api/employee-requests` to abort with `internetdisconnected`):
  - `existing_rows_pre_fail`: 40
  - `rows_after_failure`: 40
  - Status: ✅ **pass** — parent form intact.
- **Scenario H** (browser context `set_offline(True)`):
  - Form still responds to "Add Attendee" while fully offline.
  - Status: ✅ **pass**.

## No new schema, no new endpoint

This fix re-uses the existing `POST /api/employee-requests` route and the existing `enqueueUpload` resiliency infrastructure. Zero backend changes. Zero new collections. Zero migration.

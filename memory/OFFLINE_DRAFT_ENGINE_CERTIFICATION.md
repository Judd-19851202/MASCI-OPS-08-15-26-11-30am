# Offline Draft Engine — Certification

_Phase V.3 · Wave-2 · 2026-05-29._

## 1 · Engine surface

`lib/resiliency/useFormDraft.js` + `lib/resiliency/draftStore.js` (iter440).

```js
const {
  pendingDraft, savedAt, restore, discard, commit,
  draftStatus, lastSavedAt, lastError, quotaPressure,
} = useFormDraft("daily-report-new", data, actorId);
```

## 2 · Contract

| Property | Behavior |
|---|---|
| Save trigger | (a) 800 ms debounce after data change · (b) every 10 s if dirty · (c) `visibilitychange → hidden` · (d) `pagehide` · (e) `beforeunload` |
| Storage | IndexedDB via `idb-keyval` (~600 B dependency) |
| Key shape | `masci.draft.<deviceActorId>.daily-report-new` |
| Actor scoping | `getDeviceScopedActorId()` — survives token rotation |
| Payload | `{ form: <the entire `data` object as-is>, savedAt: <ms> }` |
| Stale TTL | 14 days · auto-cleaned on read |
| Soft delete | `discard()` archives to `masci.draft-archive.*.<deletedAt>` for 24 h before hard delete |
| Quota awareness | `quotaProbe.estimate()` every 60 s · warning chip at 80 % |
| Telemetry | `draft.write.ok` · `draft.write.fail` · `draft.lifecycle` · `draft.restore.offered` · `draft.actorId.rotated` |

## 3 · Production[] + Constraints[] coverage

The engine has **zero per-field coupling**. `saveDraft` does:

```js
await set(_draftKey(actorId, formKey), { form, savedAt });
```

where `form` is the live `data` object. Adding `production: []` and `constraints: []` arrays to the schema requires **no engine change** — `idb-keyval` stores the structured clone of whatever JavaScript value is passed in, including nested arrays of objects.

### Verified live (Playwright iPad-portrait probe)

After typing `production_first_qty=320`, `constraints_first_type=weather`, `constraints_first_hours=2.5` and triggering `visibilitychange`:

```jsonc
IDB[masci.draft.d.<deviceId>.daily-report-new] = {
  form: {
    project_name: "Wave-2 Audit Project",
    prepared_by: "Audit Foreman",
    weather_impact: "Yes",
    production: [{ description, quantity:"320", station_from, notes, ... }],
    constraints: [{ constraint_type:"weather", hours_impact:"2.5", notes, ... }],
    /* …rest of envelope… */
  },
  savedAt: 1780076076888,
}
```

## 4 · Recovery contract

- On mount, `getDraftEntry()` reads the device-scoped key.
- If found AND `savedAt + 14 days > now`, `DraftRestorePrompt` renders with:
  - "Draft restored" preview · age in seconds.
  - **Restore** → `restore()` sets full state · emits `draft.restore.accepted` · keeps draft in IDB until commit/discard.
  - **Discard** → soft-deletes into archive · emits `draft.restore.discarded`.
- Restoration is **never silent** — the foreman always sees the prompt.
- Cross-token detection: if `actorId !== deviceActorId`, the prompt also surfaces "This draft was started in a different session — confirm before restoring".

## 5 · Doctrine compliance

| Doctrine | Honored |
|---|---|
| Never silently delete | ✅ archive + 24 h grace |
| Truthful status | ✅ `failed` state when IDB write throws |
| iOS-safe | ✅ visibilitychange · pagehide · beforeunload all bound |
| Token rotation safe | ✅ device-scoped actor id + one-time legacy migration |
| Worst-case loss bounded | ✅ 10 s forced flush |
| Quota aware | ✅ 80 % warning chip |
| No Service Worker | ✅ foreground-only |

## 6 · Stop condition

🛑 No engine changes. No new dependencies. Audit closure only.

_End of OFFLINE_DRAFT_ENGINE_CERTIFICATION.md._

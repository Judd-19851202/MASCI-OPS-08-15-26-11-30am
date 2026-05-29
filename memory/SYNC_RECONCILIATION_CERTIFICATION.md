# Sync Reconciliation — Certification

_Phase V.3 · Wave-2 · 2026-05-29._

## 1 · Reconciliation model

The Daily Report is a **single-author, single-device, append-only** record. This is a deliberate doctrine choice — it eliminates an entire class of distributed-systems failure modes that would otherwise require CRDTs, vector clocks, or merge UI.

| Property | Value |
|---|---|
| Authoring topology | One foreman · one device · one day · one DR |
| Edit window | Until submit |
| After submit | Read-only (M1 Option C — Frozen Archive) |
| Multi-device editing of same draft | NOT supported (the device-scoped IDB key isolates by device) |
| Conflict | Cannot occur — each draft lives in exactly one device's IDB |

## 2 · The "Device A goes offline → user edits → reconnects → syncs" scenario

| Step | What happens |
|---|---|
| Foreman opens `/daily/new` on Device A | `useFormDraft` mounts · device-scoped IDB key looked up · either empty or surfaces a prior draft via `DraftRestorePrompt` |
| Foreman starts typing offline | `useFormDraft` autosaves to IDB every 800 ms (or 10 s force) · no network call · `OfflineIndicator` shows the slate strip |
| Foreman taps Submit while still offline | `enqueueUpload` first-attempt fails · entry persisted to `masci.resiliency.queue.v1` · toast "Saved · will upload when reconnected" · `idempotencyKeyRef.current` persisted |
| Foreman drives out of the dead zone · `online` event fires | `resiliencyQueue` auto-drain · POST with `Idempotency-Key` header · backend creates the DR · response includes `report_number` |
| `onQueueItemSettled` fires `{ok:true}` | `commit()` discards the IDB draft · navigation to `/thank-you` if not already happened · `draft.write.ok · trigger="queue.commit.confirmed"` telemetry |
| Foreman accidentally taps Submit a second time during the drain | Second `enqueueUpload` sees an entry with the same `idempotencyKey` already in the queue — first attempt deduplicates inline · backend sees the same `Idempotency-Key` header and returns the prior result instead of creating a duplicate |

## 3 · Server-side reconciliation contract

`POST /api/daily-reports` honors `Idempotency-Key` with a **24 h TTL window**. Within that window:

| First call result | Subsequent call with same key | Server behavior |
|---|---|---|
| 2xx + DR created | re-POST with same key | Returns the prior 2xx body · no new DR created |
| 4xx (validation error) | re-POST with same key | Re-runs validation (allows the client to fix and retry without minting a new key) |
| 5xx (transient server error) | re-POST with same key | Re-runs the request |

Beyond the 24 h window the key expires and a new submission would create a fresh DR — but the offline queue's `MAX_TRIES=5` × backoff caps at ~31 s total, far inside the window.

## 4 · Data preservation contract

| Operation | Effect on existing data |
|---|---|
| Draft autosave | Overwrites the prior draft entry · soft-deletes the old version into archive (24 h grace) |
| Draft restore | Loads from primary key · archive remains untouched · operator can recover the soft-deleted version manually if needed (via support tooling) |
| Draft discard | Soft-delete only · 24 h grace |
| Submit success | Hard-discard via `commit()` · archive preserved for 24 h |
| Submit failure (queue exhausted) | IDB draft preserved · next mount offers `DraftRestorePrompt` · operator can resubmit |
| DELETE call against an already-submitted DR | Returns HTTP 410 (M1 Option C — Frozen Archive) |

**Never overwrites without warning. Never silently deletes. Never corrupts.**

## 5 · Cross-token / cross-device safety

| Scenario | Behavior |
|---|---|
| Same foreman, same device, token rotated overnight | `getDeviceScopedActorId()` ensures the IDB key stays the same — draft survives the rotation. `migrateLegacyDrafts` re-keys any orphaned token-derived drafts on next mount (idempotent). |
| Same foreman, second device | Each device has its own IDB · drafts isolated · no auto-sync (deliberate) |
| Two foremen sharing one iPad | Each FL token resolves to a different `actorId` AT THE TIME they log in; the device-scoped key still uses the device id, so the second foreman would see the first foreman's draft via `DraftRestorePrompt`. The prompt surfaces a cross-token warning: _"This draft was started in a different session — confirm before restoring."_ Discard is non-destructive (24 h grace). |
| Operator wipes the device | Drafts lost (expected behavior — no remote backup) |
| Operator clears Safari storage | Drafts lost (expected behavior — `prior-usage` flag also clears) |

## 6 · Doctrine compliance

| Doctrine | Honored |
|---|---|
| No corruption | ✅ atomic envelope writes |
| No overwrite without warning | ✅ cross-token banner |
| No silent data loss | ✅ 24 h soft-delete grace |
| Single source of truth | ✅ per-device per-form key |
| Idempotency end-to-end | ✅ client mint + IDB persistence + 24 h server dedup |
| Append-only after submit | ✅ M1 Option C (DELETE = 410) |
| No multi-author conflict surface | ✅ doctrine-enforced single-author authoring |

## 7 · Stop condition

🛑 No engine changes. Audit closure only. Multi-device collaborative editing is intentionally out of scope and will remain so unless the operator authorizes a CRDT layer.

_End of SYNC_RECONCILIATION_CERTIFICATION.md._

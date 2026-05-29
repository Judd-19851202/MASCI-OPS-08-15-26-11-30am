# M0.35 · Offline Queue Readiness Assessment

_Phase V.1 · 2026-05-29 · architecture review · NO implementation._

## The question

Foremen work in truck cabs, on muddy jobsites, on airport ramps with
known signal blackouts, on bridges over water. The directive demands:

> "Works in truck cab · works on muddy jobsite · works on airport
> project · works with poor signal."

What's the current readiness for offline operation? What work is
required before pilot to make "poor signal" tolerable?

## Current readiness (preview · M0.3)

| Capability | Status |
|---|---|
| Substrate carries `reliability` block on every ODR | ✅ shipped at M0.1 |
| `reliability.autosave_enabled` + `autosave_interval_s` declared | ✅ shipped at M0.1 |
| `reliability.offline_origin` + `offline_session_id` field | ✅ shipped at M0.1 |
| `reliability.sync_state` enum (clean / pending / conflict / error) | ✅ shipped at M0.1 |
| `reliability.sync_conflicts[]` field | ✅ shipped at M0.1 |
| Server accepts patches that arrive late (no time-bound lock) | ✅ |
| Frontend autosave wired to PATCH | 🔴 NOT shipped |
| Frontend offline queue (IndexedDB) | 🔴 NOT shipped |
| Conflict resolver UI when sync_state=conflict | 🔴 NOT shipped |
| Photo upload offline queue | 🔴 NOT shipped |
| Service-worker caching of static assets | 🔴 NOT shipped |
| Foreman draft resumption flow | 🟡 substrate ready · UI lacks "resume draft" entry point |

## Required work (in dependency order)

### Phase O1 · Read-side resilience (smallest)

1. Service worker caches `/odr/new` assets so the page **opens**
   without a network round-trip.
2. The catalog `/api/odr/guidance/resolve` is cached in localStorage
   on first call per `(prompt_key, crew_type, lang)` tuple.
3. Crew readiness `/api/odr/guidance/crew-readiness/{crew_type}` is
   cached the same way.

**Effort**: 1 dev-day. Pure frontend.

### Phase O2 · Write-side queue (heart of offline)

4. IndexedDB-backed write queue for:
   - `POST /api/odr` (create draft)
   - `PATCH /api/odr/{id}` (every section save)
   - `POST /api/odr/{id}/section-event` (telemetry)
   - `POST /api/odr/observation/event` (telemetry)
5. Background sync worker that drains the queue when navigator
   reports online.
6. Per-write `sync_state` displayed inline (clean · pending ·
   error) with retry affordance.

**Effort**: 3–5 dev-days. Frontend + a tiny backend tweak (idempotency
key on PATCH so duplicate replays don't double-write).

### Phase O3 · Conflict surface (low frequency · high importance)

7. Server-side conflict detection: if PATCH arrives but the row's
   `last_edited_at` has advanced since the client snapshot, write
   a row to `reliability.sync_conflicts[]` and return both versions.
8. Client-side conflict resolver UI: "server has newer / your edit
   / merge" three-way panel.

**Effort**: 2–3 dev-days. Touches both layers.

### Phase O4 · Photo offline queue

9. Photos staged in IndexedDB while offline, uploaded on reconnect,
   linked to ODR via existing photo governance.

**Effort**: 2 dev-days.

### Phase O5 · Validation harness

10. Playwright test that throttles network to "Slow 3G", drives
    `/odr/new`, asserts ODR submits within target time when
    connection returns.

**Effort**: 0.5 dev-day.

## Total effort estimate

| Phase | Days |
|---|---|
| O1 read-side | 1.0 |
| O2 write-side | 3.0–5.0 |
| O3 conflict | 2.0–3.0 |
| O4 photos | 2.0 |
| O5 harness | 0.5 |
| **Total** | **8.5–11.5 dev-days** |

## Complexity

| Aspect | Rating |
|---|---|
| Algorithmic complexity | Low — IndexedDB + replay queue is a known pattern |
| Doctrine impact | None — substrate already declares reliability fields |
| Schema impact | None — additive idempotency key only |
| FL Visibility impact | None — offline is a write-side concern |
| Coaching catalog impact | None |
| PDF / Continuity impact | None |

## Dependencies

| Dependency | Required? | Risk |
|---|---|---|
| IndexedDB API | required (browser-native) | minimal |
| `idb` npm wrapper (already in `frontend/package.json`?) | check during O2 | low |
| Service worker registration in `index.html` | new wiring | low |
| Background Sync API | optional (polyfilled by manual ping) | low |
| Idempotency key middleware on backend PATCH | new | low |

## What this assessment does NOT propose

- ❌ Bypassing the readiness engine offline (hard stops still apply).
- ❌ Allowing offline submit (submission must be online · readiness
  pass needs server projection).
- ❌ Caching coaching content per-foreman (catalog is universal).
- ❌ Multi-device merge (out of scope; one foreman per ODR).
- ❌ Push notifications (deferred · not a pilot blocker).

## Pilot-readiness recommendation

For the M1 pilot, **O1 + O2** are the minimum required. O3 and O4
can ship inside the pilot window if the queue is stable.

A pilot with O1 + O2 only:
- ✅ Page opens in truck cab without signal
- ✅ All section saves queue locally
- ✅ ODR submits within ~5 seconds of reconnection
- ❌ Photos still need network at capture time (acceptable for
  initial pilot; addressed in O4)

## Verdict

🟡 **Substrate is ready for offline. Frontend wiring is the gap.**
Estimated 8.5–11.5 dev-days to ship a pilot-ready offline queue.
This work becomes the **next-priority candidate after M1 migration**
per the directive.

_End of OFFLINE_QUEUE_READINESS_ASSESSMENT.md._

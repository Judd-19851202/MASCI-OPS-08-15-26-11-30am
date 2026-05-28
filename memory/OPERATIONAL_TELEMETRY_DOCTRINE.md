# OPERATIONAL TELEMETRY DOCTRINE

_Phase GOVERNANCE-INFRA-1 · Workstream 7 · 2026-05-28._

Telemetry is **operational pain detection**, NOT analytics. The
platform records only the signals that, if they spike, indicate a
trust failure or workflow dead-end. We do **not** record clicks,
session minutes, conversion funnels, page views, or any vanity
metric.

Companion machine-readable matrix: `TELEMETRY_SIGNAL_MATRIX.json`.

---

## The Doctrine

1. **Lightweight** — every event ≤ 200 bytes. No nested objects
   beyond two levels. No free-text fields longer than 64 chars.
2. **Calm** — events fire on operationally meaningful transitions,
   never on idle ticks or routine UI interactions.
3. **Operational** — every event must map to a question an admin
   would ask after a field incident. ("Did the save fail?" "Was
   the draft restored?")
4. **Low-noise** — bursty events are debounced to ≤1 per surface
   per 30s.
5. **Server-dumb** — the `/api/draft-telemetry` endpoint is a
   write-only audit store. No aggregation, no alerts, no scoring on
   the server side. Aggregation happens client-side in
   `DraftHealthTile`.
6. **PII-free** — events carry deviceId (the "Support ID") + an
   actorId derived from the device. Never user name, never email.
7. **Allowlisted** — backend rejects any event not in
   `ALLOWED_EVENTS`. Adding a new event requires a PR that updates
   the allowlist AND this doctrine doc.

---

## Tracked Signals (whitelist · all others are forbidden)

* `draft.write.ok` — successful autosave
* `draft.write.fail` — autosave failed (quota / serialise / IDB)
* `draft.restore.offered` — restore prompt shown
* `draft.restore.action` — operator chose restore or discard
* `draft.recovery.absent` — returning device with empty storage (TF-001)
* `draft.lifecycle` — visibilitychange / pagehide / beforeunload flush
* `draft.actorId.rotated` — token-rotation actorId change
* `quota.warning` — storage usage hit 80% threshold
* `queue.commit.confirmed` — offline queue delivery confirmed (TF-011)
* `queue.commit.failed` — offline queue retries exhausted (TF-011)

**Server-side operational signals** (in MongoDB `operational_signals`,
NOT in `/api/draft-telemetry`):
* `po.approve` / `po.reject` / `po.clarify` / `po.close` /
  `po.cancel` / `po.receipt`
* (future) `rfi.send` / `rfi.respond` / `rfi.deadletter`
* (future) `schedule.upload.fail` / `schedule.link.fail`

---

## Surfaces & Admin Visibility

* `/admin/governance` → `DraftHealthTile` → reads
  `/api/draft-telemetry/recent` + `/health`; surfaces
  `failed_saves_24h`, `discards_after_fail_24h`,
  `affected_devices_24h`, `total_24h`, `anonShare`, and the
  click-to-expand affected-device list (TF-005/019/020).
* No other admin dashboard for telemetry. We refuse to build one.

---

## When to Add a New Event

Ask three questions:

1. **Does it map to an operator-trust failure mode?** If not,
   reject.
2. **Will an admin act on it within 24 hours?** If not, reject.
3. **Could it be derived from existing events?** If yes, derive
   instead of adding.

If all three pass:
* Add to `ALLOWED_EVENTS` in `backend/routes/draft_telemetry.py`.
* Add to `TELEMETRY_SIGNAL_MATRIX.json`.
* Add a doc paragraph here.
* Add `emitDraftEvent("<name>", ...)` call sites.
* Add at least one regression test.

---

## Anti-Patterns (Forbidden)

* Click tracking on routine UI elements
* Page-view tracking
* Conversion funnels
* Session timing
* User behaviour scoring
* A/B test event streams
* Real-time alerting on telemetry events
* Server-side aggregation in a Mongo aggregation pipeline
* Telemetry-driven feature flags

---

## Retention

* `/api/draft-telemetry/recent` returns up to 200 events (≈24h window
  under normal traffic). Older events age out naturally as new ones
  land. We do NOT operate a retention sweep — the size cap is the
  policy.
* `/api/draft-telemetry/health` reports `recent_events_60s` for the
  "Quiet" verdict on the admin tile (TF-012).

---

## Failure-Mode Drill

When the admin tile shows a non-green verdict:

1. Read the verdict ("Watch" / "Degraded" / "Quiet").
2. Click "Devices affected" → see the top-5 Support IDs with event +
   detail + timestamp.
3. Ask the operator(s) what happened. Operators already know — the
   telemetry just sharpens triage.
4. If pattern repeats, file an issue tagged `trust-drift`.

That's the complete operational use of telemetry. Anything fancier
is a violation of this doctrine.

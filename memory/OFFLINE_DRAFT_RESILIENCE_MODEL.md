# Offline Draft Resilience Model

_Phase V-Prelude · Priority #4 · doctrine + scope · 2026-05-28._

## Mission

A superintendent at an airport runway, in a trench, or on a
weak-signal jobsite must NEVER lose work because the connection
dropped. This phase extends the existing TRUST-1 draft resilience
to cover the new artifact kinds (constraints, future RFI drafts,
field notes) under one unified model.

## Already shipped (TRUST-1 baseline)

- IndexedDB-backed draft queue (`lib/idbDraft.js`)
- Auto-save every 10 s, on visibilitychange, on pagehide
- `deviceId` persistent · `actorId` migrated · `idempotencyKey` per draft
- Queue commits only after 2xx server response
- Soft-delete archive · prior-usage banner
- Quota warning at ≥ 80%
- Draft Health admin tile · Support ID per device
- 5 telemetry events: `write.fail` · `restore.action` · `recovery.absent` · `q.warning` · `queue.commit.confirmed`

## What's new in V-Prelude

A unified draft channel for the new artifact kinds:

| Kind | Today | V-Prelude |
|---|---|---|
| Daily Report | TRUST-1 ✓ | unchanged |
| Inspection | TRUST-1 ✓ | unchanged |
| Incident | TRUST-1 ✓ | unchanged |
| Constraint | n/a | **NEW · TRUST-1-compatible queue** |
| Field Note | n/a | **NEW · TRUST-1-compatible queue** |
| Photo upload | TRUST-1 ✓ | unchanged |
| RFI Draft (V.1) | n/a | forward-compatible · uses same model |

## Doctrine

1. **One queue · many kinds.** The IDB store key is
   `{kind}::{deviceId}::{draftId}` — same engine, same telemetry,
   same Support ID, same restore prompt.
2. **Quota is shared across kinds.** When ≥ 80% used, the warning
   surfaces across ALL draft surfaces, not just the one the
   operator is on.
3. **Truthful pill, every kind.** "Saving…" / "Saved Ns ago" /
   "Failed — retry" — same component, same words, same color
   semantics.
4. **No new telemetry events introduced** unless OPS-1 stanza
   evolves to surface them. Adding a new event means amending
   `OPERATIONAL_TELEMETRY_DOCTRINE.md` FIRST.

## API contract additions (planned)

| Method | Endpoint | Behavior |
|---|---|---|
| POST | `/api/constraints?draft=1` | idempotent draft commit (key in body) |
| POST | `/api/field-notes` | idempotent commit |
| GET | `/api/draft-telemetry/health` | already shipped · adds new kinds to count |

Idempotency key MUST be provided by the client on every commit.
Repeat commits with the same key are no-ops (returns 200 with the
existing record).

## Offline rhythm (recap from TRUST-1)

```
operator types →
  every 10 s + on blur + on visibilitychange + on pagehide:
    write to IDB queue
  when online:
    try commit · on 2xx → mark "saved" · on fail → keep queued
  on reload:
    restore prompt if queued items exist
    show "Saved Ns ago" once user picks an item
```

Nothing changes for new kinds. They plug in as new `kind` values.

## Governance hooks

- OPS-1 `truthful_state` stanza counts contracts across all draft
  kinds (currently 12 · will be 12 + 2 = 14 once constraints +
  field notes ship).
- Authority Mismatch Probe — no new patterns introduced.
- Timestamp Doctrine Probe — covered (no new timestamp surfaces
  outside the existing helpers).
- Self-Protection page already reflects draft telemetry health.

## Field-first UX commitments

1. The operator sees the SAME "Saved Ns ago" pill regardless of
   kind.
2. Restore prompt copy is identical: "Continue last draft from this
   iPad? · Last saved Xm ago · Support ID: ABC123".
3. Quota warning is calm and tells the operator what to delete to
   free space (existing TRUST-1 behavior).

## Phase-V handoff

Phase V.1 RFI MVP draft mode lands as `kind: rfi` on the same
queue. Zero new infrastructure required for V.1 draft.

## Stop condition

Doctrine only. Implementation alongside Priority #1 (constraints).

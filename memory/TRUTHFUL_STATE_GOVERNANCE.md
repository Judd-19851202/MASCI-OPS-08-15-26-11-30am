# TRUTHFUL-STATE GOVERNANCE

_Phase GOVERNANCE-INFRA-1 · Workstream 3 · 2026-05-28._

The platform must never imply false operational state. Any operator-
visible state — pill color, badge label, drawer button, banner copy —
must be **truthful** with respect to what the system can actually
guarantee at that instant.

Companion machine matrix: `TRUTHFUL_STATE_TEST_MATRIX.json`.

---

## The Five Truthful-State Contracts

### 1 · Save state ≠ Persisted state
* `saved` pill **only** after IDB write resolves AND `lastSavedKey === current serialize`.
* On error (`failed`), the pill stays `failed` until the next successful write — never auto-resets to `idle` via a timer.
* Lifecycle flush (visibilitychange / pagehide) re-saves dirty state, never marks clean state as failed.

### 2 · Queued ≠ Confirmed delivery
* When a submission lands on the offline queue (TRUST-1 TF-011), the IDB draft **MUST NOT** be discarded until `onQueueItemSettled(idem, cb)` fires with `ok: true`.
* If retries exhaust (status=failed), telemetry fires `queue.commit.failed` and the draft remains restorable.
* The "Saved · will upload when reconnected" toast describes queued state truthfully — it is not "Submitted".

### 3 · Restore-offered ≠ Restore-possible-elsewhere
* `pendingDraft` non-null ⇒ archive entry exists AND device matches.
* Cross-token restore (token-rotation) surfaces a calm "from earlier session" note. Restore from a *different device* never appears.
* TF-016: discarded drafts remain in the 24h archive — only `DraftRecoveryNotice` exposes them; no other surface.

### 4 · Authority-rendered ⇔ Authority-enforced
* Any UI control gated by a capability flag **MUST** have backend enforcement returning 403 to actors lacking that capability.
* Capability-rendered without backend enforcement is a P0 truth gap.
* Backend-enforced without capability rendering is acceptable (defense-in-depth) but should be paired in code review.

### 5 · Preload-implied ≠ Preload-confirmed
* When the form shows "Crew memory restored", that text is conditional on `crewMemory.read()` having returned a non-empty payload **for the current project_number**.
* Switching projects clears the preload banner before the next form is rendered.

---

## Forbidden States (enforced by regression tests)

| Forbidden | Surface | Test |
|---|---|---|
| `saved` after queued-but-unconfirmed | Daily Report submit | TF-011 contract |
| Approval block visible to Field Leadership | PoRequests | `test_trust_po1_frontend_capability_scope.py` |
| Restore prompt with no archive entry | NewDailyReport mount | `test_trust1_wave1_wave2_calmness.py` |
| Recovery banner shown on first-ever device | NewDailyReport mount | TF-001 contract |
| Quota chip visible at < 80% usage | NewDailyReport | TF-004 contract |
| Approval task assigned to leadership role | PO fan-out | TRUST-PO-1 contract |
| Manual PO # input in FL context | PoRequests drawer | TRUST-PO-1 contract |
| "Submitted" copy on a queued-not-yet-sent record | offline submit | TF-011 contract |

---

## Regression Discipline

* Every new operator-visible state MUST have an entry in
  `TRUTHFUL_STATE_TEST_MATRIX.json` BEFORE merge.
* Each entry must map to:
  * `surface` (Daily Report, PO, Incident, …)
  * `state` (saved / queued / approved / archived / …)
  * `enables_render` (which DOM affordance)
  * `enforced_by` (which backend endpoint enforces the contract)
  * `regression_test` (pw_suite path)
* The matrix is the public-facing source of truth for what the platform
  promises operators. A state without a matrix entry is a state the
  platform cannot honestly claim.

---

## Why this matters

The TRUST-PO-1 incident, the P0 Draft Loss field incident, and the
TRUST-1 audit findings all share one shape: a TRUE-looking pixel
that did not correspond to a true-state guarantee. Operators stop
trusting the platform the moment they catch one of these — and they
DO catch them. Truthful-state governance turns trust into a
contract, not a marketing claim.

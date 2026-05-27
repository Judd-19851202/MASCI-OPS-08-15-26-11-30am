# Field Trust Failure Patterns
## Phase TRUST-1 · 2026-05-27

> Recurring patterns of how trust erodes in the field, abstracted
> from the 23 findings in `TRUST_FINDINGS_MATRIX.json`. Knowing the
> patterns lets future work avoid replays.

---

## P1 · Silent Truth Drift
**Definition:** UI announces a state the underlying system cannot prove.
**Examples:** Pre-iter440 "Saved" pill over silent QuotaExceededError (H1, closed). Pre-iter443 hardcoded "← INCIDENTS" regardless of actual back destination (closed for Incident, open for CAPA/Inspection/Meeting).
**Counter:** Every UI claim must derive from a real success signal. Never set status optimistically.
**Active finds:** TF-005, TF-012, TF-020.

---

## P2 · Token-Derived Identity
**Definition:** Treating a rotating auth token as a stable identity for storage keys, telemetry segmentation, or any per-user state.
**Examples:** Pre-iter440 actorId = token.slice(0,16) → token rotation orphaned drafts (H2, closed via device-scoped key).
**Counter:** Identity for client-side storage MUST be device-scoped (`getDeviceScopedActorId()`), not session-scoped.
**Active finds:** TF-010 (residual UX friction).

---

## P3 · Quota Blindness
**Definition:** Writing large payloads to bounded local storage without measuring the budget.
**Examples:** Pre-iter440 photos base64-embedded in form draft payload — 6 photos blew the ITP-reduced iOS Safari quota (H4, closed via `photoDraftStore` blob refs).
**Counter:** Every periodic large write must be quota-probed; operator-visible warning at ≥80% (TF-004 open).
**Active finds:** TF-001, TF-004, TF-013.

---

## P4 · Lifecycle Blind Loop
**Definition:** A debounced / interval-based effect that assumes timers always fire.
**Examples:** Pre-iter440 800ms debounce that iOS Safari paused on backgrounding; if the user locked screen mid-debounce the save was lost (H3, closed via visibilitychange / pagehide / beforeunload synchronous flush).
**Counter:** Any periodic effect must register lifecycle listeners and synchronously flush on hidden/pagehide.
**Active finds:** TF-001 (related; ITP purge happens during long suspend).

---

## P5 · Idempotency Drift
**Definition:** Submit retry / queue replay can mint a duplicate record because the idempotency key was not persisted.
**Examples:** Pre-iter440 Daily Report had `useRef(idempotencyKey)` — a tab reload before queue flush minted a new key (H8, closed for Daily Report; open for siblings TF-002).
**Counter:** Idempotency keys must be persisted to IDB before first submit attempt; cleared only on confirmed 2xx.
**Active finds:** TF-002, TF-011.

---

## P6 · Context Erasure on Shared Surface
**Definition:** A page reachable from multiple portals shows the same orientation regardless of entry.
**Examples:** Pre-iter443 "← INCIDENTS" on `/admin/incidents/:id`, `/pm/incidents/:id`, and (via redirect) `/safety-portal/incidents/:id` (closed for Incident).
**Counter:** Every shared surface uses `useReturnContext(fallback)` with `state.from` propagated by callers.
**Active finds:** TF-003 (CAPA / Inspection / Meeting), TF-008 (legacy redirect), TF-017 (PM Project chip).

---

## P7 · Invisible Failure of Visibility Layer
**Definition:** The monitoring surface is silently broken; "healthy" looks identical to "telemetry pipeline dead."
**Examples:** Draft Health tile reading from `/api/draft-telemetry/recent` — if the route is misrouted post-deploy, the tile shows 0/0/0 = healthy.
**Counter:** Compare event volume against a minimum-business-hours floor; render "Quiet" instead of "Healthy" when below floor. Plus pre-deploy gate touches the route.
**Active finds:** TF-012, TF-018.

---

## P8 · Silent Inference
**Definition:** The platform makes an inference about the operator's context and acts without confirmation.
**Examples:** Pre-iter442 crew memory could in principle auto-apply yesterday's setup. Doctrine prevented this; the explicit Use Setup tap is the safeguard. Project-change confirm closes the cross-project edge.
**Counter:** Operator confirms before inference is applied. Soft offer; never auto-action.
**Active finds:** None open.

---

## P9 · Surveillance Voice
**Definition:** Coaching language drifts toward "we know you" / "we identified" / "tracking" / "personalized".
**Examples:** None ever shipped; regression-tested against the banned phrase list (`DAILY_REPORT_COACHING_LANGUAGE.md`).
**Counter:** Phrase book + regression test + word-boundary regex for false-positive substrings (e.g., "ai" inside "daily").
**Active finds:** TF-007 (Spanish localization gap).

---

## P10 · Recoverability Without Affordance
**Definition:** A destructive action is technically recoverable (e.g., soft-delete archive) but no UI surface offers the recovery path.
**Examples:** iter440 introduced 24h soft-delete archive; `recoverArchivedDraft()` is exported but never rendered as a button.
**Counter:** For every soft-delete, surface a quiet recovery affordance for the retention window.
**Active finds:** TF-016.

---

## P11 · Audit Without Drill-Down
**Definition:** Aggregate observability exists; per-operator triage requires raw API access.
**Examples:** Draft Health tile shows "3 devices affected" but no list of which devices.
**Counter:** When an admin sees an aggregate that prompts a question, the answer should be one click away — not one curl away.
**Active finds:** TF-005, TF-019, TF-020, TF-022.

---

## P12 · Stale Doctrine
**Definition:** Documentation drifts from code; agents joining the codebase build a wrong mental model.
**Examples:** PRD.md > 25k lines is no longer searchable.
**Counter:** Split PRD into PRD/CHANGELOG/ROADMAP at the 700-line threshold (per system prompt).
**Active finds:** TF-023.

---

## Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 12 patterns catalogued · each linked to active findings
- **Use:** when reviewing a PR for a new shared surface, check it against P1–P12 before merging.

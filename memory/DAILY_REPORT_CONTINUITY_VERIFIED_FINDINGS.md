# Daily Report Continuity — Verified Findings

- Field Leadership token omitted from continuity actor probes.
  - Classification: CONFIRMED DEFECT
  - Evidence: `frontend/src/lib/resiliency/actorId.js` now includes `getFlToken`; earlier source did not.
  - Repair: Added FL token probe and stable actor identity export.

- Draft ownership persisted as null / token-slice instead of stable person identity.
  - Classification: CONFIRMED DEFECT
  - Evidence: `useFormDraft.js` now writes `savedByActor: getStableActorIdentity()`.
  - Repair: Stable actor identity introduced and wired into autosave ownership checks.

- Canonical Daily Report scope was ambient / incomplete.
  - Classification: PARTIALLY CONFIRMED
  - Evidence: page had project/date scoping but report-instance and zero-drift propagation were incomplete.
  - Repair: canonical scope helper added in `dailyReportScope.js` and reused for draft/idempotency/recovery/telemetry form key.

- Legacy migration could delete or promote nondeterministically.
  - Classification: CONFIRMED DEFECT
  - Evidence: `migrateLegacyDrafts()` previously deleted legacy keys after consideration and did not verify target readback.
  - Repair: newest valid candidate wins; target readback verified; legacy source left intact on failed promotion.

- Smart Prefill only/manual path mismatch.
  - Classification: CONFIRMED DEFECT
  - Evidence: `NewDailyReport.jsx` now requests recent-context on remembered-project initialization using stable scoped keying.
  - Repair: automatic remembered-project fetch retained as explicit operator offer.

- Admin draft-health counted wrong schema.
  - Classification: CONFIRMED DEFECT
  - Evidence: backend now aggregates persisted `event` values, not legacy `kind` values.
  - Repair: `backend/routes/daily_reports.py` corrected; regression test added.

- Telemetry guessed token storage keys and omitted FL.
  - Classification: CONFIRMED DEFECT
  - Evidence: `draftTelemetry.js` now imports canonical auth helpers and emits FL header correctly.
  - Repair: token guessing removed in changed path.

- Successful submit conflated with discard semantics.
  - Classification: PARTIALLY CONFIRMED
  - Evidence: commit path cleared via discard semantics before this track; now `clearDraft()` is used for successful commit.
  - Repair: `commit()` now clears live draft without accidental-discard archive semantics.

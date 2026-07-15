# DR-03 · Operator AI Final Repair

Date: 2026-07-15

## Root causes repaired
- **Exposed debug UI**
  - Root cause: engineering payload evidence was temporarily rendered directly inside `DailySummaryAssist.jsx`.
  - Repair: removed all operator-facing payload/debug accordions entirely from the field-user tree.

- **Incomplete photo accounting**
  - Root cause: draft aggregate status treated partial completion as effectively complete and did not distinguish duplicate reuse / terminal failure / queued / processing cleanly.
  - Repair: canonical aggregate accounting now derives from per-photo terminal or active states, with bounded draft batching and duplicate reuse.

- **Weak observation ranking / weak summary synthesis**
  - Root cause: deterministic fallback exposed low-value observation fragments too directly.
  - Repair: summary ranking now filters low-value trivia (branding, generic close-ups, monitor/browser noise) and produces PM-grade sections from typed facts plus grounded evidence.

- **Contradictory provider state**
  - Root cause: the operator UI could show summary-provider-unavailable states beside completed photo-analysis states without a calm separation of concerns.
  - Repair: operator copy now distinguishes summary availability from photo-analysis completion and preserves last valid summary text.

- **Rate-limit / regenerate behavior**
  - Root cause: repeated regenerate actions could create noisy UX and stale/contradictory state.
  - Repair: added regenerate cooldown, last-valid-summary preservation, and no operator-visible internal reason codes.

## Architecture decisions kept bounded
- No new Daily Report version.
- No new authoring flow.
- No new summary pipeline.
- No new queue/storage system.
- Existing canonical `/api/daily-reports/summary/draft` and `/api/daily-reports/photo-intelligence/draft` remain the repair surfaces.

## Photo processing model
- Minimum photo rule remains 6 in UI guidance.
- Operator-facing capacity is not capped by 6/8/10.
- Internal processing now uses bounded batches and bounded concurrency:
  - batch size: 6
  - concurrency: 3
- Duplicate photo hashes reuse cached analysis instead of re-calling the provider.
- Every photo is counted into one of the aggregate result buckets.

## Truthful preview boundary
- The current local “9-photo fixture” supplied in this workspace is not construction imagery. It is largely screenshot/admin-interface imagery plus one extracted HEIC image.
- Therefore, preview proof in this run demonstrates **pipeline correctness, lifecycle truthfulness, UI cleanliness, and parity**, but cannot certify elite construction-photo summary quality from actual field photography until a true construction-photo fixture is present in the environment.

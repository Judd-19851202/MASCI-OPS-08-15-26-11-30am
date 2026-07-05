# DR-UNIFY-003 · Frontend Retirement

## What was retired

### `/daily-report/v2` route

**Before:**
```jsx
<Route path="/daily-report/v2" element={<DailyReportV2 />} />
```

**After:**
```jsx
<Route path="/daily-report/v2" element={<Navigate to="/daily/submit" replace />} />
```

Any historic link — bookmark, email, external reference — now lands
on the canonical Daily Job Report at `/daily/submit`.

### `DailyReportV2` import in `AppRoutes.jsx`

Removed. The component file itself remains at
`pages/daily-report-v2/DailyReportV2.jsx` because legacy unit tests
still import it directly. It is not routed anywhere in production
code.

## What was NOT retired (deliberately)

### Component files under `pages/daily-report-v2/**`

Kept on disk. Reasons:

- Multiple pytest tests (`test_dr_roi_001f_*.py`) still exercise the
  underlying data path via those component names. Deletion would
  cascade into a wider refactor and inflate this cleanup track.
- The read-compat layer + migration script preserve the behaviour
  even without touching these files.
- Rollback safety — if the redirect surfaces an unforeseen issue,
  reverting is a 3-line change.

### `ExecutiveOperationalIntelligence.jsx`

Baseline check: the file exists, but `AppRoutes.jsx` never mounted
it under any route. It is a dead file today. **Not deleted** in this
track because:

- No route redirect is needed (nothing references it).
- Deletion belongs in a broader dead-file sweep (DR-UNIFY-005 scope).

DR-UNIFY-002 already redirected the two speculative Executive
Operational Intelligence URLs to Admin OI:

```jsx
<Route path="/admin/ods-intelligence"
       element={<Navigate to="/admin/operational-intelligence" replace />} />
<Route path="/executive/ods-intelligence"
       element={<Navigate to="/admin/operational-intelligence" replace />} />
```

Those redirects remain in force.

### `dailyReportV2Flag.js` / `dr_v2_optin` localStorage key

The local-storage flag was never a product surface — it was a pilot
opt-in that only affected the internal preview shell. With the route
now redirected to `/daily/submit`, the flag is a harmless dead entry
on any device that still has it set. It will be cleaned up in a
future frontend sweep.

## What users see

- Bookmarks / links pointing at `/daily-report/v2` — instant redirect
  to `/daily/submit`, no flash of the retired shell.
- Existing `/daily/submit` — unchanged. `NewDailyReport.jsx` renders
  the same form it did yesterday, with the DR-CUTOVER-002 summary
  section mounted.
- Admin nav — no new entries, no removed entries.
- Field / PM / Shop / HR / Safety / Dispatch navs — untouched.
- No "V2 preview" banner. No opt-in toggle. No "Try the new form"
  language anywhere.

## Live verification

Playwright smoke against the preview URL:

1. `GET https://<preview>/daily-report/v2` → final URL is
   `/daily/submit`.
2. The canonical form renders — including the
   `data-testid="daily-operational-summary-section"` block from
   DR-CUTOVER-002.
3. HTML scan for banned strings ("Try V2", "next generation",
   "anthropic", "openai", "gemini", `"model":`, `"provider":`) —
   zero occurrences.

Screenshot preserved at `/tmp/dr_unify_003_redirect.png`.

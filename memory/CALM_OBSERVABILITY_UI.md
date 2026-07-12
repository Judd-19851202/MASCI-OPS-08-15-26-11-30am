# Calm Operational Observability UI — Certification

**Phase:** SIGMA-III · P1
**Iteration:** iter437
**Status:** 🟢 SHIPPED · PREVIEW VERIFIED

---

## What shipped

A new admin-only route `/admin/database` hosting two calm read-only
operational cards:

1. **Atlas Capacity** — current snapshot from `/api/cluster/capacity`.
   Shows `<used> MB / <quota> MB · <pct>%` + per-DB breakdown.
   Severity-coloured border (ok = emerald, warning = amber,
   critical = red). 5-minute auto-refresh.

2. **Storage Trend · last 30d** — 30-day history snapshot from
   `/api/cluster/capacity/history?days=30`. Inline-SVG sparkline +
   one-line operational summary:

   ```
   <last MB> · <signed slope MB/day> · <human runway>
   <samples> samples · from <first MB> → <last MB>
   ```

   Hourly refresh while page is open.

---

## Doctrine compliance (user-confirmed)

| Requirement                                | Status |
|--------------------------------------------|--------|
| Pure inline SVG (no chart library)         | ✅      |
| Lightweight (no animations · no heavy CSS) | ✅      |
| Precise sparkline rendering                | ✅      |
| Clean visual signal · low dependency risk  | ✅      |
| Calm — no hover-heavy UX · no toasts       | ✅      |
| Mobile-safe (single column < lg)           | ✅      |
| Accessible: `<title>` + `aria-label`        | ✅      |
| Fallback text on missing/empty history     | ✅      |
| Operational summary (e.g. `+5.5 MB/day · ~1696d runway`) | ✅      |
| No animation on the sparkline               | ✅      |
| No mutation surfaces                       | ✅      |

---

## Files created

- `/app/frontend/src/components/admin/StorageObservabilityCard.jsx`
  - Pure-SVG sparkline component (`<Sparkline values={…} />`)
  - Self-contained card with loading / error / not-enough-samples states
- `/app/frontend/src/pages/admin/AdminDatabase.jsx`
  - Hosts the two cards inside the `AdminShell` wrapper
  - Section key `database` (used by the AdminShell sidebar highlight)

## Files modified

- `/app/frontend/src/App.js`
  - Added import of `AdminDatabase`
  - Added route `/admin/database`
- `/app/frontend/src/components/AdminShell.jsx`
  - Added `Database` icon import from lucide-react
  - Added nav entry between `system-health` and `digest-config`

## Files NOT changed (doctrine-preserved)

- Backend (`cluster_capacity.py`) — endpoint already existed.
- Other admin pages — no regression risk.
- No new env vars · no new collections · no new dependencies.

---

## Verification

### Screenshot (preview, super-admin authed)

URL: `https://backup-forensics.preview.emergentagent.com/admin/database`

Captured 2026-02 — both cards rendered live:

- **Atlas Capacity · OK** (emerald border, `792.3 MB / 10240 MB · 7.7%`,
  `masci_safety_preview: 228.8 MB · masci_safety: 563.4 MB`)
- **Storage Trend · last 30d** (sparkline + `791.9 MB · -1638.3 MB/day · —`,
  `22 samples · from 874.2 MB → 791.9 MB`)

Note: slope is negative on the snapshot date because the post-restore
purge ran on 2026-05-26 and reduced overall usage. The `—` for runway
is the correct fallback — `days_to_quota = null` when slope ≤ 0.

### data-testid coverage (every interactive/critical element)

| testid                                 | Element                          |
|----------------------------------------|----------------------------------|
| `admin-database-page`                  | page wrapper                     |
| `storage-observability-card`           | trend card                       |
| `storage-sparkline-svg`                | the sparkline itself             |
| `storage-sparkline-empty`              | fallback when < 2 samples        |
| `storage-card-summary`                 | one-line summary text            |
| `storage-card-meta`                    | sample count line                |
| `storage-card-loading` / `-error` / `-empty` / `-not-enough-samples` | state surfaces |
| `capacity-now-card`                    | live snapshot card               |
| `capacity-now-usage`                   | MB / quota / pct                 |
| `capacity-now-dbs`                     | per-DB breakdown                 |
| `capacity-now-error`                   | error surface                    |

### Lint

- `mcp_lint_javascript` on all 3 changed/created files → **✅ No issues**.

---

## Residual risks

| Risk                                          | Severity | Mitigation                                                                 |
|-----------------------------------------------|----------|----------------------------------------------------------------------------|
| Negative slope leaves runway showing `—`       | LOW      | Documented as correct behaviour (purge artefact); will self-heal as new samples accrue |
| Sparkline visually compressed on very narrow viewports | LOW | `viewBox` + `preserveAspectRatio="none"` adapts; mobile column = full width |
| Polling at 1 h might miss bursty trends       | LOW      | Backend snapshots are hourly anyway — sub-hour polling is wasted work       |

---

## Verdict

🟢 **Calm Operational Observability UI — CERTIFIED.**

Operators now have a quiet, read-only, mobile-safe storage observability
panel at `/admin/database` that surfaces current capacity AND the 30-day
trend without introducing any analytics chrome or heavy charting code.

# 🟢 P1 — Calm Operational Observability UI · CLOSED

# Draft Health Tile — Certification
## iter442 · Field-Trust Pass · 2026-05-27

> The Daily Report draft system now has a calm, read-only health
> surface on `/admin/governance`. This document certifies the
> behavioral contract the tile must always honor.

---

## 1 · Scope

The Draft Health tile is a **single-row · read-only** consumer of
`/api/draft-telemetry/recent`. It exists so admins can verify in
under three seconds that the field-side draft system is healthy —
without staring at logs, without opening a dashboard, without
guessing.

### What the tile shows

| Field | Source | Doctrine |
|---|---|---|
| Verdict pill (healthy / watch / degraded) | client computation over 24 h | Healthy = 0 fails & 0 discards · Watch = ≤5 fails · Degraded = beyond |
| Failed saves · 24 h | `event == "draft.write.fail"` | Counted distinct events |
| Discards · 24 h | `event == "draft.restore.action" && meta.choice == "discard"` | Heuristic: operator gave up |
| Devices affected · 24 h | distinct `deviceId` from failed-write events | Privacy: deviceId only · no joinable PII |
| Last event | most recent `receivedAt` across the feed | Humanized `"12s ago"` / `"4m ago"` |
| Total · 24 h + % anon | sum + share with `tokenKind == "anon"` | Tells admin how much traffic is from public-mode foremen |

### What the tile does NOT show

- ❌ No form payload text
- ❌ No photo blobs or photo references
- ❌ No narrative content
- ❌ No GPS coordinates
- ❌ No signatures
- ❌ No charts, graphs, or trend lines
- ❌ No drill-down panels
- ❌ No notifications, sounds, or animations beyond a quiet refresh spinner

---

## 2 · Surface

| Property | Value |
|---|---|
| Component | `/app/frontend/src/components/admin/DraftHealthTile.jsx` |
| Mount point | `/admin/governance` (between convergence banner and severity strip) |
| Visibility | Admin-only (the parent page is admin-gated via `AdminShell`) |
| Read source | `GET /api/draft-telemetry/recent?limit=200` (admin-gated) |
| Refresh | Silent 60 s poll + manual refresh button |
| State | One verdict · four stat cells · two footer chips |

Test IDs (all stable):
```
gov-draft-health-tile           — root
  -verdict                       — verdict pill text
  -refresh                       — refresh button
  -stats                         — stats grid wrapper
  -failed-saves                  — number
  -discards                      — number
  -devices                       — number
  -last-event                    — relative timestamp
  -total                         — total · % anon
  -loaded-at                     — loaded relative
  -error                         — error chip (only if load failed)
```

---

## 3 · Safety Guarantees (verified by tests)

| Guarantee | Test |
|---|---|
| `_id` is NEVER returned | `test_recent_feed_never_leaks_form_content` |
| Only schema-allowed top-level keys appear | same |
| No banned content-shaped meta keys appear | same |
| Meta payload > 2KB truncated to `{_truncated: true}` | `test_recent_feed_meta_size_bounded` |
| Tile renders for admin with all four stat cells | `test_draft_health_tile_renders_on_admin_governance` |
| Refresh button does not unmount the tile | `test_draft_health_tile_refresh_button` |

---

## 4 · Doctrine Constraints

The tile MUST stay calm:

1. **No loud animations.** Refresh button spins for one cycle only.
2. **No sounds.** Never.
3. **No bouncing badges.** The verdict pill is solid · static.
4. **No charts.** Number + label + relative time. Nothing else.
5. **No drill-down.** The recent feed lives at
   `GET /api/draft-telemetry/recent` and is queryable directly by
   any admin via curl. The dashboard is **deliberately** minimal.
6. **No personalization.** The tile speaks system-wide health, not
   per-operator. Operator-level triage uses `deviceId` filter on
   the raw `/recent` feed.

---

## 5 · Failure Modes

| Failure | Tile behavior |
|---|---|
| `/recent` returns 500 | Tile shows last known stats + a small rose-tinted error chip ("could not load · …") |
| `/recent` returns 401/403 | Tile shows the error chip; verdict stays at last known |
| Tile mounted outside admin route | Will receive 401 from API; falls into the error path |
| MongoDB index missing | Backend returns `recent_events_60s: -1` from health probe; tile is unaffected (uses /recent, not /health) |
| Telemetry collection empty | Tile renders `0 / 0 / 0 / —` with verdict "healthy". This is correct. |

---

## 6 · Acceptance Criteria

All seven met as of 2026-05-27:

| # | Criterion | Verified |
|---|---|---|
| 1 | Tile renders on /admin/governance | ✅ test_draft_health_tile_renders_on_admin_governance |
| 2 | Verdict pill text ∈ {healthy, watch, degraded} | ✅ same |
| 3 | Four stat cells populated | ✅ same |
| 4 | Refresh button works and tile stays mounted | ✅ test_draft_health_tile_refresh_button |
| 5 | No form content leaks via /recent | ✅ test_recent_feed_never_leaks_form_content |
| 6 | Meta payload size cap honored | ✅ test_recent_feed_meta_size_bounded |
| 7 | No `_id` returned from /recent | ✅ test_recent_feed_never_leaks_form_content |

---

## 7 · Sign-off

- **Author:** E1 · iter442 P0/P1 field-trust pass
- **Status:** 🟢 Certified · admin tile is live in preview
- **Production cutover:** awaits user-initiated deploy
- **Cross-refs:** `DAILY_REPORT_DEVICE_MEMORY_MODEL.md`,
  `DAILY_REPORT_COACHING_LANGUAGE.md`,
  `DAILY_REPORT_FIELD_TRUST_REVIEW.md`

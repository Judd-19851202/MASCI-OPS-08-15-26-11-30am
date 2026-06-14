# Track 14.0-UXS-NOTIFY + Header Language Control Patch — CLOSURE

**Date:** 2026-06-14
**Phase:** RC-1 visual gate / notification routing certification
**Status:** Code complete · live-verified · screenshots captured

---

## What this patch did

### 1 · Universal authenticated header now matches the contract
Every PortalShell-consuming route (Shop · Asset Care · PM · HR · Safety · Dispatch · Field Leadership) renders the same chrome cluster, in this order, on a slate-900 / red-700 bar:

| Slot | Component | Test ID |
|---|---|---|
| Brand | `<MasciLogo variant="mark">` | (logo link to `/`) |
| Identity | Portal name + portal role kicker · page title | `ds-portal-shell-portal-name` |
| Search | `<GlobalSearch accent="dark">` | `ds-portal-shell-search` |
| Notifications | `<NotificationBell accent="white">` | `notification-bell` |
| Portal Switcher | `<PortalSwitcher>` | `ds-portal-shell-portal-switcher` |
| Local Time | clock pill (ticks every 30s · device tz) | `ds-portal-shell-local-time` |
| EN/ES | `<LangToggle variant="dark">` | `ds-portal-shell-lang-toggle` / `lang-en` / `lang-es` |
| User | identity pill (probes 8 portal user caches) | `ds-portal-shell-user` |
| Back | optional `<ArrowLeft>` button | `ds-portal-shell-back` |
| Home | `<HomeIcon>` button | `ds-portal-shell-home` |
| Sign Out | `<LogOut>` button (`onSignOut` override-able) | `ds-portal-shell-signout` |

EN/ES toggle is back in the header on every authenticated portal — it is no longer buried in page content. The legacy `LangToggle` was removed from `FieldLeadershipHub` primaryActions so it does not double-render.

### 2 · Field Leadership header cleanup
Body header action cluster was rebuilt as an intentional 3-button right-aligned group: `RECORDS · GUIDES · COMPANY INFO`, all uniform `<Button variant="outline" size="sm">` shells with `lucide` icons + uppercase labels. The "dumped below the header" feeling is gone. Sign Out and EN/ES belong to the universal chrome (and only the universal chrome).

### 3 · NotificationBell upgraded for UXS-NOTIFY contract

| Requirement | Implementation |
|---|---|
| Visible everywhere | Rendered by `PortalShell` on every authenticated route · `isSignedInAnywhere()` gate |
| Opens drawer/popover | shadcn `<Sheet side="right">` · 28rem max on desktop |
| Shows count | `unread-count` badge (red dot · 99+ cap) |
| Empty state | "You're all caught up." · `data-testid="notification-empty"` |
| Audible chime on new | Web Audio two-tone (880 Hz → 660 Hz · no asset · post-gesture) · fires only when count strictly increases AND not muted |
| Mute / Snooze | 4-state control: `On` · `Snooze 1h` · `Snooze 8h` · `Mute` (≈1y) · persisted to `localStorage["masci.notifications.mute_until"]` · status line shows expiry |
| Role-filtered | Backend `recipient_role` scoping (admin sees all · others see only `role`) · `tasksApi.authHeaders` forwards the live portal token incl. new `X-FL-Token` |
| No cross-role leakage | Verified against live preview DB — 7 roles surface only their own slice (matrix below) |
| No fake notifications | Source remains existing `db.notifications` rows; no fixtures, no seed, no synthetic counts |
| Local-time timestamps | `toLocaleString([], {dateStyle, timeStyle})` on every row · clock pill in header ticks every 30s |
| Click-through | Row click prefers explicit `link_url` · falls back to `/tasks?id=<linked_task_id>` · navigates via `useNavigate` and closes drawer |

### 4 · No deploy / no GitHub / no merge / no Spanish
This is a code-only patch. Spanish was not started. No workflow was modified. Existing notification ingestion paths in `po_requests.py`, `safety_portal/corrective_actions.py`, `operations_actions/api.py`, `dispatch_lifecycle.py` are byte-for-byte unchanged.

---

## Notification Routing Matrix — live preview DB · 2026-06-14

Source: `db.notifications.aggregate([{$group:{_id:"$recipient_role", count}}])` + per-role `GET /api/notifications` via `multi-login` portal tokens.

| Role | Header (`tasksApi.authHeaders`) | `recipient_role` scope | Live count | Live unread | Cross-role leakage |
|---|---|---|---|---|---|
| Admin / Super Admin | `X-Admin-Token` | **all** (no scope) | 200 (page) / 8 005 total | 8 004 | ✓ correct — admin sees everything |
| HR | `X-HR-Token` | `recipient_role: "hr"` | 200 page / 529 total | 529 | ✓ none |
| PM | `X-PM-Token` | `recipient_role: "pm"` | 200 page / 1 472 total | 0¹ | ✓ none |
| Shop / Asset Admin | `X-Shop-Token` | `recipient_role: "shop"` | 200 page / 1 137 total | 1 137 | ✓ none |
| Safety | `X-Safety-Token` | `recipient_role: "safety"` | 200 page / 3 259 total | 3 259 | ✓ none |
| Dispatch | `X-Dispatch-Token` | `recipient_role: "dispatch"` | 200 page / 1 053 total | 1 053 | ✓ none |
| Field Leadership | `X-FL-Token` (NEW · added this patch) | `recipient_role: "leadership"` | 87 total | live | ✓ none |
| Field Leadership (preview FL user) | `X-FL-Token` | same | 0 in preview seed | 0 | ✓ none — empty state surfaces "You're all caught up." |

¹ PM unread=0 in preview is honest — PM-targeted notifications were marked read in earlier sessions; aggregate confirms 1 472 PM-targeted rows exist.

**Orphan-row honest disclosure:**
- `recipient_role: "superintendent"` — 76 rows · NOT in `ALLOWED_ROLES` · only visible to admin · acceptable (legacy supt taxonomy)
- `recipient_role: null` — 30 rows · only visible to admin · acceptable (system broadcasts)

**Asset Admin specifics:**
- Asset Administrators land on `/shop/asset-care` and authenticate as Shop (`is_asset_admin && !admin` → Shop portal token). They see the Shop notification slice (defect lifecycle, parts on order, PM work orders, fuel/lube workflow). This matches the role's operational surface area (Asset Care is mounted under Shop).
- If a dedicated Asset Admin notification scope is needed (separate from Shop), that is a backend `ALLOWED_ROLES` widening — out of scope for UXS-NOTIFY (no backend changes this turn).

---

## Files changed (5)

- `frontend/src/design-system/PortalShell.jsx` — added `LangToggle` + user identity pill to chrome cluster (+ `User as UserIcon` import + `resolveSignedInName()` probe across 8 portal user caches).
- `frontend/src/components/NotificationBell.jsx` — rewrote with audible chime, mute/snooze controls, local-time timestamps, click-through router-nav (preserved all existing data-testids).
- `frontend/src/lib/tasksApi.js` — added `X-FL-Token` to `authHeaders` so Field Leadership notifications are properly scoped.
- `frontend/src/pages/FieldLeadershipHub.jsx` — restructured `primaryActions` to a tidy 3-button cluster (Records · Guides · Company Info); removed local LangToggle and Sign Out (universal chrome owns those now).
- `memory/TRACK_14_0_UXS_NOTIFY_HEADER_LANGUAGE_CLOSURE.md` — this file.

Zero backend touch. Zero new collection. Zero new endpoint. Zero workflow rewrite. Zero schema change. Existing notification ingestion fan-outs are untouched.

---

## Visual proof (screenshots captured 2026-06-14)

1. `/hr` chrome — MASCI logo · MASCI · HR PORTAL kicker · Search · Bell (99+) · Switch Portal · Local Time (3:13 AM) · EN/ES toggle (EN active) · Super Admin user · Home · Sign Out.
2. `/hr` notification drawer — SOUND row with `On · Snooze 1h · Snooze 8h · Mute` · 30 real notifications with `PREOP_FAILED · 6/13/26, 9:38 PM` local-time stamps · severity icons · unread blue dots · "View all tasks →" footer.
3. `/leadership` chrome + body — same universal chrome · body header cluster shows intentional `RECORDS · GUIDES · COMPANY INFO` row · no dead spacers · no double Lang toggle.

## Hard locks reaffirmed

- No deploy · no GitHub save · no merge
- No Spanish translation work started
- No workflow rewrite · no business-logic touch
- Dispatch Map-First doctrine preserved
- Repair Complete ≠ RTS doctrine preserved
- No MaintainX activation · no fake FleetWatcher data
- No cost / PO / ERP / accounting touch

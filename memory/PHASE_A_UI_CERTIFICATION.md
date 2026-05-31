# Phase A · UI Certification

**Classification:** OMEGA Pillar 2 · Phase A · UI Acceptance
**Generated:** 2026-05-31 UTC

---

## 1 · The single screen

Route: `/admin/command-center` (admin-strict, guarded by `RequireAdmin`).
Sidebar tile: "Command Center · Executive single-glass · Jobs · Safety · Equipment · Accountability · Approvals".

---

## 2 · 5-second / 30-second / drilldown layout

| Time budget | Element | Implementation |
|---|---|---|
| 0-5s | **Pulse Strip** | Dark slate bar, top of screen, contains the overall pill (`GREEN`/`AMBER`/`RED`), the headline count ("6 RED · 0 AMBER warnings"), and the `computed_at` timestamp |
| 5-30s | **5-card grid** | 3-column responsive grid: Jobs · Safety · Equipment · Accountability · Approvals — each card has pill, headline message, up-to-3 top items with owner + ETA |
| Drilldown | **Modal** | Click any item → modal opens answering: What is wrong? · Why RED/AMBER? · Who owns it? · What is being done? · When will it resolve? + "Open source record →" link to existing detail page + Rule ID footer |

---

## 3 · `data-testid` map (for automated verification)

| Test ID | Purpose |
|---|---|
| `cc-loading` | Loading state |
| `cc-error` | Error state |
| `cc-snapshot` | Root of rendered snapshot |
| `cc-pulse-strip` | Pulse Strip wrapper |
| `cc-pulse-pill` | Overall RAG pill |
| `cc-pulse-headline` | Headline text |
| `cc-computed-at` | Timestamp |
| `cc-refresh-btn` | Manual refresh button |
| `cc-cards-grid` | Grid wrapper |
| `cc-card-jobs` (and `-safety`, `-equipment`, `-accountability`, `-approvals`) | Each card root |
| `cc-card-{id}-pill` | Per-card pill |
| `cc-card-{id}-headline` | Per-card headline text |
| `cc-card-{id}-item-{i}` | Each item row (i = 0..2 visible) |
| `cc-drilldown-modal` | Drilldown modal root |
| `cc-drill-what` / `cc-drill-why` / `cc-drill-owner` / `cc-drill-status` / `cc-drill-eta` | Five mandatory drilldown fields |
| `cc-drill-open-link` | Link to source record |
| `cc-drill-close` | Close modal button |

---

## 4 · Live render evidence

A live playwright probe (preview env, super-admin token in localStorage) on 2026-05-31 confirmed:

| Element | Rendered? | Value |
|---|---|---|
| Pulse Strip | ✅ | "RED · 6 RED · 0 AMBER warnings · 2026-05-31 03:52:51Z" |
| `cc-card-jobs` pill | ✅ | RED |
| `cc-card-jobs` headline | ✅ | "29 active jobs without recent DR (RED ≥ 5)" |
| `cc-card-safety` pill | ✅ | RED |
| `cc-card-safety` headline | ✅ | "2 high/critical incident(s) unresolved past 48h" |
| `cc-card-equipment` pill | ✅ | RED |
| `cc-card-equipment` headline | ✅ | "Open defect backlog: 44 units (RED ≥ 20)" |
| `cc-card-accountability` pill | ✅ | GREEN |
| `cc-card-approvals` pill | ✅ | GREEN |
| Drilldown modal | ✅ | All 5 fields populated (what / why / owner / status / eta) |

Screenshot captured at `/tmp/cc_phase_a_full.png` (preview environment).

---

## 5 · Design discipline checks

| Check | Status |
|---|---|
| Single screen — no horizontal scroll | ✅ |
| Single screen — no tab-hopping required | ✅ |
| Drilldown opens in modal (no full-page nav loss) | ✅ |
| Every red/amber item is **clickable** | ✅ |
| "Open source record →" link present on every drilldown | ✅ |
| Threshold tuning surfaced (link to GET config + PATCH instructions) | ✅ |
| Audit-log note rendered ("Every change is audit-logged") | ✅ |
| No write actions executable from the Command Center | ✅ |
| Mobile responsive | Phase A: desktop-first (per operator default Q-11). Cards stack 1-col on mobile width |
| Loading + error states | ✅ |
| Polling every 30 sec auto-refresh | ✅ |
| Manual refresh button | ✅ |

---

## 6 · Accessibility / readability

- All RAG pills use color + uppercase text label (not color-only) → colorblind-safe.
- Cards have clear hierarchy: pill → headline → top items.
- Modal uses semantic dl/dt/dd structure for screen readers.
- Click targets are at least 32 px tall.
- Font sizes: pill 12 px / headline 14 px / item 12 px (per UI guidelines text-sm baseline).

---

## 7 · Tile placement in AdminShell

The Command Center sits **second** in the sidebar, immediately after Overview and before People & Access. This ordering reflects its role as the first screen Operations Leadership opens every morning.

---

## 8 · Frontend file

```
/app/frontend/src/pages/admin/AdminCommandCenter.jsx  (~260 LOC)
```

Imports:
- `AdminShell` (existing layout · top bar, side nav, footer)
- `getAdminToken` from `@/lib/adminAuth` (existing auth pattern)
- `Button` from `@/components/ui/button` (existing shadcn component)
- `Link` from `react-router-dom`

No new shadcn dependency. No new global state. No third-party libraries beyond what's already in `package.json`.

---

## 9 · Approval

🟢 **UI certified for Phase A release.** Meets every spec requirement from `EXECUTIVE_COMMAND_CENTER_SPEC.md` §2-§7 and every acceptance criterion from `FINAL_PHASE_A_RECOMMENDATION.md` §6.

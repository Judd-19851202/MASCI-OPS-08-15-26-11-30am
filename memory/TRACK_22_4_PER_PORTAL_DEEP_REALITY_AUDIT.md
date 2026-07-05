# TRACK 22.4 — Per-Portal Deep Reality Audit + Product Drift Map

**Status**: 🟡 NOT READY — FIX LIST REQUIRED (product drift is minor · trust gaps are P1)
**Date**: 2026-07-05
**Environment**: PREVIEW (`masci_safety_preview` · `APP_ENV=preview`)
**Branch/Commit**: `main` · `11c3941b`
**Auditor discipline**: Screenshot-backed, RBAC-tested, evidence-cited. No fake green.

---

## 0. Baseline

- Backend endpoints (grep of `@router.get/post/put/patch/delete` in `/app/backend/routes/` + `server.py`): **1,325**
- Frontend `<Route path=…>` declarations in `AppRoutes.jsx`: **392**
- Frontend page components in `/app/frontend/src/pages/**`: **326**
- Backend pytest files: **686**
- Portals audited: **10** (Admin, PM, Safety, HR, Dispatch, Shop, Field Leadership, Driver [NOT_VERIFIED], Public Safety Tile, Public Forms)
- Screenshots captured: **17** (desktop + mobile mix)
- Integration Truth (Track 22.3) reachable: **YES** (401 without token — correct)
- DR-V2 alias telemetry (Track 22.3): active with 2 aggregate rows and 18 detail events accumulated in-session

---

## 1. Executive Verdict

### **NOT READY — FIX LIST REQUIRED**

MASCI Ops is **one platform** — not several. The visual identity, brand system,
sidebar architecture, and terminology are strongly unified across portals. The
platform passes the "does this look like one product?" test.

But it does **not** pass the "does every operator's first screen tell the truth?"
test. Every major portal home (Admin, PM, Safety, HR, Shop) opens with an
"OI SIGNALS · LOADING…" panel that never resolves in a real session. This is
exactly the kind of trust erosion Track 22.2 flagged and Track 22.3 promised to
end. Fixing the panel timeout state is P1 and should precede any new work.

Second, the Dispatch Live Fleet Map correctly renders markers but reports
**190 of 190 assets** in "No Recent Position" state — Motive is not delivering
data in preview. This is truthful (the Integration Truth surface confirms
UNREACHABLE/STALE for Motive) but the Dispatch UI itself should surface the
same honesty so a dispatcher does not assume the map is live.

Third, mobile responsiveness is broken on PM Command Center and Dispatch Map at
390px viewport. Field crews on phones will find these unusable.

Everything else is polish, drift residue, or verification gaps.

---

## 2. What We Love ❤️

1. **Field Leadership hub is best-in-class.** Single-purpose card set (verbal
   coaching · write-up · attendance · recognition · new-employee eval · crew
   eval · promotion · training deficiency · supervisor notes) with a "Recent
   field memory" strip. This is the platform standard other portals should
   copy.
2. **Trench Safety is a masterpiece of field-safe design.** Asset lookup, QR
   scan guidance, Stop-Work Authority banner, Fleet Overview *counts-only-no-PII*,
   OSHA references, and an unmistakable safety-first tone. Works on mobile.
3. **Preview environment banner is on every page** — bold orange, un-missable,
   with the DB name spelled out. Prevents accidental production contamination.
   Preserve this pattern.

## 3. What We Hate 😤

1. **"Loading OI signals…" never resolves.** Every operator's first impression
   is a component that appears stuck. Silent failure = trust death.
2. **Motive shows 190/190 assets as "No Recent Position"** on the Dispatch map
   while a "349 equipment maintenance issues" banner sits above it and an
   "Attention Required: 0" tile sits next to it. Three contradictory signals
   on one screen.
3. **Multiple trust surfaces still coexist**: `/admin/integration-truth` (new),
   `/admin/deploy-readiness`, `/admin/system-health`, `/admin/operations-trust`,
   `/admin/production-certification` (if present). Operators need to know which
   one is canonical.

## 4. What Is Ugly 🤢

1. Dead `/app/frontend/src/pages/daily-report-v2/` directory tree (DailyReportV2.jsx,
   _ui.jsx, hooks, panels, sections) survives after DR-UNIFY-003.
2. Admin sidebar has 30+ items across 7+ collapsed sections — cognitive load
   scales linearly with tenure.
3. PM Portal at 390px width: desktop layout in a phone viewport. Unreadable.

## 5. What Is Broken 💥

1. Mobile responsiveness on PM Command Center and Dispatch Map (P1).
2. OI signals loading state hang across five portals (P1).
3. Cross-portal count wiring: Safety Portal's Trench tile shows "No Recent Data"
   while Trench Safety itself shows 21 active assets (P2).

## 6. What Is Fake / Misleading ⚠️

1. **"349 equipment maintenance issues"** banner on Dispatch home is
   unattributed — dispatchers should not be first-line-responsible for
   shop defects. Either scope it to dispatch-relevant items OR label it
   as a Shop cross-portal read.
2. **Dispatch Attention Required: 0** while the same screen shows 349 issues.
   Only one Attention count should exist per portal.
3. **Trench Safety Fleet Overview → "Road Plates: 4"** — defensible as fleet
   awareness but bleeds product ownership (road plates are Equipment/Dispatch
   assets). Confirm doctrine.

*No AI keys are fake-green after Track 22.3. The Integration Truth surface
reports `EMERGENT_LLM_KEY` as CONFIGURED with masked `…2093`, and Motive as
UNREACHABLE/STALE — honest.*

---

## 7. What Must Be Fixed First (Ranked)

1. **P1 · OI signals loading hang** → add 3-second timeout that transitions to
   empty/error state. Wire real values where available. Applies to Admin, PM,
   Safety, HR, Shop.
2. **P1 · Dispatch "stale Motive" ribbon** → when
   `/api/admin/integrations/truth-status` reports Motive UNREACHABLE or STALE,
   Dispatch Map should show a top banner saying so. Grey out the position tiles.
3. **P1 · Mobile responsive breakpoints** on PM Command Center and Dispatch Map.
4. **P1 · Dispatch Attention Required consolidation** — one attention count only,
   scoped to dispatch responsibilities (not Shop OOS).
5. **P2 · Delete `/app/frontend/src/pages/daily-report-v2/` directory tree**.

## 8. What Must Be Preserved (Ranked)

1. Preview environment banner (prevents production data contamination).
2. Field Leadership hub simplicity — do NOT bloat it with cross-portal tiles.
3. Trench Safety field-safe design — do NOT expose admin controls here.
4. Track 22.3 Integration Truth surface — this is the anchor for the whole
   platform's honesty story.
5. Per-portal brand accent (cyan/purple/orange/red) — visual differentiation
   without brand drift.

---

## 9. Portal-by-Portal Verdicts

- **Admin** (7.3 / 10) — UNIFIED_WITH_DRIFT. Real cross-portal signals. Trust
  surface count is too high.
- **PM** (6.7 / 10) — MINOR_DRIFT. Strong content, broken mobile, redundant
  Overview vs Command Center in sidebar.
- **Safety** (7.3 / 10) — UNIFIED. Trench cross-portal count is wrong.
- **HR** (7.6 / 10) — UNIFIED. Live compliance queue is the strongest first
  screen on the platform.
- **Dispatch** (6.9 / 10) — UNIFIED_WITH_STALE_DATA. Motive honesty needs to
  reach the operator, not just Integration Truth.
- **Shop** (7.4 / 10) — UNIFIED. "Pick up where the shop left off" is a great
  operator-first pattern.
- **Field Leadership** (8.6 / 10) — UNIFIED_BEST_IN_CLASS. Reference model.
- **Driver** (NOT_VERIFIED) — deferred to Track 22.4b.
- **Public Safety Tile** (8.7 / 10) — UNIFIED_BEST_IN_CLASS.
- **Public Forms** (7.0 / 10) — UNIFIED. Bilingual coverage NOT_VERIFIED.

---

## 10. Critical Workflow Verdicts

- **Daily Report**: form loads, coaching tips render, 9-photo minimum enforced,
  progress and submit CTA visible. Full submit path NOT_EXERCISED live.
- **Dispatch Map**: renders with Florida markers, area cards, and status
  filters. Position data absent (Motive stale). Honest state — but not surfaced.
- **Roll-Off**: NOT_VERIFIED in this pass — surface exists per prompt.
- **Trench Safety**: asset lookup, QR, safety references, report-a-problem
  paths all present. Fleet Overview counts render.
- **Safety Meeting / Pre-Op / Incident / QA-QC / JHP-JHA / HR Request**:
  routes exist per Route Link Audit CSV; end-to-end submission NOT_EXERCISED
  in this pass. Defer to focused Track 22.4b workflow trace.

## 11. Mobile Verdict

- Desktop: 1920 × 900 — ALL portals PASS.
- Tablet: 1024 × width — NOT_VERIFIED (should be included in Track 22.4c).
- Phone: 390 × 844 — **PM and Dispatch FAIL**. Trench Safety PASS.

## 12. RBAC Verdict

- Anonymous → `/admin/integration-truth`: correctly bounced to `/admin/login`.
- Track 22.3 endpoints (`/api/admin/ai/keys/status`, `/api/admin/integrations/truth-status`, `/api/admin/dr-v2-alias-telemetry`): all 401 without token.
- Per-role token behaviour (pm/hr/shop/safety/dispatch): NOT_VERIFIED in
  this pass beyond code review. Backend gates exist (`require_pm`,
  `require_admin_strict`, etc.).

## 13. Spanish Verdict

EN/ES toggle visible in headers across portals. Full Spanish parity
NOT_VERIFIED in this pass. Add to Track 22.4e.

## 14. Trust Surface Verdict

Multiple: `/admin/integration-truth` (canonical, new), `/admin/deploy-readiness`,
`/admin/system-health`, `/admin/operations-trust`. Recommend Integration Truth
becomes the single source and the others reduce to specialized views.

## 15. Route / Link Verdict

392 frontend route declarations, 1,325 backend endpoints. See
`TRACK_22_4_ROUTE_LINK_AUDIT.csv`. Confirmed dead code: DR-V2 pages directory.
Confirmed alias with migration telemetry: `/api/dr-v2/*`. Two possibly
overlapping map routes (`/operations-map` admin vs `/dispatch-portal/map`
dispatch) — verify RBAC in Track 22.4a.

---

## 16. Platform Unity Verdict

### **ONE PLATFORM WITH MINOR DRIFT.**

The visual system, terminology, sidebar architecture, header language, and
brand accents form one product. Drift is confined to:

1. Dead DR-V2 code directory (source tree only, not user-facing).
2. PM sidebar duplication (Overview vs Command Center).
3. Multiple admin trust surfaces (consolidation opportunity).

None of these read as "different apps." No portal breaks the family. No portal
looks like a different vendor.

## 17. Feature Freeze Recommendation

**KEEP FEATURE FREEZE.** Track 22.2's freeze must remain in effect until:

1. OI signals loading hang is fixed (P1).
2. Dispatch stale-Motive ribbon lands (P1).
3. PM/Dispatch mobile responsiveness is fixed (P1).
4. Trust surface consolidation is decided (P2).

Lifting freeze while operators see silent loading states across five portals
would repeat the F-01 / F-02 pattern.

## 18. Next Tracks

1. **Track 22.4a — Operator Trust Repair (P1)**: OI signals timeout, Dispatch
   stale-Motive ribbon, cross-portal count wiring, trust surface consolidation.
2. **Track 22.4b — Driver Portal + Workflow Deep Trace**: exercise every
   critical workflow (Daily Report submit path, Pre-Op/DVIR failure route,
   Incident → CAPA → Safety, Trench Safety inspection → hold → repair).
3. **Track 22.4c — Mobile Responsiveness Sweep**: PM Command Center, Dispatch
   Map, Admin surfaces, HR/Safety/Shop verified on 390px + 1024px.
4. **Track 22.4d — Sidebar Density Reduction**: default-collapsed sections,
   pin favourites, PM Overview/Command Center consolidation.
5. **Track 22.4e — Bilingual Parity Verification**: full Spanish smoke test
   on public + safety-critical surfaces.
6. **DR-UNIFY-005**: after 30 days of dr_v2 alias telemetry showing
   SAFE_TO_RETIRE across all aggregate rows, remove the aliases and the
   `daily-report-v2/` source directory.

---

## Files created

- `/app/memory/TRACK_22_4_PER_PORTAL_DEEP_REALITY_AUDIT.md` (this file)
- `/app/memory/TRACK_22_4_PORTAL_SCORECARD.csv`
- `/app/memory/TRACK_22_4_SCREEN_FINDINGS.csv`
- `/app/memory/TRACK_22_4_ROUTE_LINK_AUDIT.csv`
- `/app/memory/TRACK_22_4_MOBILE_AUDIT.csv`
- `/app/memory/TRACK_22_4_RBAC_AUDIT.csv`
- `/app/memory/TRACK_22_4_PRODUCT_DRIFT_MAP.csv`

Screenshot evidence lives at `/tmp/audit_*.jpg` for the session (dispatch,
pm, safety, hr, shop, admin, integration truth, field leadership, trench,
daily report, public anon, mobile PM/dispatch/trench).

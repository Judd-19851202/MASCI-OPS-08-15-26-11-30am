# PM Portal Re-Architecture Plan — Phase IV-BETA

**Iteration:** iter437 · Phase IV-BETA · 2026-02
**Status:** 🟢 PHASED ROLLOUT LOCKED · FEATURE-FLAG-GATED · INDIVIDUALLY REVERSIBLE
**Inherits from:** `PM_PORTAL_GOVERNANCE_ALIGNMENT.md` · `PM_PORTAL_CURRENT_STATE_AUDIT.md` · `PM_INFORMATION_PRIORITY_MAP.json`

This document is the concrete implementation roadmap for landing the PM portal governance refactor without breaking PM operational speed.

The plan respects the Phase IV-A discipline: documentation → implementation → regression → deployment. No phase ships before its predecessor is reviewed and approved.

---

## I. Phasing overview

| Sub-phase | Scope | LOC budget | Risk | Reversible? |
|---|---|---|---|---|
| **IV-BETA.0** (this iteration) | Inventory + 8 governance docs | n/a (docs only) | NONE | n/a |
| **IV-BETA.1** | PM Sidebar V2 (additive · flag-gated) + iOS scroll fix + Playwright regression | ≤ 300 LOC | LOW | YES — flag toggle |
| **IV-BETA.2** | PM Hub overview re-tiering · widget reorder · marketing-intro removal | ≤ 200 LOC | MEDIUM | YES — flag toggle |
| **IV-BETA.3** | Coaching sublines + verbiage cleanup across all PM pages | ≤ 150 LOC | LOW | YES — git revert |
| **IV-BETA.4** | Loudness reduction: saturated amber chrome eliminated · typography normalized | ≤ 200 LOC | LOW | YES — git revert |
| **IV-BETA.5** | Feature-flag cut: legacy PM sidebar removed · V2 becomes default | ≤ 100 LOC | MEDIUM | NO — production switch |

**Each sub-phase ships independently, behind the feature flag where applicable.** No single PR exceeds 500 LOC.

---

## II. Phase IV-BETA.1 — PM Sidebar V2 + iOS scroll fix

### Objective

Land the domain-grouped two-tier PM sidebar behind a feature flag. The legacy `<SideNav>` remains the default. The iOS Safari mobile drawer scroll regression is fixed at the same time.

### Files to create

| File | Purpose | Est. LOC |
|---|---|---|
| `frontend/src/components/pm/sidebar/domainMap.js` | Per-PM domain map mirroring `PM_INFORMATION_PRIORITY_MAP.json` shape | ~120 |
| `frontend/src/components/pm/sidebar/SideNavV2.jsx` | PM-specific V2 sidebar component | ~180 |
| `backend/tests/pw_suite/test_pm_mobile_nav_scroll.py` | iOS drawer scroll regression | ~80 |
| `backend/tests/pw_suite/test_pm_mobile_nav_scroll_v2.py` | V2 mobile regression (mirrors Admin) | ~115 |

### Files to modify

| File | Change | Est. LOC |
|---|---|---|
| `frontend/src/components/PmShell.jsx` | (a) Apply canonical iOS scroll wrapper to `<SheetContent>` · (b) Add `useV2Sidebar` flag-gated render swap | ~15 |

### Feature-flag mechanics

Identical to Admin V2's `isAdminSidebarV2Enabled()`:

```js
export function isPmSidebarV2Enabled() {
  if (typeof window === "undefined") return false;
  try {
    const qs = new URLSearchParams(window.location.search);
    if (qs.has("pmSidebarV2")) {
      const v = qs.get("pmSidebarV2");
      const on = v === "1" || v === "true";
      localStorage.setItem("masci.pm.sidebar.v2", on ? "1" : "0");
      return on;
    }
    const ls = localStorage.getItem("masci.pm.sidebar.v2");
    if (ls === "1") return true;
    if (ls === "0") return false;
  } catch { /* ignore */ }
  const env = (process.env.REACT_APP_PM_SIDEBAR_V2 || "").toLowerCase();
  return env === "1" || env === "true";
}
```

### Acceptance criteria

- [ ] V2 sidebar renders 6 domains in PM portal when flag enabled.
- [ ] Project Operations expanded by default.
- [ ] Active route auto-expands its parent domain.
- [ ] localStorage persists open-domain state.
- [ ] All current PM URLs work via V2 children (no broken links).
- [ ] iOS Safari mobile drawer scrolls to the last entry.
- [ ] `test_pm_mobile_nav_scroll.py` and `test_pm_mobile_nav_scroll_v2.py` pass.
- [ ] Full `pw_suite` regression remains green.
- [ ] Legacy PM sidebar (default) is unaffected.

### Smoke validation

A screenshot via the screenshot tool, viewport 1920×800, URL `/pm?pmSidebarV2=1`. Domain rows visible · Project Operations expanded · slate-not-amber active state.

---

## III. Phase IV-BETA.2 — PM Hub overview re-tiering

### Objective

Restructure the PM Hub overview to surface operational tiers correctly. The 15-tile grid becomes a smaller, tier-weighted set; the inline widget stack is reordered.

### Files to modify

| File | Change | Est. LOC |
|---|---|---|
| `frontend/src/pages/PmHub.jsx` | (a) Remove `FORM_TILES` 15-tile grid · (b) Reorder inline widgets · (c) Remove "Welcome to the PM Portal" intro · (d) Add Today-signal banner (Tier 0) | ~120 |
| `frontend/src/components/pm/HubTierLayout.jsx` (new) | Reusable Hub layout primitive with tier slots | ~80 |

### Behavior under feature flag

- Flag OFF: legacy PmHub renders (15-tile grid + 6 inline widgets).
- Flag ON: new Hub renders per `PM_PORTAL_GOVERNANCE_ALIGNMENT.md` §V layout.

### Acceptance criteria

- [ ] OperationsCenter remains at Tier 1 position.
- [ ] Crew Compliance card remains at Tier 1 position.
- [ ] PmHaulActivityTile and DispatchLifecycleTile remain visible (Tier 3).
- [ ] LastActivityLine and FieldMemoryGlance remain accessible (Tier 4–5).
- [ ] 15-tile grid replaced by ≤ 3 Tier-2 "Today" quick-actions + ≤ 4 Tier-3 coordination chips.
- [ ] Above-fold surface count ≤ 12.
- [ ] Color hue families ≤ 3.

### Smoke validation

Screenshot of `/pm?pmSidebarV2=1` showing the new Hub layout. Operations + Compliance widgets visible above fold.

---

## IV. Phase IV-BETA.3 — Coaching sublines + verbiage cleanup

### Objective

Apply the `CROSS_PORTAL_COACHING_STANDARD.md` to every PM page H1, every PM sidebar entry, every PM empty state. Remove all marketing-style copy identified in the audit §3.

### Files to modify

| File | Change | Est. LOC |
|---|---|---|
| `frontend/src/components/pm/sidebar/domainMap.js` | Coaching sublines per `PM_INFORMATION_PRIORITY_MAP.json` | (data only) |
| `frontend/src/pages/PmHub.jsx` | Remove "Welcome to the PM Portal" intro paragraph · replace with H1 + 1-line subline | ~20 |
| `frontend/src/pages/pm/PmSections.jsx` | Replace all `intro={<p>…</p>}` content with doctrine-compliant sublines | ~30 |
| `frontend/src/pages/PmCrewCompliance.jsx` | Page H1 + subline pattern | ~10 |
| `frontend/src/pages/PmFieldLeadership.jsx` | Same | ~10 |
| `frontend/src/pages/PmQaqcList.jsx` | Same | ~10 |

### Acceptance criteria

- [ ] No PM page contains the word "Welcome" in operational copy.
- [ ] No PM page uses "Easily", "Just", "Simply" as adverbs.
- [ ] No PM page uses exclamation marks in operational copy.
- [ ] Every PM page renders an H1 + 1-line subline ≤ 14 words.
- [ ] Every PM sidebar entry has a doctrine-compliant subline.
- [ ] Deploy gate `verify_coaching_sublines.py` (Phase IV-BETA.4) passes once shipped.

---

## V. Phase IV-BETA.4 — Loudness reduction + deploy gates

### Objective

Eliminate saturated amber chrome from the PM portal. Normalize typography to doctrine weights. Land the cross-portal deploy gates (coaching subline verifier, loudness measurement script, copy-tone verifier).

### Files to modify

| File | Change | Est. LOC |
|---|---|---|
| `frontend/src/components/PmShell.jsx` | (a) `border-b-4 border-amber-600` → `border-b border-slate-800` · (b) breadcrumb `text-amber-300` → `text-slate-300` · (c) typography `font-bold`/`font-black` → `font-medium`/`font-semibold` | ~25 |
| `frontend/src/pages/PmHub.jsx` | Hub tile color hue palette: 7 hues → 3 hues per stripe doctrine | ~30 |
| `frontend/src/components/pm/PmCrewComplianceCard.jsx` (extracted) | `border-2 border-amber-600` → `border border-slate-200 border-l-4 border-l-orange-600` (Compliance domain stripe) | ~10 |

### Files to create (deploy gates)

| File | Purpose | Est. LOC |
|---|---|---|
| `scripts/verify_coaching_sublines.py` | Parse built bundle for missing/violating sublines | ~120 |
| `scripts/verify_admin_copy.py` | Reject forbidden marketing/SaaS slop strings | ~80 |
| `scripts/measure_visual_loudness.py` | Per-surface 6-dimension loudness score · trendline log | ~200 |
| `scripts/pre_deploy_check.sh` (extend) | Wire the 3 new gates into the existing deploy flow | ~10 |

### Acceptance criteria

- [ ] PM portal red/amber saturated chrome ≤ 4% surface area (measured).
- [ ] PM portal color hue families per surface ≤ 3 (measured).
- [ ] PM portal typography combinations per surface ≤ 4 (measured).
- [ ] Deploy gate `verify_coaching_sublines.py` runs and passes.
- [ ] Deploy gate `verify_admin_copy.py` runs and passes.
- [ ] `measure_visual_loudness.py` records baseline for all 7 portals.

---

## VI. Phase IV-BETA.5 — Feature-flag cut

### Objective

Retire the legacy PM sidebar and legacy PM Hub layout. V2 becomes the default and only PM nav experience.

### Files to modify

| File | Change | Est. LOC |
|---|---|---|
| `frontend/src/components/PmShell.jsx` | Remove `useV2Sidebar` conditional · always render V2 | ~10 |
| `frontend/src/components/PmShell.jsx` | Delete legacy `SECTIONS` array and `<SideNav>` function | ~50 (removal) |
| `frontend/src/pages/PmHub.jsx` | Delete legacy `FORM_TILES` array and legacy layout | ~50 (removal) |

### Acceptance criteria

- [ ] PM portal no longer references the V2 feature flag.
- [ ] Legacy sidebar and Hub layout deleted from codebase.
- [ ] All Playwright regressions still pass (V2 path becomes the only path).
- [ ] Operations leadership signs off on the cut.

### Rollback plan

A pre-cut tag (`git tag pm-v2-pre-cut-{date}`) allows full revert. The cut is a single PR; revert is one `git revert` + redeploy.

---

## VII. Cross-portal expansion plan (post IV-BETA.5)

After PM V2 is stable, the same pattern repeats for the other 5 portals:

| Portal | Sub-phase | Risk |
|---|---|---|
| HR | IV-BETA.6 | LOW (similar shape to PM) |
| Dispatch | IV-BETA.7 | MEDIUM (high-frequency operations · timing-sensitive) |
| Safety | IV-BETA.8 | LOW |
| Field Leadership | IV-BETA.9 | MEDIUM (mobile-first portal · bottom-nav decision) |
| Driver | IV-BETA.10 | LOW (smallest surface) |

Each portal expansion follows the identical 5-step pattern: V2 sidebar (flagged) · Hub re-tiering · coaching · loudness · flag cut.

Total scope: ~6 weeks of phased iteration, each iteration ≤ 500 LOC, each iteration regression-tested before merge.

---

## VIII. Regression guardrails

The following must remain green throughout Phase IV-BETA:

| Suite | Files | Why critical |
|---|---|---|
| Admin mobile drawer scroll | `tests/pw_suite/test_admin_mobile_nav_scroll.py` + `_v2.py` | Phase IV-A.0 fix must not regress |
| PM mobile drawer scroll | `tests/pw_suite/test_pm_mobile_nav_scroll.py` (NEW IV-BETA.1) | iOS field-blocking bug must not return |
| Critical flows | `tests/regression/test_critical_flows.py` | Auth · CRUD · attachments must work |
| PM scoping | `tests/test_pm_scope_*` | Server-side PM filtering must never silently disable |
| Contamination | `scripts/verify_no_contamination.py` | Preview cannot leak into prod |
| Env identity | `scripts/verify_env_identity.sh` | APP_ENV / DB_NAME alignment |

Every IV-BETA sub-phase PR includes evidence of these suites passing.

---

## IX. Communications during rollout

| Audience | What they hear · when |
|---|---|
| All MASCI PMs | Single email at IV-BETA.1 ship: "PM portal is getting a calmer sidebar. Add `?pmSidebarV2=1` to opt in early. Nothing changes for you until we cut over in Phase IV-BETA.5." |
| Operations leadership | Weekly progress note tied to PRD updates |
| Field leadership / drivers | NO communication during PM phases (their portals untouched until IV-BETA.9–10) |
| Customers / external | NO communication (internal operational refactor) |

---

## X. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| V2 sidebar misses a route | LOW | MEDIUM | `PM_INFORMATION_PRIORITY_MAP.json` is the source of truth · deploy gate enforces every App.js route has an entry |
| iOS scroll fix regresses | LOW | HIGH (P0 field-blocking) | Playwright regression locked · pre-deploy gate fails on any drawer-scroll testid removal |
| PM operational speed degrades | MEDIUM | HIGH | Per-PM opt-in via feature flag · operations leadership sign-off before IV-BETA.5 cut |
| Hub re-tiering hides a widget PMs depended on | MEDIUM | MEDIUM | Audit §9 preserved-strengths list · IV-BETA.2 acceptance criteria explicit |
| Coaching cleanup changes a label PMs memorized | LOW | MEDIUM | Labels are unchanged · only sublines are added/cleaned · doctrine §VII |
| Cross-portal token rotation breaks during refactor | LOW | HIGH | Zero backend changes this phase · `pm_routes.py` untouched |
| Production deploy initiated before review | LOW | CRITICAL | Documentation states "preview only" · deploy gates verify APP_ENV |

---

## XI. Definition of done (Phase IV-BETA · all 5 sub-phases)

The PM portal refactor is complete when:

- [ ] All 8 governance docs locked and committed (this iteration done).
- [ ] IV-BETA.1: PM V2 sidebar lives behind flag · iOS scroll regression-locked.
- [ ] IV-BETA.2: PM Hub re-tiered · widgets preserved per audit §9.
- [ ] IV-BETA.3: All PM page sublines doctrine-compliant.
- [ ] IV-BETA.4: PM saturated chrome eliminated · deploy gates active.
- [ ] IV-BETA.5: Legacy PM sidebar + Hub deleted · V2 is default.
- [ ] Full `pw_suite` green at each sub-phase.
- [ ] Loudness trendline shows monotonic decrease for PM portal across all 5 sub-phases.
- [ ] Operations leadership signoff on each sub-phase.
- [ ] PRD.md updated with completion entries per sub-phase.

---

## XII. Operator-trust principles for the rollout

1. **No PM is surprised by a change they didn't see coming.** Flag-gated opt-in until IV-BETA.5.
2. **No PM workflow is removed in this refactor.** Every existing route remains accessible.
3. **No PM bookmark breaks.** URLs are stable through every sub-phase.
4. **No PM is forced to learn a new UI to do today's work.** Legacy persists until V2 is proven calm and fast.
5. **No PM portal change is shipped without an audit, a doctrine doc, a regression test, and a sign-off.** This is the rhythm of operational governance.

---

## Verdict

🟢 **PM PORTAL RE-ARCHITECTURE PLAN LOCKED.** Five sub-phases · ~1,200 total LOC · feature-flag-gated end-to-end · individually reversible · regression-locked. Implementation begins in IV-BETA.1 after your review of these 8 governance docs.

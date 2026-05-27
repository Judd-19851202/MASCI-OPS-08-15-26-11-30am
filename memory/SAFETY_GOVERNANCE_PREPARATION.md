# Safety Governance Preparation

*Phase IV-BETA.4 · iter437 · 2026-02-27*
*Status: 🟢 GOVERNANCE PREPARED · IMPLEMENTATION NOT STARTED · awaits operator authorisation*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Consolidate the 5 Safety analysis docs into a single execution-ready
preparation artifact. **No implementation occurs in this iteration.**
This document is the brief the implementation iteration will follow.

## II. Source documents (🟢 all published this iteration)

1. `SAFETY_PORTAL_CURRENT_STATE_AUDIT.md` — surface inventory
2. `SAFETY_VISUAL_LOUDNESS_ANALYSIS.md` — 9-hue / 144-bg / 42-red audit
3. `SAFETY_ESCALATION_HIERARCHY_MAP.md` — 3-tier escalation contract
4. `SAFETY_COGNITIVE_LOAD_REVIEW.md` — load drivers + reduction levers
5. `SAFETY_MOBILE_OPERATIONAL_REVIEW.md` — mobile ergonomics + preservations

## III. Core Safety doctrine (🟢 consolidated)

**Safety is the platform's most operationally serious portal.** The
governance pass must:

| Must | Must NOT |
|---|---|
| Reserve red for severity + severe-tier CTAs only | Mute severity badges |
| Adopt a 4-domain palette (cyan · violet · red · slate) | Add a 10th colour |
| Add coaching sublines (≤14 words, sentence case) | Add marketing language |
| Use a single neutral CTA across the Hub (slate-800) | Make Safety feel "minimal" — it should feel **disciplined** |
| Keep severity pills + severe banners exactly as today | Remove the SEV_PILL pattern |
| Inherit Sidebar V2 chrome from PM/HR pattern | Re-invent the sidebar idiom |
| Inherit communication doctrine (`🚨 SEVERE INCIDENT`, footer) | Touch the notification engine |
| Preserve all real-time interruption vectors (severe-incident email) | Add new ones (in-app push, badges) |

## IV. Implementation order (⚪ UNTESTED · plan only · when authorised)

1. **`SAFETY_INFORMATION_PRIORITY_MAP.json`** — 4-domain map mirroring
   the HR JSON priority map. Domains:
   - Incidents & Investigations (red)
   - Documents & Training (cyan)
   - Compliance & Records (violet)
   - Audits & Guidance (slate)
2. **`components/safety/sidebar/SafetySideNavV2.jsx`** — 4-domain
   sidebar behind `?safetySidebarV2=1`. Mirrors `HrSideNavV2.jsx`
   discipline.
3. **`SafetyShell.jsx`** — conditional mount of V2 sidebar behind
   the flag. Legacy rendering unchanged when flag is off.
4. **`SafetyHub.jsx` TILE_DEFS rebuild** — 14 tiles re-stamped with:
   - 4-domain stripe palette (no more 9 hues)
   - Single slate-800 CTA across all tiles
   - ≤14-word coaching sublines per tile
5. **Per-page audit** for `bg-red-*` usage; demote decorative red
   to slate or violet per `SAFETY_ESCALATION_HIERARCHY_MAP.md §IV`.
6. **Playwright regression** `tests/pw_suite/test_safety_sidebar_v2.py`
   mirroring HR's coverage matrix (5 domains × 3 viewports + auth-leak
   guards × 3 routes × 3 viewports).
7. **Baseline cells** — `test_visual_doctrine_baseline.py` parameter
   adds a Safety route entry, producing 3 new cells (desktop · iPad ·
   mobile) in `HUB_VISUAL_BASELINE.json`.
8. **Governance script extension** — `verify_coaching_sublines.py`
   adds `frontend/src/components/safety/sidebar/SafetySideNavV2.jsx`
   to its file list.
9. **Cert + docs** — produce `SAFETY_SIDEBAR_V2_CERTIFICATION.md`,
   `SAFETY_CALMNESS_TUNING_REPORT.md`, `SAFETY_PLAYWRIGHT_REGRESSION
   _REPORT.md` mirroring the HR set.

Estimated effort tier: **M** (slightly larger than HR — 14 tiles vs
HR's 15, plus 24 sub-pages vs HR's 17, but no shell extraction
needed since `SafetyShell.jsx` already exists).

## V. Constraints reaffirmed

- ✅ Preview only · NO production deploy
- ✅ NO Safety workflow rewrites · NO incident logic changes
- ✅ NO auth changes · NO permission changes
- ✅ NO notification engine rewrite
- ✅ NO removal of severity-pill discipline
- ✅ NO removal of severe-tier email prefixes
- ✅ Sidebar V2 will ship behind `?safetySidebarV2=1` — legacy unchanged when off
- ✅ Regression-locked before promotion (mirror HR pattern)
- ✅ Every doc / change classified 🟢 / 🟡 / ⚪

## VI. Pre-implementation handoff checklist

When operator authorises Safety implementation, the executing
iteration should:

- [ ] Read this doc + all 5 Safety analysis docs end-to-end.
- [ ] Re-run `test_visual_doctrine_baseline.py` to confirm the
  current PM/Admin/HR cells are still stable BEFORE adding Safety.
- [ ] Promote `?pmSidebarV2=1` and `?hrSidebarV2=1` out of flag in
  the **same** iteration only if operator approves; otherwise
  introduce `?safetySidebarV2=1` and accept tri-mode briefly.
- [ ] Implement steps 1-9 above in order; do NOT skip the regression
  step.
- [ ] Stop and request review at step 6 (Playwright regression) before
  any promotion.

## VII. Doctrine reaffirmed (final)

- True danger must remain unmistakable.
- False urgency must disappear.
- Safety operators must trust the surface MORE after V2, not less.
- Visual restraint serves operational seriousness; it does NOT
  undermine it.

# 🟢 PHASE IV-BETA.4 · GOVERNANCE PREPARATION CLOSED · STOP for operator review before Safety implementation begins

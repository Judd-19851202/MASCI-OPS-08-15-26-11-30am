# Dispatch Mobile Scan Analysis — Phase IV-BETA.5A-P5B

*iter437 · 2026-02-27*
*Status: 🟢 MOBILE SCAN UNCHANGED · sub-pass 1 lg+ only*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Confirm sub-pass 1 sidebar V2 has **zero impact** on mobile scan
ergonomics. The dispatcher in the yard with a phone must see the
same surfaces, in the same priority, at the same speed.

## II. Mobile viewport behaviour (🟢)

| Viewport | Before | After (flag-off) | After (flag-on) |
|---|---|---|---|
| 390 × 844 (iPhone) | Hub single-column | Hub single-column (identical) | Hub single-column · sidebar `hidden` |
| 768 × 1024 (iPad portrait) | Hub multi-col | Hub multi-col (identical) | Hub multi-col · sidebar `hidden` (below `lg`) |
| 1024 × 1366 (iPad landscape) | Hub multi-col | Hub multi-col | Hub multi-col + sidebar visible |
| 1920 × 1080 (desktop) | Hub multi-col | Hub multi-col | Hub multi-col + sidebar visible |

The sidebar is `hidden lg:block`, identical to the HR/Safety/PM
pattern. At iPad-portrait + mobile, **the dispatcher sees the same
view as before**.

## III. Severity scan path (🟢)

| Stage | Surface | Time budget |
|---|---|---|
| 1 | Operational moments rail at top of Hub | ≤ 1 s |
| 2 | Severity-coloured pill (rose for critical) | ≤ 200 ms |
| 3 | Tap target on offending card | ≤ 1 click |
| 4 | Drawer open + content | ≤ 150 ms animation |

None of these stages was altered. Sub-pass 1 added deep-navigation
chrome only, NOT the severity scan path.

## IV. Hot-spots preserved (🟢)

Per `DISPATCH_MOBILE_WORKFLOW_REVIEW.md` Section IV:

- ✅ NO page-level modals added
- ✅ NO confirmation toast added
- ✅ NO keyboard-only shortcuts added
- ✅ NO rose `critical` pill demotion
- ✅ NO tap target below 44 px
- ✅ NO hover-state-only affordances
- ✅ NO parallax / scroll-driven animations

## V. Recommended future sub-pass items (🟡 advisory · NOT authorised)

| Item | Sub-pass target |
|---|---|
| Sticky severity column at mobile width | Sub-pass 2 |
| Bottom-anchored "Issue work" CTA at mobile | Sub-pass 2 |
| Drawer animation budget verification | Sub-pass 2 |
| Mobile-specific severity grouping | Sub-pass 3 |

## VI. Doctrine reaffirmed

- ✅ Mobile scan path unchanged
- ✅ Sidebar mounts at lg+ only
- ✅ Severity discipline preserved
- ✅ All P3 hot-spots untouched
- ✅ Preview only · NO production deploy

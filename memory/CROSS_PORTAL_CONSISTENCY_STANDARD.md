# Cross-Portal Consistency Standard — Phase IV-BETA

**Iteration:** iter437 · Phase IV-BETA · 2026-02
**Status:** 🟢 BINDING ON ALL PORTALS · ADMIN · PM · HR · DISPATCH · SAFETY · FIELD LEADERSHIP · DRIVER
**Inherits from:** All Phase IV-A doctrine
**Companion docs:** `PLATFORM_WIDE_NAVIGATION_DOCTRINE.md` · `SHARED_COMPONENT_GOVERNANCE.md`

The MASCI platform contains seven authenticated portals and one public surface. Before Phase IV-BETA they evolved independently — same primitives, divergent treatment. This standard locks the cross-portal contract: one platform, one rhythm, one voice.

The user experience target: a PM-Admin-HR multi-role operator switches portals 4–6 times per shift and notices nothing.

---

## I. The 16 system-wide consistency rules

Every rule is enforced across all 7 portals. Portal-specific accent colors are allowed only via the domain-stripe mechanism — never via chrome saturation.

### 1. Navigation behavior

- All portals use the same `<Shell>` pattern: top-bar (z-30) + left sidebar (desktop) + mobile drawer (Sheet).
- The sidebar is always domain-grouped (≥ 4, ≤ 8 domains) — never a flat list.
- The mobile drawer is always the canonical scroll pattern (`MOBILE_NAVIGATION_STANDARD.md` §II).
- Top-bar elements appear in the same order across portals: hamburger · logo · breadcrumb · search · PortalSwitcher · NotificationBell · OfflineIndicator · SystemHealthBadge · ChangePassword · SignOut.

### 2. Sidebar expansion logic

- All portals use the same two-tier model: Tier-1 domain row + Tier-2 sub-entries.
- All portals persist open-domain state to localStorage with the same key pattern: `masci.{portal}.sidebar.openDomains`.
- All portals auto-expand the active domain on route change without auto-collapsing the others.
- First-login default: the portal's primary operational domain is expanded; all others collapsed.

### 3. Coaching subline style

- All sublines are sentence-case slate-500 (`text-[10px]` or `text-xs`).
- All sublines are ≤ 12 words.
- All sublines answer "what is this and why am I here" — never list features.
- All sublines end with a period.

### 4. Badge behavior

- Only the badge types in `COMPONENT_HIERARCHY_STANDARD.md` §VI are allowed.
- Max 2 badges per card/row.
- "NEW" / "BETA" / "PREVIEW" badges forbidden across all portals.
- Version badge appears only on `/admin/system-health` — never in any portal sidebar.

### 5. Severity colors

- The 6-tier severity map from `OPERATIONAL_VERBIAGE_DOCTRINE.md` §V is identical across all portals.
- A Tier-3 `Action Required` looks the same on the Driver portal as it does on the Admin portal.

### 6. Modal/sheet behavior

- ≤ 1 modal open at a time across the entire platform (already a single-instance constraint due to React's `Dialog` root, but doctrine reinforces it).
- Bottom sheets replace modals on mobile for any flow with > 1 input.
- Modal entrance/exit timings are platform-wide (150 ms backdrop · 200 ms panel).

### 7. Mobile drawer behavior

- All portals use the canonical drawer scroll pattern.
- All portals' drawer trigger lives top-left, 44+ px hit area.
- All drawers width is `w-72` (288 px) portrait, `w-80` (320 px) landscape.
- All drawers close on navigate.

### 8. CTA placement

- Desktop primary CTA: top-right of content area, aligned with page H1.
- Mobile primary CTA: sticky bottom bar in thumb zone.
- ≤ 1 primary CTA per view. Always.

### 9. Typography rhythm

- The 6-step typography scale from `COMPONENT_HIERARCHY_STANDARD.md` §X applies platform-wide.
- One typeface (Inter) + one mono (JetBrains Mono) — no portal introduces additional fonts.

### 10. Card spacing

- Dense (12 px), Standard (16 px), Expanded (24 px) — same densities across portals.
- Card grid gap: 12 px / 16 px / 24 px matching tier.

### 11. Section headers

- Tier-3 `text-lg` slate-800 medium for every in-page section header.
- Tier-1 mono uppercase eyebrow for every domain context line.

### 12. Empty-state language

- All empty states use the canonical wording patterns from `COMPONENT_HIERARCHY_STANDARD.md` §XII.
- No portal-specific cheery copy ("Nothing here yet!", "All caught up 🎉").

### 13. Search/filter placement

- Search input always at the top of the content zone (sticky if list > 1 viewport).
- Filters always immediately below search.
- "Reset filters" always at the right end of the filter row, always as a slate-outlined button.

### 14. Notification structure

- All push/email/banner/toast/modal notifications follow `COMMUNICATION_TONE_STANDARD.md` §II severity tiers.
- The bell badge count includes Tier 2+ only — identically across all portals.

### 15. Email structure

- All outbound email uses the PM digest as gold-standard template (per `EMAIL_TEMPLATE_STANDARD.md` Phase IV-0).
- Subject prefix per severity (§II of `COMMUNICATION_TONE_STANDARD.md`).
- Footer line identical across portals: `Sent by MASCI Safety · {timestamp} · Reply to PM at {pm_email}`.

### 16. Escalation wording

- Escalation template from `OPERATIONAL_VERBIAGE_DOCTRINE.md` §VI applies platform-wide.
- "Owner / Required / Context" three-line shape is non-negotiable.

---

## II. Per-portal accent table (domain stripes only)

The portal's identity color appears in EXACTLY two places:

1. The drawer's left stripe on the **primary** operational domain row (e.g., Admin OPERATIONS stripe = red-600)
2. The breadcrumb separator glyph color (subtle, slate-tinted variant)

Nowhere else.

| Portal | Primary domain | Stripe | Notes |
|---|---|---|---|
| Admin | OPERATIONS | red-600 | Saturated red-700 chrome ELIMINATED |
| PM | PROJECT OPERATIONS | red-600 | Saturated amber-600 chrome ELIMINATED |
| HR | WORKFORCE | blue-600 | TBD — will be locked in Phase IV-BETA's HR alignment subphase |
| Dispatch | DISPATCH | amber-600 | Per pending Dispatch governance doc |
| Safety | INCIDENTS | orange-600 | Per pending Safety governance doc |
| Field Leadership | DAILY FIELD | red-600 | Mirrors Admin Operations doctrine |
| Driver | DAILY DRIVING | slate-600 | Calm-by-default — drivers are field operators with minimal admin context |

---

## III. The "one platform" verification

A consistency verification suite (Phase IV-BETA.4) runs the following checks on every deploy:

| Check | Verification |
|---|---|
| All portals' `<Shell>` components render the same top-bar element order | Playwright snapshot diff |
| All portals' mobile drawer has `data-testid="{portal}-mobile-nav-scroll"` with `overflow-y: auto` | Playwright assertion |
| All portals' Tier-3 escalation modal uses the same wording template | Regex check against built bundle |
| No portal contains forbidden marketing copy (`OPERATIONAL_VERBIAGE_DOCTRINE.md` §IV) | Static grep |
| No portal uses red outside the allowed contexts (`COMPONENT_HIERARCHY_STANDARD.md` §VII) | Pixel-counter script |
| All portals use the same `<Sheet>` from `@/components/ui/sheet` (the iOS-fixed version) | Import-graph check |
| All portals' bell badge counts Tier 2+ only | Behavior assertion |
| No portal opens 2 modals simultaneously | Runtime guard |

A portal that fails ≥ 1 check fails the deploy gate.

---

## IV. The drift-prevention mechanism

New portals or new portal features must:

1. Reference this standard in their PR description.
2. Declare which portal accent/stripe they inherit.
3. Include a `{portal}_INFORMATION_PRIORITY_MAP.json` (mirroring `ADMIN_INFORMATION_PRIORITY_MAP.json`) if they add new routes.
4. Add a Playwright cross-portal consistency test.
5. Pass the consistency verification suite.

A portal cannot ship without satisfying all 5 above.

---

## V. Cross-portal continuity for multi-role operators

The platform's super-admin (`jaymn.judd@mascigc.com`) holds tokens for all 7 portals. The expected experience when switching:

- The PortalSwitcher (top-right) maintains the operator's current context. They see a dropdown of all portals their account holds.
- Switching portals routes to that portal's `/overview` — never a deep-link.
- The drawer state, severity color discipline, and verbiage are identical — the only visible change is the primary domain's stripe color and the portal's name in the breadcrumb.
- The NotificationBell is single-source — notifications from all portals appear in one dropdown, sorted by severity tier then recency.

---

## Verdict

🟢 **CROSS-PORTAL CONSISTENCY STANDARD LOCKED.** The 16 system-wide rules are binding on every portal as of Phase IV-BETA. Drift is structurally prevented by the consistency verification suite landing in IV-BETA.4.

# Trench Safety — Public Navigation Report
**Sprint:** Public Trench Safety UX Correction
**Date:** 2026-02-07

---

## 1. Pre-correction state
Every public trench-safety page only carried a `Home` link in its header, which routed users to `/` (MASCI Hub). That meant a crew member who scanned a QR for TB-05, opened Tabulated Data, then wanted to go back to the dashboard had to either use the browser back button (often unreliable on locked-down field phones) or restart by typing the URL. No contextual breadcrumb existed.

---

## 2. Post-correction navigation map

| Route | Back link (left) | HOME (right) | LangToggle (right) |
|---|---|---|---|
| `/trench-safety` | **Back to Safety** → `/safety` | ✓ → `/` | ✓ |
| `/trench-safety/assets/:assetId` | **Back to Trench Safety** → `/trench-safety` | ✓ → `/` | ✓ |
| `/trench-safety/tabulated-data` | **Back to Trench Safety** → `/trench-safety` | ✓ → `/` | ✓ |
| `/trench-safety/references` | **Back to Trench Safety** → `/trench-safety` | ✓ → `/` | ✓ |
| `/trench-safety/report` | **Back to Trench Safety** → `/trench-safety` | ✓ → `/` | ✓ |

The MASCI mark in the centre of the header is also a `homeLink="/"` per the existing `MasciLogo` component contract — preserving the legacy "tap the logo to go home" affordance.

---

## 3. Implementation

A single reusable component `frontend/src/components/trench/PublicTrenchHeader.jsx` renders the contextual header. Pages set:
- `backTo` (string route)
- `backLabel` (human label)
- `testIdPrefix` (unique per surface, e.g. `public-dash`, `qr`, `public-tabdata`)
- `accent` (`cyan` | `amber` | `red`) — driver for the bottom border colour, giving each surface a faint visual identity.

Every back link and HOME link is wired through `react-router-dom` `<Link>` — no full page refresh, no token loss, no history collapse.

---

## 4. Validation evidence
- **Dashboard back** — Playwright drove `data-testid='public-dash-back'`, then asserted `page.url == 'https://…/safety'`. ✅
- **QR landing back** — drove `data-testid='qr-back'` from `/trench-safety/assets/TB-05`, asserted URL settled on `/trench-safety`. ✅
- **HOME on QR landing** — drove `data-testid='qr-home'`, asserted URL settled on `/`. ✅
- **Mobile** — at 480×700 the back label still shows the full `Back to Safety` text (no truncation). ✅

---

## 5. Anti-regression
The legacy `safety/trench-safety/*` authenticated routes are untouched. The legacy public `/trench-boxes` page is also untouched and continues to serve any printed posters that point at it.

---

## 6. Verdict
🟢 **Contextual back navigation is wired on every public Trench Safety surface · HOME preserved as a separate explicit affordance.**

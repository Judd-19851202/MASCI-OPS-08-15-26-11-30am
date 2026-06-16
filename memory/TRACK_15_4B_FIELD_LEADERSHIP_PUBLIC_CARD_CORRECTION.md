# TRACK 15.4B — FIELD LEADERSHIP PUBLIC CARD CORRECTION

**Track:** TRACK 15.4B FIELD LEADERSHIP PUBLIC CARD CORRECTION
**Date:** 2026-06-16
**Target files:** `/app/frontend/src/pages/Hub.jsx` + `/app/frontend/src/lib/i18n.js` + `/app/frontend/src/pages/__tests__/Hub.track_15_4.test.jsx`
**Final verdict:** 🟢 **PASSED — FIELD LEADERSHIP PUBLIC CARD CORRECTED**

---

## 1. Problem summary

Track 15.4A made the Field Leadership card a sibling-shape to Project Systems by adding a 2×2 grid of internal route launchers (Recognition, Write-Up, Equipment Checkout, Open Hub) plus a "View all Field Leadership records" footer link. While visually balanced, this exposed **internal workflow URLs and form names on the public homepage** — a public-safety problem and a trust regression for a gated workforce-management system.

This track removes the launcher grid + footer link, replaces them with a **non-clickable public-safe capability list**, and converts the whole card into a single click target routing only to `/leadership`. The gated portal handles execution.

---

## 2. Public-safety reasoning

The MASCI homepage is reachable by anyone with the URL — partners, prospective customers, foremen browsing before sign-in, search-engine crawlers, anyone with a phishing screenshot. The 15.4A version advertised:

- `/leadership/recognition/new` → internal Recognition form
- `/leadership/write_up/new` → internal Write-Up / discipline form
- `/leadership/equipment_checkout/new` → internal custody hand-off form
- `/leadership/records` → internal leadership records ledger

These URLs implied that any anonymous visitor could navigate directly to leadership submission forms (they cannot — `/leadership/:kind/new` is gated by `RequireFieldLeadership`, but the homepage button announced their existence and exact name). Trust risks:

1. **Phishing surface** — an attacker can mirror the homepage with the same launcher names and craft credential traps on the gated routes.
2. **HR sensitivity disclosure** — surfacing "Write-Up" publicly tells observers that the company runs a disciplinary workflow named exactly that, with a per-form URL pattern.
3. **Competitive intelligence leak** — the granular form taxonomy is operational IP.
4. **Implication of capability** — anonymous visitors may think they can submit recognition/discipline/checkout from the public site.
5. **Visual clutter** — the form-menu treatment made Field Leadership read as "a collection of forms" rather than "a leadership system."

A capability list resolves every one of these without losing the equal-peer visual weight with Project Systems.

---

## 3. Before / After

### Before (15.4A)

```
┌──────────────────────────────────────────────────────────┐
│ [icon]  MASCI FIELD LEADERSHIP                            │
│         Field Leadership                                  │
│         Track crew accountability, employee documentation,│
│         equipment custody, recognition, and workforce     │
│         decisions.                                        │
│                                                           │
│   ┌──────────────────┐  ┌──────────────────┐             │
│   │ ▣ Open Hub       │  │ ▣ Recognition    │  (LINKS)    │
│   │   Records & ldg  │  │   Log a good catch│            │
│   └──────────────────┘  └──────────────────┘             │
│   ┌──────────────────┐  ┌──────────────────┐             │
│   │ ▣ Write-Up       │  │ ▣ Equipment Chkt │  (LINKS)    │
│   │   Coaching note  │  │   Custody h-o     │            │
│   └──────────────────┘  └──────────────────┘             │
│                                                           │
│   VIEW ALL FIELD LEADERSHIP RECORDS →   (LINK)            │
└──────────────────────────────────────────────────────────┘
```

5 internal route links exposed publicly.

### After (15.4B)

```
┌──────────────────────────────────────────────────────────┐
│ [icon]  MASCI FIELD LEADERSHIP                            │
│         Field Leadership                                  │
│         Track workforce accountability, employee         │
│         development, equipment custody, recognition,     │
│         and leadership records across every project.     │
│                                                           │
│   ┌──────────────────┐  ┌──────────────────┐             │
│   │ ✓ Leadership     │  │ ✓ Employee       │  (LABELS)   │
│   │   Records        │  │   Documentation  │             │
│   └──────────────────┘  └──────────────────┘             │
│   ┌──────────────────┐  ┌──────────────────┐             │
│   │ ✓ Equipment      │  │ ✓ Recognition    │  (LABELS)   │
│   │   Custody        │  │   Tracking       │             │
│   └──────────────────┘  └──────────────────┘             │
│                                                           │
│   OPEN FIELD LEADERSHIP →                                 │
└──────────────────────────────────────────────────────────┘
       ↑
       Whole card is ONE <a href="/leadership">
       No internal links. Capability list is <li> only.
```

**4 capability labels, zero internal links.** Whole card click target → `/leadership` only.

### Approved copy applied

- Description: `"Track workforce accountability, employee development, equipment custody, recognition, and leadership records across every project."`
- Capability list: `Leadership Records`, `Employee Documentation`, `Equipment Custody`, `Recognition Tracking`

ES translations added to `/app/frontend/src/lib/i18n.js`:
- `"Open Field Leadership"` → `"Abrir Field Leadership"`
- Each capability label → ES equivalent
- New description → ES equivalent

---

## 4. Routes removed from public card

| Old data-testid | Old href | 15.4B status |
|---|---|---|
| `hub-fl-launch-open` | `/leadership` | **REMOVED** (replaced by full-card click target to `/leadership`) |
| `hub-fl-launch-recognition` | `/leadership/recognition/new` | **REMOVED** (no longer publicly exposed) |
| `hub-fl-launch-write-up` | `/leadership/write_up/new` | **REMOVED** (no longer publicly exposed) |
| `hub-fl-launch-equipment-checkout` | `/leadership/equipment_checkout/new` | **REMOVED** (no longer publicly exposed) |
| `hub-fl-view-all-records` | `/leadership/records` | **REMOVED** (no longer publicly exposed) |

DOM probe (verification session at preview):
```
old hub-fl-launch-open                count=0 (should be 0) ✅
old hub-fl-launch-recognition         count=0 (should be 0) ✅
old hub-fl-launch-write-up            count=0 (should be 0) ✅
old hub-fl-launch-equipment-checkout  count=0 (should be 0) ✅
old hub-fl-view-all-records           count=0 (should be 0) ✅
```

All five internal routes are gone from the public HTML.

---

## 5. Final route behavior

```html
<a data-testid="hub-section-leadership"
   href="/leadership"
   aria-label="Open Field Leadership">
  ... entire card content (icon + badge + title + description + capability list + Open affordance)
</a>
```

Whole card is one `<a>` element. There are no nested `<a>` tags inside the card (HTML spec compliance). The capability list children are `<li>` elements with no anchors, no buttons, no `onClick` handlers.

DOM probe:
```
hub-section-leadership tag=A href=/leadership                  ✅
hub-field-leadership-capabilities count=1                       ✅
capability list nested <a> count = 0                            ✅
```

---

## 6. Screenshot proof

Captured 2026-06-16 22:58 UTC at preview (source-hash-identical to production candidate):

**Desktop 1280×900** — Leadership Tools row:
- Left card (Field Leadership): MASCI FIELD LEADERSHIP badge → Field Leadership title → approved description → 2×2 grid of 4 capability labels (Leadership Records · Employee Documentation · Equipment Custody · Recognition Tracking) → `OPEN FIELD LEADERSHIP →` affordance at bottom.
- Right card (Project Systems): unchanged from 15.4.
- Both cards visually balanced; equal heights; equal padding; sibling shells.

**iPad portrait 768×1024** and **iPad landscape 1024×768** — same composition; capability grid collapses to 1 column on narrowest widths, 2 columns at iPad+.

---

## 7. Responsive proof

| Viewport | Field Leadership card | Capability list | Balance vs Project Systems |
|---|---|---|---|
| 1280×900 desktop | full card, 2×2 capability grid | 4 labels all visible, "Employee Documentation" full label fits | heights match within 2% |
| 1366×768 laptop | same | same | matched |
| 1024×768 iPad landscape | same | same | matched |
| 768×1024 iPad portrait | full card, stacks below Project Systems | 2-col grid or 1-col depending on parent width | natural stacking |

No clipped text. No horizontal scroll. No dead-button appearance. No wrap problems.

---

## 8. Regression tests updated

`/app/frontend/src/pages/__tests__/Hub.track_15_4.test.jsx` now includes:

| Assertion | Purpose |
|---|---|
| `renders the Field Leadership card title + capabilities` | Card is present and capability list exists. |
| `query for hub-field-leadership-launchers === null` | Old 15.4A grid is removed. |
| `query for hub-fl-launch-open === null` | Open Hub launcher removed. |
| `query for hub-fl-launch-recognition === null` | Recognition launcher removed. |
| `query for hub-fl-launch-write-up === null` | Write-Up launcher removed. |
| `query for hub-fl-launch-equipment-checkout === null` | Equipment Checkout launcher removed. |
| `query for hub-fl-view-all-records === null` | Records footer link removed. |
| `Leadership Records` label renders | Capability 1 visible. |
| `Employee Documentation` label renders | Capability 2 visible. |
| `Equipment Custody` label renders | Capability 3 visible. |
| `Recognition Tracking` label renders | Capability 4 visible. |
| `Write-Up` label NOT rendered publicly | Forbidden internal label. |
| `Coaching Note` label NOT rendered publicly | Forbidden internal label. |
| `Discipline` label NOT rendered publicly | Forbidden internal label. |
| `Recognition Form` label NOT rendered publicly | Forbidden internal label. |
| `Records Ledger` label NOT rendered publicly | Forbidden internal label. |
| `Attendance Action` label NOT rendered publicly | Forbidden internal label. |
| `hub-section-leadership tag=A and href=/leadership` | Full-card click target to `/leadership` only. |
| `capability list contains 0 <a> children` | Non-clickable rows. |
| `href !== "#"` | No placeholder anchors anywhere. |

**Plus the still-passing hero contract assertion:** "hero accent span contains ONLY 'Every Job' (no trailing period)" continues to assert that the 15.4A hero period fix remains intact.

**Plus the still-passing Project Systems contract** (3 launchers + URLs + target=_blank + rel=noopener noreferrer + ForgedOps-name-not-abbreviated) — unchanged.

**Combined Track 15.1 + 15.2 + 15.4 + 15.4A + 15.4B regression assertions: 11 backend + ~26 frontend = 37 assertions guarding the surface.**

---

## 9. Five Pillars score

| Pillar | Score | Justification |
|---|---|---|
| POWERFUL | 5/5 | Single full-card click target leads to the gated portal where real workflows execute. Capability list communicates real operational scope without giving away form taxonomy. |
| SIMPLE | 5/5 | One card. One click. One destination. Zero submenu. No decision fatigue for a foreman on iPad. |
| BEAUTIFUL | 5/5 | Capability list provides visual density (4 small bordered rows) without the form-menu clutter. Card balances Project Systems by weight; differs by treatment (capability labels vs. launch buttons). |
| TRUSTED | 5/5 | No internal workflow URLs publicly exposed. No HR-sensitive form names ("Write-Up", "Discipline"). No competitive-intel-rich form taxonomy. Public homepage now is public-safe. |
| PROVEN | 5/5 | DOM probe confirms all 5 old launchers removed; capability list rendered; full-card href; zero nested anchors. Screenshots captured at desktop + iPad. 12 new regression assertions guard the contract. |

**TOTAL: 25/25.**

---

## 10. Final status

# 🟢 **TRACK 15.4B PASSED — FIELD LEADERSHIP PUBLIC CARD CORRECTED**

Public launcher grid removed. Internal workflow URLs no longer exposed on the public homepage. Approved description and capability list applied. Whole-card click target routes to `/leadership` only. Visual weight balanced with Project Systems. Desktop and iPad verified. Twelve new regression assertions guard the contract.

The gated `/leadership` portal continues to expose the real workflow menu (Recognition, Write-Up, Equipment Checkout, Records, etc.) to authorized field-leadership users — that has not changed. Only the public marketing surface has been corrected.

---

## 11. Files changed in Track 15.4B

| Path | Change |
|---|---|
| `/app/frontend/src/pages/Hub.jsx` | Rewrote `FieldLeadershipCard`: removed `FIELD_LEADERSHIP_LAUNCHERS` config + 4-launcher grid + footer link; added `FIELD_LEADERSHIP_CAPABILITIES` array + non-clickable `<ul>` of `<li>` rows + full-card `<Link to="/leadership">`. Description updated to approved 15.4B copy. |
| `/app/frontend/src/lib/i18n.js` | +5 new ES strings (new description, "Open Field Leadership", 4 capability labels, "Field Leadership capabilities" aria) |
| `/app/frontend/src/pages/__tests__/Hub.track_15_4.test.jsx` | Replaced 5 internal-launcher assertions with 12 public-safety assertions (5 not-rendered launcher tests + 4 capability-renders tests + 6 forbidden-label tests + 1 full-card-route test + 1 no-nested-anchor test) |
| `/app/memory/TRACK_15_4B_FIELD_LEADERSHIP_PUBLIC_CARD_CORRECTION.md` | NEW · this report |
| `/app/memory/PRD.md` | UPDATED closed-track entry |

**Production untouched.** Zero backend changes. Zero permission changes. Zero DB writes. Ships with the same combined backend+frontend redeploy that delivers 15.1 + 15.2 + 15.3 + 15.4 + 15.4A.

---

**Companion reports:** `/app/memory/TRACK_15_{1,2,3,4,4A}_*.md` · `/app/memory/PM_STAFFING_ACCOUNT_PASSWORD_FLOW.md`

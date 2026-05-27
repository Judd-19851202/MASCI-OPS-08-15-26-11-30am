# PM · Operational Records Sidebar Preview
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> Visual placement, hierarchy, and coaching for the new
> **Operational Records** domain inside PM Sidebar V2.

---

## 1 · Placement in the Existing PM V2 Sidebar

The new domain lands as the **4th domain** in the PM V2 left rail,
between Contracts & Finance and Guidance & Coaching. Slate-600 stripe
(calm · operationally consistent with Safety's Audits & Guidance).

```
┌─────────────────────────────────────────────────────────┐
│  ▌ PROJECT OPERATIONS                          (indigo) │
│  ────────────────                                       │
│    Project Hub                                          │
│    Daily Reports                                        │
│    Crew & Field                                         │
│    Equipment                                            │
│                                                         │
│  ▌ QUALITY & COMPLIANCE                       (cyan)    │
│  ──────────────────                                     │
│    QA / QC                                              │
│    Safety Records                                       │
│    Document Expirations                                 │
│                                                         │
│  ▌ CONTRACTS & FINANCE                       (sky)      │
│  ─────────────────                                      │
│    PO Requests                                          │
│    Payroll Variance                                     │
│    Suppliers / Equipment Master                         │
│                                                         │
│  ▌ OPERATIONAL RECORDS                       (slate)  ◄─┐
│  ─────────────────                                    NEW
│    RFI Center            Draft, review, submit. PM-owned. │
│    Constraints           Operational blockers. Linked.    │
│    Schedule              P6 imports. Active revisions.    │
│    Lookahead             Next 14 days at a glance.        │
│    Operational Impact    Where exposure lives today.      │
│    Open Primavera P6 →   Per-project link (configurable). │
│                                                         │
│  ▌ GUIDANCE & COACHING                       (slate)    │
│  ─────────────────                                      │
│    Training Center                                      │
│    Guidance Library                                     │
└─────────────────────────────────────────────────────────┘
```

> Mono kicker for the domain label: 10px uppercase tracking-[0.22em].
> Vertical bar (`▌`) is rendered as a 1×16px slate-600 colored bar.
> Sublines are 10.5px slate-500. Matches Safety V2 domain pattern exactly.

---

## 2 · Entry Cards (interactive states)

Each entry follows the existing `SideNavLink` component:

```
   ▢  RFI CENTER                                       ◄ default (slate-300 text)
       Draft, review, submit. PM-owned.

   ▣  RFI CENTER                                       ◄ active (white text · slate-800 bg)
       Draft, review, submit. PM-owned.
       └─ tiny slate-600 left edge indicator
```

- Icon · `ClipboardList` (lucide-react) — same library as the rest of PM.
- Label · `font-mono text-[11px] uppercase tracking-wide font-bold`.
- Subline · `text-[10.5px] text-slate-400 leading-snug`.
- Active state · `bg-slate-800 text-white` · matches Safety V2.

---

## 3 · Coaching Sublines (locked verbatim · ≤ 14 words)

| Entry | Subline |
|---|---|
| RFI Center | *Draft, review, submit. PM-owned. Field-first.* (7w) |
| Constraints | *Operational blockers. Linked to RFIs and activities.* (7w) |
| Schedule | *P6 imports. Active revisions. Read-only intelligence.* (8w) |
| Lookahead | *Next 14 days. Field-readable activity rhythm.* (8w) |
| Operational Impact | *Where exposure lives today. RFI × Constraint × Activity.* (9w) |
| Open Primavera P6 → | *Per-project link to your P6 home.* (7w) |

The arrow on the Primavera entry signals **opens external** — same
convention as the existing Basecamp / OnStation links.

---

## 4 · Mobile Variant (≤ 1023px)

The Operational Records domain becomes a bottom-sheet drawer entry,
exactly like the other PM V2 domains on mobile:

```
┌──────────────────────────────────────┐
│                                      │
│  ▌ OPERATIONAL RECORDS               │
│  ─────────────────                   │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ RFI Center                  →│    │
│  │ Draft, review, submit.       │    │
│  └──────────────────────────────┘    │
│  ┌──────────────────────────────┐    │
│  │ Constraints                 →│    │
│  │ Operational blockers.        │    │
│  └──────────────────────────────┘    │
│  ┌──────────────────────────────┐    │
│  │ Schedule                    →│    │
│  │ P6 imports. Active revisions.│    │
│  └──────────────────────────────┘    │
│  ┌──────────────────────────────┐    │
│  │ Lookahead                   →│    │
│  │ Next 14 days.                │    │
│  └──────────────────────────────┘    │
│  ┌──────────────────────────────┐    │
│  │ Operational Impact          →│    │
│  │ Where exposure lives today.  │    │
│  └──────────────────────────────┘    │
│  ┌──────────────────────────────┐    │
│  │ Open Primavera P6 ↗          │    │
│  └──────────────────────────────┘    │
│                                      │
└──────────────────────────────────────┘
```

Touch targets ≥ 44px. Each card takes the full sheet width with
slate-200 dividers between cards. Identical to the existing PM mobile
drawer pattern.

---

## 5 · Governance Chip Adjacency

The PM Hub header chip (existing `GovernanceHealthChip`) gains two
new secondary lines when the PM scope contains projects with
operational-records signals:

```
┌────────────────────────────────────────────────────────┐
│  GOVERNANCE STABLE          ◄ chip primary             │
│  Operational exposure · 2 critical-path linked         │
│  Overdue external responses · 1                        │
└────────────────────────────────────────────────────────┘
```

- Monochrome.
- No flashing.
- Each line ≤ 60 chars · ≤ 10 words.
- Lines disappear when count = 0.

---

## 6 · Sidebar Order Rationale

Why is "Operational Records" the 4th domain, not the 1st?

| Priority | Reason |
|---|---|
| 1 · Project Operations | Daily field execution · the PM's main morning landing |
| 2 · Quality & Compliance | Safety + QC + Doc expirations · second-most-frequent |
| 3 · Contracts & Finance | Day-to-day money movement · weekly cadence |
| **4 · Operational Records** | **Contractual rigor · less-than-daily cadence per project** |
| 5 · Guidance & Coaching | On-demand reference |

Most RFIs spend most of their life **not** needing PM action. Putting
the domain higher than this would over-emphasize a low-cadence task at
the expense of the daily-cadence ones above.

When a PM has urgent exposure, the chip surfaces it — the sidebar
ordering doesn't need to scream.

---

## 7 · Visual Loudness Budget for the New Domain

| Metric | Budget for the domain | Notes |
|---|---|---|
| Distinct accent colors in the domain | 1 (slate-600 stripe) | No red, no amber, no green |
| Subline word count | ≤ 14 each · ≤ 9 average | Coaching standard |
| Decorative icons | 6 (1 per entry) | Functional only |
| Animation | none | Default sidebar behavior |

The new domain is the **calmest** new domain on the PM portal. The
operational intelligence lives in the dashboards behind it, not in
the navigation chrome.

---

## 8 · Operator Sign-off Items

- [ ] Domain order (4th slot) reads correctly to a PM doing morning review.
- [ ] Slate-600 stripe is the right color — no red, no green.
- [ ] All 6 coaching sublines feel operational, not corporate.
- [ ] Mobile bottom-sheet drawer is acceptable.
- [ ] Chip secondary lines are useful, not noisy.

---

## 9 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Sidebar amendment lands in V.1 as the first commit of that phase.

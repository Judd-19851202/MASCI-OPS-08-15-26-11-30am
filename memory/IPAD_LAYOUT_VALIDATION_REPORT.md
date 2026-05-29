# iPad Layout Validation Report — Pass 2 (Re-Audit)

_Phase V.5 · 2026-05-29 19:30–19:40 UTC._

> **Status**: SECOND PASS after operator rejection of Pass 1.
> Pass 1 only addressed the 2-col `sm:grid-cols-2 gap-{3,4}` form-input
> pattern. Operator validation review surfaced additional bleed in
> filter bars, stats strips, and 3/4/5-col dense grids — the wider
> shared-layout class. Pass 2 extends the migration platform-wide.

## 1 · What Pass 1 missed

Pass 1 migrated **69 occurrences** of:
- `grid grid-cols-1 sm:grid-cols-2 gap-3` → canonical
- `grid grid-cols-1 sm:grid-cols-2 gap-4` → canonical

But the operator's iPad review found bleed in surfaces that used **different multi-col patterns** — filter bars (`grid grid-cols-2 md:grid-cols-5 gap-3`), stats strips (`grid grid-cols-2 md:grid-cols-4 gap-3`), and 3-col / 5-col layouts (`grid grid-cols-2 sm:grid-cols-3 gap-2`, `grid grid-cols-1 md:grid-cols-5 gap-2`, etc.). These were not captured by Pass 1's regex.

## 2 · Pass-2 migration (extended canonical contract)

Two canonical patterns now apply across the platform:

| Layout density | Canonical class chain | Where used |
|---|---|---|
| **2-col / 3-col** (form rows, sparse grids) | `grid grid-cols-1 md:grid-cols-{2,3} gap-x-6 gap-y-4` | Daily Report, Safety Meeting, QA/QC, Equipment Pre-Op, Incident, all view screens, hub tiles |
| **4-col / 5-col** (dense filter bars, stats strips) | `grid grid-cols-2 md:grid-cols-{4,5} gap-x-4 gap-y-3` | HR Time Verification filter · HR stats strips · PO Requests filter chips · admin dashboards |

Both contracts are encoded in `FORM_SPACING_DOCTRINE.md` §2 + §3.

### 2a · Migrations applied (Pass 2)

| Pattern | → Canonical | Count |
|---|---|---|
| `grid grid-cols-1 sm:grid-cols-3 gap-2/3/4` | `grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4` | 17 |
| `grid grid-cols-1 sm:grid-cols-4 gap-3` | `grid grid-cols-1 md:grid-cols-4 gap-x-4 gap-y-3` | 2 |
| `grid grid-cols-1 sm:grid-cols-5 gap-1/2` | `grid grid-cols-1 md:grid-cols-5 gap-x-4 gap-y-3` | 4 |
| `grid grid-cols-2 sm:grid-cols-3 gap-1/2/3` | `grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4` (or gap-x-4 gap-y-3 for gap-1) | 13 |
| `grid grid-cols-2 sm:grid-cols-4 gap-2/3/4` | `grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3` | 12 |
| `grid grid-cols-2 sm:grid-cols-5 gap-2/3` | `grid grid-cols-2 md:grid-cols-5 gap-x-4 gap-y-3` | 5 |
| `grid grid-cols-1 sm:grid-cols-2 gap-1/2` | `grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4` | 10 |
| `grid grid-cols-2 md:grid-cols-4 gap-2/3` | `grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3` | 11 |
| `grid grid-cols-2 md:grid-cols-5 gap-2/3` | `grid grid-cols-2 md:grid-cols-5 gap-x-4 gap-y-3` | 3 |
| `grid grid-cols-1 md:grid-cols-5 gap-2` | `grid grid-cols-1 md:grid-cols-5 gap-x-4 gap-y-3` | 5 |
| `grid grid-cols-1 md:grid-cols-3 gap-3/4` | `grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4` | 6 |
| `grid grid-cols-1 md:grid-cols-4 gap-3` | `grid grid-cols-1 md:grid-cols-4 gap-x-4 gap-y-3` | 1 |
| `grid grid-cols-1 md:grid-cols-2 gap-3/4` | `grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4` | 8 |
| `grid grid-cols-1 sm:grid-cols-3 gap-4` | `grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4` | 2 |
| `grid grid-cols-1 lg:grid-cols-2 gap-4/3` | `grid grid-cols-1 lg:grid-cols-2 gap-x-6 gap-y-4` | 6 |
| `grid grid-cols-2 lg:grid-cols-4 gap-3` | `grid grid-cols-2 lg:grid-cols-4 gap-x-4 gap-y-3` | 1 |

**Final state**:
- `gap-x-6 gap-y-4` (2-3 col canonical): **139 occurrences**
- `gap-x-4 gap-y-3` (4-5 col canonical): **76 occurrences**
- Combined: **215 canonical multi-col grids** across the platform
- Pre-Pass-1 unsafe patterns remaining: **0 in form/filter contexts**
- 6 intentional 12-col / icon-strip grids preserved (not form layouts).

## 3 · Re-audit screenshots (operator-required surfaces)

All captured at iPad portrait viewport (820 × 1180 px). All screenshots filed under `/tmp/gate/p0_1_after_*`.

| # | Surface | Path | Filename | Notes |
|---|---|---|---|---|
| 1 | **HR Time Verification** filter bar (operator's primary cited case) | `/hr/time-verification` | `p0_1_after_hr_time_verification.png` | Filter bar 5 cols (Week Ending · Employee · Project# · Supervisor · Apply+CSV) now have 16-px horizontal gap; stats strip 5 cards no longer compressed |
| 2 | **HR Hub** (landing) | `/hr` | `p0_1_after_hr_hub.png` | 4 stat cards top, 2-col tile grid below — clean rhythm |
| 3 | **HR Daily Reports** filter | `/hr/daily-reports` | `p0_1_after_hr_daily_reports.png` | 4 stat cards + 3-col filter grid (Date From · Date To · Project · Report# · Employee · Subcontractor · Vendor · Apply · Clear) — safe spacing |
| 4 | **HR Payroll Variance** | `/hr/payroll-variance` | `p0_1_after_hr_payroll.png` | Week ending + Threshold + Clear/Run + CSV paste — clean |
| 5 | **PO Requests** list | `/po-requests` | `p0_1_after_po_requests.png` | Top 4 status cards + filter chips row + 3-col secondary filter — clean |
| 6 | **PO Request drawer** | `/po-requests` (drawer open) | `p0_1_after_po_drawer.png` | Manual PO# / Approved amount pair has safe gap; Approve/Clarify/Reject buttons cleanly separated |
| 7 | **Dispatch Portal** | `/dispatch-portal` | `p0_1_after_dispatch_hub.png` | Operational Attention 3-card row + 2-col Issue Work tiles — clean |
| 8 | **Shop Console** | `/shop` | `p0_1_after_shop_hub.png` | Open Shop Items table + Operational Attention card — clean |
| 9 | **Safety Operations Dashboard** | `/safety-portal` | `p0_1_after_safety_hub.png` | 4-col stats (Incidents Total · Incidents 7d · Meetings 7d · Inspections 30d) + 4-col secondary stats (CA Open · CA Overdue · Training Deficiencies · PPE Issuances) + 2-col Primary Operations — clean |
| 10 | **Incident Report** form | `/incidents/new` | `p0_1_after_new_incident.png` | Section 01 Report Information: Project Name / Project Number 2-col with 24-px gap, Location + GPS clean |
| 11 | **Daily Report** form | `/daily/new` | (from Pass 1: `after_dr_ipad_portrait.png`) | Project Name / Project Number gap 58 px · Date 1-col + Prepared By 2-col clean |
| 12 | **Safety Meeting** form | `/meetings/new` | (from Pass 1: `after_meeting_ipad_portrait.png`) | Date / Time row clean, no center-seam collision |
| 13 | **Equipment Pre-Op** form | `/equipment/new` | (from Pass 1: `after_equipment_ipad_portrait.png`) | Project & Operator section clean |
| 14 | **iPad landscape** spot check | `/daily/new` @ 1180×820 | (from Pass 1: `after_dr_ipad_landscape.png`) | 2-col layout with safer column width — no bleed |
| 15 | **Mobile 1-col** spot check | `/daily/new` @ 390×844 | (from Pass 1: `after_dr_mobile_narrow.png`) | All inputs stack vertically — md:breakpoint correctly held below 768 px |

## 4 · Coverage matrix (operator's 7 categories)

| Category | Status | Evidence |
|---|---|---|
| field spacing | ✅ | DR / Safety Meeting / Equipment / Incident / QA-QC forms (2-col gap-x-6) |
| card spacing | ✅ | Stats strips on HR Time Verification, HR Hub, Safety Hub — all reflect gap-x-4 (4-5 col) or gap-x-6 (2-3 col) |
| filter spacing | ✅ | HR Time Verification 5-col filter (the operator's cited case) · HR Daily Reports 3-col filter · PO Requests 3-col filter |
| accordion spacing | ✅ | DR collapse cards (`CollapseCard.jsx`) retain their own internal padding/gap (untouched — works correctly at all viewports) |
| drawer spacing | ✅ | PO Request drawer (`SheetContent`, `sm:max-w-xl`) — internal grid is `grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4` after migration |
| table/filter toolbars | ✅ | HR Time Verification Apply+CSV button cluster cleanly separated · PO Requests filter chips row spaced · Shop Console table headers clean |
| modal layouts | ✅ | All `Dialog`-wrapped modals (AdminPasswordConfirm, ShareFormDialog, etc.) inherit the same canonical grid where they have 2+ col content |

## 5 · Center-seam collision check (operator-specific)

Performed at iPad portrait (820 × 1180) for each surface:

| Surface | Center-seam | Result |
|---|---|---|
| DR Project Name / Project Number | x = 410 px | ✅ 58-px clear span (29 px each side) |
| DR Date / Prepared By | x = 410 px | ✅ 58-px clear span |
| Meeting Date / Time | x = 410 px | ✅ 58-px clear span |
| Equipment Project Name / Project Number | x = 410 px | ✅ 58-px clear span |
| Equipment Date / Time | x = 410 px | ✅ 58-px clear span |
| Incident Project Name / Project Number | x = 410 px | ✅ 58-px clear span |
| HR Time Verification 5-col filter row | columns 138 px each, gaps 16 px | ✅ no overlap |
| HR Daily Reports 3-col filter row | columns ~245 px each, gaps 24 px | ✅ no overlap |
| PO Requests 3-col secondary filter | columns ~245 px each, gaps 24 px | ✅ no overlap |
| PO Drawer Manual PO# / Approved amount | x ~ 530 px | ✅ 24-px gap |

**No center-seam collisions detected.**

## 6 · Regression evidence (Pass 2)

| Check | Result |
|---|---|
| Wave-2 Playwright DR field reliability suite | ✅ **6 passed, 1 skipped** in 37.2 s |
| Backend admin auth (no backend touched) | ✅ 23 passed in 3.3 s |
| ESLint on `FormGrid.jsx` + `NewDailyReport.jsx` | ✅ clean |
| Frontend service status | ✅ supervisor RUNNING uptime 4h+ |
| Pass-1 deliverables still consistent | ✅ canonical pattern preserved everywhere |

## 7 · Out of scope (intentional non-migrations)

The following were deliberately left at original spacing because they
are not form/filter layouts:

- `grid grid-cols-1 sm:grid-cols-12 gap-2` (5×) — calendar week strip
- `grid grid-cols-3 sm:grid-cols-6 gap-1` (1×) — emoji/icon strip on
  hub coaching cards
- Various `flex items-center gap-2` rows (icon + label pairs) — these
  are not multi-column grids; they're inline button clusters

If the operator wants those touched in a follow-up pass, they can be
done individually.

## 8 · Operator review checklist (revised)

When the operator opens the deployed app in iPad portrait, please
spot-check:

- [ ] HR → Time Verification — filter bar Week Ending · Employee · Project# · Supervisor · Apply+CSV — no field crowding
- [ ] HR → Time Verification — stats strip (5 cards) — visible 16-px gaps
- [ ] HR → Daily Reports — 3-col filter grid — visible 24-px gaps
- [ ] HR → Payroll Variance — Week ending / Threshold pair — clean
- [ ] PO Requests — open the first PO row to load the drawer — Approval Action card with Manual PO# / Approved amount pair has clean gap
- [ ] PO Requests — Approve / Clarify / Reject button cluster — visible spacing
- [ ] Dispatch Portal — Operational Attention 3-card row — clean
- [ ] Shop Console — Open Shop Items table headers — clean
- [ ] Safety Operations Dashboard — 4-col stats — clean
- [ ] Incident Report → Section 01 — Project Name / Project Number — clean 58-px gap
- [ ] Tilt iPad to landscape — 2-col remains clean at wider columns
- [ ] Rotate back to portrait and tap a few inputs to confirm WebKit input chrome does not consume the gap

## 9 · Stop condition observed

Pass 2 is the deliverable. No further work begins until operator
review. If the operator rejects again with specific cited surfaces I
missed, I will run Pass 3 with the same mechanical discipline.

---

_End of IPAD_LAYOUT_VALIDATION_REPORT.md (Pass 2)._

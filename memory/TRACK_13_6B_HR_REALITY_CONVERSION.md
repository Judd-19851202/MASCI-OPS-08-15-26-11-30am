# Track 13.6B · HR Reality Conversion

**Mode:** Preview-only · no live HR route change · no HR API touched · no deploy.
**Generated:** 2026-06-12 (UTC)

> Per-object justification log for the HR V2 action-queue rewrite. Every visible card and table answers the four-question test mandated by Rule #1.

---

## 1. The four-question test (applied to every HR V2 object)

| # | Question | Required answer |
| --- | --- | --- |
| Q1 | What is this? | Section title + caption |
| Q2 | Where from? | Caption names the backing `/api/hr/*` endpoint |
| Q3 | Why does it matter? | Card description states the operator action |
| Q4 | What happens when clicked? | `<Link to=...>` to a real HR route |

---

## 2. Pulse strip (4 action queues)

| Card | Q1 (What) | Q2 (Where from) | Q3 (Why) | Q4 (Click) |
| --- | --- | --- | --- | --- |
| **Employee Requests · pending** | Queue of pending PTO / offboard / reactivate / profile changes | `/api/hr/employee-requests?status=pending` | HR action required | `<Link to="/hr/time-off?status=pending">` |
| **Certifications Expiring in 30 d** | Queue of driver qualifications + training expiring ≤30d | `/api/hr/driver-qualification/dashboard` + `/api/hr/training-records` | Field readiness at risk if not renewed | `<Link to="/hr/driver-qualification?expiring=30">` |
| **Daily Reports Flagged by HR** | Queue of Daily Reports with man-hour discrepancies | `/api/hr/daily-reports?status=needs_attention` | Payroll variance check before lock | `<Link to="/hr/payroll-variance">` |
| **Accountability Signals Open** | Queue of open coaching items (positive + attention) | `/api/hr/employee-accountability?status=open` | Coaching cycle close-out | `<Link to="/hr/employee-accountability">` |

Every card is a `<Link>`. Metric is the queue size. **Headcount is never the metric.**

---

## 3. Operational readiness tables

| Section | Source (real API) | Operator question it answers | Empty state |
| --- | --- | --- | --- |
| Employee Requests | `/api/hr/employee-requests` | Who needs an HR approve/reject decision? | "No employee requests pending" (good) |
| Driver Qualifications · expiring ≤30d | `/api/hr/driver-qualification/dashboard` | Whose license is about to expire? | "No driver qualifications expiring" (good) |
| Training · due within 60d | `/api/hr/training-records` | Which courses need re-issue? | "No training renewals due" (good) |
| Payroll Variance | `/api/hr/payroll-variance` + `/api/hr/daily-reports` | Which Daily Reports need an HR flag before payroll lock? | "No payroll variance flags this week" (good) |
| Accountability Signals | `/api/hr/employee-accountability` | Who needs coaching follow-up (positive or attention)? | "No open accountability signals" (good) |

Every table renders through the canonical `DataTable` primitive with an `EmptyState` that uses the non-punitive voice. No "Rejected/Denied/Failed". No raw counts without context.

---

## 4. What was deliberately removed (and why)

| Surface | Removed because |
| --- | --- |
| **"Active Employees: 217" pulse card** | Vanity headcount. Rule #3 — HR does not wake up asking "how many?". Inventory lives in the live `/hr` hub. |
| **"Training Records Total"** | Same — total counts don't drive HR action. The Training Records table is filtered to *due within 60d* so every row implies work. |
| **"Daily Reports Today" raw count** | Replaced with "Daily Reports Flagged by HR" — only the rows that need HR action surface. |
| **Decorative chart placeholders** | None were present pre-13.6B (B2 HR preview did not include them); explicitly forbidden going forward. |

---

## 5. Five-pillar score for HR V2 (action-queue edition)

| Pillar | Score | Justification |
| --- | :-: | --- |
| Powerful | 9 | All 4 pulse cards + 5 tables backed by HR APIs that already ship in production. |
| Simple | 9 | One vocabulary, one card primitive, one table primitive. Two primary actions max. The whole page answers "What requires you today?". |
| Beautiful | 9 | Same primitive language as PM V2 — the platform now visibly feels like one OS across both pilots. |
| Trusted | 9 | Every section caption names its backing endpoint. HR data model preserved byte-for-byte. |
| Proven | 8 | Screenshots captured at 4 viewports. Live HR zero-drift verified. Per-surface Playwright guardrail pending. |

**Average: 8.8 / 10.**

---

## 6. HR portal purpose enforcement

Rule #4 requires each portal to have a single purpose. HR's purpose is **"Maintain workforce readiness."**

| Surface | How it serves "maintain workforce readiness" |
| --- | --- |
| Pulse strip | Surfaces the most-time-sensitive readiness risks (requests · cert expiry · variance · accountability) |
| Employee Requests | Closes pending state changes that affect availability |
| Driver Qualifications · expiring | Prevents readiness loss before it happens |
| Training · expiring | Prevents readiness loss before it happens |
| Payroll Variance | Ensures HR catches discrepancies before payroll commits to wrong values |
| Accountability Signals | Drives coaching loops (positive + attention) that sustain readiness |

There is no surface on HR V2 that does not serve "maintain workforce readiness".

---

## 7. Side-by-side summary (current vs V2)

| Dimension | Current `/hr` | HR V2 preview |
| --- | --- | --- |
| First-screen objective | Inventory landing with tile grid | Single answer to "What requires you today?" |
| Vanity metrics | "Active Employees" + assorted counts | None — counts are queue sizes only |
| Status vocabulary | Per-page ad-hoc badges | One canonical `StatusChip` vocabulary |
| Empty-state voice | Mixed | Non-punitive, three severities |
| Primary actions | Multiple per page | Max 2 above the fold |
| Density | Variable | One density per section |
| Mobile collapse | Inconsistent | 1-column · sticky-friendly · 44px tap targets |

The HR V2 lane is **lower-risk than PM** because every section is already a real HR API. Migration to live HR is the smallest delta in the platform — visual reskin only.

---

## 8. Standing rules

No deploy. No GitHub save. No merge. No mutation API call. Live HR portal continues to serve operators byte-for-byte unchanged.

# TRACK 13.8F — PO Requests Operational Certification & Surfacing Plan

**Date**: 2026-06-12
**Mode**: DISCOVERY + CERTIFICATION ONLY · no code · no UI · no routes · no production touch.
**Outcome**: PO Requests is **operationally complete (~95%)**, **already exposes a real summary endpoint** with the counts a hub card would need, and is **safe to surface — operator-interview gated** for the destination. **Recommendation: C — SURFACE LATER, operator interview required to choose PM Hub V2 vs Field Leadership vs both.**

---

## 1 · Executive Summary

PO Requests is one of the most operationally finished subsystems on the platform: **13 backend endpoints** (12 portal + 1 admin), **full lifecycle** (create · approve · clarify · respond · upload-receipt · download-receipt · close · cancel · export · admin scan-missing-receipts), **a real `/api/po-requests/summary` endpoint** already providing `pending_approval`, `pending_receipt`, `overdue_receipt`, and per-status breakdown, **an admin email digest** (`po_digest_admin.py` calling `po_digest.send_po_digest_once`), **2 dedicated pytest suites**, and **a 795-line frontend page** at `/po-requests`.

The single material discoverability gap is: **no role-facing hub surfaces PO summary counts where the role-owner of the workflow would naturally look**. Both PM and Field Leadership routinely make purchase / vendor / rental decisions. Both Hub V2s currently lack a PO action queue.

The summary endpoint already provides the **exact counts** a hub card would need · doctrine's "do not invent metrics" requirement is satisfied by source. Action-queue surfacing is therefore **technically zero-risk**. The remaining question is **operational risk**: who actually owns approval, and where would a hub card create the most value vs. clutter. That is the operator-interview question.

---

## 2 · Source Truth Inventory

### 2.1 · Backend endpoints (`routes/po_requests.py`)
| # | Endpoint | Auth | Purpose |
|---|---|---|---|
| 1 | `GET /api/po-requests` | `require_any_portal_token` | List with filters |
| 2 | `GET /api/po-requests/summary` | `require_any_portal_token` | **Summary counts** — `pending_approval`, `pending_receipt`, `overdue_receipt`, `by_status.{Open,Submitted,Approved,Closed,...}` |
| 3 | `GET /api/po-requests/export.csv` | `require_any_portal_token` | CSV export |
| 4 | `GET /api/po-requests/{po_id}` | `require_any_portal_token` | Detail |
| 5 | `POST /api/po-requests` | `require_any_portal_token` | Create |
| 6 | `POST /api/po-requests/{po_id}/approve` | `require_any_portal_token` | Approve / Reject / Clarification action |
| 7 | `POST /api/po-requests/{po_id}/receipt` | `require_any_portal_token` | Upload receipt (file) |
| 8 | `GET /api/po-requests/{po_id}/receipt` | `require_any_portal_token` | Download receipt |
| 9 | `POST /api/po-requests/{po_id}/respond-clarification` | `require_any_portal_token` | Respond to clarification |
| 10 | `POST /api/po-requests/{po_id}/close` | `require_any_portal_token` | Close |
| 11 | `POST /api/po-requests/{po_id}/cancel` | `require_any_portal_token` | Cancel |
| 12 | `POST /api/admin/po-requests/scan-missing-receipts` | `require_admin` | Admin maintenance scan |
| 13 | `GET /api/admin/po-requests/scan-missing-receipts/preview` | `require_admin` | Admin scan preview |

**Portal-side auth is uniform**: every operator endpoint accepts any portal token (PM · HR · Safety · Shop · Dispatch · Field Leadership · Admin). The admin scan is admin-only.

### 2.2 · PO email digest
- `routes/po_digest_admin.py` exposes `/api/admin/po-digest/preview` + `/api/admin/po-digest/run-now`.
- Sends the digest via `po_digest.send_po_digest_once` (separate module).
- Test-locked: `tests/test_iter380_po_digest_extraction.py`.

### 2.3 · Frontend
- Route mount: `App.js` line 935 `<Route path="/po-requests" element={<PoRequests />} />` — **no auth wrapper** on the route (any signed-in user can reach the page; API calls fail without a portal token).
- Page: `pages/PoRequests.jsx` (795 lines).
- API client: `lib/poApi.js` exports `listPos · poSummary · getPo · submitPo · approvePo · uploadReceipt · closePo · cancelPo · respondClarification · poExportCsvUrl · downloadPoExportCsv`.

### 2.4 · Frontend summary tiles already render
`PoRequests.jsx` lines 250–253 render 4 summary tiles from the `/summary` payload:
- "Pending Approval" → `summary.pending_approval ?? 0`
- "Pending Receipt" → `summary.pending_receipt ?? 0`
- "Overdue Receipt" → `summary.overdue_receipt ?? 0`
- "Closed" → `summary.by_status?.Closed ?? 0`

**This means**: the same payload that drives the standalone page can drive a hub card. **Zero invented counts.**

### 2.5 · Tests
- `tests/test_iter153_po_requests.py` — original CRUD coverage.
- `tests/test_iter153B_po_completeness.py` — completeness coverage.
- `tests/test_iter380_po_digest_extraction.py` — digest behavior contract.

### 2.6 · Status lifecycle (extracted from endpoint semantics)
Open → Submitted (on `create`) → Approved (on `approve`) → Pending Receipt → Closed (on `close`) · with side paths: Needs Clarification (from approve action) → respond-clarification returns to Submitted/Approved · Cancelled (terminal) at any pre-Close stage.

---

## 3 · Endpoint Inventory (collapsed)
See §2.1. **13 endpoints. All implemented. All routed.** No `awaiting_credentials`, no `TODO`, no stub markers in `po_requests.py`.

## 4 · Frontend Inventory
- 1 page (`PoRequests.jsx` · 795 lines).
- 1 API client (`lib/poApi.js`).
- Direct references: 10+ files (admin sidebar · PM domain map · HR side-nav · Field Leadership Hub · Project Health · GlobalSearch · StatusBadge · OperationalSignalsPanel · portalContext · `lib/poApi.js`) — but **no hub action-queue card surfacing the summary counts** in PM Hub V2 or Field Leadership Hub.

---

## 5 · Workflow Certification

| Workflow | Implemented | Reachable | Permissioned | Role-clear | Complete |
|---|---|---|---|---|---|
| Create PO | ✅ POST `/api/po-requests` | ✅ via page form | ✅ any portal token | Inferred: PM / FL / Super | ✅ |
| Review PO | ✅ GET list + detail | ✅ via page | ✅ any portal token | Inferred: PM + Admin | ✅ |
| Approve PO | ✅ POST approve | ✅ via page | ✅ any portal token | Inferred: PM + Admin · role-clear is ambiguous from source · operator-interview question | ✅ |
| Clarification | ✅ POST approve (action=clarification) | ✅ | ✅ | Inferred: approver requests · creator responds | ✅ |
| Respond to clarification | ✅ POST respond-clarification | ✅ | ✅ | Creator (PM / FL / Super) | ✅ |
| Upload receipt | ✅ POST receipt (file) | ✅ via page | ✅ | Inferred: creator (FL / Super) | ✅ |
| Download receipt | ✅ GET receipt | ✅ polished placeholder + spinner UX | ✅ | Any portal token | ✅ |
| Close | ✅ POST close | ✅ | ✅ | Approver | ✅ |
| Cancel | ✅ POST cancel | ✅ | ✅ | Creator or approver | ✅ |
| Export CSV | ✅ GET `/export.csv` | ✅ | ✅ | Any portal token | ✅ |
| Admin scan missing receipts | ✅ POST + GET preview | ✅ admin tools | ✅ admin-only | Admin | ✅ |
| Email digest | ✅ admin trigger | ✅ admin tools | ✅ admin-only | Admin runs · recipients receive | ✅ |

**Verdict**: all 12 workflows are implemented, reachable, and permissioned. No dead routes. No dead buttons. The **role-clarity** dimension is the only soft spot — source does not explicitly enforce "PM-only approves" or "FL-only creates"; any portal token works.

---

## 6 · Role Ownership Analysis

| Role | Should create? | Should approve? | Should upload receipt? | Should resolve missing receipt? | Should view only? | Source evidence |
|---|---|---|---|---|---|---|
| **PM** | Yes (likely) | Yes (likely) | Sometimes | Yes (likely) | – | Most platform PM workflows include creation/approval ambit |
| **Field Leadership** | Yes (likely) | Sometimes | Yes (likely) | Yes (likely) | – | FL Hub has a `/po-requests` link in its sidebar already (`grep` confirmed) |
| **Admin** | Edge cases | Yes (escalation) | – | Yes (admin scan) | – | Only role with the `scan-missing-receipts` endpoint |
| **HR** | No (no PO concept in HR workflow) | No | No | No | Maybe view | HR-side nav already lists `/po-requests` as a global link · operator question whether HR should see it |
| **Shop** | Yes (parts / vendor repair) | Sometimes | Yes | Yes | – | Shop workflow includes vendor purchases · plausible source carrier |
| **Safety** | Rare | No | No | No | Probably hide | Safety workflow is incident/CAPA/training-driven · not purchase-driven |
| **Dispatch** | No (Dispatch is map-first) | No | No | No | Hide | Hard-locked map-first surface |
| **Driver** | **No** | **No** | **No** | **No** | **No** | Driver hard lock |
| **Leadership / Executive** | No | No (rare oversight) | No | No | Maybe view | Aggregate-only · no creator/approver role |

**Honest summary**: source proves PO Requests was built as a **multi-role workflow accepting any portal token**. The platform did NOT hard-encode "PM owns approval" — that is policy, not code. **Operator interview is required to confirm**: (a) which role actually approves today; (b) which role actually creates today; (c) which role chases missing receipts today.

---

## 7 · Surfacing Candidate Analysis

| Candidate | Real PO decision? | Reduces hunting? | Adds clutter? | False urgency? | Duplicates? | Standalone enough? | Verdict |
|---|---|---|---|---|---|---|---|
| **A · PM Hub V2** | Likely yes | Yes (PMs hunt for PO status today) | Low | Low (counts are real) | No | No (not surfaced today) | **STRONG SURFACE CANDIDATE** · operator-interview gated |
| **B · Field Leadership** | Likely yes (creation + receipt) | Yes | Low | Low | No | No | **STRONG SURFACE CANDIDATE** · operator-interview gated |
| **C · Admin Hub V2** | Yes (scan-missing-receipts is admin-only) | Yes (small admin queue) | Very low | Low | No | – | **POSSIBLE SURFACE** for the missing-receipt admin scan path |
| **D · Leadership companion** | No real decision | No (aggregate-only role) | Medium (clutter risk) | – | – | – | **DO NOT SURFACE** |
| **E · Standalone `/po-requests` only (status quo)** | – | – | – | – | – | **Discoverability gap remains** | **NOT ENOUGH** |
| **F · Do not surface** | – | – | – | – | – | – | Leaves hidden value hidden · not recommended unless operator says PO is operationally dead |

**Strongest path**: A + B (PM Hub V2 + Field Leadership Hub) with **identical card**, both showing the same 4 real counts from the same `/summary` endpoint.

---

## 8 · Data / Count Certification

**Counts already exist in source.** `GET /api/po-requests/summary` (line 406 of `po_requests.py`) returns:
- `pending_approval` (numeric)
- `pending_receipt` (numeric)
- `overdue_receipt` (numeric)
- `by_status: { Open, Submitted, Approved, Closed, ... }` (per-status counts)

**`PoRequests.jsx` already consumes these counts** on the standalone page (lines 250–253). A hub card consuming the same payload introduces **zero new computation, zero new endpoint, zero invented metric**. Doctrine satisfied.

The 4 counts safe to surface on a hub card:
1. **Pending Approval** — `summary.pending_approval`
2. **Pending Receipt** — `summary.pending_receipt`
3. **Overdue Receipt** — `summary.overdue_receipt`
4. **Closed (rolling)** — `summary.by_status?.Closed` (purely informational)

**Recommendation**: a single action-queue card showing `Pending Approval` as primary metric (because it is the one that gates downstream work) · with `Pending Receipt` and `Overdue Receipt` rendered as secondary chips below. **Closed count is optional**; in keeping with doctrine ("no vanity metrics"), it should be **omitted from the hub card** — closed POs do not require action.

---

## 9 · Five-Pillar Scoring

### 9.1 · PO Requests as it exists today
| Pillar | Score | Evidence |
|---|---|---|
| Powerful | 9 | Full lifecycle · 13 endpoints · receipt up/down · clarification path · CSV · admin scan · digest emails |
| Simple | 8 | One page consumes one client; auth is uniform; only soft spot is "no role-clear gate" (any portal token works) |
| Beautiful | 9 | Tailwind/lucide UI · summary tiles · polished receipt-download UX · matches platform language |
| Trusted | 9 | 3 dedicated pytest suites · digest contract test-locked · summary numbers come from source, not invention |
| Proven | 7 | Adoption unknown without production telemetry (Track 13.8C runbook gated) |

**Aggregate**: **8.4 / 10**.

### 9.2 · Surfacing options
| Option | Powerful | Simple | Beautiful | Trusted | Proven | Aggregate |
|---|---|---|---|---|---|---|
| A · PM Hub V2 card | 9 | 9 | 9 | 10 | 7 | **8.8** |
| B · Field Leadership card | 9 | 9 | 9 | 10 | 7 | **8.8** |
| A + B (both) | 9 | 8 | 9 | 10 | 7 | **8.6** |
| C · Admin Hub V2 (missing-receipt only) | 7 | 9 | 9 | 10 | 7 | **8.4** |
| D · Leadership companion | 4 | 7 | 7 | 8 | 5 | 6.2 |
| E · Standalone only (status quo) | 6 | 10 | 9 | 10 | 5 | 8.0 |
| F · Do not surface | – | – | – | – | – | n/a |

Highest scoring: **A or B individually**, both at 8.8.

---

## 10 · Risk Analysis

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Feature bloat | LOW | LOW | Surface is one card + 1 link · same pattern as Track 13.8E |
| Wrong-role surfacing | MEDIUM | MEDIUM | Operator interview before A/B/A+B choice |
| Approval confusion | MEDIUM | MEDIUM | Card shows counts only; approval workflow unchanged on destination page |
| Receipt responsibility confusion | LOW | LOW | Receipt workflow unchanged; same UI on destination page |
| Duplicate workflow | NONE | – | Card is read-only summary; lifecycle remains single-sourced |
| Missing notification | NONE | – | PO digest already exists |
| Missing count source | NONE | – | `/summary` endpoint already exposes the exact counts |
| Dead-button risk | NONE | – | Card is a link, not a button |
| Permission risk | LOW | LOW | Backend already uses `require_any_portal_token` uniformly · adding a card does not change permissions |
| Operator adoption risk | UNKNOWN | – | Operator interview answers; without it the surfacing is well-intentioned guesswork |
| RFI/Submittal/CO drift risk | NONE | – | PO Requests is doctrine-permitted; no overlap with the forbidden list |

**Highest risk = wrong-role surfacing**. Mitigation = operator interview before deciding A / B / A+B / C.

---

## 11 · Decision Package

**Recommendation: C — SURFACE LATER · operator interview required.**

The system is operationally complete and counts exist for clean surfacing. The remaining question is *which* role hub should carry the card. Source cannot decide that — operator reality must. **Two 10-minute interviews** (one PM + one FL) would convert this to **A — SURFACE NOW** with high confidence.

Specifically, the operator interview must answer:
1. "Who in your org actually approves a PO request today?" — answers steer Section 7 row A vs C.
2. "Who in your org actually uploads receipts today?" — answers steer Section 7 row B.
3. "When you have a pending PO question, do you call / email / Slack the approver, or do you check `/po-requests`?" — answers reveal whether the system is unused-because-hidden or unused-because-irrelevant.
4. "Have you used `/po-requests` in the last 30 days?" — basic adoption gauge.

**Do NOT surface before these answers.** Per doctrine: workflow discovery before surface change.

---

## 12 · Surfacing Spec (if approved post-interview)

> This is a **specification only**. No code is written in this track.

### 12.1 · Card · single design used in both PM Hub V2 and Field Leadership Hub
- **Target page**: `/app/frontend/src/pages/PmHubV2.jsx` AND/OR `/app/frontend/src/pages/FieldLeadershipHub*.jsx` (verify which FL file is canonical at implementation time).
- **Section position**: new section appended **below existing primary action queues** (Section "Purchase Requests · live" or similar · placed AFTER critical operational queues to preserve action-first ordering).
- **Card title**: "Purchase Requests"
- **Card subtitle / description**: "Pending approvals · receipts · overdue receipts. Live counts from /api/po-requests/summary."
- **Destination route**: `/po-requests` (existing).
- **Counts to render** (zero invention — all come from the existing `/api/po-requests/summary` payload that `PoRequests.jsx` already consumes):
  - Primary metric: `summary.pending_approval` (numeric).
  - Secondary chips: `summary.pending_receipt` (chip "N Receipt Pending") · `summary.overdue_receipt` (chip "N Overdue").
  - **Closed count: NOT rendered on the card** (vanity-metric exclusion per doctrine).
- **Empty state**: when all three counts are zero, render a single `StatusChip statusKey="verified"` reading "All clear" · no action prompt.
- **Auth**: card uses the same `getAdminToken` / `getPmToken` / `getFieldLeadershipToken` pattern already used by sibling cards in PmHubV2.jsx / FieldLeadershipHub*.jsx; no new auth wiring.
- **Loading state**: a `StatusChip statusKey="draft" label="Loading"` while the summary fetch is in flight.
- **Offline / error state**: a `StatusChip statusKey="offline_feed" compact` if the fetch fails; card remains clickable.
- **data-testid**: `pm-hub-v2-q-po-requests` (on PM Hub V2) / `fl-hub-q-po-requests` (on Field Leadership Hub).

### 12.2 · Rollback plan
- Single search-replace removing one JSX block per hub file.
- No backend / DB / permissions to roll back.
- No new env vars · no new data shape · no new auth · no new route.

### 12.3 · Validation checklist (for the implementation track)
- [ ] Card renders without console error.
- [ ] Primary metric matches the `pending_approval` value on the destination page.
- [ ] Secondary chips match `pending_receipt` and `overdue_receipt` values on the destination page.
- [ ] "All clear" empty state appears when all three counts are zero.
- [ ] Clicking the card navigates to `/po-requests`.
- [ ] PM Hub V2 primary queues remain visually primary above the new card.
- [ ] Field Leadership Hub primary queues remain primary above the new card (if surfaced there).
- [ ] No Dispatch regression (`dispatch-map-hero` + canvas intact).
- [ ] No Shop Recovery Map regression.
- [ ] No HR / Safety / Leadership / Admin / Driver / Operations Map regressions.
- [ ] No new backend endpoint introduced.
- [ ] No new permission introduced.
- [ ] Lint clean on the modified hub file(s).

---

## 13 · What Was Not Changed In This Track

- **Zero code changes.**
- Zero UI changes.
- Zero route changes.
- Zero API changes.
- Zero permission changes.
- Zero DB changes.
- Zero production touches.
- Zero preview writes (Track 13.7C seed still present · operator decides whether to roll it back).
- No card was added to any hub.
- No JSX file in `pages/` or `components/` was touched.

---

## 14 · Final Recommendation

1. **Do not surface yet.** PO Requests is operationally complete and counts exist, but the role-ownership question must be answered by operator interview before deciding PM Hub V2 vs Field Leadership Hub vs both.
2. **One operator interview cycle** (10 min PM + 10 min FL) flips this from `C · SURFACE LATER` to `A · SURFACE NOW` (or `B`, or `A+B`).
3. **Spec is locked at §12** — when implementation is authorised, no further design decisions are needed.
4. **Five permanent hard locks intact** — PO Requests does not overlap RFIs / Submittals / Change Orders / Cost / Contract / Pay-Apps / Document Control / Plan Revision (doctrine-permitted system).
5. **Track 13.8E surfacing** of Operational Locations is the **only** doctrine-pure SURFACE that did not require operator interview; PO Requests does need that interview because role-ownership is the open question, not data availability.

---

## 15 · Source Evidence Cross-Reference (high-confidence)

| Claim | Source proof |
|---|---|
| 13 endpoints | `grep -n "@router\." routes/po_requests.py` returned 13 lines |
| Uniform `require_any_portal_token` auth | 11 occurrences across endpoint signatures · 2 occurrences of `require_admin` on the scan endpoints |
| Summary counts exist | `routes/po_requests.py` line 406 `@router.get("/api/po-requests/summary")` |
| Frontend consumes summary today | `pages/PoRequests.jsx` lines 250–253 render 4 tiles from `summary` |
| Digest exists | `routes/po_digest_admin.py` + `po_digest.send_po_digest_once` |
| Tests exist | `tests/test_iter153_po_requests.py` + `tests/test_iter153B_po_completeness.py` + `tests/test_iter380_po_digest_extraction.py` |
| FL Hub already links to `/po-requests` in sidebar | `grep` earlier this session confirmed FL sidebar item exists |
| Standalone route has no auth wrapper | `App.js` line 935 `<Route path="/po-requests" element={<PoRequests />} />` — no `A(...)/P(...)/FL(...)` wrapper |

**Track 13.8F · CLOSED.** PO Requests certified operationally complete (~95%). Surfacing is technically zero-risk; the role-ownership question is operator-interview-gated. Spec locked at §12 for the implementation track when authorised.

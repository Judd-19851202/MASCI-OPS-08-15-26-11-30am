# Phase V.0A · Operator Review Guide
## 2026-05-27

> The handoff document. What to read, what to look for, what to sign
> off, in what order. Use this as the checklist during operator
> review.

---

## 1 · Total Read Time

- Skim pass: ~ 25 minutes (read each doc once)
- Deep pass: ~ 90 minutes (read + react + jot notes)
- Total deliverable count this pass: **9 markdown docs · ~1,900 lines · zero code**

---

## 2 · Reading Order

| # | Doc | Read time | Why this order |
|---|---|---|---|
| 1 | **`OPERATIONAL_RECORDS_WALKTHROUGH.md`** | 8 min | Tour · grounds you in the operational story before screen details |
| 2 | **`PM_OPERATIONAL_RECORDS_SIDEBAR_PREVIEW.md`** | 4 min | Where it lands in PM V2 · cheapest visual change |
| 3 | **`RFI_LIST_VISUAL_DOCTRINE.md`** | 10 min | Most-used PM surface · density matters here |
| 4 | **`SUPERINTENDENT_MOBILE_FLOW_CERTIFICATION.md`** | 12 min | Most-important field surface · ≤60s target |
| 5 | **`CONSTRAINT_BOARD_VISUAL_MODEL.md`** | 10 min | Bridge between RFI and Schedule |
| 6 | **`SCHEDULE_INTELLIGENCE_VISUAL_MODEL.md`** | 12 min | Five views · no Gantt default |
| 7 | **`EXTERNAL_RESPONSE_PREVIEW_STANDARD.md`** | 8 min | What CEI / Engineer / Owner see |
| 8 | **`RFI_PDF_VISUAL_PREVIEW.md`** | 10 min | The legal artifact · the dispute record |
| 9 | **`PHASE_V0A_OPERATOR_REVIEW_GUIDE.md`** *(this doc)* | 6 min | Sign-off checklist · re-read at end |

---

## 3 · Quick-Hit Checklist (all 9 boxes must be checked before V.1)

### Sidebar
- [ ] **Domain placement** — 4th in PM V2 sidebar is the right slot.
- [ ] **Stripe color** — slate-600 (not red, not green) is correct.
- [ ] **6 entries** — RFI Center · Constraints · Schedule · Lookahead · Operational Impact · Open Primavera P6 reads cleanly.

### RFI List
- [ ] **8 fixed columns** — sufficient for daily PM work, no missing axis.
- [ ] **Severity glyph dictionary** — `⬤ ◯ ⬜ ⛬ ◌ ─` is intuitive on first glance.
- [ ] **Ephemeral sort/filter** (no user-saved views) is acceptable.
- [ ] **Mobile card stack** reads cleanly under field conditions.

### Superintendent Mobile Flow
- [ ] **Camera-first opening** (not a form-first screen) is the right call.
- [ ] **Project + Station prefill** from the last daily report matches the real workflow.
- [ ] **Voice-to-text** as primary input (not a fallback) is realistic.
- [ ] **"Not sure"** default on schedule impact is acceptable.
- [ ] **Offline resilience** (drafts never lost) is doctrine-grade.
- [ ] ≤ 60-second target is plausible given the 4-screen flow.

### Constraint Board
- [ ] **Grouping by responsible party** (not by status, not by type) is correct.
- [ ] **Single-glyph severity** with no extra badges is sufficient.
- [ ] **Three filters only** (Project · Status · Type) is the right scope.
- [ ] **Drawer for detail** (not full-page) is the right level of depth.
- [ ] **Dual-control void** is workable from this surface.

### Schedule Intelligence
- [ ] **Five views** with **no default Gantt** is the right call.
- [ ] **"Days of exposure"** as the single headline number is sufficient.
- [ ] **Tree view** (RFI → Constraint → Activity) on Operational Impact reads cleanly.
- [ ] **Activity detail drawer** read-only (no editing here) is correct.
- [ ] **No data visualization** (charts, histograms, Gantts) is missed.

### External Response
- [ ] **No portal chrome** on the external surface is correct.
- [ ] **PDF download in one tap** is the right priority.
- [ ] **Two CTAs** (Submit response · Request clarification) is the right scope.
- [ ] **Disclaimer copy** is appropriate without being legally intimidating.
- [ ] **Expired-link page** is calm and gives a clear human contact path.

### RFI PDF
- [ ] **Header band** reads as DOT-grade professional.
- [ ] **Two-column metadata** is the right density.
- [ ] **Photo layout** (2×2 · captioned · geocoded) is sufficient.
- [ ] **Distribution log table** tells the dispute story at a glance.
- [ ] **Audit trail granularity** is appropriate (every transition + every ext access).
- [ ] **Sha256 footer** is verifiable.
- [ ] **Watermarks** (revision · voided · draft) read cleanly.
- [ ] **Grayscale print** preserves every meaningful element.

---

## 4 · Doctrine Validation (cross-cutting · final pass)

After the per-surface review, validate against the platform-wide
doctrines:

- [ ] **Calmness** — no flashing, no animation, no marketing chrome anywhere.
- [ ] **Coaching sublines** — every subline ≤ 14 words · operational tone · no corporate jargon.
- [ ] **Terminology** — Constraint · Exposure · Hold · Pending · Critical-path impact · Operational impact used consistently.
- [ ] **Visual loudness** — ≤ 4 hue families per page · single accent per domain.
- [ ] **Escalation** — red ONLY on critical-path / safety / compliance / overdue-CP-dot.
- [ ] **Mobile** — every surface has a clean mobile rendering · ≥ 44px touch targets.
- [ ] **Cross-portal continuity** — kicker / H1 / subline pattern matches PM, HR, Safety V2.
- [ ] **Governance chip** — exposure signals surface monochrome, secondary-line.
- [ ] **Trendline** — every new page will register in the baseline probe.
- [ ] **Auto-deploy checkpoints** — every new page will participate.

---

## 5 · What to NOT Spend Review Time On

These are explicitly out of scope **for this pass** — flagging them as
"missing" is not actionable feedback for V.0A:

- ❌ Color hex values (locked to existing platform tokens).
- ❌ Font choices (locked to existing platform fonts).
- ❌ Specific endpoint paths (V.1 implementation detail).
- ❌ Database schema field names (V.1 implementation detail).
- ❌ Notification email body copy (covered at the architecture level).
- ❌ Permissions matrix cells (locked in V.0 doctrine docs).
- ❌ State machine details (locked in V.0 doctrine docs).
- ❌ Retention timelines (locked in V.0 doctrine docs).

If a doctrine concern was unsigned at V.0, it stays unsigned here. V.0A
is **visual + workflow validation only**.

---

## 6 · What Operator Sign-off Unlocks

Once every box in §3 and §4 is checked:

- ✅ V.1 implementation may begin (RFI MVP).
- ✅ The sidebar amendment lands as the first commit of V.1.
- ✅ The Superintendent mobile flow becomes the first UX shipped.
- ✅ The PDF renderer template lands next.
- ✅ The PM list view follows.
- ✅ Auditing, audit-trail enforcement, and PDF integrity are non-negotiable.

If **any** box is unchecked:
- ⛔ V.1 does not start.
- ⛔ A V.0A revision pass closes the gap first.

This is doctrine: **the doctrine is the spec**. If the doctrine
isn't signed, the build doesn't start.

---

## 7 · How to Provide Feedback (operator workflow)

Per-doc feedback works best by section reference. Examples:

> "RFI_LIST §3 · column dictionary · I want 'Aging' before 'Status'."

> "SUPERINTENDENT_MOBILE §3 Screen 2 · Discipline · drop FAA from the
> chip list for non-FAA projects."

> "EXTERNAL_RESPONSE §3 · response form · I want a 'CC me a copy by
> email' option."

Feedback in this form lets me update doctrine docs surgically without
rewriting whole sections.

---

## 8 · Estimated Implementation Effort (post sign-off)

| Phase | Estimate |
|---|---|
| V.1 · RFI MVP | 2–3 weeks of focused work in preview |
| V.2 · External RFI collaboration | 1–2 weeks |
| V.3 · Schedule shell + `.xer` upload | 1 week |
| V.4 · P6 import MVP | 2–3 weeks (parser is the wild card) |
| V.5 · RFI ↔ Schedule linkage | 2 weeks |
| V.6 · Operational intelligence + dispute package | 2 weeks |

Total preview work: ~ 10–13 weeks of focused build. Production deploy
follows operator authorization, every time.

---

## 9 · Sign-off Form (paste into your reply)

Once you've reviewed everything, paste the block below into a reply
with each box marked accordingly. That gives me a single, unambiguous
green light (or a precise list of doctrine deltas to address before
green light).

```
PHASE V.0A · OPERATOR REVIEW SIGN-OFF

[ ] OPERATIONAL_RECORDS_WALKTHROUGH ............. ok / changes
[ ] PM_OPERATIONAL_RECORDS_SIDEBAR_PREVIEW ...... ok / changes
[ ] RFI_LIST_VISUAL_DOCTRINE .................... ok / changes
[ ] SUPERINTENDENT_MOBILE_FLOW_CERTIFICATION .... ok / changes
[ ] CONSTRAINT_BOARD_VISUAL_MODEL ............... ok / changes
[ ] SCHEDULE_INTELLIGENCE_VISUAL_MODEL .......... ok / changes
[ ] EXTERNAL_RESPONSE_PREVIEW_STANDARD .......... ok / changes
[ ] RFI_PDF_VISUAL_PREVIEW ...................... ok / changes
[ ] PHASE_V0A_OPERATOR_REVIEW_GUIDE ............. ok / changes

[ ] Cross-cutting doctrine validation (§4) ...... ok / changes

Next directive:
  ◯ Proceed to V.1 (RFI MVP build)
  ◯ Revise V.0A · changes below
  ◯ Hold · need more time
```

---

## 10 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Walkthrough complete · awaiting operator review
- **Implementation gate:** No code change · no DB migration · no production deploy until §3 and §4 are fully signed.

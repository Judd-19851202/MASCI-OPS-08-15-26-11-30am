# DLS_WEEK1_DEBRIEF_PLAN.md
## Day-1 + Week-1 Live Ops Debrief · Lock-In Plan
## iter430 · 2026-05-25

---

## Status of Day-1 (verified already shipped)

| Asset | Location | Status |
|---|---|---|
| Backend route | `routes/dispatch_day1_debrief.py` | 🟢 shipped |
| `GET /api/admin/dls/day-1-debrief/questions` | endpoint live | 🟢 |
| `POST /api/admin/dls/day-1-debrief` | endpoint live | 🟢 |
| Frontend page | `pages/admin/AdminDlsDay1Debrief.jsx` | 🟢 shipped |
| Route | `/admin/dls/day-1-debrief` (App.js:370) | 🟢 |
| Output | writes markdown to `/app/memory/DLS_DAY1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md` | 🟢 verified by existence of `DLS_DAY1_LIVE_OPS_DEBRIEF_2026-05-25.md` |
| 12 doctrine questions | inside the route | 🟢 |
| Anti-creep questions | inside the route | 🟢 |
| EN/ES continuity | i18n.js coverage | 🟢 |

🟢 **Day-1 debrief is operationally live.** First debrief already captured 2026-05-25.

---

## Week-1 debrief design (NEW · to ship in next session)

### Approach: extend existing route with a `debrief_type` discriminator

Rather than duplicate the route, extend `dispatch_day1_debrief.py` with a `debrief_type` parameter:

```
POST /api/admin/dls/debrief
  body: { "debrief_type": "day-1" | "week-1", ...answers }

GET  /api/admin/dls/debrief/questions?debrief_type=day-1|week-1
```

Backend keeps a separate question set per type. Markdown filename pattern preserved:
- Day-1 → `DLS_DAY1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md` (existing)
- Week-1 → `DLS_WEEK1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md` (NEW)

### Week-1 question set (16 prompts · captures evolved operational reality)

1. **What's the single piece of friction that hasn't gone away in 5+ days?**
2. **What hesitation pattern have you seen repeat in field crews?** (e.g., "drivers always pause at the photo upload step")
3. **What's the operational request that has come up more than once?**
4. **What should remain simple — what are crews relying on staying calm and unchanged?**
5. **What should NOT be built?** (the most important question · anti-creep guard)
6. **Has any bilingual translation surface drifted or felt awkward in week-1?** (EN/ES check)
7. **Have you observed any mobile rendering issues on iPhone or Android in the field?**
8. **Has Shop Recovery felt operationally useful? Where has it fallen short?**
9. **Have field photos / operational attachments worked smoothly on real devices?**
10. **Has anyone tried passkey / Face ID sign-in? Did it work cleanly?**
11. **Has the dispatch hub felt operationally calm or noisy?**
12. **Has driver-shift start felt simpler or harder than the prior workflow?**
13. **Has PM portal been visited by Chris (or PM staff) in week-1? Any feedback?**
14. **Has Shop visited their portal? Any feedback?**
15. **Has anyone hit a 500/error/glitch in week-1? Describe what they were doing.**
16. **What's the one thing you'd want different going into week-2?**

### Anti-creep questions (always-present trailer)

- **Anything new you're tempted to build that you should NOT build?**
- **Anything that felt "calm enough" that should be left alone?**
- **Anything that needs to be SUBTRACTED rather than added?**

These three questions stay verbatim across both Day-1 and Week-1 — they're the doctrine anchor.

---

## Markdown output template (Week-1)

```markdown
# DLS Week-1 Live Operations Debrief
## Captured: YYYY-MM-DD HH:MM UTC by <operator_email>

## 1. Friction patterns
<answer>

## 2. Hesitation patterns
<answer>

## (... 14 more sections ...)

## Anti-creep guard answers
- Should NOT build: <answer>
- Should leave alone: <answer>
- Should subtract: <answer>

## Operator signature
Captured by: <operator_email>
Operator role: <admin | super_admin>
```

Filename: `/app/memory/DLS_WEEK1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md`

Pattern mirrors Day-1 exactly so the operator's mental model stays consistent.

---

## Frontend page (NEW · to ship in next session)

Route: `/admin/dls/week-1-debrief`
Component: `pages/admin/AdminDlsWeek1Debrief.jsx`
Pattern: clone of `AdminDlsDay1Debrief.jsx` with the new question array and the new POST shape.

UX:
- Calm dark form (matches Day-1 visual continuity)
- All 16 questions visible (no pagination · doctrine: feedback is one calm sitting)
- Anti-creep questions at the bottom
- One submit button: "Capture Week-1 debrief"
- On success: green confirmation + the markdown filename + link to `/admin/system` to see the file in `/app/memory/`

---

## Discoverability

Add a single calm link on `/admin/dls/day-1-debrief` after the user submits their Day-1:

> "Week-1 follow-up debrief available 6 days from now → /admin/dls/week-1-debrief"

No notifications. No emails. No dashboard. The operator knows when week-1 is — that's the trigger.

---

## Doctrine guardrails (held)

| Restraint | Status |
|---|---|
| NO survey analytics | ✅ |
| NO reporting dashboards | ✅ |
| NO charts | ✅ |
| NO sentiment scoring | ✅ |
| NO trending across debriefs | ✅ |
| Markdown-only output (operator reads, doctrine evolves) | ✅ |
| EN/ES coverage on all 16 questions | required in implementation |

---

## Estimated effort

- Engineering time: **0.5 session**
- Files touched: 2 backend (extend `dispatch_day1_debrief.py` + i18n strings) + 2 frontend (new page + route)
- Test coverage: `test_iter432_week1_debrief.py`

---

## Status

📋 **PLAN COMPLETE · execution awaits the operator's Day-7 cue**

The natural trigger for shipping the Week-1 form is **on the morning of Day-6 of production live-ops**, so it's available for the operator to capture on Day-7. Until then, the form lives only as a plan.

---

End of DLS Week-1 Debrief Plan.

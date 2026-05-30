# GAP_REGISTER_UPDATE

**Date:** 2026-02-01 · Batch A · Step 2
**Authorized action:** Add NEW-GAP-A to `ORPHAN_AND_GAP_REGISTER.md`. Apply re-ranking from `GAP_REVALIDATION_REPORT.md`.

---

## Change applied

A new row was added to `ORPHAN_AND_GAP_REGISTER.md` under §3 Soft orphans, and the inventory rollup in §8 was updated.

### NEW-GAP-A · Safety Meeting submit — no bell/task fan-out

- **Code evidence**: `routes/safety.py:455–465` — only `schedule_auto_email("meeting", doc)` is called; **no `emit_task_and_notification(...)` call exists** in the meeting submit handler. This was missed in the original gap register because the Truth Map (Phase 1) incorrectly described the meeting workflow as "Email + task + bell via emit_task_and_notification".
- **Same family as**: GAP-3 (JHA) and GAP-1 (FL forms) and GAP-2 (Safety Forms) — all P1 visibility gaps where email-only delivery exists but in-app fan-out is missing.
- **Severity**: P1 (must fix before pilot) — but **operator decision required** on whether meetings are intentionally email-only ledger or should join the fix track.
- **Business impact**: Meetings recorded as ledger only; no per-record actionable queue. Safety supervisor must check their inbox or open the Admin/Safety meetings list to find new submissions; no bell drawer entry.
- **Owner**: Safety supervisor (primary action), HR (compliance lens).
- **Recommended fix (NOT YET AUTHORIZED)**: One-line insertion after `routes/safety.py:464`:
  ```python
  await emit_task_and_notification(
      db,
      task={
          "kind": "safety.meeting.review",
          "title": f"Review safety meeting — {doc.get('topic') or doc.get('meeting_type')}",
          "assignee_role": "safety",
          "priority": "Low",
          "context": {"meeting_id": doc["id"], "project_number": doc.get("project_number")},
      },
      notification={
          "kind": "safety.meeting.submitted",
          "title": "New safety meeting submitted",
          "recipient_role": "safety",
          "priority": "Low",
          "deep_link": f"/admin/meetings/{doc['id']}",
      },
  )
  ```
- **Operator decision needed**: Decide whether to authorize this fix in a future batch.

---

## Re-ranked inventory (post-update)

| Tier | Items | Count |
|------|-------|-------|
| **P0 (operational risk now)** | GAP-7 (Backup scheduler dead — HELD) · GAP-6/ORPHAN-1 (Fleet DVIR) | 2 |
| **P1 (must fix before pilot)** | GAP-1, GAP-2, GAP-3, **NEW-GAP-A (Meeting)**, GAP-4, GAP-10, GAP-16, GAP-17 | 8 |
| **P2 (improvement opportunity)** | GAP-5, GAP-8, GAP-9, GAP-14, GAP-15, GAP-18 | 6 |
| **P3 (test-only)** | GAP-11, GAP-12, GAP-13 | 3 |
| **Total** | | **19 gaps + 1 confirmed orphan** |

---

## Stop-condition compliance

- ✅ No notification wiring applied (the recommended fix is documented only)
- ✅ No gap closure begun
- ✅ Documentation-only change to `ORPHAN_AND_GAP_REGISTER.md`
- ✅ No code changes

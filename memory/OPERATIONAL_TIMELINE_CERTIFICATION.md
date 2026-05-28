# Operational Timeline — Certification

**Phase V-Prelude · Wave 1 · Substrate**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Doctrine reference

- `/app/memory/OPERATIONAL_TIMELINE_FOUNDATION.md`

## Files

| File | Purpose |
|---|---|
| `backend/routes/operational_timeline.py` | Read-only aggregator endpoint |
| `frontend/src/components/operational/ChronologyPanel.jsx` | Calm, text-only renderer |
| `frontend/src/lib/operationalApi.js` | `getTimeline(project_id, { from, to })` |
| `backend/tests/test_v_prelude_wave1_substrate.py` | Timeline contract tests |

## API surface

```
GET /api/timeline?project_id=...&[from=ISO]&[to=ISO]
```

### Response shape

```json
{
  "project_id": "P-XYZ",
  "generated_at": "2026-05-28T17:33:11.123Z",
  "truncated": false,
  "items": [
    {
      "kind": "operational_constraint",
      "id": "<uuid>",
      "at": "2026-05-28T17:30:00.000Z",
      "title": "Utility conflict STA 144+50",
      "subtitle": "utilities · high",
      "relationship": null,
      "project_id": "P-XYZ",
      "linked_to": []
    }
  ]
}
```

## Doctrine guarantees (verified)

| Rule | Enforcement |
|---|---|
| Single project per call | `project_id` is REQUIRED (`HTTP 422` otherwise). `test_timeline_requires_project_id`. |
| Read-only | No write endpoints exist on this router. |
| Sorted newest-first | `items.at` is monotonically non-increasing. `test_timeline_aggregates_and_sorts`. |
| ≤ 200 items | `MAX_ITEMS=200` constant; `truncated=true` flag if more. |
| TRUST-TIME-1 timestamps | `generated_at` and every `at` end with `Z`. |
| Audit-only visibility filter | `visibility="audit-only"` links hidden from non-admin. |
| Voided links hidden | `status="voided"` excluded from item set. |
| No charts, no gantt, no swim-lanes | `ChronologyPanel.jsx` renders `<ol>` of `<li>` rows only. |

## Aggregation sources

The timeline aggregates from THREE existing substrate sources — no
new collection, no derived materialised view:

1. **`operational_constraints`** — one row per constraint (creation
   event) plus one row per chronology event (resolve, owner contacted,
   operator note).
2. **`operational_links`** — every active or archived link touching
   the project surfaces as a row labelled by its `relationship`.
3. **Future:** when V.1 RFI lands, RFI rows will appear automatically
   through the `operational_links` substrate — zero timeline code
   changes required. That's the forward-compatibility contract.

## Visual doctrine

`ChronologyPanel.jsx` renders:
- Slate text on white.
- Date · kind · title · subtitle (no badges, no colour pills).
- Empty state copy: "No chronology yet." (italic, slate-500).
- No icons. No avatars. No gradient. No animation.

— certified by E1 · 2026-05-28

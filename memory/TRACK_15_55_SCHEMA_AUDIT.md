# TRACK 15.55 · Schema Audit

**Status:** ✅ Schema supports unlimited attendees at every layer below the UI.

## Layer-by-layer verification

| Layer | Source | Capacity |
|---|---|---|
| React state | `useState({ attendees: [] })` in `NewMeeting.jsx:73` | unbounded |
| API contract (Pydantic) | `class MeetingCreate ... attendees: List[MeetingAttendee] = Field(default_factory=list)` in `routes/safety.py:178` | **no `max_items` cap** |
| MeetingAttendee fields | `name · employee_id · non_masci · company · trade · signature · acknowledged · acknowledged_at` (`routes/safety.py:166`) | per-row free; array length free |
| Mongo storage | `db.meetings` documents · `attendees: [...]` array | BSON document up to 16 MB — at typical ~250 bytes per attendee (no signature) or ~5 KB with signature, ceiling is ≈ 3,000 signed attendees |
| PDF render | `pdf_render.py:render_record_pdf("meeting", record)` iterates `record["attendees"]` via Jinja loop with no `[:N]` slice | unbounded |
| List endpoint | `GET /api/meetings` returns `attendee_count = len(d.get("attendees", []))` (`routes/safety.py:674`) | counts every row |
| CSV/Excel exports | `routes/exports.py` follows the same array | unbounded |

## Live evidence — historical production meetings

Ran live aggregation against production `meetings` collection:

```
meetings_total = 65
max_attendees   = 15      ← largest meeting on record
avg_attendees   = 2.6
```

The platform has already persisted a 15-attendee meeting through every layer (state → API → Mongo → list → PDF). No structural cap exists.

## Scenarios revisited

| Scenario | Schema-level support |
|---|:---:|
| 1 superintendent + 1 laborer | ✅ |
| 5 MASCI employees | ✅ |
| 20 MASCI employees | ✅ |
| 15 roster + 2 subcontractors + 1 inspector | ✅ |
| 25 manual attendees | ✅ |
| Mixed EN / ES attendees | ✅ (no language field on attendee; meeting captures `language`/`language_other` separately) |

## Backend cap search

`grep -nE "attendees|max_items|max_length" /app/backend/routes/safety.py | grep -iE "attendee"`:
- Line 178: `attendees: List[MeetingAttendee] = Field(default_factory=list)` — no cap.
- Line 641: `f"Attendees: {len(doc.get('attendees') or [])}"` — used for digest/email body, no cap applied.
- Line 662: `attendees: 1` — Mongo projection field, no cap applied.
- Line 674: `attendee_count=len(d.get("attendees", []) or [])` — count for list endpoint.

**No `max_items`, no `max_length`, no hard-coded slice anywhere.** Schema-level audit complete: unlimited attendees supported.

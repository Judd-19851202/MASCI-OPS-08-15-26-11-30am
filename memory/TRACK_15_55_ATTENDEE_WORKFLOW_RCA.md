# TRACK 15.55 · Attendee Workflow RCA

**Status:** ✅ Root cause identified · 2 lines of code · fixed in this track.

## Defect (observed)

Field superintendents report that the "Add Attendee" button stops working after the first attendee is added, forcing them toward "Bulk Add From Roster" — which inverts the real-world workflow of "type all 20 names first, collect signatures as people arrive."

## Exact root cause

`/app/frontend/src/pages/NewMeeting.jsx` lines 146-164 (`addAttendee`) and line 965 (button `disabled` prop).

```javascript
const addAttendee = () => {
  // SAFETY-MEETING-CERT · block adding a new row until current row is complete.
  const last = data.attendees[data.attendees.length - 1];
  if (last) {
    const incomplete = isAttendeeIncomplete(last);   // requires name + company + signature + acknowledgement
    if (incomplete) {
      toast.error(t("Complete the current attendee before adding another: ..."));
      return;
    }
  }
  setData((p) => ({ ...p, attendees: [...p.attendees, { ...blankRow }] }));
};
```

And the button:
```jsx
<Button onClick={addAttendee}
  disabled={data.attendees.length > 0 && !!isAttendeeIncomplete(data.attendees[data.attendees.length - 1])}
  className="… disabled:opacity-50 disabled:cursor-not-allowed"
  data-testid="attendee-add"
> Add Attendee </Button>
```

Two gates layered on top of each other (toast in handler + `disabled` prop on button) blocked every superintendent who tried to add Row 2 before signing Row 1.

## Was this intentional, regression, side-effect, or unfinished?

**Intentional.** The `// SAFETY-MEETING-CERT` comments mark it as a previous certification track's hardening attempt. The intent was *probably* "prevent submitting blank attendee rows" — but the implementation placed the gate at row-creation time instead of submit time, which is what made it user-hostile.

The correct gate is at submit-time, which **already exists** at lines 211-217 (the `validate()` function loops over every attendee row and blocks the submission if any row is missing name/company/signature/acknowledgement). The row-creation gate was redundant defense-in-depth that broke the primary workflow.

## Bulk Add interaction

`AttendeeBulkAddDialog` at lines 974-982 already does the right thing:

```jsx
onAdd={(additions) =>
  setData((p) => ({ ...p, attendees: [...p.attendees, ...additions] }))
}
```

It **appends** to the existing attendee list. It does not overwrite manual entries. The fact that field superintendents thought it was "forced" came purely from the disabled "Add Attendee" button — there was no real coupling between the two.

## Layer audit (each layer cleared)

| Layer | Limit found? | Notes |
|---|:---:|---|
| UI button + handler | ✅ YES — the bug | Fixed in this track |
| React state | ❌ none | `data.attendees` is an unbounded array |
| Form schema | ❌ none | No client-side length restriction |
| Validation | ❌ correct | Submit-time `validate()` is the right place; unchanged |
| Backend Pydantic model `MeetingCreate.attendees: List[MeetingAttendee]` (`routes/safety.py:178`) | ❌ none | No `max_items` cap |
| Mongo schema | ❌ none | Free-form array |
| Submission serializer | ❌ none | Round-trips the array as-is |
| PDF generation | ❌ none | `pdf_render.py` iterates all attendees, no slicing |
| Audit trail | ❌ none | Each attendee is part of the meeting document |
| Attendee collection | n/a | Embedded in meeting doc, not a separate collection |
| Roster import | ❌ correct | Appends, never overwrites |

The only real limit lived in the UI. Everything below the UI already supported unlimited attendees.

## Conclusion

The defect is fully diagnosed and corrected in this track by removing the per-row creation gate. Submission-time validation is preserved (every row must have name + company + signature + acknowledgement before the meeting persists), which is the correct gate.

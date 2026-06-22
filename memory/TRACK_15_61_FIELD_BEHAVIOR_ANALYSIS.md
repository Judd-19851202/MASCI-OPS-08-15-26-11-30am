# TRACK 15.61 — Field Behaviour Analysis (Phase 9)

**Method:** classify every report in the 60-day corpus by which surface(s) the operator actually used for narrative.

## Observed behavioural patterns

| Pattern | Reports | % |
|---|---|---|
| Photos but **no** Activity Log entries | **110 / 154** | **71.4 %** |
| Crew listed (`masci_crews`) but no Activity Log | ≈ 100+ (subset of above) | — |
| `general_notes` used as a substitute narrative (no `activities[]`) | 43 | 27.9 % |
| `activities[]` used but no `general_notes` | 21 | 13.6 % |
| Both `activities[]` AND `general_notes` populated | ≈ 16 | 10.4 % |
| **Zero narrative anywhere** (no activities, no general_notes) | **72** | **46.8 %** |
| Outbound materials populated but no Activity Log narrative | 3 | 1.9 % |
| Materials IN populated but no Activity Log narrative | 18 | 11.7 % |

## What the data tells us about field behaviour

1. **Operators prefer `general_notes` to `activities[]`.** `general_notes` is non-empty on 40.3 % of reports; `activities[]` is non-empty on only 26.0 %. **The free-text field beats the structured field 3:2.** Operators reach for the surface that lets them just type, not the surface that asks them to assemble rows.

2. **Photos are the dominant communication.** 97.4 % of reports have photos. 71.4 % have photos but no Activity-Log narrative. The pattern is: take photos → describe later if at all.

3. **Half the corpus has no narrative anywhere.** 72 reports of 154 (46.8 %) have neither `activities[]` rows nor `general_notes`. The report fundamentally cannot tell the story of the day.

4. **Crews enter Materials IN more than Materials OUT.** Materials IN 23.4 % vs. Materials OUT 2.6 %. Inbound deliveries arrive with paperwork (delivery tickets) that operators must record; outbound hauls are a "we know we ran trucks" tribal fact that nobody puts on a daily report.

5. **The `prepared_by` field is treated as a role label, not a name.** 11 reports have `"Superintendent"` typed into `prepared_by`. The form does not validate or auto-resolve identity.

## Is the UI teaching the wrong behaviour?

Yes, on three counts:

### (a) The Activity Log surface is structured the wrong way for foremen.

The current Activities section asks operators to add rows with `{activity, % done, notes}`. A foreman in the field at 5:30 PM writing a daily report on an iPad does not naturally compose a multi-row table. They write a paragraph. That paragraph lands in `general_notes` and is treated as a second-class field by every downstream consumer.

### (b) The form does not prompt for the story.

There is no helper / wizard / coaching block on the Daily Report that says "Tell me what your crew finished today" or "What slowed you down?". Compare with the Safety Meeting form, which now ships per-section coaching tips. The Daily Report has equipment pickers and material pickers and photo prompts, but no narrative prompt.

### (c) Photos are not captioned.

97 % of reports have photos but the photos do not carry per-photo captions in the rendered PDF. The story-telling potential of photos is being absorbed by the camera and lost on the way to the page.

## What operators ARE doing well

- Filling out crews + foreman counts (96.8 %).
- Photographing the work (97.4 %).
- Signing the report on the foreman line (97.4 %).
- Recording weather snapshots (51.9 %).

This is a literate, attentive field force. They are taking the time to use the form — they are just being routed to the wrong narrative surface.

## Conclusion

The MASCI field behaviour pattern is consistent and predictable:

> "I'll take photos · I'll list my crew · I'll mark safety incidents · I'll type a quick line in general_notes · I'll skip the activities table because filling out three fields per row is more work than typing two sentences."

This is a **UX design problem**, not a discipline problem. The fix is not to push harder on the activities table; it is to align the form with the way operators actually want to narrate.

See `TRACK_15_61_HUMAN_USABILITY_AUDIT.md` for the UX-side root-cause walkthrough and `TRACK_15_61_RECOMMENDATIONS.md` items R-UX-NARRATIVE and R-UX-PROMPT.

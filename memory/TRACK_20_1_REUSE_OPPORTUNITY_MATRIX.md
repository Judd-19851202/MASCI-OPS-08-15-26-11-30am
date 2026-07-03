# TRACK 20.1 · Reuse Opportunity Matrix

Track 19.55 universal Thread section → Employee Thread source.

| Section (Universal Thread) | Data source available today                                          | Reuse quotient           | Recommendation                     |
|----------------------------|-----------------------------------------------------------------------|--------------------------|------------------------------------|
| 1. Mission Overview         | `current_state` on Accountability endpoint · employee record         | ✅ Reuse unchanged        | Wrap in shell                       |
| 2. Attention                | Derived from `current_state` (holds / expirations / open incidents)  | ✅ Reuse with adapter     | Adapter maps to `attention.items[]` |
| 3. Operational Guidance     | Track 19.54 Guidance Card (already ships)                             | ✅ Reuse unchanged        | Pass `hr_intelligence` product row  |
| 4. Timeline                 | `events[]` on Accountability endpoint                                | ✅ Reuse with adapter     | Map to Track 19.54 event schema     |
| 5. Relationships            | Employee record + timeline (supervisor / project / crew / unit)       | ✅ Reuse with adapter     | Feed into Track 19.55 graph         |
| 6. Documents                | `/api/employee-records/records/{rid}/file`                            | ✅ Reuse unchanged        | Slot into shell                     |
| 7. Photos                   | Existing safety / field photo store                                   | ⚠️ Slot exists in shell   | Populate in follow-up if data warrants |
| 8. Operational Intelligence | `hr_intelligence` + `training_intelligence` from OI summary          | ✅ Reuse unchanged        | Slot into shell                     |
| 9. History                  | OI history for HR products                                            | ✅ Reuse unchanged        | Slot into shell                     |
| 10. Audit                   | OI audit endpoint                                                     | ✅ Reuse unchanged        | Slot into shell                     |

## Composite reuse quotient
- **10 of 10 sections** can be filled from existing endpoints.
- **7 of 10 sections** reuse unchanged.
- **3 sections** need a light frontend adapter (Sections 2 · 4 · 5).
- **0 sections** need new backend code.

## Adapters required (frontend only · Track 19.56 scope)
1. `attentionAdapter(current_state) → attention.items[]` (Section 2).
2. `timelineAdapter(events) → OperationalThread events` (Section 4).
3. `relationshipAdapter(employee, events) → RelationshipGraph edges` (Section 5).

All three adapters live in a single Employee-Thread page component
that composes `OperationalThreadPage`. Zero shared-primitive changes.

## Net new code estimated
- **Backend:** 0 lines.
- **Frontend:** ~ 1 new page (adapter + wiring) · ~ 250 LOC.
- **Tests:** ~ 1 lock test file · ~ 15 assertions.

## Verdict
🟢 **Maximum reuse achievable.** The Employee Thread is 100 %
reachable through existing certified endpoints + universal primitives.

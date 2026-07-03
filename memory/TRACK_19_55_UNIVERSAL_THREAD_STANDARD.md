# TRACK 19.55 · Universal Thread Standard

## Doctrine
Every important operational object in ForgedOps has ONE
Operational Thread that follows this exact 10-section architecture.
Fleet Unit is the pilot; Employee, Project, Incident, Vendor, and
Asset threads inherit unchanged.

## Section spec (locked · testid enforced)

| # | Section                | testid slot                       | Data slot on OperationalThreadPage  | Purpose                                                                 |
|---|------------------------|-----------------------------------|--------------------------------------|-------------------------------------------------------------------------|
| 1 | Mission Overview       | `<root>-section-1-mission`        | `mission` (label · kind · health · facts · explanation) | What is it · what state is it in · who owns it |
| 2 | Attention              | `<root>-section-2-attention`      | `attention.items[]`                  | Every item shows severity · why · owner · due · direct action           |
| 3 | Operational Guidance   | `<root>-section-3-guidance`       | `guidanceProduct` (OI summary row)   | Opens Track 19.54 Guidance Card                                          |
| 4 | Timeline               | `<root>-section-4-timeline`       | `timelineEvents[]` (Track 19.54 OperationalThread schema) | Chronological operational history          |
| 5 | Relationships          | `<root>-section-5-relationships`  | `relationships.subject` + `edges[]`  | Every connected object · clickable nodes                                 |
| 6 | Documents              | `<root>-section-6-documents`      | `documents[]`                        | Existing documents only · no duplication                                 |
| 7 | Photos                 | `<root>-section-7-photos`         | `photos[]`                           | Existing photos only · newest first                                      |
| 8 | Operational Intelligence | `<root>-section-8-oi`           | `oiProduct` (OI summary row)         | Current Score · Attention · Trend · Top Driver                           |
| 9 | History                | `<root>-section-9-history`        | `history[]`                          | Historical snapshots                                                     |
|10 | Audit                  | `<root>-section-10-audit`         | `audit[]`                            | Read-only who-changed-what                                               |

Order is **immutable**. Enforced by `test_thread_page_has_all_ten_sections`.

## Shared-primitive rule
`OperationalThreadPage` MUST import and use:
- `AttentionChip` (Track 19.54)
- `TrendChip` (Track 19.54)
- `GuidanceCard` (Track 19.54)
- `OperationalThread` (Track 19.54) — for Section 4 rendering
- `RelationshipGraph` (Track 19.55) — for Section 5 rendering

No thread page may reimplement any of these. Enforced by
`test_thread_page_reuses_shared_primitives`.

## Universal Action Queue
Every thread's shell auto-caps the `actionQueue` prop at **5 items**
via `.slice(0, 5)`. Enforced by `test_fleet_pilot_caps_action_queue_at_five`.

## Read-only guarantee
`OperationalThreadPage` never fetches. The shell is pure
presentation; the caller assembles data from existing endpoints and
passes it in. Enforced by `test_thread_page_no_fetch`.

## Future adopters
Track 19.56 · Employee Thread · uses same shell · slots come from
`/api/employees/{id}/timeline` (or nearest existing endpoint) +
`hr_intelligence` OI product.

Track 19.57 · Project Thread · uses same shell · slots come from
existing project / daily-report / PO endpoints + `project_intelligence`.

Track 19.58 · Incident Thread · uses same shell · slots come from
`/api/incidents/{id}` + `incident_intelligence`.

Track 19.59 · Vendor Thread · uses same shell.

Track 19.60 · Asset Thread · uses same shell.

Every future thread inherits ALL 10 sections. Only the data sources
change. The experience never changes.

## Delete Test
Every section must answer: "If this disappeared tomorrow, would
someone make a worse operational decision?" If the answer is NO,
the section must remain empty (honest empty state) rather than filled
with decorative data.

## Zero-drift matrix
- No new timeline framework.
- No new relationship graph framework.
- No new score model.
- No new health engine (Operational Health is derived client-side and explained in plain English).
- No new backend routes.
- No new email / recipient / scheduler path.

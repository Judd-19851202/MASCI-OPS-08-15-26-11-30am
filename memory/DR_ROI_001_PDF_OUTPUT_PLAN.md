# DR-ROI-001 · PDF Output Plan

**Track:** DR-ROI-001F (deferred per user Q5 decision)
**Session decision:** Preserve current PDF pipeline byte-for-byte. Architect V2 PDF here; do not implement.

## V2 PDF sections (planned)

1. **Executive Header** — project · date · shift · weather · GPS · supervisor · report #
2. **Today's PM Brief** — from `pm_action_items[]` + PM Agent output
3. **Production Summary** — from `production_by_activity[]` + `production_by_area[]`
4. **Delay / Constraint Log** — from `constraint_cards[]`
5. **Crew Time Summary** — from `masci_crews[]`
6. **Equipment Summary** — from `equipment[]` + `equip_hours_by_activity[]`
7. **Material / Truck Summary** — from `materials[]` + `outbound_materials[]`
8. **Safety / Quality Section** — from existing gate fields
9. **Approved Operational Narrative** — from `final_approved_narrative`
10. **AI Confidence + Source Trace** — compact summary from `ai_source_trace{}`
11. **Photo Evidence** — thumbnails linked to activity cards
12. **Signature + Audit Metadata** — verification QR code

## Cutover flag
`PDF_V2_ENABLED=false` in prod until Track F certifies dual-render.

## Backward-compat rule
V2 PDF must be generated from the same approved source-of-truth report — never regenerated independently by AI.

*Details in `DR_ROI_001_CONSOLIDATED_PLANS.md § 3`.*

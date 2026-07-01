# Track 19.05 · Daily Report Industry Research Map

Comparative research (2026 knowledge cutoff) against heavy-civil industry standards. **No copying** — extract high-value patterns only.

## Products surveyed

| Tool | Segment | Daily-log pattern |
| --- | --- | --- |
| **HCSS HeavyJob** | Heavy civil (self-perform) | Foreman-time-card-first: crew clocks in/out; production quantities tied to labor cost codes; equipment hours drive equipment cost; production auto-rolls into job cost |
| **Procore Daily Log** | Vertical + horizontal | Section-based (Weather, Manpower, Equipment, Deliveries, Visitors, Delays, Photos, Notes, Attachments); templates per project; email + web viewer |
| **Raken** | Field-first | Voice-to-text narrative; equipment usage; hours by trade; photo-heavy; PM roll-up dashboards |
| **Fieldwire** | Task + punch | Not primary DR — mainly RFI/punch. Daily reports are lightweight photo + note per task |
| **B2W Track** | Heavy civil | Similar to HeavyJob — cost-code-first, structured production, timesheets bundled |

## Common section pattern (industry consensus)

1. **Header** — project, date, weather, prepared by, superintendent
2. **Labor / Crew** — MASCI crew + hours + trade + optional cost code
3. **Subcontractors** — company + trade + count + hours + work performed
4. **Equipment** — description + hours used
5. **Materials** — deliveries inbound + hauling / exports outbound
6. **Production quantities** — description + qty + unit + station (Heavy Civil signature move)
7. **Delays / constraints** — type + impact hours + notes → often feeds RFI/schedule impact
8. **Visitors / inspections** — inspector name, agency, notes
9. **Safety / incidents** — Yes/No + escalation flow
10. **Notes / narrative** — guided prompts or free text
11. **Photos** — 5-10 minimum, geo-tagged where possible
12. **Attachments** — CEI reports, delivery tickets, quantity sheets (PDF/XLSX)
13. **Sign-off** — foreman signature + optional superintendent

## MASCI current vs industry (Δ = redesign opportunity)

| Pattern | Industry standard | MASCI today | Δ |
| --- | --- | --- | --- |
| Cost-code integration on production rows | HCSS + B2W | NOT present — `production[]` has no cost code | GAP |
| Voice-to-text narrative | Raken | NOT present | Enhancement candidate |
| Foreman time card auto-derives crew hours | HCSS | Manual entry per crew row | Enhancement candidate |
| Structured production with quantity/unit | Procore + HCSS | ✓ `production[]` exists (Wave-1A) but 0% adoption | UX GAP |
| Inbound + outbound materials | Procore + HeavyJob | ✓ `materials[]` + `outbound_materials[]` — matches best-in-class | STRONG |
| Attachments (PDF + Excel) | Procore + Raken | ✓ Track 19.04 — matches best-in-class | STRONG (new) |
| Geo-tagged photos | Raken | ✓ GPS captured on DR, not per-photo | PARTIAL |
| PM roll-up dashboards | All | ✓ `/pm/daily` + `PmProjectFirstHome` | STRONG |
| Structured delays with RFI/schedule advisory flags | HCSS | ✓ `constraints[]` + `_derive_advisory_flags` | STRONG |
| Cost code / phase alignment | HCSS + B2W | NOT present | Future track |
| Foreman → payroll timesheet bridge | HCSS + Vista | NOT present in DR (HR Payroll Variance is separate) | Future track |

## High-value patterns MASCI already has that most competitors don't

* **Trust-spine correlation IDs** — each DR emits an auditable lifecycle event chain.
* **Actor-scoped autosave** (Track 19.04) — no cross-user residue.
* **HR canonical roster** (Track 19.03) — employee identity is single-source.
* **Job-ownership team_snapshot** — historical roster snapshot preserved on submit.
* **Excavation activity two-way linkage** — trench safety and DR are linked bidirectionally.
* **Advisory RFI/schedule flags** derived from constraint type — proactive PM signal.

## Redesign direction implications

The current MASCI DR is at parity with Procore + HCSS on structure; the redesign should focus on **adoption of existing structured fields** (production, constraints) via better UX, and NOT add more fields. The `activities[]` legacy free-text section is the confusion source — see Redundancy Audit.

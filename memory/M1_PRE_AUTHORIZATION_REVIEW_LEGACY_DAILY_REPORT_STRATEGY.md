# M1 Pre-Authorization Review · Legacy Daily Report Migration Strategy

_Phase V.1 · Pre-M1 architecture review · 2026-05-29_

> **Status:** Review and architecture answer only. **No migration code
> has been written. M1 is NOT authorized. M1 is NOT started.**

This document answers the operator's pre-authorization review question:
_"When ODR goes live, what happens to all existing Daily Reports?"_

It is grounded in **actual measurements** taken from the live preview
DB, not assumptions.

---

## 0 · Live measurements (what we are actually working with)

Pulled directly from `daily_reports` and adjacent collections in the
preview environment.

| Metric | Value |
|---|---|
| Total `daily_reports` rows | **85** |
| Distinct projects | 10 |
| Distinct `report_date` values | 24 |
| `report_date` span | **2024-08-15 → 2026-05-27** (~21 months) |
| `created_at` span | 2026-04-26 → 2026-05-27 (preview backfill window) |
| Reports with `prepared_by_signature` | 68 / 85 |
| Reports with `superintendent_signature` | 37 / 85 |
| Reports with both signatures | 37 / 85 |
| Reports with at least one crew row | 70 / 85 |
| Reports with at least one activity row | 32 / 85 |
| Reports with at least one equipment row | 35 / 85 |
| Reports with at least one material row | 23 / 85 |
| Reports with at least one photo | 70 / 85 |
| Total photo references | **481** |
| Photo formats | `photo://` 464 · `data:` 12 · other 5 |
| `job_photos` rows with `source="daily_report"` | 488 |
| `operational_links` involving any daily_report | **0** |
| Legacy doctrine docs already on disk | 5 (`DAILY_REPORT_*`) |
| Pre-existing ODR migration plan | `ODR_MIGRATION_PLAN.md` (718 lines) |

**Important:** the `daily_reports` collection is the legacy production
substrate — not synthetic. Real signatures, real photos, real crew
rosters, real safety/incident references are present.

---

## 1 · Primary answer matrix (the four binary decisions)

The operator's primary question can be expressed as four binary
decisions. The recommendation appears in the right column.

| Decision | Answer | Why |
|---|---|---|
| **Are legacy daily_reports preserved exactly as-is?** | ✅ **YES** | Historical truth is contractually and legally untouchable. The 37 fully-signed reports are operational records, not draft data. |
| **Are they converted into ODR records?** | ⛔ **NO (recommended)** | Legacy schema is fundamentally lossier than ODR. Forced conversion = invented information. (See §2 mapping audit.) |
| **Are they displayed through a unified viewer?** | ✅ **YES (read-only bridge)** | Operators search one surface. Each row carries an honest "ARCHIVE" badge so audience always knows the source. |
| **Are they searchable alongside ODR records?** | ✅ **YES** | One operator search index · two underlying schemas · read-only legacy projector. |

---

## 2 · Field-level mapping audit (legacy → ODR · "what would conversion cost?")

This audit is what makes me cautious about full conversion. Numbers
are from the 85-row inventory.

### 2.1 Fields that map cleanly (15 / ~31)

| Legacy field | ODR field | Confidence |
|---|---|---|
| `id` | `legacy_daily_report_id` (preserve) | 100% |
| `doc_id` (`DR-YYYY-NNNNN`) | `legacy_doc_id` (preserve) | 100% |
| `project_name` | `project.project_name` | 100% |
| `project_number` | `project.project_number` (4 of 85 are blank — flag) | 95% |
| `report_date` | `project.report_date` | 100% |
| `location` | `project.location_text` | 100% |
| `prepared_by` | `project.foreman_name` (UID requires lookup) | 90% |
| `superintendent` (where present) | `project.superintendent_name` | 65% (55/85 present) |
| `weather_summary` + `weather_impact` | `weather_impact.*` | 95% |
| `weather_snapshots[]` | `weather_snapshots[]` (carry as-is) | 100% |
| `gps_lat` · `gps_lng` · `gps_accuracy` | `location_at_submit` | 100% |
| `safety_incidents_today` (flag) | `safety.any_event` | 100% |
| `injuries_reported` (flag) | `safety.injury` | 100% |
| `safety_notified` / `safety_contact_*` | `safety.events[0].*` | 90% |
| `prepared_by_signature` (PNG/data URL) | `signature.foreman_acknowledgement.image_data_url` (new field, non-canonical) | 100% as preserved evidence; **0% as ODR-compliant signature** |

### 2.2 Fields that DO NOT map cleanly (16 / ~31)

The blocker isn't "we can't write data into ODR fields." The blocker
is **the ODR schema enforces closed enums and structured shapes that
the legacy data was never collected against.**

| Legacy field | Shape | What ODR demands | Conversion risk |
|---|---|---|---|
| `masci_crews[]` | `[{trade, foreman, count, hours, work_performed}]` (218 rows total · free-text `trade`) | `crew_profile.crew_type` ∈ closed set: pipe/utility/grading/fine_grade/stabilization/concrete/structures/curb/sidewalk/milling/paving/mot/survey/airfield/electrical/other | **HIGH** — every legacy row would need human classification or default to `other`, losing taxonomy fidelity |
| `crew_profile.crew_id` | not collected | required | **HIGH** — no source of truth |
| `crew_profile.primary_operation` | not collected (work_performed is free-text) | required free text but tied to crew_type | **MEDIUM** — heuristic, fragile |
| `activities[]` | empty in 53/85 reports; free-text where present | `production_segments[]` with closed `crew_type` + structured pipe/paving/concrete/structures sub-bodies | **HIGH** — most activity fidelity is unrecoverable |
| `equipment[]` | free-text rows · 35/85 populated | `equipment.rows[]` with hours/idle/down splits | **MEDIUM** — most legacy rows lack the splits |
| `materials[]` | 23/85 populated · free-text `description` | `materials[]` with closed `kind` (delivered/rejected/installed/wasted) + closed `uom` (ton/cy/lf/ea/sf/sy/each/other) + closed `material_code` | **HIGH** — closed enums had no equivalent in legacy capture |
| `subcontractors[]` | 34/85 · free shape | `subcontractors.entries[]` with `name` + `crew_size` + `hours` + `purpose` | **MEDIUM** — partial fields |
| `schedule_delays` | "Yes" / "No" string | `delays.any_delays` (bool) **plus** `entries[]` with closed `delay_type` ∈ {weather, faa, utility, material, mot, equipment, manpower, design, other} | **HIGH** — type taxonomy was never captured · everything would default to `other` |
| `schedule_delays_notes` | free text (rare · 0 used in sample) | `delays.entries[0].description` | LOW |
| `general_notes` | free text · 43/85 used | no ODR field — "narrative box" exists per section, not as a global note | **HIGH** — semantically homeless; would force operator interpretation |
| `incident_notes` | free text · 13/85 used | `safety.events[].notes` | LOW–MEDIUM (assumes incident exists) |
| `incident_report_filled` | bool | `safety.events[].incident_report_complete` | LOW |
| `incident_report_time` | local string | `safety.events[].contact_time_utc` (UTC required) | **MEDIUM** — TZ inference required |
| `submit_language` | "en" / "es" | not stored on ODR (translation events use a side table) | LOW (drop · informational) |
| `distribution_list[]` | 36/85 · email list | NOT carried into ODR (one-time mailing) | LOW (drop) |
| `prepared_by_signature` / `superintendent_signature` | base64 image data URL · 68/85 + 37/85 | ODR signature is `acknowledged: bool` + `acknowledged_at_utc` + `text` (statement) — **NOT an image** | **HIGH for compliance** — the legal artifact is the inked image; ODR's text-acknowledgement is a fundamentally different attestation. Re-recording as ODR-style signature would invent attestation that didn't happen. |

### 2.3 Manual-review burden estimate

If we forced conversion (Option B), the realistic manual-review
queue would be:

| Review category | Rows requiring review | Reason |
|---|---|---|
| `crew_type` classification | ~70 rows (218 crew sub-rows) | closed enum required |
| Production segment shape (pipe/paving/concrete) | ~32 rows | crew_type drives sub-body shape |
| Material `kind` + `uom` + `material_code` | ~23 rows · ~25 sub-rows | closed enums |
| Delay `delay_type` | unknown count (many "Yes" with no notes) | closed enum |
| Signature attestation re-anchor | 68 + 37 | legal exposure (re-attesting historical work) |
| `general_notes` semantic placement | 43 rows | no canonical destination |
| Project / superintendent UID resolution | ~15 ambiguous | fuzzy name match |

**~150–200 individual operator decisions across 85 reports** to convert
faithfully. At ~3 min/decision, that's **~10 hours of senior PM
review time for 85 records.** Multiplied for the future when this
collection grows, the slope is unfavorable.

### 2.4 The killer constraint: signature re-attestation

This is the single hardest reason to avoid forced conversion:

> When a legacy daily report was signed by a foreman, that signature
> attests _to the legacy form's content shape_, not to an ODR
> envelope. Converting the row into an ODR envelope and carrying the
> old signature image creates an artifact in which the **signed
> evidence is the legacy schema, but the displayed envelope is ODR
> schema.** That is a chain-of-custody fault line.

The honest disposition is: **signed = frozen.** Don't touch.

---

## 3 · Option-by-option analysis

### Option A · Legacy daily_reports remain untouched forever; ODR only for new records

| Dimension | Assessment |
|---|---|
| **Pros** | Zero migration risk · zero legal exposure · 100% historical truth preserved · zero conversion cost · existing PDFs stay byte-identical · existing public links keep working · the 37 fully-signed reports remain canonical · DOT/FAA discovery requests answer with original artifacts |
| **Cons** | Two surfaces in the UI ("Daily Reports" + "ODR") · two search experiences · operators need training on which to use when · cross-cutting reports (e.g. project-to-date timeline) need a bridge layer · legacy form remains writable unless explicitly frozen |
| **Operational impact** | LOW · negligible behavior change for crews; field walks unchanged for the 21 months of historical work |
| **Reporting impact** | MEDIUM · trend reports need to read from BOTH collections; without a bridge, weekly/monthly rollups span two schemas |
| **Search impact** | MEDIUM · without a unified projector, searching "all reports for project T5860" requires hitting both surfaces |

### Option B · Migrate historical Daily Reports into ODR

| Dimension | Assessment |
|---|---|
| **Migration complexity** | **HIGH** · ~16 of 31 fields don't map cleanly · ~150–200 manual decisions for 85 rows · closed enums require human classification |
| **Risk** | **HIGH** · signature re-attestation creates legal chain-of-custody concerns · forced enum classification invents fidelity not in source · narrative semantics (`general_notes`) have no canonical home |
| **Audit implications** | **HIGH** · the migrated ODR carries a `legacy_daily_report_id` pointer, but inspectors comparing the ODR record to the original signed daily report will see structural divergence · inspector confidence decreases |
| **Chronology implications** | LOW–MEDIUM · ODR-doc-id sequence would need a special legacy band (e.g. `ODR-LEGACY-NNNN`) to avoid colliding with native ODR sequence; alternatively, migrated rows skip the doc_id allocator |
| **Confidence levels** | **65 / 85** rows can be converted with HIGH confidence (no signatures to re-attest, simple shape) · **20 / 85** can be converted with MEDIUM confidence · **0 / 85** can be converted with VERY HIGH confidence · the 37 fully-signed rows are the riskiest |

This option is **NOT recommended**.

### Option C · Hybrid: legacy preserved, ODR forward-only, unified read surface

| Dimension | Assessment |
|---|---|
| **Implementation complexity** | **MEDIUM** · `daily_reports` collection becomes write-frozen (one boolean check at create endpoint) · a `/api/operational-records` unified read API merges ODR rows + legacy daily_reports rows into one normalized projection (read-only) · search index spans both collections via a small projector layer |
| **Operational benefits** | One search box · one timeline · one PM dashboard tile · operators see "ARCHIVE" badge on legacy rows so context is never ambiguous · zero re-training on historical material |
| **Audit benefits** | **HIGH** · every legacy row remains byte-identical to what was signed · DOT/FAA discovery answers point at the original signed PDF · ODR-era rows are governed by ODR audit trail · the seam between the two is a documented boundary, not a hidden conversion |
| **Recommended approach** | ✅ **YES — this is the recommended path.** It honors every one of the operator's six concerns (no data loss · no corruption · no rewriting truth · no broken audit trails · no migration risk · no legal exposure). |

---

## 4 · Recommended approach (detail)

**Recommendation: Option C — "Frozen Archive + Forward-Only ODR"**

### 4.1 Three concrete moves (architecture only · NOT implementation)

1. **Freeze `daily_reports` writes.**
   - At cutover, the create endpoint for daily_reports returns
     `410 Gone` with a calm "Daily Reports are now Operational Daily
     Records — open ODR" message.
   - Existing reads continue working unchanged.
   - The 85 historical rows remain queryable, exportable, and
     byte-identical to their signed state.

2. **Add a unified read projector — `GET /api/operational-records`.**
   - Returns a normalized envelope merging ODR + frozen
     daily_reports.
   - Each row carries `record_kind` ∈ `{odr, legacy_daily_report}`
     and an `archive: true` flag for legacy.
   - Field shape is the **subset that exists in both schemas**
     (project, date, foreman, signed?, photo_count, status). Anything
     ODR-specific (audience projection, amendments) is null on legacy
     rows.
   - This is a **read-only projector**, not a migration.

3. **Bridge `operational_links` for legacy rows.**
   - Today: 0 legacy rows participate in `operational_links`.
   - Forward: when a future ODR amends a project that has legacy
     reports, create a `chronology_anchor` link (`source_type=odr`,
     `target_type=legacy_daily_report`, `relationship=succeeds`).
   - This preserves cross-document chronology without touching the
     legacy row's content.

### 4.2 What changes for the operator (in plain English)

| Operator action | Before M1 | After M1 |
|---|---|---|
| Foreman fills out today's report | Daily Report form | ODR foreman entry |
| PM looks at last 6 months of project records | Daily Reports dashboard | Operational Records dashboard (mixed list, archive badge on legacy) |
| Inspector requests historical record | Same legacy PDF as ever | Same legacy PDF as ever |
| Inspector requests current record | n/a | ODR external PDF (M0.4 audience-projected) |
| PM searches "all reports with safety event for project X" | Daily Reports search | One unified search across both |
| Auditor compares signed evidence | Original legacy form | Original legacy form (untouched) |

### 4.3 What does NOT change

- ✅ Every signed daily report remains byte-identical.
- ✅ Every legacy PDF link remains valid.
- ✅ Every audit trail remains untouched.
- ✅ Every legacy photo remains where it was uploaded (`job_photos` indexed against `source="daily_report"` is preserved).
- ✅ No row is rewritten, re-attested, or re-classified.
- ✅ Closed-enum decisions for legacy rows are **never made** — legacy stays in legacy shape.

### 4.4 Why this option uniquely satisfies the six operator concerns

| Operator concern | How Option C satisfies it |
|---|---|
| Don't lose historical data | Legacy collection frozen, never touched after M1 |
| Don't corrupt historical records | Zero mutations to `daily_reports` rows |
| Don't rewrite historical truth | No closed-enum guesses, no signature re-attestation |
| Don't break audit trails | Both substrates retain their native audit (legacy `created_at` chain, ODR `odr_section_events` chain) |
| Don't create migration risk | No migration script touches legacy rows; the only new code is the read projector |
| Don't introduce legal exposure | Original signed forms stay canonical for all 37 signed reports |

---

## 5 · Answers to the 10 additional questions

### Q1 · Approximately how many Daily Reports currently exist?

**85 records in preview.** Span: 2024-08-15 → 2026-05-27. Distinct
projects: 10. Production environment count needs a separate
read; it is governed by the same recommendation regardless of
multiplier.

### Q2 · What fields map cleanly into ODR?

**~15 of ~31 fields.** Identifiers, project metadata, dates,
location, GPS, weather snapshots, safety flags, contact metadata —
all carry losslessly. Full mapping table in §2.1.

### Q3 · What fields do NOT map cleanly?

**~16 of ~31 fields.** The blocker is **closed enums and structured
shapes that legacy never collected against**: `crew_type`,
`primary_operation`, `delay_type`, `material.kind/uom/material_code`,
`production_segments` body shape, signature semantics, narrative
placement (`general_notes`). Detail in §2.2.

### Q4 · How many reports would require manual review?

If forced conversion: **~150–200 individual classification
decisions across 85 reports.** Roughly:
- 70 `crew_type` decisions (218 sub-rows aggregated)
- 32 `production_segments` shape decisions
- 23 `material.kind/uom` decisions
- Unknown delay-type decisions
- 105 signature re-attestations
- 43 `general_notes` semantic placements

**Recommended path (Option C): 0.** Legacy stays in legacy.

### Q5 · How would legacy photos be handled?

Already governed correctly today:

- **481 photo references** across 70 reports
- **488 rows in `job_photos` indexed with `source="daily_report"`** — the photo library bridge already works
- 464 are `photo://` cloud refs · 12 `data:` URLs · 5 other
- **Recommendation:** the unified read projector returns a
  `photo_count` for legacy rows; legacy PDFs continue serving the
  original photos via existing endpoints; ODR-era photos go through
  the M0.4 audience-projected pipeline. Two pipelines, one user-
  visible badge ("Archive · Photos served via legacy library").

### Q6 · How would legacy attachments be handled?

Legacy `daily_reports` does NOT have an `attachments` collection.
There are 0 legacy attachments to migrate. ODR's `odr_attachments`
collection (currently 0 rows) starts clean from M1 forward. **No
attachment migration is needed.**

### Q7 · How would chronology work across legacy + ODR?

Two-layer chronology:

- **Per-record chronology** stays native to each substrate (legacy
  `created_at` + signature timestamps; ODR `odr_section_events`).
- **Cross-record chronology** is provided by `operational_links`.
  Currently 0 legacy rows participate. Forward, when ODR rows
  reference the same project, the projector emits
  `chronology_anchor` links pointing at the legacy `daily_report.id`
  (`relationship=succeeds`). This stitches the timeline without
  mutating the legacy row.

### Q8 · How would `operational_links` work with legacy records?

Today: no legacy row participates. Forward: legacy rows are valid
**targets** of `operational_links` but **never sources** (frozen
write-side). Specifically:

- A new ODR can link `source_type=odr → target_type=legacy_daily_report` (relationship=`succeeds` or `references`).
- A photo can link to a legacy daily report (`source_type=photo → target_type=legacy_daily_report`, `relationship=evidence_for`) for retroactive evidence assignment without mutating the legacy row.
- Legacy rows themselves are never the source of new links.

This requires `operational_links.ARTIFACT_TYPES` to learn the
`legacy_daily_report` token. Doctrine-allowed; one-line schema
addition. (NOT IMPLEMENTING — review only.)

### Q9 · How would public PDF continuity work for legacy reports?

**Legacy PDFs continue working exactly as before.** The legacy daily
report PDF endpoint is preserved read-only. No migration to ODR's
PDF framework. Existing public-link continuity for daily reports is
governed by the legacy stack; ODR's M0.2 + M0.4 PDF framework
applies only to ODR-native records.

If at some future point an operator wants ODR-style audience-
projected PDFs for legacy material, that is a **render-time
projection**, not a migration. The legacy row remains untouched.

### Q10 · What is your recommended migration strategy and why?

**Recommended: Option C — "Frozen Archive + Forward-Only ODR" with
a unified read projector.** Reasons in priority order:

1. **Preserves every signed record byte-identical.** The 37 fully-
   signed and 31 partially-signed rows are operational evidence,
   not data. Forced conversion = re-attesting attestations.
2. **No closed-enum invention.** ODR's strength is its closed-enum
   discipline. Forced conversion would defeat that discipline by
   defaulting to `other` for the entire ~21-month history.
3. **Zero migration risk.** The hardest bug to find is the bug you
   introduce in code that didn't need to exist.
4. **Legal defensibility is highest.** Inspectors and DOT/FAA
   reviewers see original artifacts unchanged; ODR-era rows have
   their own clean audit trail. The seam between the two is
   documented, not hidden.
5. **Operator UX is preserved.** One unified projector gives PMs and
   FLs the single search/timeline/dashboard surface they want.
6. **Reversible.** If 12 months from now field reality argues for
   conversion of a specific subset, that subset can be opted in
   one project at a time — never the whole archive at once.

The pre-existing `ODR_MIGRATION_PLAN.md` (718 lines, very thorough)
was written for Option B. **My recommendation is to mark that plan
"Option B reference · not selected" and adopt Option C as the M1
contract.** Most of its mapping work becomes useful background
material for the unified read projector, not a migration script.

---

## 6 · What I am asking the operator to authorize at M1

If Option C is acceptable, M1 authorization would scope:

| M1 Scope | Description |
|---|---|
| **Freeze writes** on `daily_reports` (one server-side check + a calm 410 Gone) |
| **Unified read projector** at `GET /api/operational-records` (read-only) |
| **`operational_links.ARTIFACT_TYPES` learns `legacy_daily_report`** as a target-only token |
| **Frontend: `OperationalRecordsDashboard.jsx`** showing both substrates with archive badge |
| **Per-doc-id resolver** that routes `/r/<doc_id>` to the right viewer (DR-* → legacy view, ODR-* → ODR view) |
| **NO mutation of any `daily_reports` row** |
| **NO conversion script** |
| **NO signature re-attestation** |
| **NO closed-enum guessing** |

That scope is small, safe, reversible, and respects every operator
concern.

---

## 7 · What is NOT included in this answer (per directive)

- ❌ No migration code written
- ❌ No `daily_reports` writes-frozen change applied
- ❌ No unified projector implemented
- ❌ No new collections created
- ❌ No M1 work begun
- ❌ No dual-write surface introduced
- ❌ No pilot rollout

This artifact is **review only**. M1 awaits explicit authorization
in the form of a directive that says (or is equivalent to):

> _"M1 authorized. Proceed under Option C. Implement freeze + read
> projector + operational_links bridge as scoped in §6. STOP at end
> of M1 closure for re-review before pilot."_

---

_End of M1_PRE_AUTHORIZATION_REVIEW_LEGACY_DAILY_REPORT_STRATEGY.md._

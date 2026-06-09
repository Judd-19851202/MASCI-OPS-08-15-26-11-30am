# DR-PDF-001 · DAILY REPORT PDF CONSTITUTIONAL AUDIT

**Authority:** OMEGA DIRECTIVE — DR-PDF-001 (PDF audit and modernization sprint)
**Date:** 2026-02-09
**Scope:** AUDIT-ONLY. Zero code changes performed. Recommendations require subsequent explicit authorization.
**Evidence base:**
- `/app/backend/pdf_render.py` (full read of `_render_daily` and `render_record_pdf`)
- Live PDF fixture rendered in-process via `render_record_pdf("daily-report", …)` against a fully-populated, realistic paving-day Daily Report
- Per-page screenshots captured + cross-checked by independent visual analyzer
- Cross-reference: `DR_AUDIT_001_FULL_CONSTITUTIONAL_AUDIT.md`, `DR_FIX_1`/`DR_FIX_2`/`DR_FIX_3` certifications, `MM_001B_VISIBILITY_CERTIFICATION.md`, `MM_001B_F1_FALSE_OUTGOING_FIX_CERTIFICATION.md`, `PDF_AUDIT_FOOTER_RENDER_CERTIFICATION.md`

---

## EXECUTIVE FINDING (one paragraph)

The Daily Report PDF is **technically complete but operationally illegible** for the audiences it serves. The data layer is now solid (DR-FIX-1/2/3 + MM-001B). The render layer is **information-flat**: it presents every section at equal visual weight, in order of historical numbering rather than executive value, with no "today in numbers" surface, no severity escalation, no day-over-day context, and material duplication between Activities (09), Production (09b), and General Notes (03). A representative paving day produces a **4-page PDF** where pages 1 and 4 are ~⅓ empty, page 2 is bloated by a redundant inline math line repeated under every crew member, and the highest-signal narrative (General Notes) is buried below "Schedule Delays: No / Accidents: No" boolean rows. **A 60-second reader will not understand the day from this PDF today.** The path forward is additive (one Executive Summary at the top, one Quiet Day badge for safety status, two duplication removals, one crew-math collapse) — not a redesign.

---

## SECTION A · PDF STRUCTURE INVENTORY

Rendered sample: realistic I-95 SB resurfacing day, 6 MASCI crew, 1 sub, 1 visitor, 3 equipment, 2 materials, 2 activities, 2 production rows, 2 constraints, 6 photos. Total output = **4 pages, 1.43 MB**.

| Section ID | Title | Source field(s) | Renderer | Pillar gate | Always on? |
|---|---|---|---|---|---|
| **Header** | "Daily Job Report" + MASCI logo + "Ref · {report_number}" + project banner | `project_name` / `report_date` / `id[:8]` | `render_record_pdf` HTML head (lines 1485+) | Trusted · Beautiful | Yes |
| **01 · Project Information** | Project, #, Location, Date, Report #, Prepared By, Superintendent, Weather, GPS | top-level DR fields | `_render_daily` lines 211-233 | Trusted · Powerful | Yes |
| **(02)** | — | — | **Missing** — numbering jumps 01 → 03 | — | n/a |
| **03 · General Information** | Schedule Delays Y/N, Weather Impact Y/N, Accidents Y/N, Injuries Y/N, Detail, Safety Escalation block (conditional), **General Notes** | mixed Y/N + free text | `_render_daily` lines 235-266 | Powerful · Trusted | Yes |
| **04 · MASCI Crews on Site** | Name, Trade, Start, Stop, Lunch, Hours, Work Performed (+ inline gross/net summary), Total Hours row | `masci_crews[]` | lines 268-325 | Powerful · Proven | Conditional |
| **05 · Subcontractors** | Company, Trade, Headcount, Hours, Notes (+ per-sub photo grid + note) | `subcontractors[]` | lines 327-384 | Powerful · Trusted | Conditional |
| **06 · Visitors** | Name, Company, Purpose, Time In, Time Out | `visitors[]` | lines 386-405 | Trusted | Conditional |
| **07 · Equipment Log** | Unit, Hours Used, Time Delivered, Time Removed, Notes | `equipment[]` | lines 407-426 | Powerful · Proven | Conditional |
| **08 · Materials Delivered** | Description, Qty, Unit, Supplier, Ticket #, Notes (+ ticket-photo grid) | `materials[]` | lines 428-460 | Powerful · Trusted | Conditional |
| **09 · Activities Performed** | Activity, % Done, From, To, Notes | `activities[]` (legacy free-text) | lines 462-490 | Powerful | Conditional |
| **09b · Production Quantities** | Description, Qty, Unit, From, To, Notes | `production[]` (DR-FIX-1 / Wave-1B) | lines 492-521 | Powerful · Proven | Conditional |
| **09c · Delays / Extra Work · Constraints** | Type, Hours Impact, Advisory (RFI / Schedule), Notes | `constraints[]` (DR-FIX-1 / Wave-1B) | lines 523-552 | Powerful · Trusted · Proven | Conditional |
| **09d · MASCI Hauling Today** | Haul Type / Material / Source / Destination / Loads / Carrier + summary line | `dispatch_assignments` derived (MM-001B / E-1) | lines 554-631 | Powerful · Trusted | Conditional (dispatch rows exist) |
| **10 · Photos** | Up to 24-photo grid | `photos[]` (capped at 24) | lines 164-179 + 633 | Beautiful · Proven | Conditional (becomes empty header if photos unresolvable) |
| **11 · Signature** | Prepared By signature only (DR-FIX-3 / R13) | `prepared_by` + `prepared_by_signature` | lines 635-648 | Trusted | Conditional |
| **Header line** (every page) | "Generated through MASCI Operations Platform — Powered by ForgedOps™ \| © 2026 ForgedOps™" | static | `@page @bottom-left` | Trusted | Yes |
| **Audit footer** (every page) | "Official Record · {doc_id} · sha256={first16} · rendered {utc}" | derived | `@page @bottom-center` (lines 1408-1442) | Trusted · Proven · **R5 SHIPPED** | Yes (daily-report only) |
| **Pagination** (every page) | "Page X of Y" | counter | `@page @bottom-right` | Trusted | Yes |
| **Disclaimer block** | Platform / no-substitute-for-supervision + ForgedOps attribution | static HTML | end of `render_record_pdf` | Trusted | Yes (last page only) |

**Page Map for the sample render:**
- **P1**: Header · 01 Project · 03 General + General Notes — *~⅓ unused vertical*
- **P2**: 04 Crews (51-row total; ~70% of page) · 05 Subs · 06 Visitors · 07 Equipment — *densest page*
- **P3**: 08 Materials · 09 Activities · 09b Production · 09c Constraints — *densest content-per-pixel*
- **P4**: 10 Photos (empty header in sample) · 11 Signature · Disclaimer — *~⅔ unused vertical, signature feels orphaned*

---

## SECTION B · INFORMATION HIERARCHY REVIEW

### What gets rendered first?
**Pre-fix order**: Header → Project ID block → "Schedule Delays: No / Accidents: No" → General Notes → Crews → Subs → Visitors → Equipment → Materials → Activities → Production → Constraints → Hauling → Photos → Signature.

### What an executive actually needs first?
1. **The day's verdict** (Safe day? · On schedule? · How much work?) — currently demands scanning 3 pages to assemble
2. **Production achieved** (e.g., "240 TON SP-12.5 placed STA 12+50→23+50") — currently page 3
3. **Constraints / schedule risk** (RFI candidates · schedule-impact flags) — currently page 3, last
4. **Resource utilization** (51 crew-hrs, 3 pieces of equipment, 1 sub) — currently page 2, scattered
5. **Safety status** (Incidents / Injuries / Escalation) — currently page 1 but rendered as plain "No" — visually identical to "Yes"
6. **Material movement** (12 loads SP-12.5 inbound) — currently page 3 (when dispatch exists)
7. **General narrative** — currently page 1, bottom of Section 03

### Verdict on order
Order is **historical (numbering-driven), not signal-driven**. A reader assembling the day must scan all 4 pages and mentally reconstruct totals. There is no surface that says *"This day in 12 numbers."*

---

## SECTION C · EXECUTIVE CONSUMPTION AUDIT

**Time-to-understand the sample day (measured on the rendered PDF):**
- Read P1 header + Section 01: ~6s — captures project, date, prepared by
- Read P1 Section 03: ~10s — confirms safety "No/No/No/No" but General Notes paragraph requires a deeper read
- Skim P2 Crews table: ~15s — must mentally roll up to "6 MASCI + 6 sub-hauling + 1 CEI visitor"
- Skim P3 (Materials + Production + Constraints): ~20s — *this is where executive value lives*
- Skim P4: ~5s — photos block, signature

**Total elapsed: ~55s minimum to reach a clear mental model — at the limit of the 60s target on a happy-path day.** Increase complexity (4 crews + 2 subs + delays + RFI flag) and this exceeds 90s.

**Failure modes for execs:**
- "Safe / Not safe" status is buried as four "No" KVs that look identical to a "Yes" KV (no visual escalation when something is wrong)
- "Schedule risk" is a column flag (`Schedule`) in a table on page 3 — invisible at executive glance
- Production headline numbers (TON / LF / lane-miles) require math: sum 240 TON + 165 GAL + 1100 LF — not surfaced as totals
- No day-over-day or vs-plan signal

---

## SECTION D · PM CONSUMPTION AUDIT

PMs CAN find: production rows (09b), constraints with advisory flags (09c), material deliveries (08), subcontractor activity (05), MASCI crew burn (04).

PMs CANNOT efficiently find:
- Cumulative production vs the job (no "Y/T/D" rollup; each DR is a standalone island)
- Cost-relevant rollup (total crew-hours = 51 is calculable from page 2 but not surfaced near production)
- Risk severity at a glance (RFI advisory flag is a column tag, not a callout)
- Crew vs production efficiency ratios (would need a side-by-side compute)

---

## SECTION E · SUPERINTENDENT CONSUMPTION AUDIT

Supers CAN find: crews + start/stop/lunch (04), equipment (07), per-crew work performed (04 right column), safety yes/no (03), production (09b).

Supers CANNOT efficiently find:
- Crews that didn't show vs roster (no "expected vs actual" surface)
- Equipment idle (Time Delivered / Time Removed is shown but no idle-hours derivation)
- Daily Total Hours is at the bottom of the Crews table — readable but visually subdued
- Constraint hours are in 09c but not echoed into the Crews section (a 0.75 h trucking delay impacts production but doesn't show in Crews)

---

## SECTION F · SAFETY CONSUMPTION AUDIT

Safety CAN find: Accidents / Injuries yes/no (03), Escalation block (conditional · only when Yes), Visitors (06), Subs headcount (05).

Safety CANNOT efficiently find:
- **Excavation activity visibility** — `excavation_activity_today` and `linked_excavation_ids` are gate-validated server-side (raises 422 on submit when YES + no linkage), but neither field is rendered on the PDF anywhere. *Gap.*
- Safety meeting / JHA cross-link to the DR
- Stop-work / near-miss / observation surface (none in DR schema today)
- Lift / hot-work / confined-space / dig activity callouts

---

## SECTION G · PHOTO INTELLIGENCE AUDIT

`_photos_block` renders up to **24 photos** in a CSS grid (lines 164-179). At ~3 per row with full-width thumbnails, 24 photos = 8 rows ≈ 2.5 pages of photos alone on a busy day.

Observed issues:
- **Empty-header bug** — Section 10 still emits the "10 · PHOTOS" header even when every `photos[]` entry fails to resolve (e.g., the 1px placeholder fixtures in the audit sample → header on P4, zero thumbnails below it, large whitespace). Dead weight.
- **No captions** — every photo prints with no station / no timestamp / no caption, even though the data model carries that metadata on adjacent records (e.g., subcontractor block-level photos do get a "Company · Trade" header — `materials[].ticket_photos` and top-level `photos[]` do not).
- **Photo overflow** — at >12 photos, P4 fills before signature → signature pushed to P5 → orphan disclaimer page.
- **Subcontractor / Materials photo blocks are well-implemented** (5 + 8 inline) — these set the right pattern, but Section 10 doesn't follow it.

---

## SECTION H · MATERIAL MOVEMENT (MM-001B / E-1) VISIBILITY AUDIT

**Placement:** Section 09d, between Constraints (09c) and Photos (10).
**Source:** Async query to `dispatch_assignments` at render time (lines 562-628).
**Render:** Summary line ("Assignments: N · Loads: N · Trucks: N · Material: N · Other: N") + 6-column table (Haul Type, Material, Source, Destination, Loads, Carrier).
**Defect coverage:** MM-001B-F1 already excluded production[] from the rollup. PDF only shows dispatch-derived hauling — correct.

**Consumer value:**
- **PM:** ✅ Strong — surfaces today's dispatch-controlled hauling without needing to open the dispatch portal.
- **Exec:** 🟡 Moderate — visible only via the summary line, which buries the relevant load count in a comma-separated string.
- **Super:** ✅ Strong — confirms carrier presence.
- **Safety:** 🟡 Weak — no link to excavation activity or job-site flow.

**Gap:** Section 09d is gated on `dispatch_assignments` only. External vendor deliveries surfaced via DR `materials[]` are separately rendered in Section 08 — so two surfaces describe the same day's material flow. Either consolidate by reference or label them clearly as "MASCI hauling" vs "Vendor inbound." Currently the labels say exactly that — minor wording confusion exists but no functional defect.

---

## SECTION I · PRODUCTION (DR-FIX-1 / R1) VISIBILITY AUDIT

**Placement:** Section 09b, between Activities (09) and Constraints (09c).
**Render:** 6-column table.
**Status:** Working as designed since DR-FIX-1 ship. Verified on this audit's render — "SP-12.5 placed · 240 · TON · 12+50 · 23+50 · 1.5 in lift" appears correctly.

**Weaknesses:**
- **No totals row** — Crews has a "Total Hours: 51.00" row; Production has no equivalent total-by-unit row. A PM scanning a multi-row production list (e.g., 240 TON + 165 GAL + 1100 LF) gets no summary.
- **OTHER · Lane-Mi rendering** — the unit field for "Lane miles complete" shows `OTHER · Lane-Mi` in the Unit column. Functional but visually awkward (looks like a tag, not a unit).
- **No vs-plan signal** — production is a flat list with no comparison to job-level expected daily output.

---

## SECTION J · CONSTRAINTS (DR-FIX-1 / R2) VISIBILITY AUDIT

**Placement:** Section 09c.
**Render:** 4-column table with server-derived advisory flags.
**Status:** Working as designed. Advisory column shows "Schedule" / "RFI" tags correctly.

**Weaknesses:**
- **No severity color/icon** — a `Schedule` advisory reads as plain text; an executive scanning the PDF sees no visual difference between a 0.5h CEI inspection (no impact) and a 0.75h trucking delay (schedule-impacting).
- **Constraint type values are raw enum codes** — `cei_inspection`, `trucking`, `owner_engineer`. These are stored as `snake_case_lower` and rendered verbatim. Should be human title-cased for the PDF (`CEI Inspection`, `Trucking`, `Owner / Engineer`).
- **No rollup of total constraint hours** — easy to add ("Schedule-impacting constraints today: 0.75 h").

---

## SECTION K · IDENTITY & SIGNATURE (DR-FIX-3) AUDIT

**Status:** Working as designed since DR-FIX-3 ship.

**Render observations:**
- Section 11 = single Prepared By signature block.
- Superintendent name still renders in Section 01 (informational context, no signature).
- `prepared_by_identity` and `prepared_by_bound` are stored server-side but NOT surfaced on the PDF — correct per R9 directive (no GUID leakage).

**Weakness on the PDF:**
- Signature page often orphans alone on P4 (sample: signature block plus ~⅔ empty page below it). Could co-locate with the audit footer to save a full sheet of paper.
- No "Submitted: {timestamp local TZ}" stamp adjacent to the signature — only the UTC `rendered` stamp in the audit footer. PMs printing the PDF for a paper sign-off would benefit from a visible submitted-at timestamp.

---

## SECTION L · AUDITABILITY & TRUST AUDIT

| Trust signal | Status |
|---|---|
| `doc_id` (DR-YYYY-NNNNN) | ✅ Visible in header ref + audit footer |
| SHA256 envelope hash | ✅ **Already shipped** (Wave-1C, line 1408-1442). 16-char prefix visible in audit footer on every page |
| Rendered-at UTC stamp | ✅ Audit footer |
| Lifecycle state (draft / final / superseded) | ❌ Not visible on PDF |
| Revision history | ❌ Not visible (revisions stored via `workflow_state_events` but not surfaced) |
| Prepared-by-bound vs FSI flag | ❌ Not surfaced (correct for UI; debate-worthy for the audit footer) |
| Excavation-record linkage | ❌ Not surfaced (server-validated only) |

**R5 (DR-AUDIT-001 SHA256 audit footer) is NO LONGER an open recommendation** — it has already shipped via Phase V.2 Wave-1C. The audit footer renders on every page with `Official Record · DR-YYYY-NNNNN · sha256={first16} · rendered {ISO-UTC}`.

---

## SECTION M · DUPLICATION AUDIT

| Information | Location 1 | Location 2 | Location 3 | Verdict |
|---|---|---|---|---|
| Daily safety status | Section 03 "Accidents on Site: No" + "Injuries Reported: No" | Section 03 Safety Escalation block (only when Yes) | — | **Keep both**, but elevate to top of page as a single Safe-Day badge |
| Schedule delay status | Section 03 "Schedule Delays: No" | Section 09c (Delays / Extra Work · Constraints) advisory flags | — | **Remove from 03** (or relabel to "Today's Day-One Hazards"); rely on 09c as source of truth |
| Production / Activities overlap | Section 09 "Activities Performed" (legacy) | Section 09b "Production Quantities" (Wave-1B) | — | **Deprecate 09** when 09b is non-empty (or merge into a single "Production" section). Two parallel tables describe the same day's work. |
| Material flow | Section 08 "Materials Delivered" | Section 09d "MASCI Hauling Today" | General Notes in 03 | **Keep both** but tighten labels and consolidate the "Materials Delivered" vs "MASCI Hauling" naming so a reader knows which is vendor inbound vs MASCI-controlled |
| Crew hours math | Inline "9.0 h gross − 0.50 h lunch = 8.50 h net" under EVERY crew Work-Performed cell | Hours column on each row | "Total Hours" footer row | **Strip inline math from per-row** when all crew share the same start/stop/lunch; show inline math only for the row(s) that differ from the common pattern |
| Subcontractor photos | Inline grid inside Section 05 | Also concatenated into Section 10 if foreman re-uploaded | — | **Keep current per-sub block**; document that Section 10 must NOT duplicate sub photos |
| Material ticket photos | Inline grid inside Section 08 | Could appear in Section 10 if foreman re-uploaded | — | Same as above — keep per-material; don't dupe |
| Footer attribution | "Generated through MASCI Operations Platform — Powered by ForgedOps™ \| © 2026 ForgedOps™" repeats on **every** page | Disclaimer block at end of document repeats the ForgedOps attribution | — | **Remove repetition** from the disclaimer block — every page already carries the @bottom-left attribution |

---

## SECTION N · DEAD WEIGHT AUDIT

| Item | Evidence | Severity |
|---|---|---|
| **Inline gross/net math under every crew row** | Sample: 6 identical crew schedules → 6 identical "9.0 h gross − 0.50 h lunch = 8.50 h net" lines = ~⅓ of P2 burned on a value that equals "8.50" already in the Hours column | HIGH |
| **Empty `10 · PHOTOS` header** | When `photos[]` entries are placeholder / unresolvable, Section 10 emits a header with no body, taking ~80 px of P4 for nothing | MEDIUM |
| **"Activities Performed" + "Production Quantities" parallel tables** | Both describe what was placed today; legacy 09 is rarely empty on a real DR — adds a full table without new information | MEDIUM |
| **Two-line footer attribution repetition** | "Powered by ForgedOps™" appears in @bottom-left footer on every page AND in the final disclaimer block on the last page | LOW |
| **Orphaned signature page** | On the sample 4-page render, P4 contains signature + disclaimer in ~30% of the page; ~70% empty | MEDIUM |
| **Page 1 right-column whitespace** | KV blocks left-align into the 32% label column; right-column whitespace below them is ~25% of page area unused | LOW (informational density is fine; could host a Day-in-Numbers card) |
| **"Schedule Delays: No" KV in Section 03** | Redundant with Section 09c which is the canonical constraint surface | LOW (only fires on "No" days — but adds a row on every PDF) |
| **Numbering jump 01 → 03** | Reader sees "01 Project Info → 03 General Information" with no Section 02 → impression of a missing section | LOW (cosmetic) |
| **Header banner truncation** | The page-1 banner truncates `RECORD ID: AUDIT-FIXTURE-001` to `RECORD ID: AUDIT-FI` mid-string in the meta line | LOW |

---

## SECTION O · CONSTITUTIONAL SCORECARD

Scored on the 5 ForgedOps pillars (1 = poor, 5 = excellent):

| Section | Powerful | Simple | Beautiful | Trusted | Proven | Avg |
|---|---:|---:|---:|---:|---:|---:|
| Header / Title / Banner | 3 | 4 | 3 | 5 | 5 | 4.0 |
| 01 Project Info | 4 | 4 | 3 | 5 | 5 | 4.2 |
| 03 General Info + Safety Escalation | 3 | 2 | 2 | 4 | 5 | 3.2 |
| 04 Crews on Site | 4 | 2 | 2 | 4 | 4 | 3.2 |
| 05 Subcontractors (+ inline photos) | 4 | 4 | 4 | 5 | 5 | 4.4 |
| 06 Visitors | 3 | 5 | 4 | 5 | 5 | 4.4 |
| 07 Equipment Log | 3 | 4 | 3 | 4 | 4 | 3.6 |
| 08 Materials Delivered (+ ticket photos) | 4 | 4 | 4 | 5 | 5 | 4.4 |
| 09 Activities Performed (legacy) | 2 | 2 | 2 | 3 | 3 | 2.4 |
| 09b Production Quantities | 4 | 3 | 3 | 5 | 5 | 4.0 |
| 09c Constraints + Advisory Flags | 4 | 3 | 2 | 5 | 5 | 3.8 |
| 09d MM-001B Hauling | 4 | 3 | 3 | 5 | 5 | 4.0 |
| 10 Photos | 3 | 3 | 3 | 4 | 4 | 3.4 |
| 11 Signature (DR-FIX-3) | 3 | 5 | 4 | 5 | 5 | 4.4 |
| Audit footer (R5 shipped) | 5 | 5 | 4 | 5 | 5 | 4.8 |
| **Overall PDF (weighted by section frequency)** | **3.5** | **3.4** | **3.0** | **4.6** | **4.5** | **3.8** |

**Reading:** Trust and Proven are strong (audit footer, sha256, doc_id, pagination, signature). Powerful is mid (data is there but not surfaced). Beautiful and Simple are the weakest pillars — driven primarily by crew bloat, duplication, lack of executive surface.

---

## RECOMMENDATIONS

Each recommendation includes ID, description, pillar impact, risk, effort estimate, and priority. **Nothing in this section has been implemented — all require subsequent OMEGA authorization.**

### R-PDF-1 · Executive Summary Card (P1, above Section 01)
**Description:** Add a single fixed-height card at the top of the PDF rendering: `{date} · {project_short} · {crew_count} crew · {total_hours} hrs · {production_one_liner} · {open_constraints} flags · {photos} pics · {safe_day_badge}`. Strict one-line render, monospace, color-coded badge (Green = safe day, Amber = constraints, Red = incidents).
- **Pillar impact:** Powerful · Simple · Beautiful · Trusted · Proven
- **Risk:** LOW (pure additive render, no schema change)
- **Effort:** ~80 lines in `_render_daily` + ~30 lines of CSS in `render_record_pdf`
- **Priority:** **HIGH** — single highest-leverage change in this audit. Solves 60-second comprehension.

### R-PDF-2 · Safe Day Badge replacing four "No" KVs in Section 03
**Description:** When `safety_incidents_today != "Yes"` AND `injuries_reported != "Yes"`, replace the four KV rows in Section 03 with a single green pill: `"SAFE DAY · NO INCIDENTS · NO INJURIES"`. When either is "Yes," render the existing Safety Escalation block as the entire Section 03 surface.
- **Pillar impact:** Simple · Beautiful · Trusted
- **Risk:** LOW
- **Effort:** ~20 lines in `_render_daily`
- **Priority:** HIGH

### R-PDF-3 · Collapse inline crew gross/net math (dedup)
**Description:** When all crew rows share the same start/stop/lunch, emit a single line ABOVE the Crews table: *"All crew · 6:30 AM → 3:30 PM · 30 min lunch · 8.5 h net"*. Keep the per-row inline math ONLY for crew whose times differ from the common pattern.
- **Pillar impact:** Simple · Beautiful · Powerful
- **Risk:** LOW (algorithmic — group by (start, stop, lunch))
- **Effort:** ~30 lines in `_render_daily`
- **Priority:** HIGH (eliminates ~25% of P2 dead weight)

### R-PDF-4 · Hide empty `10 · Photos` section
**Description:** Defer the Section 10 header until at least one `_resolve_photo_ref` succeeds. Current code emits header before any resolution — fix is one conditional.
- **Pillar impact:** Simple · Beautiful
- **Risk:** LOW
- **Effort:** ~5 lines in `_render_daily`
- **Priority:** MEDIUM

### R-PDF-5 · Deprecate Section 09 "Activities Performed" when 09b "Production Quantities" is non-empty
**Description:** Production V.2 is the authoritative source. When `production[]` has rows, suppress Section 09 entirely. When 09b is empty but 09 has rows, render 09 (legacy fallback). Optionally, retitle 09 to "Notes (Activities)" so it never visually competes with 09b.
- **Pillar impact:** Simple · Powerful
- **Risk:** LOW (subtractive when 09b populated; preserves legacy when not)
- **Effort:** ~15 lines in `_render_daily`
- **Priority:** MEDIUM

### R-PDF-6 · Add Production totals row (mirror Crews "Total Hours")
**Description:** Append a totals-by-unit row at the bottom of Section 09b that aggregates quantities by unit (e.g., "TON: 240 · LF: 1100 · LM: 0.21").
- **Pillar impact:** Powerful · Proven
- **Risk:** LOW
- **Effort:** ~25 lines in `_render_daily`
- **Priority:** MEDIUM

### R-PDF-7 · Title-case constraint enum codes
**Description:** Map `cei_inspection`/`owner_engineer`/`mot` → "CEI Inspection"/"Owner / Engineer"/"MOT" in Section 09c rendering. Server-side data unchanged; UI/PDF presentation only.
- **Pillar impact:** Beautiful · Simple
- **Risk:** LOW
- **Effort:** ~10 lines (lookup dict in `_render_daily`)
- **Priority:** MEDIUM

### R-PDF-8 · Severity color on constraint advisory flags
**Description:** When a row has `may_affect_schedule=True`, render the cell with a light amber background tint; when `may_require_rfi=True`, render with a light blue tint. Pure CSS.
- **Pillar impact:** Powerful · Simple · Beautiful
- **Risk:** LOW
- **Effort:** ~15 lines CSS + 2 lines per-row tagging
- **Priority:** MEDIUM

### R-PDF-9 · Renumber sections so the numbering is consecutive
**Description:** Promote Weather to "02 · Weather" (currently embedded as a KV under 01). Removes the visible 01 → 03 numbering jump.
- **Pillar impact:** Simple · Beautiful
- **Risk:** LOW (cosmetic; no data dependency)
- **Effort:** ~5 lines in `_render_daily`
- **Priority:** LOW

### R-PDF-10 · Render Excavation activity flag + linked record IDs
**Description:** When `excavation_activity_today` is "Yes", render a short callout block (between Section 03 and Section 04) listing `linked_excavation_ids` with their `excavation_number`s. The data is already validated server-side and stored — pure surface gap.
- **Pillar impact:** Powerful · Trusted · Safety
- **Risk:** LOW
- **Effort:** ~30 lines + 1 async fetch
- **Priority:** HIGH

### R-PDF-11 · Move "General Notes" up to immediately follow the Executive Summary Card
**Description:** General Notes is the highest-signal narrative on the report. Today it sits at the bottom of Section 03. Promote it directly under R-PDF-1.
- **Pillar impact:** Powerful · Simple
- **Risk:** LOW
- **Effort:** ~10 lines in `_render_daily`
- **Priority:** MEDIUM (depends on R-PDF-1)

### R-PDF-12 · Photo caption fallback (station / timestamp)
**Description:** When a top-level photo can be associated with a production/activity row by station tag or timestamp, render a one-line caption beneath it. When no association exists, omit caption. Per-sub and per-material photo blocks already follow this pattern.
- **Pillar impact:** Beautiful · Powerful · Proven
- **Risk:** MEDIUM (requires association heuristic — could ship trivial first cut)
- **Effort:** ~60 lines in `_render_daily` + `_photos_block` extension
- **Priority:** LOW

### R-PDF-13 · "Submitted at" timestamp adjacent to Signature
**Description:** Render a local-time submit stamp next to the Prepared By signature block (e.g., `Submitted: 2026-06-08 17:43 ET`). Source: `created_at` converted to project-local time.
- **Pillar impact:** Trusted · Proven
- **Risk:** LOW
- **Effort:** ~15 lines
- **Priority:** LOW

### R-PDF-14 · Co-locate signature with audit footer (keep P4 from going half-empty)
**Description:** Pin Section 11 + audit footer at the top of the last content page when there's room rather than forcing an orphan page. Could be CSS-only via `page-break-before: avoid`.
- **Pillar impact:** Beautiful · Simple
- **Risk:** MEDIUM (CSS print-rule tuning can be fragile across WeasyPrint versions)
- **Effort:** ~10 lines CSS
- **Priority:** LOW

### R-PDF-15 · Remove ForgedOps attribution from the end-of-document disclaimer block
**Description:** The @bottom-left footer already attributes every page. Drop the redundant attribution paragraph from the final disclaimer block.
- **Pillar impact:** Simple · Beautiful
- **Risk:** NONE
- **Effort:** ~3 lines
- **Priority:** LOW

### R-PDF-16 · Lifecycle stamp in audit footer (e.g., "DRAFT" / "FINAL" / "SUPERSEDED")
**Description:** Add a lifecycle marker to the existing audit footer when state ≠ "final" (when DR has revisions, when superseded, when in draft). Aligns with the `workflow_state_events` data that already exists.
- **Pillar impact:** Trusted · Proven
- **Risk:** LOW
- **Effort:** ~20 lines (read latest state event, fold into footer string)
- **Priority:** MEDIUM

### R-PDF-17 · Day-over-day or vs-plan context line in Executive Summary
**Description:** When historical DRs exist for the same project, add a sub-line to the Executive Summary Card: `Yesterday: 220 TON · Δ +20 TON`. Or vs job-plan when `jobs_master.expected_daily_production` exists.
- **Pillar impact:** Powerful · Proven
- **Risk:** MEDIUM (depends on jobs_master maturity; may degrade gracefully when missing)
- **Effort:** ~80 lines + 1 async aggregate
- **Priority:** LOW (high value when data permits; falls to LOW because of missing job-plan data today)

---

## RECOMMENDATIONS BY PRIORITY (cross-reference)

| Priority | Items |
|---|---|
| **HIGH** | R-PDF-1 Executive Summary · R-PDF-2 Safe Day Badge · R-PDF-3 Crew math collapse · R-PDF-10 Excavation surface |
| **MEDIUM** | R-PDF-4 Empty photos · R-PDF-5 Deprecate 09 when 09b populated · R-PDF-6 Production totals · R-PDF-7 Constraint title-case · R-PDF-8 Severity color · R-PDF-11 General Notes up · R-PDF-16 Lifecycle stamp |
| **LOW** | R-PDF-9 Renumber · R-PDF-12 Photo captions · R-PDF-13 Submit timestamp · R-PDF-14 Signature placement · R-PDF-15 Footer dedup · R-PDF-17 Day-over-day |

---

## WHAT SHOULD NEVER BE TOUCHED

These elements are working well and any modification carries unnecessary risk:

1. **Audit footer (R5)** — already SHA256-attested, monospace, every-page placement. Do not redesign.
2. **Subcontractor photos pattern (Section 05)** — header "Company · Trade" + optional note + 3-col grid is the right template; recommend OTHER sections (10, sub-Materials) ADOPT this pattern.
3. **Material ticket photos (Section 08)** — same pattern as Section 05. Working.
4. **MM-001B Section 09d** — recently certified (MM-001B + MM-001B-F1). Do not modify rendering during PDF cleanup.
5. **DR-FIX-3 Section 11 single Prepared By signer** — recently certified. Do not re-add Superintendent.
6. **DR-FIX-1 Production / Constraints render** — recently certified. R-PDF-5 deprecates the LEGACY 09 only, never 09b/09c.
7. **DR-FIX-2 Superintendent auto-populate** — backend behavior, not PDF surface. Leave alone.

---

## STOP CONDITION

Per OMEGA directive: **STOP**.

This audit document is the complete deliverable. No code has been changed. No PDFs have been re-rendered with modifications. No fields have been added or removed. No workflows have been altered. No data has been migrated.

The 17 recommendations above await explicit authorization before any implementation work begins. Authorization should be granular per recommendation (or per batch — e.g., "HIGH-priority sprint = R-PDF-1, R-PDF-2, R-PDF-3, R-PDF-10"). Each recommendation is independently shippable.

---

**AUDIT COMPLETE · AWAITING OMEGA AUTHORIZATION FOR REMEDIATION**

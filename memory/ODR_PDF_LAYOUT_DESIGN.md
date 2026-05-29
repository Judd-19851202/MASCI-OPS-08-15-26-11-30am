# ODR PDF LAYOUT DESIGN

_Phase V.1 · Operational Daily Record · Architecture Artifact 4 of 5 · 2026-05-29_

The ODR PDF is the **legal, executive, and claims-ready artifact** of
a field day. It must be understandable in **≤ 3 minutes** by any of:
Executive Leadership · PM · Superintendent · CEI · Owner · FAA ·
FDOT · Attorney · Claims Analyst.

This document specifies the page-by-page layout, the typographic
contract, the footer doctrine, and the rendering strategy.

---

## 1 · Document-wide standards

| Property | Value |
|---|---|
| Page size | US Letter (8.5″ × 11″) |
| Margins | 0.5″ top / 0.5″ bottom / 0.6″ side |
| Body font | system-serif fallback (e.g., Source Serif) for the body; one sans (Inter or system) for tabular blocks |
| Body size | 10 pt body · 9 pt tabular · 14 pt section titles · 22 pt cover title |
| Color palette | navy primary (#0a1f44) · single red accent (#c0322a) used **only** for safety-event surfaces · neutral grays elsewhere |
| Single-red doctrine | At most one red surface visible on any one page |
| Footer | shared `operational_footer.render_operational_footer_html()` rendered as `wkhtmltopdf` chunk (existing module — same as PO / Safety digests) |
| Headers | running header on pages 2+: `ODR-2026-00427 · I-95 / SR-9 Widening · 2026-05-28 · Crew: PIPE · CR Reyes` |
| Page numbers | `Page 3 of 9` bottom-right |
| Signature blocks | last body page · Foreman + Superintendent + PM (when approved) |
| QR code | bottom-left of cover · resolves to the operator URL `https://mascidocs.com/o/odr/{doc_id}` for verifying authenticity |
| Single-footer invariant | enforced by `test_iter310_pdf_single_footer_invariant.py` — the existing PDF gate continues to apply |

---

## 2 · Page 1 · Executive Summary

```
┌────────────────────────────────────────────────────────────┐
│  MASCI   Operational Daily Record                          │
│          ODR-2026-00427                                    │
├────────────────────────────────────────────────────────────┤
│  Project   I-95 / SR-9 Widening (#43-217)                  │
│  Contract  E1S22                                           │
│  Date      Wednesday, May 28, 2026 · Day 47                │
│  Crew      Pipe · "Reyes Crew"  (Primary: Storm Pipe)      │
│  Foreman   Carlos Reyes  ·  Super: J. Murphy               │
│  PM        M. Ortiz      ·  Weather: 78°F partly cloudy    │
├────────────────────────────────────────────────────────────┤
│  ── Today at a glance ──                                   │
│   Manpower            8 / 8 expected · 81.5 h total         │
│   Equipment           5 assigned · 1 maintenance flag       │
│   Production          220 LF · 1 structure                  │
│   Delays              1 · 2.5 h lost (utility)              │
│   Extra Work          1 · est $4,200 · 0.5 day              │
│   Safety              No events                             │
│   Weather impact      None                                  │
│   Plan vs Actual      Completed ✓                           │
│                                                            │
│  ── 3-line narrative (PM-authored on review) ──             │
│   "Pipe crew installed 24" RCP between S-14 and S-16        │
│    despite FPL delay; structure S-15 set. CEI requested     │
│    additional connection at S-16; scope under review."      │
├────────────────────────────────────────────────────────────┤
│  ▢ QR · authenticity verify       Signed: Reyes · Murphy   │
└────────────────────────────────────────────────────────────┘
```

**Goal**: an executive or attorney can read just Page 1 and know
exactly what happened and where the risk is.

The "3-line narrative" is the only PM-authored block; it appears
once the ODR is **approved**. For `submitted` ODRs the narrative
slot reads "(awaiting PM review)".

---

## 3 · Page 2 · Labor / Equipment

```
┌────────────────────────────────────────────────────────────┐
│  Labor                                                      │
├──────────────────────────┬─────┬─────┬────────────────────┤
│  Employee                 │ Reg │  OT │  Role / Notes      │
├──────────────────────────┼─────┼─────┼────────────────────┤
│  Reyes, Carlos            │10.0 │ 0.0 │ Foreman            │
│  Murphy, J.               │ 9.5 │ 0.0 │ Operator           │
│  Webb, T.                 │10.0 │ 0.0 │ Laborer            │
│  Vance, K.                │ 8.0 │ 0.0 │ Operator           │
│  …                        │     │     │                    │
│  ── totals ──             │81.5 │ 0.0 │ 8 / 8 expected     │
└──────────────────────────┴─────┴─────┴────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Equipment                                                  │
├──────────────────┬─────┬─────┬──────┬─────────────────────┤
│  Asset            │ Run │Idle │ Down │  Maintenance        │
├──────────────────┼─────┼─────┼──────┼─────────────────────┤
│  Cat 320 #E-114   │ 8.5 │ 1.5 │  0.0 │ —                   │
│  JD 850K #E-088   │ 7.0 │ 2.0 │  1.0 │ Hydraulic leak ⚠    │
│                   │     │     │      │ → Shop #SH-1289     │
│  …                │     │     │      │                     │
└──────────────────┴─────┴─────┴──────┴─────────────────────┘
```

Tables use the existing PDF table style (calm gray rules, no neon
zebra). The Shop ticket id links the day to the maintenance trail
without duplicate entry.

---

## 4 · Page 3 · Production

Polymorphic body — driven by `crew_type`. Same typographic system
across all variants.

```
┌────────────────────────────────────────────────────────────┐
│  Production · Pipe                                          │
├──────────┬────────┬───────┬──────────┬──────────┬──────────┤
│ Run      │ Size   │ LF    │ From     │ To       │ Backfill │
├──────────┼────────┼───────┼──────────┼──────────┼──────────┤
│  1       │ 24"RCP │  220  │  S-14    │  S-16    │ #57      │
└──────────┴────────┴───────┴──────────┴──────────┴──────────┘

  Structures set today: S-15 (24" tee, 11:40)

  Testing: 1 pressure test · pass · 11:55
  Compaction: 98% (S-15 bedding)

  Photos: 4 (see Photo Appendix · tag = production)
```

For **paving**, the same page renders a Lift × Station-limits × Tons
× Mix matrix. For **MOT**, a Closure-event × Hours-active timeline.
For **other** crew types, the engine falls back to a key-value list.

---

## 5 · Page 4 · Delays / Constraints / Extra Work

```
┌────────────────────────────────────────────────────────────┐
│  Delays                                                     │
├────────────────────┬──────┬───────────────────────────────┤
│ Type                │ Hours│ Description                   │
├────────────────────┼──────┼───────────────────────────────┤
│ Utility             │ 2.5  │ FPL crew did not arrive on    │
│                     │      │ schedule. Photos · 2          │
└────────────────────┴──────┴───────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Constraints (today)                                        │
├────────────────────┬───────────────────────────────────────┤
│ Type                │ Description                            │
├────────────────────┼───────────────────────────────────────┤
│ Utility (recurring) │ FPL hand-off coordination · linked to  │
│                     │ operational_constraints OC-2026-0188   │
└────────────────────┴───────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Extra Work                                                 │
├────────────────────┬──────┬───────────┬───────────────────┤
│ Requested by        │ $ est│ Days est  │ Description       │
├────────────────────┼──────┼───────────┼───────────────────┤
│ M. Lopez (CEI)      │ 4,200│   0.5     │ Additional cnxn   │
│                     │      │           │ at S-16. Photos·2 │
└────────────────────┴──────┴───────────┴───────────────────┘
```

This is the **claims-protection page**. Attorneys and claims analysts
look here first.

---

## 6 · Page 5 · Safety / Weather

```
┌────────────────────────────────────────────────────────────┐
│  Safety today                                                │
├────────────────────────────────────────────────────────────┤
│  Accidents                ◯ No                              │
│  Incidents                ◯ No                              │
│  Near misses              ◯ No                              │
│  Property damage          ◯ No                              │
│  Environmental release    ◯ No                              │
│  Injuries                 ◯ No                              │
│                                                              │
│  Status: NO SAFETY EVENTS                                    │
└────────────────────────────────────────────────────────────┘
```

When any flag is `Yes`, this page becomes a richer surface with:

```
┌────────────────────────────────────────────────────────────┐
│  ⛔ Safety event — Near Miss (Incident · INC-2026-00188)     │
├────────────────────────────────────────────────────────────┤
│  Notified Safety: Yes · J. Vincent · 14:12 ET               │
│  Incident report complete: Yes · INC-2026-00188             │
│  Linked photos: see Photo Appendix · tag = safety           │
└────────────────────────────────────────────────────────────┘
```

The red accent appears here **only**, satisfying the single-red
doctrine page-wide.

Weather impact block (always present):

```
┌────────────────────────────────────────────────────────────┐
│  Weather impact                                              │
├────────────────────────────────────────────────────────────┤
│  Conditions    78°F partly cloudy · 6 mph W                 │
│  Sunrise/set   06:39 — 20:14                                │
│  Impacted work?  No                                          │
└────────────────────────────────────────────────────────────┘
```

---

## 7 · Pages 6+ · Photo Appendix

```
┌────────────────────────────────────────────────────────────┐
│  Photos · 9 today                                            │
├────────────────────────────────────────────────────────────┤
│  ┌──────┐  Production · S-15 tee installation               │
│  │ img  │  11:40 ET · 27.962, -82.120 ±3m                   │
│  └──────┘  "Setting structure"  — voice transcript          │
│                                                              │
│  ┌──────┐  Delay · FPL coordination                          │
│  │ img  │  10:21 ET                                          │
│  └──────┘                                                    │
│                                                              │
│  …                                                           │
└────────────────────────────────────────────────────────────┘
```

- Photos rendered **two per row** at 3" × 2.25" with caption block to
  the right.
- Section anchor printed beneath the caption (e.g., `delays.entry[0]`)
  so an attorney can find which event the photo belongs to.
- Voice transcripts appear in italics; original audio is referenced
  by `odr_photos.audio_object_key` (not embedded in the PDF).
- Photo governance Wave 1 contract enforced — each photo carries
  its `photo_governance_id` and a chain-of-custody footer block.

---

## 8 · Final page · Signatures + audit envelope

```
┌────────────────────────────────────────────────────────────┐
│  Authored by      Carlos Reyes       Submitted 18:11 ET     │
│  Reviewed by      J. Murphy          (Superintendent)       │
│  Approved by      M. Ortiz           (PM · 18:48 ET)        │
│                                                              │
│  Audit envelope                                              │
│    ODR id:         a1c4-…-2188                              │
│    doc_id:         ODR-2026-00427                            │
│    schema_version: 1                                         │
│    created_at:     2026-05-28T22:14:11Z                      │
│    submitted_at:   2026-05-28T22:11:43Z                      │
│    location:       27.96198, -82.12041 · ±3.2 m              │
│    SHA-256 of payload: 9a4c…f127                             │
└────────────────────────────────────────────────────────────┘
```

The SHA-256 + QR code combination make the PDF verifiable: any
auditor can hit `/api/odr/{id}/verify` with the SHA they hold and
confirm the payload matches.

---

## 9 · Rendering strategy

| Concern | Choice |
|---|---|
| HTML → PDF engine | `wkhtmltopdf` (existing pipeline in `backend/pdf_render.py` — proven, single-footer-tested) |
| Templating | Jinja2 — one master `odr.html.j2` + 6 partials (one per page kind) |
| Asset storage | photo bytes stay in R2; the renderer downloads to a temp dir per render |
| Cache | rendered PDFs cached under `R2:odr-pdf/{doc_id}.pdf` with cache-bust on any `submitted_at`/`review` change |
| Concurrency | one renderer worker per request; long-running renders push to a queue |
| Failure | partial PDFs are NEVER cached; renderer returns 500 if any section fails |
| Single-footer invariant | enforced by existing test `test_iter310_pdf_single_footer_invariant.py` |
| Audit | rendering writes one row to `odr_section_events` (`event="pdf_rendered"`, `bytes_size`, `sha256`) |

---

## 10 · Variants

| Variant | When used | What changes |
|---|---|---|
| `executive` | default | Pages 1–5 + photo appendix (all pages) |
| `claims_only` | claims package | Page 1 + Page 4 + Page 5 + photo appendix tagged `delay/extra_work/safety` |
| `cei_packet` | CEI weekly | Page 1–3 only · no claims surfaces · no costs |
| `fdot_owner` | regulatory submission | Pages 1–5 + photo appendix · with SHA + QR footer reinforced |
| `attorney_full` | litigation hold | every page + audit envelope expanded · `odr_section_events` rows appended |

Variant selector is a query string on the render endpoint:
`GET /api/odr/{id}/pdf?variant=claims_only`.

---

## 11 · Three-minute readability test (the doctrine ask)

A reviewer is expected to absorb the day in this order:

1. **Page 1, "Today at a glance"** — 30 seconds. The reviewer
   knows: was anything bad, did the crew make production, was the
   plan met.
2. **Page 4** — 60 seconds. Where the dollars and days are.
3. **Page 5** — 30 seconds. Any safety event.
4. **Photos** — 60 seconds for the relevant tag.

Total: ~3 minutes. The PDF is **structured to be skimmed**, not
read. No marketing copy. No celebratory chrome. Calm typography.

---

## 12 · Open PDF questions for operator review

1. Should the cover include the operator's photograph (foreman)?
   (Default: no — name only, in keeping with operational tone.)
2. Should the SHA + QR appear on every page footer or only on the
   cover and audit envelope? (Default: cover + audit envelope.)
3. Should weather impact block always appear on Page 5, or move to
   Page 1 when impact = Yes? (Default: always on Page 5; surface
   impact-occurred indicator on Page 1.)
4. Should the photo appendix include audio QR codes (link to the
   original voice file) for attorney review? (Default: yes —
   small QR beneath the photo when a voice caption is attached.)
5. Should the PDF embed the entire ODR JSON in a hidden XMP
   metadata block for forensic verification? (Default: yes — small
   payload, opaque to readers, machine-verifiable.)

Awaiting operator decisions before implementation.

---

_Artifact 4 of 5 · proceed to ODR_MIGRATION_PLAN.md_

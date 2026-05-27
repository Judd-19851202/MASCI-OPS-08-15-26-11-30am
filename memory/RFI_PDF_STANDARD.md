# RFI PDF Standard
## Phase V.0 · Architecture & Governance · 2026-05-27

> Visual + structural specification for every RFI PDF produced by
> MASCI Ops. DOT / FAA / CEI-ready. Doctrine-locked.

---

## 1 · Why PDFs Matter

The PDF is the **legal artifact**. Field workflows are mobile-first,
but disputes, audits, and external collaboration use the PDF as the
canonical record. The PDF must:

- Read cleanly on letter-size print.
- Read cleanly in Adobe Reader, Preview, browser PDF viewers.
- Survive black-and-white photocopying.
- Carry every piece of metadata an auditor or claim reviewer expects.
- Look unmistakably like MASCI Ops — not generic.

---

## 2 · Page Format

| Property | Value |
|---|---|
| Page size | US Letter (8.5" × 11") |
| Margins | 0.75" all sides |
| Body font | Inter or system sans, 10pt |
| Section heading font | Inter Bold, 12pt |
| Page header / footer font | Inter Mono, 8pt |
| Color | Monochrome body · cyan-700 accent for header rule · red-700 for severity badges ONLY when severity is critical-path or safety/compliance exposure |
| Print safety | All text must remain legible if printed grayscale |

---

## 3 · Required Sections (in order)

```
┌────────────────────────────────────────────────────────────────┐
│ 1 · HEADER BAND                                                │
│   MASCI logo  |  Project name + contract #  |  RFI # · Rev N   │
│   ─────────── cyan-700 rule ─────────────────                 │
├────────────────────────────────────────────────────────────────┤
│ 2 · PROJECT INFO BLOCK                                         │
│   Project name · Contract # · Owner · Engineer · CEI · PM      │
│   Discipline · Station/Offset · Plan sheet refs · Spec refs    │
│   Pay item refs                                                │
├────────────────────────────────────────────────────────────────┤
│ 3 · RFI METADATA BLOCK                                         │
│   Status · Priority · Submitted by · Submitted at              │
│   Response due · Assigned reviewer · Recipients                │
├────────────────────────────────────────────────────────────────┤
│ 4 · FIELD CONDITION                                            │
│   Operational description of the field state                   │
├────────────────────────────────────────────────────────────────┤
│ 5 · CONTRACTOR QUESTION                                        │
│   The specific clarification being requested                   │
├────────────────────────────────────────────────────────────────┤
│ 6 · PLAN / SPEC / PAY-ITEM REFERENCES                          │
│   Cited references, page #s, sheet #s                          │
├────────────────────────────────────────────────────────────────┤
│ 7 · PROPOSED SOLUTION                                          │
│   Contractor's preferred resolution (if any)                   │
├────────────────────────────────────────────────────────────────┤
│ 8 · IMPACT ASSESSMENT                                          │
│   Schedule impact  | Cost impact | Safety impact               │
│   MOT impact       | FAA operational impact                    │
├────────────────────────────────────────────────────────────────┤
│ 9 · PHOTOS                                                     │
│   Captioned. Geotagged when available.                         │
├────────────────────────────────────────────────────────────────┤
│ 10 · ATTACHMENTS                                               │
│   Document inventory · filename · sha256 first 12 chars         │
├────────────────────────────────────────────────────────────────┤
│ 11 · RESPONSE SECTION                                          │
│   External response body · responder · responded_at            │
│   Distribution list                                            │
├────────────────────────────────────────────────────────────────┤
│ 12 · DISTRIBUTION LOG                                          │
│   Every recipient · token id (last 8) · opens · downloads     │
│   responses · timestamps                                       │
├────────────────────────────────────────────────────────────────┤
│ 13 · REVISION HISTORY                                          │
│   Chain of revisions with deltas                               │
└────────────────────────────────────────────────────────────────┘
            ─── footer rule ───
  Page X of Y · MASCI Ops · Document ID · sha256 first 12 · Generated UTC
```

---

## 4 · Header / Footer Rules

- **Every page** carries: project · contract · RFI # · revision # · page X of Y.
- **Footer** carries: document ID · sha256 first 12 chars of body · generated UTC.
- Revision PDFs carry a watermark: `REVISION N · supersedes Rev N-1` in 14pt cyan-700 across the top-right corner.
- Voided PDFs carry a diagonal watermark: `VOIDED · <reason · truncated>` in red-700 at 25% opacity.
- Severity escalation (critical-path / safety exposure): a 4pt red-700 left rule on page 1, **never** on every page.

---

## 5 · Field Density Discipline

- Body sections allow free text but the renderer enforces:
  - Max 4 photos per page (grid of 2 × 2).
  - Photos auto-scaled with 4:3 aspect ratio.
  - Attachment list paginates cleanly (no orphan rows).
  - Tables use 1pt slate-300 rules — no heavy borders.
- White space is doctrine: at least 0.5" between sections. The PDF
  must feel calm, not cramped.

---

## 6 · Severity Pills (the ONE place red is allowed)

| Pill | Color | When |
|---|---|---|
| Routine | slate-500 outline | default |
| Action Required | amber-600 outline | priority elevated |
| Critical Path Impact | red-700 fill | PM-confirmed CP impact |
| Safety / Compliance Exposure | red-700 fill | safety-confirmed exposure |

One pill per RFI. Severity escalation requires PM (and Safety, when
applicable) confirmation. The audit trail records the actor who
elevated severity.

---

## 7 · Internationalization

PDFs render in English by default. If the project flag has Spanish
enabled and the recipient is internal, a parallel Spanish edition can
be requested. External PDFs render in the language of the recipient's
RFI distribution preference (English default). Translation discipline
follows the existing BILINGUAL_OPERATIONAL_MEANING_AUDIT rules.

---

## 8 · Content-Addressable Hash

Every PDF is fingerprinted by sha256 of its rendered content. The
first 12 chars appear in the footer. This lets:

- Auditors verify a printed PDF matches the live record.
- Disputes cite an exact PDF.
- Restore drills confirm content integrity.

If a regenerated PDF would carry the **same** hash as a prior PDF for
the same revision, the new file is not written — the existing file is
referenced (idempotent regeneration).

---

## 9 · Branding Discipline

- Logo: existing `MasciLogo` mark · top-left of header band.
- Logo never appears in body sections.
- No marketing language. No "we're proud to deliver" boilerplate.
- No QR codes inside the PDF unless the recipient requested one.

---

## 10 · Renderer

V.1 renderer should reuse the existing `pdf_render.py` discipline (the
same library that already renders training packets, welcome letters,
ops manual, field-leadership PDFs). No new dependency. No new font
license. Same tool, new template.

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Renderer lands in V.1. Layout locked here.

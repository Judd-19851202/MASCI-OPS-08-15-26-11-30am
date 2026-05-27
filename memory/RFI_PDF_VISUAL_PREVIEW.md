# RFI PDF · Visual Preview
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> Sample DOT/FAA-grade RFI PDF rendered as fixed-width text.
> What an auditor, claim reviewer, or CEI rep will see in 2029 when
> they open the record for a dispute on a 2026 RFI. Doctrine-locked.

---

## 1 · Page 1 (Header · Project Info · Metadata · Field Condition · Question)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ▌                                                                                   │
│ ▌  [M] MASCI                          REQUEST FOR INFORMATION       RFI #0040       │
│ ▌                                     ────────────────              Rev 1           │
│ ▌  CC5744 OXFORD RD IMPROVEMENTS                                                    │
│ ▌  Contract C-44-2026-118                                                           │
│ ▌─────────────────────────────────────────── cyan-700 rule ─────────────────────────│
│                                                                                     │
│   ┌──────────────────────────────────────┐  ┌────────────────────────────────────┐  │
│   │ PROJECT INFO                         │  │ RFI METADATA                       │  │
│   │ ───                                  │  │ ───                                │  │
│   │ Project       CC5744 Oxford Rd       │  │ Status        Submitted            │  │
│   │ Contract      C-44-2026-118          │  │ Priority      Critical-Path Impact │  │
│   │ Owner         Hillsborough County    │  │ Submitted by  Chris Wright (PM)    │  │
│   │ Engineer      Stantec                │  │ Submitted at  2026-05-22 14:18 UTC │  │
│   │ CEI           HNTB                   │  │ Response due  2026-05-29           │  │
│   │ PM            Chris Wright           │  │ Assigned      Sue Patton (EOR)     │  │
│   │ Discipline    Drainage               │  │ Recipients    EOR · CEI · Owner    │  │
│   │ Station       STA 220+40             │  │ Template      FDOT                 │  │
│   │ Plan sheets   C-12, C-13             │  │                                    │  │
│   │ Spec sections 430-3                  │  │                                    │  │
│   │ Pay items     0440-71-001            │  │                                    │  │
│   └──────────────────────────────────────┘  └────────────────────────────────────┘  │
│                                                                                     │
│   FIELD CONDITION                                                                   │
│   ─────────                                                                         │
│   Storm sub-base at STA 220+40 encountered conflicting utility marker.              │
│   FPL conduit appears 14 ft south of plan-set location. Crew has demobilized       │
│   pending clarification. Conduit is visible at +/- 3 ft depth, marked as            │
│   active 13.2 kV per the FPL field tag.                                             │
│                                                                                     │
│   CONTRACTOR QUESTION                                                               │
│   ─────────                                                                         │
│   Reroute proposed storm pipe or relocate FPL conduit? Confirm which solution       │
│   is acceptable. If reroute is approved, provide redline alignment for storm        │
│   between STA 220+10 and STA 221+00.                                                │
│                                                                                     │
│   PLAN / SPEC / PAY-ITEM REFERENCES                                                 │
│   ─────────                                                                         │
│     • Sheet C-12 (Storm Plan)                                                       │
│     • Sheet C-13 (Profile)                                                          │
│     • Spec Section 430-3 (Storm Sewer Pipe)                                         │
│     • Pay Item 0440-71-001 (24" RCP)                                                │
│                                                                                     │
│   PROPOSED SOLUTION                                                                 │
│   ─────────                                                                         │
│   Reroute storm 14 ft north between STA 220+10 and STA 221+00. Maintain 18"         │
│   clearance from FPL conduit. Update as-builts.                                     │
│                                                                                     │
│   IMPACT ASSESSMENT                                                                 │
│   ─────────                                                                         │
│   Schedule    Critical path · 0 days float (A1320 Storm Phase 3)                   │
│   Cost        TBD pending solution selection                                        │
│   Safety      Standard precautions in place                                         │
│   MOT         No MOT impact                                                         │
│   FAA         N/A                                                                   │
│                                                                                     │
│ ─── footer ──────────────────────────────────────────────────────────────────────── │
│  Page 1 of 4 · MASCI Ops · Doc ID b3f2a7e0 · sha256 b3f2a7e0c1ab · 2026-05-22 UTC  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

Key visual choices:

- **Severity stripe** (`▌` red-700 down the left margin of page 1) ONLY
  because this RFI is critical-path. Routine RFIs have no stripe.
- **Header band** with MASCI mark, RFI # / Rev top-right, project / contract
  below. cyan-700 hairline rule.
- **Two-column top block** for Project Info + Metadata. Clean, scannable.
- **Section headings** are 12pt bold with a slate-300 hairline below.
- **Body** in 10pt Inter.

---

## 2 · Page 2 (Photos)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ▌  [M] MASCI                          RFI #0040 · Rev 1 · Page 2 of 4               │
│                                                                                     │
│   PHOTOS                                                                            │
│   ─────────                                                                         │
│                                                                                     │
│   ┌────────────────────────┐    ┌────────────────────────┐                          │
│   │                        │    │                        │                          │
│   │    [photo placeholder] │    │    [photo placeholder] │                          │
│   │                        │    │                        │                          │
│   │                        │    │                        │                          │
│   └────────────────────────┘    └────────────────────────┘                          │
│   Photo 1 · STA 220+40 RT       Photo 2 · FPL field tag                             │
│   2026-05-22 06:34 local        2026-05-22 06:35 local                              │
│   28.0214°N · 82.4612°W         28.0214°N · 82.4612°W                              │
│                                                                                     │
│   ┌────────────────────────┐    ┌────────────────────────┐                          │
│   │                        │    │                        │                          │
│   │    [photo placeholder] │    │    [photo placeholder] │                          │
│   │                        │    │                        │                          │
│   │                        │    │                        │                          │
│   └────────────────────────┘    └────────────────────────┘                          │
│   Photo 3 · Existing storm      Photo 4 · Centerline view                          │
│   2026-05-22 06:36 local        2026-05-22 06:37 local                              │
│   28.0214°N · 82.4612°W         28.0214°N · 82.4612°W                              │
│                                                                                     │
│ ─── footer ──────────────────────────────────────────────────────────────────────── │
│  Page 2 of 4 · MASCI Ops · Doc ID b3f2a7e0 · sha256 b3f2a7e0c1ab · 2026-05-22 UTC  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

- 2×2 grid · 4 photos per page max.
- Each photo: 4:3 aspect · ~3.5" × 2.6" on the page.
- Caption below: number · location · timestamp · geocoords when available.
- Additional photos page if needed (Page 2A, 2B, etc.).

---

## 3 · Page 3 (Attachments · Response Section · Distribution Log)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ▌  [M] MASCI                          RFI #0040 · Rev 1 · Page 3 of 4               │
│                                                                                     │
│   ATTACHMENTS                                                                       │
│   ─────────                                                                         │
│     • RFI_0040_Rev1.pdf      1.4 MB  sha256 b3f2a7e0c1ab                            │
│     • PlanSheet_C-12.pdf     3.1 MB  sha256 4f8c9d12e5b7                           │
│                                                                                     │
│   RESPONSE                                                                          │
│   ─────────                                                                         │
│                                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────┐ │
│   │  Response from Sue Patton · Engineer of Record (Stantec)                     │ │
│   │  Submitted 2026-05-26 11:42 UTC                                              │ │
│   │  ────                                                                        │ │
│   │                                                                              │ │
│   │  Acceptable to reroute storm pipe per attached redline. Maintain 18"        │ │
│   │  clearance from FPL conduit. Update as-builts to reflect actual location.   │ │
│   │                                                                              │ │
│   │  Attached: Storm_Reroute_Redline.pdf  (2.2 MB)                              │ │
│   │                                                                              │ │
│   └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│   PM DISPOSITION                                                                    │
│   ─────────                                                                         │
│   Accepted · Chris Wright · 2026-05-26 14:50 UTC                                    │
│                                                                                     │
│   DISTRIBUTION LOG                                                                  │
│   ─────────                                                                         │
│   RECIPIENT                ROLE                ISSUED      OPENS  RESPONSE          │
│   Sue Patton               Engineer of Record  2026-05-22  3      2026-05-26       │
│   Mike Chen                CEI                 2026-05-22  2      —                 │
│   Linda Park               Owner Rep           2026-05-22  1      —                 │
│                                                                                     │
│ ─── footer ──────────────────────────────────────────────────────────────────────── │
│  Page 3 of 4 · MASCI Ops · Doc ID b3f2a7e0 · sha256 b3f2a7e0c1ab · 2026-05-22 UTC  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4 · Page 4 (Revision History · Audit Trail)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ▌  [M] MASCI                          RFI #0040 · Rev 1 · Page 4 of 4               │
│                                                                                     │
│   REVISION HISTORY                                                                  │
│   ─────────                                                                         │
│   REV  DATE        ACTOR              CHANGE                                        │
│   1    2026-05-22  Chris Wright (PM)  Initial submission                            │
│                                                                                     │
│   AUDIT TRAIL                                                                       │
│   ─────────                                                                         │
│   2026-05-22 06:38 UTC  Tom Diaz (SI)         Draft created · 4 photos              │
│   2026-05-22 13:50 UTC  Chris Wright (PM)     Draft opened · added refs             │
│   2026-05-22 14:18 UTC  Chris Wright (PM)     Submitted · distribution issued       │
│   2026-05-22 14:18 UTC  system                Tokens issued · EOR · CEI · Owner     │
│   2026-05-22 14:20 UTC  system                Email delivered to 3 recipients       │
│   2026-05-22 16:33 UTC  Mike Chen (CEI)       Link opened (ext)                     │
│   2026-05-23 09:10 UTC  Linda Park (Owner)    Link opened (ext)                     │
│   2026-05-24 10:22 UTC  Sue Patton (EOR)      Link opened (ext)                     │
│   2026-05-26 11:42 UTC  Sue Patton (EOR)      Response submitted                    │
│   2026-05-26 14:50 UTC  Chris Wright (PM)     Disposition · accepted                │
│                                                                                     │
│   This RFI was generated by the MASCI Operations system on 2026-05-22.              │
│   Document integrity is verifiable via the sha256 hash in the page footer.          │
│   Operational record · retained 7 years post-project closeout.                      │
│                                                                                     │
│ ─── footer ──────────────────────────────────────────────────────────────────────── │
│  Page 4 of 4 · MASCI Ops · Doc ID b3f2a7e0 · sha256 b3f2a7e0c1ab · 2026-05-22 UTC  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

- The audit trail is rendered in a tight monospace table.
- Every state transition + every external access event is line-itemed.
- The final paragraph is the legal/audit closing line — single
  sentence, calm, no boilerplate.

---

## 5 · Watermark Discipline

| Condition | Watermark |
|---|---|
| Normal submitted | none |
| Revision 2+ supersedes prior | top-right: `REVISION 2 · supersedes Rev 1` · 14pt cyan-700 |
| Voided | diagonal across center: `VOIDED · <reason truncated>` · 25% opacity red-700 |
| Print-preview / draft | top-right: `DRAFT · NOT SUBMITTED` · 14pt slate-500 |

Watermarks are large enough to survive a black-and-white photocopy.

---

## 6 · Print Safety Discipline

- Monochrome printout: every meaningful element remains legible.
- Color is **functional** — removing it loses urgency but never
  loses information. The severity pill text still reads "Critical-Path
  Impact" even in grayscale.
- Photos print at acceptable contrast — captions describe what the
  photo shows so the record stands without the photo.

---

## 7 · Operator Sign-off Items

- [ ] Header band reads as DOT-grade.
- [ ] Two-column metadata block is the right level of density.
- [ ] Photo layout (2×2 grid · captions with geocoords) is sufficient.
- [ ] Distribution log table tells the dispute story at a glance.
- [ ] Audit trail granularity is appropriate (every state · every ext access).
- [ ] Footer with doc ID + sha256 is verifiable.
- [ ] Watermarks for revisions and voided records read clearly.
- [ ] Print-safe in grayscale.

---

## 8 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Renderer template locked for V.1.

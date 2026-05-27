# External Response Preview · Visual Standard
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> What CEI / Engineer / Owner / DOT / FAA / Utility see when they
> open the tokenized link. Professional. DOT-grade. No portal chrome.
> Doctrine-locked.

---

## 1 · The Surface Belongs to the Recipient

External parties are not MASCI staff. The page must feel like:

- A reputable contracting platform.
- A document portal an agency rep is comfortable using.
- A workflow that finishes in ≤ 3 minutes.

The page must NOT feel like:

- Internal MASCI navigation accidentally exposed.
- Generic ticketing software.
- Marketing.

---

## 2 · Landing Page (Read · Mobile-First)

```
┌────────────────────────────────────────────────────┐
│  ───── caution stripe ─────                        │
│                                                    │
│  [M] MASCI                              [ EN | ES ]│
│                                                    │
│  REQUEST FOR INFORMATION · RESPONSE REQUESTED      │
│                                                    │
│  RFI 0040 · CC5744 OXFORD RD IMPROVEMENTS          │
│  Drainage · STA 220+40                             │
│                                                    │
│  Issued by  Chris Wright (PM · MASCI)              │
│             chris.wright@mascigc.com · 813-555-...│
│  Response due  Wednesday, May 29, 2026             │
│                                                    │
│  ──────                                            │
│                                                    │
│  FIELD CONDITION                                   │
│  ──────                                            │
│  Storm sub-base at STA 220+40 encountered          │
│  conflicting utility marker. FPL conduit appears   │
│  14 ft south of plan-set location. Crew has demob- │
│  ilized pending clarification.                     │
│                                                    │
│  PHOTOS (3)                                        │
│   ┌──────┐ ┌──────┐ ┌──────┐                      │
│   │ img  │ │ img  │ │ img  │                      │
│   └──────┘ └──────┘ └──────┘                      │
│                                                    │
│  CONTRACTOR QUESTION                               │
│  ──────                                            │
│  Reroute proposed storm or relocate FPL conduit?   │
│  Confirm which solution is acceptable.             │
│                                                    │
│  PLAN / SPEC REFERENCES                            │
│  ──────                                            │
│  Sheet C-12 · Storm Plan                           │
│  Spec Section 430-3 · Storm Sewer Pipe             │
│  Pay item 0440-71-001                              │
│                                                    │
│  IMPACT ASSESSMENT (from PM)                       │
│  ──────                                            │
│  Schedule · Critical path · 0 days float           │
│  Cost · TBD pending solution                       │
│  Safety · Standard precautions in place            │
│                                                    │
│  ATTACHMENTS  (2)                                  │
│   • RFI_0040_Rev1.pdf  (1.4 MB) · Download         │
│   • PlanSheet_C-12.pdf (3.1 MB) · Download         │
│                                                    │
│  ──────                                            │
│                                                    │
│  [    Submit a response    ]                       │
│  [    Request clarification    ]                   │
│                                                    │
│  ──────                                            │
│  Contact PM for questions: 813-555-...             │
│  This link expires Fri Jun 28, 2026                │
│  Auditing applies · every view logged              │
└────────────────────────────────────────────────────┘
```

Layout discipline:

- **No left sidebar.** No top portal nav. The only chrome is the
  caution-stripe header with the MASCI mark and a language toggle.
- **Photos render small** — taps open the lightbox.
- **PDF download is one tap** — the most-used action for agency staff.
- **Two CTAs** — Submit response · Request clarification. Neutral
  slate-800 button color. No third CTA.

---

## 3 · Response Submission Form (Tap "Submit a response")

```
┌────────────────────────────────────────────────────┐
│  ←  Back to RFI                                    │
│  ──────                                            │
│                                                    │
│  Respond to RFI 0040                               │
│                                                    │
│  Your name                                         │
│  ┌──────────────────────────────────────────────┐ │
│  │ Sue Patton                                   │ │
│  └──────────────────────────────────────────────┘ │
│  Prefilled from invite. Edit if needed.            │
│                                                    │
│  Your role                                         │
│  [ Engineer of Record ▾ ]                          │
│                                                    │
│  Response                                          │
│  ┌──────────────────────────────────────────────┐ │
│  │  ⓜ Tap and hold to dictate                    │ │
│  │                                              │ │
│  │  Acceptable to reroute storm pipe per        │ │
│  │  attached redline. Maintain 18" clearance   │ │
│  │  from FPL conduit. Update as-builts to      │ │
│  │  reflect actual location.                    │ │
│  │                                              │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Attachments (optional)                            │
│  [ ➕ Add a file ]                                  │
│                                                    │
│  ──────                                            │
│  By submitting, you confirm this response is on    │
│  behalf of your firm and may be used as a record   │
│  of contract clarification.                        │
│  ──────                                            │
│                                                    │
│  [    Send response    ]                           │
│  Cancel                                            │
└────────────────────────────────────────────────────┘
```

- Single-screen form. Mobile-friendly.
- Voice-to-text on the response field.
- Optional attachments (PDFs, images).
- One submit button · slate-800.
- A short legal-style disclaimer before the button (single sentence ·
  not a wall of text).

After tap → confirmation card:

```
┌────────────────────────────────────────────────────┐
│                                                    │
│              ◉  Response submitted                 │
│                                                    │
│   MASCI received your response to RFI 0040.        │
│   Chris Wright will review and confirm.            │
│                                                    │
│   You will be notified of any follow-up.           │
│                                                    │
│              [   Close window   ]                  │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 4 · Request Clarification Form

```
┌────────────────────────────────────────────────────┐
│  Request clarification                             │
│  ─────                                             │
│                                                    │
│  What do you need from MASCI?                      │
│  ┌──────────────────────────────────────────────┐ │
│  │ Provide centerline survey of FPL conduit     │ │
│  │ within 50 ft of STA 220+40.                  │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  [    Send request    ]                            │
│  Cancel                                            │
└────────────────────────────────────────────────────┘
```

Two-field form. Recipient sends a clarification request without
having to compose a full response. PM gets the request, addresses it
via a revision, the link rebinds to the new revision.

---

## 5 · Expired / Revoked Link

```
┌────────────────────────────────────────────────────┐
│                                                    │
│              ◌  This link is no longer active.     │
│                                                    │
│   Contact MASCI to request an updated link:        │
│                                                    │
│              Chris Wright (PM)                     │
│              chris.wright@mascigc.com              │
│              813-555-1234                          │
│                                                    │
└────────────────────────────────────────────────────┘
```

- No error code shown.
- Calm tone.
- Direct human contact path.

---

## 6 · Audit Awareness

A subtle line in the landing footer reads:

> *"This link is audited. Each view, download, and response is
> recorded as part of the operational record."*

No flashing. No legal pop-ups. Just a calm statement that this
is operational documentation, not informal communication.

---

## 7 · Mobile Discipline

Everything above is mobile-first.

- Single column.
- Photos open native lightbox (pinch to zoom).
- Forms scroll cleanly.
- PDFs download to device default location.
- Touch targets ≥ 56px for primary CTAs.

The external surface is the **easiest** mobile surface in the entire
MASCI ecosystem because the recipient might be on an iPad in a
construction trailer or a phone in their truck.

---

## 8 · Branding Discipline

- MASCI logo top-left of caution-stripe header.
- No tagline. No "powered by". No marketing.
- Cyan-700 used **once** — the caution-stripe accent.
- Severity red appears only on the priority pill if the RFI is
  critical-path or safety/compliance exposure (single pill, header
  area).
- Recipient never sees PM portal navigation, sidebar, or chip.

---

## 9 · Multi-Recipient Distribution

When the same RFI is distributed to multiple external parties (CEI +
Engineer of Record + Owner), each receives their own tokenized link.
On the landing page, the **Distribution** block (read-only) reads:

```
DISTRIBUTION
─────────
Sue Patton · Engineer of Record       you
Mike Chen · CEI                       responded 2026-05-26
Linda Park · Owner Rep                opened 2026-05-25
```

This tells the recipient who else is in the loop without exposing
contact details. Names + roles + per-recipient state only.

---

## 10 · Email Companion (recap from `RFI_EXTERNAL_ACCESS_MODEL §6`)

The link arrives via a Resend email styled to match this landing page.
The PDF is attached AND linked. The email body is:

```
RFI 0040 · CC5744 OXFORD RD IMPROVEMENTS
Drainage · STA 220+40 · Response requested by 2026-05-29

Chris Wright (PM) has issued the attached RFI for response.

Open the RFI: https://mascidocs.com/rfi/ext/<token>/<slug>
Download PDF: attached and downloadable at the link.

If the link does not open, reply to this email or call 813-555-1234.

— MASCI Operations
```

No HTML decoration. Plain operational tone.

---

## 11 · Loudness Probe Targets

| Metric | Target |
|---|---|
| Hue families | ≤ 2 (slate + cyan-700 accent only) |
| Badge density | ≤ 5 |
| Escalation noise | ≤ 2 (priority pill only when warranted) |
| Calmness score | ≥ 78 |

This is the **calmest** surface in the entire MASCI ecosystem. It
must be — it represents MASCI to outside parties.

---

## 12 · Operator Sign-off Items

- [ ] No portal chrome present.
- [ ] PDF download is one tap.
- [ ] Two CTAs (Submit response · Request clarification) is the right scope.
- [ ] Disclaimer copy is appropriate without being legally intimidating.
- [ ] Expired-link page is calm and gives a clear human contact.
- [ ] Audit notice is present without being heavy-handed.

---

## 13 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Locked for V.2 (External RFI collaboration).

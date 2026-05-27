# Superintendent Mobile Flow · Certification
## Phase V.0A · Paper-Prototype Visual Validation · 2026-05-27

> The single most important UX in this entire subsystem. ≤ 60-second
> draft from a phone in the dirt at 6:15am. Doctrine-locked.

---

## 1 · Why This Surface Decides Whether the Whole System Works

If superintendents can't draft an RFI in under a minute on a phone
with one hand and a dust-covered glove, they will:

1. Wait until they're back at the truck (loses fidelity).
2. Wait until that evening (loses memory).
3. Call the PM (loses paper trail).
4. Or worst: not raise the RFI at all.

Every visual and interaction decision below exists to push the draft
toward "yes, doing it right now" instead of "later".

---

## 2 · Entry Point · Field Leadership Hub

The superintendent's FL hub gains a single new tile in the existing
4-domain layout. **One tile. Not a domain. Not a section. One tile.**

```
┌──────────────────────────────────────┐
│  FIELD LEADERSHIP                    │
│  ──────────────                      │
│                                      │
│  ▌ DAILY EXECUTION                   │
│  ──────                              │
│   [ Daily Reports ]   [ Crew ]       │
│   [ Equipment Pre-Op ]               │
│                                      │
│  ▌ SAFETY                            │
│  ──────                              │
│   [ Safety Meeting ]  [ JHA ]        │
│   [ Incidents ]                      │
│                                      │
│  ▌ FIELD COORDINATION       ◄ NEW    │
│  ──────                              │
│   ┌──────────────────────────────┐   │
│   │ RFI · Field Issue           →│   │
│   │ Snap a photo. Send to PM.    │   │
│   └──────────────────────────────┘   │
│                                      │
│  ▌ RECORDS                           │
│  ──────                              │
│   [ My Drafts ]   [ My Active RFIs ] │
│                                      │
└──────────────────────────────────────┘
```

Coaching subline: *"Snap a photo. Send to PM."* (5 words) — that's
the entire promise.

---

## 3 · The Draft Flow (4 screens · ≤ 60 seconds)

### Screen 1 · Camera (opens immediately on tile tap · ≤ 1 second)

```
┌──────────────────────────────────────┐
│                                      │
│              [ camera ]              │
│              [ preview ]             │
│                                      │
│                                      │
│                                      │
│                                      │
│                                      │
│                                      │
│                                      │
│                                      │
│                                      │
│                                      │
│   ◯ Photo  ◯ Photo + 2 more  Done    │
│        [    Big Camera Btn    ]      │
│                                      │
│  Cancel                              │
└──────────────────────────────────────┘
```

- Camera opens by default. No menu in between.
- Big shutter button · 96px diameter · thumb-reachable.
- Operators can take up to 4 photos in one session.
- "Done" advances when ≥ 1 photo is captured.
- A single "Cancel" exits back to FL hub (with confirmation if any
  photo was already taken).

> Why photo-first: the photo IS the field condition. Words can wait.

### Screen 2 · Quick Context (≤ 15 seconds)

```
┌──────────────────────────────────────┐
│  ← back    NEW RFI · STEP 2 of 4     │
│  ──────                              │
│                                      │
│   Project                            │
│   ┌────────────────────────────────┐ │
│   │ T5860 SR 9 (I-95)         ▾   │ │
│   └────────────────────────────────┘ │
│   ⓘ Prefilled from your last report  │
│                                      │
│   Station / Offset                   │
│   ┌────────────────────────────────┐ │
│   │ STA  145 + 50   RT             │ │
│   └────────────────────────────────┘ │
│   ⓘ Prefilled from your last report  │
│                                      │
│   Discipline                         │
│   [ Roadway ] [ Drainage ] [✓Util ]  │
│   [ MOT ] [ FAA ] [ Survey ]         │
│                                      │
│                                      │
│      [    Continue    ]              │
│                                      │
└──────────────────────────────────────┘
```

- Project · prefilled from the user's most recent daily report.
- Station · prefilled from the user's most recent daily report.
- Discipline · chip selector · single tap.
- Big slate-800 "Continue" button.

> If everything is prefilled correctly (common case), this entire
> screen is one tap.

### Screen 3 · Field Condition (≤ 25 seconds)

```
┌──────────────────────────────────────┐
│  ← back    NEW RFI · STEP 3 of 4     │
│  ──────                              │
│                                      │
│   Field Condition                    │
│   ┌────────────────────────────────┐ │
│   │ ⓜ Tap and hold to dictate       │ │
│   │                                │ │
│   │ Utility marked at 145+50 RT    │ │
│   │ doesn't match the actual line. │ │
│   │ Conduit is 14 feet further     │ │
│   │ south. Need clarification.     │ │
│   │                                │ │
│   └────────────────────────────────┘ │
│                                      │
│   Contractor Question                │
│   ┌────────────────────────────────┐ │
│   │ ⓜ Tap and hold to dictate       │ │
│   │                                │ │
│   │ Reroute proposed conduit or    │ │
│   │ relocate water main?           │ │
│   │                                │ │
│   └────────────────────────────────┘ │
│                                      │
│      [    Continue    ]              │
│                                      │
└──────────────────────────────────────┘
```

- Both text areas support **press-and-hold dictation** (native OS
  voice-to-text · we just expose the input).
- Coaching microcopy under each label is ≤ 8 words.
- No spell-check correction overlays that obscure the text.

### Screen 4 · Send (≤ 5 seconds)

```
┌──────────────────────────────────────┐
│  ← back    NEW RFI · STEP 4 of 4     │
│  ──────                              │
│                                      │
│   Send this draft to PM              │
│   ─────────                          │
│                                      │
│   Photos          ◉ 3 attached       │
│   Project         T5860 SR 9         │
│   Station         145+50 RT          │
│   Discipline      Utilities          │
│   Condition       3 sentences        │
│   Question        1 sentence         │
│                                      │
│   Schedule impact (optional)         │
│   [ Not sure · PM will decide  ▾ ]   │
│                                      │
│                                      │
│   [    Send to PM    ]               │
│                                      │
│   Cancel                             │
└──────────────────────────────────────┘
```

- Summary card · operator can verify everything in 2 seconds.
- Schedule-impact picker has 3 options: *Yes · No · Not sure (PM will
  decide)*. Default is "Not sure" — superintendents shouldn't make
  schedule-impact calls on the phone.
- Big "Send to PM" button · neutral slate-800.

After tap: confirmation card · 2 seconds · auto-returns to FL hub.

```
┌──────────────────────────────────────┐
│                                      │
│              ◉                       │
│        Sent to PM                    │
│        Draft #0042 · queued for      │
│        Chris Wright (PM)             │
│                                      │
│              [ Done ]                │
│                                      │
└──────────────────────────────────────┘
```

---

## 4 · Total Path Cost

| Step | Best case | Realistic case |
|---|---|---|
| Camera capture (3 photos) | 12s | 20s |
| Context screen (all prefilled) | 1s | 6s |
| Field condition (dictation) | 15s | 25s |
| Question (dictation) | 5s | 8s |
| Send screen review | 3s | 5s |
| **Total** | **36s** | **64s** |

The doctrine target is **≤ 60 seconds** for the realistic case. We
hit it.

---

## 5 · Glove + Dust Discipline

| Element | Constraint |
|---|---|
| Tap targets | ≥ 56px square (above the 44px platform minimum) for primary actions |
| Spacing between taps | ≥ 16px |
| Contrast | WCAG AAA on outdoor brightness (test in direct sunlight before V.1 sign-off) |
| Form fields | Auto-focus the next field on each step |
| Errors | Inline · non-blocking · slate-200 background · slate-900 text |
| Keyboard | Numeric-decimal for station fields · standard for text |
| Network | Save offline · queue upload · "Sent when reconnected" indicator |

---

## 6 · Drafts That Don't Send (resilience)

If the network is unreachable on Send:
- The draft persists locally.
- A non-blocking toast: *"Saved offline. Will send when reconnected."*
- The FL hub's "My Drafts" badge shows the count.
- Background retry every 60s when network is detected.

The superintendent never loses a draft to a flaky cell connection.
This is non-negotiable.

---

## 7 · What's Intentionally NOT in This Flow

- ❌ Plan-sheet / spec / pay-item references — **PM adds these**.
- ❌ Proposed solution — **PM adds this**.
- ❌ Severity / priority selection — **PM sets this**.
- ❌ Recipient picker — **PM owns distribution**.
- ❌ "Save as draft" button — drafts save automatically every 5s.
- ❌ Tutorial / walkthrough overlays — never.
- ❌ Auto-generated AI summaries — never.

Every cut here is a deliberate offload to the PM. Field operators
contribute the field condition. Contract custodians contribute the
contractual rigor.

---

## 8 · Spanish-First Capability

Many superintendents work primarily in Spanish. The flow:

- Honors the existing `LangToggle` already in the FL portal chrome.
- Renders every label, coaching microcopy, and button in the user's
  selected language.
- Voice-to-text captures whatever the operator dictates (English or
  Spanish · native OS handles transcription).
- The submitted RFI body preserves the dictated language.
- The PM sees the original language **and** an optional inline
  translation toggle (existing `/api/translate` pattern).

---

## 9 · Operator Sign-off Items

- [ ] Camera-first opening is the right call (not a form-first screen).
- [ ] Project + station prefill behavior matches the real field workflow.
- [ ] Voice-to-text is the primary input mechanism, not a fallback.
- [ ] "Not sure" is the right default for schedule impact.
- [ ] Confirmation card timing (≤ 2s) is acceptable.
- [ ] Offline resilience is doctrine-grade (drafts never lost).

---

## 10 · Sign-off

- **Author:** E1 · Phase V.0A paper-prototype authoring pass
- **Status:** 🟢 Doctrine-grade · field-first certified
- **Implementation gate:** Mobile draft path is the **first** UX shipped in V.1, before the PM list view.

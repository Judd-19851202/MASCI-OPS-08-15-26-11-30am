# RFI Coaching & Terminology Standard
## Phase V.0 · Architecture & Governance · 2026-05-27

> Approved vocabulary, coaching subline patterns, and tone for every
> RFI-facing surface. Inherits the platform terminology doctrine.
> Doctrine-locked.

---

## 1 · Audience

Every RFI surface — draft form, review screen, PDF, email, external
landing page, audit trail — speaks to **field operators and contract
custodians under time pressure**. Not to lawyers. Not to marketers.
Not to executives.

Tone is **industrial, calm, operationally precise**.

---

## 2 · Approved Operational Terms

> When in doubt, use the term in this list. Mixing terminology breaks
> the cross-portal glossary and creates cognitive load.

| Approved Term | Use When | DO NOT Use Instead |
|---|---|---|
| **Constraint** | Anything blocking forward progress on a schedule activity | "issue" · "problem" · "blocker" (generic) |
| **Exposure** | Quantified risk surface (cost, schedule, safety) | "risk" (vague) · "concern" |
| **Hold** | Active stop on work pending resolution | "freeze" · "pause" · "stoppage" |
| **Pending** | Awaiting external action | "open" (used for status enum only) |
| **Critical-path impact** | RFI / constraint touches a CP activity | "schedule-critical" · "urgent" |
| **Operational impact** | Real effect on field work | "business impact" · "production impact" |
| **Schedule exposure** | Quantified schedule risk created by an RFI / constraint | "schedule risk" |
| **Field condition** | Observed reality at the site | "as-built" (reserved for closeout) · "field issue" |
| **Coordination issue** | Inter-party clarification needed | "communication problem" |
| **Submitted** | RFI is locked + routed | "sent" · "filed" |
| **Response received** | External party returned an answer | "reply" · "feedback" |
| **Clarification required** | External party asked us for more info | "more info needed" |
| **Converted to Change Condition** | RFI scope exceeded; new CC opened | "turned into a change order" |
| **Voided** | Submitted in error; preserved for audit | "deleted" · "removed" · "cancelled" |
| **Revision** | New version of an active RFI | "update" · "edit" |
| **Distribution** | Routing to one or more recipients | "send list" · "mailing list" |
| **Tokenized link** | External access via signed URL | "magic link" · "share link" |

---

## 3 · Forbidden Vocabulary

| ❌ Forbidden | Why |
|---|---|
| "AI-powered", "smart", "intelligent" (as adjectives on UI) | Marketing slop |
| "Easy", "simple", "fast" (descriptors) | Trust comes from doing, not claiming |
| "Reach out" | Corporate · use "contact" |
| "Drill down" | Marketing · use "review" or "open detail" |
| "Stakeholders" | Vague · name the role (CEI, Engineer, Owner, etc.) |
| "Robust", "seamless", "powerful" | Empty adjectives |
| "Unlock", "supercharge", "boost" | Marketing tone |
| "User" (in UI text) | Use the role: superintendent, PM, etc. |
| "Click here" | Accessibility · always describe the destination |
| "Don't forget to..." | Coaching · not nagging |

---

## 4 · Coaching Subline Patterns (≤ 14 words · CROSS_PORTAL_COACHING_STANDARD §V)

Every RFI screen, tile, sidebar entry, and section header carries a
**single** coaching subline. Patterns:

### 4.1 — On a navigation entry

> *"Draft, review, submit. Field-first. PM-owned."*  (10 words)

### 4.2 — On a list view

> *"Active RFIs across this project. Submitted, pending response, overdue."*  (10 words)

### 4.3 — On a draft form

> *"Capture the field condition. Plan and spec refs. Submit when ready."*  (12 words)

### 4.4 — On a submitted record

> *"Submitted. Awaiting response. Distribution log open. Revision allowed via PM."*  (10 words)

### 4.5 — On a critical-path RFI

> *"Critical-path impact confirmed. Response due inside the active window."*  (10 words)

### 4.6 — On an overdue RFI

> *"Overdue. PM contact escalation visible. Reissue the link if needed."*  (10 words)

### 4.7 — On the external landing page

> *"Open the linked RFI. Download the PDF. Respond when ready."*  (10 words)

### 4.8 — On a voided record

> *"Voided. Reason on file. Snapshot preserved. Audit available."*  (8 words)

---

## 5 · Tone Rubric

| Quality | Yes | No |
|---|---|---|
| Voice | declarative, present tense | passive, conditional |
| Sentence length | ≤ 14 words for sublines · ≤ 20 for body | run-on, multi-clause |
| Punctuation | period, comma, dash · em-dash sparingly | exclamation marks · ellipses |
| Capitalization | sentence case in body · MONO UPPERCASE for kickers (existing platform doctrine) | TITLE CASE EVERYTHING · all caps body |
| Emojis | none in operational copy | any |
| Numbers | operational specifics: days, stations, dollars | vague: "many", "lots", "soon" |

---

## 6 · Error Messages

The same coaching rules apply to error messaging. Field operators must
know **what failed** and **what to do next**.

| Bad | Good |
|---|---|
| "An error occurred." | "Submit failed. Network dropped. Tap retry · draft saved." |
| "You don't have permission." | "Submit requires PM. Your draft is saved · PM <name> notified." |
| "Invalid input." | "Station field expects format STA 100+00. Try again." |
| "Server error." | "Save paused · we'll retry automatically. Your draft is local." |

---

## 7 · External-Facing Copy

External recipients (CEI / Engineer / Owner) see **plainer, even
calmer** copy. They are not MASCI staff and do not share the internal
glossary perfectly. Rules:

- Spell out role names: "Engineer of Record" not "EOR".
- Spell out station: "Station 145+50 (offset 12' RT)" not "STA 145+50 12'R".
- Avoid internal terminology unless the agency uses it natively
  (e.g., "MOT" is acceptable for FDOT recipients; not for FAA).
- Always include a human contact (PM name + phone + email).

---

## 8 · Coaching Tile Patterns (matching existing PM/HR/Safety V2)

When the RFI subsystem mounts in the PM V2 sidebar, its domain tile
follows the same template used by Safety:

```
─── 4-domain doctrine palette · slate stripe (operational) ───
Operational Records · slate-600

  RFI Center                Draft, review, submit. PM-owned.
  Constraints               Schedule impact tracker. Linked to RFIs.
  Schedule Intelligence     P6 import. Lookahead. Critical path.
```

No red stripe in this domain. Red remains reserved for the Incidents
domain. Schedule exposure surfaces inside the RFI Center via a single
slate-with-red-dot indicator on the row, not on the sidebar.

---

## 9 · Bilingual Discipline

RFI copy must round-trip cleanly through the existing `i18n` pipeline.
Spanish translations are not auto-generated; they enter through the
existing translation review process (BILINGUAL_OPERATIONAL_MEANING_AUDIT).

Field operators on bilingual crews may draft in Spanish; the submitted
PDF defaults to English unless the project carries Spanish-PDF mode.

---

## 10 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Vocabulary locks during V.1. Sublines reviewed against this doc during V.1 implementation.

# TRACK 19.08 · UI Component Atlas

Structural inventory of the top-8 New*.jsx form pages plus shared building blocks. Purpose · Visibility · Trigger · Dependencies · Consumers · Test-IDs · Validation · Persistence.

---

## 1 · Shared shell primitives (used by 8+ forms)

| Component | File | Purpose | Trigger | Persistence |
| --- | --- | --- | --- | --- |
| `<MasciLogo>` | `components/MasciLogo.jsx` | Corporate identity on header | Always | none |
| `<Section number title>` | `components/Section.jsx` | Numbered form section wrapper | Always | none |
| `<CollapseCard>` | `components/CollapseCard.jsx` | Progressive-disclosure card | Toggle | UI-only |
| `<PresenceGate>` (`_PresenceGate` on DR) | inline in `NewDailyReport.jsx` | Yes/No progressive gate (Track 19.06) | User click | UI-only, does not clear underlying data |
| `<YesNo>` | `components/YesNo.jsx` | Yes/No pill pair | User click | Value stored on parent field |
| `<SignaturePad>` | `components/SignaturePad.jsx` | Canvas-based signature capture | Sign action | data-URL persisted on submit |
| `<PhotoUpload>` | `components/PhotoUpload.jsx` | Multi-photo picker → R2 | Photo pick | R2 key + thumb URL on `photos[]` |
| `<AttachmentUpload>` | `components/AttachmentUpload.jsx` | Unified PDF/XLSX/XLS/CSV picker (Track 19.04) | File pick | Envelope on `attachments[]` |
| `<JobPicker>` | `components/JobPicker.jsx` | MASCI job dropdown → `jobs_master` | User pick | `project_number` + `project_name` |
| `<EmployeeCombo>` | `components/EmployeeCombo.jsx` | HR roster search (Track 19.03) | Search + pick | `name` + `employee_id` |
| `<EquipmentCombo>` | `components/EquipmentCombo.jsx` | `equipment_master` search | Search + pick | `unit_number` / `asset_id` |
| `<LangToggle>` | `components/LangToggle.jsx` | EN / ES switch | Toggle | `getLang()` writes local storage; submit path translates ES→EN |
| `<DistributionList>` | `components/DistributionList.jsx` | PM email recipients | Auto-load per project | Included in email routing |
| `<LifecycleGuide>` | `components/LifecycleGuide.jsx` | Coaching card (icon + accent + sections[]) | Always visible | UI-only |
| `<HelpTipBlock>` | `components/HelpTipBlock.jsx` | Contextual guidance panel (per form/section key) | Loaded from `guidance/` | UI-only |
| `<CoachingPanel>` (family of `LifecycleGuide` derivatives) | Various | Educational content on hover / tap | Always visible | UI-only |
| `<sonner>` toaster | `components/ui/sonner.jsx` | Success / info / error toasts | Event-driven | none |
| Sticky submit footer | Inline in each `New*.jsx` | Always-visible submit + hint | Always | none |
| Coaching-tip bar (`5 COACHING TIPS AVAILABLE`) | Inline (`NewDailyReport.jsx` line ~1400) | Collapsed 5-item tip strip | Tap to expand | UI-only |

---

## 2 · Section / band structure per form

### 2.1 Daily Report (redesigned by Track 19.06/19.07)

Six cognitive checkpoints (see `TRACK_19_07_EXECUTIVE_SUMMARY.md`):
1. Job Setup — WHO WAS THERE? band ► crew · subs · visitors · equipment (each behind `<PresenceGate>`).
2. WHAT MOVED? band ► materials in / materials out (gates).
3. WHAT GOT DONE? band ► Activity + Production Log (single card).
4. WHAT IMPACTED TODAY? band ► delays · constraints · weather (gate).
5. WAS THE JOB SAFE? band ► safety triggers · injuries · accidents.
6. WHAT HAPPENS NEXT? band ► Tomorrow / Follow-Up.
7. Required Evidence — photos (6-min) + attachments.
8. Sign-off — signature + submit.
9. Additional context (rarely needed) — collapsed `<details>` with the old six narrative prompts.

### 2.2 Equipment Pre-Op — `NewEquipmentInspection.jsx`

Flat single-page layout (pre-19.06 pattern):
* Section 01 — Report Information (asset + operator + job + time).
* Section 02 — Inspection Body — N template-driven sections × M items each. Each item is `{label, status pill (Pass/Fail/N-A), notes, photos[]}`.
* Section 03 — Defects Summary (auto-calc from failed items).
* Section 04 — Photos / Attachments.
* Section 05 — Sign-off.

**Coaching stack**: header `<LifecycleGuide>` + section-level `<HelpTipBlock>` on Report Information + inline instruction paragraphs on each section — **three helper systems, same page**. See `11_DUPLICATE_LOGIC_REPORT.md`.

### 2.3 DVIR — `NewFleetDVIR.jsx`

Similar to Equipment Pre-Op but with DVIR-specific sections (Engine · Steering · Brakes · Tires · Lights · Body · Emergency-Equipment). Additional footer band: `overall_status` pill (Safe / Unsafe) + `next_action` copy.

### 2.4 Safety Meeting — `NewMeeting.jsx`

* Section 01 — Meeting Type + Topic (with topic-library picker).
* Section 02 — When / Where.
* Section 03 — Presenter.
* Section 04 — Attendees (EmployeeCombo × N rows, each with a signature pad).
* Section 05 — Topics Covered (long-form) + Key Takeaways.
* Section 06 — Photos / Attachments.
* Section 07 — Sign-off.

### 2.5 Incident — `NewIncident.jsx` (1,672 LOC — longest form)

* Section 01 — Incident Type + Severity + Date/Time.
* Section 02 — Reporter / Discovered By.
* Section 03 — Location + GPS.
* Section 04 — People Involved (conditional expansion for injuries).
* Section 05 — Equipment Involved.
* Section 06 — Witnesses.
* Section 07 — Description.
* Section 08 — Immediate Actions Taken.
* Section 09 — Root Cause Notes (optional).
* Section 10 — Photos / Attachments.
* Section 11 — Sign-off + Supervisor Sign-off.

Ten sections. Highest cognitive load on the platform.

### 2.6 QA-QC Inspection — `NewQaqcInspection.jsx`

Same shape as Equipment Pre-Op — reason: shares `<CanonicalInspectionSections>` component (`/frontend/src/components/CanonicalInspectionSections.jsx`).

### 2.7 Safety Equipment Issuance / Training — `NewSafetyEquipmentIssuance.jsx` / `NewSafetyEquipmentTraining.jsx`

Single-column, four sections each. Simple by comparison.

---

## 3 · Progress indicators observed

| Form | Progress cue | Location |
| --- | --- | --- |
| Daily Report | "0/9 · Needs work" badge in top header | Post-19.06 |
| DVIR | Section pass/fail chip aggregation | Header |
| Equipment | "Sections completed" derived (unclear to operator) | None visible |
| Meeting | Attendee count | Attendance section |
| Incident | Section-1 → Section-11 numbering (no completion cue) | Section headers |
| QA-QC | Same as Equipment | — |

**Observation**: Only Daily Report exposes an aggregated "readiness" pill. Others rely on section numbering.

---

## 4 · Modal / dialog inventory

| Modal | Trigger | Owner |
| --- | --- | --- |
| Draft Restore | Mount + saved draft found | `useFormDraft` hook |
| Discard Draft confirmation | User taps Discard | Inline |
| Photo picker | User taps camera icon | `<PhotoUpload>` |
| Attachment picker | User taps attachment icon | `<AttachmentUpload>` |
| Signature erase confirmation | Signature Clear | `<SignaturePad>` |
| Smart Prefill offer card | Job pick + prior DR exists | `NewDailyReport.jsx` (Track 19.04) |
| Reset-hours per row (Track 19.06 amend) | Amber pill on prefilled row | `NewDailyReport.jsx` |
| Excavation link picker (DR) | Yes on excavation gate | `NewDailyReport.jsx` |
| Field-Leadership signature-required dialog | On submit | `FieldLeadershipFormPage` |
| Admin-password re-entry | Destructive admin actions | Track iter266 (admin console) |

---

## 5 · Sticky footers / floating controls

* Every `New*.jsx` mounts a sticky submit footer with a state message ("Ready to submit" / "Need N more photos") and a red-accent submit button.
* No form uses a floating action button (FAB) — deliberate on mobile to avoid keyboard collision.

---

## 6 · Chip / badge / status indicator inventory

* Job status chips (`SAVED JUST NOW`, `0/9 · Needs work`) — global header.
* Crew linkage chips (`Linked to roster` · `Not in roster — will create governance finding`) — per crew row in DR.
* Prefill review-hours amber notice — DR post-amendment.
* Cognitive-checkpoint band label (mono red uppercase) — DR post-19.07.
* Section-level pill counters (attendees / defects) — Meeting / DVIR.
* Overall-status pill — DVIR footer.
* Skipped-pill on presence-gates set to No — DR post-19.06.

---

## 7 · Test-ID conventions observed

Universal patterns:
* `data-testid="submit-sticky-btn"` on the primary CTA of each form.
* `data-testid="crew-row-${i}"` / `crew-remove-${i}` / `crew-name-${i}` / etc. — per crew row on DR.
* `data-testid="presence-crews-yes"` / `presence-crews-no` — per gate on DR.
* `data-testid="daily-report-smart-prefill-*"` — Smart Prefill offer buttons.
* `data-testid="daily-report-prefill-review-notice"` — post-amendment.
* `data-testid="daily-report-prefill-notice-dismiss"` — dismiss button.
* `data-testid="crew-reset-hours-${i}"` — per-row reset (this amendment).

**Consistency**: Test-IDs use kebab-case; Section-level test-IDs use `band-*` prefix; buttons use `-btn` suffix; per-row identifiers use `-${i}` template. Not 100% enforced across all forms — see `17_PLATFORM_CONSISTENCY_AUDIT.md`.

# TRACK 19.08 · Executive Recommendations + Platform Consistency Audit + Operational Value Analysis

Merged for reader convenience. No implementation — this is guidance for the redesign phase.

---

## PART A · Platform Consistency Audit (Phase 17)

Cross-form consistency scoring. Green = universal · Amber = mostly · Red = inconsistent.

| Surface | DR | Eq-PreOp | DVIR | Meeting | Incident | JHA | QAQC | Iss/Trn |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Header pattern (logo · title · lang · save state · submit) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Sticky submit footer | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Autosave / draft restore banner | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Actor-scoped draft (Track 19.04) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Photo upload path | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Unified attachment (Track 19.04) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟡 (some legacy paths) | 🟢 | 🟢 |
| HR canonical roster (Track 19.03) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Job picker (JobPicker) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Language toggle EN/ES | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Signature pad UX | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| GPS auto-capture | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 |
| Progressive disclosure | 🟢 | 🔴 | 🔴 | 🟡 | 🔴 | 🔴 | 🔴 | 🟢 (short forms) |
| Cognitive-checkpoint framing | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |
| Submit-time confirmation of downstream fanout | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |
| Photo required at defect | — | 🔴 | 🔴 | — | 🟡 (min 1 on injury) | — | 🔴 | — |
| Idempotency + queued-retry | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Trust-spine correlation | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| Test-ID kebab-case | 🟢 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 |

**Reading**: The infrastructure primitives (auth, draft, photo, attachment, HR, idempotency, trust-spine) are universally consistent — the platform's strongest layer. The **UX layer** (progressive disclosure, GPS capture, cognitive framing, submit confirmation) is inconsistent because only the Daily Report has received the modernization pass.

---

## PART B · Operational Value Analysis (Phase 18)

For each family: **if it disappeared tomorrow, what would we lose?** and **which fields provide little value?**

### B.1 · Daily Report — if it disappeared

* Payroll timesheet crosscheck → LOST
* PM crew-compliance intelligence → LOST
* Historical accountability timeline → LOST
* Job Photos indexer feed → LOST (photos would have no anchor)
* Compliance export → LOST
* Excavation daily-linkage → LOST
* Superintendent identity trail → LOST

**Value = irreplaceable.** Even the "weak" pre-19.07 version was carrying immense downstream weight. Post-19.07 it's the platform's operational spine.

**Low-value fields identified (candidates for CAN-HIDE)**: `submit_language` (used only for i18n debug; not surfaced downstream).

### B.2 · Equipment Pre-Op — if it disappeared

* Pre-shift safety confirmation → LOST (OSHA §1926.601)
* Fleet-defect intake → PARTIAL LOST (DVIR still covers vehicles)
* Non-vehicle asset condition tracking → LOST (no other source)
* Operator accountability per shift per unit → LOST

**Value = high, especially for non-vehicle assets.**

**Low-value fields**: `shift_start`/`shift_end` on some template variants — collected but rarely used downstream.

### B.3 · DVIR — if it disappeared

* Federal DOT compliance → LOST (§396.11 mandated)
* Shop defect intake → LOST
* OOS workflow → LOST
* Motive / Samsara integration → BROKEN

**Value = federal-mandate. Cannot disappear.**

**Low-value fields**: `next_action` (derived; rarely surfaced).

### B.4 · Meeting — if it disappeared

* OSHA §1926.20 training documentation → LOST
* HR-accountability training credit → LOST
* Weekly safety cadence → LOST

**Value = compliance-anchored. Operational value would improve with the changes in `12_UX_FRICTION`.**

**Low-value fields**: `meeting_duration_minutes` (rarely inspected). `key_takeaways` (currently redundant with `topics_covered`).

### B.5 · Incident — if it disappeared

* OSHA §1904 recordkeeping → LOST
* HR injury timeline → LOST
* Corrective action linkage → BROKEN
* Trust-spine safety events → LOST

**Value = federal-mandate + risk-management-critical.**

**Low-value fields**: `witnesses[]` when severity is low (rarely provides forensic value). `osha_form_300_number` when `osha_recordable=false` (not applicable).

### B.6 · JHA — if it disappeared

* OSHA §1926.20 hazard-analysis documentation → LOST
* Pre-task briefing evidence → LOST
* Per-employee acknowledgement audit → LOST

**Value = federal + operational.**

**Low-value fields**: `task_description` when the JHA template is already task-specific.

### B.7 · QA-QC / Corrective Action / Safety Equipment / Excavation

All carry either compliance or downstream-workflow value. **None are candidates for removal.**

---

## PART C · Executive Recommendations

Ordered by return-on-effort. **None are implemented in Track 19.08.**

### P0 — high-value / low-risk

1. **Apply Track 19.06 PresenceGate to Equipment Pre-Op, DVIR, Incident.** Section-level Yes/No gates. Same UX pattern proven on Daily Report. Zero schema change. Cognitive load −60% on these three forms.
2. **Add submit-time confirmation panel.** After 2xx, show: "PDF #X rendered · shop ticket #Y opened · Foreman Jane notified · DVIR mirrored to Motive." Ten lines of UI, matches industry standard (Fleetio/Samsara/MaintainX), closes the operator-trust gap identified in `07_FAIL_CASCADE_ANALYSIS.md`. Zero backend change.
3. **Consolidate three helper systems** (`LifecycleGuide` + `HelpTipBlock` + section-prose) into a single lazy-loadable help drawer. Content preserved; presentation collapsed. Zero coaching content lost.

### P1 — medium-value

4. **Require photo at defect-level FAIL** on Equipment / DVIR. Industry-standard pencil-whip guard. Requires schema-level `required_photo_on_fail: true` UI enforcement + one lock test. Zero backend change.
5. **Apply Smart Prefill to Equipment / DVIR** (using Track 19.06 amendment pattern). Prior-shift template + defect notes carry forward as an editable offer.
6. **Merge Meeting `topics_covered` + `key_takeaways`** into a single "discussed and decided" field. Add per-attendee single-tap knowledge-check ("one thing you'll do differently"). Adds operational value without violating OSHA-recordkeeping shape.
7. **Auto-capture GPS on Equipment / DVIR / Meeting / JHA / QAQC** using the same pattern as Incident / Daily Report. Trust-spine timestamp+location provenance.

### P2 — nice-to-have

8. **Pencil-whip heuristics**: detect 100%-pass streaks and identical crew-list-week-over-week; surface to Safety-Manager only. Read-only alert.
9. **Retire Hub V1** once Hub V2 adoption is >80%. Product decision required.
10. **QR-scan asset-binding on Equipment / DVIR**. Reduces asset-picker friction. Requires per-asset QR labelling (business-process change, not just code).

### P3 — future

11. AI-assisted "smart defaults" via historical inspection data (parity with Fleetio Service Advisor).
12. Visual-diagram defect selection (parity with Raken).
13. Automated Motive / Samsara sync improvements (currently one-way; make bidirectional).

---

## PART D · What must NEVER change (redesign hard-locks)

* Any field in `03_MASTER_FIELD_DICTIONARY.md` classified P-LEGAL / P-DOT / P-OSHA / P-PAYROLL / P-FLEET / P-BE.
* Route aliases in `11_DUPLICATE_LOGIC_REPORT.md` §2 — live-compat.
* Legacy read-tolerance values (`tailgate`, `injury_reported` booleans, `dvir` collection reads, etc.).
* Trust-Spine correlation ids — end-to-end auditor traceability.
* Historical immutability — no PATCH / DELETE routes on the historical collections.
* HR canonical roster is the single source of truth for employee identity.

---

## PART E · The one-sentence summary

> The MASCI operational forms ecosystem is functionally complete, legally-compliant, and structurally strong; the only missing layer is a UX consolidation pass — the same pass that Track 19.06/19.07 already proved on the Daily Report — applied to Equipment Pre-Op, DVIR, Incident, and Meeting.

Redesign begins in a subsequent track. Track 19.08 is now closed.

# FIELD TRIAL — OBSERVER CHECKLIST
## Safety observer · one checklist per foreman per day

**Observer name**: ____________________   **Date**: _______   **Foreman**: ____________________   **Job**: ____________________   **Device**: __________________________

---

## PRE-FLIGHT (before foreman starts)

- [ ] Foreman has the trial URL bookmarked or saved.
- [ ] Foreman has the **FIELD_TRIAL_FOREMAN_SCRIPT.md** (printed or on a second device).
- [ ] Foreman knows your phone number for support.
- [ ] You have a stopwatch (phone is fine).
- [ ] You have the **FIELD_TRIAL_FEEDBACK_FORM.md** ready (one copy per foreman per day).
- [ ] You have a way to take screenshots (foreman's phone is best).
- [ ] You have the issue-log template open (`FIELD_TRIAL_ISSUE_LOG_TEMPLATE.md`).

---

## DURING THE TRIAL

### Daily Report — excavation = NO  (W1)
- [ ] Foreman opens Daily Report successfully.
- [ ] Excavation question is visible and understood.
- [ ] Foreman taps NO without help.
- [ ] Daily Report submits without blocking.
- [ ] Time to complete (start to submit) recorded: _____ min

### Daily Report — excavation = YES  (W2)
- [ ] Excavation question requires Create/Link before submit.
- [ ] Foreman understands what "Create" vs "Link" means.
- [ ] Daily Report cannot be submitted without an Excavation Record.
- [ ] Foreman picks the right option without help.
- [ ] Time to complete (start to submit) recorded: _____ min

### Create Excavation from Daily Report  (W3)
- [ ] Tap from Daily Report opens the Excavation form.
- [ ] Job is pre-filled from the Daily Report.
- [ ] Foreman does NOT have to re-type project info.
- [ ] Excavation record creates successfully.
- [ ] Daily Report shows the linkage on save.

### Link Existing Excavation  (W4)
- [ ] Foreman can find their existing excavation in the list.
- [ ] Tap links it to the Daily Report.
- [ ] Linkage persists on Daily Report save.

### Public Excavation Form direct entry  (W5)
- [ ] Foreman can reach the form from the **public** tile (no login).
- [ ] Foreman can submit without a MASCI login.
- [ ] Submission returns an EX-2026-### ID.

### Trench Box linkage  (W6)
- [ ] Foreman picks correct trench box from the asset list.
- [ ] Asset shows in the submitted record.
- [ ] Verify on Oversight that the asset is reflected.

### Road Plate linkage  (W7)
- [ ] Foreman picks correct road plate.
- [ ] Plate shows in the submitted record.

### Competent Person selection  (W8)
- [ ] The CP picker shows **only designated** CPs (not all employees).
- [ ] Foreman finds the correct CP for their crew.
- [ ] If no CP is available → foreman knows to flag this to you.

### OSHA flag review  (W9 / W10 / W11)
- [ ] When a flag fires (PROTECTIVE_SYSTEM, COMPETENT_PERSON, TRENCH_BOX_DEPTH, ROAD_PLATE_DIMENSION, REINSPECTION), the foreman sees and understands it.
- [ ] Foreman can read the flag message and act on it.
- [ ] If TRENCH_BOX_DEPTH fires → foreman knows to acknowledge with a reason (stacked, engineered, tabulated data).

### Reinspection request  (W12)
- [ ] Foreman triggers a reinspection successfully.
- [ ] Foreman picks an appropriate reason from the 7 chips.
- [ ] Confirmation message appears.
- [ ] Safety + Superintendent receive notification (verify on their devices).

### EN/ES toggle (only if Spanish-speaking foreman)
- [ ] Toggle button is visible.
- [ ] Tap switches the entire form (not just headings).
- [ ] Emergency Excavation block reads "¿Excavación de Emergencia?" in ES.
- [ ] No mixed-language strings.
- [ ] Buttons read SÍ / NO / N/D.

---

## EVERY 15 MINUTES — QUICK PULSE

- [ ] Foreman still progressing (not stuck).
- [ ] Foreman not asking the same question twice (if yes → log as confusion point).
- [ ] No app crash, no spinner-of-doom, no infinite reload.
- [ ] Mobile layout still usable (no horizontal scroll, no clipped buttons).

---

## END-OF-DAY DEBRIEF (5 min · with the foreman)

Run through the 8 questions in **FIELD_TRIAL_FEEDBACK_FORM.md** — capture **verbatim quotes**. Do NOT summarize. Do NOT defend the platform.

After the debrief, fill out:
- [ ] Feedback form (one per foreman per day) — submitted.
- [ ] Issue log updated for any new issues observed.
- [ ] Screenshots saved with naming convention `<foreman>_<day>_<issue#>.png`.

---

## ESCALATION

| Severity | Definition | Action |
|---|---|---|
| **P0** | Foreman cannot complete a workflow at all · or wrong data submitted · or asset/job/CP missing | **STOP** the trial. Call Safety lead immediately. |
| **P1** | Foreman completes workflow but with critical confusion or visible error | Log in issue log. Continue trial. Address in post-trial verdict. |
| **P2** | Minor UI issue, translation gap, typo | Log in issue log. Continue trial. |
| **P3** | Cosmetic preference | Note in feedback. No action required. |

---

## DAILY SUBMISSION

End of each day, send to trial lead:
1. This checklist (one per foreman) — completed.
2. Feedback form (one per foreman) — completed.
3. Issue log additions.
4. Screenshots folder.

Trial lead compiles into `/app/memory/FIELD_TRIAL_DAY_<N>_REAL_REPORT.md`.

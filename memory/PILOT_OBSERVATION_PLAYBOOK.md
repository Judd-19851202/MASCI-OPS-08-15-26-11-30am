# PILOT OBSERVATION PLAYBOOK

**Doctrine:** Watch the real user. Score real friction. Fix what field truth reveals.
**Established:** Track 19.30 · 2026-07-03
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

---

## Charter

Automated tests prove the platform *works*. Pilot observation proves the platform *fits*. Every pilot session is an opportunity to catch confusion, extra clicks, abandoned flows, misunderstood labels, slow screens, missing data, bad PDFs, wrong emails, permission problems, mobile issues, Spanish issues, and training gaps that no test can catch.

This playbook defines how to observe, what to record, and how to route findings into the P0/P1/P2/P3 remediation stream.

---

## Observation cadence

- **Every pilot session:** capture at least one persona walkthrough end-to-end.
- **Weekly summary:** aggregate findings across sessions and route to the appropriate track backlog.
- **Executive review:** monthly review of top confusion points.

## Observation modes

1. **Shoulder-surf (silent):** Watch the user without prompting. Note every hesitation, back-navigation, tap-and-hold, or pause > 3 seconds.
2. **Think-aloud:** Ask the user to narrate what they're doing and why.
3. **Task-completion:** Give the user a task ("File your Daily Report for job 24-018") and time how long it takes end-to-end.
4. **Bilingual pass:** Same tasks with the user in Spanish mode.

## Capture format (per session)

```markdown
### Session <ID> · <date> · <persona> · <device>

**Task:** <what the user was asked to do>
**Duration:** <minutes>
**Result:** completed / abandoned / partial

**Confusion points:**
- <bullet>
- <bullet>

**Extra clicks (paths that should have been shorter):**
- <bullet>

**Abandoned flows:**
- <bullet>

**Misunderstood labels:**
- <bullet>

**Slow screens (> 2 s to render):**
- <bullet>

**Missing data:**
- <bullet>

**Bad PDFs / emails:**
- <bullet>

**Permission problems:**
- <bullet>

**Mobile / iPad issues:**
- <bullet>

**Spanish issues:**
- <bullet>

**Training gaps:**
- <bullet>

**Severity classification:**
- P0 (blocks operations): <list>
- P1 (serious usability): <list>
- P2 (post-deploy polish): <list>
- P3 (opportunistic): <list>
```

---

## Persona-specific observation scripts

### 1 · Foreman completing Daily Report
- Ask the foreman to file a Daily Report for today, on his phone, in the field.
- Watch: does he pick the right project? Does autosave surface when he pauses? Does he attach photos? Does he understand the "submit" state versus "draft"?
- Confirm: PDF arrives in PM inbox within 60 seconds. Photo attachments visible.

### 2 · Operator completing Pre-Op
- Ask the operator to scan the QR on his machine and file a pre-op.
- Watch: does he understand the checklist? Does he capture a defect if prompted? Does the OOS cascade fire correctly?
- Confirm: Shop portal `/shop/equipment` shows the defect.

### 3 · Driver completing DVIR
- Ask the driver to file his morning DVIR from the cab.
- Watch: does he mark defects? Does OOS cascade to Fleet? Does the confirmation page make sense?
- Confirm: Dispatch command summary shows the OOS unit.

### 4 · Supervisor running Safety Meeting
- Ask the foreman/supervisor to run a Toolbox Talk with 6 crew members.
- Watch: does the topic auto-load? Do crew members sign? Does he collect all attendance before submit?
- Confirm: PDF attendance sheet arrives to Safety + PM.

### 5 · HR uploading employee records
- Ask HR to upload a batch of 25 historical records from a legacy box scan.
- Watch: does Intake Session provenance work? Does bulk-classify happen in one pass? Does queue routing work?
- Confirm: `/hr/historical-records/batches` shows the session. Employee 360 reflects the new records.

### 6 · Safety reviewing incident case
- Ask Safety to review a new incident report and open a Case Workspace.
- Watch: does she find the case? Can she navigate Investigation → Evidence → Findings → CAPAs → Closeout?
- Confirm: Executive PDF exports without missing fields.

### 7 · PM finding report / photos / PDF
- Ask the PM to find the Daily Report submitted this morning for project 24-018.
- Watch: how many clicks? Does she find photos? Does she find the PDF?
- Confirm: total time from login to PDF viewer.

### 8 · Shop reviewing failed equipment
- Ask the Shop Manager to review today's OOS units.
- Watch: does she use the Recovery Map? Does she find defect history? Does she understand RTS verification versus repair-complete?
- Confirm: workflow order matches doctrine (repair complete ≠ safe to use).

### 9 · Dispatch viewing fleet / transportation
- Ask Dispatch to check the fleet status and hand off a unit to another project.
- Watch: does she use Command Center? Are asset transfers intuitive? Does Motive data render correctly?
- Confirm: transfer records land in `/asset-transfers`.

### 10 · Executive reviewing dashboard
- Ask an executive to answer: "What requires attention right now?" and "What is our incident trend this month?"
- Watch: does she find Executive Intelligence Center? Does she find Governance Health? Does she find Command Center?
- Confirm: less than 3 clicks from login to answer.

---

## Bilingual observation

- Every persona script above should be repeated with a Spanish-speaking user in ES mode.
- Capture: language toggle discoverability · translation completeness · translation quality · comfort using canonical EN values in freeform ES text.

## Mobile / iPad observation

- Every persona script should include a device-swap variant (mobile · iPad · desktop) where the persona actually uses that device.

## Routing findings

- **P0 findings** → immediate hotfix. Halt pilot rollout for that surface until closed.
- **P1 findings** → high-priority backlog. Fix within the current sprint / track cycle.
- **P2 findings** → post-deploy polish backlog (append to next major remediation roadmap).
- **P3 findings** → opportunistic polish backlog.

All findings must be captured in `/app/memory/PILOT_OBSERVATION_FINDINGS_<YYYY-MM>.md` (author monthly).

## Post-pilot deliverables (per major pilot phase)

- Aggregate findings document.
- Updated remediation roadmap.
- Six Pillars re-scoring.
- Go/No-Go verdict for continued rollout.

## Owner

Pilot observation is owned jointly by:
- The main platform agent (routes findings into tracks).
- The MASCI operations lead (ensures observation happens).
- The pilot user themselves (empowered to flag friction without retribution).

# TRACK 20.3 · Human Walkthrough

For each persona: what do they need · what should they not see · where they go today · how many clicks · what the thread would improve · what must remain restricted.

## Field Reporter
- Needs: to submit a report and know it was received.
- Should not see: other cases, medical, agency, evidence.
- Today: `/incidents/new` public form + `/near-miss` kiosk.
- Clicks: 1 (form).
- Thread would improve: N/A — reporter never sees the thread.
- Restricted: everything.

## Safety Director
- Needs: full case story, attention items, blockers, evidence, witnesses, medical, agency, CAPA, PDFs, cross-links.
- Should not see: nothing hidden from this role.
- Today: Safety Case Workspace tabs; Incidents Dashboard; Portfolio Attention.
- Clicks: 3 – 6 (dashboard → case → tab).
- Thread would improve: **≤ 2 clicks** to "how is this case doing" via a single-scroll morning read.
- Restricted: none for Safety.

## Project Manager
- Needs: cases on their projects, project impact, CAPA on their projects.
- Should not see: medical, witness names, evidence files, attorney work product, non-PM projects' cases.
- Today: PM Command Center attention chip + Project Health + Safety Case Workspace (limited).
- Clicks: 4 – 6.
- Thread would improve: single scroll for their scope only; deep-links to full workspace if allowed.
- Restricted: medical · witness names · attorney work product · non-scope projects.

## Executive
- Needs: severity · attention level · trend · CAPA status · executive report deep-link.
- Should not see: raw evidence, medical, witness names, attorney work product.
- Today: Executive Case Report + Executive Intelligence Center.
- Clicks: 3 – 5.
- Thread would improve: unified read that matches the Employee / Project / Fleet Thread cadence they already know.
- Restricted: raw evidence · medical · witness names · attorney work product.

## HR
- Needs: cases involving their employees, redacted narrative, no medical raw data.
- Should not see: witness names, evidence files, agency internals, attorney work product, medical raw data.
- Today: HR Incidents rollup + Employee Thread → accountability timeline.
- Clicks: 3 – 5.
- Thread would improve: consistent employee ↔ case linkage.
- Restricted: witness names · evidence files · agency internals · attorney work product · medical raw data.

## Fleet Manager
- Needs: cases involving fleet units, equipment linkage, downtime impact.
- Should not see: employee-level information beyond first name role labels; medical; witness names.
- Today: Fleet Unit Thread + Asset timeline cross-link.
- Clicks: 3 – 5.
- Thread would improve: single view of what happened on the unit today / this week.
- Restricted: employee-level information beyond role · medical · witness names.

## Shop Manager
- Needs: equipment damage / repair scope.
- Should not see: personnel info, medical, agency, evidence beyond repair-relevant photos.
- Today: cross-portal navigation from Fleet.
- Clicks: 4 – 6.
- Thread would improve: repair-scope-only view derived from the same case.
- Restricted: personnel · medical · agency · non-repair evidence.

## Transportation Manager
- Needs: driver / DVIR / route impact.
- Should not see: unrelated employees, medical, witness names, non-driver evidence.
- Today: dispatch / fleet cross-portal.
- Clicks: 4 – 6.
- Thread would improve: driver-scope view.
- Restricted: unrelated employees · medical · witness names · non-driver evidence.

## Attorney / legal reviewer
- Needs: attorney work product, full evidence, agency records, timeline.
- Should not see: nothing hidden from this role, but strictly gated (Admin + Safety access).
- Today: full workspace.
- Clicks: 4 – 6.
- Thread would improve: one printable, defensible view.
- Restricted: same as Safety + Admin (no additional gain).

## Insurance reviewer
- Needs: insurance package, redacted narrative, redacted photos, agency contacts.
- Should not see: employee personal data, medical raw, attorney work product.
- Today: PDF download.
- Clicks: 2 – 3.
- Thread would improve: nothing directly (insurance reviewer receives PDF, not thread access).
- Restricted: employee personal data · medical raw · attorney work product.

## Client / Owner representative
- Needs: executive summary + severity + CAPA status.
- Should not see: raw evidence, employee names, medical, witness names, agency internals, attorney work product.
- Today: Executive Report PDF.
- Clicks: 1 (they receive the PDF).
- Thread would improve: nothing directly (client sees PDF, not thread).
- Restricted: raw evidence · employee names · medical · witness names · agency internals · attorney work product.

## OSHA / regulator package reviewer
- Needs: OSHA-formatted package.
- Should not see: attorney work product; non-OSHA-relevant fields.
- Today: OSHA report package endpoint (if configured for report_type).
- Clicks: 1.
- Thread would improve: nothing directly.
- Restricted: attorney work product · non-OSHA-relevant fields.

## Certification
**The proposed Incident Thread strictly serves Safety · Admin (full), PM (project-scoped), Executive (summary), HR (employee-scoped), and Fleet (unit-scoped) — all inheriting the existing endpoint gates. Every other role is either never given thread access or receives a downstream PDF instead.**

# iter317 · Operational Coaching + Guidance Parity Audit

**Scope:** visibility-only convergence audit covering coaching, HelpTipBlocks,
guidance articles, and operational guidance parity against the post-iter285 /
iter286 / iter287 / iter288 / iter314 / iter315 / iter316 platform behavior.

**Method:** evidence-based grep + AST traversal of `tips.py` / `tips_es.py` /
`content.py` + frontend HelpTipBlock mount inventory. **No code changes.**

**Date:** 2026-05-21 · post-iter316 closure

---

## Evidence baseline

| Surface | Count |
|---|---|
| EN coaching tip rows (`tips.py`) | 373 |
| Distinct `(form_key, kind)` EN tips | 373 |
| ES translations (`tips_es.py`) | 429 (legacy super-set) |
| EN tips without ES translation | **0** ✅ bilingual parity holds |
| Guidance articles (`content.py`) | 131 |
| Frontend HelpTipBlock mount points (sampled) | 89 |

**Bilingual coaching parity is intact at the tip level.** Every iter314–iter316
tip has its Spanish counterpart. The gaps below are in *content* (what coaching
exists at all) and *placement* (where HelpTipBlocks are mounted), not
*translation*.

---

## A · Employee Lifecycle coaching parity

### Existing families (✅ aligned with platform behavior)

| Family | Tips | Source |
|---|---|---|
| `employee-lifecycle` | 4 (canonical why/who/next/escalate) | iter224 |
| `employee-lifecycle.day-one` | 1 (next) | iter224 |
| `employee-lifecycle.documents` | 2 (why/mistake) | iter224 |
| `employee-lifecycle.first-impression` | 3 (why/mistake/example) | iter224 |
| `employee-lifecycle.welcome` | 2 (why/mistake) | iter224 |
| `employee-lifecycle.lifecycle-dates` | 3 (why/mistake/next) | iter285 |
| `employee-lifecycle.separation` | 3 (why/mistake/escalate) | iter285 |
| `employee-lifecycle.rehire` | 4 (why/mistake/next/escalate) | iter316 |

### Frontend mount points (`HrEmployees.jsx`)

| Line | Surface | Family |
|---|---|---|
| 141 | Page top banner | `employee-lifecycle` (showCounter) |
| 614 | Drawer Details tab | `employee-lifecycle.lifecycle-dates` |
| 790 | Status-change separation section | `employee-lifecycle.separation` |
| 823 | Status-change rehire-eligibility section | `employee-lifecycle.rehire` |
| 985 | Reactivate dialog | `employee-lifecycle.rehire` |

### Gaps

1. **`AddDialog` duplicate-warning has no coaching mount.**
   `hremp-add-dup-warning` is a hardcoded amber banner. The operator-mandate
   coaching tone for this decision ("find them, don't recreate them") lives in
   `employee-lifecycle.rehire` and is never shown at the warning surface — HR
   sees the warning, may dismiss it without ever seeing the coaching.
2. **`employee-lifecycle.lifecycle-dates`** is the only iter285+ family that
   does NOT carry a `kind="escalate"` tip — breaks canonical-4 coverage. The
   missing tip would explain "when a date dispute reaches HR" (employee
   contesting last-day-worked, supervisor contesting termination_date, etc.).
3. **No `employee-lifecycle.reactivate` slice.** The reactivate dialog mounts
   the broader `employee-lifecycle.rehire` family; that works today but the
   reactivate action is operationally distinct (preserves original_hire_date,
   appends `kind=reactivate` audit event, clears live termination dates while
   preserving them in history). A 1-2 tip dedicated slice would close the
   architectural-discipline reference at the action surface.

---

## B · Driver Qualification coaching parity

### Existing families (✅ aligned)

| Family | Tips | Source |
|---|---|---|
| `driver-qualification` | 4 (canonical) | iter286 |
| `driver-qualification.cdl-vs-approved` | **2 (why/mistake only)** | iter286 |
| `driver-qualification.dashboard` | 5 (canonical + 1 mistake) | iter288 |
| `driver-qualification.endorsements` | 4 (canonical) | iter287 |
| `driver-qualification.expirations` | **3 (why/next/escalate)** | iter286 |
| `driver-qualification.restrictions` | **2 (why/mistake only)** | iter287 |

### Frontend mount points

| File | Line | Family |
|---|---|---|
| `HrEmployees.jsx` | 702 | `driver-qualification` |
| `HrEmployees.jsx` | 703 | `driver-qualification.cdl-vs-approved` |
| `HrEmployees.jsx` | 736 | `driver-qualification.expirations` |
| `HrEmployees.jsx` | 743 | `driver-qualification.endorsements` |
| `HrEmployees.jsx` | 767 | `driver-qualification.restrictions` |
| `HrDriverQualificationDashboard.jsx` | 154 | `driver-qualification.dashboard` |

### Gaps

1. **`driver-qualification.cdl-vs-approved` lacks `next` + `escalate`.** The
   operator-named distinction (CDL holder ≠ Approved Company Driver) is the
   most safety-consequential field-edit decision in the dashboard yet only
   carries 2 of 4 canonical tips.
2. **`driver-qualification.expirations` lacks `mistake`.** The typical operator
   mistake ("we'll renew next week" / waiting for dispatch to be the renewal
   alarm) is the kind of coaching the platform should surface at the dashboard.
3. **`driver-qualification.restrictions` lacks `next` + `escalate`.** Air-brake
   and manual-transmission restrictions have direct dispatch implications
   (driver cannot be routed to certain equipment); a `next` tip would document
   that operationally.
4. **No `driver-qualification.medical-card` slice.** Medical card expiration is
   structurally distinct from CDL expiration (FMCSA 391.45 cadence differs;
   lapse means the driver cannot operate today, full stop). Conflating it with
   `driver-qualification.expirations` glosses over a high-consequence
   operational distinction.
5. **No `driver-qualification.tanker` slice.** Operator explicitly named
   tanker as operationally important (dewatering work). The endorsements
   family treats N/H/X/T/P/S generically; a tanker-specific slice (why MASCI
   cares specifically, which endorsement combination dispatch needs to see)
   would close this without expanding into generic endorsement coaching for
   codes MASCI rarely uses.

---

## C · Field Leadership Portal coaching parity

### Existing families

| Family | Tips | Notes |
|---|---|---|
| `field-leadership.records` | 4 | **LEGACY** — HR write-ups workflow |
| `field-leadership.records.documentation-discipline` | 2 | LEGACY |
| `field-leadership.records.follow-through` | 2 | LEGACY |
| `field-leadership.records.review-tone` | 2 | LEGACY |
| **`field-leadership.portal.*`** | **0** | **🔴 ENTIRELY MISSING** |

### Frontend mount points

| Page | HelpTipBlock count |
|---|---|
| `FieldLeadershipPortalLogin.jsx` | **0** 🔴 |
| `FieldLeadershipPortalDashboard.jsx` | **0** 🔴 |
| `FieldLeadershipPortalChangePassword.jsx` | **0** 🔴 |
| `HrFieldLeadershipUsers.jsx` | **0** 🔴 |
| `AdminFieldLeadershipUsersPanel.jsx` | **0** 🔴 |

### Gap — HIGHEST PRIORITY

**Iter314 shipped a brand new portal + a brand new HR/Admin management
surface with ZERO coaching layer.** A new Superintendent issued a per-user
FL Portal account today sees no inline coaching anywhere. Every existing
guidance article steers them to the legacy `/leadership/login` shared-password
gate (see §D), so they will bounce between the two surfaces with no platform
guidance distinguishing them.

### Recommended (operational tone, bounded)

| Family | Tips | Purpose |
|---|---|---|
| `field-leadership.portal` | canonical 4 (why/who/next/escalate) | Governed per-user identity here; distinct from legacy shared-password gate |
| `field-leadership.portal.first-login` | 2 (why/mistake) | Temp password + forced change; do not share |
| `field-leadership.portal.dispatch-scope` | 2 (why/escalate) | Today/tomorrow only · read-only · when FL needs further out |
| `field-leadership.portal.account-management` | 3 (why/mistake/escalate) | HR/Admin issuing/resetting/deactivating · distinct from Records · roster as source of truth |

Mount points needed: portal login (footer), dashboard (top), change-password
(above form), admin panel (top), HR host page (above panel, replacing the
current hardcoded blurb).

---

## D · Guidance Center article convergence

### Stale articles (`content.py`)

| Article id | Line | Issue |
|---|---|---|
| `onboard-leadership-first-week` | 1559 | Tells Supers/Foremen to use `/leadership/login` with shared password. Never mentions the iter314 per-user portal. **STALE.** |
| `tshoot-leadership-login` | 1607 | All troubleshooting steps assume the legacy shared-password gate. No "forgot password" / `must_change_password` / reset-link coverage for the new per-user portal. **STALE.** |
| `portal-leadership-identity` | 1647 | "How to access it: sign in at `/leadership/login` with the shared leadership password." Never mentions per-user portal. **STALE.** |
| `portal-leadership` | 1528 | Lists workflows accurately for HR Field Leadership Records; pre-dates iter314 — needs a one-paragraph reference to the per-user portal pathway. |
| `hr-offboarding` | 1435 | Doesn't mention required `separation_type` (iter285), required `rehire_eligibility` (iter316), Reactivate pathway, or `original_hire_date` write-once protection. **STALE.** |
| `hr-onboarding-new-hire` | 1318 | Mentions "field / shop / dispatch" portal accounts but not the new Field Leadership Portal account pathway. Mildly stale. |

### Missing articles (0 references in `content.py` body text)

| Topic | Evidence |
|---|---|
| **Driver Qualification overview** | The only reference is line 413 — a passing mention "Document expirations — driver's licenses, medical cards, certifications" inside an HR article. Zero dedicated article. |
| **CDL Holder vs Approved Company Driver** | Operator-named distinction. Zero article. |
| **Medical card expiration cadence** | FMCSA 391.45 differs from CDL renewal. Zero article. |
| **Tanker endorsement at MASCI** | Operator-named operational importance. Zero article. |
| **Rehire eligibility** | Iter316 contract. Zero article. `rehire`, `reactivat`, `review_required` all return 0 grep matches. |
| **Reactivation workflow** | Zero article. |
| **Lifecycle dates conceptual overview** | The 6 dates and their relationships. Zero article. |
| **FL Portal Accounts (per-user)** | Iter314 contract. Zero article. |

### Bilingual parity (article level)

Out of scope for this audit signal — already swept by iter279/280/281/297
incremental ES passes. The translation files (`translations_es_iter279.py`
through `translations_es_iter297.py`) exist as evidence those passes happened.
Verifying article-level bilingual parity belongs to a separate iter279-style
sweep, not this audit.

---

## Operational risks (from the gaps above)

1. **FL Portal coaching vacuum (HIGH).** A new Superintendent issued a per-user
   FL Portal account today sees no inline coaching anywhere. Every guidance
   article steers them to the legacy shared-password gate. They will bounce
   between surfaces with no platform signal distinguishing them.
2. **HR creating duplicates despite iter316 warning (MEDIUM).** AddDialog
   duplicate-warning has no coaching mounted. If HR clicks "Create new record
   anyway" they get no second-touch coaching reinforcing the reactivate path.
3. **Driver Qualification operational illiteracy (MEDIUM).** Dispatch /
   Safety / HR have no Guidance Center article to send new staff to before
   they make a dashboard-driven decision (e.g., dispatching a driver whose
   medical card lapses tomorrow). The dashboard exists; the explanatory
   article does not.
4. **Stale articles steer to deprecated workflow (MEDIUM).** Four FL articles
   all point to `/leadership/login` shared password; iter314 introduced the
   per-user portal alongside. Articles don't reflect both pathways.
5. **Canonical-4 incomplete on three driver-qualification slices (LOW).**
   `cdl-vs-approved` (2/4), `expirations` (3/4 · no mistake), `restrictions`
   (2/4) all lack the full set the iter224 standard documented.

---

## Recommended bounded closure sequence

All steps are single-purpose, independent, regression-protected, and reversible.
None require schema, permission, or architecture changes.

### iter317-A · Field Leadership Portal Coaching (HIGHEST PRIORITY)

- ADD coaching families in `tips.py` + `tips_es.py`:
  - `field-leadership.portal` (4 canonical)
  - `field-leadership.portal.first-login` (2)
  - `field-leadership.portal.dispatch-scope` (2)
  - `field-leadership.portal.account-management` (3)
- MOUNT HelpTipBlocks on five pages (login footer, dashboard top, change-pw
  above form, AdminFieldLeadershipUsersPanel top, HrFieldLeadershipUsers
  replacing the current hardcoded blurb).
- Tests: regression-test EN+ES coverage + presence at every mount point.

### iter317-B · Field Leadership Guidance Article Convergence

- MODIFY `onboard-leadership-first-week`, `tshoot-leadership-login`,
  `portal-leadership-identity`, `portal-leadership` to reflect BOTH pathways
  (legacy shared-password gate AND new per-user FL Portal) with an explicit
  "which one do I use?" decision at the top of each.
- ADD 1 article: `portal-field-leadership-portal-accounts` covering the
  per-user portal, who issues accounts, what's bounded, distinct from
  Records, distinct from the shared-password gate.

### iter317-C · Driver Qualification Guidance Article Convergence

- ADD 2-3 articles: `hr-driver-qualification-overview` (CDL vs Approved
  Driver, endorsements, restrictions, medical card cadence, tanker
  importance), `hr-driver-qualification-dashboard-howto` (how to read it,
  what each column means, when to act), `why-driver-qualification` (Why
  It Matters section).
- OPTIONAL coaching gap closure: add `mistake` to
  `driver-qualification.expirations`; add `next`+`escalate` to
  `driver-qualification.cdl-vs-approved`; add `next`+`escalate` to
  `driver-qualification.restrictions`; ADD slice
  `driver-qualification.medical-card` (3 tips); ADD slice
  `driver-qualification.tanker` (2 tips). All EN + ES.

### iter317-D · Lifecycle / Rehire Guidance Article Convergence

- MODIFY `hr-onboarding-new-hire` to reference `lifecycle_status` +
  `original_hire_date` + FL Portal account pathway.
- MODIFY `hr-offboarding` to mention `separation_type` + `rehire_eligibility`
  + Reactivate pathway + write-once protection.
- ADD 2 articles: `hr-rehire-reactivation` (when to reactivate, what gets
  preserved, the audit event), `hr-lifecycle-dates-and-tenure` (the six
  dates explained operationally).
- OPTIONAL: add `escalate` to `employee-lifecycle.lifecycle-dates` for
  canonical-4 coverage.

### iter317-E · AddDialog Duplicate-Warning Coaching Mount

- MOUNT `employee-lifecycle.rehire` HelpTipBlock above the amber duplicate
  warning in HrEmployees AddDialog when the warning fires. Single-line
  change. Reinforces the iter316 "find them, don't recreate them" coaching
  at the decision point.

---

## Out of scope (per operator instructions)

- ❌ No rewrites in this iteration
- ❌ No new LMS / onboarding academy / curriculum / tutorial system
- ❌ No HR policy manual expansion
- ❌ No compliance-suite drift
- ❌ No certifications / corporate training tone
- ❌ No `best practices` / `journey` / `empower` / `stakeholders` / `culture of` language in any future closure
- ❌ No legal-advice tone
- ❌ No dashboard or Guidance Center redesign
- ❌ No permission widening

---

## Tone reminder for the closure sequence (when operator approves)

All new coaching + guidance must remain:
- operational · concise · workflow-linked · accountability-oriented ·
  escalation-aware · bilingual · field-realistic · HR-realistic ·
  dispatch-realistic.

Anchor tone: same voice as the existing iter285 / iter286 / iter287 / iter288 /
iter316 tips. Re-read `employee-lifecycle.rehire` and
`driver-qualification.cdl-vs-approved` before authoring any new tip — those
two are the most recent operator-aligned examples and carry the right tone.

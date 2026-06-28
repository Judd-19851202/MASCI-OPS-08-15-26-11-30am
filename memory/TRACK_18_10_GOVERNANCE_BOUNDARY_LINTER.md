# TRACK 18.10 · Governance Boundary Linter

**Status:** ✅ GO · Permanent architecture guardrail · CI-enforced · Track 18.09C drift permanently prevented
**Date:** 2026-02-10

---

## Executive Summary

Track 18.09C closed a real architectural defect — six compat redirects inside `TransportationApp.jsx` silently bounced dispatch-authenticated users into the admin shell. The defect was small in code but symptomatic of a broader risk: **without a CI-enforced rule, any future feature accidentally born under `pages/admin/` would slowly re-create the same drift the Track 18.09C amendment just rejected.**

Track 18.10 ships that CI-enforced rule.

* A **governance-boundary registry** classifies every existing `pages/admin/*` file into GOVERNANCE, READ_ONLY_OVERSIGHT, or THIN_ALIAS.
* A new **linter test** (`backend/tests/test_track_18_10_governance_boundary_linter.py`) blocks any new file added under `pages/admin/` that does not appear in the registry (or fail one of the precise classification rules).
* The linter is **deliberately calibrated for low false-positives**: every existing file is grandfathered; the content-based scan only fires on NEW files with two or more high-confidence operational-execution signals.

---

## Constitutional rule

**Administration governs. Operations execute.**

* Transportation Operations runs transportation.
* Project Management runs projects.
* Human Resources runs workforce processes.
* Safety Operations runs safety work.
* Shop Operations runs shop and equipment work.
* Field Leadership runs field workflows.
* Dispatch execution remains dispatch execution.
* Administration does not own those workflows.

---

## Workstream summary

| Workstream | Result |
|---|---|
| 1 · Define governance vs operational ownership | `GOVERNANCE_BOUNDARY_LINTER_RULES.md` — registry + classifications + false-positive controls |
| 2 · Audit existing admin pages | `ADMIN_GOVERNANCE_BOUNDARY_AUDIT.md` — 43 files audited; **0 violations** |
| 3 · Build governance boundary linter | `backend/tests/test_track_18_10_governance_boundary_linter.py` — 34 assertions |
| 4 · Thin alias validation | `AdminTransportation.jsx` locked at ≤ 25 non-empty lines + single `export { default } from` |
| 5 · Admin read-only oversight validation | 7 pages classified READ_ONLY_OVERSIGHT; no forked logic |
| 6 · Protect Transportation ownership | `TransportationApp.jsx` locked as the operational source of truth; dual doorway preserved; redirects path-relative |
| 7 · Protect future workspace ownership | Linter blocks new operational pages under `pages/admin/` for Transportation, Dispatch, PM, HR, Safety, Shop, Field Leadership, Fleet/Equipment |

---

## What the linter checks

1. **Allow-list integrity.** Every existing `pages/admin/*` file must appear in the registry with classification GOVERNANCE / READ_ONLY_OVERSIGHT / THIN_ALIAS.
2. **New file gate.** A new file appearing under `pages/admin/` that is not in the registry triggers a linter failure with a helpful message guiding the developer to either (a) add it to the registry with a classification, (b) relocate to the owning operational workspace, or (c) make it a thin alias.
3. **Thin alias discipline.** `AdminTransportation.jsx` ≤ 25 non-empty lines + must contain exactly one `export { default } from "./transportation/TransportationApp"` import path.
4. **Operational-execution content scan** (NEW files only). Two or more high-confidence signals (`assignLoad(`, `assignDriver(`, `onboardDriver(`, `submitDailyReport(`, etc.) → FORBIDDEN classification.
5. **Track 18.09C contract preservation.** `TransportationApp.jsx` is the single source of truth; compat redirects path-relative; both doorways gated correctly in `App.js`.
6. **No new collections** (constitutional rule).
7. **No new endpoints** (except documented test/linter support).
8. **RBAC / auth helpers preserved** (no removal of `A`, `TX`, dispatch helpers).
9. **Dispatch portal preserved** (`/dispatch-portal/*`).
10. **Driver token surfaces preserved** (`/dr/*`).

---

## False-positive controls

* **Allow-list-first.** Existing files are grandfathered.
* **Two-signal threshold** for content scan.
* **Read-only oversight classification** explicitly carves out pages that *render* operational data through shared components.
* **Thin alias rule** matches a single canonical pattern (≤ 25 lines + one `export { default } from`).
* **Allow-list lives in human-readable markdown** so any maintainer can add a justified entry with a one-line review.

---

## Violations found

**None.** The 43 existing `pages/admin/*` files plus the one thin alias at `pages/AdminTransportation.jsx` all classify cleanly.

---

## Fixes made

* No code changes required to existing files — the audit passed clean.
* New lock test enforces the rule going forward.
* `scripts/deployment_gate.py` REGRESSION_FILES extended with Track 18.10.

---

## Routes / Auth / RBAC preserved

| Concern | Status |
|---|:---:|
| `/admin/transportation/*` admin-strict | ✅ Preserved |
| `/transportation-operations/*` TX-gated | ✅ Preserved |
| `/dispatch-portal/*` dispatch token gate | ✅ Preserved |
| `/dr/*` driver token gate | ✅ Preserved |
| `/api/admin/transportation/*` API prefix | ✅ Preserved |
| Backend collections | ✅ Preserved |
| Backend endpoints | ✅ Preserved |
| Auth helpers (`A`, `AP`, `TX`) | ✅ Preserved |
| Audit trail | ✅ Preserved |
| RBAC | ✅ Preserved |

---

## Dispatch / Driver validation

* `/dispatch-portal/*` → Dispatch operational system of record. Untouched.
* `/dr/*` → Driver self-service routes. Untouched.
* `/admin/dispatch` → classified READ_ONLY_OVERSIGHT. Admin variant of equipment availability/utilization. Operational execution remains at `/dispatch-portal/*`.

---

## Six-Pillar self-check

* Powerful ✅ — Operational work lives where operators actually work.
* Simple ✅ — Users are not forced into Administration to do normal work.
* Beautiful ✅ — Workspace architecture feels clean and intentional.
* Trusted ✅ — A route name reflects ownership and permission expectations.
* Proven ✅ — Enforced by CI, not memory. Future drift fails the gate.
* Operational ✅ — Dispatchers, PMs, HR, Safety, Shop, Field Leadership users can work in their own workspace.

---

## Risks

1. **Allow-list maintenance burden.** Every new governance page requires a one-line registry entry. Mitigation: the linter failure message is explicit and actionable; adding a row to a markdown table is trivial.
2. **Content-scan false positives** if a governance dashboard happens to use signal-shaped variable names. Mitigation: two-signal threshold and existing-file grandfathering eliminate this entirely.

## Deferrals

None.

---

## Final certification

🟢 **GO. Administration governs. Operations execute. Track 18.10 makes the rule permanent.**

The next time someone tries to build an operational execution page under `pages/admin/`, the deployment gate will reject the PR with a clear message: *"This file looks operational. Either relocate it to its owning workspace, or document it in `ADMIN_GOVERNANCE_BOUNDARY_AUDIT.md` with a clear classification."*

Future drift fails the gate.

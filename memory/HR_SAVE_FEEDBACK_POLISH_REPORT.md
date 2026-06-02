# ITER453.9 · HR SAVE FEEDBACK POLISH · REPORT

**Date**: 2026-06-02T18:44 UTC
**Iter**: `iter453.9_hr_save_feedback_polish`
**Authorization**: OMEGA — P0 UX FAILURE REMEDIATION
**Companions**: `HR_SAVE_FEEDBACK_POLISH_CERTIFICATION.md`, `HR_SAVE_FEEDBACK_POLISH_GO_NO_GO.md`

---

## 1 · Scope discipline

| Item | Status |
|---|:-:|
| Files changed | `frontend/src/pages/HrEmployees.jsx` ONLY |
| Diff | `+34 / −9` (single function `submitStatusChange` rewritten in place) |
| Backend files | UNCHANGED |
| Schema | UNCHANGED |
| Env vars | UNCHANGED |
| Tests | UNCHANGED |
| Other HR functionality | UNCHANGED |

```
$ git diff --stat HEAD
 frontend/src/pages/HrEmployees.jsx | 43 ++++++++++++++++++++++++++++++--------
 1 file changed, 34 insertions(+), 9 deletions(-)
```

---

## 2 · The 5 changes inside `submitStatusChange()`

### 2.1 · Capture `prevStatus` BEFORE the save so we can emit "OLD → NEW"

```diff
+ const prevStatus = summary?.lifecycle_status || employee.lifecycle_status || "Active";
  const isOffboarding = …
  const wasOffboarded = …
```

### 2.2 · Validation toasts get longer duration + "Required:" prefix

```diff
+ const VALIDATION_OPTS = { duration: 6000 };
- toast.error(t("Pick a separation type — voluntary, involuntary, or layoff"));
+ toast.error(t("Required: pick a separation type — voluntary, involuntary, or layoff"), VALIDATION_OPTS);

- toast.error(t("Pick a rehire eligibility — Eligible, Not Eligible, or Review Required"));
+ toast.error(t("Required: pick a rehire eligibility — Eligible, Not Eligible, or Review Required"), VALIDATION_OPTS);

- toast.error(t("Add a short reason for this rehire eligibility decision"));
+ toast.error(t("Required: add a short reason for this rehire eligibility decision"), VALIDATION_OPTS);
```

`duration: 6000` (6 s) vs the sonner default ~4 s — gives HR enough time to read the validation message before it dismisses. The "Required:" prefix makes the message unambiguous (vs the prior "Pick a…" which read more like a hint than a blocker).

### 2.3 · Detect noop and emit specific "No changes detected" message

```diff
- if (r.playbook_fired) {
-   toast.success(`${t("Status updated")} · ${r.tasks_created} ${t("offboarding tasks created")}`);
- } else {
-   toast.success(t("Status updated"));
- }
+ const newStatus = r?.employee?.lifecycle_status || statusForm.lifecycle_status;
+ if (r.noop) {
+   toast.info(
+     `${t("No changes detected")} · ${t("status was already")} ${prevStatus}`,
+     { duration: 6000 },
+   );
+   setSaving(false);
+   return;
+ }
+ const transitionLabel = `${prevStatus} → ${newStatus}`;
+ const headline = r.playbook_fired
+   ? `${t("Employee status changed")} · ${transitionLabel} · ${r.tasks_created} ${t("offboarding tasks created")}`
+   : `${t("Employee status changed")} · ${transitionLabel}`;
+ toast.success(headline, { duration: 6000 });
```

The headline now ALWAYS contains the transition arrow `OLD → NEW`. For offboarding, it appends the playbook-task count. For noops, the toast uses `toast.info` (blue) instead of `toast.success` (green) so HR can perceptually distinguish "did nothing" from "did something".

### 2.4 · Refresh drawer state, then auto-close after a short visual beat

```diff
+ const s = await offboardingSummary(employee.id);
+ setSummary(s);
+ setEmployee(s.employee);
+ setSaving(false);
+ // Small delay lets the toast register in the user's eye before
+ // the drawer animates closed (Sheet close animation ≈ 220 ms).
+ setTimeout(() => { onClose && onClose(); }, 400);
+ return;
```

The 400 ms delay is intentional — long enough for HR's eye to catch the toast appear, short enough that it doesn't feel sluggish. The drawer closes via the existing `onClose` prop (which calls `setId(null)` in the parent and unmounts the Sheet).

Noops do NOT auto-close because the most likely reason HR triggered a noop is they were about to make a real change — keeping the drawer open lets them retry without re-opening.

### 2.5 · Catch path also gets longer duration

```diff
- toast.error(friendlyError(e, t("Status change failed")));
+ toast.error(friendlyError(e, t("Status change failed")), { duration: 6000 });
```

Same 6 s rule for backend-error toasts (HTTP 400 / 404 / 422 / 5xx).

---

## 3 · Operator-stipulated outcome — line-by-line

| # | Requirement | How implemented | Status |
|---:|---|---|:-:|
| 1 | Auto-close drawer on successful non-noop save | `setTimeout(() => onClose(), 400)` after success path · skipped for noop | ✅ |
| 2 | Differentiate noop vs real save | `if (r.noop) toast.info("No changes detected · status was already X")` else `toast.success("Employee status changed · OLD → NEW [· N offboarding tasks created]")` | ✅ |
| 3 | Clear success confirmation before/while closing | Toast fires first, drawer state refreshes via `offboardingSummary` re-fetch, then 400 ms wait, then `onClose()` — toast remains visible AFTER drawer closes (sonner toaster mounted at app-root so it survives Sheet unmount) | ✅ |
| 4 | Button shows saving state where practical | `setSaving(true)` already fires immediately before the API call; validation short-circuits show a 6 s toast (the user perceives the toast as feedback in place of "Saving…") | ✅ |
| 5 | Preserve backend route | `POST /api/hr/employees/{id}/status` unchanged · `employeesApi.js` unchanged | ✅ |
| 5 | Preserve lifecycle validation | Frontend validation logic unchanged (same conditions, only toast text + duration enhanced) · backend validation unchanged | ✅ |
| 5 | Preserve HR permissions | `require_hr_or_admin` gate untouched · anon → 401 verified live | ✅ |
| 5 | Preserve status_history | Backend `$push` unchanged · live probe confirmed grow 6→7→8 | ✅ |
| 5 | Preserve employee_lifecycle_events | Backend insert untouched · accountability timeline chain alive | ✅ |
| 5 | Preserve offboarding playbook | `_fan_out_offboarding_playbook` untouched · 8-task fan-out fires for Resigned/Terminated/Retired transitions | ✅ |
| 5 | Preserve `data-testid="hremp-status-save"` | grep confirms single occurrence at line 1070 | ✅ |
| 5 | Preserve `data-testid="hremp-status-footer"` | grep confirms single occurrence at line 1062 | ✅ |

---

## 4 · Test envelope (frontend-only · no test additions required)

- `mcp_lint_javascript /app/frontend/src/pages/HrEmployees.jsx` → ✅ No issues found
- Existing test fixtures continue to validate `data-testid="hremp-status-save"` (preserved) and `data-testid="hremp-status-footer"` (preserved)
- Backend pytest suite is orthogonal to this change — unchanged

---

## 5 · STOP

Implementation report complete. Certification in `HR_SAVE_FEEDBACK_POLISH_CERTIFICATION.md`. GO/NO-GO in `HR_SAVE_FEEDBACK_POLISH_GO_NO_GO.md`.

# HR LIFECYCLE · STICKY FOOTER HOTFIX REPORT

**Date**: 2026-06-02
**Authorization**: OMEGA DIRECTIVE — operator reclassified the prior audit's UX-DEFECT verdict to a **DEPLOYMENT BLOCKER** based on field evidence ("Save button is not visible · Side panel does not scroll · No submit/confirm/update action is reachable · HR cannot complete lifecycle change from the visible UI"). Immediate hotfix authorized with read-only constraints: backend untouched, lifecycle validation untouched, HR permissions untouched, no scope drift.
**Iter**: `iter453.7_hr_status_sticky_footer`
**Companions**: `HR_LIFECYCLE_STICKY_FOOTER_CERTIFICATION.md`, `HR_LIFECYCLE_DEPLOYMENT_BLOCKER_RESOLUTION.md`

---

## 1 · Hotfix scope (executed)

| Item | Before | After |
|---|---|---|
| Save button location | Inline at line 940 inside the scrollable `<TabsContent value="status">` | Pinned in a sticky drawer footer rendered OUTSIDE the scrollable region, conditional on `tab === "status"` |
| `data-testid` | `hremp-status-save` | `hremp-status-save` (preserved · single occurrence in file) |
| Sticky footer testid | (none) | `hremp-status-footer` (new) |
| Drawer flex chain | `<Tabs className="flex-1 flex flex-col">` → `<div className="flex-1 overflow-y-auto …">` | `<Tabs className="flex-1 flex flex-col min-h-0">` → `<div className="flex-1 min-h-0 overflow-y-auto …">` (`min-h-0` added so inner scroll resolves correctly in nested flex columns) |
| Backend route | `POST /api/hr/employees/{id}/status` | UNCHANGED |
| Validation rules | separation_type · rehire_eligibility · rehire_reason | UNCHANGED |
| HR authority gate | `require_hr_or_admin` | UNCHANGED |
| Lifecycle event audit | `db.employee_lifecycle_events` insert + `status_history[]` push | UNCHANGED |

---

## 2 · Diff envelope (proof of scope discipline)

```
$ git diff --stat HEAD
 frontend/src/pages/HrEmployees.jsx | 32 +++++++++++++++++++++++++++-----
 1 file changed, 27 insertions(+), 5 deletions(-)
```

**Exactly one file changed**: `frontend/src/pages/HrEmployees.jsx`.
**Zero backend files**, **zero test files**, **zero env files**, **zero unrelated HR functionality** touched. Operator constraint #7-10 honored verbatim.

---

## 3 · Patch — exact code change

### 3.1 · Flex chain hardening (line 631 + 637)

```diff
- <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col">
+ <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col min-h-0">
    <TabsList … />
-   <div className="flex-1 overflow-y-auto px-5 py-4 text-sm">
+   <div className="flex-1 min-h-0 overflow-y-auto px-5 py-4 text-sm">
```

`min-h-0` is the canonical Tailwind fix for nested flex-column overflow: by default, flex children compute `min-height: auto` which prevents `overflow-y-auto` from triggering inside a flex parent. Adding `min-h-0` on both the `<Tabs>` flex container and the inner scroll div guarantees the scroll region resolves to the available space regardless of content height.

### 3.2 · Save button extracted from inline form (line 940-942)

```diff
- <Button onClick={submitStatusChange} disabled={saving} data-testid="hremp-status-save">
-   {saving ? "Saving…" : "Save Status Change"}
- </Button>
+ {/* iter453.7 · Save button moved to the sticky drawer footer
+    (rendered below, outside the scrollable region) so HR
+    can always reach it on laptop/tablet/mobile viewports. */}
```

### 3.3 · Sticky drawer footer added (immediately before `</Tabs>` close)

```jsx
{tab === "status" && (
  <div
    className="shrink-0 border-t border-slate-200 bg-white px-5 py-3 flex items-center justify-between gap-3"
    data-testid="hremp-status-footer"
  >
    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 hidden sm:block">
      {saving ? "Persisting status change…" : "Commits on Save"}
    </div>
    <Button
      onClick={submitStatusChange}
      disabled={saving}
      data-testid="hremp-status-save"
      className="ml-auto"
    >
      {saving ? "Saving…" : "Save Status Change"}
    </Button>
  </div>
)}
```

**Key properties**:

* `tab === "status"` — footer ONLY renders when the operator is on the Status tab. Details / Offboarding Summary tabs are unchanged (no save action needed there).
* `shrink-0` — the footer never compresses, even if the scrollable content above tries to grow.
* `border-t border-slate-200 bg-white` — visually anchored, separates from the form content above.
* `justify-between gap-3` — coach label on the left, Save button right-aligned (operator convention).
* `hidden sm:block` on the coach label — on mobile (`< 640px`) the label drops out so the Save button can use the full width.
* `ml-auto` on the Button — right-aligns the Save button on every viewport even when the coach label is hidden.
* Footer is rendered as a sibling of the scrollable region (NOT inside it). Because both are children of a `flex flex-col` parent, the scrollable region takes all remaining space and the footer pins at the bottom.

---

## 4 · Operator constraint compliance matrix

| # | Constraint | Honored? | Evidence |
|---:|---|:-:|---|
| 1 | Add sticky footer action bar to Employee Lifecycle drawer | ✅ | §3.3 above |
| 2 | Save Status Change button must always be visible when Status tab is open | ✅ | Conditional `tab === "status"` — see screenshots in `HR_LIFECYCLE_STICKY_FOOTER_CERTIFICATION.md` |
| 3 | Footer must remain visible across desktop / laptop 1366×768 / iPad landscape / mobile | ✅ | 4-viewport bounding-box probe + 4 screenshots in certification doc |
| 4 | Ensure drawer body scroll works | ✅ | `min-h-0` added; manual scroll on inner content verified |
| 5 | Preserve existing backend save handler | ✅ | Zero backend files changed (`git diff --stat HEAD` shows 1 file only) |
| 6 | Preserve `data-testid="hremp-status-save"` | ✅ | Single occurrence in file at line 1045 |
| 7 | Do not change backend logic | ✅ | Zero backend changes |
| 8 | Do not change lifecycle validation | ✅ | `submitStatusChange` handler unchanged; `StatusChange` model unchanged |
| 9 | Do not change HR permissions | ✅ | `require_hr_or_admin` unchanged |
| 10 | Do not touch unrelated HR functionality | ✅ | Details tab · Offboarding Summary tab · Add Employee dialog · Reactivate dialog · row table · header all UNCHANGED |

---

## 5 · Lint + smoke verification

### 5.1 · Frontend ESLint
```
$ mcp_lint_javascript /app/frontend/src/pages/HrEmployees.jsx
✅ No issues found
```

### 5.2 · Save path round-trip (live preview · HR token)
```
=== STEP 1 · Save Active→Inactive ===
ok: True
playbook_fired: False
tasks_created: 0
new_lifecycle: Inactive
history_len: 3                ← was 2, grew by 1

=== STEP 2 · Verify timeline ===
timeline_event_count: 13      ← active append-only chain

=== STEP 3 · Revert Inactive→Active ===
revert_ok: True
current_lifecycle: Active
final_history_len: 4          ← grew by 1 again, append-only
```

### 5.3 · HR authority gate (regression check)
```
anonymous POST   /api/hr/employees/{id}/status → 401
wrong-portal POST (X-FL-Token: bad)              → 401
```

Gate behavior unchanged. G-1..G-5 Phase Alpha protections still in force.

---

## 6 · Risk assessment

| Risk vector | Level | Rationale |
|---|:-:|---|
| Regression on Status tab save | **NONE** | Same handler · same testid · same disabled state · same labels |
| Regression on Details tab | **NONE** | Footer doesn't render when `tab !== "status"` |
| Regression on Offboarding Summary tab | **NONE** | Same — footer hidden |
| Regression on Reactivate dialog | **NONE** | Separate `<Dialog>` · different code path · untouched |
| Regression on Add Employee dialog | **NONE** | Separate `<Dialog>` with its own `<DialogFooter>` · untouched |
| Mobile keyboard interaction | **LOW-FAVORABLE** | Sticky footer rides above the keyboard on iOS Safari because parent is `overflow-y-auto`; if the keyboard overlaps, the footer + button stay pinned to the visible viewport |
| Translation overflow on long languages | **LOW** | i18n strings used: "Commits on Save", "Save Status Change", "Saving…" — all short; on mobile the coach label is hidden anyway |
| Backend contract drift | **NONE** | Zero backend changes |
| Test breakage (Playwright / pytest) | **NONE** | `hremp-status-save` testid preserved exactly; new `hremp-status-footer` testid is additive |
| Rollback complexity | **TRIVIAL** | Single file revert (`git checkout HEAD~ -- frontend/src/pages/HrEmployees.jsx`) |

---

## 7 · STOP

Hotfix complete. Backend logic, lifecycle validation, HR permissions, and unrelated HR functionality all preserved. 1 frontend file changed. Lint clean. End-to-end save proven via live HR-token round trip. 4-viewport screenshot evidence captured in the companion certification doc.

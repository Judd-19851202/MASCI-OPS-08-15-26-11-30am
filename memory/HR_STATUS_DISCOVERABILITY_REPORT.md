# PHASE 2 · HR STATUS DISCOVERABILITY REPORT (REC-2)

**Date**: 2026-06-02
**Batch**: ITER453.5 HR Lifecycle UX Hardening.
**Scope**: When HR clicks the employee status badge, open the drawer focused on the Status tab.

---

## 1 · Before (root cause of "where is the save button?")

* Default tab on drawer open: `useState("details")` (`HrEmployees.jsx:466`).
* Row click handler: `onClick={() => setEditId(e.id)}` (line 236) — entire row opens drawer to **Details**.
* Status editor and Save button live on the **Status** tab — second of three tabs.
* HR clicking the status badge had no shortcut; they had to click the row, see Details, and then click the Status tab.

## 2 · After (this batch)

Three coordinated changes inside `HrEmployees.jsx`:

### 2.1 New state in `HrEmployees`

```jsx
const [editTab, setEditTab] = useState("details");
```

### 2.2 Row click → Details (unchanged intent)

```jsx
<tr onClick={() => { setEditTab("details"); setEditId(e.id); }} …>
```

### 2.3 StatusBadge click → Status tab

The badge is now wrapped in a `<button>` whose own `onClick` calls `ev.stopPropagation()` and `setEditTab("status")`:

```jsx
<button
  type="button"
  onClick={(ev) => { ev.stopPropagation(); setEditTab("status"); setEditId(e.id); }}
  data-testid={`hremp-status-badge-${e.id}`}
  aria-label="Edit status"
>
  <StatusBadge kind="lifecycle" value={status} size="sm" />
</button>
```

### 2.4 `EmployeeDrawer` accepts `initialTab` prop

```jsx
function EmployeeDrawer({ id, onClose, initialTab = "details" }) {
  …
  const [tab, setTab] = useState(initialTab || "details");
  useEffect(() => { setTab(initialTab || "details"); }, [id, initialTab]);
  …
}

<EmployeeDrawer
  id={editId}
  initialTab={editTab}
  onClose={() => { setEditId(null); setEditTab("details"); fetchAll(); }}
/>
```

The `useEffect` re-seeds the tab when either `id` or `initialTab` changes, so consecutive opens (row vs badge) always land on the correct tab.

## 3 · Preserved

* No route changes (`/hr/employees` is unchanged).
* No permission changes (still HR-or-Admin gated).
* No workflow changes (status save flow is identical).
* Existing `data-testid="hremp-tab-status"` / `hremp-tab-details` / `hremp-tab-offboarding` unchanged.
* New `data-testid="hremp-status-badge-${id}"` added per row for testing.
* `aria-label="Edit status"` on the badge button preserves accessibility.

## 4 · LOC accounting

* `editTab` state: **2 lines** (declaration + comment).
* `EmployeeDrawer` signature + useState/useEffect: **2 lines added + 1 line modified** (with comment header inserted).
* Row click handler: **1 line modified**.
* StatusBadge wrapped in button: **9 lines** (replacing 1 line).
* `EmployeeDrawer` callsite: **4 lines** (replacing 1 line).

Net additions: ~12 functional lines + 3 comment lines.

## 5 · Result

🟢 **PASS.** HR's click on a status badge now opens the drawer directly on the Status tab with the save button visible. One click instead of three. Zero functional regression — the row body still opens to Details for unrelated edits.

## 6 · Operator alignment with success criteria

> HR can immediately find: "Where do I change status?" YES

The badge is now the affordance for status editing — HR sees the badge they want to change → clicks it → the Status tab appears with the dropdown, the Save button, and the status history all visible.

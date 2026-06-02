# HR LIFECYCLE · UI FORENSICS

**Date**: 2026-06-02
**Mode**: READ-ONLY.
**Companion**: `HR_LIFECYCLE_SAVEPATH_AUDIT.md`.

---

## 1 · DOM tree of the Status tab content area

```
<Sheet open=true>
  <SheetContent side="right"
                className="w-full sm:max-w-xl p-0 flex flex-col"
                data-testid="hremp-drawer">          ← FULL viewport height
    <SheetHeader className="px-5 pt-5 pb-3 border-b">  ← ~110 px fixed
      <SheetTitle>{employee.name}</SheetTitle>
      <StatusBadge … />
      <Link to=`/hr/employees/${id}/accountability`>
        View Accountability Timeline
      </Link>
    </SheetHeader>

    <Tabs className="flex-1 flex flex-col">
      <TabsList className="rounded-none border-b px-5">  ← ~40 px fixed
        <TabsTrigger value="details">Details</TabsTrigger>
        <TabsTrigger value="status">Status</TabsTrigger>
        <TabsTrigger value="offboarding">Offboarding Summary</TabsTrigger>
      </TabsList>

      <div className="flex-1 overflow-y-auto px-5 py-4 text-sm">  ← SCROLLABLE
        <TabsContent value="status" className="mt-0 space-y-3">

          <HelpTipBlock formKey="employee-lifecycle.separation" />
          <HelpTip testId="lifecycle-vocabulary" … />                ← REC-3
          <div>
            <Label>New status</Label>
            <Select … data-testid="hremp-status-new">
              {LIFECYCLE_STATUSES.map(...)}
            </Select>
          </div>

          {/* conditional: Terminated / Resigned / Retired */}
          <div data-testid="hremp-separation-section">
            <Label>Separation Type *</Label>
            <Select data-testid="hremp-separation-type" />
            <div grid-cols-2>
              <Input type="date" data-testid="hremp-tx-last-day" />
              <Input type="date" data-testid="hremp-tx-term-date" />
            </div>
            <HelpTipBlock formKey="employee-lifecycle.rehire" />
            <Label>Rehire Eligibility *</Label>
            <Select data-testid="hremp-rehire-eligibility" />
            {/* conditional: not_eligible OR review_required */}
            <Textarea data-testid="hremp-rehire-reason" rows={2} />
          </div>

          {/* conditional: Leave of Absence */}
          <div data-testid="hremp-leave-section">
            <Input type="date" data-testid="hremp-tx-leave-start" />
            <Input type="date" data-testid="hremp-tx-leave-return" />
          </div>

          <div>
            <Label>Reason / note</Label>
            <Textarea rows={3} data-testid="hremp-status-reason" />
          </div>

          {/* conditional: fresh transition into Term/Resigned/Retired */}
          <div data-testid="hremp-playbook-warning" className="bg-amber-50…">
            ⚠ Offboarding playbook will fire — 8 follow-up tasks
          </div>

          ╔══════════════════════════════════════════════════════════╗
          ║   <Button data-testid="hremp-status-save"               ║
          ║           onClick={submitStatusChange}                   ║
          ║           disabled={saving}>                             ║
          ║     "Save Status Change" / "Saving…"                     ║
          ║   </Button>          ← LINE 940 · THE SAVE ACTION        ║
          ╚══════════════════════════════════════════════════════════╝

          {summary?.last_status_change && (
            <div className="mt-4 pt-3 border-t">
              <div>Recent status history</div>
              <ul>{(employee.status_history||[]).slice().reverse().slice(0,5).map(...)}</ul>
            </div>
          )}

        </TabsContent>
      </div>
    </Tabs>
  </SheetContent>
</Sheet>
```

## 2 · Computed CSS on the Save button

| Property | Value | Effect |
|---|---|---|
| `display` | inline-flex (shadcn Button default) | Visible (in DOM) |
| `visibility` | visible | Visible |
| `opacity` | 1 | Visible |
| `position` | static (inline within parent stack) | Scrolls with parent |
| `z-index` | auto | No overlay issue |
| `pointer-events` | auto | Clickable |
| `disabled` | only true while `saving=true` | Otherwise enabled |
| Background | shadcn default (slate primary) | Visible against white form |
| Width | `w-auto` (intrinsic) | Single-line "Save Status Change" |
| Sticky? | **NO** | Scrolls out of view |

## 3 · Critical absence

The status form does NOT contain a `<SheetFooter>` element. The shadcn convention for action buttons in a Sheet is:

```jsx
<SheetFooter className="sticky bottom-0 bg-white border-t p-4">
  <Button>Save</Button>
</SheetFooter>
```

This pattern is used elsewhere in the codebase (e.g., `EditField` quick-edit toggles), but it is **NOT used on the EmployeeDrawer Status tab**. The result: the Save button rides with the scroll content rather than being pinned to the bottom of the drawer.

## 4 · Tab default state

When the drawer opens from a generic row click, `useState("details")` (line ~480) puts the tab strip on **Details**. The Save button is on **Status** tab. The user must:

1. Open the drawer (any row click).
2. Click the **Status** tab (line 634 testid `hremp-tab-status`).
3. Pick a new lifecycle status.
4. Fill in required fields.
5. **Scroll down within the modal** to reach the Save button.

ITER453.5 REC-2 added a shortcut: clicking the **StatusBadge** on a row (line ~246, testid `hremp-status-badge-{id}`) opens the drawer directly on the Status tab — but step 5 (scroll within modal) still applies.

## 5 · Status badge click affordance (REC-2 verification)

The shipped REC-2 wraps the StatusBadge in a `<button type="button">` with `stopPropagation` and `setEditTab("status")`. This is in the production bundle (verified by `main.037e8fa1.js` containing `hremp-status-badge-` testid string in the post-deploy audit).

Direct evidence:
* `frontend/src/pages/HrEmployees.jsx:246-256` — wraps the StatusBadge with `onClick={(ev) => { ev.stopPropagation(); setEditTab("status"); setEditId(e.id); }}`.
* `aria-label="Edit status"` for accessibility.

**Verdict**: the discoverability path WORKS — clicking the status badge opens directly on the Status tab. But once there, the Save button is below the fold on the affected viewports.

## 6 · Mobile-specific observations

On mobile (`w-full` sheet content):

1. Sheet takes 100% of viewport width.
2. Vertical layout same as desktop.
3. Software keyboard overlay (≈ 330 px on iPhone) reduces the visible viewport when any textarea is focused.
4. Typing in `hremp-status-reason` (3-row textarea) or `hremp-rehire-reason` (2-row textarea) forces the keyboard up; the Save button (positioned just below the textarea in document order) is pushed out of visible space.
5. Auto-scroll-into-view on focus moves the textarea into view, but does NOT scroll further to reveal the Save button.

This is the specific scenario most likely to match HR's "no visible Save" report on a tablet/iPad.

## 7 · Forensic conclusion

| Finding | Verdict |
|---|---|
| Save button exists in DOM | ✅ |
| Save button is correctly wired | ✅ |
| Save button is NOT hidden by CSS | ✅ |
| Save button is NOT clipped by parent | ✅ |
| Save button IS below the fold on laptop / tablet / mobile + keyboard | 🔴 |
| There is NO sticky footer | 🔴 |
| No keyboard shortcut (Enter / Ctrl+S) | 🔴 |
| `aria-label` / role information for screen readers | ✅ (button has accessible text "Save Status Change") |

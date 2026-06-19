# TRACK 15.39A · Frontend Implementation Handoff Plan

**Track:** 15.39A · single-session fork plan · NO code changed in this session
**Prerequisite:** Track 15.39 backend complete + certified (PATCH/DELETE/audit all live)
**Target:** complete the entire Team Assignment P2 frontend in one fresh-context fork session

---

## 0 · T0 Fixture Seed Block — known-good 2-row scenario

> The fork session runs this BEFORE writing any code. It produces a deterministic
> 2-assignment fixture (Alec Perkins · foreman + safety_rep on project `20-07`)
> against PREVIEW only, captures both `assignment_id`s + the audit baseline count,
> and is the same fixture the cert procedure in §6 references. Re-runnable
> (deactivates any prior active rows for the same user×project before reseeding).

### 0.1 · Constants (preview-only)
```
PROJECT     = "20-07"
EMPLOYEE_ID = "c9d7ebc3-a292-4d7a-8765-0ce2739c6029"     # Alec Perkins (preview directory)
EMPLOYEE_EMAIL = "alec.perkins@mascigc.com"              # display sanity check
SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASS  = "Maddix123!"
ROLES       = ["foreman", "safety_rep"]
```

### 0.2 · Seed commands (paste verbatim into the fork session shell)
```bash
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

# 1. Mint admin token via super-admin multi-login
ADMIN_TOK=$(curl -sS -X POST "$API/api/auth/multi-login" \
    -H "Content-Type: application/json" \
    -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['portal_tokens']['admin'])")
echo "ADMIN_TOK len: ${#ADMIN_TOK}"   # expect 64

# 2. Baseline audit count BEFORE seed
BASE_AUDIT=$(curl -sS "$API/api/admin/jobs/20-07/team/audit?limit=500" \
    -H "X-Admin-Token: $ADMIN_TOK" \
  | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('items',[])))")
echo "BASE_AUDIT_COUNT=$BASE_AUDIT"

# 3. Cleanup: remove any pre-existing active rows for this user×project
#    (idempotent — DELETE 404 is fine when none exist)
EXISTING=$(curl -sS "$API/api/admin/jobs/20-07/team" \
    -H "X-Admin-Token: $ADMIN_TOK" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(' '.join([i['id'] for i in d.get('items',[]) if i.get('active') and i.get('user_id')=='c9d7ebc3-a292-4d7a-8765-0ce2739c6029']))")
for AID in $EXISTING; do
  curl -sS -X DELETE "$API/api/admin/jobs/20-07/team/$AID" \
       -H "X-Admin-Token: $ADMIN_TOK" \
       -H "Content-Type: application/json" \
       -d '{"reason_category":"reassigned","reason_text":"T0 cleanup before seed"}' >/dev/null
done

# 4. Seed Row A — foreman
ROW_A=$(curl -sS -X POST "$API/api/admin/jobs/20-07/team" \
    -H "X-Admin-Token: $ADMIN_TOK" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"c9d7ebc3-a292-4d7a-8765-0ce2739c6029","assignment_role":"foreman","notes":"T0 fixture · foreman"}')
ASSIGN_FOREMAN=$(echo "$ROW_A" | python3 -c "import sys,json;print(json.load(sys.stdin)['assignment']['id'])")
echo "ASSIGN_FOREMAN=$ASSIGN_FOREMAN"

# 5. Seed Row B — safety_rep
ROW_B=$(curl -sS -X POST "$API/api/admin/jobs/20-07/team" \
    -H "X-Admin-Token: $ADMIN_TOK" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"c9d7ebc3-a292-4d7a-8765-0ce2739c6029","assignment_role":"safety_rep","notes":"T0 fixture · safety_rep"}')
ASSIGN_SAFETY=$(echo "$ROW_B" | python3 -c "import sys,json;print(json.load(sys.stdin)['assignment']['id'])")
echo "ASSIGN_SAFETY=$ASSIGN_SAFETY"

# 6. Verify
curl -sS "$API/api/admin/jobs/20-07/team" -H "X-Admin-Token: $ADMIN_TOK" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);rows=[i for i in d.get('items',[]) if i.get('active') and i.get('user_id')=='c9d7ebc3-a292-4d7a-8765-0ce2739c6029'];print('SEEDED_ACTIVE_ROWS:',len(rows));[print(r['id'],r['assignment_role']) for r in rows]"
```

### 0.3 · Expected output
```
ADMIN_TOK len: 64
BASE_AUDIT_COUNT=<N>            # captured baseline
ASSIGN_FOREMAN=<uuid-1>         # used by T1 (Change Role), T3 (Remove), T5 (History)
ASSIGN_SAFETY=<uuid-2>          # used by T2 (Duplicate Role 409)
SEEDED_ACTIVE_ROWS: 2
<uuid-1> foreman
<uuid-2> safety_rep
```

### 0.4 · Per-test references
| Test | Uses fixture row |
|---|---|
| T1 Change Role inline | `$ASSIGN_FOREMAN` · change `foreman → assistant_superintendent`, then back to `foreman` for repeatability |
| T2 Duplicate role guard | `$ASSIGN_SAFETY` · try to change to `foreman` → 409 because `$ASSIGN_FOREMAN` already holds it |
| T3 Remove with reason | `$ASSIGN_SAFETY` · remove with `reason_category=staffing_adjustment` |
| T4 Other-requires-text | `$ASSIGN_FOREMAN` · open dialog only — close without submitting (no state mutation) |
| T5 History Drawer | reads project-wide audit · expects ≥ 1 each of assign / role_change / remove from T1+T3 |
| T6 Performance | reuses T1 + T3 timings |

### 0.5 · Teardown (post-cert)
```bash
# Idempotent — remove both seeded rows with a structured reason so the audit trail is clean
for AID in $ASSIGN_FOREMAN $ASSIGN_SAFETY; do
  curl -sS -X DELETE "$API/api/admin/jobs/20-07/team/$AID" \
       -H "X-Admin-Token: $ADMIN_TOK" \
       -H "Content-Type: application/json" \
       -d '{"reason_category":"project_complete","reason_text":"T0 fixture teardown after Track 15.39A cert"}' >/dev/null
done
```

### 0.6 · Guard-rails
* PREVIEW only — script must NOT run against production (`DB_NAME=masci_safety`). Verify by hitting `/api/admin/env-check` or by visually confirming the amber preview banner.
* If step 4 or 5 returns 409 ("User already holds the ... role"), step 3 cleanup did not complete — re-run step 3 then resume.
* If the directory does not contain Alec Perkins under the documented `EMPLOYEE_ID`, fall back to: pick any active employee from `GET /api/admin/directory/k4/users?limit=10` and substitute `EMPLOYEE_ID` everywhere above.

---

## 1 · Architecture map (already-existing files the fork edits / creates)

| Path | Role | Action |
|---|---|---|
| `/app/frontend/src/components/team/JobTeamRosterPanel.jsx` | **Primary component** · current roster · holds `prompt()` calls + history toggle | **EDIT** — replace prompts, add role-change inline control, swap inline audit panel for drawer |
| `/app/frontend/src/lib/teamRosterApi.js` | API wrapper · already exports `fetchTeam`, `fetchTeamAudit`, `addTeamMember`, `patchTeamMember`, `removeTeamMember`, `transferTeamMember` | **EDIT** — extend `patchTeamMember` to accept `assignment_role` · extend `removeTeamMember` to send JSON body `{reason_category, reason_text}` instead of `?reason=` query |
| `/app/frontend/src/components/team/RemoveReasonDialog.jsx` | NEW shadcn Dialog | **CREATE** |
| `/app/frontend/src/components/team/AssignmentHistoryDrawer.jsx` | NEW shadcn Sheet | **CREATE** |
| `/app/frontend/src/pages/admin/AdminJobTeam.jsx` | Admin team page wrapper · already uses `JobTeamRosterPanel` | NO CHANGE (UI surface is the panel) |
| `/app/frontend/src/pages/pm/PmJobTeam.jsx` | PM team page wrapper · `pmScope=true` (limited role set, no audit drawer per existing rule) | NO CHANGE for Change Role + Remove Dialog. History Drawer stays admin-only as designed. |

Existing `data-testid` on the panel (line 295, 601, 605): `job-team-audit-toggle`, `job-team-audit-drawer`. Reuse these. Add new ones (see §5).

---

## 2 · Backend endpoints (already certified — DO NOT touch)

### Change Role
```
PATCH /api/admin/jobs/{project_number}/team/{assignment_id}
Headers: X-Admin-Token: <admin token>
Body:    { "assignment_role": "<new_role_key>" }

→ 200 { "ok": true, "assignment": {...}, "role_changed": true }
→ 409 { "detail": "User already holds the <Role> role on this project. Remove the existing assignment first." }
→ 404 { "detail": "assignment not found" }
→ 400 { "detail": "unknown assignment_role: <value>" }
```

### Remove with structured reason
```
DELETE /api/admin/jobs/{project_number}/team/{assignment_id}
Headers: X-Admin-Token: <admin token>
         Content-Type: application/json
Body:    { "reason_category": "<one of 7>", "reason_text": "<optional unless other>" }

Allowed reason_category values (lowercase, exact):
  reassigned · staffing_adjustment · promotion · demotion ·
  project_complete · left_company · other

→ 200 { "ok": true }
→ 400 { "detail": "reason_text is required when reason_category is 'other'." }
→ 400 { "detail": "unknown reason_category: <value>. Allowed: [...]" }
→ 404 { "detail": "active assignment not found" }
```

### Assignment history (already works)
```
GET /api/admin/jobs/{project_number}/team/audit?limit=100
Headers: X-Admin-Token: <admin token>

→ 200 { "items": [
    {
      "id": "<audit row id>",
      "at": "2026-06-19T11:52:09.123Z",
      "action": "assign" | "role_change" | "update" | "remove",
      "project_number": "20-07",
      "assignment_role": "foreman",
      "target_user_id": "...",
      "target_email": "...",
      "before": { ... },
      "after": { ... },
      "actor_id": "...",
      "actor_name": "Admin",
      "notes": "role: Foreman → Assistant Superintendent"
              | "Reassigned: moved to new project"
              | "Other: <free text>"
              | null
    }, ...
  ] }
```

---

## 3 · React components to build

### 3A · `RemoveReasonDialog.jsx` (NEW · shadcn Dialog)

```jsx
// /app/frontend/src/components/team/RemoveReasonDialog.jsx
import { Dialog, DialogContent, DialogHeader, DialogTitle,
         DialogDescription, DialogFooter } from "../ui/dialog";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";

const CATEGORIES = [
  { key: "reassigned",          label: "Reassigned" },
  { key: "staffing_adjustment", label: "Staffing Adjustment" },
  { key: "promotion",           label: "Promotion" },
  { key: "demotion",            label: "Demotion" },
  { key: "project_complete",    label: "Project Complete" },
  { key: "left_company",        label: "Left Company" },
  { key: "other",               label: "Other" },
];

export function RemoveReasonDialog({
  open, onOpenChange,
  member,                // { id, display_name, role_label }
  onConfirm,             // (reason_category, reason_text) => Promise<void>
}) {
  const [category, setCategory] = useState("reassigned");
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const otherRequiresText = category === "other" && !text.trim();

  async function handleSubmit() {
    setSubmitting(true); setError(null);
    try {
      await onConfirm(category, text.trim() || undefined);
      onOpenChange(false);
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="remove-reason-dialog" className="max-w-md">
        <DialogHeader>
          <DialogTitle>Remove {member?.display_name}</DialogTitle>
          <DialogDescription>
            Currently {member?.role_label}. Choose a reason for the audit log.
          </DialogDescription>
        </DialogHeader>
        <RadioGroup value={category} onValueChange={setCategory} className="space-y-2">
          {CATEGORIES.map(c => (
            <div key={c.key} className="flex items-center gap-2">
              <RadioGroupItem value={c.key} id={`reason-${c.key}`}
                              data-testid={`reason-${c.key}`}/>
              <Label htmlFor={`reason-${c.key}`} className="cursor-pointer">
                {c.label}
              </Label>
            </div>
          ))}
        </RadioGroup>
        <Textarea
          data-testid="reason-text"
          placeholder={category === "other"
                       ? "Required — explain the reason"
                       : "Optional notes"}
          value={text}
          onChange={e => setText(e.target.value)}
          rows={3}
        />
        {error && <p data-testid="reason-error" className="text-sm text-red-600">{error}</p>}
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}
                  disabled={submitting}
                  data-testid="reason-cancel">Cancel</Button>
          <Button onClick={handleSubmit}
                  disabled={submitting || otherRequiresText}
                  data-testid="reason-submit">
            {submitting ? "Removing…" : "Remove"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### 3B · `AssignmentHistoryDrawer.jsx` (NEW · shadcn Sheet)

```jsx
// /app/frontend/src/components/team/AssignmentHistoryDrawer.jsx
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "../ui/sheet";
import { Badge } from "../ui/badge";

const ACTION_META = {
  assign:      { label: "ASSIGNED",     classes: "bg-emerald-100 text-emerald-800" },
  role_change: { label: "ROLE CHANGED", classes: "bg-amber-100  text-amber-800"   },
  update:      { label: "UPDATED",      classes: "bg-blue-100   text-blue-800"    },
  remove:      { label: "REMOVED",      classes: "bg-red-100    text-red-800"     },
};

export function AssignmentHistoryDrawer({ open, onOpenChange, items }) {
  // items already newest-first from backend; defensively re-sort if needed
  const sorted = [...(items || [])].sort((a,b) => (b.at || "").localeCompare(a.at || ""));
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl overflow-y-auto"
                    data-testid="assignment-history-drawer">
        <SheetHeader>
          <SheetTitle>Assignment History</SheetTitle>
          <SheetDescription>Read-only audit · newest first</SheetDescription>
        </SheetHeader>
        <div className="mt-4 space-y-2" data-testid="history-list">
          {sorted.length === 0 && (
            <p className="text-sm text-slate-500">No history yet.</p>
          )}
          {sorted.map(ev => {
            const meta = ACTION_META[ev.action] || ACTION_META.update;
            const oldRole = ev.before?.role_label || ev.before?.assignment_role;
            const newRole = ev.after?.role_label  || ev.after?.assignment_role;
            return (
              <div key={ev.id} className="border rounded p-3 bg-white"
                   data-testid={`history-row-${ev.action}`}>
                <div className="flex items-center justify-between">
                  <Badge className={meta.classes}>{meta.label}</Badge>
                  <span className="text-xs text-slate-500">
                    {new Date(ev.at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-2 text-sm font-medium">
                  {ev.target_email || ev.before?.email || ev.after?.email || "(unknown)"}
                </p>
                <p className="text-xs text-slate-600">
                  {ev.action === "role_change"
                    ? <>{oldRole} → <strong>{newRole}</strong></>
                    : ev.assignment_role && (ev.after?.role_label || ev.assignment_role)}
                </p>
                {ev.notes && (
                  <p className="text-xs text-slate-700 mt-1 italic">{ev.notes}</p>
                )}
                <p className="text-xs text-slate-500 mt-1">by {ev.actor_name || ev.actor_id}</p>
              </div>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

### 3C · `JobTeamRosterPanel.jsx` edits

**Replace** the `prompt(...)` block (lines 241-242) with state + dialog:

```jsx
const [removeTarget, setRemoveTarget] = useState(null);   // member to remove
async function handleRemoveConfirm(category, text) {
  await removeTeamMember(projectNumber, removeTarget.id,
                         { reason_category: category, reason_text: text },
                         { adminScope });
  setRemoveTarget(null);
  await reloadRoster();        // re-fetches team + audit
}
// in the row's Remove button onClick:
<Button data-testid={`row-remove-${it.id}`}
        onClick={() => setRemoveTarget(it)}>Remove</Button>
// at the bottom of the panel JSX:
<RemoveReasonDialog
  open={!!removeTarget}
  onOpenChange={(v) => !v && setRemoveTarget(null)}
  member={removeTarget}
  onConfirm={handleRemoveConfirm}
/>
```

**Add** inline role-change `<Select>` per row (shadcn `select.jsx`):

```jsx
async function handleRoleChange(it, newRole) {
  if (newRole === it.assignment_role) return;
  setRowBusy(it.id, true);
  try {
    await patchTeamMember(projectNumber, it.id, { assignment_role: newRole });
    await reloadRoster();
    toast.success(`Role changed to ${roleRegistry[newRole]?.label || newRole}`);
  } catch (e) {
    if (e.status === 409) toast.error(e.detail);   // duplicate role on project
    else toast.error(e?.message || "Role change failed");
  } finally {
    setRowBusy(it.id, false);
  }
}
// in each row, where role_label is displayed:
<Select value={it.assignment_role} onValueChange={(v) => handleRoleChange(it, v)}
        disabled={rowBusy[it.id]}>
  <SelectTrigger data-testid={`row-role-${it.id}`} className="w-56">
    <SelectValue/>
  </SelectTrigger>
  <SelectContent>
    {availableRoleKeys.map(k => (
      <SelectItem key={k} value={k}
                  data-testid={`row-role-${it.id}-opt-${k}`}>
        {roleRegistry[k]?.label || k}
      </SelectItem>
    ))}
  </SelectContent>
</Select>
```

**Replace** the inline audit block (lines 601-610) with a Drawer trigger:

```jsx
<Button variant="outline" size="sm"
        data-testid="open-history-drawer"
        onClick={() => setHistoryOpen(true)}>
  Assignment History ({audit.length})
</Button>
<AssignmentHistoryDrawer
  open={historyOpen}
  onOpenChange={setHistoryOpen}
  items={audit}
/>
```

### 3D · `teamRosterApi.js` edits

```js
// patchTeamMember: already takes a body — no change needed; just call with
//   patchTeamMember(pn, id, { assignment_role: newRoleKey })

// removeTeamMember: change from query string to JSON body
export async function removeTeamMember(projectNumber, assignmentId, body, { adminScope = false } = {}) {
  const url = adminScope ? "/api/admin/jobs/" : "/api/pm/jobs/";
  const res = await fetch(`${API_BASE}${url}${projectNumber}/team/${assignmentId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", ...adminHeaders() },
    body: JSON.stringify({
      reason_category: body?.reason_category || null,
      reason_text:     body?.reason_text     || null,
    }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const err = new Error(detail.detail || `HTTP ${res.status}`);
    err.status = res.status;
    err.detail = detail.detail;
    throw err;
  }
  return res.json();
}
```

> **Migration note:** every existing call site passes a STRING reason; convert call sites in `JobTeamRosterPanel.jsx` to pass `{ reason_category, reason_text }`. There's only ONE call site (line 244).

---

## 4 · shadcn components inventory (already installed)

All required components already exist under `/app/frontend/src/components/ui/`:
* `dialog.jsx` (for RemoveReasonDialog)
* `sheet.jsx` (for AssignmentHistoryDrawer)
* `select.jsx` (for inline role change)
* `radio-group.jsx` (for reason category)
* `label.jsx`
* `textarea.jsx`
* `button.jsx`
* `badge.jsx`

No installation needed.

---

## 5 · Test-ID surface (Playwright cert depends on these)

| Element | data-testid |
|---|---|
| Inline role select per row | `row-role-{assignment_id}` |
| Role select option | `row-role-{assignment_id}-opt-{role_key}` |
| Remove button per row | `row-remove-{assignment_id}` |
| Remove dialog | `remove-reason-dialog` |
| Reason radio per category | `reason-{category}` |
| Reason text area | `reason-text` |
| Reason error | `reason-error` |
| Reason cancel | `reason-cancel` |
| Reason submit | `reason-submit` |
| History trigger button | `open-history-drawer` |
| History drawer | `assignment-history-drawer` |
| History list | `history-list` |
| History row by action | `history-row-{assign|role_change|update|remove}` |

---

## 6 · Certification procedure

### 6.1 · Setup (fork session start)

```bash
# Fresh admin token against PREVIEW
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
SUPER=$(curl -sS -X POST "$API/api/auth/multi-login" -H "Content-Type: application/json" \
        -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}')
ADMIN_TOK=$(echo "$SUPER" | python3 -c "import sys,json;print(json.load(sys.stdin)['portal_tokens']['admin'])")
# Probe project: 20-07 · Probe employee: c9d7ebc3-a292-4d7a-8765-0ce2739c6029 (Alec Perkins)
```

### 6.2 · Browser cert (Playwright via mcp_screenshot_tool)

For each viewport in §6.3, run six tests:

#### T1 · Change Role inline
1. Navigate to `/admin/jobs/20-07/team` (or wherever `AdminJobTeam` mounts)
2. Locate row with our pre-seeded assignment (created via curl pre-test)
3. Click `[data-testid="row-role-<id>"]` → select Assistant Superintendent option
4. Wait for toast success / loading spinner clears
5. Hard refresh page (`page.reload()`)
6. Assert the SELECT value reflects `assistant_superintendent`
7. Curl `/api/admin/jobs/20-07/team/audit?limit=5` and assert exactly one `role_change` row exists for this id (not assign+remove pair)

#### T2 · Duplicate role guard (409)
1. Pre-seed TWO assignments for the same employee on `20-07` via curl (foreman + safety_rep)
2. Try to change safety_rep row → foreman via UI
3. Assert error toast contains "User already holds the Foreman role on this project"
4. Assert no row mutation happened (refresh, both roles still present)

#### T3 · Remove with structured reason
1. Click `[data-testid="row-remove-<id>"]`
2. Assert `[data-testid="remove-reason-dialog"]` visible
3. Click `[data-testid="reason-promotion"]`
4. Optionally type "moved up to PM" in `[data-testid="reason-text"]`
5. Click `[data-testid="reason-submit"]`
6. Hard refresh page
7. Curl team list — assert removed row has `active=false`, `remove_reason_category="promotion"`, `remove_reason_text="moved up to PM"`

#### T4 · Other requires text
1. Open remove dialog
2. Select `[data-testid="reason-other"]`
3. Leave text blank → assert `[data-testid="reason-submit"]` is `disabled`
4. Type "test" → assert button enables
5. Clear text → assert button disables again

#### T5 · History Drawer
1. Click `[data-testid="open-history-drawer"]`
2. Assert `[data-testid="assignment-history-drawer"]` visible
3. Assert at least one of each: `history-row-assign`, `history-row-role_change`, `history-row-remove`
4. Assert first row's timestamp > second row's timestamp (newest first)
5. Assert each row shows actor name + role + (where applicable) reason
6. Close drawer via Esc or outside-click — assert it dismisses cleanly

#### T6 · Performance
* `change-role` action → toast success in < 5s (measure with `Date.now()` deltas)
* `remove` action → toast success in < 5s
* `open-history-drawer` click → drawer rendered in < 2s

### 6.3 · Viewport test matrix

| Test | Desktop 1920×800 | iPad portrait 768×1024 | iPad landscape 1024×768 |
|---|---|---|---|
| T1 Change Role | ✓ run | ✓ run | ✓ run |
| T2 Duplicate guard | ✓ run | ✓ run | ✓ run |
| T3 Remove Dialog | ✓ run | ✓ run | ✓ run |
| T4 Other-requires-text | ✓ run | ✓ run | ✓ run |
| T5 History Drawer | ✓ run | ✓ run | ✓ run |
| T6 Performance | desktop only | iPad portrait only | (skip — re-uses landscape T1-T5 timings) |

Playwright viewport setup:
```python
# Desktop
await page.set_viewport_size({"width": 1920, "height": 800})
# iPad portrait
await page.set_viewport_size({"width": 768, "height": 1024})
# iPad landscape
await page.set_viewport_size({"width": 1024, "height": 768})
```

### 6.4 · Pass/Fail criteria

| Criterion | Pass condition |
|---|---|
| T1 | Role persists after hard refresh + exactly 1 `role_change` audit row · 0 duplicate assignments |
| T2 | 409 caught + clear error toast shown · no row mutation |
| T3 | Dialog submits · DELETE returns 200 · `remove_reason_category` + `remove_reason_text` persist in DB |
| T4 | Submit button disabled when `other` + blank text · enabled when text present |
| T5 | At least one row of each action type visible · newest first · actor + reason visible · read-only (no edit/delete buttons) |
| T6 | All three perf targets met |
| Viewport matrix | All tests pass at all three viewports · no horizontal scroll · no clipped dialogs/drawers · all click targets ≥ 44×44 px |
| No regressions | Existing `addTeamMember` flow still works · existing PM-scope view unchanged |
| Five Pillars | Powerful 9 · Simple 9 · Beautiful 9 · Trusted 9 · Proven 9 |

### 6.5 · Cert script template (Playwright via mcp_screenshot_tool)

```python
# Pseudocode for each viewport
await page.goto(f"{PREVIEW_URL}/admin/sign-in")
await page.fill('[data-testid="signin-email"]', "jaymn.judd@mascigc.com")
await page.fill('[data-testid="signin-password"]', "Maddix123!")
await page.click('[data-testid="signin-submit"]')
await page.wait_for_url("**/admin/**")
await page.goto(f"{PREVIEW_URL}/admin/jobs/20-07/team")
# T1
await page.click('[data-testid="row-role-<id>"]')
await page.click('[data-testid="row-role-<id>-opt-assistant_superintendent"]')
await page.wait_for_selector("text=Role changed", timeout=5000)
await page.reload()
# ... assertions ...
```

---

## 7 · Pre-cert preparation (fork session step 1)

Before any UI work, the fork agent should:
1. Re-login and seed a controlled test fixture: 2 assignments for Alec Perkins on `20-07` (foreman + safety_rep) via curl. Store both ids for the test.
2. Snapshot the current audit count: `GET /api/admin/jobs/20-07/team/audit?limit=200 | count(items)`. Used as the baseline for T1's "no duplicate audit row" check.
3. Verify `data-testid="job-team-audit-toggle"` still works (so the old inline panel is the deliberate target for replacement, not a stale element).

---

## 8 · Deliverables the fork session must produce

| File | Status |
|---|---|
| `/app/frontend/src/lib/teamRosterApi.js` | EDITED (remove API body shape) |
| `/app/frontend/src/components/team/JobTeamRosterPanel.jsx` | EDITED (3 sections: row role dropdown · remove dialog wiring · history drawer trigger) |
| `/app/frontend/src/components/team/RemoveReasonDialog.jsx` | CREATED |
| `/app/frontend/src/components/team/AssignmentHistoryDrawer.jsx` | CREATED |
| `/app/memory/TRACK_15_39A_TEAM_ASSIGNMENT_P2_FRONTEND_IMPLEMENTATION.md` | CREATED |
| `/app/memory/TRACK_15_39A_TEAM_ASSIGNMENT_P2_FRONTEND_CERTIFICATION.md` | CREATED with full T1-T6 × 3-viewport evidence |
| `/app/memory/CHANGELOG.md` + `/app/memory/PRD.md` | APPENDED |

---

## 9 · Hard rules for the fork session

* DO NOT modify backend code (Track 15.39 backend is certified — any backend change forks the cert)
* DO NOT add new endpoints
* DO NOT add new collections
* DO NOT modify PM-scope view (already designed without audit drawer)
* DO NOT add notifications/emails/AI/analytics/dashboards/reports
* If a backend bug blocks the frontend, document it and STOP — escalate to operator, do not silently work around it
* Use shadcn components exclusively · no custom Dialog/Sheet rolls
* Every interactive element MUST have a unique `data-testid` per §5
* Mobile/iPad: no hover-only actions, no <44px click targets

---

## 10 · Final executive answer (to be confirmed by fork session)

After fork session completes with all green:

🟢 **GREEN** · "MASCI operators can now add, change, remove, and audit project team assignments from the browser without backend-only workarounds. The frontend uses certified backend endpoints exclusively, supports desktop + iPad portrait + iPad landscape, and emits a single canonical audit row per intent."

🛑 Track 15.39A planning STOPS here. No code changes this session. The fork session has everything it needs to execute the entire scope in one pass and close the track completely.

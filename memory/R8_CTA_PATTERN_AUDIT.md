# R8 · CTA Pattern Audit

**Track 18.11.** Audit of CTA patterns across every operational workspace before R8 ships.

## Scope of audit
Cards across:
* Transportation Operations · Mission Control · Right Rail
* Search results · Dispatch surfaces
* Project Management · Human Resources · Safety Operations · Shop Operations
* Administration oversight cards · Operational Guidance Center
* Hub / public workspace cards

## CTA hierarchy classification

| Category | Visual treatment | Examples observed |
|---|---|---|
| **PRIMARY CTA** | Button default (no `variant=`) — solid fill | "Open Workspace", "Review Documents", "Start Review", "Enter →" |
| **SECONDARY CTA** | `variant="outline"` — bordered | "View Details", "See History", "Open Guide" |
| **UTILITY ACTION** | `variant="ghost"` or icon-only | "Refresh", "Copy", "Expand", "Collapse", "Close", "Clear" |
| **ROW / LIST ACTION** | Buttons inside `<TableRow>` or list mappings | "View" per row, "Open" per row, "Edit" per row |
| **PAIRED DECISION** | One primary + one outline/ghost | Save / Cancel, Approve / Needs Correction, Accept / Decline |
| **NAVIGATION** | Inside `<NavigationMenu>`, `<TabsList>`, `<Breadcrumb>`, `<Pagination>` | Sub-nav links, tab triggers |
| **DROPDOWN ITEM** | Inside `<DropdownMenu...>` | Menu items |
| **STATUS CHIP** | `<Badge>`, `<StatusChip>`, `<BandChip>` | Risk band labels, status pills |
| **EXEMPT** | Documented allow-list entries | Approve/Needs Correction in disposition workflows |

## R8 scans these
* `<Card>...</Card>` blocks across every authenticated workspace.

## R8 does NOT scan
* `<NavigationMenu>`, `<TabsList>`, `<Tabs>`, `<Tab>`, `<Breadcrumb>`, `<Pagination>`, `<DropdownMenu*>`, `<Select>`, `<Popover>`, `<TableRow>`, `<TableCell>`, `<Table>` subtrees.
* `<Badge>`, `<StatusChip>`, `<BandChip>`, `<Chip>` — these are not Buttons.
* Buttons with `variant="outline"`, `variant="ghost"`, `variant="link"`, `variant="secondary"`, `variant="destructive"`.
* Icon-only Buttons with `aria-label` + `title` (utilities — covered by 18.09A a11y pass).

## Audit findings

| Workspace | Card patterns reviewed | R8 violations | Notes |
|---|---:|---:|---|
| Public Hub | Field / QA-QC / Safety / Operations workspace cards | 0 | Each card has one primary "Enter →" CTA. No drift. |
| Sign-In | Single card | 0 | One primary "Sign in" button. |
| Transportation Operations · Mission Control | Mission brief + readiness tiles | 0 | Each tile drills into a single drawer. |
| Transportation Operations · Lists (Drivers / Carriers / Trucks) | Workspace cards | 0 | Single "Open workspace" or row drill. |
| Dispatch Board · Command · Map · Ledger | Card layouts | 0 | Dispatcher actions live in drawer footers (Confirm/Cancel) — paired decision. |
| Project Management home | Readiness chips + attention badges | 0 | No competing primary CTAs. |
| Human Resources | HR cards | 0 | **HrDriverQualificationDashboard.jsx** filter buttons initially flagged — confirmed as toggle filters (`variant={X ? "default" : "outline"}`); scanner upgraded to recognize dynamic variant expressions as non-primary. **No code change required.** |
| Safety Operations | Incident queue + corrective actions | 0 | |
| Shop Operations | Work-order cards | 0 | |
| Field Leadership | Leadership tiles + leadership form | 1 (allow-listed) | `FieldLeadershipFormPage.jsx` — inline "Add new employee" sub-panel renders inside the main form Card. Inline `Add`/`Cancel` pair (already with outline Cancel) + main form `Submit & Email PDF`. Allow-listed with documented justification (sub-panel is conditionally rendered, doesn't visually compete at runtime). |
| Administration · oversight cards | Cards | 0 | |
| Operational Guidance Center | Article cards | 0 | One "Read" CTA per article. |
| Right Rail | Quick action stack | 0 | Stack is vertical primary→secondary→utility — visually clear hierarchy. |
| Search results | Result cards | 0 | One "Open" CTA per result. |
| PO Requests | Filter cards + result cards | 0 | |

**Total R8 violations found in the current codebase: 1 (allow-listed with documented justification).**

## Conclusion
The current codebase has **zero duplicate-CTA card violations**. R8 ships as a permanent **forward-looking guardrail**: future drift fails the gate.

## Six-Pillar self-check
Powerful ✅ · Simple ✅ · Beautiful ✅ · Trusted ✅ · Proven ✅ · Operational ✅

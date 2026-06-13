# MASCI Platform · BUTTONS_DICT.md

**Status:** v1.0 · authoritative · Track 14.0-BT (2026-06-13)
**Scope:** Every button on the MASCI Operations Platform.
**Audience:** Developers · agents · designers · translators.

> Translate this dictionary, not 1 385 strings. Every new button uses one of the entries below.

---

## 1. Button Roles (use these · not new ones)

| Role | Variant | Use when |
|---|---|---|
| **Primary Action** | `variant="default"` (orange-on-slate platform-primary) | The one *most-important* action on a form, modal, or section. Submit · Save · Add Asset · Generate PDF. One per surface. |
| **Secondary Action** | `variant="outline"` | Supporting actions next to a primary. Edit · Download · Export CSV. |
| **Destructive Action** | `variant="destructive"` | Delete · Remove · Discard. Must show confirm. Red. |
| **Safe Cancel** | `variant="ghost"` or `variant="outline"` | Cancel · Close · Dismiss. Never red. |
| **Navigation Back** | `variant="ghost"` + `<ArrowLeft>` icon | "Back" or "Return to {Place}". Always returns user to a known parent. |
| **Modal Primary** | `variant="default"` | The confirm/submit action in a Dialog. Right side of modal footer. |
| **Modal Secondary** | `variant="ghost"` | Cancel in modal. Left side of modal footer. |
| **Table Row Action** | icon-only · 24-32 px · `variant="ghost"` | View · Edit · Download a single row. Must have `title` or `aria-label`. |
| **Dashboard Quick Action** | tile/card style · platform "mark" or "outline" | KPI card CTAs · hub tiles. |
| **Public Submit** | `variant="default"` · full-width on mobile | Daily Report · Pre-Op · DVIR · Incident · Excavation submit. Always last in form. |
| **Workflow Transition** | `variant="default"` for forward · `variant="outline"` for revision · `variant="destructive"` for cancel | Approve · Needs Revision · Cancel Transfer. |
| **Verification/Review** | `variant="default"` for Verify · `variant="outline"` for Review | Verify Document · Review Asset · Acknowledge. |

---

## 2. Approved Labels (English · canonical)

Every entry below is a fixed canonical English string. New labels must come from this table. Do not invent synonyms.

### Submit / Save / Workflow

| Approved label | Use when | Avoid these synonyms |
|---|---|---|
| **Submit** | Sending a field/public form for review or processing | Send · Push · Post · Finalize |
| **Save** | Persisting changes to an existing record (no workflow) | Update · Commit · Store |
| **Save Changes** | Save when there's also a separate Submit action on the surface | n/a |
| **Save Draft** | Storing in-progress form without submitting | Save for Later · Park |
| **Submit for Review** | Submitting with explicit reviewer in the loop | Send for Approval · Push to QA |
| **Submit Report** | Daily Report / Incident / Safety Meeting public form submit | Send Report · Post Report |

### Add / Create / Remove / Delete

| Approved | Use when | Avoid |
|---|---|---|
| **Add** | Creating a new record from a user action (Add Asset · Add Document) | New · Insert · Plus |
| **Add {Entity}** | Add Asset · Add Employee · Add Document — destination explicit | Create Asset (admin-config exception below) |
| **Create** | Admin/system **configuration** where creation is abstract (Create Template · Create Role) | Add Template (avoid) |
| **Edit** | Modifying an existing record's fields | Update · Modify |
| **Update** | Reserved for in-toast/status text ("Asset updated.") — NOT as a button label | Save as Update |
| **Remove** | Detaching/unassigning without deleting the record (Remove from Crew) | Delete (avoid for unassignment) |
| **Delete** | Hard-delete (record is recoverable or fully gone) | Trash · Discard (avoid) |
| **Clear** | Resetting a filter / search field | Empty · Wipe |
| **Reset** | Reset entire form/filter group | Clear All |

### Navigation

| Approved | Use when | Avoid |
|---|---|---|
| **Back** | Plain browser-style return one step | Previous · Go Back · Return |
| **Return to {Place}** | Destination matters — e.g. "Return to Asset Care" | Back to · Go Home |
| **Home** | Portal-shell home button (chrome) | Dashboard · Hub |
| **Sign In** | Login button | Log In · Login |
| **Sign Out** | Logout button | Log Out · Logout |
| **Continue** | Multi-step form forward action | Next · Forward · Proceed |
| **Previous** | Multi-step form backward action | Back (use "Back" only for chrome) · Prev |

### Open / View / Details

| Approved | Use when | Avoid |
|---|---|---|
| **Open** | Opens a profile / detail page in the same surface | Go · Launch · Show |
| **Open Profile** | When destination is the canonical entity profile | View Profile (avoid) |
| **View** | Read-only viewer (PDF · photo · report) — opens viewer/modal | Show · See |
| **View Details** | When the action expands current row to detail panel | Details · More |

### Upload / Download / Export / Print

| Approved | Use when | Avoid |
|---|---|---|
| **Upload** | Add a file to a record (Upload Document · Upload Photo) | Attach · Send File |
| **Upload Document** | Specific upload-document modal/CTA | Add Document (acceptable alternative when no upload step) |
| **Download** | Single-file download (Download CSV · Download PDF) | Get · Save File · Fetch |
| **Export CSV** | Aggregated CSV export | Download CSV (acceptable for single record) |
| **Generate PDF** | Generate-and-download PDF action | Make PDF · Print PDF |
| **Print** | Trigger browser/system print dialog | Open Print Preview |

### Review / Approve / Needs Revision / Verify / Acknowledge

| Approved | Use when | Forbidden |
|---|---|---|
| **Review** | Send to reviewer · or open the review modal | Audit (avoid) |
| **Approve** | Final approval action in a review workflow | Accept · Pass · Confirm |
| **Needs Revision** | Send back for changes (NOT Reject / Denied / Failed) | **Reject** · **Denied** · **Failed** · Refuse |
| **Verify** | Mark document/data as verified | Validate · Confirm Verified |
| **Acknowledge** | Worker confirms they have seen / received | Got It · OK |

### Workflow Transitions (Asset / Shop / Dispatch)

| Approved | Use when | Forbidden |
|---|---|---|
| **Assign** | Assign to crew/employee/mechanic | Allocate · Attach to |
| **Transfer** | Move asset between projects · employee between crews | Move · Reassign |
| **Complete Work** | Mechanic marks shop work complete | Done · Finish · Wrap Up |
| **Repair Complete** | Specific Shop repair-completion state — does NOT return to service | Done · Ready · Fixed |
| **Return to Service** | Dispatch / Admin RTS authority — restricted role | Activate · Reactivate · Put Back |
| **Place Out of Service** | Dispatch / Admin take asset out | OOS · Park · Down |
| **Hold for Maintenance** | Maintenance hold transition | Lock · Freeze |

### Cancel / Close / Discard

| Approved | Use when | Avoid |
|---|---|---|
| **Cancel** | Abandon a modal/form before save | Discard · Quit · Exit |
| **Close** | Dismiss a viewer / dialog where nothing was being edited | Dismiss · X · Done |
| **Discard Changes** | Confirmation step when cancelling a modified form | Throw Away · Lose Changes |

### Sign-in / Auth

| Approved | Use when | Avoid |
|---|---|---|
| **Sign In** | Portal login button | Log In · Login |
| **Sign Out** | Portal logout | Log Out · Exit |
| **Forgot password?** | Password-recovery link | Lost password · Reset password (acceptable for admin-tool) |

---

## 3. Variant Rules (visual)

| Variant | Where to use | Forbidden where |
|---|---|---|
| `variant="default"` | Primary action on a surface | Cancel · destructive |
| `variant="outline"` | Secondary action · table actions · sometimes Cancel | Destructive (use destructive) |
| `variant="ghost"` | Quiet actions · header chrome · Cancel · icon-only table rows | Primary submit |
| `variant="destructive"` | Delete · Remove (hard) · Cancel Transfer | Save · Submit · Add |
| `variant="link"` | Inline text-style action | Modal footer · public-form submit |
| `variant="mark"` (legacy 159 uses) | Dashboard tile / KPI CTA | Cancel · destructive |
| `variant="login"` (legacy 15 uses) | Portal sign-in shells only | Anywhere else (retire by post-RC-1) |
| Other long-tail (`meeting` · `header` · `body` · `warning` · `success` · `light` · `global` · `danger`) | Existing surfaces only | New code (use `default`/`outline`/`ghost`/`destructive` instead) |

**Target consolidation (post-RC-1):** 5 canonical variants — `default` · `outline` · `ghost` · `destructive` · `link`. Retire `login` · `meeting` · `header` · `body` · `warning` · `success` · `light` · `global` · `danger` in favour of mapping to the 5 canonical variants. `mark` may stay as a dashboard-tile variant.

---

## 4. Accessibility Rules

- **Icon-only buttons** must carry either `aria-label` or a tooltip with `title`. No exceptions.
- **Disabled state** must not be the *only* signal — pair with a tooltip or helper text that explains why.
- **Destructive actions** must show a confirmation Dialog (`AlertDialog`) before executing.
- **Primary action** must be visually larger or bolder than the surface's secondary actions.
- **Mobile public-form submit** must be full-width and remain reachable without keyboard collision.

---

## 5. Forbidden Button Labels

| Forbidden | Use instead |
|---|---|
| Reject · Denied · Refuse · Decline (as user-facing button) | Needs Revision |
| Failed (as button) | n/a — "Failed" may only appear as inspection-item pass/fail control state |
| Invalid (as user-blame button) | Needs Revision · Check Required Fields |
| Go · Submit Now · Click Here | Submit · Continue |
| Make · Build · Run | Create · Generate · Start |
| Throw Away · Wipe · Erase | Discard · Delete · Remove |
| Allocate · Bind | Assign |
| OK · Got It · Roger | Acknowledge · Close |
| Update (as button verb) | Save · Save Changes |
| Push · Post · Send (when meaning submit) | Submit |

---

## 6. Spanish Readiness Notes (for 14.0-S1)

| Button | i18n key | Frequency | Priority |
|---|---|---:|---|
| Submit | `t("Submit")` | very high | P0 |
| Save | `t("Save")` | very high | P0 |
| Save Changes | `t("Save Changes")` | high | P0 |
| Cancel | `t("Cancel")` | very high | P0 |
| Close | `t("Close")` | very high | P0 |
| Back | `t("Back")` | very high | P0 |
| Return to {Place} | `t("Return to %{place}", { place })` | medium | P0 |
| Add | `t("Add")` | high | P0 |
| Add Asset | `t("Add Asset")` | medium | P0 |
| Edit | `t("Edit")` | high | P0 |
| Delete | `t("Delete")` | medium | P0 |
| Remove | `t("Remove")` | medium | P0 |
| Upload | `t("Upload")` | high | P0 |
| Upload Document | `t("Upload Document")` | medium | P0 |
| Download | `t("Download")` | high | P0 |
| Export CSV | `t("Export CSV")` | medium | P1 |
| Generate PDF | `t("Generate PDF")` | medium | P1 |
| View | `t("View")` | high | P0 |
| View Details | `t("View Details")` | medium | P1 |
| Open | `t("Open")` | medium | P0 |
| Review | `t("Review")` | medium | P0 |
| Approve | `t("Approve")` | medium | P0 |
| Needs Revision | `t("Needs Revision")` | medium | P0 |
| Verify | `t("Verify")` | medium | P0 |
| Acknowledge | `t("Acknowledge")` | low | P1 |
| Assign | `t("Assign")` | medium | P0 |
| Transfer | `t("Transfer")` | medium | P1 |
| Complete Work | `t("Complete Work")` | medium | P0 |
| Repair Complete | `t("Repair Complete")` | medium | P0 |
| Return to Service | `t("Return to Service")` | medium | P0 |
| Place Out of Service | `t("Place Out of Service")` | medium | P0 |
| Sign In | `t("Sign In")` | very high | P0 |
| Sign Out | `t("Sign Out")` | very high | P0 |
| Continue | `t("Continue")` | medium | P0 |
| Previous | `t("Previous")` | medium | P0 |
| Print | `t("Print")` | medium | P1 |

**~36 P0/P1 button keys cover ≈ 99 % of platform button text** by frequency. 14.0-S1 should translate this dictionary first.

---

## 7. Examples · Correct and Incorrect

### Correct
```jsx
<Button variant="default" data-testid="add-asset-btn">{t("Add Asset")}</Button>
<Button variant="ghost" onClick={onCancel} data-testid="cancel-btn">{t("Cancel")}</Button>
<Button variant="destructive" onClick={onDelete} data-testid="delete-asset-btn">{t("Delete")}</Button>
<Button variant="outline" data-testid="export-csv-btn">{t("Export CSV")}</Button>
```

### Incorrect
```jsx
<Button data-testid="reject-btn">Reject</Button>               // ❌ Use "Needs Revision"
<Button>Submit Now!</Button>                                    // ❌ Use "Submit"
<button>Go</button>                                             // ❌ Use shadcn Button + approved label
<Button variant="destructive">Cancel</Button>                   // ❌ Red Cancel · use ghost/outline
<Button>X</Button>                                              // ❌ Icon-only · no aria-label
<Button>Update</Button>                                         // ❌ Use "Save" or "Save Changes"
```

---

**End of BUTTONS_DICT.md v1.0.**

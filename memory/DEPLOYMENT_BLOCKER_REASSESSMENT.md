# DEPLOYMENT BLOCKER REASSESSMENT

**Date**: 2026-06-02T18:33 UTC
**Mode**: READ-ONLY · NO fixes · NO code · NO deploy
**Authority**: OMEGA P0 — HR Lifecycle Save Button Forensic Failure (reopened)
**Companions**: `HR_SAVE_BUTTON_FORENSIC.md`, `HR_SAVE_BUTTON_EXECUTION_TRACE.md`, `HR_SAVE_BUTTON_ROOT_CAUSE.md`

---

# 🟡 **CLASSIFICATION: UX FAILURE**

---

## 1 · Classification verdict

Per the three classification options provided by the operator:

| Option | Threshold | Verdict |
|---|---|:-:|
| 🟢 User Misunderstanding | User error · system fully communicates outcome · HR ignored or misread valid feedback | ❌ NO — the user is reporting a legitimate gap; the system's success-feedback is genuinely sparse |
| 🟡 **UX Failure** | System executes correctly but communicates outcome poorly · user perception of "nothing happened" is legitimate even though save persists | ✅ **YES — this is the correct classification** |
| 🔴 Workflow Failure | Save click does NOT result in DB write · status_history NOT appended · governance broken · data integrity at risk | ❌ NO — every probe confirms DB writes, status_history append-only chain, audit trail, playbook fan-out all working |

---

## 2 · Why NOT 🔴 Workflow Failure

The previous L1+L2 final certification confirmed the HR Lifecycle workflow is operationally complete:

| Evidence | Source | Result |
|---|---|:-:|
| HR-token save round-trip Active → Inactive → Active on preview | `HR_LIFECYCLE_STICKY_FOOTER_CERTIFICATION.md` | ✅ status_history grew 2 → 3 → 4 |
| Live audit probe (this audit) Active → Resigned with playbook | Probe A in `HR_SAVE_BUTTON_EXECUTION_TRACE.md` §2 | ✅ status_history grew 4 → 5, 8 playbook tasks created |
| Phase Alpha governance gate | `L1_L2_REMEDIATION_CERTIFICATION.md` | ✅ HR-only, all forged tokens 401, anon 401 |
| Frontend bundle has iter453.7 sticky footer | Production bundle audit | ✅ `hremp-status-footer` present in `main.8e2b2094.js` |
| Save button preserves `hremp-status-save` testid | Same | ✅ |
| Toast Mounter is wired | `App.js:283` | ✅ `<Toaster position="bottom-right" richColors closeButton />` |
| Backend gate returns 200 for HR | Live probe | ✅ |

There is NO evidence of:
* Silent button click failure (handler is wired)
* Network failure (200s observed)
* Permission failure (HR token accepted)
* Validation false-positives (validation is correct per business rules)
* DB write failure (status_history grew)
* Lost audit trail (chain alive)
* Governance breach (Phase Alpha intact)

**The workflow is intact.** Therefore the classification is NOT 🔴.

---

## 3 · Why NOT 🟢 User Misunderstanding

The user's report is internally consistent and externally reproducible:

* **"Save button is visible"** — TRUE (verified in production bundle)
* **"User fills out lifecycle form"** — TRUE (form fields render and accept input)
* **"User clicks Save Status Change"** — TRUE (`onClick={submitStatusChange}` wired)
* **"Nothing appears to happen"** — PARTIALLY TRUE — *something* happens (toast fires, drawer state refreshes), but the visible feedback is:
  * Bottom-right toast that auto-dismisses in ~4 s
  * A subtle StatusBadge color shift in the drawer header
  * A new entry in "Recent status history" that may be below the visible scroll area
  * NO drawer auto-close
  * NO in-drawer success banner
  * NO form reset

The user's perception is legitimately formed by the system's UX choices. This is not user error.

---

## 4 · Why this IS 🟡 UX Failure

The system communicates save outcome through ephemeral, peripheral, and weak signals. The signals exist but are not designed to be impossible to miss. A user under load, on a small viewport, or with focus on the modal can plausibly conclude "nothing happened" without misreading anything — the system's affordance for success-acknowledgement is genuinely thin.

| Quality dimension | Score | Note |
|---|:-:|---|
| Does the save persist? | ✅ Strong | DB write + history append + playbook fan-out all confirmed |
| Does the user know the save persisted? | ⚠️ Weak | Only the bottom-right toast (4 s auto-dismiss) and a subtle badge shift |
| Does the user know WHY a failed save failed? | ⚠️ Mixed | Validation toasts say what to fix, but they fire and dismiss quickly |
| Does the user know when nothing actually changed (noop)? | 🔴 Bad | Backend returns `noop:true` but frontend shows generic "Status updated" toast — misleading |
| Does the drawer state reinforce the save outcome? | 🔴 Bad | Drawer stays open with same form state · no closing action · no in-drawer banner |
| Is the post-save table refresh visible to the user? | ❌ No | Drawer covers the table; user has to close drawer to see the row change |

Three weak/bad signals on the user-feedback axis = legitimate UX failure.

---

## 5 · Deployment impact

| Question | Answer |
|---|---|
| Is data integrity at risk? | NO — saves persist correctly |
| Is governance at risk? | NO — Phase Alpha G-1..G-5 intact |
| Is audit trail at risk? | NO — status_history + employee_lifecycle_events both append-only and alive |
| Is the offboarding playbook firing? | YES — 8 tasks created on Active → Resigned |
| Are HR users currently unable to complete the workflow? | NO — they CAN complete it. Some users may NOT REALIZE they completed it and re-attempt, which can produce noop 200 returns (zero-side-effect retries — safe) |
| Should production be rolled back? | NO — rollback removes a working workflow and replaces it with a strictly worse state (below-fold Save) |
| Is there a hard blocker for HR daily ops? | NO — the workflow is operable; the friction is in feedback, not in execution |

---

## 6 · Compared to the prior reopened blocker (HR_LIFECYCLE_SAVEPATH_AUDIT)

| Aspect | Prior blocker (iter453.7 fix scope) | This blocker |
|---|---|---|
| Save button visibility | Below fold on 60-70% of HR fleet | Visible (iter453.7 sticky footer live) |
| Save click result | Worked when invoked, but operators were dropping writes by closing the drawer | Works AND saves AND audit-trails AND fires playbook |
| Failure mode | Discoverability of the action | Discoverability of the outcome |
| Operator-side impact | Operators could not initiate save | Operators initiate save successfully but cannot tell it worked |
| Risk to data | Low — dropped writes are recoverable | None — writes persist correctly |
| Required action | Code change (sticky footer) | UX feedback enhancement (≤ 5 LOC ideas in `HR_SAVE_BUTTON_ROOT_CAUSE.md` §5) |
| Classification then | 🔴 (operator reclassified) | n/a |
| Classification now | n/a | 🟡 UX FAILURE |

---

## 7 · Final classification

# 🟡 **UX FAILURE**

* The Save Status Change button works.
* The API fires.
* The backend validates.
* The DB updates.
* The status_history appends.
* The employee_lifecycle_events appends.
* The offboarding playbook fires.
* Phase Alpha governance is intact.
* HR authority is intact.
* The audit trail is intact.

But the system's signaling of save success/failure is sparse enough that HR users can legitimately perceive "nothing happened" even when everything happened correctly.

**No deployment block. No rollback. No emergency action.** The fix is a small set of feedback affordances awaiting operator authorization.

---

## 8 · STOP

Reassessment complete. Read-only directive honored. No code · no fix · no deploy.

**Evidence-only verdict: 🟡 UX FAILURE.**

# FIELD WALK · PM

_Operator role: Project Manager · Device: iPad or laptop · Time: ~15 min._

---

## 1 · PM Hub entry

1. Sign in to PM portal.
2. PROVES: PM Hub loads with project chips.
3. PROVES: governance health chip shows green or `improving N/100`.

## 2 · PO approval flow

1. Tap **Purchase Requests**.
2. Tap a PO in `Submitted` or `Pending Approval` status.
3. PROVES: Approval block is visible: Approve / Clarify / Reject
   buttons + Manual PO # + Approved amount inputs.
4. Tap **Clarify** with a short note.
5. PROVES: PO moves to `Clarification Needed`.
6. PROVES: requester gets a clarification task in their bell.

## 3 · PO approval — happy path

1. Open a fresh `Submitted` PO.
2. Fill Manual PO # (optional).
3. Fill Approved amount.
4. Tap **Approve**.
5. PROVES: PO moves to `Approved` or `Pending Receipt`.
6. PROVES: requester gets a "PO approved · upload receipt" task.
7. PROVES: NO new approval task fans out (approval done).

## 4 · Project Dashboard — incident chip

1. Navigate to a project's dashboard.
2. Tap the incident counter chip.
3. PROVES: lands on filtered incidents list for THAT project.
4. Tap an incident.
5. PROVES: "Back" button reads "Back to Project" or similar — NOT
   a generic label.

## 5 · Daily Report visibility

1. Open the project's Daily Reports list.
2. PROVES: see today's reports from FL crews.
3. Open one.
4. PROVES: read-only view; no edit affordance unless YOU created it.

## 6 · Notifications

1. Open the bell.
2. PROVES: "PO needs approval" tasks present (you're an approver).
3. PROVES: "Receipt missing" tasks present for overdue POs.

## 7 · Cross-portal navigation

1. From PM Hub, tap a "Go to Admin" link if present.
2. PROVES: sidebar updates to Admin chrome.
3. Open `/po-requests` from Admin.
4. PROVES: approval controls still visible (you have admin token).
5. Return to PM portal.
6. Open `/po-requests` again.
7. PROVES: approval controls still visible (PM context).

## 8 · Cross-portal mid-session simulation

1. Have a Super Admin colleague sign in alongside (or use a separate
   tab as Super Admin).
2. From the Super Admin session, navigate INTO the Field Leadership
   portal hub.
3. From Field Leadership hub, open `/po-requests`.
4. PROVES: NO approval controls visible (FL context overrides admin
   token presence).
5. Navigate BACK to Admin hub, open `/po-requests`.
6. PROVES: approval controls return.

---

## Pass / Fail

Same as FL — any "PROVES" miss is a ticket with Support ID attached.

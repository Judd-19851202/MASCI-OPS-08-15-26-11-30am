# FIELD WALK · FIELD LEADERSHIP

_Operator role: foreman / superintendent · Device: iPhone or iPad ·
Time: ~15 min._

Run this on **preview** before any production cutover.

---

## 1 · Daily Report — clean start

1. Open Safari → preview URL.
2. Sign into the Leadership portal.
3. Tap **"Submit a Daily Report"** tile.
4. PROVES: page loads under 3 sec.
5. PROVES: top-right shows the autosave pill (slate dot).
6. PROVES: there is **no** "Welcome back" banner (first time on
   this device).

## 2 · Daily Report — fill + autosave

1. Pick a project number you'd normally use.
2. Fill the crew header (foreman name, hours, weather).
3. Add 2-3 task notes.
4. Attach **1 photo** from camera roll.
5. PROVES: pill animates to "Saving…" then "Saved a few seconds ago".
6. PROVES: the photo thumbnail appears within 3 seconds of attach.
7. PROVES: Support ID popover opens cleanly when you tap the
   life-buoy icon and the value starts with `d.`.

## 3 · Daily Report — survivability under reload

1. Mid-form, force a **page reload** (pull-down on iOS Safari).
2. PROVES: restore prompt appears with "Saved {ago}".
3. PROVES: tapping **Restore** brings back EVERYTHING — text + photo.
4. PROVES: tapping **Discard** removes the restore prompt AND
   subsequently a **calm recovery notice** appears offering "Bring
   it back".

## 4 · Daily Report — submit (online)

1. Fill out everything you need.
2. Tap **Submit**.
3. PROVES: success toast + you land on Thank-You page.
4. PROVES: no error toast appears in the next 10 seconds.

## 5 · Daily Report — submit (offline)

1. Turn ON airplane mode.
2. Start a new Daily Report, fill it minimally, tap **Submit**.
3. PROVES: toast reads "Saved · will upload when reconnected".
4. PROVES: no "Submitted" copy appears — submission is HONEST.
5. Turn OFF airplane mode.
6. Wait ~60 seconds.
7. PROVES: a second submission confirmation arrives (silent OK is
   acceptable; failure toast is NOT).

## 6 · Project switch — no preload contamination

1. Open a NEW Daily Report.
2. Pick **Project A**, fill the crew header.
3. Switch to **Project B**.
4. PROVES: crew header CLEARS — does not carry forward Project A.
5. PROVES: any "Crew memory restored" banner disappears or
   re-derives for Project B.

## 7 · PO Request — capability scope (the big one)

1. Tap **Purchase Requests** tile.
2. Tap an existing PO row to open the drawer.
3. PROVES: NO **Approve** button visible.
4. PROVES: NO **Reject** button.
5. PROVES: NO **Clarify** button.
6. PROVES: NO **Manual PO #** input.
7. PROVES: NO **Approved amount** input.
8. PROVES: NO **Cancel** button.
9. PROVES: NO **Close** button.
10. PROVES: You CAN see the status timeline, who requested,
    description, vendor, urgency, and (if applicable) the receipt
    upload form.

## 8 · Incident — navigation continuity

1. Tap **Submit an Incident**.
2. Fill + attach photo.
3. PROVES: pill behaves identically to Daily Report.
4. Submit. Land on Incident view.
5. PROVES: "Back" button label matches where you came from
   (Leadership Hub) — not a generic "INCIDENTS".

## 9 · Bell feed — no admin notifications

1. Tap the notification bell.
2. PROVES: no "PO needs approval" tasks.
3. PROVES: no "Admin approval queue" notifications.
4. PROVES: clarification / receipt / status notifications for YOUR
   POs DO show.

## 10 · Storage health

1. Open settings → Safari → Advanced → Website Data.
2. PROVES: app data > 0 (autosave is real).
3. Note the size for reference.

---

## Pass / Fail

* Pass: every "PROVES" line confirmed.
* Fail: any "PROVES" line not confirmed. **File a ticket immediately**
  with the Support ID (long-press the life-buoy icon to copy).

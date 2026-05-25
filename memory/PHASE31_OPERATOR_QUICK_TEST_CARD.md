# MASCI · Operator Quick-Test Card

_Print this · 1 page · 5 minutes per device · no jargon._

Hand this to any foreman, driver, or shop tech. They run the
5 tests on their phone or tablet, mark the boxes, and hand it back.
That's the entire real-device certification for Phase 31 + 31.1.

---

## Device under test

> **Device**: ___________________________  (e.g. iPhone 14 · Pixel 7 · iPad Pro · Toughbook)
>
> **Browser**: ___________________________  (Safari · Chrome · Edge)
>
> **Tester**: ___________________________
>
> **Date**: ___________________________

---

## Test 1 · "Did the app remember my work after a refresh?"

1. Open the app · go to **Daily Report** (the New Daily Report button).
2. Type your name into the **Prepared By** field.
3. Type any project name into the **Project Name** field.
4. Wait 3 seconds.
5. Hit the browser refresh button (or close & reopen the app).
6. Look at the top of the form.

**Pass condition**: An amber box appears asking _"You have unsaved
work from earlier."_ with **Restore** and **Discard** buttons.

> [ ] ✅ Pass  [ ] ❌ Fail   Notes: ______________________________

---

## Test 2 · "Did Restore actually bring my typing back?"

1. From Test 1, tap the **Restore** button in the amber box.

**Pass condition**: The Prepared By and Project Name fields fill in
with what you typed. No data was lost.

> [ ] ✅ Pass  [ ] ❌ Fail   Notes: ______________________________

---

## Test 3 · "Did the app remember yesterday's crew setup?"

> _Only run this if you (or someone) filed a real Daily Report on
> THIS device within the last 30 days. If not, skip this test._

1. Go to **Daily Report** again.

**Pass condition**: At the top of the form, an amber box appears
asking _"Use yesterday's crew and equipment setup from this
device?"_ with three buttons: **Use Setup**, **Start Blank**,
**Clear Saved Setup**. The box shows your project name and a count
like "3 crew members".

> [ ] ✅ Pass  [ ] ❌ Fail   Notes: ______________________________

> _Bonus check_: tap **Use Setup**. The crew + equipment lists fill
> in but **today's date stays today's date** (NOT yesterday's date).
>
> [ ] ✅ Bonus pass  [ ] ❌ Bonus fail

---

## Test 4 · "Does it work without signal?"

1. Turn **Airplane Mode** ON.
2. Open a fresh **Daily Report**.
3. Type any name + project name + a crew member.
4. Hit submit.

**Pass condition**: A calm message says
_"Saved · will upload when reconnected"_ — NOT a red error.

5. Turn Airplane Mode OFF.
6. Wait ~10 seconds.

**Pass condition**: The report uploads on its own. You should see it
appear under **Daily Reports** within a minute.

> [ ] ✅ Pass  [ ] ❌ Fail   Notes: ______________________________

---

## Test 5 · "Does the camera upload survive a dropped signal?"

> _Skip this test if you're not on the Dispatch board._

1. Open Dispatch Board · pick any assignment · open it.
2. Turn **Airplane Mode** ON.
3. In the assignment attachment section, tap **Take Photo / Upload**
   and pick any photo from your gallery.

**Pass condition**: A calm pill appears showing _"N waiting to send"_
in the attachment section. No red error toast.

4. Turn Airplane Mode OFF.
5. Wait ~10 seconds.

**Pass condition**: The pill disappears. The photo appears in the
attachment list. You did not have to tap anything to retry.

> [ ] ✅ Pass  [ ] ❌ Fail   Notes: ______________________________

---

## Result · circle one

> **All 5 PASS** · device is certified ✅
>
> **1 or 2 fails** · note the device + browser version, send to ops
>
> **3+ fails** · this device is NOT ready for field use yet · escalate

---

## What to do with this card

- Snap a photo of the filled-out card and text it to ops, OR
- Reply to your iteration thread with the device + result lines

We track one row per device in the build log. After 3-4 devices
pass, real-device certification is done.

---

## A few notes for testers

- **Test 1 + 2** prove your typed words are safe on every form. If
  the amber box never appears, something is wrong on the device.
- **Test 3** only fires if there's a setup saved from a previous
  Daily Report on this exact device. New devices show no box (correct).
- **Test 4 + 5** prove the platform handles weak signal calmly. The
  app should NEVER show a red error when you lose signal — just a
  calm "saved · will send when online" message.
- If you see anything you don't recognize — a red banner that won't
  go away, a popup that nags repeatedly, anything that feels wrong —
  screenshot it and send it. That's exactly the kind of feedback
  that closes Phase 31.

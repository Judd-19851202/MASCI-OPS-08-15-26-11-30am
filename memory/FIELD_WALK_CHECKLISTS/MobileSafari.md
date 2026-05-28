# FIELD WALK · MOBILE SAFARI (CROSS-CUTTING)

_Operator role: any · Device: iPhone or iPad on Safari · Time: ~10 min._

This is the **survivability walk**. Mobile Safari is the platform's
hardest environment — ITP, quota sweeps, aggressive background
suspension, photo upload quirks, network jitter. Every prod cutover
that touches `lib/resiliency/*` MUST clear this walk.

---

## 1 · Cold start

1. Force-quit Safari completely.
2. Re-open Safari → preview URL.
3. PROVES: page loads under 5 sec on LTE.
4. PROVES: no console errors visible if you have Web Inspector.

## 2 · Backgrounding mid-form

1. Open NewDailyReport, type 30+ chars in the description.
2. Tap iOS home indicator to background Safari.
3. Wait 60 seconds.
4. Bring Safari back to foreground.
5. PROVES: form contents preserved EXACTLY.
6. PROVES: pill shows "Saved {ago}".

## 3 · Tab swap

1. Open NewDailyReport, fill some fields.
2. Open a different tab (or new tab) and browse anything else.
3. Return to the form tab.
4. PROVES: form contents preserved.

## 4 · Force-quit recovery

1. Open NewDailyReport, fill some fields (DON'T submit).
2. Force-quit Safari.
3. Re-launch, navigate back to NewDailyReport.
4. PROVES: restore prompt offers your draft.
5. PROVES: timestamp matches when you closed Safari.

## 5 · Photo attach

1. Attach 1 photo.
2. PROVES: thumbnail renders within 5 sec.
3. PROVES: orientation correct (no sideways).
4. PROVES: pill shows "Saved" after photo attach.

## 6 · Photo recovery

1. Attach a photo, then force-reload the page.
2. PROVES: restore prompt offers the draft.
3. Tap Restore.
4. PROVES: photo comes back (IDB `photoStaging` blob store works).

## 7 · Weak signal

1. Go to a corner of the office with poor Wi-Fi or LTE.
2. Submit a Daily Report.
3. If success → you're online. Move further away.
4. PROVES: when the network fails, the toast reads "Saved · will
   upload when reconnected" (NOT a generic error).

## 8 · Airplane → online cycle

1. Turn ON airplane mode.
2. Fill + submit a Daily Report.
3. PROVES: queued toast.
4. Turn OFF airplane mode.
5. Wait 30-60 sec.
6. PROVES: queued submission delivers (check from a desktop in
   parallel that the report shows up server-side).

## 9 · Quota approaching

1. Skip if quota chip never shows during testing.
2. If quota chip surfaces:
3. PROVES: copy reads "Storage NN% full" (no "QuotaExceededError"
   or "navigator.storage" jargon).
4. PROVES: chip is amber, not red.

## 10 · Support ID

1. Tap the life-buoy icon next to the autosave pill.
2. PROVES: popover opens with "Support ID" label and the value.
3. Tap the Support ID row.
4. PROVES: clipboard copy succeeds (paste it into Notes to verify).

---

## Pass / Fail

Pass: every PROVES confirmed under real iOS Safari (NOT desktop
Safari simulation).

Fail: file ticket with iOS version + device model + Support ID.
This walk is the bedrock of platform survivability — every PROVES
matters.

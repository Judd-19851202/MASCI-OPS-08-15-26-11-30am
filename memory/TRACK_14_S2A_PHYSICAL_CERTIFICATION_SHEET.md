# TRACK 14.0-S2A · Physical-Device Certification Sheet

> Items that **cannot be honestly proven** inside the sandboxed
> agent environment (Chromium-only Playwright, no physical device,
> no real Florida sun, no real cell-jobsite signal, no real fatigued
> humans). Each item below carries **exact manual test steps and
> pass/fail criteria** so a human tester can sign off.

**Track may only close 🟢 PROVEN · TRUSTED · FIELD-READY after this
sheet is signed off by a human running the listed steps on real
devices.** Until then, status is 🟢 *Automated Field Certification
Complete · Physical Field UAT Pending*.

---

## 1 · Safari on a real iPad (Apple WebKit, not Playwright WebKit)

**Why:** Playwright's WebKit engine differs from real Mobile Safari
in font rendering, viewport handling, IndexedDB quotas, and the
notorious iOS focus-zoom on `<input>` < 16 px. Only a real iPad
proves the field user's actual experience.

**Devices:** iPad Pro 11" (2022+), iPad Air, iPad Mini 6.

**Steps:**

1. Open Safari on the iPad. Visit `https://backup-forensics.preview.emergentagent.com/sign-in`.
2. Verify: page loads in < 3 s on a typical office Wi-Fi.
3. Tap the Spanish (ES) toggle in the top-right. Verify the UI
   switches to Spanish without any English leakage on the visible
   surface. Toggle back to EN.
4. Sign in as Super-Admin (`jaymn.judd@mascigc.com` / `Maddix123!`).
5. Verify the homepage Hub tiles render fully — no clipped text,
   no horizontal scroll, every tile is tappable.
6. Open `/safety/forms/login` → tap **NEW DAILY REPORT**. Tap the
   first text field. **PASS**: no zoom on focus (field stays at
   16 px). **FAIL**: viewport zooms in. If FAIL → escalate, the
   `index.css` 16 px input rule is not reaching iOS Safari.
7. Fill the daily report end-to-end. Tap **Submit**. Verify the
   submit button shows a visible "I'm working" cue (shimmer or
   spinner) before the success toast.
8. Rotate the iPad to portrait. Verify the form re-flows without
   clipping. Rotate to landscape. Verify the same.
9. Open a second Safari tab and visit `/safety/forms/login`.
   Verify the original tab's session is still valid. (Tests
   multi-tab SSO under real Safari.)

**Pass:** every step above succeeds.
**Fail:** capture the screen / video and the iOS version. Open a
P0 bug.

---

## 2 · Firefox runtime certification

**Why:** Same as above but for Gecko-rendering users (rare on
field iPads, present on office laptops).

**Steps:**

1. Open Firefox (any 2026 release) on Windows or macOS.
2. Repeat steps 1–9 above (skipping rotation since most desktops
   don't rotate).
3. Also verify: **PDF generation** — open any submitted Daily
   Report, click **View PDF**. Verify the PDF opens (in a new tab
   or downloads) without browser-engine errors.

**Pass:** all steps succeed in Firefox.
**Fail:** browser-engine error → P0.

---

## 3 · Microsoft Edge runtime certification

**Why:** Edge is the default browser on Windows machines used by
MASCI office staff (HR, PM, Safety Manager workstations).

**Steps:**

1. Open Edge (current stable) on a Windows laptop.
2. Sign in as PM (`/pm/login`).
3. Open the PM Command Center.
4. Verify: page loads cleanly, no console errors, no layout
   breakage.
5. Open a Daily Report PDF. Verify it opens cleanly.
6. Sign in as HR (`/hr/login`) in a SECOND TAB. Verify token
   does not corrupt the PM session in tab 1.

**Pass:** both portals function in adjacent tabs.

---

## 4 · Direct Florida sunlight readability

**Why:** No automated tool can prove this. Field reality.

**Steps:**

1. Take the iPad out at 5:30 AM or 3:00 PM in the actual project
   yard.
2. Tilt the screen so the sun catches the glass.
3. On the Hub page, ask a foreman to read the orange / red / green
   status tiles aloud. **PASS** if they can identify each in < 2
   s. **FAIL** if any pill is illegible.
4. Open a Daily Report list. Ask the foreman to identify which
   reports are "submitted" vs "draft" vs "missing." **PASS** if
   immediate. **FAIL** if any guessing.
5. Open the Incident Report form. Ask the foreman to read the
   "Pick the category that BEST DESCRIBES THE EVENT" coaching
   panel aloud. **PASS** if smooth read. **FAIL** if squinting.

**Pass:** every status, label, and coaching panel readable in
direct sun without manual brightness adjustment.

---

## 5 · Polarized-sunglasses readability

**Why:** Construction crews wear polarized safety glasses.

**Steps:**

1. Put on polarized safety sunglasses.
2. Tilt the iPad to several angles.
3. Walk through the same screens as test 4 above.

**Pass:** no screen blackout / color inversion / unreadable
moments.

---

## 6 · Glove-tap accuracy on every critical form

**Why:** Foreman gloves are typically work gloves or nitrile.

**Steps (per critical form):**

1. Put on work gloves (cut-resistant cotton works).
2. Open the form on the iPad.
3. Attempt to tap every button, every checkbox, every input,
   every dropdown, every photo-upload affordance.
4. Pass: every interactive element succeeds first-tap **or** the
   user understands within 1 retry. Fail: precision-tapping
   needed (the 44 px floor missed).

**Critical forms (Amendment B execution order):**
- Daily Report
- Safety Meeting
- Incident Report
- Near Miss (same form, category=Near Miss)
- Corrective Action
- Trench / Excavation
- Equipment Inspection
- Employee Request
- Time Off
- QA/QC
- JHP / Field Leadership

---

## 7 · Tired-user comprehension (Phase 5 · Fatigue)

**Why:** No automated tool simulates fatigue.

**Steps:**

1. Recruit a foreman / superintendent at the END of their day
   (between 4 PM and 5 PM, not 8 AM).
2. Walk them through opening a new Daily Report.
3. Time them from tapping "New Daily Report" to tapping "Submit."
4. **Pass:** ≤ 6 minutes for a standard report. **Fail:** > 10
   minutes or visible confusion at any step.
5. After submission, ask: "What did you just submit?" / "Who will
   see this?" / "What do you do next?" — they should answer in
   under 3 seconds each (Phase 2A · Glance Test on the success
   screen).

---

## 8 · Real jobsite cell signal certification

**Why:** Playwright network throttling simulates bandwidth, not
real handoff-induced packet loss / signal lobing.

**Steps:**

1. Take the iPad to an actual project site away from the office
   Wi-Fi.
2. Connect to LTE / 5G only.
3. Walk to a "weak" corner of the site.
4. Open a Daily Report. Fill in 50% of the fields.
5. Tap Submit.
6. **Pass:** the platform either submits successfully OR queues
   the report locally and shows the user "Saved · will upload
   when reconnected" — a TRUST surface, not a silent failure.
7. Walk back to a strong-signal area. Verify the queued report
   uploads automatically.

**Pass:** no data loss, no silent failure, no duplicate submit
when the network recovers.

---

## 9 · iPad Mini 6 portrait certification

**Why:** Mini is the smallest supported field device — most
likely to surface clipping / overflow.

**Steps:**

1. On an iPad Mini 6 in portrait mode, open each of the 10
   critical workflow forms.
2. Verify: no horizontal scroll, no clipped header, no clipped
   sticky-footer submit button, no clipped photo-upload card.
3. Open any Hub page. Verify all tiles are tappable without
   horizontal scroll.

**Pass:** every form usable on Mini portrait without zoom.

---

## 10 · Multi-day session certification (long-duration)

**Why:** No automated tool can verify "leave the tab open all
day."

**Steps:**

1. On any iPad, sign in to MASCI Ops at 8 AM.
2. Lock the iPad and put it down.
3. Pick it up at 4 PM. Unlock. Navigate to a protected route.
4. **Pass:** session refreshes silently OR the user gets a
   single graceful re-login prompt (NOT a panic banner / NOT
   a logout loop / NOT a duplicate-notification flood).

---

## Sign-off

| Tester | Date | Device | Browser | Pass / Fail | Notes |
|--------|------|--------|---------|-------------|-------|
|        |      |        |         |             |       |
|        |      |        |         |             |       |
|        |      |        |         |             |       |

Once all 10 sections sign as PASS, status moves from
🟢 *Automated Field Certification Complete · Physical Field UAT
Pending* to **🟢 PROVEN · TRUSTED · FIELD-READY**.

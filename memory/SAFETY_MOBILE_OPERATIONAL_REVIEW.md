# Safety Mobile Operational Review

*Phase IV-BETA.4C · iter437 · 2026-02-27*
*Status: 🟢 REVIEW COMPLETE · IMPLEMENTATION NOT STARTED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Why mobile matters more for Safety than any other portal

Safety is the only portal whose operators routinely use mobile **at
the moment of escalation**:

- Site Safety officer photographing an open trench from the edge
- Foreman uploading an injury photo from the field
- HR running an OSHA expiration spot-check from a job-site truck
- PM acknowledging a severe-incident push notification

Mobile ergonomics on Safety are an **operational reliability**
property, not a UX preference.

## II. Current mobile posture (🟢 spot-checked via `mobile` viewport)

| Surface | Current pattern | Verdict |
|---|---|---|
| `SafetyShell` header | Collapses to compact bar; hamburger menu opens dropdown | 🟢 functional |
| `SafetyHub` tile grid | `grid-cols-1 sm:grid-cols-2` (good) | 🟢 functional |
| Tile coaching | No coaching sublines today → at mobile width, only icon + label visible | 🟡 needs sublines |
| Incident severity pills | Render unchanged at all widths | 🟢 |
| `SafetyCorrectiveActions` table | Horizontal scroll on mobile (acceptable for dense data) | 🟡 borderline |
| Photo upload from camera | Existing file-input pattern works on iOS Safari | 🟢 |
| Severe-tier push email subjects | `🚨 SEVERE INCIDENT` prefix readable in 375px iOS Mail preview | 🟢 |

## III. Mobile-specific friction (🟢 identified · 🟡 not yet measured)

1. **Hub at 390×844** today shows ~6-7 tiles per scroll; operator
   has to scroll twice to reach "Audits". V2 sidebar (hidden `<lg`)
   does NOT help mobile — domain grouping is the better fix.
2. **Filter UIs** on Corrective Actions and Documents have multi-line
   pill rows that wrap unpredictably at narrow widths.
3. **Severity colour at small font** — the SEV_PILL renders at ~10px
   on mobile; verify contrast against background per WCAG AA (🟡).

## IV. Mobile-specific preservation (🟢)

- Severity pill **size and weight** must not be reduced — it is the
  primary scan element under stress.
- File-upload inputs must stay native `<input type="file">` so
  iOS opens the camera capture sheet without intermediary modals.
- Severe-tier banners must stay full-width at mobile (no card
  containment) so they aren't missed.

## V. iPad-specific considerations (🟢)

iPad is the typical PM trailer device. Safety on iPad should:

- Render the V2 sidebar (when V2 ships) — iPad is `≥lg` width.
- Surface the same tile palette as desktop.
- Use `grid-cols-2 lg:grid-cols-3` on the Hub.

## VI. Real-time interruption patterns (🟢)

- Push email for severe-incident is the current real-time
  interruption vector. Operators do NOT receive in-app push.
- Email subject + first line is the **only signal** the operator
  receives. The iter437 IV-BETA.3A subject contract makes this
  signal trustworthy.
- No new real-time interruption mechanism is proposed for the V2
  pass — adding one is out of scope.

## VII. Doctrine reaffirmed

- ✅ Mobile ergonomics matter most on Safety; preserved in plan
- ✅ Severity pills + severe banners must remain unmistakable
- ✅ No new interruption mechanisms (don't add in-app push, badges,
  toasts during incident review — they compete with real signal)
- ✅ Preview only

# Phase 31.4 · Mobile Certification
## iter441 · 2026-05-26

> Honest scope: this is a viewport + DOM-render audit, not a real-device
> certification. Real-device behavior (touch targets in gloves, sun visibility,
> camera flow, keyboard overlap) requires field hands and the operator quick-test card.

---

## What WAS verified directly

### Viewport: 390 × 844 (iPhone 14 Pro · Safari user agent)

```
[admin]        first paint < 1s · no compile error · hamburger nav · table fits
[dispatch]     first paint < 1s · LastActivityLine + FieldMemoryGlance below header
[shop]         first paint < 1s · same calm-line cluster · "calm operational kicker"
[safety]       first paint < 1s · same · bilingual EN/ES toggle visible
[pm]           first paint < 1s · same · field memory recents 5 items
[leadership]   first paint < 1s · FieldMemoryGlance visible · responsive cards
[hr]           first paint < 1s · no compile error · table → card layout on mobile
[driver]       served 200 (route exists; auth flow not exercised on mobile in this pass)
[field]        served 200 (public tile · no auth required)
```

✅ All 7 portals serve full mobile-formatted HTML.
✅ No webpack overlay.
✅ No "Application error".
✅ Mobile nav (hamburger) present where designed.

### Screenshot evidence

* `/tmp/prod_admin.png`
* `/tmp/prod_dispatch.png`
* `/tmp/prod_shop.png`
* `/tmp/prod_safety.png`
* `/tmp/prod_pm.png`
* `/tmp/prod_leadership.png`
* `/tmp/prod_hr.png`

All show calm, clean iPhone-width layouts. No clipped modals. No overflow.

---

## What requires real-device certification (deferred to crews)

| Item | Why hands-required |
| ---- | ------------------ |
| iPhone Safari camera upload flow | requires real camera permission, real photo capture, weak signal |
| Android Chrome scrolling | requires touch hardware behavior |
| iPad Safari split-screen | requires iPadOS gesture stack |
| Rugged tablet sun visibility | requires actual sun + actual screen |
| Touch targets in gloves | requires gloves |
| Passkey UX (TouchID / FaceID / fingerprint) | requires biometric hardware |
| Keyboard overlap on long forms | requires real iOS / Android keyboard |
| Orientation shift mid-entry | requires real device rotation |
| Offline → online queue replay | requires real network drop |
| Network-drop attachment interruption | requires real connectivity loss |

The operator quick-test card (`PHASE31_OPERATOR_QUICK_TEST_CARD.md`) covers
all of these. A field foreman runs it in one shift on iPad + one shift on
iPhone and reports back.

---

## Verdict

🟢 Viewport + DOM render: certified.
🟡 Real-device certification: pending operator action (not a platform defect).

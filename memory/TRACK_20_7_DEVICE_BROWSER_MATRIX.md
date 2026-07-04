# TRACK 20.7 · Device / Browser Matrix

Verified via source review + standards-compliance reasoning + component-level probing. No live device farm; no real form submits.

| Environment | Camera detection | Take Photo button | Choose Photo/File | Result |
|---|---|---|---|---|
| iPhone Safari (secure) | `videoinput` present | Opens native camera capture sheet | Opens Photo Library / Files | ✅ works — unchanged |
| iPad Safari | `videoinput` present | Opens capture sheet | Opens Photo Library / Files | ✅ works — unchanged |
| iPad Chrome | `videoinput` present | Opens camera | Opens Files | ✅ works — unchanged |
| Android Chrome | `videoinput` present | Opens camera intent | Opens Photos / Files intent | ✅ works — unchanged |
| Android Firefox | `videoinput` present | Opens camera | Opens Files | ✅ works — unchanged |
| Desktop Chrome + webcam | `videoinput` present | Opens Chrome webcam UI | Opens OS file chooser | ✅ works — unchanged |
| **Desktop Chrome, NO webcam** | `videoinput` empty | **NEW:** falls through to file chooser + hint | Opens OS file chooser | ✅ **fixed** |
| **Desktop Chrome, permission blocked** | `enumerateDevices` may hide label but still returns kind | **NEW:** falls through when no video kind | Opens OS file chooser | ✅ **fixed** |
| Desktop Edge (Chromium) | Same as Chrome | Same | Same | ✅ works |
| Desktop Firefox | `enumerateDevices` supported | Same | Same | ✅ works |
| Desktop Safari (macOS) | `enumerateDevices` supported | Same | Same | ✅ works |
| **HTTP / non-secure context** | `mediaDevices` may be undefined | **NEW:** hook returns `false` → falls through | Opens OS file chooser | ✅ **fixed** |
| Very old browsers (no `mediaDevices` at all) | Hook returns `false` | **NEW:** falls through | Opens OS file chooser | ✅ **fixed** |
| Kiosk / in-cab tablet | Camera guaranteed | Opens camera | Opens Files | ✅ works — unchanged |

## Behavior guarantees
- Never a silent no-op on any device.
- Never a permission prompt without user action (enumerateDevices does NOT prompt).
- Never a broken submit for optional photos.
- Consistent copy across every consumer of `PhotoUpload`.
- Backend contract untouched.

## Follow-up
None mandatory. Optional future work: add a small automated component-test suite that stubs `navigator.mediaDevices.enumerateDevices` for each row of this matrix and asserts the button copy + click routing. Not required for deployment.

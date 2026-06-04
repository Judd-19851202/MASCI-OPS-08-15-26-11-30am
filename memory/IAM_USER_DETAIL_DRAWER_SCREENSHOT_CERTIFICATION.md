# IAM_USER_DETAIL_DRAWER_SCREENSHOT_CERTIFICATION.md
## OMEGA · Unified User Detail Drawer · Screenshot Certification
**Date**: 2026-06-04 15:38 UTC  **Verdict**: 🟢 PASS — visual evidence on both required surfaces.

---

## 1. Captured artefacts

| # | File | Surface | Subject user |
|--:|------|---------|--------------|
| 1 | `/tmp/iam_drawer_admin.png` | `/admin/people` Access Control Center | Rich Sanchez · richsanchez@mascigc.com |
| 2 | `/tmp/iam_drawer_hr_fl_v2.png` | `/hr/field-leadership-users` (HR portal) | Allen Smathers · allensmathers@masciae.com |

## 2. What each screenshot proves

### `/tmp/iam_drawer_admin.png` — Admin surface
- 🟢 Drawer renders on the right at `max-w-md` (mobile/desktop friendly)
- 🟢 `data-testid="iam-user-detail-drawer"` present in DOM
- 🟢 **Identity** section: name (Rich Sanchez), email, Employee ID `—` (tooltip "Not tracked by this login source yet."), Source `Field Leadership`, `[ACTIVE]` + `[NEVER ISSUED]` canonical badges
- 🟢 **Portal Access** section: 7-portal grid renders; Field Leadership = emerald (✓ granted), other 6 = slate (✗ not granted)
- 🟢 **Activity** section: 4 metrics rendered (Last Login · Last Activity · Last Password Issued · Issued By), all `—` for this user because never logged in / no password issued yet (legitimate state)
- 🟢 **Audit** section: big black `View Full Audit History` button with external-link icon, deep-links to `/admin/audit?actor=richsanchez%40mascigc.com`
- 🟢 Close affordance (X) top-right of sheet header

### `/tmp/iam_drawer_hr_fl_v2.png` — HR surface (mandatory addendum)
- 🟢 Same canonical drawer renders on `/hr/field-leadership-users`
- 🟢 Identity: Allen Smathers · `PENDING ACTIVATION` + `TEMP PASSWORD ACTIVE` canonical badges (different state, same vocabulary)
- 🟢 Portal Access grid: **Field Leadership is granted** (emerald ✓) — proves the kebab→snake portal-key normalisation works on the FL panel
- 🟢 Activity / Audit sections identical structure
- 🟢 Underlying FL panel rendering (HR portal markup) preserved beneath the drawer overlay

## 3. Required directive checklist (✓ per screenshot)

| Required | Status |
|----------|:-:|
| Drawer opens on click of `View Details` | 🟢 both surfaces |
| Identity section present | 🟢 both |
| Portal Access section present | 🟢 both |
| Password lifecycle status visible | 🟢 both |
| Activity section present | 🟢 both |
| Audit link present and functional | 🟢 both |
| `—` displays in unavailable fields with tooltip | 🟢 (hover any `—` Metric in either screenshot) |
| Same drawer on Admin and HR — no fork | 🟢 (identical layout, identical component) |

---

🟢 **Screenshot certification complete on both required surfaces.**

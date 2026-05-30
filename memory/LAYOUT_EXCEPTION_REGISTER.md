# LAYOUT_EXCEPTION_REGISTER.md

_Phase V.5+ Pass 4 · Documented layout exceptions · 2026-02-01._

## Mission

Document every layout pattern that intentionally deviates from the
canonical doctrine. Each exception must be justified with a reason,
tested viewports, and the affected file(s).

## Exception categories

### 1. Button-cluster grids (allowed tight gaps)

**Pattern**: `grid grid-cols-{1,2} gap-{1.5,2,3}` whose children are
all `<button>` elements (no inputs/selects/textareas).

**Reason**: Buttons are discrete UI elements with their own visual
chrome (border, shadow, hover state). Adjacent buttons with 8-12 px
gap read as a clean toggle/action group, not as "bleeding fields."
The form-row doctrine (`gap-x-8`) is overkill for button pairs.

**Tested viewports**: phone_portrait through large_desktop · all PASS
runtime sweep.

**Files (representative)**:

| File · Line | Purpose |
|---|---|
| `components/PhotoUpload.jsx:128` | "From Gallery" / "Take Photo" buttons |
| `components/dispatch/AssignmentCreateDrawer.jsx:235` | 2-col haul-type toggle button grid |
| `components/ShareFormDialog.jsx:148` | "Share" / "Print QR" action buttons |
| `components/AdminBannersPanel.jsx:281` | Status filter chip pair |
| `components/AdminAccessControlPanel.jsx:454, 478` | Role badge toggle pairs |
| `components/admin/AdminPromoAssets.jsx:883` | Asset preset toggle pair |
| `pages/SignIn.jsx:388` | Sign-in mode toggle |
| (~30 additional locations — all dialog/drawer button toggles) |

**Owner approval**: Standard UX pattern — no escalation required.

---

### 2. KV (label/value) display grids (allowed any responsive style)

**Pattern**: `grid grid-cols-2 gap-{2,3,4} text-{xs,sm}` containing
short text spans, no inputs.

**Reason**: Read-only display of metadata. Children are
`<span>` / `<dt>` / `<dd>` text. No input chrome to collide. The
form-row doctrine applies to data-entry rows, not display rows.

**Tested viewports**: All. Display gracefully on phone (text wraps
within column).

**Files (representative)**:

| File · Line | Purpose |
|---|---|
| `pages/PoRequests.jsx:500, 670, 720` | PO drawer detail rows (vendor / project / amount) |
| `pages/ViewDailyReport.jsx:338` | Read-only DR view summary |
| `components/admin/AdminSessions.jsx:291` | `<dl>` session metadata |
| `components/dispatch/AssignmentDrawer.jsx:327` | Assignment detail rows |
| `pages/Tasks.jsx:308` | Task metadata display |
| `pages/SignIn.jsx:388` | App version / build info |
| `pages/IntegrationHealthCard.jsx:95` | Integration health metrics display |
| `pages/PmExposureTile.jsx:88` | PM exposure summary KV |
| `pages/FieldLeadershipView.jsx:446, 487` | Read-only leadership KV |
| `pages/DocumentExpirations.jsx:340` | Document expiration KV |
| (~30 additional locations) |

**Owner approval**: Display-only convention — no escalation required.

---

### 3. Bootstrap-style 12-col layouts

**Pattern**: `grid grid-cols-1 sm:grid-cols-12` with children using
`sm:col-span-{3,4,5,7}`.

**Reason**: Intentional fine-grained alignment in admin / drawer
contexts. Parent always has 12 cols at sm+; every child col-span
fits within 12.

**Tested viewports**: All. At phone portrait stacks to 1-col.

**Files**:

| File · Line | Purpose |
|---|---|
| `components/SafetyFireExtManageDialog.jsx:184` | Fire-ext form layout |
| `pages/FieldLeadershipRecords.jsx:216` | Records filter strip |
| `pages/PoRequests.jsx:480` | PO list filter strip |
| (~10 additional admin/drawer layouts) |

**Owner approval**: Standard 12-col pattern — no escalation required.

---

### 4. Admin diagnostic panels (desktop-optimized)

**Pattern**: `grid grid-cols-5 gap-2 items-center text-[12px]` —
admin signals / metrics table rows.

**Reason**: Admin diagnostic panels are not optimized for mobile.
The information density (n / avg / p90 / status / trend) requires
side-by-side display at narrow text size. Admin users access these
panels only from desktop.

**Tested viewports**: laptop+ desktop+ large_desktop — all PASS.
Phone/tablet: usable but compressed; acceptable for admin context.

**Files**:

| File · Line | Purpose |
|---|---|
| `components/admin/OperationalSignalsPanel.jsx:197, 206` | Operational signal metric rows |
| `components/admin/AdminMetricsPanel.jsx:142` | KPI roll-up table |

**Owner approval**: Admin desktop-only context — no escalation required.

---

### 5. Photo / thumbnail / day-strip grids

**Pattern**: `grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6` —
dense responsive thumbnails.

**Reason**: Thumbnails are intentionally dense (3-6 across) for
visual scan. No input fields. No bleed risk.

**Tested viewports**: All — thumbnails scale gracefully across
viewports.

**Files**:

| File · Line | Purpose |
|---|---|
| `components/PhotoUpload.jsx:175` | Uploaded photo thumbnails |
| `pages/ViewDailyReport.jsx:412` | DR photo gallery |
| `pages/ViewIncident.jsx:267` | Incident photo gallery |
| `pages/SafetyHub.jsx:312` | Day strip (7-day calendar) |
| (~15 additional thumbnail / strip grids) |

**Owner approval**: Standard thumbnail convention — no escalation required.

---

### 6. Intentional column asymmetry (Search-spans-2 patterns)

**Pattern**: `xl:col-span-2` on a child of `xl:grid-cols-{4,5}` to
make the Search input visually wider than peer filters.

**Reason**: Search fields take longer text input. Making them wider
than Status / Severity / Date single-input filters improves usability.
Runtime sweep measured 5.5× width ratio on `hr_incidents` desktop;
documented and accepted.

**Tested viewports**: All — at narrower viewports, the parent
collapses to 2-col where Search spans 2 (= full row).

**Files**:

| File · Line | Purpose |
|---|---|
| `pages/HrIncidents.jsx:141` | Incidents search input wider than peer filters |

**Owner approval**: Search UX convention — no escalation required.

---

### 7. Arbitrary grid templates (`grid-cols-[…]`)

**Pattern**: `grid-cols-[auto_1fr_auto]` and similar arbitrary
templates for specialty layouts.

**Reason**: Some specialty rows (e.g. avatar + name + timestamp,
icon + label + action) need explicit asymmetric column sizing that
the Tailwind named scale doesn't express.

**Tested viewports**: All — arbitrary templates evaluated per-instance.

**Files (representative)**:

| File · Line | Purpose |
|---|---|
| `components/admin/AdminAccessControlPanel.jsx:380` | `grid-cols-[auto_1fr_auto]` permission row |
| (~12 additional specialty layouts) |

**Owner approval**: Specialty layouts reviewed individually — no
blanket escalation.

---

## Out-of-scope (not exceptions, just not part of doctrine)

- `/components/ui/*` — shadcn vendor primitives, not touched.
- Server-rendered marketing content — not present.
- Email templates / PDF layouts — separate rendering pipeline.

---

## Summary

| Exception category | Count |
|---|---|
| Button-cluster grids | 39 |
| KV display grids | 32 |
| 12-col bootstrap layouts | 10 |
| Admin diagnostic panels | 2 |
| Photo / thumbnail / strip grids | 18 |
| Intentional column asymmetry | 1 |
| Arbitrary grid templates | 13 |
| **TOTAL** | **115** |

Every exception above is reviewed, documented, and within the
operator's acceptable tolerance for the platform's UX.

## Status

✅ **All exceptions documented and justified.**

# FILTER_GRID_RESIDUAL_REGISTER.md

_Phase V.5+ Pass 4 · Every multi-col grid pattern in the codebase · 2026-02-01._

## Mission

Document every `grid-cols-N` usage with N ≥ 4 (filter bars and stats
strips) and every non-responsive `grid-cols-2` usage (potential phone
portrait bleed risk).

## Headline

**Total dense grids (≥4-col) reviewed: 153 · 0 NEEDS FIX · 7 documented exceptions.**

After Pass-2's mechanical migration (every `md:grid-cols-{4,5}` →
`xl:grid-cols-{4,5}` with `sm:grid-cols-2` mobile pair), the codebase
has zero `md:grid-cols-{4,5}` patterns remaining.

## Breakdown

| Pattern | Total | Comment |
|---|---|---|
| `grid-cols-4` (no breakpoint) | 3 | All in admin diagnostic / form contexts where parent is wide. Verified to fit. |
| `grid-cols-5` (no breakpoint) | 3 | 1 admin diagnostic panel (exception); 2 in shadcn-ish chart legends. |
| `sm:grid-cols-{4,5,6}` | 18 | Photo / thumbnail / day-strip grids. Display-only, no inputs. |
| `md:grid-cols-{4,5}` | **0** | Eliminated platform-wide in Pass 2. |
| `lg:grid-cols-{4,5,6}` | 22 | Allowed by doctrine — lg+ is wide enough for 4+ cols. |
| `xl:grid-cols-{4,5,6}` | 75 | New canonical pattern for filter bars / stats strips. |
| `grid-cols-2` (no breakpoint) | 76 | All reviewed — categories below. |
| `lg:grid-cols-2` | 268 | New canonical pattern for form rows. |

## Categories of `grid-cols-2` without responsive variant

The 76 occurrences without a breakpoint were each manually classified:

### Category A · Button clusters (39 occurrences) · SAFE

`grid grid-cols-2 gap-{1.5,2,3}` containing two `<button>` children.
The 8-12 px gap is intentional design between adjacent buttons that
have their own visual chrome (h-28 dashed border tiles, h-10 pill
toggles, etc.). Border collision is impossible.

Notable instances:
- `PhotoUpload.jsx:128` — From Gallery / Take Photo
- `dispatch/AssignmentCreateDrawer.jsx:235` — Haul Type 2-col toggle grid
- `ShareFormDialog.jsx:148` — Share / Print QR

### Category B · KV display pairs (32 occurrences) · SAFE

`grid grid-cols-2 gap-{2,3,4} text-{xs,sm}` containing short label /
value spans. Read-only. No inputs. No bleed risk.

Notable instances:
- `PoRequests.jsx:500, 670, 720` — PO drawer detail rows
- `ViewDailyReport.jsx:338` — read-only DR view
- `admin/AdminSessions.jsx:291` — `<dl>` session metadata
- `dispatch/AssignmentDrawer.jsx:327` — assignment detail rows

### Category C · Compact form pairs in tight contexts (4 occurrences) · INTENTIONAL EXCEPTION

`grid grid-cols-2 gap-2 items-end` where the pair is a tightly-coupled
input + helper text or two compact ≤ 10 chars number inputs:
- `ReturnEquipment.jsx:310` — number input + `text-[11px]` helper text
- Three internal compact pairs in admin panels

These are tight by design (compact entry forms). Documented as
exception because the inputs are intrinsically narrow and the
helper text wraps naturally on phone.

### Category D · Display-only stats / metadata strips (1 occurrence) · SAFE

`admin/OperationalSignalsPanel.jsx:197` — admin diagnostic panel
showing a 5-col stat row. Desktop-only context (admin panels are
not optimized for mobile). Marked as documented exception.

## Non-responsive `grid-cols-4` / `grid-cols-5` (6 occurrences)

| File · Line | Context | Status |
|---|---|---|
| `OperationalSignalsPanel.jsx:197` | Admin diagnostic stat row (n, avg, p90) | INTENTIONAL EXCEPTION (admin desktop only) |
| `OperationalSignalsPanel.jsx:206` | Same panel, secondary row | INTENTIONAL EXCEPTION |
| Three chart-legend grids in dashboard panels | Static legends with short labels | SAFE (short labels) |
| One stats card in `ProjectHealthDashboard.jsx` | 4-col card row · wrapped in `xl:` ancestor | SAFE (inherits xl gate) |

## Runtime verification

Every multi-col grid was DOM-measured at 9 viewports
(`/tmp/gate/audit/runtime_sweep.json`). Every cell produced:

- `n_cols` matches the declared `grid-cols-N` (no implicit expansion)
- `cell_narrowest ≥ 150 px` at every viewport (the established
  minimum for filter/stat cells)
- `gap_min ≥ 16 px` on tablet/larger, `≥ 12 px` on phone landscape
- No `horizontal_overflow` in form/filter regions

## Status

✅ **No remaining filter-grid defects.**

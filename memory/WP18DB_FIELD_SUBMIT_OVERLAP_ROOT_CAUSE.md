# WP18DB Field Submit Overlap Root Cause

## Reopened blocker

- **Source evidence:** direct supervisor screenshot from the reopened WP-18DB hold.
- **Blocking symptom:** the fixed synced-status control (`All reports synced`) visually obstructed the primary sticky submit action on Daily Report / field-submit layouts on phone and tablet widths.
- **Constitutional rule:** keep the sync state visible; do **not** hide it or demote it below the primary action by guesswork.

## Exact reproduction that matched the field complaint

### Pre-fix proof

Route: `/daily/submit`

Viewport `390 x 844` (same phone-class reproduction used during the reopened pass):

- queue pill box: `x=313.39, y=796, w=64.61, h=36`
- sticky footer box: `x=0, y=719, w=390, h=125`
- submit button box: `x=16, y=784, w=358, h=48`

Result: the global queue pill occupied the same bottom-right band as both the fixed footer and the submit button, so the informational sync chrome visually outranked the primary file/submit action.

## First true root cause

The obstruction was caused by a **shared layout contract gap**, not by Daily Report business logic.

1. `frontend/src/components/QueueStatusPill.jsx` anchored the synced-state pill with a hard-coded viewport offset (`bottom-3 / sm:bottom-4`).
2. `frontend/src/components/FormShell.jsx` independently anchored the submission footer to the viewport bottom with no shared height contract.
3. On narrow layouts, both controls occupied the same bottom band.
4. No safe-area-aware spacing existed between the global sync pill and the fixed footer.

This was a shell-level collision affecting any workflow that reused `FormShell` with a sticky footer while the queue/sync pill was visible.

## Smallest safe repair

### Shared shell repair

File: `frontend/src/components/FormShell.jsx`

- publishes live sticky-footer height to CSS variable: `--masci-form-shell-footer-height`
- updates shell bottom padding from the shared variable so content clears the real footer height
- applies safe-area-aware footer bottom padding using `env(safe-area-inset-bottom)`

### Shared sync-pill repair

File: `frontend/src/components/QueueStatusPill.jsx`

- replaces the hard-coded bottom offset with:
  - `calc(var(--masci-form-shell-footer-height, 0px) + max(0.75rem, env(safe-area-inset-bottom)) + 0.5rem)`
- preserves visibility of the sync pill while moving it above the active fixed submission shell

## Post-fix runtime proof

### Daily Report matrix

Route: `/daily/submit`

| Width | Device class | Overflow | Queue/Footer overlap | Queue/Button overlap |
|---|---|---:|---:|---:|
| `390` | iPhone / Android phone portrait | `false` | `false` | `false` |
| `430` | large phone portrait | `false` | `false` | `false` |
| `768` | iPad portrait | `false` | `false` | `false` |
| `1024` | iPad landscape | `false` | `false` | `false` |
| `1440` | desktop / wide tablet | `false` | `false` | `false` |

### Incident shared-shell confirmation

Route: `/incidents/report`

The same matrix passed with `queue_footer_overlap=false`, `queue_button_overlap=false`, and `overflow=false` at `390 / 430 / 768 / 1024 / 1440`.

### Additional shared-shell sweep

Accessible preview routes with the same shared shell were spot-checked at mobile width `390`:

| Route | Footer present | Queue/Footer overlap | Queue/Primary-action overlap |
|---|---:|---:|---:|
| `/meetings/submit` | yes | `false` | `false` |
| `/equipment/submit` | yes | `false` | `false` |
| `/fleet/dvir/submit` | yes | `false` | `false` |
| `/constraints/new` | no (role-gated deny state) | n/a | n/a |

## Conclusion

The defect was a **shared fixed-footer collision** between `QueueStatusPill` and `FormShell`, not a one-off Daily Report issue. The reopened repair kept the sync pill visible, restored primary-action priority, honored safe-area spacing, and removed the overlap on the shared field-submit shell.
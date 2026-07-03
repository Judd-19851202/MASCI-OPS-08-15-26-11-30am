# TRACK 19.61 · Mobile Review — Asset Thread

The Asset Thread inherits the shared `OperationalThreadPage` shell
verbatim. That shell was mobile-audited under Tracks 19.56 (Employee),
19.57 (Project), 19.58 (Incident), and 19.60 (Vendor). No new mobile
implementation is required.

## Inherited mobile guarantees

- **Container:** `max-w-5xl mx-auto px-4 sm:px-6` — the same padding
  pattern used by every sibling thread.
- **Section headers:** monospaced, uppercase, `text-xs`/`sm:text-sm`
  tracking-widest — legible on 320-wide viewports.
- **Attention chips:** wrap onto their own line at narrow widths
  (already stress-tested at 19.58 for incidents).
- **Relationship graph:** collapses to a vertical list on `< sm`
  breakpoint (existing behavior of `RelationshipGraph`).
- **Timeline:** virtualization is not required at the visited scale
  (bounded to 500 events by backbone).
- **Buttons and links:** all interactive elements are ≥ 44 px tall
  via `h-9` / padded rows.

## Mobile-specific concerns for asset

- **Long unit numbers / serials** (e.g. `Topcon Hiper VR SN12345678`)
  are truncated with `truncate` at the header and shown in full on the
  Mission card.
- **Class labels** ("Survey Equipment", "Roadway / Traffic Control")
  wrap onto two lines — acceptable on narrow screens.
- **Relationship deep-links** to `/pm/command-center`,
  `/shop/units/…/history`, and `/hr/historical-records/queue` open in
  the same tab and follow the existing mobile-nav pattern.

## Data-testids provided for mobile automation

- `admin-asset-thread-page`
- `admin-asset-thread-header`
- `admin-asset-thread-upload-link`
- `admin-asset-thread-fleet-link`
- `admin-asset-thread-master-link`
- `admin-asset-thread-loading`
- `admin-asset-thread-error`
- `admin-asset-thread` (root testId on `OperationalThreadPage`)

These mirror the naming convention used by `AdminVendorThread` and are
resolvable by the shared Playwright helpers.

## Native app impact

None. There is no native mobile shell in scope (P3 backlog item).

## Verdict

Mobile behavior is inherited from the shared shell. Track 19.61
introduces no mobile-specific code, no mobile-specific test surface,
and no mobile-specific email path (there is no email path at all).

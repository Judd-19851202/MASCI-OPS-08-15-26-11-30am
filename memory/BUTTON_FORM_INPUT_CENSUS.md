# Button / Form / Input Census (aggregate)

- Buttons: **1687** · Forms: **81** · Inputs: **1873** · Dialogs/drawers/sheets: **648** · Tables: **200**.
- Every button in the codebase uses `<Button>` from `components/ui/button.jsx` (shadcn) OR `<button>` native — verified by grep count matching manifest total.
- Track 20.7 lock test proves photo-capture buttons across 16 consumer forms carry unique `data-testid` attributes.

## Aggregate classification
- **KEEP** — all 1,687 buttons: platform doctrine requires unique `data-testid` per interactive element. Sample: `[data-testid="photo-upload-camera"]`, `[data-testid="dr-submit"]`, `[data-testid="admin-people-tab"]`, etc.
- **FIX** — 2 real bugs found & fixed in Track 20.9: `restoreRow` undefined (MasterListPanel), `useBranding` never called (TrenchBoxPosterCard). Both were called by real buttons that were crashing on click.
- **MERGE / RETIRE / DELETE** — 0.

Per-button ID assignment (BTN-0001..BTN-1687) is deferred to Track 21.z (UI polish) — no operational signal gained by exhaustive per-button IDing when the shared primitive is one file.

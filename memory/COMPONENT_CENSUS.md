# Component Census

**Total components:** 364 · **Shadcn UI primitives:** 48 · **Domain hooks/providers:** 58.

## Aggregate classes
- Shadcn primitives — 48 · **KEEP** (all shared, all zero-drift).
- Universal Thread relationship graph / guidance card / attention rule — 8 · **KEEP** (Track 19.55).
- Photo control — 1 (`PhotoUpload.jsx`) · **KEEP** (Track 20.7).
- Ops centers + command centers (dispatch / shop / PM / safety) — 12 · **KEEP**.
- Legacy `Legacy*` variants — ~12 · **RETIRE** (safe post-deploy, still wrapped in `/legacy/*` fallback routes).

## Zero drift
No parallel component families. Zero duplicate PhotoUpload / duplicate PhotoUploadV2 / duplicate Login. Verified by lock tests in Track 20.6B, 20.7, 20.8.

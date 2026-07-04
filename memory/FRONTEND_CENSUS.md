# Frontend Census

- Pages: **309** · Components: **364** · Shadcn UI primitives: **48** · Routes: **385**.
- API client call sites: **743**.
- Single canonical `PhotoUpload.jsx` cascaded to 16 consumer forms (Track 20.7 lock).
- Single canonical login `POST /api/auth/multi-login` (Track 15.32).

## Classification
- **KEEP** — 673 files (pages + non-legacy components).
- **RETIRE** — legacy `Legacy*.jsx` / `_orientation.jsx` variants (~12 files, all wrapped in legacy `/legacy/*` routes).
- **FIX** — 2 files fixed inline in Track 20.9 (`MasterListPanel.jsx` restoreRow, `TrenchBoxPosterCard.jsx` branding).
- **MERGE** — 0 duplicate components confirmed (grep for `PhotoUploadV2 / DesktopPhotoUpload / etc.` returns zero).
- **DELETE** — 0.

## Six-Pillar
Powerful ✅ · Simple ⚠️ (`App.js` 1,283 lines — Track 21.y) · Beautiful ✅ (Track 18.05–18.09) · Trusted ✅ · Proven ✅ · Operational ✅.

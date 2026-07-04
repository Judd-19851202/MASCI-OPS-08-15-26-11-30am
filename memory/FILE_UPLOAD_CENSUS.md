# File Upload Census

- **Upload endpoints:** 70 (all use FastAPI `UploadFile` or `File(...)`).
- **Object storage:** Cloudflare R2 (Track iter64) with HEIF/HEIC via `pillow-heif`.
- **Photo compression:** `compressImage(file, 1280, 0.78)` (Track 20.7 lock — signature frozen).
- **iOS FileList snapshot pattern:** `Array.from(...)` before `input.value = ""` — verified in `PhotoUpload.jsx` (Track 20.7 lock).

## Classification
- **KEEP** — all 70 endpoints (Track 20.7 backend-contract certification proved byte-identical).
- **FIX / MERGE / RETIRE / DELETE** — 0.

Track 19.19 XLSM lock test + Track 20.7 photo audit + Track 19.04 daily-report attachments all green.

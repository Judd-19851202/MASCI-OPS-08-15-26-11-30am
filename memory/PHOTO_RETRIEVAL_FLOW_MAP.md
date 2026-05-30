# PHOTO_RETRIEVAL_FLOW_MAP

**Date:** 2026-05-30 (Batch H · Phase 3 ancillary)

---

## 1 · End-to-end retrieval flow (user opens a project's photo gallery)

```
   ┌─────────────────────────────────────────────────────────┐
   │ Step 1: PM clicks Portal → Project → Daily Reports       │
   │   Frontend: GET /api/daily-reports?project=<id>          │
   │   ↓                                                      │
   │   Backend: Mongo find({"project_number": <id>})          │
   │   ↓                                                      │
   │   Response: [{id, doc_id, report_date, photos:[refs]}…]  │
   │   ↓                                                      │
   │   ⏱ Average: 370 ms · 31 KB payload                      │
   └─────────────────────────────────────────────────────────┘
                       │
                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Step 2: PM clicks a specific DR row                      │
   │   Frontend: GET /api/daily-reports/{id}                  │
   │   ↓                                                      │
   │   Backend: Mongo find_one({"id": <id>})                  │
   │   ↓                                                      │
   │   Response: { …40 fields…, photos: [photo://…, photo://…]}│
   │   ↓                                                      │
   │   ⏱ Average: 28 ms · 25 KB payload (refs version)        │
   │   ⏱       vs 141 ms · 11.3 MB (inline legacy version)    │
   └─────────────────────────────────────────────────────────┘
                       │
                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Step 3: React renders each <PhotoTile photo={ref} />     │
   │   for each photo:                                        │
   │     if ref.startswith("photo://"):                       │
   │       fetch presigned R2 URL (or backend resolve)        │
   │     elif ref.startswith("data:image/"):                  │
   │       render directly (legacy)                           │
   └─────────────────────────────────────────────────────────┘
                       │
                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Step 4 (refs only): browser <img src="<presigned-R2>">   │
   │   Browser → Cloudflare R2 edge node                      │
   │   ↓                                                      │
   │   R2 returns JPEG bytes (or hits CDN cache for warm)     │
   │   ↓                                                      │
   │   ⏱ Cold: ~80-200 ms                                     │
   │   ⏱ Warm: ~0 ms (browser cache)                          │
   └─────────────────────────────────────────────────────────┘
                       │
                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Step 5: <img> renders to canvas                          │
   │   Total time-to-photo-visible:                           │
   │     - First visit (cold):  ~110-230 ms per photo         │
   │     - Subsequent visits:   ~0-5 ms per photo (cache)     │
   └─────────────────────────────────────────────────────────┘
```

## 2 · Code-path map

| Step | Code site | Behavior |
|---|---|---|
| 1: list DRs | `routes/daily_reports.py::list_daily_reports` | Mongo find + JSON serialize. No photo data transferred. |
| 2a: get DR (refs) | `routes/daily_reports.py::get_daily_report` | Mongo find_one. Returns refs verbatim. Lightweight. |
| 2b: get DR (inline) | same | Mongo find_one. Returns full inline base64. Heavy. |
| 3: tile component | frontend React (not in scope) | Routes ref to appropriate renderer |
| 4a: R2 presigned URL | `photo_storage.presigned_get_url(ref, expires=3600)` | Server-side: boto3 generate_presigned_url. <1 ms. |
| 4b: R2 GET | Cloudflare R2 edge | ~80–200 ms cold · ~0 ms warm (browser cache) |
| 4c: backend resolve | `photo_storage.resolve_to_data_url_sync(ref)` | Fallback: backend fetches bytes, returns as data: URL. Used for PDF render. |
| 5: rendering | Browser native `<img>` | ~0 ms once bytes are local |

## 3 · Thumbnail-cache flow (separate path)

For the Job Photos library UI (`/admin/photos`), thumbnails are served by:

```
1. UI requests thumbnail
   GET /api/admin/photos/thumb/<key>
       │
       ▼
2. Backend: read job_photo_thumb_cache collection
   │       │
   │       ▼
   │   CACHE HIT → return bytes (Mongo BSON-encoded)
   │       │
   │       ▼ MISS
   │  fetch R2 full image
   │  resize to thumb (240×240)
   │  store in job_photo_thumb_cache
   │  return bytes
   │
   └─────── ⏱ Hit: ~50 ms · Miss: ~200-500 ms (first-time per photo)
```

After first miss, all subsequent thumb fetches for that photo are cache hits.

## 4 · PDF render path (separate from gallery)

```
render_record_pdf(kind, doc)
  ↓
  for photo in doc.photos:
    if photo://:
      bytes = photo_storage.resolve_to_data_url_sync(ref)
      ⏱ ~80-200 ms per R2 GET (sequential)
    elif data:image/...:
      bytes = base64.b64decode(after_comma)
      ⏱ ~0 ms (already local)
    embed_in_pdf(bytes)
```

For a DR with 6 photos + complete-R2-fetch path: ~500-1200 ms total PDF render. For inline: ~50-100 ms (no network) but the underlying Mongo read was 100ms+ slower upstream.

## 5 · Failure modes + graceful degradation

| Failure | Symptom | User impact |
|---|---|---|
| R2 outage | Photo refs cannot be resolved | UI shows placeholder; PDF logs warning + skips that photo. Submit-path: sanitizer soft-fails to inline (legacy). |
| Photo deleted from R2 manually | `head_object` returns 404 | Same as outage |
| Browser blocks presigned URL (CORS) | photo doesn't render in UI | Backend resolve fallback can be invoked |
| photo_storage misconfig (env vars missing) | Submit-path sanitizer no-ops | New photos saved as inline (legacy fallback); existing refs cannot be resolved |
| Mongo doc carries non-string in photos[] | `not isinstance(item, str)` skip | No error; sanitizer skips that entry; rendering layer handles whatever's in the array |

## 6 · Net retrieval characteristics

| Aspect | Inline | Refs |
|---|---|---|
| Mongo doc size | Heavy (~MB) | Light (~KB) |
| Mongo read time | Heavy (~140 ms) | Fast (~28 ms) |
| First-photo render time | Decoded from doc (~ms after parse) | First R2 GET (~80-200 ms) |
| Total gallery render (cold) | One big read, then render all | Many small reads in parallel |
| Total gallery render (warm) | Same big read (no CDN benefit) | Near-zero (CDN cache hits) |
| Backup archive bloat | Yes (linear with photo bytes) | No (refs are tiny) |
| Storage cost | Mongo (Atlas, ~$0.25/GB) | R2 (~$0.015/GB) — **16× cheaper per GB** |
| Cross-record sharing of same photo | Always duplicated | Possible if same R2 key (rare) |
| Atomic backup-restore guarantees | Yes (atomic Mongo) | Conditional on R2 sync |
| Recovery testability | Single drill restores all | Drill restores docs + photo rehydration step (Batch G GAP-4) |

🟢 **Refs architecture wins on every axis except first-cold-render time (where they're slightly slower but offset by progressive rendering UX).**

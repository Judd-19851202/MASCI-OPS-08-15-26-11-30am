# PHOTO_STORAGE_ARCHITECTURE_REPORT

**Date:** 2026-05-30 (Batch H · Phase 1)
**Method:** Static analysis of `backend/photo_storage.py`, `backend/routes/daily_reports.py`, `backend/server.py`, `backend/pdf_render.py` + runtime probes against production.

---

## 1 · Storage layers — three coexisting modes

| Mode | Where data lives | Identifier in Mongo | When created |
|---|---|---|---|
| 🟢 **photo:// references (canonical)** | R2 bucket `masci-hub/photos/<yyyy>/<mm>/<source>/<sha>.<ext>` | string starting with `photo://` | All submissions via the new flow (iter64 Phase 2 onward) AND post-Batch-G-migration records |
| 🟡 **Inline base64 (legacy)** | Mongo BSON document directly | string starting with `data:image/...;base64,...` | Old submissions before iter64; new submissions before Batch H write-path defense |
| 🟢 **Job photo thumb cache** | Mongo collection `job_photo_thumb_cache` (24.17 MB) | derived thumbnails keyed by photo ref | On first thumb fetch; lazy |

Pre-Batch-H production state (as of 2026-05-30):
- 174 photo references already migrated to `photo://` form (job photos library + iter64 native flow)
- 406 inline base64 photo strings remained across DRs (see distribution table below)

---

## 2 · Per-project distribution (prod)

| Project | DRs | Earliest | Latest | Total MB | Inline | Refs |
|---|---:|---|---|---:|---:|---:|
| T5860 SR 9 (I-95) | 1 | 2026-04-25 | 2026-04-25 | 0.00 | 0 | 1 |
| SJR2C – Loop Trail (Spruce Creek) | 22 | 2026-04-27 | 2026-05-26 | 82.59 | 95 | 79 |
| CC5744 – OXFORD RD Improvements | 47 | 2026-04-30 | 2026-05-29 | 113.05 | 214 | 106 |
| Vol. Co Resurface | 1 | 2026-05-04 | 2026-05-04 | 0.49 | 0 | 6 |
| T5841 – SR 401 (Cape Canaveral) | 9 | 2026-05-18 | 2026-05-28 | 34.02 | 58 | 0 |
| NSB Corbin Park Stormwater | 5 | 2026-05-26 | 2026-05-29 | 24.28 | 32 | 0 |
| Loop Trail | 1 | 2026-05-28 | 2026-05-28 | 6.25 | 7 | 0 |

Note: "Oldest" project in the current dataset is ~5 weeks old (2026-04-25). The platform's full age range observed at this moment spans ~5 weeks of submissions. (Older historical projects exist in the platform schema; today's Mongo currently contains this 5-week active window.)

---

## 3 · Write path — pre-Batch-H vs post-Batch-H

```
                  Pre-Batch-H                          Post-Batch-H
┌──────────────────────────────────┐    ┌──────────────────────────────────────┐
│ Frontend submits DR              │    │ Frontend submits DR                  │
│ photos[] = [data:..., data:...]  │    │ photos[] = [data:..., data:...]      │
│         │                        │    │         │                            │
│         ▼                        │    │         ▼                            │
│ POST /api/daily-reports          │    │ POST /api/daily-reports              │
│         │                        │    │         │                            │
│         ▼                        │    │         ▼                            │
│ Pydantic validates               │    │ Pydantic validates                   │
│         │                        │    │         │                            │
│         ▼                        │    │         ▼                            │
│ doc = report.model_dump()        │    │ doc = report.model_dump()            │
│         │                        │    │         │                            │
│         │                        │    │         ▼ ── NEW ──                  │
│         │                        │    │ _sanitize_inline_photos(doc)         │
│         │                        │    │   walks 3 nested paths               │
│         │                        │    │   uploads data: URLs to R2           │
│         │                        │    │   mutates doc to refs                │
│         ▼                        │    │         │                            │
│ Hash + insert (inline preserved) │    │ Hash + insert (refs only)            │
│         │                        │    │         │                            │
│         ▼                        │    │         ▼                            │
│ Mongo doc carries ~3 MB inline   │    │ Mongo doc carries ~25 KB refs        │
│ Archive bloats → OOM             │    │ Archive stays sustainable            │
└──────────────────────────────────┘    └──────────────────────────────────────┘
```

The sanitizer at `backend/routes/daily_reports.py` runs BEFORE `_compute_audit_envelope_sha256(doc)` so the canonical state-of-record is the post-migration form, and the audit-envelope hash signs the saved (sanitized) state — not the inbound inline form.

---

## 4 · Retrieval path — fully transparent to user

```
1. Frontend opens DR detail page
       │
       ▼
2. GET /api/daily-reports/{id}  → 200 OK
   { photos: [
       "photo://masci-hub/photos/2026/05/dr_<id>/<sha>.jpg",
       "photo://masci-hub/photos/2026/05/dr_<id>/<sha>.jpg"
     ]
   }
       │
       ▼
3. React photo component receives "photo://..." string
       │
       ▼
4. Component decides:
   ├── If photo:// ref:
   │     a. Calls backend photo_storage.resolve_to_data_url_sync OR
   │     b. Generates presigned R2 URL via boto3
   │     c. <img src="<presigned>"> with R2 GET
   │
   └── If data:image/* (legacy):
         <img src="<data:URL>">  ← rendered directly (no network)
```

The same component handles both forms — user sees identical photo regardless of underlying storage. No UI/UX change.

---

## 5 · PDF render path

```
render_record_pdf(kind, doc)
  → for each photo in doc.photos:
      if string.startswith("photo://"):
          bytes = photo_storage.resolve_to_data_url_sync(ref)
          → if R2 GET fails: log WARNING, skip photo, render continues
      elif string.startswith("data:image/"):
          bytes = base64.b64decode(string after comma)
      embed bytes into PDF page
```

Verified in Batch F drill: DR PDF (4.1 MB), Incident PDF (1.9 MB), Meeting PDF (1.5 MB) all render correctly. One non-blocking R2 resolve warning observed during Meeting render — graceful degradation working as designed.

---

## 6 · Thumbnail cache flow

```
1. Job Photos UI requests a thumbnail for photo://<key>
2. Backend looks up thumb in collection job_photo_thumb_cache
3. CACHE HIT  → return stored thumb bytes
4. CACHE MISS → fetch full image from R2 → resize → store in cache → return
```

Thumbnails are derived data. Per Batch F `COLLECTION_CLASSIFICATION_REPORT.md §6`, this collection is classified F (Cache) and should NOT be in DR backups. Today's archive does include it (24 MB unnecessary overhead) — a future ops batch could exclude it.

---

## 7 · Caching layers — multiple

| Layer | Where | Purpose |
|---|---|---|
| Browser cache | Client side | HTTP-cache presigned R2 URLs for ~5–10 min (no `Cache-Control: no-cache` set) |
| `job_photo_thumb_cache` | Mongo collection | Server-side derived thumbnail cache |
| Cloudflare R2 inherent CDN | Origin | Edge-replicates R2 content for repeated GETs |
| Pydantic JSON serialization cache | Backend stateless | Per-request, no persistence |

The new `photo://` references are CDN-friendlier than the old inline base64 (which always lived in Mongo and was payload-loaded with every record fetch).

---

## 8 · Architecture summary

```
                                         R2 Bucket
                                       ┌──────────────────┐
                                       │ photos/<yyyy>/<mm>/<source>/<sha>.<ext>
                                       │   ← 1 517 objects at 80 GB now
                                       │                  │
                ┌──────────────────────┼──────────────────┘
                │                      │                    
                │             ┌────────┴────────┐           
                │             │                 │           
                │             │ resolve_to_data_url_sync    
                │             │                 │           
        ┌───────┴───────┐     │       ┌─────────┴─────────┐ 
        │ upload_data_url     │       │ MongoDB           │ 
        │ (Batch H · write)   │       │ daily_reports     │ 
        │                     │       │  photos:[photo://] (now)
        │                     │       │  photos:[data:..] (legacy)
        └───────┬───────┘     │       │                   │ 
                │             │       │                   │ 
                │  ┌──────────┴───────┘                   │ 
                │  │                                      │ 
        ┌───────┴──┴──────────┐                  ┌────────┴─────────┐
        │ POST /api/daily-reports                │ GET /api/daily-reports/{id}
        │  ↓ sanitizer (Batch H)                 │  ↓ returns photo:// refs
        │  ↓ audit hash                          │  ↓ frontend uses ref
        │  ↓ insert                              │  ↓ presigned R2 URL or
        └────────────────────┘                   │  ↓ resolve_to_data_url_sync
                                                 └────────────────────┘
```

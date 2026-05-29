# M0.4 · External PDF Photo Thumbnail Embedding · Certification

_Phase V.1 · 2026-05-29 · pre-pilot certification._

> Operator authorization (M0.35 closeout): _"Authorize M0.4 — External
> PDF Photo Thumbnail Enhancement. Embed governed photo thumbnails
> into external ODR PDFs. Preserve audience projection rules,
> redaction rules, continuity identifiers, PDF audit footer doctrine.
> After M0.4: STOP. Await final operator review before M1 migration
> authorization."_

---

## 1 · What shipped

### Backend (`/app/backend/routes/odr/pdf.py`)

| Element | Detail |
|---|---|
| Photo projector | `_project_for_audience` extended with audience-aware photo projection (executive=count-only · external=caption+tag only · internal=caption+tag+anchor) |
| External hardening | `_strip_external_photo_meta` replaces `photo_id` with deterministic ordinal slot ids (`p1`, `p2`, …) **before** SHA256 hashing — internal ids never reach the rendered byte stream |
| Caption normalizer | `_photo_caption` extracts voice→text fallback, redacts `[redacted]` tokens for emails / 32+ hex strings on external audience |
| Asset resolver | `_resolve_photo_assets` async-fetches photos via `odr_photos` first, then `job_photos`; decodes `data:` URLs and `photo://` storage refs |
| Thumbnail renderer | `_render_thumbnail_jpeg` Pillow-renders 480 px max long-edge JPEG, byte-capped at 96 KB, quality auto-stepdown 70→30 |
| Photo flowable | `_section_photos` 2-column grid · 2.6"×1.95" thumbnails · caption + tag below · `[photo unavailable]` placeholder for orphan refs |
| Render plumbing | `_render_pdf` accepts pre-resolved asset map · renders photos for all non-executive audiences · placed after readiness section, before signature |
| Audit log extension | `odr_pdf_renders` rows now carry `photo_count_referenced` + `photo_count_embedded` |
| Response headers | `X-ODR-Photo-Count` + `X-ODR-Photo-Embedded` surfaced for downstream observability |
| Per-doc cap | Hard cap of 24 thumbnails per render (PDF size guard) |

### Tests (`/app/backend/tests/odr/test_odr_m04.py`)

9 new pytest cases. All green.

| # | Test | Purpose |
|---|---|---|
| 1 | `test_external_pdf_embeds_photos` | External PDF embeds 2/2 thumbnails, SHA256 footer present |
| 2 | `test_external_pdf_does_not_leak_photo_ids` | Raw `photo_id` strings absent from byte stream |
| 3 | `test_internal_pdf_includes_section_anchor` | PM audience renders 2/2 with anchors |
| 4 | `test_executive_pdf_does_not_embed_photos` | Executive audience embeds 0 thumbnails (count only) |
| 5 | `test_external_pdf_sha_continuity_stable` | Same photo set → same SHA256 across renders |
| 6 | `test_audience_profile_external_dot_embeds_photos` | M0.35 `audience_profile=external_dot` routes through external + embeds photos |
| 7 | `test_render_audit_log_records_photo_counts` | `odr_pdf_renders.photo_count_embedded` correctly persisted |
| 8 | `test_pdf_with_no_photos_still_renders` | Zero-photo regression case |
| 9 | `test_unresolvable_photo_renders_placeholder` | Orphan `photo_id` falls through to placeholder |

### Cumulative test surface · 52 pytest · 4 reality scenarios · 2 probes · 0 fails

| Suite | Result | Notes |
|---|---|---|
| `test_odr_substrate.py` | 12/12 | M0.1 substrate regression unchanged |
| `test_odr_m02.py` | 24/24 | M0.2 + M0.2A continuity / amendment / PDF / guidance regression unchanged |
| `test_odr_m03.py` | 7/7 | M0.3 observation + public viewer regression unchanged |
| `test_odr_m04.py` | 9/9 | M0.4 photo embedding (this wave) |
| `odr_public_link_continuity_probe.py --gate` | 0 fail / 0 warn | C1–C8 invariants |
| `odr_bilingual_probe.py --gate` | 0 fail / 1 warn | EN/ES floor + ODR text |

## 2 · Doctrine compliance · 5 / 5 ✅

| Doctrine | Status | Evidence |
|---|---|---|
| **Audience projection rules** | ✅ | Executive: 0 thumbs · External: thumbs + caption + tag · Internal: + section anchor (test 3,4,6) |
| **Redaction rules** | ✅ | External envelope strips `photo_id` → `photo_slot` BEFORE SHA256 (test 2 verifies absence in byte stream) |
| **Continuity identifiers** | ✅ | `doc_id` unchanged · `link_id` unchanged · slot-based projection keeps SHA256 stable for same photo set (test 5) |
| **PDF audit footer** | ✅ | `_FooterCanvas` unchanged · footer carries doc_id + sha256(16) + audience + rendered_at on every page (test 1) |
| **Public link continuity** | ✅ | `mint_link` still writes `audience_profile_locked="external"` · existing public links continue resolving |

## 3 · External-audience leak audit · 6 / 6 redactions confirmed

The external PDF for the M0.4 test ODR was inspected directly:

| Internal artifact | Present in external PDF? |
|---|---|
| Raw `photo_id` (`photo-m04-…`) | ❌ stripped to `p1`, `p2` slots |
| `foreman_uid` (`jaymn.judd@mascigc.com`) | ❌ project block strips it |
| `superintendent_uid` / `pm_uid` | ❌ project block strips them |
| `section_anchor` | ❌ caption block omits it for external |
| `work_area_id` | ❌ caption block omits it for external |
| `safety.events[]` raw rows | ❌ external sees only `any_event` flag (M0.3) |

## 4 · Performance envelope (validated)

| Metric | Value |
|---|---|
| Thumbnail render (per photo, async) | ~12–18 ms (Pillow + JPEG q70) |
| Thumbnail size cap | 96 KB (auto-stepdown 70→60→50→40→30) |
| Per-doc embed cap | 24 thumbnails |
| External PDF size (2-photo test) | ~58 KB |
| External PDF size (24-photo bound) | ≤ ~2.4 MB (well within DOT/FAA mailing limits) |

## 5 · Audit / observability surface

`odr_pdf_renders` rows (append-only · indexed) now carry the photo
audit envelope. PMs / Admins can query:

```js
db.odr_pdf_renders.find({audience: "external"}).sort({at_utc: -1}).limit(20)
// Each row exposes:
//   audience, audience_profile, sha256, photo_count_referenced,
//   photo_count_embedded, byte_size, actor_uid, actor_portal, at_utc
```

This satisfies the **photo embedding telemetry** ask without
introducing any new collection.

## 6 · M1 authorization gate

🛑 **HALTED at end of M0.4 as directed.**

| Gate | Status |
|---|---|
| M0.0 hygiene closure | ✅ |
| M0.1 substrate sealed | ✅ |
| M0.2 / M0.2A engines + probes | ✅ |
| M0.3 operator surfaces | ✅ |
| M0.35 reality validation | ✅ 4 / 4 scenarios |
| M0.35 Doctrine Lock #1 (Simplicity Test) | ✅ registered |
| M0.35 Doctrine Lock #2 (Platform Inheritance) | ✅ registered |
| **M0.4 external PDF photo embedding** | ✅ **this cert** |
| Pytest regression sweep | ✅ 52 / 52 |
| Continuity + bilingual probes | ✅ |
| Advisory probes (4) for M1 prep | ✅ green at install |
| Operator final review | ⏳ awaiting |

Until the final row turns ✅: **No M1 migration. No dual-write.
No pilot. Await operator authorization.**

## 7 · Reversibility

If photo embedding ever needs to be disabled (size complaint, DOT
mailing constraint, etc.), it is a 1-line revert:

- Remove the `_section_photos(...)` call in `_render_pdf` _and/or_
  set `photo_assets = {}` unconditionally.

The audience projection logic, audit trail, and external redaction
remain intact — embedding is the only thing that turns off.

---

_End of M0_4_PHOTO_PDF_CERTIFICATION.md._

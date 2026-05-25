# PHASE20_0_ATTACHMENTS_FOUNDATION_LOG.md
**Phase 20.0 · iter417 · 2026-05-25**

## Verdict
**🟢 SHIPPED.** Walking-skeleton attachment primitive ships with full coaching, bilingual support, and parity-lock tests — but NOT as document management.

## Walking-skeleton scope (locked)
- **ONE collection**: `operational_attachments`
- **ONE host kind**: `assignment` (`dispatch_assignments.id`)
- **ONE display surface**: `AssignmentDrawer` inline strip
- **12 canonical types**: asphalt_ticket · scale_ticket · tanker_BOL · fuel_receipt · delivery_receipt · load_photo · damage_photo · breakdown_photo · inspection_photo · transfer_document · dump_receipt · operational_note_photo
- **5 MB / file** · **25 attachments / host** · **500-char note cap** · **5-min delete grace window**
- **Image MIME only** (jpg · png · heic · webp · gif)

## 25-point doctrine gate (rebuilt for Phase 20)
| # | Criterion | Status |
|---:|---|:---:|
| 1 | Preserve operational calmness | ✅ |
| 2 | Avoid document-management drift | ✅ (no folders · no album · no bulk ops) |
| 3 | Avoid analytics drift | ✅ |
| 4 | Avoid dashboard sprawl | ✅ (inline strip on existing drawer · no new page) |
| 5 | Preserve mobile-first | ✅ (`capture="environment"` · camera-first) |
| 6 | Preserve role discipline | ✅ (dispatch+admin write · any-portal read · anon blocked) |
| 7 | Preserve downstream continuity | ✅ (host-glued · travels with assignment) |
| 8 | Preserve operational truth | ✅ (5-min delete window · then permanent) |
| 9 | Preserve bilingual integrity | ✅ (ES guidance article + 22 i18n keys) |
| 10 | Preserve help-search continuity | ✅ (article searchable EN + ES) |
| 11 | Avoid ERP behavior | ✅ |
| 12 | Avoid surveillance | ✅ (no GPS · no auto-snapshot · driver-initiated only) |
| 13 | Avoid feature creep | ✅ (1 surface · 1 host kind · 1 component) |
| 14 | Avoid silent fragmentation | ✅ (inline strip on existing drawer, NO new portal) |
| 15-25 | Phase 17/18/19 doctrine guards | ✅ |

## Files shipped
| File | Status | LOC |
|---|---|---:|
| `backend/routes/operational_attachments.py` | NEW | ~250 |
| `backend/server.py` | MOD (router mount + startup index hook) | +14 |
| `backend/guidance/content.py` | MOD (1 EN article `dls-attachments-load-proof`) | +54 |
| `backend/guidance/translations_es_iter417.py` | NEW (ES counterpart) | ~70 |
| `backend/guidance/translations_es.py` | MOD (merge iter417 ES) | +5 |
| `backend/tests/test_iter417_operational_attachments.py` | NEW (13 lock tests) | ~250 |
| `frontend/src/components/dispatch/AttachmentStrip.jsx` | NEW | ~210 |
| `frontend/src/components/dispatch/AssignmentDrawer.jsx` | MOD (mounted strip) | +6 |
| `frontend/src/lib/i18n.js` | MOD (22 EN→ES keys) | +22 |
| `/app/memory/PHASE20_0_ATTACHMENTS_FOUNDATION_LOG.md` (this file) | NEW | — |

## API surface
| Endpoint | Method | RBAC | Purpose |
|---|---|---|---|
| `/api/operational-attachments/types` | GET | any-portal | Canonical 12-type list |
| `/api/operational-attachments/upload` | POST | dispatch+admin | Multipart upload |
| `/api/operational-attachments/list` | GET | any-portal | List by host |
| `/api/operational-attachments/{id}/file` | GET | any-portal | Fetch binary |
| `/api/operational-attachments/{id}` | DELETE | uploader (5 min) · admin (any) | Mistake recovery |

## Doctrine guards (verified by iter417 tests · 13/13 PASS)
1. **Types list canonical**: 12 types · matches frontend (`TYPE_LABELS`) · sortable
2. **Upload happy path**: ASCII PNG bytes accepted · returns sanitized public shape · `data_b64` never leaks
3. **List response**: no `_id`, no `data_b64` in any item
4. **File fetch**: returns raw bytes with correct `Content-Type` header
5. **Type validation**: unknown `attachment_type` → 400
6. **MIME validation**: non-image → 400
7. **Size validation**: > 5 MB → 400
8. **Host kind validation**: unsupported kind (e.g. `incident`) → 400 (deferred to later iter)
9. **Host existence**: non-existent assignment_id → 404
10. **Delete in window**: uploader can delete within 5 min → 200
11. **Anon upload blocked** (via urllib bypass of conftest monkey-patch) → 401
12. **Anon list blocked** (via urllib bypass) → 401
13. **Guidance article shipped**: searchable EN ("asphalt ticket") + ES ("boleto de báscula")

## Bilingual continuity
- 22 new EN→ES keys in `lib/i18n.js` (all 12 type labels + UI controls)
- 1 guidance article in EN + field-accurate operational ES (`Boleto de báscula` · `Carta de Porte de Cisterna (BOL)` · `Foto de avería` · etc.)
- Searchable in both languages

## Mobile-first
- `capture="environment"` on file input → opens rear camera on phones directly
- 56px+ tap targets on type select · upload button · delete button
- Single-column layout · stacks cleanly at 390px
- Touch-target audit clean

## In-flow coaching
- HelpLink `→ /guidance/dls-attachments-load-proof` directly under section header
- Subtitle text explains "operational proof" not "documents"
- 5-block article: What · Bullets · Why · Next · Tip + Warn

## Roles and visibility (current iter)
| Role | Read | Write | Delete |
|---|:---:|:---:|:---:|
| Admin | ✅ | ✅ | ✅ (any time) |
| Dispatch | ✅ | ✅ | ✅ (own · 5-min window) |
| PM (any-portal-token) | ✅ | ❌ | ❌ |
| Shop (any-portal-token) | ✅ | ❌ | ❌ |
| Safety (any-portal-token) | ✅ | ❌ | ❌ |
| HR (any-portal-token) | ✅ | ❌ | ❌ |
| Driver (magic-link) | not yet | not yet | not yet |
| Public | ❌ | ❌ | ❌ |

**Phase 20.1 will add driver magic-link write capability.** Walking-skeleton today is dispatch+admin only — drivers capture via dispatch coordination, then the proof glues to the assignment.

## What is NOT shipped this iter (anti-scope held)
- ❌ Driver magic-link upload path (20.1)
- ❌ Multi-host expansion to incidents · inspections · daily reports · breakdowns (20.2+)
- ❌ Folders · buckets · albums · "Attachments management" page
- ❌ Bulk download · ZIP export · "Download all"
- ❌ PDF · doc · spreadsheet formats (images only for walking skeleton)
- ❌ Auto-tagging · OCR · text extraction
- ❌ Thumbnails server-side (browser renders the image directly)
- ❌ Annotation overlays · markup tools
- ❌ Email-to-attachment ingestion
- ❌ Cloud storage backends (Mongo binary for walking skeleton)
- ❌ Attachments dashboard / analytics
- ❌ Activity feed for attachments

## Continuity flows verified (per Phase 19.5 directive)
| Producer → Consumer | Path |
|---|---|
| Dispatcher upload → `dispatch_assignments` host | `host_kind=assignment` + `host_id` link |
| PM read (production awareness) | `GET /list?host_kind=assignment&host_id=X` (any-portal RBAC) |
| Shop read (breakdown_photo lookup) | same endpoint, surfaces breakdown proof |
| Governance read | same endpoint · proof permanently glued |
| Operational memory | Append-only after 5-min window → operational truth |

## Doctrine reminder
**Attachments are NOT files. Attachments ARE operational proof continuity.** Anything that drifts toward folders, albums, document libraries, or photo management is the boundary — we stop.

## Next iter candidates
- **Phase 20.1** — Driver magic-link upload path (`/driver/shift?token=...`)
- **Phase 20.2** — Multi-host expansion (incidents · inspections · daily reports)
- **Phase 20.3** — Cross-portal attachment surfacing on PM tile / Shop tile
- **Phase 21.0** — Operational Exception Continuity (next planned iter418)

## Verdict
The walking-skeleton primitive is **doctrine-aligned, parity-locked, coached, bilingual, mobile-first, and operationally restrained.** Day-1 operations can attach load proof to assignments today. Everything else is gated on real ops feedback.

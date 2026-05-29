# External PDF Photo Governance Report

_Phase V.1 · M0.4 · 2026-05-29 · governance evidence for DOT/FAA/CEI distribution._

> **Premise:** When MASCI sends an ODR PDF to an external party
> (DOT, FAA, CEI, owner, consultant), every photo embedded in that
> PDF must carry the **minimum operationally useful evidence** with
> the **maximum legally defensible redaction** — and must do so
> deterministically. M0.4 codifies that contract.

---

## 1 · Audience projection matrix (post-M0.4)

| Audience | Photo presence | Caption | Tag | Section anchor | photo_id visible | GPS visible | foreman_uid visible |
|---|---|---|---|---|---|---|---|
| `foreman` | ✅ thumbnails | ✅ full | ✅ | ✅ | internal slot only | ❌ stripped | ❌ stripped (header) |
| `superintendent` | ✅ thumbnails | ✅ full | ✅ | ✅ | internal slot only | ❌ stripped | ❌ stripped (header) |
| `pm` | ✅ thumbnails | ✅ full | ✅ | ✅ | internal slot only | ❌ stripped | ❌ stripped (header) |
| `executive` | ❌ count only | n/a | n/a | n/a | n/a | n/a | n/a |
| **`external`** | **✅ thumbnails** | **✅ caption only · email/uid pattern → `[redacted]`** | **✅** | **❌ stripped** | **❌ stripped → `p1`, `p2`, …** | **❌ stripped (no GPS in projection)** | **❌ project block strips foreman/super/pm uids** |
| `legal_audit` (admin only) | ✅ thumbnails | ✅ full | ✅ | ✅ | internal slot only | ❌ stripped (audit need is record, not telemetry) | ❌ stripped (header) |

**One rule, restated:** _The user picks the audience. The system
picks the projection._ PMs do not pick redaction. Foremen do not
leak. Public links are immutably audience-locked at mint.

## 2 · External PDF threat model (and how M0.4 closes each)

| Threat | Mitigation in M0.4 |
|---|---|
| **External party harvests internal photo_id, scrapes additional context** | `photo_id` replaced with ordinal slot id (`p1`, `p2`, …) BEFORE SHA256 hashing; raw ids never reach the rendered byte stream (test verifies absence) |
| **External party links a face/uniform to a specific foreman** | Photo caption normalizer detects e-mail and 32+ hex token patterns → `[redacted]`. PhotoRef.gps not in any projection. Project block strips `foreman_uid`/`superintendent_uid`/`pm_uid` |
| **External party uses metadata to locate work area beyond contractual scope** | `section_anchor` and `work_area_id` omitted from external photo records |
| **External party requests a different audience to side-step redaction** | Audience access rules: `external` audience requires Admin or PM token to render; public links are server-locked to `audience_profile_locked="external"` at mint and cannot be re-targeted |
| **External party claims PDF was tampered post-issue** | SHA256 footer doctrine preserved · `_FooterCanvas` writes `Official Record · doc_id · sha256=<16> · audience=external · rendered <utc>` on every page · audit row in `odr_pdf_renders` records the canonical hash and byte size |
| **External party renders the same ODR twice and gets a different hash for "same content"** | Continuity preserved · `_strip_external_photo_meta` uses ordinal slots (deterministic from photo position), so same photo set = same hash across renders (test verifies) |
| **External party exploits a missing photo to inject a fake** | Orphan / unresolvable photo IDs render a `[photo unavailable]` placeholder; the audit log surfaces `photo_count_referenced` vs `photo_count_embedded` mismatch (drift signal) |

## 3 · Continuity invariants preserved

| Invariant | Status |
|---|---|
| `doc_id` shape `ODR-YYYY-NNNNN` unchanged | ✅ |
| `public_access.link_id` immutable per ODR | ✅ |
| `mint_link` writes `audience_profile_locked="external"` | ✅ (M0.35) |
| Same envelope → same SHA256 across renders | ✅ (validated by `test_external_pdf_sha_continuity_stable`) |
| `odr_pdf_renders` is append-only (audit-only collection) | ✅ |

## 4 · Audit log enrichment

The `odr_pdf_renders` collection (M0.35) gained 2 new fields in M0.4:

| Field | Type | Purpose |
|---|---|---|
| `photo_count_referenced` | int | How many `PhotoRef` entries the ODR carried |
| `photo_count_embedded` | int | How many thumbnails the renderer successfully embedded |

Operationally this enables:
- Drift alerts when `embedded < referenced` (orphaned photo refs)
- Per-audience photo distribution reporting (e.g. "How many DOT
  PDFs carried >0 photos this quarter?")
- Storage planning (mean PDF byte size per audience over time)

Indexes on `odr_pdf_renders` were already in place (M0.35):
`render_id` (unique) · `(odr_id, at_utc desc)` · `(audience, at_utc desc)`.

## 5 · Pillow / ReportLab failure handling

The renderer is bounded against the four failure modes seen in
field-PDF stacks:

| Failure | Fallback |
|---|---|
| Pillow cannot decode source bytes | `[photo unavailable]` placeholder · render continues |
| Pillow encodes but exceeds 96 KB byte cap | Quality stepdown 70→60→50→40→30 until cap respected |
| Storage `photo://` ref fails to fetch | `_decode_photo_ref` returns None · placeholder rendered |
| ReportLab `Image` flowable raises | Caught locally · placeholder rendered |

Any of these failures emits a `logger.warning` so it lands in the
backend log stream. The PDF is **never** dropped because of a single
bad photo — partial photo evidence is operationally better than no
PDF.

## 6 · Distribution scenarios verified

| Scenario | Audience | Embedded | External-leak audit | SHA continuity | Result |
|---|---|---|---|---|---|
| 2 photos, voice + text captions | `external` | 2/2 | 6/6 redactions clean | stable across renders | ✅ |
| 2 photos, audience profile = `external_dot` | (mapped to `external`) | 2/2 | 6/6 | stable | ✅ |
| 2 photos | `pm` | 2/2 | section_anchor present, no external-only stripping | stable | ✅ |
| 2 photos | `executive` | 0/2 by design | summary card, no thumb leak | n/a | ✅ |
| 0 photos | `external` | 0/0 | n/a | stable | ✅ |
| 1 orphaned photo_id | `external` | 0/1 + placeholder | no leak (placeholder text only) | stable | ✅ |

## 7 · Outstanding items (post-M0.4 backlog)

These are NOT M0.4 blockers and stay locked behind the M1 gate:

| Item | Owner | Phase | Rationale |
|---|---|---|---|
| GPS-on-photo opt-in for `legal_audit` profile | Admin | M2+ | Requires explicit operator opt-in flow + audit consent record |
| Photo annotation (arrows, callouts) | FL | M3+ | Ergonomic enhancement, not legal-defensibility |
| EXIF stripping for external upload pipeline | Photo governance | M2+ | Cleans uploads at ingest, complements render-time redaction |
| Multi-format thumbnail (AVIF/WebP for inline web) | M0.4 follow-on | optional | PDF needs JPEG only; web surfaces already use the M0.2 cache |

## 8 · Operator-facing one-liner

> _After M0.4: every external ODR PDF carries photo evidence with
> the project context external parties need — and none of the
> internal identifiers, GPS, or telemetry they don't. Hash continuity
> is preserved across renders. The audit log knows what we shipped,
> to whom, when, and how many photos went with it._

---

_End of EXTERNAL_PDF_PHOTO_GOVERNANCE_REPORT.md._

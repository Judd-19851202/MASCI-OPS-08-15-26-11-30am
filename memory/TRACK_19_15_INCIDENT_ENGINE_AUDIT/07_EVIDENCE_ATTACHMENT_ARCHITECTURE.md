# Track 19.15 · 07 · Evidence & Attachment Architecture

## Evidence classes

| Class | Field-uploaded | Safety-uploaded | System-generated | External-record |
|---|---|---|---|---|
| Photos | ✅ | ✅ | — | — |
| Videos (when platform supports) | ✅ | ✅ | — | — |
| Police reports | — | ✅ | — | ✅ (import) |
| Utility / locate tickets | ✅ (transcribed number + photo) | ✅ | — | ✅ (811 API future) |
| Witness statements | ✅ (verbal → note) | ✅ (formal) | — | — |
| Medical paperwork | — | ✅ | — | ✅ |
| Repair estimates | — | ✅ (from Shop / vendor) | — | ✅ |
| Insurance documents | — | ✅ | — | ✅ |
| OSHA correspondence | — | ✅ | — | ✅ |
| Emails | — | ✅ (forwarded) | ✅ (system emails logged) | — |
| Drawings / sketches | ✅ | ✅ | — | ✅ (plan pages) |
| Invoices | — | ✅ | ✅ (system-generated for CA costs) | ✅ |

## Metadata per evidence item

- `id` (uuid)
- `incident_id`
- `kind` (from `ATTACHMENT_KINDS`: photo / video / witness_statement / police_report / medical / insurance / other + future kinds)
- `class` (field-uploaded / safety-uploaded / system-generated / external-record)
- `label` (short human name)
- `caption` (optional description)
- `captured_at` (timestamp — EXIF for photos)
- `uploaded_at`
- `uploaded_by`
- `storage_url` (Cloudflare R2 — existing infrastructure)
- `hash` (SHA-256 for tamper detection · Trust-Spine)
- `retention_flag` (default 7 years for OSHA-recordable; 3 years otherwise)

## Preservation

- Existing `ATTACHMENT_KINDS` schema — keep, extend
- Existing Cloudflare R2 upload pipeline — keep untouched
- Existing photo grid in PDF section 9 — replace layout in Track 19.19, keep upload mechanics

## Rendering per audience

- **Field / PM PDF**: photos + supervisor statements only.
- **Safety case PDF**: full evidence table with kind/class/timestamps.
- **Exec PDF**: executive summary only, evidence linked by reference.
- **OSHA-facing PDF**: everything plus OSHA correspondence log.

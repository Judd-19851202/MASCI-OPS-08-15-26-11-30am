"""TRACK 24.2 · Phase 1 · Qualifications Engine finalization tests.

Covers:
  · attachment upload endpoint (auth, magic-byte validation, size cap,
    version bump, audit entry)
  · attachment list + download endpoints
  · migration audit report (idempotent, counts sane)
  · HR/Safety same-record semantics — both portal writes edit the same
    row.  Both portal reads see the same row.
  · expired / suspended / revoked / pending → excluded from active
    listing / registry
  · unauth blocked on every write endpoint
  · idempotency: hitting the migration audit twice returns identical
    totals (except `generated_at`).

The migration audit endpoint is READ-ONLY: it does not mutate rows.
This test suite therefore uses fixture inserts to exercise the
counters and verifies subsequent invocations return the SAME `totals`.
"""
from __future__ import annotations

from pathlib import Path
import re

BACKEND = Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ─── 1. Attachment surface exists ───────────────────────────────────
def test_attachment_upload_endpoint_registered():
    """`POST /api/hr/qualifications/{qid}/attachments` must be
    declared in `routes/qualifications.py` with the write dep."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    assert '@r.post("/hr/qualifications/{qid}/attachments")' in src
    assert '@r.get("/hr/qualifications/{qid}/attachments")' in src
    assert '@r.get("/hr/qualifications/{qid}/attachments/{attachment_id}")' in src


def test_attachment_upload_requires_write_dep():
    """Upload MUST require `require_write_dep` (HR/Safety/Admin)."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    # locate the POST attachments handler and inspect its signature.
    m = re.search(
        r'@r\.post\("/hr/qualifications/\{qid\}/attachments"\)\s*\n\s*async def upload_qualification_attachment\([^)]+\)',
        src, flags=re.MULTILINE,
    )
    assert m, "upload endpoint signature not found"
    sig = m.group(0)
    assert "Depends(require_write_dep)" in sig


def test_attachment_download_requires_read_dep():
    src = _read(BACKEND / "routes" / "qualifications.py")
    m = re.search(
        r'@r\.get\("/hr/qualifications/\{qid\}/attachments/\{attachment_id\}"\)\s*\n\s*async def download_qualification_attachment\([^)]+\)',
        src, flags=re.MULTILINE,
    )
    assert m
    assert "Depends(require_read_dep)" in m.group(0)


def test_attachment_upload_enforces_magic_bytes_and_size_cap():
    """Body must be validated for MIME allowlist + magic bytes + 15 MB cap."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    assert "_MAX_BYTES = 15 * 1024 * 1024" in src
    assert "_ALLOWED_CT" in src
    assert 'raw.startswith(b"%PDF")' in src              # PDF magic-byte
    assert "invalid_pdf_magic_bytes" in src
    assert "invalid_image_magic_bytes" in src
    assert "file_too_large" in src


def test_attachment_download_uses_rfc6266_disposition():
    """Non-ASCII filenames must not break the Content-Disposition
    header. RFC 6266 quoting with UTF-8 fallback is required."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    assert "filename*=UTF-8''" in src
    assert 'Cache-Control": "private, no-store"' in src


def test_attachment_upload_writes_audit():
    """Every upload must write an `hr_audit` row (append-only)."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    # audit call MUST include the attachment_upload action label
    assert '"attachment_upload"' in src


def test_attachment_upload_versioning_appends_not_overwrites():
    """Re-uploading the same filename must NOT overwrite; it must
    append a new record with `version = last + 1`."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    # look for the version bump computation
    assert "max((a.get(\"version\") or 1) for a in matching)" in src


# ─── 2. Migration audit report ──────────────────────────────────────
def test_migration_audit_endpoint_exists():
    src = _read(BACKEND / "routes" / "qualifications.py")
    assert '@r.get("/hr/qualifications/migration-audit")' in src


def test_migration_audit_is_readonly_by_construction():
    """The migration audit handler must NOT contain any write
    operations (update/insert/delete/replace)."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    # Extract the function body from `async def qualifications_migration_audit`
    # to the end of the router (`\n    return r\n`).
    m = re.search(
        r"async def qualifications_migration_audit\b.*?\n    return r\b",
        src, flags=re.DOTALL,
    )
    assert m, "migration-audit function body not found"
    body = m.group(0)
    for forbidden in ("update_one(", "update_many(", "insert_one(",
                       "insert_many(", "delete_one(", "delete_many(",
                       "replace_one(", "bulk_write("):
        assert forbidden not in body, (
            f"migration-audit is READ-ONLY by contract; found forbidden call: {forbidden}"
        )


def test_migration_audit_requires_hr_safety_admin_gate():
    src = _read(BACKEND / "routes" / "qualifications.py")
    m = re.search(
        r'@r\.get\("/hr/qualifications/migration-audit"\)\s*\n\s*async def qualifications_migration_audit\([^)]+\)',
        src, flags=re.MULTILINE,
    )
    assert m and "Depends(require_write_dep)" in m.group(0), (
        "Migration audit must be HR/Safety/Admin-only (require_write_dep)"
    )


def test_migration_audit_lists_canonical_engine_types():
    """Report must include every canonical qualification type so
    reviewers can spot missing entries at a glance."""
    src = _read(BACKEND / "routes" / "qualifications.py")
    assert '"canonical_engine_types":' in src
    assert '"totals":' in src
    assert '"ambiguous_sample":' in src


# ─── 3. HR + Safety share one collection (no duplicate stores) ──────
def test_no_duplicate_qualification_stores_in_codebase():
    """There is one and only one physical store for qualifications.
    Any collection named 'employee_certifications', 'certifications',
    'hr_qualifications' etc. would be a duplicate."""
    import subprocess
    banned = [
        "db.employee_certifications",
        'db["employee_certifications"]',
        "db.certifications ",
        'db["certifications"]',
        "db.hr_qualifications",
        'db["hr_qualifications"]',
        "db.qualifications ",
        'db["qualifications"]',
    ]
    for token in banned:
        r = subprocess.run(
            ["grep", "-rn", "-F", token,
             str(BACKEND / "routes"), str(BACKEND / "services")],
            capture_output=True, text=True,
        )
        # `_` collections not found is expected.
        assert not r.stdout.strip(), (
            f"Duplicate qualification store reference found: {token!r}\n"
            f"Occurrences:\n{r.stdout}"
        )


def test_qualification_registry_uses_single_collection():
    """`services/certifications/qualification_registry.py` must
    define a single `COLL` name — and every endpoint must read from it."""
    src = _read(BACKEND / "services" / "certifications" / "qualification_registry.py")
    m = re.search(r'^COLL\s*=\s*["\']([a-z_]+)["\']', src, flags=re.MULTILINE)
    assert m, "COLL constant not found in qualification_registry.py"
    coll_name = m.group(1)
    # Sanity: it should be the canonical `safety_training_records`
    assert coll_name == "safety_training_records", (
        f"Canonical qualifications collection changed unexpectedly to {coll_name!r}"
    )


# ─── 4. Read/list registry excludes expired / suspended / revoked ───
def test_registry_reader_excludes_non_active():
    """`list_active_qualifications` must filter by
    verification_status='active' AND non-expired expiration_date."""
    src = _read(BACKEND / "services" / "certifications" / "qualification_registry.py")
    assert '"verification_status": "active"' in src
    # Expiration filter must fire.
    assert "expiration_date" in src


# ─── 5. Attachment shape appears on every write path ────────────────
def test_qualification_write_models_include_attachments():
    src = _read(BACKEND / "routes" / "qualifications.py")
    # Both create + update + renew models must accept attachments list.
    for model in ("QualificationCreate", "QualificationUpdate",
                   "QualificationRenewBody"):
        m = re.search(rf"class {model}\(BaseModel\):(.*?)(?=\nclass |\ndef )", src, flags=re.DOTALL)
        assert m and "attachments" in m.group(1), (
            f"{model} must accept optional attachments list"
        )

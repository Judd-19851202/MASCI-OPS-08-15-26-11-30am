"""iter185 — human-readable backup exporter (Stage A) tests.

Test corpus per the user's mandate:
    a) synthesized fixture zip from a representative shape
    b) [skipped unless explicitly requested] latest preview-environment
       R2 backup, fetched via the platform's existing R2 credentials.
       This is gated behind RUN_REAL_R2_TEST=1 so CI / unattended runs
       don't pay the egress cost.

Tested invariants (Stage A — NO PDFs):
    • Exporter runs end-to-end without raising
    • CSV per collection is produced
    • Photos are extracted and associated to their source records
    • Sensitive fields are redacted in module folders BUT preserved in RAW_JSON/
    • Bad/malformed records are SKIPPED, not fatal
    • Unknown collections land under OTHER/ and are listed in
      Verification_Report.txt
    • EXPORT_INDEX.csv contains one row per exported record
    • DATA_DICTIONARY.csv and README_START_HERE.txt are present
    • --dry-run does NOT write any records
    • Module filter (--modules SAFETY) limits the export to that module
    • Archive name honors EXPORT_COMPANY_NAME
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path("/app/scripts/export_human_readable.py")
PYTHON = sys.executable


# ─────────────────────────────────────────────────────────────────────────
# Fixture: build a synthetic technical-backup zip that mimics the layout
# produced by /app/backend/server.py::_build_complete_archive_on_disk.
# ─────────────────────────────────────────────────────────────────────────
def _make_fixture_backup(tmp: Path) -> Path:
    src = tmp / "fixture_src"
    src.mkdir()

    # daily_reports/json/<id>.json (the platform's canonical filename pattern)
    (src / "daily_reports" / "json").mkdir(parents=True)
    (src / "daily_reports" / "json" / "DR-001.json").write_text(json.dumps({
        "id": "DR-001",
        "report_date": "2026-02-10",
        "project_name": "Highway 50",
        "project_number": "1234",
        "prepared_by": "Joe Smith",
        "superintendent_name": "Jane Doe",
        "weather_summary": "Sunny",
        "high_temp_f": 78,
        "crew_count": 12,
        # Sensitive — must be redacted in module folder, preserved in RAW_JSON
        "api_token": "secret-token-value-AAA",
        "password_hash": "$2b$12$abcdefgh",
        "delays_or_issues": "None",
        "created_at": "2026-02-10T18:00:00Z",
    }, indent=2))

    # jhas
    (src / "jhas" / "json").mkdir(parents=True)
    (src / "jhas" / "json" / "JHA-001.json").write_text(json.dumps({
        "id": "JHA-001",
        "jha_date": "2026-02-11",
        "project_name": "Highway 50",
        "supervisor_name": "Bob Mason",
        "task_description": "Trench excavation 8 ft",
        "step_count": 5,
        "created_at": "2026-02-11T08:00:00Z",
    }, indent=2))

    # incidents
    (src / "incidents" / "json").mkdir(parents=True)
    (src / "incidents" / "json" / "INC-001.json").write_text(json.dumps({
        "id": "INC-001",
        "incident_date": "2026-02-12",
        "project_name": "Yard",
        "incident_type": "Near Miss",
        "severity": "Low",
        "description": "Equipment swung close to ground crew",
    }, indent=2))

    # field_leadership_records (HR)
    (src / "field_leadership_records" / "json").mkdir(parents=True)
    (src / "field_leadership_records" / "json" / "FL-001.json").write_text(json.dumps({
        "id": "FL-001",
        "record_date": "2026-02-09",
        "record_type": "Verbal Coaching",
        "employee_name": "Alex Operator",
        "supervisor": "Jane Doe",
        "notes": "Reminded about hard-hat policy on the yard.",
    }, indent=2))

    # admin_users (security-sensitive — must be SKIPPED from human-readable
    # but preserved in RAW_JSON/)
    (src / "admin_users" / "json").mkdir(parents=True)
    (src / "admin_users" / "json" / "ADM-001.json").write_text(json.dumps({
        "id": "ADM-001",
        "email": "admin@masci.example",
        "password_hash": "$2b$12$DO_NOT_LEAK",
    }, indent=2))

    # malformed record — must be SKIPPED gracefully, logged as WARN
    (src / "incidents" / "json" / "BAD.json").write_text("not valid json at all{{{")

    # unknown collection — must land in OTHER/ and be logged in verification
    (src / "future_unknown_collection" / "json").mkdir(parents=True)
    (src / "future_unknown_collection" / "json" / "X-1.json").write_text(json.dumps({
        "id": "X-1", "anything": "goes here",
    }))

    # photos
    photo_root = src / "photos" / "photos" / "2026" / "02" / "DR-001"
    photo_root.mkdir(parents=True)
    (photo_root / "abc123.jpg").write_bytes(b"\xff\xd8\xff\xe0FAKE-JPEG-DR-001")

    # an orphan photo (source-id doesn't match any record)
    orphan_root = src / "photos" / "photos" / "2026" / "02" / "ORPHAN-XYZ"
    orphan_root.mkdir(parents=True)
    (orphan_root / "lost.jpg").write_bytes(b"\xff\xd8\xff\xe0FAKE-JPEG-ORPHAN")

    # MANIFEST.json (the platform writes one at root)
    (src / "MANIFEST.json").write_text(json.dumps({
        "generated_at": "2026-02-15T03:00:00Z",
        "mode": "complete",
        "source": "fixture",
    }, indent=2))

    # Build the zip
    zip_path = tmp / "MASCI_complete_backup_FIXTURE.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in src.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(src))
    return zip_path


def _run(*args: str, env_extra: dict = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [PYTHON, str(SCRIPT), *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Fixture-based tests
# ═════════════════════════════════════════════════════════════════════════════
@pytest.fixture
def fixture_backup_and_out():
    tmp = Path(tempfile.mkdtemp(prefix="masci_export_test_"))
    try:
        zp = _make_fixture_backup(tmp)
        out = tmp / "out"
        out.mkdir()
        yield zp, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_exporter_runs_end_to_end(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0, f"stderr={r.stderr}\nstdout={r.stdout}"

    # locate the produced folder
    folders = [p for p in out.iterdir() if p.is_dir() and "HUMAN_READABLE_EXPORT" in p.name]
    assert len(folders) == 1, f"expected one export folder, got {folders}"
    exp = folders[0]
    assert exp.name.startswith("MASCI_HUMAN_READABLE_EXPORT_"), exp.name

    # canonical artefacts present
    assert (exp / "README_START_HERE.txt").exists()
    assert (exp / "MANIFEST.json").exists()
    assert (exp / "EXPORT_INDEX.csv").exists()
    assert (exp / "DATA_DICTIONARY.csv").exists()
    assert (exp / "SYSTEM" / "Verification_Report.txt").exists()
    assert (exp / "SYSTEM" / "Export_Errors.csv").exists()
    assert (exp / "SYSTEM" / "Backup_Info.txt").exists()


def test_csv_per_collection(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0
    exp = next(p for p in out.iterdir() if p.is_dir())
    # DAILY_REPORTS/CSV/daily_reports.csv
    csv_path = exp / "DAILY_REPORTS" / "CSV" / "daily_reports.csv"
    assert csv_path.exists(), f"missing: {csv_path}"
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["id"] == "DR-001"
    assert rows[0]["project_name"] == "Highway 50"


def test_sensitive_fields_redacted_in_module_folder(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0
    exp = next(p for p in out.iterdir() if p.is_dir())

    # The DR-001 JSON inside the module folder must NOT contain the token
    dr_dir = exp / "DAILY_REPORTS"
    found = list(dr_dir.rglob("DR-001*.json"))
    assert len(found) == 1, f"expected one DR-001 json under module folder, got {found}"
    text = found[0].read_text()
    assert "secret-token-value-AAA" not in text, "token leaked into module folder"
    assert "REDACTED" in text

    # The RAW_JSON mirror MUST still contain the original (it's for IT only)
    raw = exp / "RAW_JSON" / "daily_reports" / "DR-001.json"
    assert raw.exists(), f"missing raw mirror: {raw}"
    raw_text = raw.read_text()
    assert "secret-token-value-AAA" in raw_text, "raw mirror should keep originals"


def test_security_skipped_collection_not_in_module_folders(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0
    exp = next(p for p in out.iterdir() if p.is_dir())

    # admin_users must NOT appear under any module folder
    for module_dir in exp.iterdir():
        if module_dir.name in {"RAW_JSON", "SYSTEM", "PHOTOS_AND_ATTACHMENTS"}:
            continue
        if not module_dir.is_dir():
            continue
        for p in module_dir.rglob("*ADM-001*"):
            pytest.fail(f"admin_users leaked into module folder: {p}")

    # But it MUST be in RAW_JSON/
    raw = exp / "RAW_JSON" / "admin_users" / "ADM-001.json"
    assert raw.exists()


def test_photos_associated_and_orphans(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0
    exp = next(p for p in out.iterdir() if p.is_dir())

    # associated photo lands under PHOTOS_AND_ATTACHMENTS/Daily_Reports/DR-001/
    assoc = exp / "PHOTOS_AND_ATTACHMENTS" / "Daily_Reports" / "DR-001" / "abc123.jpg"
    assert assoc.exists(), f"missing associated photo: {assoc}"

    # orphan lands under ORPHANED_FILES/ with INDEX.csv
    orphan_idx = exp / "PHOTOS_AND_ATTACHMENTS" / "ORPHANED_FILES" / "INDEX.csv"
    assert orphan_idx.exists()
    with orphan_idx.open() as f:
        rows = list(csv.DictReader(f))
    assert any("ORPHAN" in r["source_id_guess"] for r in rows), rows


def test_bad_record_does_not_crash(fixture_backup_and_out):
    """The malformed BAD.json must NOT abort the export. Other records
    should still come through, and a WARN row should appear in
    Export_Errors.csv."""
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0, r.stderr
    exp = next(p for p in out.iterdir() if p.is_dir())
    err_csv = exp / "SYSTEM" / "Export_Errors.csv"
    with err_csv.open() as f:
        rows = list(csv.DictReader(f))
    assert any(row["where"] == "parse_json" and row["level"] == "WARN" for row in rows), rows


def test_unknown_collection_lands_in_other(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0
    exp = next(p for p in out.iterdir() if p.is_dir())
    other = exp / "OTHER"
    assert other.exists(), "OTHER/ folder must be created when an unmapped collection exists"
    # verification report must list it
    ver = (exp / "SYSTEM" / "Verification_Report.txt").read_text()
    assert "future_unknown_collection" in ver


def test_export_index_one_row_per_record(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip")
    assert r.returncode == 0
    exp = next(p for p in out.iterdir() if p.is_dir())
    idx = exp / "EXPORT_INDEX.csv"
    with idx.open() as f:
        rows = list(csv.DictReader(f))
    ids = {r["record_id"] for r in rows}
    # DR-001, JHA-001, INC-001, FL-001, X-1 — BAD.json skipped, ADM-001 skipped
    assert "DR-001" in ids
    assert "JHA-001" in ids
    assert "INC-001" in ids
    assert "FL-001" in ids
    assert "X-1" in ids
    assert "ADM-001" not in ids, "security-skipped collection leaked into index"


def test_dry_run_writes_no_records(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip", "--dry-run")
    assert r.returncode == 0, r.stderr
    exp = next(p for p in out.iterdir() if p.is_dir())
    # no records written into module folders
    dr_dir = exp / "DAILY_REPORTS"
    if dr_dir.exists():
        # Only empty subfolders allowed (the report generator may have made
        # the dir scaffolding). Ensure no JSON files leaked.
        for p in dr_dir.rglob("*.json"):
            pytest.fail(f"dry-run wrote record: {p}")


def test_module_filter(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip",
             "--modules", "SAFETY")
    assert r.returncode == 0, r.stderr
    exp = next(p for p in out.iterdir() if p.is_dir())
    # SAFETY records present
    assert any((exp / "SAFETY").rglob("*.json"))
    # DAILY_REPORTS records NOT written (filtered out)
    dr_dir = exp / "DAILY_REPORTS"
    if dr_dir.exists():
        for p in dr_dir.rglob("*.json"):
            pytest.fail(f"module filter failed — wrote: {p}")


def test_company_name_env_override(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out), "--no-zip",
             env_extra={"EXPORT_COMPANY_NAME": "ACME-CONSTRUCTION"})
    assert r.returncode == 0, r.stderr
    folders = list(out.iterdir())
    assert any(f.name.startswith("ACME-CONSTRUCTION_HUMAN_READABLE_EXPORT_") for f in folders), \
        f"got: {[f.name for f in folders]}"


def test_zip_mode(fixture_backup_and_out):
    zp, out = fixture_backup_and_out
    r = _run("--backup", str(zp), "--out", str(out))  # no --no-zip
    assert r.returncode == 0, r.stderr
    zips = list(out.glob("*.zip"))
    assert len(zips) == 1, f"expected one zip, got {zips}"
    # zip should contain the canonical artefacts
    with zipfile.ZipFile(zips[0], "r") as zf:
        names = zf.namelist()
    assert any(n.endswith("README_START_HERE.txt") for n in names)
    assert any(n.endswith("EXPORT_INDEX.csv") for n in names)


def test_from_source_folder(fixture_backup_and_out):
    """--from-source-folder accepts an already-extracted backup."""
    zp, out = fixture_backup_and_out
    extracted = out.parent / "extracted"
    extracted.mkdir()
    with zipfile.ZipFile(zp, "r") as zf:
        zf.extractall(extracted)
    r = _run("--from-source-folder", str(extracted), "--out", str(out), "--no-zip")
    assert r.returncode == 0, r.stderr
    exp = next(p for p in out.iterdir() if p.is_dir() and "HUMAN_READABLE" in p.name)
    assert (exp / "EXPORT_INDEX.csv").exists()


# ═════════════════════════════════════════════════════════════════════════════
# Optional — real R2 backup smoke test. Skipped by default.
# Run with: RUN_REAL_R2_TEST=1 pytest backend/tests/test_iter185_human_readable_export.py
# ═════════════════════════════════════════════════════════════════════════════
@pytest.mark.skipif(
    os.environ.get("RUN_REAL_R2_TEST", "") != "1",
    reason="set RUN_REAL_R2_TEST=1 to fetch the latest preview R2 backup",
)
def test_real_r2_backup_smoke(tmp_path):
    """Fetch the newest preview R2 backup, run the exporter against it,
    assert verification report says PASS."""
    import boto3
    from botocore.config import Config

    src = Path("/app/backend/.env")
    env = {}
    for line in src.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"')

    s3 = boto3.client(
        "s3",
        endpoint_url=env["S3_ENDPOINT_URL"],
        aws_access_key_id=env["S3_ACCESS_KEY"],
        aws_secret_access_key=env["S3_SECRET_KEY"],
        region_name=env.get("S3_REGION") or "auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    # Newest under backups/auto-90d/ if any, else newest backups/
    objs = []
    for prefix in ("backups/auto-90d/", "backups/"):
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=env["S3_BUCKET"], Prefix=prefix):
            for o in page.get("Contents", []):
                if o["Key"].endswith(".zip"):
                    objs.append(o)
        if objs:
            break
    assert objs, "no R2 backups available"
    objs.sort(key=lambda o: o["LastModified"], reverse=True)
    newest = objs[0]
    target = tmp_path / Path(newest["Key"]).name
    s3.download_file(env["S3_BUCKET"], newest["Key"], str(target))

    out = tmp_path / "out"
    out.mkdir()
    r = _run("--backup", str(target), "--out", str(out), "--no-zip")
    assert r.returncode == 0, r.stderr
    exp = next(p for p in out.iterdir() if p.is_dir() and "HUMAN_READABLE" in p.name)
    ver = (exp / "SYSTEM" / "Verification_Report.txt").read_text()
    assert "VERDICT: PASS" in ver, ver[-500:]

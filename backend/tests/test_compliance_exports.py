"""Compliance CSV Export — verifies summary counts + CSV download per kind."""
import io
import csv
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.conftest import URL  # noqa: E402


def _hdr():
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD", "Happy123!")},
        timeout=10,
    )
    return {"X-Admin-Token": r.json()["token"]}


def test_export_summary_returns_all_six_kinds():
    r = requests.get(f"{URL}/api/exports/summary", headers=_hdr(), timeout=10)
    assert r.status_code == 200
    body = r.json()
    expected = {
        "inspections",
        "meetings",
        "jhas",
        "incidents",
        "daily-reports",
        "equipment-inspections",
    }
    assert set(body["counts"].keys()) == expected
    assert body["total"] == sum(body["counts"].values())


def test_export_summary_with_date_range():
    r = requests.get(
        f"{URL}/api/exports/summary?start=2026-01-01&end=2026-12-31",
        headers=_hdr(),
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["start"] == "2026-01-01"
    assert body["end"] == "2026-12-31"


def test_export_csv_inspections_returns_csv():
    r = requests.get(
        f"{URL}/api/exports/csv?kind=inspections",
        headers=_hdr(),
        timeout=15,
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".csv" in cd
    # X-Record-Count header is set so the UI can show how many rows were exported
    assert "x-record-count" in {k.lower() for k in r.headers.keys()}

    # The body parses as valid CSV
    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    assert len(rows) >= 1  # at least the header
    header = rows[0]
    for required in ("inspection_date", "project_name", "inspector_name", "id"):
        assert required in header


def test_export_csv_unknown_kind_400s():
    r = requests.get(
        f"{URL}/api/exports/csv?kind=bogus",
        headers=_hdr(),
        timeout=10,
    )
    assert r.status_code == 400


def test_export_csv_each_kind_has_distinct_header():
    """Smoke-check every kind exports a CSV with at least its date column."""
    matrix = {
        "inspections": "inspection_date",
        "meetings": "meeting_date",
        "jhas": "jha_date",
        "incidents": "incident_date",
        "daily-reports": "report_date",
        "equipment-inspections": "inspection_date",
    }
    for kind, date_col in matrix.items():
        r = requests.get(
            f"{URL}/api/exports/csv?kind={kind}", headers=_hdr(), timeout=15
        )
        assert r.status_code == 200, f"{kind} failed: {r.status_code} {r.text[:200]}"
        rows = list(csv.reader(io.StringIO(r.text)))
        assert rows, f"{kind} returned empty body"
        assert date_col in rows[0], (
            f"{kind} header missing {date_col!r}: {rows[0]}"
        )


def test_export_csv_strips_photos_and_signatures():
    r = requests.get(
        f"{URL}/api/exports/csv?kind=inspections", headers=_hdr(), timeout=15
    )
    assert r.status_code == 200
    # Even if the projection didn't help, the CSV value flattener strips
    # data:image/* blobs — check no row contains a data URI
    assert "data:image/" not in r.text


# ---------------- Full backup .zip ----------------
import zipfile


def test_full_backup_returns_zip_with_required_structure():
    """End-to-end smoke for /api/exports/full-backup.

    The zip can be 500+ MB on a populated DB so we stream + retry on the
    flaky ChunkedEncodingError that can hit a long stream over an external
    proxy. Two retries, then bail.
    """
    last_err = None
    body = None
    headers = None
    for attempt in range(3):
        try:
            r = requests.get(
                f"{URL}/api/exports/full-backup",
                headers=_hdr(),
                timeout=180,
                stream=True,
            )
            assert r.status_code == 200, r.text[:300]
            # Drain via iter_content so we recover from intermittent reads
            chunks = []
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    chunks.append(chunk)
            body = b"".join(chunks)
            headers = r.headers
            break
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
        ) as e:
            last_err = e
            continue
    assert body is not None, f"all 3 attempts failed: {last_err}"
    assert "application/zip" in headers.get("content-type", "")
    cd = headers.get("content-disposition", "")
    assert "MASCI_full_backup_" in cd
    assert ".zip" in cd
    assert "x-record-count" in {k.lower() for k in headers.keys()}

    z = zipfile.ZipFile(io.BytesIO(body))
    names = z.namelist()

    # backup_log.txt must be present
    assert "backup_log.txt" in names
    log = z.read("backup_log.txt").decode()
    assert "MASCI Hub — Full Backup" in log
    assert "Per-kind record counts:" in log
    assert "Totals:" in log

    # /CSV/ folder has one CSV per kind
    csv_files = [n for n in names if n.startswith("CSV/")]
    assert len(csv_files) == 6
    for kind in (
        "inspections",
        "meetings",
        "jhas",
        "incidents",
        "daily-reports",
        "equipment-inspections",
    ):
        assert any(f"MASCI_{kind}_" in n for n in csv_files), (
            f"Missing CSV for {kind}: {csv_files}"
        )

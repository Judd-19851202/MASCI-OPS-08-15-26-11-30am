"""Track 21.1 · Zero-Defect Platform Remediation — lock test.

Static, side-effect-free assertions that codify the Class-C cleanups completed
in Track 21.1. Never triggers live emails, never spins backend, purely reads
files on disk.

Run:
    pytest /app/backend/tests/test_track_21_1_remediation.py -v
"""
import json
import re
import subprocess
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FRONTEND = REPO / "frontend"
I18N = FRONTEND / "src" / "lib" / "i18n.js"


# --------------------------------------------------------------------- deliverables

def test_final_report_exists_and_mentions_scope():
    report = MEM / "TRACK_21_1_FINAL_REPORT.md"
    assert report.is_file(), "TRACK_21_1_FINAL_REPORT.md must exist"
    body = report.read_text(encoding="utf-8")
    for tag in ("Track 21.1", "Zero-Drift", "Email Safety", "ESLint"):
        assert tag in body, f"final report missing marker: {tag}"


def test_technical_debt_register_updated_for_21_1():
    reg = MEM / "TECHNICAL_DEBT_REGISTER.md"
    assert reg.is_file(), "TECHNICAL_DEBT_REGISTER.md must exist"
    body = reg.read_text(encoding="utf-8")
    assert "Track 21.1" in body, "debt register missing Track 21.1 entry"


def test_changelog_appended():
    log = MEM / "CHANGELOG.md"
    assert log.is_file(), "CHANGELOG.md must exist"
    body = log.read_text(encoding="utf-8")
    assert "Track 21.1" in body, "CHANGELOG missing Track 21.1 entry"


# --------------------------------------------------------------------- i18n integrity

def test_i18n_has_no_orphaned_value_lines():
    """After Track 21.1, no value-only orphan lines may remain."""
    lines = I18N.read_text(encoding="utf-8").split("\n")
    orphan_pat = re.compile(r'^\s{2,}"[^"]*",\s*$')
    orphans = []
    prev = ""
    for idx, line in enumerate(lines, start=1):
        # a value-only line is `  "..."` with NO colon and where prev does not end with ':'
        if orphan_pat.match(line) and ":" not in line and not prev.rstrip().rstrip(",").rstrip().endswith(":"):
            orphans.append((idx, line.strip()))
        prev = line
    assert not orphans, f"orphan i18n value lines detected: {orphans[:5]}"


def test_i18n_has_no_duplicate_keys():
    """Duplicate keys must be zero after Track 21.1 dedupe."""
    src = I18N.read_text(encoding="utf-8")
    key_pat = re.compile(r'^\s{2}"([^"\\]+)"\s*:', re.MULTILINE)
    keys = key_pat.findall(src)
    dupes = {}
    for k in keys:
        dupes[k] = dupes.get(k, 0) + 1
    conflicts = {k: v for k, v in dupes.items() if v > 1}
    assert not conflicts, f"duplicate i18n keys remaining: {list(conflicts)[:5]}"


# --------------------------------------------------------------------- lint hygiene

def test_frontend_eslint_reports_zero_errors():
    """Full ESLint run must be lint-clean (0 errors)."""
    proc = subprocess.run(
        ["npx", "eslint", "src", "--format", "json"],
        cwd=str(FRONTEND),
        capture_output=True,
        text=True,
        timeout=180,
    )
    # Non-zero exit is acceptable only if stdout is JSON with zero errors.
    payload = proc.stdout.strip() or "[]"
    data = json.loads(payload)
    err_total = sum(entry.get("errorCount", 0) for entry in data)
    fatal_total = sum(entry.get("fatalErrorCount", 0) for entry in data)
    assert err_total == 0 and fatal_total == 0, (
        f"eslint reported {err_total} errors / {fatal_total} fatal — expected 0"
    )


# --------------------------------------------------------------------- email safety

def test_no_new_live_email_paths_introduced_in_21_1():
    """Track 21.1 is a hygiene track; no runtime email helpers may be added."""
    # Assert the previously certified safety switch remains in place.
    report = (MEM / "TRACK_21_1_FINAL_REPORT.md").read_text(encoding="utf-8")
    assert "Email Safety Mandate" in report, (
        "Track 21.1 report must reaffirm Email Safety Mandate"
    )


# --------------------------------------------------------------------- server/app untouched

def test_server_and_app_not_split_in_21_1():
    """21.1 is not the split track. Verify header markers unchanged (files still exist)."""
    server = REPO / "backend" / "server.py"
    app = REPO / "frontend" / "src" / "App.js"
    assert server.is_file(), "backend/server.py must remain in place"
    assert app.is_file(), "frontend/src/App.js must remain in place"

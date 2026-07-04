"""Track 20.9 · P1 Codebase Cleanup + Production Hardening — lock test.

Locks the additive, zero-drift-safe cleanups Track 20.9 made. No live
network. No email dispatch. Pure structural + source-level assertions.

Run:
    pytest /app/backend/tests/test_track_20_9_cleanup.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend"
BE = REPO / "backend"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


REQUIRED_DOCS = [
    "TRACK_20_9_EXECUTIVE_SUMMARY.md",
    "TRACK_20_9_CLEANUP_REPORT.md",
    "TRACK_20_9_DEPLOYMENT_CHECKLIST_UPDATE.md",
    "TRACK_20_9_README_RUNBOOK_REPORT.md",
    "TRACK_20_9_DEPENDENCY_FORMAT_REPORT.md",
    "TRACK_20_9_GITIGNORE_SECURITY_REPORT.md",
    "TRACK_20_9_SERVER_APP_SPLIT_PLAN.md",
    "TRACK_20_9_ZERO_DRIFT_MATRIX.md",
    "TRACK_20_9_TEST_REPORT.md",
]


# ── Deliverables ────────────────────────────────────────────────────

def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.9 deliverables: {missing}"


# ── Class-A runtime bugs fixed ──────────────────────────────────────

def test_td_20_9_a01_restore_row_defined():
    """MasterListPanel.jsx must define restoreRow — TD-20.9-A01 was
    the pre-Track-20.9 crash on the archive-tab restore button."""
    src = _read(FE / "src/components/MasterListPanel.jsx")
    # Must have BOTH: the call site (unchanged) and the definition (added).
    assert "restoreRow(row)" in src, "call site removed?"
    assert "const restoreRow = async (row)" in src or \
           "async function restoreRow" in src, (
        "restoreRow definition missing — TD-20.9-A01 regressed"
    )


def test_td_20_9_a02_branding_hook_called():
    """TrenchBoxPosterCard.jsx must call useBranding — TD-20.9-A02 was
    the pre-Track-20.9 crash on every render."""
    src = _read(FE / "src/components/TrenchBoxPosterCard.jsx")
    assert "useBranding" in src, "useBranding import removed?"
    assert "const branding = useBranding();" in src, (
        "useBranding never called — TD-20.9-A02 regressed"
    )


# ── Frontend lint gate is real ──────────────────────────────────────

def test_eslint_config_exists():
    p = FE / "eslint.config.js"
    assert p.exists(), "Track 20.9 real ESLint config missing"


def test_eslint_config_targets_src():
    src = _read(FE / "eslint.config.js")
    assert 'files: ["src/**' in src, "eslint.config.js must target src/"
    # Critical rules present (must catch real bugs, not just cosmetic).
    for rule in ('"no-undef": "error"',
                 '"no-unreachable": "error"',
                 '"no-dupe-keys": "error"',
                 '"react-hooks/rules-of-hooks": "error"'):
        assert rule in src, f"missing critical rule in eslint.config.js: {rule}"


def test_frontend_lint_script_is_real():
    """package.json must invoke real ESLint, NOT the pre-Track-20.9 stub."""
    src = _read(FE / "package.json")
    assert '"lint": "eslint src"' in src, (
        "lint script must invoke real eslint (Track 20.9 requirement)"
    )
    # The old stub message must be gone.
    assert "gate stage 3 (raw eslint v9)" not in src, (
        "pre-Track-20.9 lint stub message must be removed"
    )


# ── Deployment checklist upgraded ───────────────────────────────────

def test_deployment_checklist_at_track_20_9_standard():
    src = _read(REPO / "DEPLOYMENT_CHECKLIST.md")
    assert "Track 20.9" in src, "DEPLOYMENT_CHECKLIST.md must be marked Track 20.9"
    # New sections must be present.
    for needle in ("Email-Safety Certification",
                   "Photo Capture Smoke",
                   "Operational Threads Smoke",
                   "Post-deploy monitoring",
                   "synthetic-test-record",
                   "TEST_"):
        assert needle in src, f"DEPLOYMENT_CHECKLIST.md missing: {needle}"


# ── README is a real runbook ────────────────────────────────────────

def test_readme_is_real_runbook():
    src = _read(REPO / "README.md")
    # Pre-Track-20.9 boilerplate must be gone.
    assert src.strip() != "# Here are your Instructions", (
        "README.md still shows the pre-Track-20.9 scaffold boilerplate"
    )
    # Core runbook sections must exist.
    for needle in ("Architecture at a glance",
                   "Boot the platform locally",
                   "Run the tests",
                   "Frontend lint",
                   "Deploy",
                   "Rollback",
                   "Environment variables",
                   "Health checks",
                   "Email-safety rule",
                   "Track discipline",
                   "TEST_"):
        assert needle in src, f"README.md missing runbook section: {needle}"


# ── Requirements format ─────────────────────────────────────────────

def test_requirements_one_dep_per_line():
    src = _read(BE / "requirements.txt")
    lines = [ln for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    for ln in lines:
        # No whitespace-separated multi-dep lines
        assert " " not in ln.strip() or "@" in ln, (
            f"multi-dep line in requirements.txt: {ln!r}"
        )
    # File is non-trivial (sanity: > 100 real deps)
    assert len(lines) > 100, f"requirements.txt suspiciously short: {len(lines)} deps"


# ── .gitignore cleanup + secret protections ────────────────────────

def test_gitignore_cleaned_up():
    src = _read(REPO / ".gitignore")
    # Track 20.9 header lock
    assert "Track 20.9" in src, ".gitignore must carry Track 20.9 lock header"
    # Must be well under the pre-Track-20.9 862-line explosion
    line_count = src.count("\n")
    assert line_count < 300, (
        f".gitignore is {line_count} lines — cleanup regressed"
    )


def test_gitignore_preserves_secret_protections():
    src = _read(REPO / ".gitignore")
    # Every historical secret protection MUST remain
    for pattern in (".env", ".env.*", "*.env",
                    "credentials.json", "*.pem", "*.key",
                    ".credentials", ".secrets/",
                    "memory/test_credentials.md",
                    "*.env.template",
                    "*_SECRETS_*.env*",
                    "*SEALED*.env*",
                    "secrets.env*"):
        # match as a whole line
        assert any(ln.strip() == pattern for ln in src.splitlines()), (
            f"secret protection missing from .gitignore: {pattern!r}"
        )


def test_no_real_secrets_committed():
    """git ls-files must not surface any real .env / credentials / pem."""
    import subprocess
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=str(REPO), text=True
    ).splitlines()
    suspicious = [
        f for f in out
        if any(pat in f.lower() for pat in
               (".env", "credentials.json", ".pem", ".key", "sealed", "_secrets_"))
    ]
    # The only allowable hit is the secret-scanner test file itself.
    disallowed = [f for f in suspicious
                  if "test_track_15_80_no_secrets_in_repo.py" not in f]
    assert not disallowed, (
        f"real secret-like files tracked in git: {disallowed}"
    )


# ── Zero-drift · Track 20.6B email gate untouched ──────────────────

def test_track_20_6b_email_gate_still_present():
    """Track 20.9 must NOT touch the Track 20.6B synthetic-test-record
    short-circuit in _dispatch_auto_email."""
    src = _read(BE / "server.py")
    fn_idx = src.find("async def _dispatch_auto_email")
    assert fn_idx != -1
    body = src[fn_idx: fn_idx + 8000]
    assert 'startswith("TEST_")' in body
    assert '"synthetic_test_record"' in body
    assert 'status="skipped"' in body


# ── Zero-drift · Track 20.7 photo fallback untouched ───────────────

def test_track_20_7_photo_fallback_still_present():
    src = _read(FE / "src/components/PhotoUpload.jsx")
    assert "useCameraSupport" in src
    assert "cameraKnownUnsupported" in src
    assert "Camera unavailable" in src


# ── Class-C debt registered ────────────────────────────────────────

def test_class_c_debt_registered():
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    for did in ("TD-20.9-A01", "TD-20.9-A02", "TD-20.9-C01"):
        assert did in src, f"Track 20.9 debt entry missing: {did}"


# ── PRD + CHANGELOG updated ────────────────────────────────────────

def test_prd_updated():
    assert "TRACK 20.9" in _read(MEM / "PRD.md")


def test_changelog_updated():
    assert "TRACK 20.9" in _read(MEM / "CHANGELOG.md")


# ── Prior track deliverables preserved ─────────────────────────────

def test_prior_tracks_preserved():
    for name in ("TRACK_20_8_EXECUTIVE_DEPLOYMENT_REPORT.md",
                 "TRACK_20_7_EXECUTIVE_SUMMARY.md",
                 "TRACK_20_6B_EXECUTIVE_SUMMARY.md",
                 "TECHNICAL_DEBT_REGISTER.md"):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"

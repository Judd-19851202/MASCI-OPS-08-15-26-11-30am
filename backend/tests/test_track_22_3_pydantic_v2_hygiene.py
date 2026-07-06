"""Track 22.3 · Pydantic v2 hygiene sweep — lock test.

Enforces:
  1. Zero `regex=` in Pydantic Query/Path/Body/Field/constr contexts anywhere in backend.
  2. No global `filterwarnings` suppression added.
  3. Starlette CORS `allow_origin_regex=` preserved (allow-listed).
  4. Runtime parity: routes / methods / OpenAPI unchanged.
  5. Lifecycle safety: `lifecycle_complete=true`, 9/9 bytecode clean.
  6. Email safety: strict.
"""
from __future__ import annotations
import ast
import os
import sys
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_3"

DELIVERABLES = [
    "TRACK_22_3_EXECUTIVE_SUMMARY.md",
    "TRACK_22_3_WARNING_INVENTORY.md",
    "TRACK_22_3_OPENAPI_VALIDATION_PARITY.md",
    "TRACK_22_3_WARNING_REDUCTION.md",
    "TRACK_22_3_ENGINEERING_AUDIT.md",
    "TRACK_22_3_SAFETY_RECERTIFICATION.md",
    "TRACK_22_3_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_3_TEST_REPORT.md",
]

# Callable names that accept a Pydantic-style `regex=` kwarg. `allow_origin_regex`
# is Starlette CORS and MUST be preserved verbatim.
_PYDANTIC_KWARG_CARRIERS = {"Query", "Path", "Body", "Field", "Form", "Header", "Cookie", "constr"}


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def _iter_pydantic_regex_kwargs():
    """Yield (file, lineno, callable) tuples for every `regex=...` kwarg
    passed to a Pydantic-style parameter carrier (Query/Path/Body/Field/etc.)."""
    for py in BACKEND.rglob("*.py"):
        if "test_track" in py.name:
            continue
        try:
            src = py.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(py))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            else:
                continue
            if name not in _PYDANTIC_KWARG_CARRIERS:
                continue
            for kw in node.keywords or []:
                if kw.arg == "regex":
                    yield f"{py.relative_to(APP)}:{kw.lineno}:{name}"


def test_zero_pydantic_regex_kwarg_anywhere_in_backend():
    """PERMANENT · fails CI if any new `regex=` is passed to Query/Path/Body/Field/etc."""
    offenders = list(_iter_pydantic_regex_kwargs())
    assert not offenders, (
        f"ZERO-`regex=` RULE VIOLATED — Pydantic v1 `regex=` kwarg detected in:\n  "
        + "\n  ".join(offenders)
        + "\nUse `pattern=` instead."
    )


def test_starlette_allow_origin_regex_preserved():
    """The CORS Starlette parameter `allow_origin_regex=` MUST remain."""
    server_src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "allow_origin_regex=" in server_src, (
        "Starlette CORS `allow_origin_regex=` was removed — this would break CORS."
    )


def test_no_pydantic_regex_warning_filter_added():
    """No global `warnings.filterwarnings(...)` for the `regex=` DeprecationWarning."""
    banned_patterns = ("filterwarnings.*regex", "filterwarnings.*Pydantic")
    import re  # noqa: PLC0415
    banned_re = re.compile("|".join(banned_patterns), re.IGNORECASE)
    for py in BACKEND.rglob("*.py"):
        if "test_track" in py.name:
            continue
        src = py.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(src.splitlines(), start=1):
            if banned_re.search(line) and "regex" in line.lower():
                # Allow-list: comments / docstrings that mention the pattern
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"'):
                    continue
                raise AssertionError(
                    f"forbidden warning suppression detected: {py.relative_to(APP)}:{line_no}: {line}"
                )


def test_route_and_openapi_parity():
    server = _load_server()
    route_count = sum(1 for r in server.app.routes if hasattr(r, "endpoint"))
    # TRACK 22.5-RERUN re-lock (2026-02): baseline bumped after
    # legitimate route additions in tracks 22.4b/22.4b-followup family
    # (idempotency wrappers on Trench/Shop/Driver/HR), 22.4c (mobile
    # gate endpoints), 22.4d (session-status telemetry probes),
    # 22.5A (governance/audit shell readers), and TRACK 22.6A
    # (production certification session control plane · 4 endpoints).
    # Each set of new routes has its own dedicated regression suite;
    # this counter locks the aggregate at the pre-deploy baseline.
    assert route_count == 1499, f"route drift: {route_count}"
    methods = 0
    for r in server.app.routes:
        if hasattr(r, "endpoint"):
            methods += len(getattr(r, "methods", None) or [])
    assert methods == 1503, f"method drift: {methods}"
    oa = len(server.app.openapi().get("paths", {}))
    assert oa == 1320, f"openapi drift: {oa}"


def test_lifecycle_complete_unchanged():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    mig = out["lifecycle"]["migration_progress"]
    assert mig["lifecycle_complete"] is True
    assert mig["startup_migration_pct"] == 100.0
    assert mig["shutdown_migration_pct"] == 100.0
    assert mig["on_startup_legacy_count"] == 0
    assert mig["on_shutdown_legacy_count"] == 0


def test_bytecode_fingerprints_still_clean():
    server = _load_server()
    from lib.scheduler_bootstrap import verify_locked_bytecode
    result = verify_locked_bytecode(server.app)
    assert result["drift"] == []
    assert result["missing"] == []
    assert result["checked"] >= 9


def test_email_safety_strict_mode_intact():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["resend_sdk_patched"] is True
    assert out["email_safety"]["live_emails_possible"] is False


def test_targeted_files_now_use_pattern():
    """The 8 touched files must all contain `pattern=` and NO `regex=` in Pydantic contexts."""
    touched = [
        "routes/operations_map_contract.py",
        "routes/operational_events.py",
        "routes/verification.py",
        "routes/operational_locations.py",
        "routes/asset_mapping_recon.py",
        "routes/sprint_a.py",
        "routes/integrations/autolink.py",
        "routes/equipment_detection.py",
    ]
    for rel in touched:
        src = (BACKEND / rel).read_text(encoding="utf-8")
        # There should be no `regex=r?"..."` in a Pydantic Query/Path context;
        # broadly assert no `, regex=` on the file (comments/docstrings won't have this pattern).
        # If a legitimate non-Pydantic `regex=` usage exists in a touched file we
        # would need a stricter AST check — but grep for `, regex=` covers the cases here.
        assert ", regex=" not in src, (
            f"`, regex=` still present in {rel} — the mechanical fix missed a spot"
        )


def test_snapshot_artifacts_committed():
    for name in (
        "PYDANTIC_WARNING_INVENTORY_before.json",
        "PYDANTIC_WARNING_INVENTORY_after.json",
    ):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 200, f"missing/empty snapshot: {name}"


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 100]
    assert not missing, f"missing/empty: {missing}"


def test_prd_and_changelog_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    assert "22.3" in prd
    assert "22.3" in changelog
    assert "pattern" in prd.lower() or "regex" in prd.lower()

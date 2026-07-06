"""Track 22.4A · Pydantic V2 completion — lock test.

Enforces:
  1. Zero Pydantic V1 `class Config` under a BaseModel subclass anywhere in backend.
  2. Zero deprecated V1 kwargs: `schema_extra`, `json_encoders`.
  3. Zero deprecated V1 decorators: `@validator`, `@root_validator`.
  4. No global `filterwarnings` suppression added for Pydantic deprecations.
  5. Runtime parity: routes / methods / OpenAPI unchanged.
  6. Lifecycle safety: `lifecycle_complete=true`, 9/9 bytecode clean.
  7. Email safety: strict.
  8. `class Config` DeprecationWarning eliminated at runtime.
"""
from __future__ import annotations
import ast
import os
import sys
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_4a"

DELIVERABLES = [
    "TRACK_22_4A_EXECUTIVE_SUMMARY.md",
    "TRACK_22_4A_PYDANTIC_V2_INVENTORY.md",
    "TRACK_22_4A_ZERO_DRIFT_MATRIX.md",
    "TRACK_22_4A_TEST_REPORT.md",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def _iter_python_files():
    for py in BACKEND.rglob("*.py"):
        if "test_track" in py.name:
            continue
        yield py


def _pydantic_basemodel_classes(tree: ast.AST):
    """Yield ClassDef nodes that subclass BaseModel (heuristic: any base
    named 'BaseModel' or ending in 'BaseModel' or 'BaseDocument')."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)
        if any(b == "BaseModel" or b.endswith("BaseModel") or b == "BaseDocument" for b in bases):
            yield node


def test_zero_pydantic_v1_class_config_in_backend():
    """PERMANENT · fails CI if any Pydantic BaseModel subclass declares a nested `class Config`."""
    offenders = []
    for py in _iter_python_files():
        try:
            src = py.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(py))
        except Exception:
            continue
        for cls in _pydantic_basemodel_classes(tree):
            for child in cls.body:
                if isinstance(child, ast.ClassDef) and child.name == "Config":
                    offenders.append(f"{py.relative_to(APP)}:{child.lineno}:{cls.name}.Config")
    assert not offenders, (
        "PYDANTIC-V1 `class Config` RULE VIOLATED — use `model_config = ConfigDict(...)`:\n  "
        + "\n  ".join(offenders)
    )


def test_zero_pydantic_v1_deprecated_kwargs():
    """No `schema_extra=` and no `json_encoders=` kwargs in Pydantic BaseModel bodies."""
    banned = {"schema_extra", "json_encoders"}
    offenders = []
    for py in _iter_python_files():
        try:
            src = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(src.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for kw in banned:
                if f"{kw}=" in line or f"{kw} =" in line or f'"{kw}"' in line:
                    offenders.append(f"{py.relative_to(APP)}:{i}:{kw}")
    assert not offenders, (
        "PYDANTIC-V1 deprecated kwargs detected:\n  " + "\n  ".join(offenders)
    )


def test_zero_pydantic_v1_validator_decorators():
    """No `@validator(...)` or `@root_validator(...)` — use `@field_validator` / `@model_validator`."""
    offenders = []
    for py in _iter_python_files():
        try:
            src = py.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(py))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for dec in node.decorator_list:
                fn = dec.func if isinstance(dec, ast.Call) else dec
                name = None
                if isinstance(fn, ast.Name):
                    name = fn.id
                elif isinstance(fn, ast.Attribute):
                    name = fn.attr
                if name in {"validator", "root_validator"}:
                    offenders.append(f"{py.relative_to(APP)}:{dec.lineno}:@{name}")
    assert not offenders, (
        "PYDANTIC-V1 validator decorator detected — use `@field_validator` / `@model_validator`:\n  "
        + "\n  ".join(offenders)
    )


def test_no_pydantic_v2_warning_filter_added():
    """No new `filterwarnings` suppression for Pydantic deprecations."""
    import re  # noqa: PLC0415
    banned_re = re.compile(r"filterwarnings.*(pydantic|deprecat|config)", re.IGNORECASE)
    for py in _iter_python_files():
        src = py.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(src.splitlines(), start=1):
            if banned_re.search(line):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"'):
                    continue
                raise AssertionError(
                    f"forbidden warning suppression detected: {py.relative_to(APP)}:{line_no}: {line.strip()}"
                )


def test_route_and_openapi_parity():
    server = _load_server()
    route_count = sum(1 for r in server.app.routes if hasattr(r, "endpoint"))
    # TRACK 22.5-RERUN re-lock (2026-02): baseline bumped after
    # legitimate route additions in tracks 22.4b/22.4b-followup family
    # (idempotency wrappers on Trench/Shop/Driver/HR), 22.4c (mobile
    # gate endpoints), 22.4d (session-status telemetry probes), and
    # 22.5A (governance/audit shell readers). Each set of new routes
    # has its own dedicated regression suite; this counter locks the
    # aggregate at the pre-deploy baseline for Track 22.5.
    assert route_count == 1495, f"route drift: {route_count}"
    methods = 0
    for r in server.app.routes:
        if hasattr(r, "endpoint"):
            methods += len(getattr(r, "methods", None) or [])
    assert methods == 1499, f"method drift: {methods}"
    oa = len(server.app.openapi().get("paths", {}))
    assert oa == 1316, f"openapi drift: {oa}"


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


def test_passkeys_generic_payload_uses_configdict():
    """Explicit check on the file we touched: passkeys.py must use model_config = ConfigDict."""
    src = (BACKEND / "routes" / "passkeys.py").read_text(encoding="utf-8")
    assert "model_config = ConfigDict(" in src, (
        "passkeys.py GenericPayload must declare `model_config = ConfigDict(...)`"
    )
    assert "class Config" not in src or "# " in src, (
        "passkeys.py must not contain a live `class Config` declaration"
    )
    # Strict: raw pattern must be gone
    assert "class Config:" not in src, "passkeys.py still contains `class Config:`"


def test_runtime_no_pydantic_class_config_deprecation():
    """Import passkeys module and confirm no PydanticDeprecatedSince20 fires from GenericPayload."""
    import warnings  # noqa: PLC0415
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    sys.path.insert(0, str(BACKEND))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Re-import passkeys.py fresh
        if "routes.passkeys" in sys.modules:
            del sys.modules["routes.passkeys"]
        import importlib  # noqa: PLC0415
        importlib.import_module("routes.passkeys")
    pydantic_warnings = [
        str(x.message) for x in w
        if "PydanticDeprecatedSince" in x.category.__name__
        and ("class-based `config`" in str(x.message).lower() or "class Config" in str(x.message))
    ]
    assert not pydantic_warnings, (
        f"Pydantic class Config DeprecationWarning still fires: {pydantic_warnings}"
    )


def test_all_deliverables_present():
    missing = [n for n in DELIVERABLES if not (MEM / n).is_file() or (MEM / n).stat().st_size < 100]
    assert not missing, f"missing/empty: {missing}"


def test_prd_and_changelog_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    assert "22.4A" in prd
    assert "22.4A" in changelog
    assert "ConfigDict" in prd or "model_config" in prd

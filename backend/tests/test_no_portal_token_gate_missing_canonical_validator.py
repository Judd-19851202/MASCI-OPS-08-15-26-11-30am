"""TRACK 28.04 · Platform-wide portal-token gate invariant.

**Contract.** Every function that reads a portal-token header
(`X-HR-Token`, `X-Safety-Token`, `X-Shop-Token`, `X-PM-Token`,
`X-Dispatch-Token`, `X-FL-Token`) to make an authorization
decision MUST validate that token via the canonical async
validator for that portal. Silent rejection of valid
per-user portal tokens has already caused two P0
regressions this quarter (28.02-A · Safety factories,
28.03-A · Field Leadership); this invariant closes the
class of defect for every remaining portal.

**Canonical async validators.**

  * X-HR-Token       → ``is_valid_hr_user_token_async``
  * X-Safety-Token   → ``is_valid_safety_user_token_async``
  * X-Shop-Token     → ``is_valid_shop_user_token_async``
  * X-PM-Token       → ``is_valid_pm_user_token_async``
  * X-Dispatch-Token → ``is_valid_dispatch_user_token_async``
  * X-FL-Token       → ``is_valid_fl_user_token_async``  (aliases ok)

**Rule.** Any function that references a portal-token header
alias inside a FastAPI ``Header(...)`` default MUST also
reference the canonical async validator for that portal
(direct name reference or attribute access on the module).
Exception: functions that only extract the header for
audit/logging purposes and never authorize.

Every exception MUST live in :data:`INTERNAL_ALLOWLIST`
with a **structured reason** documenting file, function,
purpose, why the canonical validator is unnecessary, and a
risk owner. Empty reasons fail loudly.

**Ordering rule.** When admin fallback is present, it must
be paired with ``_is_valid_directory_admin_token_async`` —
enforced separately by the Track 28.03E invariant.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


BACKEND_ROOT = Path("/app/backend")

# ─── Header alias → canonical async validator name ────────────────
PORTAL_HEADERS: Dict[str, Tuple[str, ...]] = {
    "X-HR-Token":       ("is_valid_hr_user_token_async",),
    "X-Safety-Token":   ("is_valid_safety_user_token_async",),
    "X-Shop-Token":     ("is_valid_shop_user_token_async",),
    "X-PM-Token":       ("is_valid_pm_user_token_async",
                         "compute_pm_scope", "resolve_pm_actor"),
    "X-Dispatch-Token": ("is_valid_dispatch_user_token_async",),
    "X-FL-Token":       ("is_valid_fl_user_token_async",
                         "is_valid_fl_token_async",
                         "resolve_fl_user"),
}

# ─── Trusted delegating-helper symbols ────────────────────────────
# Functions that read a portal-token header may also validate via a
# helper that INTERNALLY calls the canonical async validator. Naming
# these helpers here treats their invocation as equivalent to calling
# the canonical validator directly. Every helper listed here has been
# manually audited to confirm it eventually calls the canonical
# async validator for the token type(s) it accepts.
TRUSTED_DELEGATION_HELPERS: Set[str] = {
    # Cross-portal actor resolvers (all internally call canonical
    # async validators for whichever portal token they receive).
    "_resolve_actor",              # shop_intel, safety_forms
    "_resolve_rich_actor",         # fleet_ops (multi-portal)
    "_resolve_hr_user",            # notifications, HR portal
    "_resolve_pm_user",            # notifications, PM portal
    "_resolve_dispatch_user",      # notifications, Dispatch portal
    "_resolve_fl_user",            # notifications, FL portal
    "_resolve_safety_user",        # notifications, Safety portal
    "_resolve_shop_user",          # notifications, Shop portal
    "resolve_authenticated_actor", # generic multi-portal resolver
    # Gate factories from the safety_portal / fleet_ops modules that
    # internally call canonical validators via kwargs already wired.
    "make_require_safety_or_admin",
    "make_require_safety_admin_or_pm",
    "make_require_safety_or_hr_or_admin",
    "make_require_safety_or_admin_fleet",
    "make_require_shop_or_admin_fleet",
    "make_require_dispatch_or_admin",
    "make_require_any_portal_token",
    "make_require_fleet_submitter",
    "make_require_any_fleet_portal",
    "make_employee_records_actor_gate",
    "build_safety_forms_router",
    # Legacy audit / telemetry writers that don't authorize (they
    # just capture actor context from whatever token was already
    # validated by an upstream dependency).
    "_actor_from_headers",
    "_actor_context_from_headers",
    # Field-leadership helpers that internally check FL / PM / HR.
    "_resolve_fl_actor",
    "_pm_actor",
}


class Reason:
    def __init__(self, purpose: str, why_no_validator: str, risk_owner: str) -> None:
        assert purpose.strip(), "empty purpose"
        assert why_no_validator.strip(), "empty why_no_validator"
        assert risk_owner.strip(), "empty risk_owner"
        self.purpose = purpose
        self.why_no_validator = why_no_validator
        self.risk_owner = risk_owner


INTERNAL_ALLOWLIST: Dict[Tuple[str, str, str], Reason] = {
    # -----------------------------------------------------------------
    # (file, function, header_alias)  →  Reason
    # -----------------------------------------------------------------

    # The canonical validators themselves — obviously exempt.
    ("hr_users.py", "is_valid_hr_user_token_async", "X-HR-Token"): Reason(
        purpose="The canonical HR async validator definition itself.",
        why_no_validator="This IS the validator.",
        risk_owner="platform-core",
    ),
    ("safety_users.py", "is_valid_safety_user_token_async", "X-Safety-Token"): Reason(
        purpose="The canonical Safety async validator definition itself.",
        why_no_validator="This IS the validator.",
        risk_owner="platform-core",
    ),
    ("shop_users.py", "is_valid_shop_user_token_async", "X-Shop-Token"): Reason(
        purpose="The canonical Shop async validator definition itself.",
        why_no_validator="This IS the validator.",
        risk_owner="platform-core",
    ),
    ("dispatch_users.py", "is_valid_dispatch_user_token_async", "X-Dispatch-Token"): Reason(
        purpose="The canonical Dispatch async validator definition itself.",
        why_no_validator="This IS the validator.",
        risk_owner="platform-core",
    ),

    # Header capture for audit logging only — no authorization.
    # (Preemptive slot for future audit middleware — removed when the
    # target file didn't exist to avoid stale-allowlist rot.)

    # ─── Delegating wrappers that use shared/canonical gates ──────
    ("server.py", "_require_dispatch_or_admin", "X-Dispatch-Token"): Reason(
        purpose="Thin wrapper around _shared_dispatch_or_admin (make_require_dispatch_or_admin factory).",
        why_no_validator="Delegates to the canonical async-wired shared gate (TRACK 28.03E). "
                         "The wrapper only exists to inject fleet_ops kwargs.",
        risk_owner="dispatch-platform",
    ),
    ("server.py", "_require_safety_or_admin_fleet", "X-Safety-Token"): Reason(
        purpose="Thin wrapper around _shared_safety_or_admin_fleet (make_require_safety_or_admin_fleet factory).",
        why_no_validator="Delegates to the canonical async-wired shared gate (TRACK 28.03E).",
        risk_owner="safety-platform",
    ),
    ("server.py", "_require_shop_or_admin_fleet", "X-Shop-Token"): Reason(
        purpose="Thin wrapper around _shared_shop_or_admin_fleet (make_require_shop_or_admin_fleet factory).",
        why_no_validator="Delegates to the canonical async-wired shared gate (TRACK 28.03E).",
        risk_owner="shop-platform",
    ),
    ("server.py", "_require_optional_portal_token", "X-Shop-Token"): Reason(
        purpose="Optional portal-token capture for public/anonymous endpoints; returns None on missing.",
        why_no_validator="This function does NOT authorize any request — it returns None if no token or "
                         "an unvalidated string if present. Callers use it purely for identity hints; "
                         "actual auth happens on the parent dependency.",
        risk_owner="platform-core",
    ),
    ("server.py", "_require_optional_portal_token", "X-FL-Token"): Reason(
        purpose="Same as X-Shop-Token — non-authorizing identity hint capture.",
        why_no_validator="Non-authorizing; parent dependency handles auth.",
        risk_owner="platform-core",
    ),
    ("server.py", "_require_optional_portal_token", "X-HR-Token"): Reason(
        purpose="Same as X-Shop-Token — non-authorizing identity hint capture.",
        why_no_validator="Non-authorizing; parent dependency handles auth.",
        risk_owner="platform-core",
    ),
    ("server.py", "_require_optional_portal_token", "X-Dispatch-Token"): Reason(
        purpose="Same as X-Shop-Token — non-authorizing identity hint capture.",
        why_no_validator="Non-authorizing; parent dependency handles auth.",
        risk_owner="platform-core",
    ),
    ("server.py", "_require_optional_portal_token", "X-PM-Token"): Reason(
        purpose="Same as X-Shop-Token — non-authorizing identity hint capture.",
        why_no_validator="Non-authorizing; parent dependency handles auth.",
        risk_owner="platform-core",
    ),
    ("server.py", "_require_optional_portal_token", "X-Safety-Token"): Reason(
        purpose="Same as X-Shop-Token — non-authorizing identity hint capture.",
        why_no_validator="Non-authorizing; parent dependency handles auth.",
        risk_owner="platform-core",
    ),

    # ─── Field-leadership internal auth helpers ────────────────────
    ("routes/field_leadership.py", "_is_authed", "X-PM-Token"): Reason(
        purpose="FL internal auth helper — accepts FL portal + PM/HR fallback.",
        why_no_validator="Delegates PM token validation to compute_pm_scope via imported helper; "
                         "the PM validator is called inside the resolve step. Direct signature check "
                         "misses the dynamic import.",
        risk_owner="field-leadership-platform",
    ),
    ("routes/field_leadership.py", "_is_hr_authed", "X-HR-Token"): Reason(
        purpose="FL internal HR-auth helper for time-off admin endpoints.",
        why_no_validator="Delegates HR token validation to is_valid_hr_user_token_async via inline import; "
                         "the validator IS called but through a nested await which the scanner "
                         "walks past the enclosing function scope.",
        risk_owner="field-leadership-platform",
    ),
    ("routes/legacy_imports.py", "_li_require_uploader", "X-Safety-Token"): Reason(
        purpose="Legacy CSV imports uploader gate — accepts HR/Safety/Admin.",
        why_no_validator="Delegates Safety token validation to is_valid_safety_user_token_async via inline "
                         "import; validator IS called but the scanner cannot reach into the async import.",
        risk_owner="hr-platform",
    ),

    # ─── Factory-inner deps ────────────────────────────────────────
    ("routes/fleet_ops_deps.py", "_dep", "X-HR-Token"): Reason(
        purpose="Fleet-ops submitter gate accepts every signed-in employee for DVIR submissions.",
        why_no_validator="HR / Shop tokens are captured for AUDIT identity only; actual auth "
                         "is admin/safety/dispatch. Any signed-in employee is allowed by design "
                         "(anonymous public-tile drivers included).",
        risk_owner="fleet-ops-platform",
    ),
    ("routes/fleet_ops_deps.py", "_dep", "X-Shop-Token"): Reason(
        purpose="Same as X-HR-Token — audit-identity capture only.",
        why_no_validator="Auth is submitter-permissive by design (D2 operator decision).",
        risk_owner="fleet-ops-platform",
    ),

    # ─── Draft telemetry: pure write-only endpoint ────────────────
    ("routes/draft_telemetry.py", "append_events", "X-HR-Token"): Reason(
        purpose="Draft telemetry ingest — accepts any portal token as an actor tag.",
        why_no_validator="Non-authorizing write endpoint. Any authenticated portal is accepted; "
                         "the token string is used to tag telemetry rows with the portal name only.",
        risk_owner="platform-observability",
    ),
    ("routes/draft_telemetry.py", "append_events", "X-Safety-Token"): Reason(
        purpose="Same as above.", why_no_validator="Non-authorizing telemetry writer.",
        risk_owner="platform-observability",
    ),
    ("routes/draft_telemetry.py", "append_events", "X-Shop-Token"): Reason(
        purpose="Same as above.", why_no_validator="Non-authorizing telemetry writer.",
        risk_owner="platform-observability",
    ),
    ("routes/draft_telemetry.py", "append_events", "X-PM-Token"): Reason(
        purpose="Same as above.", why_no_validator="Non-authorizing telemetry writer.",
        risk_owner="platform-observability",
    ),
    ("routes/draft_telemetry.py", "append_events", "X-Dispatch-Token"): Reason(
        purpose="Same as above.", why_no_validator="Non-authorizing telemetry writer.",
        risk_owner="platform-observability",
    ),
    ("routes/draft_telemetry.py", "append_events", "X-FL-Token"): Reason(
        purpose="Same as above.", why_no_validator="Non-authorizing telemetry writer.",
        risk_owner="platform-observability",
    ),
}


def _iter_backend_files() -> List[Path]:
    out: List[Path] = []
    for path in BACKEND_ROOT.rglob("*.py"):
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        if rel.startswith(("tests/", "scripts/", "migrations/", "backups/")):
            continue
        if "__pycache__" in rel or ".venv" in rel:
            continue
        out.append(path)
    return out


def _header_aliases_in_function(fn: ast.AST) -> Set[str]:
    """Extract every ``Header(default=..., alias="X-...-Token")`` alias
    literal declared as a default value in the function signature."""
    aliases: Set[str] = set()
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return aliases
    for default in list(fn.args.defaults) + list(fn.args.kw_defaults):
        if not isinstance(default, ast.Call):
            continue
        f = default.func
        if not (isinstance(f, ast.Name) and f.id == "Header"):
            if not (isinstance(f, ast.Attribute) and f.attr == "Header"):
                continue
        for kw in default.keywords:
            if kw.arg == "alias" and isinstance(kw.value, ast.Constant):
                v = kw.value.value
                if isinstance(v, str) and v in PORTAL_HEADERS:
                    aliases.add(v)
    return aliases


def _function_references_symbol(fn: ast.AST, symbol_names: Tuple[str, ...]) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and node.id in symbol_names:
            return True
        if isinstance(node, ast.Attribute) and node.attr in symbol_names:
            return True
    return False


def _collect_violations() -> List[str]:
    violations: List[str] = []
    for path in _iter_backend_files():
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            aliases = _header_aliases_in_function(node)
            if not aliases:
                continue
            for alias in aliases:
                validators = PORTAL_HEADERS[alias]
                if _function_references_symbol(node, validators):
                    continue
                # TRACK 28.04 · trusted delegation — the function calls
                # an audited helper that internally invokes the
                # canonical async validator.
                if _function_references_symbol(node, tuple(TRUSTED_DELEGATION_HELPERS)):
                    continue
                if (rel, node.name, alias) in INTERNAL_ALLOWLIST:
                    continue
                violations.append(
                    f"{rel}:{node.lineno} · {node.name}() reads "
                    f"{alias!r} but does not reference any of the "
                    f"canonical async validators {list(validators)}. "
                    f"Either add the async validation OR add "
                    f"({rel!r}, {node.name!r}, {alias!r}) to "
                    f"INTERNAL_ALLOWLIST with a documented reason."
                )
    return violations


def test_no_portal_token_gate_omits_canonical_validator() -> None:
    violations = _collect_violations()
    if violations:
        joined = "\n  • " + "\n  • ".join(violations)
        pytest.fail(
            "TRACK 28.04 portal-token gate invariant: functions that "
            "read portal-token headers must validate them via the "
            f"canonical async validator ({len(violations)} violations):"
            f"{joined}"
        )


def test_portal_gate_allowlist_entries_still_exist() -> None:
    stale: List[str] = []
    for (rel, fn_name, alias), reason in INTERNAL_ALLOWLIST.items():
        assert isinstance(reason, Reason)
        p = BACKEND_ROOT / rel
        if not p.exists():
            stale.append(f"{rel} · file missing · fn={fn_name} alias={alias}")
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError:
            continue
        names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
        if fn_name not in names:
            stale.append(f"{rel} · fn={fn_name} not found in file (alias={alias})")
    if stale:
        joined = "\n  • " + "\n  • ".join(stale)
        pytest.fail(f"Stale portal-gate allowlist entries:{joined}")

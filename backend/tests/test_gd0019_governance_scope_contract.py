"""GD-0019 — canonical GOVERNANCE-SCOPE contract guard (Checkpoint 3).

Locks the ONE governance actor-context scope contract and prevents the D-EXPIRY-SCOPE
defect class from reappearing: a served read/gate path deriving access from a governance
context key that DOES NOT EXIST (e.g. the legacy `permissions` key) silently yields an
empty set — which blacked out 423 document_expirations rows even for Super Admin.

Three layers:
  1. Contract: the resolved context exposes only the canonical scope keys via helpers.
  2. Behavioral failure injection: stale key -> empty (would false-deny/blackout);
     canonical direct/delegated keys -> correct; unauthorized -> still denied.
  3. Static anti-pattern scan: NO served backend file may read the stale governance keys
     off a governance context. Fails on reintroduction. One authority — no second contract.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path("/app/backend")))
from lib.enterprise_governance import (  # noqa: E402
    GOVERNANCE_SCOPE_CONTRACT_KEYS,
    governance_effective_permissions,
    governance_is_global_scope,
)

BACKEND = Path("/app/backend")


# -------------------- 1. contract --------------------
def test_canonical_scope_keys_are_the_authority():
    # The keys a resolved governance context actually emits (proven live in the audit).
    assert {"direct_permissions", "delegated_permissions", "governance_scope_mode"} <= set(
        GOVERNANCE_SCOPE_CONTRACT_KEYS
    )
    # The legacy/stale keys that caused the blackout are NOT part of the contract.
    for stale in ("permissions", "is_super_admin", "authority_level"):
        assert stale not in GOVERNANCE_SCOPE_CONTRACT_KEYS


# -------------------- 2. behavioral failure injection --------------------
def test_effective_permissions_reads_canonical_keys():
    ctx = {"direct_permissions": ["a.read"], "delegated_permissions": ["b.write"]}
    assert governance_effective_permissions(ctx) == {"a.read", "b.write"}


def test_stale_permissions_key_is_the_blackout_defect_and_is_not_used():
    # The REAL resolved context carries direct/delegated perms and NO legacy `permissions` key.
    real_ctx = {"direct_permissions": ["document_expirations.read.employee"], "delegated_permissions": []}
    # Buggy old code read `context.get("permissions")` -> [] on the real context => blackout.
    buggy = set(real_ctx.get("permissions") or [])
    canonical = governance_effective_permissions(real_ctx)
    assert buggy == set()                      # the defect: sees nothing -> denies everything
    assert canonical == {"document_expirations.read.employee"}
    assert buggy != canonical                  # divergence is detectable


def test_delegated_and_direct_paths_both_grant():
    assert "x.manage" in governance_effective_permissions({"direct_permissions": ["x.manage"]})
    assert "x.manage" in governance_effective_permissions({"delegated_permissions": ["x.manage"]})


def test_unauthorized_actor_remains_denied():
    # No direct/delegated perm and not global -> empty perms + not global => denied.
    ctx = {"direct_permissions": [], "delegated_permissions": [], "governance_scope_mode": "project"}
    assert governance_effective_permissions(ctx) == set()
    assert governance_is_global_scope(ctx) is False


def test_global_scope_signal_is_canonical():
    assert governance_is_global_scope({"governance_scope_mode": "global"}) is True
    assert governance_is_global_scope({"governance_scope_mode": "project"}) is False
    assert governance_is_global_scope({}) is False


# -------------------- 3. static anti-pattern scan (permanent guard) --------------------
# Matches a read of a stale governance scope key off a `context`/`ctx`/`governed*` variable.
_STALE = re.compile(
    r"\b(context|ctx|governed_actor|governed|gov_ctx)\s*\.\s*get\(\s*['\"]"
    r"(permissions|authority_level)['\"]"
)
# Files that legitimately reference the stale key names as *documentation/guard* (not a read).
_ALLOWED_FILES = {
    "lib/enterprise_governance.py",     # defines the contract + helper docstrings
    "tests/test_gd0019_governance_scope_contract.py",
}


def _served_py_files():
    for base in ("routes", "lib", "services"):
        for p in (BACKEND / base).rglob("*.py"):
            if "__pycache__" in p.parts or "/tests/" in str(p):
                continue
            yield p
    yield BACKEND / "server.py"


def test_no_served_path_reads_stale_governance_scope_keys():
    offenders = []
    for p in _served_py_files():
        rel = str(p.relative_to(BACKEND))
        if rel in _ALLOWED_FILES:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in _STALE.finditer(text):
            line = text[: m.start()].count("\n") + 1
            offenders.append(f"{rel}:{line} -> {m.group(0)}")
    assert not offenders, (
        "Served code reads a stale/nonexistent governance-context scope key (D-EXPIRY-SCOPE "
        "defect class). Use governance_effective_permissions()/governance_is_global_scope() "
        "on the canonical contract instead:\n" + "\n".join(offenders)
    )

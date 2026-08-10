"""
AI-CONFIG-001 · Tenant AI Capability Resolver
=============================================

Single authoritative check for "may this module call an AI provider
for this tenant right now?".

Every AI code path MUST route through `resolve_ai_capabilities()` and
short-circuit on the returned `Capability.enabled` field. Modules that
call a provider without consulting the resolver are treated as bugs.

Doctrine
--------
- AI is a premium optional capability.
- Platform must remain fully usable with EVERY flag set to false and
  EVERY provider key blank.
- Missing provider key → module gracefully disabled, never a crash.
- Tenant AI OFF → provider never called for that tenant, regardless
  of module or global flags.
- Fine-grained on/off per module: a tenant can enable Photo
  Intelligence without enabling PM Summaries, and vice versa.

Precedence (all must be true for a module to be `enabled`)
---------------------------------------------------------
    1. AI_GATEWAY_ENABLED (global env)
    2. TENANT_AI_ENABLED (tenant capability doc, else env default)
    3. AI_<MODULE>_ENABLED (module env flag)
    4. TENANT_AI_<MODULE>_ENABLED (tenant module flag)
    5. Selected provider is enabled AND its API key is set

If ANY link fails, the resolver returns `enabled=False` with a machine-
readable `reason_disabled` code the caller can log but MUST NOT surface
as user-facing "AI is off" chrome (per Invisible Intelligence).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


# ─────────────────────── env helpers ──────────────────────────────

def _truthy(v: Optional[str]) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def _env(name: str) -> str:
    return os.environ.get(name, "")


# ─────────────────────── modules ──────────────────────────────────

MODULE_ENV_MAP = {
    # module_key   →  (deployment env flag,               tenant env flag)
    "daily_report_summary":  ("AI_DAILY_REPORT_SUMMARY_ENABLED",  "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED"),
    "photo_intelligence":    ("AI_PHOTO_VISION_ENABLED",          "TENANT_AI_PHOTO_INTELLIGENCE_ENABLED"),
    "pm_intelligence":       ("AI_PM_INTELLIGENCE_ENABLED",       "TENANT_AI_PM_INTELLIGENCE_ENABLED"),
    "admin_intelligence":    ("AI_ADMIN_INTELLIGENCE_ENABLED",    "TENANT_AI_ADMIN_INTELLIGENCE_ENABLED"),
    "safety_intelligence":   ("AI_SAFETY_INTELLIGENCE_ENABLED",   "TENANT_AI_SAFETY_INTELLIGENCE_ENABLED"),
    "translation":           ("AI_TRANSLATION_ENABLED",           "TENANT_AI_TRANSLATION_ENABLED"),
}

PROVIDER_KEY_MAP = {
    "anthropic": ("AI_PROVIDER_ANTHROPIC_ENABLED", "ANTHROPIC_API_KEY"),
    "openai":    ("AI_PROVIDER_OPENAI_ENABLED",    "OPENAI_API_KEY"),
    "google":    ("AI_PROVIDER_GOOGLE_ENABLED",    "GOOGLE_AI_API_KEY"),
}

_UNIVERSAL_KEY_ENV = "EMERGENT_LLM_KEY"


@dataclass
class Capability:
    """Result of a capability check for a single module."""
    module: str
    tenant_id: str
    enabled: bool
    reason_disabled: Optional[str] = None      # machine-readable code
    selected_provider: Optional[str] = None    # e.g. "anthropic"
    fallback_provider: Optional[str] = None
    provider_available: bool = False
    tenant_ai_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ────────────────── tenant capability loader ──────────────────────

async def _tenant_capabilities_doc(db, tenant_id: str) -> Dict[str, Any]:
    """Load a tenant override doc from Mongo, if present.

    Absence of a doc is normal — env defaults apply. `db` may be None
    (e.g. during unit tests). Returns an empty dict on any error so
    the resolver stays on the safe path.
    """
    if db is None or not tenant_id:
        return {}
    try:
        doc = await db["tenant_ai_capabilities"].find_one(
            {"tenant_id": tenant_id}, {"_id": 0},
        )
        return doc or {}
    except Exception:  # noqa: BLE001
        return {}


# ─────────────────────── provider check ───────────────────────────

def _resolve_provider() -> tuple[Optional[str], Optional[str], bool]:
    """Pick a usable provider based on global flags + key presence.

    Returns (selected_provider, fallback_provider, available).
    """
    default = (_env("AI_DEFAULT_PROVIDER") or "anthropic").lower()
    candidates = [default] + [p for p in ("anthropic", "openai", "google") if p != default]
    selected: Optional[str] = None
    fallback: Optional[str] = None
    for name in candidates:
        flag_name, key_name = PROVIDER_KEY_MAP.get(name, ("", ""))
        if not flag_name:
            continue
        if _truthy(_env(flag_name)) and _provider_key_present(key_name):
            if selected is None:
                selected = name
            elif fallback is None:
                fallback = name
                break
    return selected, fallback, bool(selected)


def _provider_key_present(key_name: str) -> bool:
    return bool(_env(key_name).strip()) or bool(_env(_UNIVERSAL_KEY_ENV).strip())


def _covered_by_universal(key_name: str) -> bool:
    return not bool(_env(key_name).strip()) and bool(_env(_UNIVERSAL_KEY_ENV).strip())


# ─────────────────────── main resolver ────────────────────────────

async def resolve_ai_capabilities(
    db,
    tenant_id: str,
    module: str,
) -> Capability:
    """The single authoritative capability check.

    Callers MUST early-return when `enabled=False`.
    """
    if module not in MODULE_ENV_MAP:
        return Capability(
            module=module, tenant_id=tenant_id, enabled=False,
            reason_disabled="unknown_module",
        )

    # 1) Global gateway
    if not _truthy(_env("AI_GATEWAY_ENABLED")):
        return Capability(
            module=module, tenant_id=tenant_id, enabled=False,
            reason_disabled="ai_gateway_disabled_global",
        )

    # 2) Tenant enrollment
    tenant_doc = await _tenant_capabilities_doc(db, tenant_id)
    tenant_ai_env = _truthy(_env("TENANT_AI_ENABLED"))
    tenant_ai_enabled = tenant_doc.get("tenant_ai_enabled", tenant_ai_env)
    if not tenant_ai_enabled:
        return Capability(
            module=module, tenant_id=tenant_id, enabled=False,
            reason_disabled="tenant_ai_disabled",
            tenant_ai_enabled=False,
        )

    # 3) Module (deployment env)
    module_env_flag, tenant_module_key = MODULE_ENV_MAP[module]
    if not _truthy(_env(module_env_flag)):
        return Capability(
            module=module, tenant_id=tenant_id, enabled=False,
            reason_disabled=f"module_disabled_global:{module}",
            tenant_ai_enabled=True,
        )

    # 4) Module (tenant override)
    tenant_module_env_default = _truthy(_env(tenant_module_key))
    tenant_module_enabled = tenant_doc.get(
        _snake_field(tenant_module_key), tenant_module_env_default
    )
    if not tenant_module_enabled:
        return Capability(
            module=module, tenant_id=tenant_id, enabled=False,
            reason_disabled=f"module_disabled_tenant:{module}",
            tenant_ai_enabled=True,
        )

    # 5) Provider + key
    selected, fallback, available = _resolve_provider()
    if not available:
        return Capability(
            module=module, tenant_id=tenant_id, enabled=False,
            reason_disabled="no_provider_available",
            tenant_ai_enabled=True,
        )

    return Capability(
        module=module, tenant_id=tenant_id, enabled=True,
        selected_provider=selected, fallback_provider=fallback,
        provider_available=True, tenant_ai_enabled=True,
    )


def _snake_field(env_name: str) -> str:
    """`TENANT_AI_PHOTO_INTELLIGENCE_ENABLED` → `photo_intelligence_enabled`."""
    trimmed = env_name.removeprefix("TENANT_AI_").removesuffix("_ENABLED")
    return trimmed.lower() + "_enabled"


# ──────────────── admin startup/status snapshot ───────────────────

def gateway_status_snapshot() -> Dict[str, Any]:
    """Non-secret snapshot for admin-only /api/ai/status.

    IMPORTANT: never returns raw API keys. Only booleans indicating
    key presence.
    """
    def _key_present(name: str) -> bool:
        return bool(_env(name).strip())

    modules = {}
    for m, (flag, tenant_flag) in MODULE_ENV_MAP.items():
        modules[m] = {
            "deployment_flag": flag,
            "deployment_enabled": _truthy(_env(flag)),
            "tenant_default_flag": tenant_flag,
            "tenant_default_enabled": _truthy(_env(tenant_flag)),
        }

    providers = {}
    for p, (flag, key) in PROVIDER_KEY_MAP.items():
        providers[p] = {
            "flag": flag,
            "enabled": _truthy(_env(flag)),
            "key_env": key,
            "key_present": _provider_key_present(key),
            "covered_by_universal": _covered_by_universal(key),
        }

    selected, fallback, available = _resolve_provider()
    return {
        "gateway_enabled": _truthy(_env("AI_GATEWAY_ENABLED")),
        "tenant_ai_default_enabled": _truthy(_env("TENANT_AI_ENABLED")),
        "default_provider": _env("AI_DEFAULT_PROVIDER") or "anthropic",
        "default_text_model": _env("AI_DEFAULT_TEXT_MODEL"),
        "default_vision_provider": _env("AI_DEFAULT_VISION_PROVIDER"),
        "default_vision_model": _env("AI_DEFAULT_VISION_MODEL"),
        "resolved_selected_provider": selected,
        "resolved_fallback_provider": fallback,
        "resolved_provider_available": available,
        "providers": providers,
        "modules": modules,
        "transport": {
            "timeout_ms": int(_env("AI_PROVIDER_TIMEOUT_MS") or 30000),
            "max_retries": int(_env("AI_PROVIDER_MAX_RETRIES") or 2),
            "failover_enabled": _truthy(_env("AI_PROVIDER_FAILOVER_ENABLED")),
        },
    }


__all__ = [
    "Capability",
    "resolve_ai_capabilities",
    "gateway_status_snapshot",
    "MODULE_ENV_MAP",
    "PROVIDER_KEY_MAP",
]

"""
AI-CONFIG-001 · Tenant AI capability lock envelope.

Every test proves ONE invariant:
  1. All AI flags false → resolver returns disabled for every module.
  2. Missing provider keys → resolver returns disabled even with all
     other flags set to true.
  3. Tenant AI off (Mongo override) → resolver returns disabled even
     when deployment flags are on.
  4. Module-level tenant override can independently enable/disable.
  5. Provider selection respects `AI_DEFAULT_PROVIDER`.
  6. `.env.example` contract holds — every documented key is present.
  7. Daily Report submit path does NOT import the resolver at module
     load (proves AI is not an import-time dependency).
  8. `gateway_status_snapshot` never leaks a real key value.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


# ─────────────────────── env sandbox ──────────────────────────────

AI_ENV_KEYS = [
    "AI_GATEWAY_ENABLED",
    "AI_PROVIDER_ANTHROPIC_ENABLED", "AI_PROVIDER_OPENAI_ENABLED", "AI_PROVIDER_GOOGLE_ENABLED",
    "AI_DEFAULT_PROVIDER", "AI_DEFAULT_TEXT_MODEL",
    "AI_DEFAULT_VISION_PROVIDER", "AI_DEFAULT_VISION_MODEL",
    "AI_DAILY_REPORT_SUMMARY_ENABLED", "AI_PHOTO_VISION_ENABLED",
    "AI_PM_INTELLIGENCE_ENABLED", "AI_ADMIN_INTELLIGENCE_ENABLED",
    "AI_SAFETY_INTELLIGENCE_ENABLED",
    "AI_TRANSLATION_ENABLED",
    "AI_PROVIDER_TIMEOUT_MS", "AI_PROVIDER_MAX_RETRIES", "AI_PROVIDER_FAILOVER_ENABLED",
    "DR_DAILY_OPERATIONAL_SUMMARY_ENABLED", "DR_PHOTO_INTELLIGENCE_ENABLED",
    "DR_EN_ES_MODE_ENABLED", "DR_CANONICAL_ENGLISH_SUBMIT_ENABLED",
    "TENANT_AI_ENABLED",
    "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED",
    "TENANT_AI_PHOTO_INTELLIGENCE_ENABLED",
    "TENANT_AI_PM_INTELLIGENCE_ENABLED",
    "TENANT_AI_ADMIN_INTELLIGENCE_ENABLED",
    "TENANT_AI_SAFETY_INTELLIGENCE_ENABLED",
    "TENANT_AI_TRANSLATION_ENABLED",
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY",
]


@pytest.fixture(autouse=True)
def _clean_env():
    saved = {k: os.environ.get(k) for k in AI_ENV_KEYS}
    for k in AI_ENV_KEYS:
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


# ────────────────────── fake Mongo db ─────────────────────────────

class _TenantCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return {kk: vv for kk, vv in d.items() if kk != "_id"}
        return None


class _FakeDB:
    def __init__(self, tenant_docs=None):
        self.tenant_ai_capabilities = _TenantCollection(tenant_docs)

    def __getitem__(self, name):
        return getattr(self, name)


# ────────────────────── invariants ────────────────────────────────

@pytest.mark.asyncio
async def test_all_flags_false_returns_disabled_for_every_module():
    from services.ai_gateway.capabilities import (
        resolve_ai_capabilities, MODULE_ENV_MAP,
    )
    db = _FakeDB()
    for module in MODULE_ENV_MAP:
        cap = await resolve_ai_capabilities(db, "masci", module)
        assert cap.enabled is False, f"{module} must be disabled when all flags off"
        assert cap.reason_disabled == "ai_gateway_disabled_global"


@pytest.mark.asyncio
async def test_missing_provider_key_disables_module_even_with_flags_on():
    os.environ["AI_GATEWAY_ENABLED"] = "true"
    os.environ["TENANT_AI_ENABLED"] = "true"
    os.environ["AI_DAILY_REPORT_SUMMARY_ENABLED"] = "true"
    os.environ["TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED"] = "true"
    os.environ["AI_PROVIDER_ANTHROPIC_ENABLED"] = "true"
    # ANTHROPIC_API_KEY intentionally unset.
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    cap = await resolve_ai_capabilities(_FakeDB(), "masci", "daily_report_summary")
    assert cap.enabled is False
    assert cap.reason_disabled == "no_provider_available"


@pytest.mark.asyncio
async def test_tenant_off_blocks_all_modules_even_when_deployment_flags_on():
    for k in ("AI_GATEWAY_ENABLED", "AI_DAILY_REPORT_SUMMARY_ENABLED",
              "AI_PROVIDER_ANTHROPIC_ENABLED"):
        os.environ[k] = "true"
    os.environ["ANTHROPIC_API_KEY"] = "sk-test-value"
    os.environ["TENANT_AI_ENABLED"] = "true"  # deployment default true
    db = _FakeDB([{"tenant_id": "masci", "tenant_ai_enabled": False}])  # override
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    cap = await resolve_ai_capabilities(db, "masci", "daily_report_summary")
    assert cap.enabled is False
    assert cap.reason_disabled == "tenant_ai_disabled"


@pytest.mark.asyncio
async def test_tenant_module_flag_independent_of_other_modules():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
        "AI_PHOTO_VISION_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-test",
    })
    # Tenant enables Photo Intelligence ONLY.
    db = _FakeDB([{
        "tenant_id": "masci",
        "tenant_ai_enabled": True,
        "photo_intelligence_enabled": True,
        "daily_report_summary_enabled": False,
    }])
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    photo = await resolve_ai_capabilities(db, "masci", "photo_intelligence")
    summary = await resolve_ai_capabilities(db, "masci", "daily_report_summary")
    assert photo.enabled is True, photo.reason_disabled
    assert summary.enabled is False
    assert summary.reason_disabled == "module_disabled_tenant:daily_report_summary"


@pytest.mark.asyncio
async def test_summary_only_does_not_enable_photo_intelligence():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
        # AI_PHOTO_VISION_ENABLED intentionally unset.
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-test",
    })
    db = _FakeDB([{
        "tenant_id": "masci",
        "tenant_ai_enabled": True,
        "daily_report_summary_enabled": True,
        "photo_intelligence_enabled": True,   # tenant flag on...
    }])
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    photo = await resolve_ai_capabilities(db, "masci", "photo_intelligence")
    assert photo.enabled is False, "deployment module flag must gate tenant flag"
    assert photo.reason_disabled == "module_disabled_global:photo_intelligence"


@pytest.mark.asyncio
async def test_provider_selection_respects_default_provider_env():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_TRANSLATION_ENABLED": "true",
        "TENANT_AI_ENABLED": "true",
        "TENANT_AI_TRANSLATION_ENABLED": "true",
        "AI_DEFAULT_PROVIDER": "openai",
        "AI_PROVIDER_OPENAI_ENABLED": "true",
        "OPENAI_API_KEY": "sk-oai",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-anth",
    })
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    cap = await resolve_ai_capabilities(_FakeDB(), "masci", "translation")
    assert cap.enabled is True
    assert cap.selected_provider == "openai"
    assert cap.fallback_provider == "anthropic"


@pytest.mark.asyncio
async def test_two_tenants_can_have_different_ai_state():
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-test",
    })
    db = _FakeDB([
        {"tenant_id": "acme", "tenant_ai_enabled": True,
         "daily_report_summary_enabled": True},
        {"tenant_id": "widgets", "tenant_ai_enabled": False},
    ])
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    acme = await resolve_ai_capabilities(db, "acme", "daily_report_summary")
    widgets = await resolve_ai_capabilities(db, "widgets", "daily_report_summary")
    assert acme.enabled is True
    assert widgets.enabled is False
    assert widgets.reason_disabled == "tenant_ai_disabled"


def test_status_snapshot_never_leaks_raw_keys():
    os.environ["ANTHROPIC_API_KEY"] = "sk-should-NEVER-leak"
    os.environ["OPENAI_API_KEY"] = "sk-openai-secret"
    from services.ai_gateway.capabilities import gateway_status_snapshot
    snap = gateway_status_snapshot()
    import json
    j = json.dumps(snap)
    assert "sk-should-NEVER-leak" not in j
    assert "sk-openai-secret" not in j
    # But `key_present` booleans must be surfaced.
    assert snap["providers"]["anthropic"]["key_present"] is True
    assert snap["providers"]["openai"]["key_present"] is True
    assert snap["providers"]["google"]["key_present"] is False


def test_env_example_documents_every_required_key():
    example_path = Path("/app/.env.example")
    assert example_path.exists()
    body = example_path.read_text(encoding="utf-8")
    required = [
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY",
        "AI_GATEWAY_ENABLED",
        "AI_PROVIDER_ANTHROPIC_ENABLED", "AI_PROVIDER_OPENAI_ENABLED", "AI_PROVIDER_GOOGLE_ENABLED",
        "AI_DEFAULT_PROVIDER", "AI_DEFAULT_TEXT_MODEL",
        "AI_DEFAULT_VISION_PROVIDER", "AI_DEFAULT_VISION_MODEL",
        "AI_DAILY_REPORT_SUMMARY_ENABLED", "AI_PHOTO_VISION_ENABLED",
        "AI_PM_INTELLIGENCE_ENABLED", "AI_ADMIN_INTELLIGENCE_ENABLED",
        "AI_SAFETY_INTELLIGENCE_ENABLED",
        "AI_TRANSLATION_ENABLED",
        "AI_PROVIDER_TIMEOUT_MS", "AI_PROVIDER_MAX_RETRIES", "AI_PROVIDER_FAILOVER_ENABLED",
        "DR_DAILY_OPERATIONAL_SUMMARY_ENABLED", "DR_PHOTO_INTELLIGENCE_ENABLED",
        "DR_EN_ES_MODE_ENABLED", "DR_CANONICAL_ENGLISH_SUBMIT_ENABLED",
        "TENANT_AI_ENABLED",
        "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED",
        "TENANT_AI_PHOTO_INTELLIGENCE_ENABLED",
        "TENANT_AI_PM_INTELLIGENCE_ENABLED",
        "TENANT_AI_ADMIN_INTELLIGENCE_ENABLED",
        "TENANT_AI_SAFETY_INTELLIGENCE_ENABLED",
        "TENANT_AI_TRANSLATION_ENABLED",
    ]
    for k in required:
        assert f"{k}=" in body, f"{k} missing from .env.example"


def test_env_example_never_contains_real_key_values():
    body = Path("/app/.env.example").read_text(encoding="utf-8")
    # Placeholders must have empty values (no sk-… or key-… strings).
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "API_KEY=" in stripped:
            _, value = stripped.split("=", 1)
            assert value.strip() == "", f"Real key detected in .env.example line: {line!r}"


def test_daily_report_submit_module_does_not_import_resolver_at_load_time():
    """AI capability check is opt-in per callsite; the submit route
    must not import the resolver at module load — that would couple
    Daily Report submit to AI infra."""
    import routes.daily_reports as dr_mod
    src = Path(dr_mod.__file__).read_text(encoding="utf-8")
    # Resolver is fine to lazy-import inside a function; but must not
    # appear as a top-level import.
    top = "\n".join(src.splitlines()[:80])
    assert "resolve_ai_capabilities" not in top, (
        "resolve_ai_capabilities must not be imported at module load "
        "in routes/daily_reports.py — AI is optional"
    )


@pytest.mark.asyncio
async def test_v1_submit_hook_still_works_with_all_ai_off():
    """Sanity: the V1 → ODS hook does not depend on AI. Even with
    every AI flag OFF, `ingest_dr_v1_report` still emits facts."""
    # AI flags all off. ODS flags on.
    os.environ["ODS_ENABLED"] = "1"
    os.environ["DR_V2_SPINE_EMISSION_ENABLED"] = "1"
    from services.ods_spine.ingest import _build_facts_from_dr_v1_report
    doc = {
        "id": "ai-off-lock",
        "project_number": "AI-OFF-TEST",
        "report_date": "2026-02-15",
        "masci_crews": [{"trade": "Concrete", "count": 4, "hours": 8}],
        "photos": ["p1", "p2", "p3", "p4", "p5", "p6"],
    }
    facts = _build_facts_from_dr_v1_report(doc)
    assert len(facts) >= 7  # 1 labor + 6 photos minimum
    assert all(f["source_type"] == "daily_report_v1" for f in facts)


def test_snake_field_helper_maps_env_names_to_doc_keys():
    from services.ai_gateway.capabilities import _snake_field
    assert _snake_field("TENANT_AI_PHOTO_INTELLIGENCE_ENABLED") == "photo_intelligence_enabled"
    assert _snake_field("TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED") == "daily_report_summary_enabled"
    assert _snake_field("TENANT_AI_TRANSLATION_ENABLED") == "translation_enabled"


@pytest.mark.asyncio
async def test_unknown_module_returns_disabled_with_reason():
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    cap = await resolve_ai_capabilities(_FakeDB(), "masci", "unknown_thing")
    assert cap.enabled is False
    assert cap.reason_disabled == "unknown_module"


@pytest.mark.asyncio
async def test_admin_intelligence_flag_independent_of_pm_intelligence():
    """`admin_intelligence` and `pm_intelligence` must be independently
    gatable via distinct deployment env flags (contract per user)."""
    os.environ.update({
        "AI_GATEWAY_ENABLED": "true",
        "TENANT_AI_ENABLED": "true",
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "ANTHROPIC_API_KEY": "sk-test",
        # Turn ON pm, leave admin OFF.
        "AI_PM_INTELLIGENCE_ENABLED": "true",
        "TENANT_AI_PM_INTELLIGENCE_ENABLED": "true",
        "TENANT_AI_ADMIN_INTELLIGENCE_ENABLED": "true",
    })
    from services.ai_gateway.capabilities import resolve_ai_capabilities
    pm = await resolve_ai_capabilities(_FakeDB(), "masci", "pm_intelligence")
    admin = await resolve_ai_capabilities(_FakeDB(), "masci", "admin_intelligence")
    assert pm.enabled is True, pm.reason_disabled
    assert admin.enabled is False
    assert admin.reason_disabled == "module_disabled_global:admin_intelligence"


def test_backend_env_exposes_every_ai_placeholder_to_secrets_ui():
    """The Emergent Secrets UI reads `/app/backend/.env`. Every AI key
    the operator must be able to paste MUST be present there with an
    empty or safe default value — otherwise the field will not appear
    in the Secrets UI, and the operator has no place to paste a real
    key. This is the acceptance criterion for AI-CONFIG-001."""
    body = Path("/app/backend/.env").read_text(encoding="utf-8")
    lines = {ln.split("=", 1)[0].strip() for ln in body.splitlines()
             if "=" in ln and not ln.lstrip().startswith("#")}
    required = [
        # Provider API keys — must be present as empty placeholders.
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY",
        # Provider enable flags.
        "AI_PROVIDER_ANTHROPIC_ENABLED",
        "AI_PROVIDER_OPENAI_ENABLED",
        "AI_PROVIDER_GOOGLE_ENABLED",
        # Global gateway + defaults.
        "AI_GATEWAY_ENABLED", "AI_DEFAULT_PROVIDER",
        # Module deployment flags.
        "AI_DAILY_REPORT_SUMMARY_ENABLED",
        "AI_PHOTO_VISION_ENABLED",
        "AI_PM_INTELLIGENCE_ENABLED",
        "AI_ADMIN_INTELLIGENCE_ENABLED",
        "AI_SAFETY_INTELLIGENCE_ENABLED",
        "AI_TRANSLATION_ENABLED",
        # Tenant-level defaults.
        "TENANT_AI_ENABLED",
        "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED",
        "TENANT_AI_PHOTO_INTELLIGENCE_ENABLED",
        "TENANT_AI_PM_INTELLIGENCE_ENABLED",
        "TENANT_AI_ADMIN_INTELLIGENCE_ENABLED",
        "TENANT_AI_SAFETY_INTELLIGENCE_ENABLED",
        "TENANT_AI_TRANSLATION_ENABLED",
    ]
    missing = [k for k in required if k not in lines]
    assert not missing, (
        "AI-CONFIG-001 secret-panel contract broken. Missing keys in "
        f"/app/backend/.env: {missing}. Add them (empty values are OK) "
        "so the Emergent Secrets UI exposes the fields."
    )


def test_backend_env_provider_keys_are_placeholders_not_real_keys():
    """Even though the backend/.env may hold real secrets in prod, in
    this codebase repo the provider keys must ship as empty placeholders
    (the operator pastes real values via the Secrets UI, not git)."""
    body = Path("/app/backend/.env").read_text(encoding="utf-8")
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        if k.strip() in {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY"}:
            assert v.strip() == "", (
                f"{k} must ship as an empty placeholder in backend/.env — "
                f"paste real values via Emergent Secrets UI, never commit."
            )


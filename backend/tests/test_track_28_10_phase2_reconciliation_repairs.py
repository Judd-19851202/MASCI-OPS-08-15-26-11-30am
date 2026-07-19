from __future__ import annotations

import json
import sys
from pathlib import Path


BACKEND = Path("/app/backend")
sys.path.insert(0, str(BACKEND))


def test_openai_wrapped_json_extractor_handles_fenced_payloads():
    from services.ai_gateway.adapters.openai_adapter import _extract_wrapped_json

    wrapped = "```json\n{\"narrative\":\"ok\",\"confidence\":0.8}\n```"
    assert _extract_wrapped_json(wrapped) == '{"narrative":"ok","confidence":0.8}'


def test_restore_drill_supports_collections_name_json_layout_and_content_hash_key():
    src = Path("/app/backend/tools/restore_drill.py").read_text(encoding="utf-8")
    assert 'parts[0] == "collections"' in src
    assert 'single_payload[Path(parts[1]).stem] = n' in src
    assert 'def _content_hash_key(doc: dict) -> str:' in src
    assert '"_restore_content_hash": key' in src
    assert 'UpdateOne({"_restore_content_hash": key}, {"$set": d}, upsert=True)' in src


def test_daily_reports_new_alias_redirect_present():
    src = Path("/app/frontend/src/app/routing/AppRoutes.jsx").read_text(encoding="utf-8")
    assert 'path="/daily-reports/new" element={<Navigate to="/daily/submit" replace />}' in src


def test_splash_overlay_duration_class_repaired():
    src = Path("/app/frontend/src/components/SplashOverlay.jsx").read_text(encoding="utf-8")
    assert 'duration-[400ms]' in src
    assert 'duration-&lsqb;400ms&rsqb;' not in src


def test_pm_actor_tagging_present_on_shared_auth_gates():
    src = Path("/app/backend/server.py").read_text(encoding="utf-8")
    required = [
        'return {**pm_doc, "_actor_kind": "pm_user", "_actor": "pm", "role": "pm"}',
    ]
    for needle in required:
        assert src.count(needle) >= 4, needle

"""OpenAI adapter — scaffold with matching interface.

Backed by emergentintegrations when EMERGENT_LLM_KEY is present (which
routes internally to OpenAI). Vision path is scaffolded so PhotoIntelligence
can plug in when the OpenAI vision model is enabled — no schema drift required.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from ..envelope import AiEnvelope


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpenAIAdapter:
    name = "openai"

    async def text(
        self, *, system: str, user_payload: Dict[str, Any],
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope:
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY") or ""
        if not key:
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["openai_key_missing"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="missing_api_key")

        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=[f"import_error:{exc.__class__.__name__}"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="import_error")

        prompt = (
            "EVIDENCE BUNDLE (json):\n"
            + json.dumps(user_payload, sort_keys=True, ensure_ascii=False)
            + "\n\nRespond with strict JSON matching this schema:\n"
            + json.dumps(response_schema, ensure_ascii=False)
        )
        try:
            chat = LlmChat(
                api_key=key, session_id=session_id, system_message=system,
            ).with_model("openai", model)
            raw = await chat.send_message(UserMessage(text=prompt))
        except Exception as exc:  # noqa: BLE001
            # Preserve the auth signal so the gateway can short-circuit
            # retries and failover immediately on invalid keys.
            cls = exc.__class__.__name__
            msg = str(exc).lower()
            is_auth = (
                "authentication" in cls.lower()
                or "unauthorized" in msg
                or "401" in msg
                or "invalid api key" in msg
                or "incorrect api key" in msg
            )
            reason = "unauthorized" if is_auth else "llm_call_failed"
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=[f"call_failed:{cls}"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason=reason)

        text = (raw or "").strip().lstrip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
        try:
            data = json.loads(text)
        except Exception:  # noqa: BLE001
            return AiEnvelope(task=task, narrative=text[:500], confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["non_json_response"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="invalid_json")

        try:
            conf = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        return AiEnvelope(
            task=task,
            narrative=str(data.get("narrative", ""))[:4000],
            confidence=max(0.0, min(1.0, conf)),
            evidence_refs=[str(x) for x in data.get("evidence_refs", [])][:64],
            sources_used=[str(x) for x in data.get("sources_used", [])][:64],
            uncertainties=[str(x) for x in (data.get("uncertainties") or [])][:32],
            provider=self.name, model=model, generated_at=_now(),
            ai_available=True,
        )

    async def vision(
        self, *, system: str, images: list, user: str,
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope:
        """Real vision path. `images` is a list of base64 strings OR
        `{"content_type": str, "file_content_base64": str}` dicts."""
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY") or ""
        if not key:
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["openai_vision_key_missing"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="missing_api_key")

        try:
            from emergentintegrations.llm.chat import (  # noqa: PLC0415
                LlmChat, UserMessage, FileContent, ImageContent,
            )
        except Exception as exc:  # noqa: BLE001
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=[f"import_error:{exc.__class__.__name__}"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="import_error")

        file_contents = []
        for img in (images or [])[:6]:  # cap at 6 images per call
            if isinstance(img, dict) and img.get("file_content_base64"):
                file_contents.append(FileContent(
                    content_type=img.get("content_type", "image/jpeg"),
                    file_content_base64=img["file_content_base64"],
                ))
            elif isinstance(img, str):
                # Assume base64 image
                try:
                    file_contents.append(ImageContent(image_base64=img))
                except Exception:  # noqa: BLE001
                    file_contents.append(FileContent(content_type="image/jpeg", file_content_base64=img))

        if not file_contents:
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["no_images_provided"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="no_images")

        prompt = user + "\n\nRespond with strict JSON matching:\n" + json.dumps(response_schema, ensure_ascii=False)
        try:
            chat = LlmChat(
                api_key=key, session_id=session_id, system_message=system,
            ).with_model("openai", model)
            raw = await chat.send_message(UserMessage(text=prompt, file_contents=file_contents))
        except Exception as exc:  # noqa: BLE001
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=[f"vision_call_failed:{exc.__class__.__name__}"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="vision_call_failed")

        text = (raw or "").strip().lstrip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
        try:
            data = json.loads(text)
        except Exception:  # noqa: BLE001
            return AiEnvelope(task=task, narrative=text[:500], confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["non_json_vision_response"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="invalid_json",
                              raw={"text": text[:2000]})

        try:
            conf = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        return AiEnvelope(
            task=task,
            narrative=str(data.get("narrative", ""))[:4000],
            confidence=max(0.0, min(1.0, conf)),
            evidence_refs=[str(x) for x in data.get("evidence_refs", [])][:64],
            sources_used=[str(x) for x in data.get("sources_used", [])][:64],
            uncertainties=[str(x) for x in (data.get("uncertainties") or [])][:32],
            provider=self.name, model=model, generated_at=_now(),
            ai_available=True,
            raw=data,  # observations/links/questions live here for the caller
        )

    def ping(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "key_present": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")),
        }

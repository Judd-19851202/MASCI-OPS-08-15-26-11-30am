"""ForgedOps · AI Gateway.

Model-agnostic gateway sitting between operational workflows (Daily
Report V2, PM briefs, photo vision, executive intelligence) and any
LLM provider (Anthropic, OpenAI, Google Gemini, future).

Design:
    workflow  →  task_router (task_type)  →  registry (provider)
                                            →  adapter (model)
                                            →  provider SDK

Every adapter implements the same 4 methods:
    text(system, user, response_schema, session_id) -> AiEnvelope
    vision(system, images[], user, response_schema) -> AiEnvelope (future)
    stream(...)                                     -> async iterator (future)
    ping()                                          -> dict health

Public surface:
    get_gateway()               — singleton gateway
    Gateway.dispatch(task, ...) — task-typed dispatch
    Gateway.provider(name)      — direct adapter access
    TaskType                    — literal task-name constants
"""
from .registry import Gateway, get_gateway, provider_meta_snapshot
from .task_router import TASK_ROUTES, TaskType
from .env import env_snapshot
from .envelope import AiEnvelope

__all__ = [
    "Gateway", "get_gateway", "provider_meta_snapshot",
    "TASK_ROUTES", "TaskType",
    "env_snapshot", "AiEnvelope",
]

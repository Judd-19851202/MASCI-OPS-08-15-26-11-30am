from __future__ import annotations

import os
from typing import Any, Dict, List, Mapping, Optional


DEFAULT_CORS_REGEX = (
    r"^https://("
    r"(www\.)?mascidocs\.com"
    r"|.*\.emergentagent\.com"
    r"|.*\.preview\.emergentagent\.com"
    r"|.*\.emergent\.host"
    r")$"
)


def resolve_effective_cors_config(env: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    source = env or os.environ
    cors_origins_env = str(source.get("CORS_ORIGINS") or "").strip()
    cors_origin_regex = str(source.get("CORS_ORIGIN_REGEX") or "").strip() or None

    if cors_origins_env and cors_origins_env != "*":
        allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
        allow_origin_regex = None
        origin_mode = "explicit_list"
    else:
        allow_origins = []
        allow_origin_regex = cors_origin_regex or DEFAULT_CORS_REGEX
        origin_mode = "regex_fallback" if cors_origins_env in {"", "*"} else "regex_explicit"

    allow_methods: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
    allow_headers: List[str] = [
        "Authorization",
        "Content-Type",
        "X-Admin-Token",
        "X-PM-Token",
        "X-HR-Token",
        "X-Safety-Token",
        "X-Dispatch-Token",
        "X-Leadership-Token",
        "X-Shop-Token",
        "X-FL-Token",
    ]

    return {
        "allow_credentials": True,
        "allow_origins": allow_origins,
        "allow_origin_regex": allow_origin_regex,
        "allow_methods": allow_methods,
        "allow_headers": allow_headers,
        "origin_mode": origin_mode,
        "raw_env": cors_origins_env,
        "raw_origin_regex": cors_origin_regex,
    }


def summarize_cors_truth(env: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    cfg = resolve_effective_cors_config(env)
    explicit_origin_count = len(cfg["allow_origins"])
    origin_regex = cfg["allow_origin_regex"]
    effective_pinned = bool(explicit_origin_count or origin_regex)
    return {
        "cors_pinned": effective_pinned,
        "allows_wildcard_origin": False,
        "origin_mode": cfg["origin_mode"],
        "explicit_origin_count": explicit_origin_count,
        "origin_regex_configured": bool(origin_regex),
        "credentials_allowed": bool(cfg["allow_credentials"]),
        "raw_env_blank_or_wildcard": cfg["raw_env"] in {"", "*"},
        "effective_origin_regex": origin_regex,
    }

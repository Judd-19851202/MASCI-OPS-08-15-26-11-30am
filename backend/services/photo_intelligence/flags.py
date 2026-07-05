"""DR-ROI-001D · Photo Intelligence feature flag."""
from __future__ import annotations
import os


def photo_vision_enabled() -> bool:
    return (os.environ.get("DR_V2_PHOTO_VISION_ENABLED") or "").lower() in {"1", "true", "yes", "on"}

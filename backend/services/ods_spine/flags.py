"""ODS-001 · Feature flags.

ODS_ENABLED                     — global spine ingestion + read APIs
DR_V2_SPINE_EMISSION_ENABLED    — DR-V2 → spine emission hook

Both default OFF so a stale env cannot flood the spine.
"""
from __future__ import annotations
import os


def _truthy(v) -> bool:
    return (v or "").lower() in {"1", "true", "yes", "on"}


def ods_enabled() -> bool:
    return _truthy(os.environ.get("ODS_ENABLED"))


def dr_v2_spine_emission_enabled() -> bool:
    return _truthy(os.environ.get("DR_V2_SPINE_EMISSION_ENABLED"))

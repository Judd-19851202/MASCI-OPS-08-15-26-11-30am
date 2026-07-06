"""services/operational_kpis/__init__.py — TRACK 23.7."""
from .aggregator import aggregate_project_kpis, _resolve_window

__all__ = ["aggregate_project_kpis", "_resolve_window"]

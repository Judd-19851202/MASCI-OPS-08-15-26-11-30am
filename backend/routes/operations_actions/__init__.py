"""OA-1 · Operations Actions module.

Cross-portal operational coordination layer. Read this constitution
before changing anything in this module:

    /app/memory/OA1_OPERATIONS_ACTIONS_CONSTITUTION.md

OMEGA discipline applies:
  * CRUD only (Create / Assign / Update / Notes / Photos / Status / Close / View).
  * No automation. No AI. No email/SMS. No SLA. No bulk. No export.
  * ForgedOps is NEVER the system of record.
"""
from .api import register_operations_actions_routes

__all__ = ["register_operations_actions_routes"]

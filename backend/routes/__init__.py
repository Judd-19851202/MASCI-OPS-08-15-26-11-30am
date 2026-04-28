"""Server route modules.

Each `register_*_routes()` function takes the shared `api_router`, `db`,
and any auth dependencies, and attaches its endpoints. This pattern lets
us split server.py without touching the global FastAPI app or breaking
import cycles.

To migrate more legacy routes out of server.py:
1. Copy the route group + its helpers into a new file in this package.
2. Replace any module-level captures with explicit args to `register_*`.
3. In server.py, replace the original code with a single call:
       register_xxx_routes(api_router, db, ...)
4. Restart the backend, then run pytest + the testing agent to confirm
   no endpoints regressed.
"""

from .shop_parts import register_shop_parts_routes  # noqa: F401
from .safety import register_safety_routes  # noqa: F401
from .daily_reports import register_daily_reports_routes  # noqa: F401
from .equipment import register_equipment_routes  # noqa: F401

__all__ = [
    "register_shop_parts_routes",
    "register_safety_routes",
    "register_daily_reports_routes",
    "register_equipment_routes",
]

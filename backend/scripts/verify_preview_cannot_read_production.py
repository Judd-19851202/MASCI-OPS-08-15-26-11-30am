"""Wrapper · runs verify_isolation_suite.preview_cannot_read_production · PREPARED · operator runs after rotation."""
import sys, asyncio
sys.path.insert(0, "/app/backend/scripts")
from verify_isolation_suite import preview_cannot_read_production as _run
if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))

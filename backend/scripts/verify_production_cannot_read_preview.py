"""Wrapper · runs verify_isolation_suite.production_cannot_read_preview · PREPARED · operator runs after rotation."""
import sys, asyncio
sys.path.insert(0, "/app/backend/scripts")
from verify_isolation_suite import production_cannot_read_preview as _run
if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))

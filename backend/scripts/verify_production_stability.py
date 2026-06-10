"""Wrapper · runs verify_isolation_suite.production_stability · PREPARED · operator runs after rotation."""
import sys, asyncio
sys.path.insert(0, "/app/backend/scripts")
from verify_isolation_suite import production_stability as _run
if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))

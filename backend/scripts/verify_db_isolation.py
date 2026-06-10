"""Wrapper · runs verify_isolation_suite.db_isolation · PREPARED · operator runs after rotation."""
import sys, asyncio
sys.path.insert(0, "/app/backend/scripts")
from verify_isolation_suite import db_isolation as _run
if __name__ == "__main__":
    sys.exit(asyncio.run(_run()))

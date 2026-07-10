"""
TRACK 27.06 · R2 STORAGE LIFECYCLE GOVERNANCE
==============================================

Permanent storage-governance foundation for the platform.  Every object
in R2 gets a deterministic classification (VERIFIED_OWNER, VERIFIED_ORPHAN,
AMBIGUOUS, RETENTION_PROTECTED, BACKUP_PROTECTED, SYSTEM_RESERVED,
LEGAL_HOLD, HISTORICAL, PENDING, UNKNOWN) backed by evidence rows in Mongo.

This session ships Phase 1 (inventory) + Phase 2/3 (Mongo cross-ref) +
Phase 4 (classification) + Phase 6 (dry-run) + Phase 10 (health score) +
Phase 12 (tests). Delete engine is explicitly out of scope.

Modules
-------
- `inventory`      → paginated R2 bucket walker, persists `r2_inventory`.
- `references`     → extensible registry of Mongo collections that
                     legitimately reference R2 objects, plus a walker
                     that extracts R2 keys from their documents.
- `classification` → applies the strict "verified orphan" contract.
- `intelligence`   → executive stats (top prefixes, growth, cost).
- `health`         → Phase 10 Storage Health score aggregator.

Every function is read-only.  Nothing writes to R2, nothing deletes,
nothing repairs Mongo references.
"""

from .inventory import (
    IR2Client,
    run_inventory_scan,
    inventory_summary,
    latest_run_id,
)
from .references import (
    REFERENCE_SOURCES,
    ReferenceSource,
    scan_mongo_references,
    reference_summary,
)
from .classification import (
    CLASSIFICATIONS,
    classify_object,
    classify_all,
    classification_counts,
    ALLOWED_FOR_DELETION,
    DRY_RUN_REFUSAL_STATES,
)
from .intelligence import (
    top_prefixes,
    top_projects,
    largest_objects,
    growth_series,
    estimate_cost,
)
from .health import (
    compute_storage_health,
    health_summary,
)

__all__ = [
    "IR2Client",
    "run_inventory_scan",
    "inventory_summary",
    "latest_run_id",
    "REFERENCE_SOURCES",
    "ReferenceSource",
    "scan_mongo_references",
    "reference_summary",
    "CLASSIFICATIONS",
    "classify_object",
    "classify_all",
    "classification_counts",
    "ALLOWED_FOR_DELETION",
    "DRY_RUN_REFUSAL_STATES",
    "top_prefixes",
    "top_projects",
    "largest_objects",
    "growth_series",
    "estimate_cost",
    "compute_storage_health",
    "health_summary",
]

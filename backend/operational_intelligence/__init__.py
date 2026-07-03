"""Unified Operational Intelligence Engine · Track 19.40.

**Foundation for every operational briefing, digest, executive report,
dashboard, PDF, and email dispatched from the MASCI Operations Platform.**

One engine. Many intelligence products.

Zero-drift design
-----------------
- The Track 19.39 morning-digest collections (`morning_digest_recipients`
  and `morning_digest_audit`) are **reused** as the canonical recipient
  registry and audit ledger. Both already carry a `digest_type` column
  and were built additive-shaped for multi-product use.
- The existing `fsi_send_email` is the only email provider.
- The existing WeasyPrint helper is the only PDF renderer.
- Every product goes through `registry.OperationalIntelligenceProduct`
  contract; no product may implement its own scheduler, sender,
  renderer, or audit path.
"""

from .registry import (
    OperationalIntelligenceProduct,
    ProductStatus,
    register_product,
    get_product,
    list_products,
    require_product,
)
from .engine import (
    ENGINE_VERSION,
    compose,
    render_html,
    dispatch,
    dedupe_key_for,
    compute_trend,
    write_audit,
    write_history,
)
from .recipients import (
    list_recipients_for,
    list_groups,
    add_group,
    add_group_member,
    list_recipients,
    add_recipient,
    update_recipient,
    deactivate_recipient,
    bulk_import_recipients,
)
from .scheduler import (
    schedule_definition_for,
    scheduler_enabled,
)
from .score_model import (
    OperationalIntelligenceScore,
    Contributor,
    ATTENTION_LOW, ATTENTION_MEDIUM, ATTENTION_HIGH, ATTENTION_CRITICAL,
    attention_from_score,
    score_from_contributors,
    insufficient_data_score,
)
from .product_layout import (
    STANDARD_SECTION_ORDER,
    EMPTY_STATE_ITEM,
    build_standard_layout,
    not_applicable_section,
)

# Importing ``products`` at package load registers every intelligence
# product (2 implemented + 8 contract-registered) in the shared registry.
from . import products as _products  # noqa: F401

__all__ = [
    "ENGINE_VERSION",
    "OperationalIntelligenceProduct",
    "ProductStatus",
    "register_product", "get_product", "list_products", "require_product",
    "compose", "render_html", "dispatch",
    "dedupe_key_for", "compute_trend",
    "write_audit", "write_history",
    "list_recipients_for", "list_groups", "add_group", "add_group_member",
    "list_recipients", "add_recipient", "update_recipient",
    "deactivate_recipient", "bulk_import_recipients",
    "schedule_definition_for", "scheduler_enabled",
    "OperationalIntelligenceScore", "Contributor",
    "ATTENTION_LOW", "ATTENTION_MEDIUM", "ATTENTION_HIGH", "ATTENTION_CRITICAL",
    "attention_from_score", "score_from_contributors", "insufficient_data_score",
    "STANDARD_SECTION_ORDER", "EMPTY_STATE_ITEM",
    "build_standard_layout", "not_applicable_section",
]

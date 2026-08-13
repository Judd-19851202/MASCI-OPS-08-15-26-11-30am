"""Known-legacy queue transport-metadata sanitizer (P0-QUEUE-2026-08-13).

Owner directive: do NOT globally weaken request validation. Strict models must
keep rejecting genuinely unknown BUSINESS fields. But a small, explicitly
enumerated set of CLIENT TRANSPORT metadata keys were historically written into
device-queued submission bodies and must be sanitized (stripped) BEFORE
canonical business validation so days-old queued records can finally sync.

Semantics achieved when a model uses `extra="forbid"` + the before-validator
returned by :func:`legacy_transport_before_validator`:

    KNOWN LEGACY TRANSPORT FIELD  -> silently stripped (safe)
    UNKNOWN BUSINESS FIELD        -> still rejected truthfully (extra_forbidden)

The canonical idempotency value travels on the ``Idempotency-Key`` HTTP header,
so these body helpers are provably redundant transport metadata that carry no
operator-entered business information.
"""
from __future__ import annotations

from typing import Any

# Explicit allowlist. Add a key here ONLY once it is proven to be client/queue
# transport metadata (never operator-entered business data).
KNOWN_LEGACY_TRANSPORT_FIELDS: frozenset[str] = frozenset(
    {
        # EmployeeCombo inline "request to add employee" idempotency helper.
        # Canonical idempotency is the Idempotency-Key header. TRACK 15.60.
        "_track_15_60_client_idempotency_key",
    }
)


def strip_known_legacy_transport(data: Any) -> Any:
    """Return `data` with ONLY known legacy transport keys removed.

    Non-dict inputs pass through unchanged. The input is never mutated in
    place (a shallow copy is returned when a strip occurs).
    """
    if not isinstance(data, dict):
        return data
    present = KNOWN_LEGACY_TRANSPORT_FIELDS.intersection(data.keys())
    if not present:
        return data
    cleaned = dict(data)
    for key in present:
        cleaned.pop(key, None)
    return cleaned


def legacy_transport_before_validator(cls, data: Any) -> Any:  # noqa: ARG001
    """Pydantic v2 ``mode="before"`` model validator.

    Runs BEFORE field validation and BEFORE the ``extra="forbid"`` check, so
    known transport keys are removed while any remaining unknown field is still
    rejected by the model's strict config.
    """
    return strip_known_legacy_transport(data)

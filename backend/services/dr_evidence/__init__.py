"""TRACK 24.13 · Daily Report Evidence Intelligence Engine.

Public surface for the Daily Report Evidence Intelligence subsystem.

The evidence engine converts a saved Daily Report + its uploaded
attachments + its analyzed photo intelligence into a canonical
:class:`EvidenceManifest` that the AI summary engine and downstream
consumers (PDF, PM email, DR viewer, archive, ODS/KPI) can trust.

Design principles
-----------------
* **Grounded only** — the manifest is the ONLY input the AI is
  permitted to reason over. Every fact it emits must trace back to a
  manifest field. Anything outside the manifest is a hallucination.
* **Honest failure** — every extraction records its status: extracted,
  unsupported, failed, too_large, encrypted, corrupt, scanned_pdf_no_text.
  The AI is told to treat metadata-only entries as metadata-only.
* **Idempotent + cached** — every extraction is keyed by a file hash;
  reruns are free. See :mod:`.extract`.
* **Bounded** — every extractor caps output size + row count + page
  count so a 200 MB spreadsheet cannot blow up token budgets.
* **Non-blocking** — extraction failures NEVER block DR submit or PDF
  render; the manifest degrades gracefully to `metadata_only`.
"""
from __future__ import annotations

from .extract import (  # noqa: F401
    EXTRACTION_STATUSES,
    ExtractionResult,
    extract_attachment,
    hash_bytes,
)
from .manifest import (  # noqa: F401
    EvidenceManifest,
    build_manifest,
    manifest_hash,
    manifest_to_ai_bundle,
)
from .materials import (  # noqa: F401
    NormalizedTicket,
    normalize_ticket_row,
    reconcile_tickets,
)

__all__ = [
    "EXTRACTION_STATUSES",
    "EvidenceManifest",
    "ExtractionResult",
    "NormalizedTicket",
    "build_manifest",
    "extract_attachment",
    "hash_bytes",
    "manifest_hash",
    "manifest_to_ai_bundle",
    "normalize_ticket_row",
    "reconcile_tickets",
]

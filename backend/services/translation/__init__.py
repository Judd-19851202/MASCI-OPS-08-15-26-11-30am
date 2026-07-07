"""TRACK 24.3 · Spanish → English canonical translation service.

Called from POST /api/translate/dr-v3-freetext at Daily Report V3 submit
time when the operator authored the DR in Spanish. Translates natural-
language free-text field values to English so the DR that lands in the
database, ODS, AI evidence bundle, PDF, and email is 100 % English —
regardless of the UI language the operator used.

Fail-closed on any error. Never returns Spanish where English was
expected.
"""
from .service import translate_es_to_en_bulk, TranslationResult

__all__ = ["translate_es_to_en_bulk", "TranslationResult"]

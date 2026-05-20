"""
iter280 · Sequence #8 knowledge i18n closure regression test.

Mirrors the iter279 pattern. Locks in that all 19 knowledge-section
articles flagged by the iter277 pre-audit now carry full Spanish
translations and that the merge into _ARTICLES at import time works.
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import guidance  # noqa: F401 — triggers import-time merge
from guidance import content as guidance_content
from guidance import translations_es as guidance_es


KNOWLEDGE_I18N_CLOSURE_IDS = {
    "field-project-scope",
    "pm-coordination",
    "hr-audit-trail",
    "dispatch-accuracy-why",
    "connect-incident-to-audit",
    "connect-admin-controls",
    "shop-operator-responsibilities",
    "hr-cross-portal-reads",
    "dispatch-field-coordination",
    "shop-downtime-logic",
    "pm-cross-project-visibility",
    "connect-pm-field-review",
    "admin-governance-why",
    "safety-escalation-chain",
    "connect-field-to-payroll",
    "connect-equipment-lifecycle",
    "safety-photo-quality",
    "safety-near-miss-importance",
    "connect-shop-to-dispatch",
}


def test_all_19_knowledge_articles_have_es_entries():
    missing = [
        aid for aid in KNOWLEDGE_I18N_CLOSURE_IDS
        if aid not in guidance_es.TRANSLATIONS_ES
    ]
    assert not missing, f"ES entries missing for: {missing}"


def test_each_es_entry_has_title_summary_and_body():
    incomplete = []
    for aid in KNOWLEDGE_I18N_CLOSURE_IDS:
        e = guidance_es.TRANSLATIONS_ES.get(aid, {})
        if not e.get("title_es"):
            incomplete.append((aid, "title_es"))
        if not e.get("summary_es"):
            incomplete.append((aid, "summary_es"))
        body = e.get("body_es")
        if not body or not isinstance(body, list):
            incomplete.append((aid, "body_es"))
    assert not incomplete, f"Incomplete ES entries: {incomplete}"


def test_body_structure_matches_en():
    """Block count + type per index must match EN exactly."""
    arts = {a["id"]: a for a in guidance_content._ARTICLES}
    mismatches = []
    for aid in KNOWLEDGE_I18N_CLOSURE_IDS:
        en_body = arts[aid].get("body", []) or []
        es_body = guidance_es.TRANSLATIONS_ES[aid].get("body_es", []) or []
        if len(en_body) != len(es_body):
            mismatches.append((aid, "count", len(en_body), len(es_body)))
            continue
        for i, (eb, sb) in enumerate(zip(en_body, es_body)):
            en_type = eb.get("type") if isinstance(eb, dict) else None
            es_type = sb.get("type") if isinstance(sb, dict) else None
            if en_type != es_type:
                mismatches.append((aid, i, en_type, es_type))
    assert not mismatches, f"Structure mismatch: {mismatches}"


def test_articles_received_translation_at_import_time():
    arts = {a["id"]: a for a in guidance_content._ARTICLES}
    not_merged = []
    for aid in KNOWLEDGE_I18N_CLOSURE_IDS:
        a = arts[aid]
        if not a.get("title_es") or not a.get("body_es"):
            not_merged.append(aid)
    assert not not_merged, f"Articles missing merged ES: {not_merged}"


def test_total_es_count_grew_by_19():
    """50 (pre) + 33 (iter279) + 19 (iter280) = at least 102 entries.
    Inequality lets later iterations grow the dict without breaking the lock."""
    assert len(guidance_es.TRANSLATIONS_ES) >= 102, \
        f"Expected >=102 ES entries, got {len(guidance_es.TRANSLATIONS_ES)}"


def test_no_stale_terminology_in_new_es_entries():
    stale = [
        re.compile(r"\bToolbox Talks?", re.I),
        re.compile(r"\bCrew Hub\b", re.I),
        re.compile(r"\bcharla\s+de\s+seguridad\b", re.I),
    ]

    def flatten(blocks):
        if not isinstance(blocks, list): return ""
        out = []
        for blk in blocks:
            if isinstance(blk, dict):
                for v in blk.values():
                    if isinstance(v, str): out.append(v)
                    elif isinstance(v, list):
                        for it in v:
                            if isinstance(it, str): out.append(it)
                            elif isinstance(it, dict):
                                out.extend(s for s in it.values() if isinstance(s, str))
        return "\n".join(out)

    hits = []
    for aid in KNOWLEDGE_I18N_CLOSURE_IDS:
        e = guidance_es.TRANSLATIONS_ES[aid]
        text = "\n".join([e.get("title_es",""), e.get("summary_es",""), flatten(e.get("body_es",[]))])
        for pat in stale:
            m = pat.search(text)
            if m:
                hits.append((aid, pat.pattern, m.group()))
    assert not hits, f"Stale terminology in iter280 ES: {hits}"

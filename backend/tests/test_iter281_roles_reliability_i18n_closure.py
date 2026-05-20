"""
iter281 · Sequence #8 roles + reliability i18n closure regression test.

Locks in the final 4 articles flagged by the iter277 pre-audit as
"minor (i18n only)" outside the portals/knowledge clusters:
  - role-foreman · role-hr · role-superintendent (roles section)
  - why-backups (reliability section)
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import guidance  # noqa: F401 — import-time merge
from guidance import content as guidance_content
from guidance import translations_es as guidance_es


ITER281_CLOSURE_IDS = {
    "role-foreman",
    "role-hr",
    "role-superintendent",
    "why-backups",
}


def test_all_4_articles_have_es_entries():
    missing = [
        aid for aid in ITER281_CLOSURE_IDS
        if aid not in guidance_es.TRANSLATIONS_ES
    ]
    assert not missing, f"ES entries missing for: {missing}"


def test_each_es_entry_has_all_three_fields():
    incomplete = []
    for aid in ITER281_CLOSURE_IDS:
        e = guidance_es.TRANSLATIONS_ES.get(aid, {})
        if not e.get("title_es"):
            incomplete.append((aid, "title_es"))
        if not e.get("summary_es"):
            incomplete.append((aid, "summary_es"))
        if not e.get("body_es") or not isinstance(e.get("body_es"), list):
            incomplete.append((aid, "body_es"))
    assert not incomplete, f"Incomplete: {incomplete}"


def test_body_structure_matches_en():
    arts = {a["id"]: a for a in guidance_content._ARTICLES}
    mismatches = []
    for aid in ITER281_CLOSURE_IDS:
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
    not_merged = [
        aid for aid in ITER281_CLOSURE_IDS
        if not arts[aid].get("title_es") or not arts[aid].get("body_es")
    ]
    assert not not_merged, f"Not merged: {not_merged}"


def test_total_es_count_grew_by_4():
    """50 + 33 + 19 + 4 = at least 106 entries. Forward-compatible inequality."""
    assert len(guidance_es.TRANSLATIONS_ES) >= 106, \
        f"Expected >=106 ES entries, got {len(guidance_es.TRANSLATIONS_ES)}"


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
    for aid in ITER281_CLOSURE_IDS:
        e = guidance_es.TRANSLATIONS_ES[aid]
        text = "\n".join([e.get("title_es",""), e.get("summary_es",""), flatten(e.get("body_es",[]))])
        for pat in stale:
            m = pat.search(text)
            if m: hits.append((aid, pat.pattern, m.group()))
    assert not hits, f"Stale terminology: {hits}"

"""
iter279 · Sequence #8 portals i18n closure regression test.

Locks in that the 33 portals-section articles flagged by the iter277
pre-audit ("minor (i18n only)" + "moderate (i18n only)") now carry full
Spanish translations (title_es + summary_es + body_es) and that the
merge into _ARTICLES at import time still works.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import guidance  # noqa: F401 — triggers import-time merge
from guidance import content as guidance_content
from guidance import translations_es as guidance_es


PORTALS_I18N_CLOSURE_IDS = {
    "portal-leadership",
    "pm-reporting-workflows",
    "field-coaching-documentation",
    "field-equipment-checkout",
    "shop-maintenance-coordination",
    "admin-system-health",
    "admin-audit-forensics",
    "pm-labor-documentation",
    "pm-project-review-cadence",
    "dispatch-availability-management",
    "field-incident-escalation",
    "safety-training-compliance",
    "safety-fire-extinguishers",
    "admin-data-portability",
    "safety-audits-workflow",
    "field-writeup-authoring",
    "admin-role-templates",
    "shop-equipment-return",
    "admin-sentry-observability",
    "dispatch-holds-transfers",
    "shop-damage-reporting",
    "admin-backup-restore",
    "hr-writeups-correctives",
    "admin-user-management",
    "dispatch-equipment-movement",
    "shop-failed-preop-workflow",
    "hr-offboarding",
    "safety-corrective-actions-workflow",
    "shop-preop-deep",
    "hr-time-verification-deep",
    "field-daily-report-howto",
    "safety-incident-investigation",
    "hr-onboarding-new-hire",
}


def test_all_33_portals_articles_have_es_entries():
    missing = [
        aid for aid in PORTALS_I18N_CLOSURE_IDS
        if aid not in guidance_es.TRANSLATIONS_ES
    ]
    assert not missing, f"ES entries missing for: {missing}"


def test_each_es_entry_has_title_summary_and_body():
    incomplete = []
    for aid in PORTALS_I18N_CLOSURE_IDS:
        entry = guidance_es.TRANSLATIONS_ES.get(aid, {})
        if not entry.get("title_es"):
            incomplete.append((aid, "title_es"))
        if not entry.get("summary_es"):
            incomplete.append((aid, "summary_es"))
        body = entry.get("body_es")
        if not body or not isinstance(body, list):
            incomplete.append((aid, "body_es"))
    assert not incomplete, f"Incomplete ES entries: {incomplete}"


def test_body_structure_matches_en_block_count():
    """ES body block count must match EN block count for each article.
    Mismatched block counts indicate translation lost or invented structure."""
    arts = {a["id"]: a for a in guidance_content._ARTICLES}
    mismatches = []
    for aid in PORTALS_I18N_CLOSURE_IDS:
        en_body = arts[aid].get("body", []) or []
        es_body = guidance_es.TRANSLATIONS_ES[aid].get("body_es", []) or []
        if len(en_body) != len(es_body):
            mismatches.append((aid, len(en_body), len(es_body)))
    assert not mismatches, f"Block count mismatch (id, en_count, es_count): {mismatches}"


def test_block_types_match_en():
    """The `type` of each ES block must match the EN block at the same index."""
    arts = {a["id"]: a for a in guidance_content._ARTICLES}
    mismatches = []
    for aid in PORTALS_I18N_CLOSURE_IDS:
        en_body = arts[aid].get("body", []) or []
        es_body = guidance_es.TRANSLATIONS_ES[aid].get("body_es", []) or []
        for i, (eb, sb) in enumerate(zip(en_body, es_body)):
            en_type = eb.get("type") if isinstance(eb, dict) else None
            es_type = sb.get("type") if isinstance(sb, dict) else None
            if en_type != es_type:
                mismatches.append((aid, i, en_type, es_type))
    assert not mismatches, f"Block type mismatch (id, idx, en, es): {mismatches}"


def test_articles_received_translation_at_import_time():
    """guidance.__init__ should have merged title_es / body_es onto each article."""
    arts = {a["id"]: a for a in guidance_content._ARTICLES}
    not_merged = []
    for aid in PORTALS_I18N_CLOSURE_IDS:
        a = arts[aid]
        if not a.get("title_es") or not a.get("body_es"):
            not_merged.append(aid)
    assert not not_merged, f"Articles missing merged ES: {not_merged}"


def test_total_es_count_grew_by_33():
    """Sanity: 50 (pre-iter279) + 33 (iter279) = at least 83 entries.
    Inequality lets later iterations grow the dict without breaking the lock."""
    assert len(guidance_es.TRANSLATIONS_ES) >= 83, \
        f"Expected >=83 ES entries, got {len(guidance_es.TRANSLATIONS_ES)}"


def test_no_stale_terminology_in_new_es_entries():
    """The iter278 stale-term ban applies to the new entries too."""
    import re
    stale_patterns = [
        re.compile(r"\bToolbox Talks?", re.IGNORECASE),
        re.compile(r"\bCrew Hub\b", re.IGNORECASE),
        re.compile(r"\bcharla\s+de\s+seguridad\b", re.IGNORECASE),
    ]

    def flatten(blocks):
        if isinstance(blocks, list):
            out = []
            for blk in blocks:
                if isinstance(blk, dict):
                    for v in blk.values():
                        if isinstance(v, str):
                            out.append(v)
                        elif isinstance(v, list):
                            for it in v:
                                if isinstance(it, str):
                                    out.append(it)
                                elif isinstance(it, dict):
                                    out.extend(s for s in it.values() if isinstance(s, str))
            return "\n".join(out)
        return ""

    hits = []
    for aid in PORTALS_I18N_CLOSURE_IDS:
        e = guidance_es.TRANSLATIONS_ES[aid]
        text = "\n".join([
            e.get("title_es", ""), e.get("summary_es", ""),
            flatten(e.get("body_es", [])),
        ])
        for pat in stale_patterns:
            m = pat.search(text)
            if m:
                hits.append((aid, pat.pattern, m.group()))
    assert not hits, f"Stale terminology found in new ES: {hits}"

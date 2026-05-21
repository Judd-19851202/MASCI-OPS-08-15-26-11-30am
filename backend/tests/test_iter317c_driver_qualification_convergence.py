"""
iter317-C · Driver Qualification convergence regression invariants.

Locks the deliverables:
  • 5 new articles (section="trucking") covering CDL vs Approved
    Company Driver · medical card cadence · tanker endorsement ·
    dashboard interpretation · restrictions & escalation.
  • Coaching gap closures completing canonical-4 on three families
    (cdl-vs-approved · expirations · restrictions) + two NEW
    families (medical-card · tanker).
  • Bilingual parity for every new tip + every new article.
  • Operator-mandated tone discipline (no LMS/corporate phrasing).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT = REPO_ROOT / "backend/guidance/content.py"
TIPS_EN = REPO_ROOT / "backend/guidance/tips.py"
TIPS_ES = REPO_ROOT / "backend/guidance/tips_es.py"
TRANS_ES = REPO_ROOT / "backend/guidance/translations_es.py"


NEW_ARTICLES = (
    "driver-cdl-vs-approved-company-driver",
    "driver-medical-card-and-expirations",
    "driver-tanker-and-endorsements",
    "driver-qualification-dashboard-understanding",
    "driver-restrictions-and-escalation",
)
ALLOWED_SCOPES = {"hr", "safety", "dispatch", "admin"}

EXPECTED_FAMILY_COUNTS = {
    "driver-qualification.cdl-vs-approved": 4,
    "driver-qualification.expirations": 4,
    "driver-qualification.restrictions": 4,
    "driver-qualification.medical-card": 3,
    "driver-qualification.tanker": 2,
}

BANNED_PHRASES = (
    "best practices",
    "empower",
    "journey",
    "stakeholders",
    "culture of",
    "training module",
    "learning module",
    "compliance pathway",
    "compliance posture",
)


def _load_articles():
    import sys
    backend = str(REPO_ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from guidance import _articles_by_id
    return _articles_by_id


def _load_tips():
    import sys
    backend = str(REPO_ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from guidance.tips import all_tips
    return all_tips()


def _body_text(blocks):
    parts = []
    for b in blocks or []:
        if isinstance(b, dict):
            if b.get("text"):
                parts.append(str(b["text"]))
            for it in (b.get("items") or []):
                parts.append(str(it))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------


def test_iter317c_five_articles_present():
    articles = _load_articles()
    for aid in NEW_ARTICLES:
        assert aid in articles, f"missing iter317-C article: {aid}"
        assert articles[aid].get("section") == "trucking", (
            f"{aid}: section must be 'trucking'"
        )
        scopes = set(articles[aid].get("scopes") or [])
        assert scopes == ALLOWED_SCOPES, (
            f"{aid}: scopes must be {sorted(ALLOWED_SCOPES)}, got {sorted(scopes)}"
        )


def test_iter317c_articles_have_bilingual_body():
    articles = _load_articles()
    for aid in NEW_ARTICLES:
        en_blocks = articles[aid].get("body") or []
        es_blocks = articles[aid].get("body_es") or []
        assert len(en_blocks) >= 4, f"{aid}: too few EN body blocks"
        assert len(es_blocks) == len(en_blocks), (
            f"{aid}: ES body block count ({len(es_blocks)}) "
            f"must mirror EN ({len(en_blocks)})"
        )
        assert articles[aid].get("title_es"), f"{aid}: missing title_es"
        assert articles[aid].get("summary_es"), f"{aid}: missing summary_es"


def test_iter317c_articles_cross_link_each_other():
    """The 5 articles form a small operational ring — each one's
    `related` list should reference at least 2 others in the set."""
    articles = _load_articles()
    new_set = set(NEW_ARTICLES)
    for aid in NEW_ARTICLES:
        related = set(articles[aid].get("related") or [])
        overlap = related & new_set
        assert len(overlap) >= 2, (
            f"{aid}: must `related`-link to at least 2 other "
            f"iter317-C articles; found {sorted(overlap)}"
        )


def test_iter317c_trucking_section_registered():
    """The new `trucking` section is declared in SECTIONS so the
    Guidance Center integrity check passes."""
    src = CONTENT.read_text()
    assert '{"id": "trucking"' in src, (
        "SECTIONS must declare 'trucking' section"
    )


# ---------------------------------------------------------------------------
# Coaching gap closures + 2 new slices
# ---------------------------------------------------------------------------


def test_iter317c_coaching_families_at_expected_counts():
    tips = _load_tips()
    counts = {}
    for t in tips:
        fk = t.get("form_key")
        if fk in EXPECTED_FAMILY_COUNTS:
            counts[fk] = counts.get(fk, 0) + 1
    for fk, expected in EXPECTED_FAMILY_COUNTS.items():
        assert counts.get(fk, 0) >= expected, (
            f"{fk}: expected at least {expected} tips, "
            f"got {counts.get(fk, 0)}"
        )


def test_iter317c_canonical_4_completed_for_three_families():
    """cdl-vs-approved · expirations · restrictions must now carry
    all four canonical kinds (why · mistake · next · escalate)."""
    tips = _load_tips()
    for fk in (
        "driver-qualification.cdl-vs-approved",
        "driver-qualification.expirations",
        "driver-qualification.restrictions",
    ):
        kinds = {t["kind"] for t in tips if t.get("form_key") == fk}
        for required in ("why", "mistake", "next", "escalate"):
            assert required in kinds, (
                f"{fk}: missing canonical-4 kind '{required}' "
                f"(have {sorted(kinds)})"
            )


def test_iter317c_medical_card_and_tanker_bilingual():
    tips = _load_tips()
    new_families = {
        "driver-qualification.medical-card",
        "driver-qualification.tanker",
    }
    for t in tips:
        if t.get("form_key") not in new_families:
            continue
        title_es = (t.get("title_es") or "").strip()
        body_es = (t.get("body_es") or "").strip()
        assert title_es and body_es, (
            f"{t['form_key']}/{t['kind']} missing ES translation"
        )


def test_iter317c_coaching_tone_discipline():
    """Banned-phrase scan on the iter317-C tip families."""
    tips = _load_tips()
    hits = []
    for t in tips:
        fk = t.get("form_key", "")
        if fk not in EXPECTED_FAMILY_COUNTS:
            continue
        body = (t.get("body") or "").lower()
        title = (t.get("title") or "").lower()
        for banned in BANNED_PHRASES:
            if banned in body or banned in title:
                hits.append((fk, t.get("kind"), banned))
    assert not hits, f"iter317-C tone violations: {hits}"


def test_iter317c_articles_tone_discipline():
    articles = _load_articles()
    hits = []
    for aid in NEW_ARTICLES:
        en = _body_text(articles[aid].get("body")).lower()
        es = _body_text(articles[aid].get("body_es")).lower()
        for banned in BANNED_PHRASES:
            if banned in en:
                hits.append((aid, "EN", banned))
            if banned in es:
                hits.append((aid, "ES", banned))
    assert not hits, f"iter317-C article tone violations: {hits}"


# ---------------------------------------------------------------------------
# Operational anchors — verify key terms appear in EN+ES
# ---------------------------------------------------------------------------


def test_iter317c_operational_anchors_present():
    """Key operational terms operator named — must appear at least
    once across the iter317-C content."""
    articles = _load_articles()
    en_blob = " ".join(_body_text(articles[a].get("body")) for a in NEW_ARTICLES)
    es_blob = " ".join(_body_text(articles[a].get("body_es")) for a in NEW_ARTICLES)
    # Operator-named anchors
    for term in ("FMCSA 391.45", "tanker", "dewatering", "MVR", "CMV"):
        assert term in en_blob, f"EN content missing operational anchor '{term}'"
    for term_es in ("FMCSA 391.45", "tanque", "dewatering", "MVR", "CMV"):
        assert term_es in es_blob, f"ES content missing operational anchor '{term_es}'"


def test_iter317c_marker_comments_for_grep_discoverability():
    for path in (CONTENT, TIPS_EN, TIPS_ES, TRANS_ES):
        assert "iter317-C" in path.read_text(), (
            f"{path.name} must keep an iter317-C marker comment"
        )

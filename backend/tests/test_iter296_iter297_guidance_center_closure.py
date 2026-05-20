"""
iter296 + iter297 regression tests · Guidance Center visibility-first
audit closure bundle.

iter296 — shell-chrome i18n closure on OperationalGuidanceCenter.jsx:
  - 11 previously-hardcoded EN strings now wrapped in `t()`
  - matching ES entries present in `/app/frontend/src/lib/i18n.js`
  - `Related guidance` ternary replaced with standard `t()` pattern

iter297 — operational `why-*` knowledge ES translation pass:
  - 7 `why-*` knowledge articles now carry `title_es` + `summary_es` +
    `body_es` with EN/ES block-count parity
  - registered via `translations_es_iter297.py` merged into TRANSLATIONS_ES
  - operational tone discipline (no LMS, no corporate framing)

Both iterations are bilingual-integrity + visibility-first closure work
under the Platform Operational Maturity Governance Matrix. No scope
widening permitted in this test surface.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDANCE_CENTER_JSX = REPO_ROOT / "frontend/src/pages/guidance/OperationalGuidanceCenter.jsx"
I18N_JS = REPO_ROOT / "frontend/src/lib/i18n.js"

ITER297_TARGETS = [
    "why-daily-reports",
    "why-photos",
    "why-incidents",
    "why-corrective-actions",
    "why-equipment-accountability",
    "why-time-verification",
    "why-audit-logs",
]

# Operational anchors that must survive translation (canonical terminology).
ITER297_ES_ANCHORS = {
    "why-daily-reports":            ["Reporte Diario", "cuadrilla"],
    "why-photos":                   ["fotos", "evidencia" if False else "verificable"],
    "why-incidents":                ["incidente", "casi-accidente"],
    "why-corrective-actions":       ["Acción Correctiva", "seguimiento"],
    "why-equipment-accountability": ["equipo", "responsabilidad"],
    "why-time-verification":        ["nómina", "auditoría"],
    "why-audit-logs":               ["auditoría", "quién hizo qué"],
}

# Strings the iter296 closure committed to make translatable.
ITER296_REQUIRED_ES_KEYS = [
    "Search results",
    "All guidance",
    "No matching guidance available for your access level.",
    "Not available",
    "This guidance isn't available for your access level.",
    "Back to Guidance",
    "Section",
    "No articles in this section for your access level.",
    "Related guidance",
]


# ── iter297 backend translation regression ───────────────────────────

def _load_articles():
    from backend.guidance import content  # type: ignore  # noqa
    return content.all_articles()


@pytest.fixture(scope="module")
def articles_by_id():
    # Run from /app so the `backend.guidance` namespace resolves.
    import sys
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from backend.guidance import content
    return {a["id"]: a for a in content.all_articles()}


@pytest.mark.parametrize("aid", ITER297_TARGETS)
def test_iter297_translation_present(articles_by_id, aid):
    a = articles_by_id[aid]
    assert a.get("title_es"), f"{aid} missing title_es"
    assert a.get("summary_es"), f"{aid} missing summary_es"
    assert isinstance(a.get("body_es"), list) and a["body_es"], f"{aid} missing body_es"


@pytest.mark.parametrize("aid", ITER297_TARGETS)
def test_iter297_block_count_parity(articles_by_id, aid):
    a = articles_by_id[aid]
    assert len(a["body_es"]) == len(a["body"]), (
        f"{aid} body_es block count {len(a['body_es'])} != body {len(a['body'])}"
    )


@pytest.mark.parametrize("aid", ITER297_TARGETS)
def test_iter297_block_type_parity(articles_by_id, aid):
    a = articles_by_id[aid]
    en_types = [b.get("type") for b in a["body"]]
    es_types = [b.get("type") for b in a["body_es"]]
    assert en_types == es_types, f"{aid} block type mismatch: EN={en_types} ES={es_types}"


@pytest.mark.parametrize("aid", ITER297_TARGETS)
def test_iter297_operational_anchors_present(articles_by_id, aid):
    a = articles_by_id[aid]
    haystack = a["title_es"] + " " + a["summary_es"]
    for b in a["body_es"]:
        haystack += " " + (b.get("text") or "")
        for item in (b.get("items") or []):
            haystack += " " + item
    for anchor in ITER297_ES_ANCHORS[aid]:
        assert anchor.lower() in haystack.lower(), (
            f"{aid} missing operational anchor in ES: '{anchor}'"
        )


@pytest.mark.parametrize("aid", ITER297_TARGETS)
def test_iter297_no_lms_drift_in_es(articles_by_id, aid):
    a = articles_by_id[aid]
    haystack = (a["title_es"] + " " + a["summary_es"]).lower()
    for b in a["body_es"]:
        haystack += " " + (b.get("text") or "").lower()
        for item in (b.get("items") or []):
            haystack += " " + item.lower()
    # LMS / corporate / motivational drift bans (Spanish equivalents).
    BANNED = [
        "mejores prácticas",
        "empoderar",
        "sinergia",
        "holístico",
        "mentalidad de crecimiento",
        "iniciativa estratégica",
        "ecosistema de aprendizaje",
        "cultura de excelencia",
    ]
    for term in BANNED:
        assert term not in haystack, f"{aid} ES contains banned LMS/corporate term: '{term}'"


def test_iter297_translations_module_importable():
    from backend.guidance import translations_es_iter297 as mod  # noqa
    assert isinstance(mod.EXTRA_ES, dict)
    assert set(mod.EXTRA_ES.keys()) == set(ITER297_TARGETS), (
        "iter297 EXTRA_ES keys drifted from the audit-approved 7-article scope"
    )


def test_iter297_merged_into_translations_es():
    from backend.guidance import translations_es as tes
    for aid in ITER297_TARGETS:
        assert aid in tes.TRANSLATIONS_ES, f"{aid} not merged into TRANSLATIONS_ES"


def test_iter297_section_is_knowledge_only(articles_by_id):
    """Bounded-scope guard — iter297 must not silently translate articles
    in other sections. The audit-approved scope is knowledge `why-*` only."""
    for aid in ITER297_TARGETS:
        assert articles_by_id[aid].get("section") == "knowledge", (
            f"{aid} unexpectedly in non-knowledge section"
        )


# ── iter296 frontend chrome regression ──────────────────────────────

def _i18n_text():
    return I18N_JS.read_text(encoding="utf-8")


def _jsx_text():
    return GUIDANCE_CENTER_JSX.read_text(encoding="utf-8")


@pytest.mark.parametrize("key", ITER296_REQUIRED_ES_KEYS)
def test_iter296_es_key_present(key):
    text = _i18n_text()
    # Look for the key as a literal JSON-like string entry: "Key": "..."
    pattern = re.compile(r'"%s"\s*:\s*"[^"]+"' % re.escape(key))
    assert pattern.search(text), f"i18n.js missing ES entry for: {key!r}"


def test_iter296_jsx_no_hardcoded_shell_titles():
    jsx = _jsx_text()
    # The committed closure removed these literal Shell title props.
    BANNED_LITERALS = [
        '<Shell title="Search results">',
        '<Shell title="Not available">',
        '|| "Section"',
    ]
    for lit in BANNED_LITERALS:
        assert lit not in jsx, f"iter296 regression: hardcoded shell string survived: {lit!r}"


def test_iter296_jsx_no_hardcoded_back_button_label():
    jsx = _jsx_text()
    # Article reader back button — must now be `{t("Back")}`, not plain `Back`.
    assert "<ChevronLeft className=\"w-4 h-4\" /> Back\n" not in jsx, (
        "iter296 regression: article reader back button label not wrapped in t()"
    )
    assert '<ChevronLeft className="w-4 h-4" /> {t("Back")}' in jsx, (
        "iter296 expected `t(\"Back\")` wrapping in article reader back button"
    )


def test_iter296_jsx_no_hardcoded_all_guidance_label():
    jsx = _jsx_text()
    # Both occurrences (search-back + section-back) must be t("All guidance").
    assert ' All guidance\n        ' not in jsx, (
        "iter296 regression: 'All guidance' literal still appears in JSX"
    )
    assert jsx.count('{t("All guidance")}') >= 2, (
        "iter296 expected at least 2 `t(\"All guidance\")` call sites"
    )


def test_iter296_related_guidance_uses_standard_t_pattern():
    jsx = _jsx_text()
    # The pre-iter296 inline ternary must be gone.
    assert 'lang === "es" ? "Guía relacionada" : "Related guidance"' not in jsx, (
        "iter296 regression: Related-guidance ternary not normalized to t() pattern"
    )
    assert '{t("Related guidance")}' in jsx, (
        "iter296 expected `t(\"Related guidance\")` after ternary normalization"
    )


def test_iter296_jsx_no_hardcoded_empty_state_strings():
    jsx = _jsx_text()
    assert "No matching guidance available for your access level.\n" not in jsx, (
        "iter296 regression: search empty-state string not wrapped"
    )
    assert "No articles in this section for your access level.</div>" not in jsx, (
        "iter296 regression: section empty-state string not wrapped"
    )
    assert "This guidance isn't available for your access level.\n" not in jsx, (
        "iter296 regression: article-not-found string not wrapped"
    )


def test_iter296_back_to_guidance_uses_t():
    jsx = _jsx_text()
    assert '{t("Back to Guidance")}' in jsx, (
        "iter296 expected `t(\"Back to Guidance\")` wrapping on the Not-Available shell"
    )


# ── matrix-truth · combined milestone guard ──────────────────────────

def test_iter296_iter297_no_remaining_knowledge_why_es_gap(articles_by_id):
    """Combined milestone: after iter297 the knowledge `why-*` cluster
    is fully ES-translated. If a future iteration adds a new `why-*`
    knowledge article without ES, this test fails loudly."""
    missing = [
        a["id"] for a in articles_by_id.values()
        if a.get("section") == "knowledge"
        and a["id"].startswith("why-")
        and not a.get("title_es")
    ]
    assert missing == [], (
        f"Knowledge `why-*` ES gap re-opened after iter297: {missing}"
    )

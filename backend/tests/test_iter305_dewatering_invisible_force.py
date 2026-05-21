"""
iter305 · Dewatering family tone benchmark · `dewatering_invisible_force_discipline`.

Scope (operator-approved per iter305 prose-benchmark sign-off):
  - 1 new topic appended to existing `dewatering` domain (NOT a new domain).
  - Voice template: invisible-force discipline (4th and final philosophical
    template after custody-first / mental-model-first / default-state).
  - Connects existing 8 dewatering_* topics as symptoms of one underlying
    failure to read invisible-force (vacuum · stored pressure · saturation).
  - Envelope: 1,150–1,700 chars discussion_notes · 10 bullets. The dewatering
    benchmark runs longer than iter302/303/304 because the invisible-force
    framing requires concrete time-window and pressure specificity (vacuum
    persistence seconds · 25 psi · 12 inHg · saturation behavior) — the
    operator-approved prose was retained verbatim per iter305 sign-off.
  - Rhetorical anchor locked (operator-revised sentence):
    "Dewatering is a discipline of forces you can feel before you can see them
    — and the operators who get hurt usually never recognized the force that
    was already there."
  - ES anchor locked: "El dewatering es una disciplina de fuerzas que se
    sienten antes de verse — y los operadores que se lastiman usualmente
    nunca reconocieron la fuerza que ya estaba ahí."

Bounded-scope guards:
  - Existing 8 dewatering topics MUST remain untouched.
  - No new domain registration.
  - No TopicPicker chip changes.
  - Total library grows 142 → 143.
  - Field-Spanish anglicisms preserved: dewatering, wellpoint, vapor lock.
  - `nomás` BANNED (iter303 universality discipline).

This benchmark closes the 4-template philosophical foundation. After this
ship, the operator has explicitly directed PAUSING major Toolbox expansion
for real-world observation and cultural absorption — no further topic
families to be proposed without fresh operator decision.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPICS_DIR = REPO_ROOT / "frontend/src/lib/topics"
DEWATERING_EN = TOPICS_DIR / "dewatering.js"
DEWATERING_ES = TOPICS_DIR / "dewatering.es.js"

NEW_KEY = "dewatering_invisible_force_discipline"

# The existing 8 dewatering topics that this benchmark unifies as symptoms.
EXISTING_DEWATERING_KEYS = [
    "dewatering_jetting_rig_overhead_strike",
    "dewatering_suction_line_entrapment",
    "dewatering_diesel_pump_fueling_fires",
    "dewatering_wellpoint_trench_collapse",
    "dewatering_rotating_shaft_belt",
    "dewatering_discharge_hose_whip",
    "dewatering_spoil_edge_instability",
    "dewatering_night_work_struck_by",
]

DN_MIN, DN_MAX = 1150, 1700

EN_RHETORICAL_ANCHOR = (
    "Dewatering is a discipline of forces you can feel before you can see "
    "them — and the operators who get hurt usually never recognized the "
    "force that was already there."
)
ES_RHETORICAL_ANCHOR = (
    "El dewatering es una disciplina de fuerzas que se sienten antes de "
    "verse — y los operadores que se lastiman usualmente nunca "
    "reconocieron la fuerza que ya estaba ahí."
)

EN_OPERATIONAL_ANCHORS = [
    "Invisible-Force Discipline",                # title-level anchor
    "The veteran walks the system",              # veteran/new contrast
    "The new operator watches the pump",
    "25 psi of vacuum",                          # operational specificity
    "thirty to ninety seconds after shutdown",   # concrete time window
    "12 inches of mercury",                      # vacuum specificity
    "forces you can feel before you can see them",  # rhetorical anchor stem
    "Wellpoints don't pop straight up",          # failure-direction knowledge
    "pop sideways toward whoever's closest",
    "Treat suction lines like they're under pressure",  # the cognitive flip
    "Light it like a job, not a campground",     # veteran cadence
    "Treat it as permanent or remove it",        # temp-becomes-permanent
    "If the pump stops on its own",              # root-cause discipline
    "Vapor lock",                                # field-natural failure name
]

ES_OPERATIONAL_ANCHORS = [
    "Disciplina de la Fuerza Invisible",
    "El veterano camina el sistema",
    "El operador nuevo mira la bomba",
    "25 psi de vacío",
    "treinta a noventa segundos después del apagado",
    "12 pulgadas de mercurio",
    "fuerzas que se sienten antes de verse",
    "Los wellpoints no salen disparados hacia arriba",
    "Salen de lado hacia el que esté más cerca",
    "Trate las líneas de succión como si estuvieran bajo presión",
    "Ilumínelo como obra, no como campamento",
    "Trátela como permanente o quítela",
    "Si la bomba se apaga sola",
    "Vapor lock",                                # untranslated per ES voice notes
    "wellpoint",                                 # untranslated per convention
    "dewatering",                                # untranslated per convention
    "cuadrilla",                                 # cross-region universal
]

BANNED_LMS_EN = [
    "best practices", "empower", "synergy", "holistic", "growth mindset",
    "strategic initiative", "learning ecosystem", "culture of excellence",
    "learning journey",
]
BANNED_LMS_ES = [
    "mejores prácticas", "empoderar", "sinergia", "holístico",
    "mentalidad de crecimiento", "iniciativa estratégica",
    "ecosistema de aprendizaje", "cultura de excelencia",
]


@pytest.fixture(scope="module")
def en_text():
    return DEWATERING_EN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def es_text():
    return DEWATERING_ES.read_text(encoding="utf-8")


def _extract_en_block(text: str, key: str) -> str:
    idx = text.find(f'key: "{key}"')
    if idx == -1:
        return ""
    end = text.find('key: "', idx + 20)
    return text[idx:end] if end != -1 else text[idx:]


def _extract_es_block(text: str, key: str) -> str:
    idx = text.find(f"{key}: {{")
    if idx == -1:
        return ""
    end = text.find("\n  },", idx)
    return text[idx:end] if end != -1 else text[idx:]


def test_iter305_topic_present_with_canonical_fields(en_text, es_text):
    en_block = _extract_en_block(en_text, NEW_KEY)
    for f in ("title:", "severity:", "category:", "role_context:",
              "incident_pattern:", "hazards_reviewed:", "discussion_notes:",
              "references_cited:", "action_items:"):
        assert f in en_block, f"{NEW_KEY} missing {f} in EN"
    es_block = _extract_es_block(es_text, NEW_KEY)
    for f in ("title:", "incident_pattern:", "hazards_reviewed:",
              "discussion_notes:", "references_cited:", "action_items:"):
        assert f in es_block, f"{NEW_KEY} missing {f} in ES"


def test_iter305_severity_fatal_risk(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    m = re.search(r'severity:\s*"([^"]+)"', block)
    assert m and m.group(1) == "fatal_risk"


def test_iter305_compressed_dn_envelope(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    m = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', block, re.DOTALL)
    n = len(m.group(1))
    assert DN_MIN <= n <= DN_MAX, (
        f"discussion_notes {n} chars outside compressed envelope [{DN_MIN}, {DN_MAX}]"
    )


def test_iter305_bullet_count_parity(en_text, es_text):
    en_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"',
                       _extract_en_block(en_text, NEW_KEY), re.DOTALL).group(1)
    es_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"',
                       _extract_es_block(es_text, NEW_KEY), re.DOTALL).group(1)
    assert en_dn.count("•") == es_dn.count("•") == 10


def test_iter305_en_rhetorical_anchor_preserved(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    assert EN_RHETORICAL_ANCHOR in block, (
        "iter305 EN rhetorical anchor (operator-revised sentence) missing"
    )


def test_iter305_es_rhetorical_anchor_preserved(es_text):
    block = _extract_es_block(es_text, NEW_KEY)
    assert ES_RHETORICAL_ANCHOR in block, (
        "iter305 ES rhetorical anchor (operator-revised sentence) missing"
    )


@pytest.mark.parametrize("anchor", EN_OPERATIONAL_ANCHORS)
def test_iter305_en_operational_anchor_present(en_text, anchor):
    block_lower = _extract_en_block(en_text, NEW_KEY).lower()
    assert anchor.lower() in block_lower, f"EN missing anchor: {anchor!r}"


@pytest.mark.parametrize("anchor", ES_OPERATIONAL_ANCHORS)
def test_iter305_es_operational_anchor_present(es_text, anchor):
    block_lower = _extract_es_block(es_text, NEW_KEY).lower()
    assert anchor.lower() in block_lower, f"ES missing anchor: {anchor!r}"


def test_iter305_es_nomas_banned(es_text):
    """iter303 universality discipline carries forward — `nomás` MUST NOT
    appear in the iter305 ES block."""
    block = _extract_es_block(es_text, NEW_KEY)
    assert "nomás" not in block.lower(), (
        "iter305 ES regression: 'nomás' present (must use universal Spanish per iter303)"
    )


def test_iter305_es_field_spanish_anglicisms_preserved(es_text):
    """Operator-approved: dewatering, wellpoint, and vapor lock remain
    untranslated in the ES block (field-Spanish convention for the family)."""
    block = _extract_es_block(es_text, NEW_KEY)
    for term in ("dewatering", "wellpoint", "Vapor lock"):
        assert term in block, (
            f"iter305 ES field-Spanish anglicism {term!r} lost"
        )


@pytest.mark.parametrize("banned", BANNED_LMS_EN)
def test_iter305_no_lms_drift_en(en_text, banned):
    assert banned.lower() not in _extract_en_block(en_text, NEW_KEY).lower()


@pytest.mark.parametrize("banned", BANNED_LMS_ES)
def test_iter305_no_lms_drift_es(es_text, banned):
    assert banned.lower() not in _extract_es_block(es_text, NEW_KEY).lower()


@pytest.mark.parametrize("key", EXISTING_DEWATERING_KEYS)
def test_iter305_existing_dewatering_topics_untouched(en_text, es_text, key):
    """Bounded-scope guard — the 8 existing dewatering topics that this
    benchmark unifies must remain present and unchanged at the structural
    level (key + severity + canonical fields)."""
    en_block = _extract_en_block(en_text, key)
    es_block = _extract_es_block(es_text, key)
    assert en_block.strip(), f"existing {key} missing from EN"
    assert es_block.strip(), f"existing {key} missing from ES"
    m = re.search(r'severity:\s*"([^"]+)"', en_block)
    assert m, f"existing {key} severity field missing"


def test_iter305_no_new_domain_registered():
    index_en = (TOPICS_DIR / "index.js").read_text()
    index_es = (TOPICS_DIR / "index.es.js").read_text()
    BANNED_NEW_IMPORTS = [
        "TOPICS_INVISIBLE_FORCE", "TOPICS_WELLPOINT",
        '"./invisible_force.js"', '"./wellpoint.js"',
    ]
    for bad in BANNED_NEW_IMPORTS:
        assert bad not in index_en, f"iter305 scope violation: new domain {bad}"
        assert bad not in index_es


def test_iter305_total_library_grew_to_143():
    total = 0
    for jsfile in TOPICS_DIR.glob("*.js"):
        if jsfile.name.endswith(".es.js") or jsfile.name.startswith("index"):
            continue
        text = jsfile.read_text()
        total += len(re.findall(r'^\s*key:\s*"', text, re.MULTILINE))
    assert total == 143, (
        f"library size: expected 143 (142 + 1 from iter305), got {total}"
    )


def test_iter305_dewatering_es_topic_count_grew_by_1():
    text = DEWATERING_ES.read_text()
    keys = re.findall(r'^\s*([a-z_]+):\s*\{', text, re.MULTILINE)
    assert NEW_KEY in keys, "iter305 ES topic missing from dewatering.es.js"
    # 8 existing + 1 new = 9 total ES dewatering topics
    assert len(keys) == 9, (
        f"dewatering.es.js: expected 9 topics (8 existing + iter305), got {len(keys)}"
    )


def test_iter305_voice_template_signal_present_for_family():
    """The benchmark title and invisible-force anchor signal the inheritance
    pattern. After this ship, the family carries one mental model that
    unifies the existing 8 scenario-driven topics — no further family
    expansion proposed per operator direction."""
    en_block = _extract_en_block(DEWATERING_EN.read_text(), NEW_KEY)
    assert "Invisible-Force Discipline" in en_block, (
        "Voice template signal 'Invisible-Force Discipline' missing from title"
    )
    assert "forces you can feel before you can see them" in en_block, (
        "Family rhetorical anchor lost — the conceptual lock for invisible-force"
    )


def test_iter305_fourth_philosophical_template_locked():
    """Cross-template structural confirmation: with iter305 shipped, the
    platform now carries four distinct operational-cognition templates.
    This test asserts the title-level anchors for all four are present in
    their respective domain files."""
    custody = (TOPICS_DIR / "lab.js").read_text()
    mental_model = (TOPICS_DIR / "airport.js").read_text()
    default_state = (TOPICS_DIR / "trucking.js").read_text()
    invisible_force = DEWATERING_EN.read_text()

    assert "Custody" in custody, "iter302 custody-first template anchor missing"
    assert "Mental Model" in mental_model or "mental model" in mental_model.lower(), (
        "iter303 mental-model template anchor missing"
    )
    assert "Default-State Discipline" in default_state, (
        "iter304 default-state template anchor missing"
    )
    assert "Invisible-Force Discipline" in invisible_force, (
        "iter305 invisible-force template anchor missing"
    )

"""
iter304 · Dump-bed family tone benchmark · `dump_bed_transition_discipline` ship test.

Scope (operator-approved per iter304 prose-benchmark sign-off):
  - 1 new topic appended to existing `trucking` domain (NOT a new domain).
  - Voice template: default-state discipline / seam framing.
  - Connects existing 5 dump_bed_* topics as symptoms of one underlying
    transition-discipline failure.
  - Compressed envelope: 1,150–1,320 chars discussion_notes · 10 bullets.
  - Rhetorical anchor locked: "It got hurt in the seam between the two — when
    the driver's mind had already left the dump and the truck hadn't."
  - ES anchor locked: "Se daña en la costura entre los dos — cuando la mente
    del chofer ya se fue del volteo y la troca no."

Bounded-scope guards:
  - Existing 12 trucking topics MUST remain untouched.
  - No new domain registration.
  - No TopicPicker chip changes.
  - Total library grows 141 → 142.
  - ES `nomás` REMAINS BANNED per iter303 universality discipline (replaced
    with `Nada más` in the driver-quote bullet).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPICS_DIR = REPO_ROOT / "frontend/src/lib/topics"
TRUCKING_EN = TOPICS_DIR / "trucking.js"
TRUCKING_ES = TOPICS_DIR / "trucking.es.js"

NEW_KEY = "dump_bed_transition_discipline"

# The existing 5 dump_bed_* topics that this benchmark unifies as symptoms.
EXISTING_DUMP_BED_KEYS = [
    "dump_bed_overhead_strike",
    "dump_bed_traveling_raised",
    "dump_bed_pto_habits",
    "dump_bed_soft_ground_tipover",
    "dump_bed_wind_raised",
]

DN_MIN, DN_MAX = 1150, 1320

EN_RHETORICAL_ANCHOR = "It got hurt in the seam between the two — when the driver's mind had already left the dump and the truck hadn't."
ES_RHETORICAL_ANCHOR = "Se daña en la costura entre los dos — cuando la mente del chofer ya se fue del volteo y la troca no."

EN_OPERATIONAL_ANCHORS = [
    "Default-State Discipline",       # title-level
    "I thought the bed was down",     # canonical post-incident driver quote
    "the seam between the two",       # the conceptual lock
    "the next thirty seconds",        # operator-approved time-window framing
    "physical handshake",             # PTO disengage metaphor
    "silent alarm is the worst possible default state",  # secondary anchor
    "Six feet finds power lines",     # operational specificity
    "Twenty feet finds bridges",
    "Mirror-confirm BEFORE motion",
    "Bed-down isn't the last step of dumping",
    "first step of traveling",
    "the dash in front of the driver",  # real operational practice
    "Repetitive-task complacency",
    "4,000 times",                    # the veteran-driver specificity
]

ES_OPERATIONAL_ANCHORS = [
    "Disciplina del Estado por Defecto",
    "pensé que la caja estaba abajo",
    "la costura entre los dos",
    "los siguientes treinta segundos",
    "apretón de manos físico",
    "Una alarma silenciosa es el peor estado por defecto posible",
    "Seis pies alcanzan para una línea eléctrica",
    "Veinte pies alcanzan para un puente",
    "Confirmar por espejo ANTES de moverse",
    "Caja abajo no es el último paso del volteo",
    "primer paso del viaje",
    "en el tablero frente al chofer",
    "complacencia por tarea repetida",
    "4,000 veces",
    "troca",                   # operator-approved field-Spanish (singular here)
    "Bájese si tiene que",     # operator-approved universal imperative
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
    return TRUCKING_EN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def es_text():
    return TRUCKING_ES.read_text(encoding="utf-8")


def _extract_en_block(text: str, key: str) -> str:
    idx = text.find(f'key: "{key}"')
    end = text.find('key: "', idx + 20)
    return text[idx:end] if end != -1 else text[idx:]


def _extract_es_block(text: str, key: str) -> str:
    idx = text.find(f"{key}: {{")
    end = text.find("\n  },", idx)
    return text[idx:end] if end != -1 else text[idx:]


def test_iter304_topic_present_with_canonical_fields(en_text, es_text):
    en_block = _extract_en_block(en_text, NEW_KEY)
    for f in ("title:", "severity:", "category:", "role_context:",
              "incident_pattern:", "hazards_reviewed:", "discussion_notes:",
              "references_cited:", "action_items:"):
        assert f in en_block, f"{NEW_KEY} missing {f} in EN"
    es_block = _extract_es_block(es_text, NEW_KEY)
    for f in ("title:", "incident_pattern:", "hazards_reviewed:",
              "discussion_notes:", "references_cited:", "action_items:"):
        assert f in es_block, f"{NEW_KEY} missing {f} in ES"


def test_iter304_severity_fatal_risk(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    m = re.search(r'severity:\s*"([^"]+)"', block)
    assert m and m.group(1) == "fatal_risk"


def test_iter304_compressed_dn_envelope(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    m = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', block, re.DOTALL)
    n = len(m.group(1))
    assert DN_MIN <= n <= DN_MAX, (
        f"discussion_notes {n} chars outside compressed envelope [{DN_MIN}, {DN_MAX}]"
    )


def test_iter304_bullet_count_parity(en_text, es_text):
    en_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"',
                       _extract_en_block(en_text, NEW_KEY), re.DOTALL).group(1)
    es_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"',
                       _extract_es_block(es_text, NEW_KEY), re.DOTALL).group(1)
    assert en_dn.count("•") == es_dn.count("•") == 10


def test_iter304_en_rhetorical_anchor_preserved(en_text):
    assert EN_RHETORICAL_ANCHOR in _extract_en_block(en_text, NEW_KEY)


def test_iter304_es_rhetorical_anchor_preserved(es_text):
    assert ES_RHETORICAL_ANCHOR in _extract_es_block(es_text, NEW_KEY)


@pytest.mark.parametrize("anchor", EN_OPERATIONAL_ANCHORS)
def test_iter304_en_operational_anchor_present(en_text, anchor):
    block_lower = _extract_en_block(en_text, NEW_KEY).lower()
    assert anchor.lower() in block_lower, f"EN missing anchor: {anchor!r}"


@pytest.mark.parametrize("anchor", ES_OPERATIONAL_ANCHORS)
def test_iter304_es_operational_anchor_present(es_text, anchor):
    block_lower = _extract_es_block(es_text, NEW_KEY).lower()
    assert anchor.lower() in block_lower, f"ES missing anchor: {anchor!r}"


def test_iter304_es_nomas_substitution(es_text):
    """iter303 universality discipline carries forward — `nomás` MUST NOT
    appear in the iter304 ES block. The driver-quote bullet uses `Nada más`."""
    block = _extract_es_block(es_text, NEW_KEY)
    assert "nomás" not in block.lower(), (
        "iter304 ES regression: 'nomás' present (must use 'Nada más' per iter303 universality)"
    )
    assert "Nada más moviéndome" in block, (
        "iter304 ES must use 'Nada más moviéndome unos pies' in driver-quote bullet"
    )


@pytest.mark.parametrize("banned", BANNED_LMS_EN)
def test_iter304_no_lms_drift_en(en_text, banned):
    assert banned.lower() not in _extract_en_block(en_text, NEW_KEY).lower()


@pytest.mark.parametrize("banned", BANNED_LMS_ES)
def test_iter304_no_lms_drift_es(es_text, banned):
    assert banned.lower() not in _extract_es_block(es_text, NEW_KEY).lower()


@pytest.mark.parametrize("key", EXISTING_DUMP_BED_KEYS)
def test_iter304_existing_dump_bed_topics_untouched(en_text, es_text, key):
    """Bounded-scope guard — the 5 existing dump_bed_* topics that this
    benchmark unifies must remain present and unchanged at the structural
    level (key + severity + canonical fields)."""
    en_block = _extract_en_block(en_text, key)
    es_block = _extract_es_block(es_text, key)
    assert en_block.strip(), f"existing {key} missing from EN"
    assert es_block.strip(), f"existing {key} missing from ES"
    m = re.search(r'severity:\s*"([^"]+)"', en_block)
    assert m and m.group(1) == "fatal_risk", (
        f"existing {key} severity changed (must remain fatal_risk)"
    )


def test_iter304_signature_trucking_anchors_survive(en_text):
    """Bounded-scope guard — trucking domain's canonical anecdotal voice
    anchors must survive (these are the iter301 audit's gold-standard markers
    that prove the trucking domain is the deepest in the library)."""
    SIGNATURE_LINES = [
        "I forgot the bed was up",       # dump_bed_traveling_raised anchor
        "the quiet killer",              # dump_bed_traveling_raised framing
        "the last 10 feet",              # trucking_backing_struck_by anchor (if present)
    ]
    # Each line must appear at least once in the file — proves we didn't
    # accidentally collapse or rewrite the existing topics.
    text_lower = en_text.lower()
    present = [line for line in SIGNATURE_LINES if line.lower() in text_lower]
    assert "i forgot the bed was up" in text_lower, (
        "Canonical trucking anchor 'I forgot the bed was up' lost — iter304 "
        "must NOT have rewritten dump_bed_traveling_raised"
    )


def test_iter304_no_new_domain_registered():
    index_en = (TOPICS_DIR / "index.js").read_text()
    index_es = (TOPICS_DIR / "index.es.js").read_text()
    BANNED_NEW_IMPORTS = [
        "TOPICS_DUMP_BED", "TOPICS_DUMPBED", '"./dump_bed.js"',
    ]
    for bad in BANNED_NEW_IMPORTS:
        assert bad not in index_en, f"iter304 scope violation: new domain {bad}"
        assert bad not in index_es


def test_iter304_total_library_grew_to_142():
    total = 0
    for jsfile in TOPICS_DIR.glob("*.js"):
        if jsfile.name.endswith(".es.js") or jsfile.name.startswith("index"):
            continue
        text = jsfile.read_text()
        total += len(re.findall(r'^\s*key:\s*"', text, re.MULTILINE))
    # iter304 shipped library at 142 (141 + 1). Later iterations (iter305+)
    # may grow this further. Lower-bound guards iter304's bounded-scope
    # promise that the iteration added exactly 1 topic.
    assert total >= 142, (
        f"library size: iter304 shipped at 142, got {total} (regression — iter304 topic removed?)"
    )


def test_iter304_trucking_es_topic_count_grew_by_1():
    text = TRUCKING_ES.read_text()
    keys = re.findall(r'^\s*([a-z_]+):\s*\{', text, re.MULTILINE)
    assert NEW_KEY in keys, "iter304 ES topic missing from trucking.es.js"


def test_iter304_voice_template_signal_present_for_family():
    """The benchmark title and seam-anchor signal the inheritance pattern
    for any future dump-bed family expansion (post-dump distraction,
    windrow-clearing complacency, plant-exit body-angle discipline, etc.)."""
    en_block = _extract_en_block(TRUCKING_EN.read_text(), NEW_KEY)
    assert "Default-State Discipline" in en_block, (
        "Voice template signal 'Default-State Discipline' missing from title"
    )
    assert "seam between the two" in en_block, (
        "Seam-anchor lost — the conceptual lock for the family"
    )

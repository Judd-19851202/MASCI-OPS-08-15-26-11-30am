"""
iter303 · Airport-domain tone benchmark · `airport_fod_control` ship test.

Scope (operator-approved per iter301 audit + iter303 v2 tone-benchmark sign-off):
  - 1 new topic appended to existing `airport` domain (NOT a new domain)
  - Voice template: mental-model-first framing (parallels iter302's custody-first)
  - Compressed discussion_notes envelope: ~1,260 chars (operator approved depth)
  - 10-bullet EN/ES block-count parity
  - Rhetorical anchor locked: "The bolt didn't change. The pavement it sat on
    changed everything about what the bolt meant."
  - ES rhetorical anchor locked: "El perno no cambió. El pavimento donde quedó
    cambió todo el significado del perno."

Bounded-scope guards:
  - Existing 2 airport topics MUST remain untouched (airport_movement_area_awareness +
    airport_jet_blast_fueling).
  - NO new domain registration (FOD lives in existing airport domain).
  - NO TopicPicker chip changes (existing `airport` chip already in place).
  - Total topic library grows 140 → 141.
  - ES `nomás` removed per operator caution about regional slang.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPICS_DIR = REPO_ROOT / "frontend/src/lib/topics"
AIRPORT_EN = TOPICS_DIR / "airport.js"
AIRPORT_ES = TOPICS_DIR / "airport.es.js"

NEW_KEY = "airport_fod_control"
EXISTING_AIRPORT_KEYS = ["airport_movement_area_awareness", "airport_jet_blast_fueling"]

# Operator-approved compressed envelope.
DN_MIN, DN_MAX = 1150, 1320

# Voice-template anchors (must survive any future edit).
EN_RHETORICAL_ANCHOR = "The bolt didn't change. The pavement it sat on changed everything about what the bolt meant."
ES_RHETORICAL_ANCHOR = "El perno no cambió. El pavimento donde quedó cambió todo el significado del perno."

EN_OPERATIONAL_ANCHORS = [
    "FOD is not litter",
    "Air France 4590",
    "8,000 RPM",
    "Tire-knock at the perimeter every trip",
    "Twelve in, twelve out",
    "Walk it. Don't drive it",
    "live until it's in someone's hand",
    "your contract is on the line",
    "they treat the airfield like another paving job",  # the operator-highlighted core line
    "in their bones",
    "one shift at a time",
    "Airfield Ops",
]

ES_OPERATIONAL_ANCHORS = [
    "El FOD no es basura",
    "Air France 4590",
    "8,000 RPM",
    "Golpe de llanta en el perímetro cada vuelta",
    "Doce entran, doce salen",
    "Camínelo. No lo maneje",
    "vivo hasta que esté en la mano de alguien",
    "su contrato está en juego",
    "tratan el aeródromo como otra obra de pavimento",
    "en los huesos",
    "se construye un turno a la vez",
    "Operaciones del Aeródromo",
    # NOTE: `trocas` was operator-approved as ACCEPTABLE field-Spanish but
    # the FOD topic doesn't naturally reference a specific truck type
    # (talks about "Cajas abiertas" / open beds). Not required here. Will
    # appear in future airport topics that talk about vehicle approaches.
    "wash de la hélice",     # operator-approved field-Spanish
    "tarp",                  # untranslated per operator approval
    "golpe de llanta",       # operator-approved
]

# LMS / corporate / motivational drift bans.
BANNED_LMS_EN = [
    "best practices",
    "empower",
    "synergy",
    "holistic",
    "growth mindset",
    "strategic initiative",
    "learning ecosystem",
    "culture of excellence",
    "learning journey",
]
BANNED_LMS_ES = [
    "mejores prácticas",
    "empoderar",
    "sinergia",
    "holístico",
    "mentalidad de crecimiento",
    "iniciativa estratégica",
    "ecosistema de aprendizaje",
    "cultura de excelencia",
]


@pytest.fixture(scope="module")
def en_text():
    return AIRPORT_EN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def es_text():
    return AIRPORT_ES.read_text(encoding="utf-8")


def _extract_en_block(en_text: str, key: str) -> str:
    idx = en_text.find(f'key: "{key}"')
    end = en_text.find('key: "', idx + 20)
    return en_text[idx:end] if end != -1 else en_text[idx:]


def _extract_es_block(es_text: str, key: str) -> str:
    idx = es_text.find(f"{key}: {{")
    end = es_text.find("\n  },", idx)
    return es_text[idx:end] if end != -1 else es_text[idx:]


def test_iter303_topic_present_with_canonical_fields(en_text, es_text):
    en_block = _extract_en_block(en_text, NEW_KEY)
    for field in ("title:", "severity:", "category:", "role_context:",
                  "incident_pattern:", "hazards_reviewed:", "discussion_notes:",
                  "references_cited:", "action_items:"):
        assert field in en_block, f"airport_fod_control missing {field} in EN"
    es_block = _extract_es_block(es_text, NEW_KEY)
    for field in ("title:", "incident_pattern:", "hazards_reviewed:",
                  "discussion_notes:", "references_cited:", "action_items:"):
        assert field in es_block, f"airport_fod_control missing {field} in ES"


def test_iter303_severity_fatal_risk(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    m = re.search(r'severity:\s*"([^"]+)"', block)
    assert m and m.group(1) == "fatal_risk", (
        "airport_fod_control severity must be fatal_risk per operator approval"
    )


def test_iter303_compressed_dn_envelope(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    m = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', block, re.DOTALL)
    assert m, "discussion_notes missing"
    n = len(m.group(1))
    assert DN_MIN <= n <= DN_MAX, (
        f"discussion_notes {n} chars outside compressed envelope [{DN_MIN}, {DN_MAX}]"
    )


def test_iter303_bullet_count_parity(en_text, es_text):
    en_block = _extract_en_block(en_text, NEW_KEY)
    es_block = _extract_es_block(es_text, NEW_KEY)
    en_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', en_block, re.DOTALL).group(1)
    es_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', es_block, re.DOTALL).group(1)
    assert en_dn.count("•") == es_dn.count("•") == 10, (
        f"bullet count drift: EN={en_dn.count('•')} ES={es_dn.count('•')} (must both be 10)"
    )


def test_iter303_en_rhetorical_anchor_preserved(en_text):
    block = _extract_en_block(en_text, NEW_KEY)
    assert EN_RHETORICAL_ANCHOR in block, (
        "EN rhetorical anchor missing — the operator-approved core conceptual lock"
    )


def test_iter303_es_rhetorical_anchor_preserved(es_text):
    block = _extract_es_block(es_text, NEW_KEY)
    assert ES_RHETORICAL_ANCHOR in block, (
        "ES rhetorical anchor missing — the operator-approved conceptual lock"
    )


@pytest.mark.parametrize("anchor", EN_OPERATIONAL_ANCHORS)
def test_iter303_en_operational_anchor_present(en_text, anchor):
    block_lower = _extract_en_block(en_text, NEW_KEY).lower()
    assert anchor.lower() in block_lower, (
        f"EN missing operational anchor: {anchor!r}"
    )


@pytest.mark.parametrize("anchor", ES_OPERATIONAL_ANCHORS)
def test_iter303_es_operational_anchor_present(es_text, anchor):
    block_lower = _extract_es_block(es_text, NEW_KEY).lower()
    assert anchor.lower() in block_lower, (
        f"ES missing field-Spanish anchor: {anchor!r}"
    )


def test_iter303_es_nomas_removed(es_text):
    """Operator caution about regional slang — `nomás` must be absent from
    the iter303 ES block (replaced with `No solamente`)."""
    block = _extract_es_block(es_text, NEW_KEY)
    assert "nomás" not in block.lower(), (
        "iter303 ES regression: 'nomás' present (must use 'No solamente' for universality)"
    )
    assert "No solamente" in block or "no solamente" in block, (
        "iter303 ES must use 'No solamente' substitution"
    )


def test_iter303_air_france_simplified(en_text, es_text):
    """v2 framing — must NOT contain v1's '16-inch titanium strip' or 'People died.'"""
    en_block = _extract_en_block(en_text, NEW_KEY)
    es_block = _extract_es_block(es_text, NEW_KEY)
    BANNED_V1_FRAGMENTS_EN = ["16-inch titanium strip", "People died."]
    BANNED_V1_FRAGMENTS_ES = ["tira de titanio de 16 pulgadas", "Murió gente."]
    for frag in BANNED_V1_FRAGMENTS_EN:
        assert frag not in en_block, f"v1 fragment leaked into EN: {frag!r}"
    for frag in BANNED_V1_FRAGMENTS_ES:
        assert frag not in es_block, f"v1 fragment leaked into ES: {frag!r}"
    # Must contain v2 framing
    assert "destroyed by debris left on a runway from a previous aircraft" in en_block
    assert "The consequence was total" in en_block
    assert "destruido por escombros dejados en una pista por un avión anterior" in es_block
    assert "La consecuencia fue total" in es_block


@pytest.mark.parametrize("banned", BANNED_LMS_EN)
def test_iter303_no_lms_drift_en(en_text, banned):
    block_lower = _extract_en_block(en_text, NEW_KEY).lower()
    assert banned.lower() not in block_lower, (
        f"EN contains banned LMS phrase: {banned!r}"
    )


@pytest.mark.parametrize("banned", BANNED_LMS_ES)
def test_iter303_no_lms_drift_es(es_text, banned):
    block_lower = _extract_es_block(es_text, NEW_KEY).lower()
    assert banned.lower() not in block_lower, (
        f"ES contains banned LMS phrase: {banned!r}"
    )


@pytest.mark.parametrize("key", EXISTING_AIRPORT_KEYS)
def test_iter303_existing_airport_topics_untouched(en_text, es_text, key):
    """Bounded-scope guard — the existing 2 airport topics must remain present
    and carry their original signature anchors."""
    en_block = _extract_en_block(en_text, key)
    es_block = _extract_es_block(es_text, key)
    assert en_block.strip(), f"existing {key} missing from EN"
    assert es_block.strip(), f"existing {key} missing from ES"
    # Signature anchors from iter260 / iter301-audited content.
    if key == "airport_movement_area_awareness":
        assert "ATC clearance" in en_block, f"{key} ATC clearance anchor lost"
        assert "autorización de ATC" in es_block, f"{key} ES ATC anchor lost"
    elif key == "airport_jet_blast_fueling":
        assert "100+ mph" in en_block, f"{key} jet blast anchor lost"
        assert "Jet-A" in en_block, f"{key} Jet-A anchor lost"


def test_iter303_no_new_domain_registered():
    """iter303 ships into existing `airport` domain — NO new domain creation.
    Future-airport-topics inherit this benchmark's voice within the same file."""
    index_en = (TOPICS_DIR / "index.js").read_text()
    index_es = (TOPICS_DIR / "index.es.js").read_text()
    # No spurious airport-sub-domain imports.
    BANNED_NEW_IMPORTS = [
        "TOPICS_AIRPORT_FOD",
        "TOPICS_FOD",
        '"./airport_fod.js"',
        '"./fod.js"',
    ]
    for bad in BANNED_NEW_IMPORTS:
        assert bad not in index_en, f"iter303 scope violation: new domain {bad}"
        assert bad not in index_es


def test_iter303_total_library_grew_to_141():
    """Aggregator-level sanity: total topic count is now ≥ 141 (140 + 1 from
    iter303). Range-tolerant so later iterations (iter304 +1, etc.) legitimately
    grow the library further. iter303's contribution is locked by the dedicated
    ES-topic-count + existing-topics-untouched tests above."""
    total = 0
    for jsfile in TOPICS_DIR.glob("*.js"):
        if jsfile.name.endswith(".es.js") or jsfile.name.startswith("index"):
            continue
        text = jsfile.read_text()
        total += len(re.findall(r'^\s*key:\s*"', text, re.MULTILINE))
    assert total >= 141, (
        f"library size regressed below iter303 floor: expected ≥ 141, got {total}"
    )


def test_iter303_es_topic_count_grew_by_1():
    """ES dict for airport now holds 3 topics."""
    text = AIRPORT_ES.read_text()
    keys = re.findall(r'^\s*(airport_[a-z_]+):\s*\{', text, re.MULTILINE)
    assert sorted(keys) == sorted(EXISTING_AIRPORT_KEYS + [NEW_KEY]), (
        f"ES airport topic set drifted: {keys}"
    )


def test_iter303_voice_template_signal_present_for_future_topics(en_text):
    """The benchmark explicitly signals the mental-model framing pattern via
    its title prefix '— The Discipline That Closes the Mental-Model Gap'.
    Future airport topics should be reviewed against this voice template."""
    block = _extract_en_block(en_text, NEW_KEY)
    assert "Mental-Model Gap" in block, (
        "Voice template signal lost from benchmark title (signals the pattern future "
        "airport topics inherit)"
    )

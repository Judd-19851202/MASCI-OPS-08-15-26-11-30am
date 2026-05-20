"""
iter302 · Dedicated `lab` domain regression tests.

Scope (operator-approved per iter301 audit + tone-benchmark sign-off):
  - 4 topics in a new `lab` domain · operator-approved Option α
  - Tone benchmark: `lab_nuclear_gauge_handling` (custody-first framing)
  - Compressed discussion_notes envelope: 1150-1280 chars per topic
  - 10-bullet EN/ES block-count parity per topic
  - New `lab` chip in TopicPicker.jsx + SafetyTopicLibrary.jsx
  - `plant` chip renamed from "Plant / Lab" → "Plant" (lab is now first-class)

Bounded-scope guards:
  - The existing 136 topics MUST remain untouched (NO content drift in plant /
    paving / trucking domains).
  - The lab domain is registered in BOTH aggregators (`index.js` + `index.es.js`)
    in the same position (after plant, before airport).
  - All 4 lab topics carry the canonical `incident_pattern` / `hazards_reviewed`
    / `discussion_notes` / `references_cited` / `action_items` field set.
  - Operational-tone discipline: zero LMS-drift hits; canonical regulatory
    anchors preserved as-is (NRC · OSHA · NFPA · ASTM · AASHTO · NIOSH · EPA).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPICS_DIR = REPO_ROOT / "frontend/src/lib/topics"
LAB_EN = TOPICS_DIR / "lab.js"
LAB_ES = TOPICS_DIR / "lab.es.js"
INDEX_EN = TOPICS_DIR / "index.js"
INDEX_ES = TOPICS_DIR / "index.es.js"
TOPIC_PICKER = REPO_ROOT / "frontend/src/components/TopicPicker.jsx"
LIBRARY_PAGE = REPO_ROOT / "frontend/src/pages/SafetyTopicLibrary.jsx"

LAB_KEYS = [
    "lab_nuclear_gauge_handling",
    "lab_oven_burns_chemistry",
    "lab_core_drilling_silica",
    "lab_solvent_handling_ppe",
]

# Operator-approved compressed-depth envelope per topic.
DN_MIN, DN_MAX = 1150, 1320  # operator target 1150-1250; +70 buffer for the benchmark

# Per-topic severity decisions captured in the audit.
EXPECTED_SEVERITY = {
    "lab_nuclear_gauge_handling": "fatal_risk",
    "lab_oven_burns_chemistry":   "fatal_risk",
    "lab_core_drilling_silica":   "serious_injury",
    "lab_solvent_handling_ppe":   "serious_injury",
}

# Operational anchors that MUST appear in the EN copy (custody framing, etc.).
EN_ANCHORS = {
    "lab_nuclear_gauge_handling": [
        "custody IS the safety",
        "NRC",
        "RSO",
        "10 CFR 30",
    ],
    "lab_oven_burns_chemistry": [
        "vapor",
        "NFPA 45",
        "fume hood",
        "OSHA 1910.1450",
    ],
    "lab_core_drilling_silica": [
        "wet-cut",
        "silica",
        "OSHA 1926.1153",
        "GFCI",
    ],
    "lab_solvent_handling_ppe": [
        "nitrile",
        "fume hood",
        "EPA TSCA",
        "self-heating",
    ],
}

# Canonical ES operational anchors (field-Spanish discipline check).
ES_ANCHORS = {
    "lab_nuclear_gauge_handling": [
        "la custodia ES la seguridad",
        "troca",  # operator-approved field-Spanish
        "NRC",
        "Responsable de Seguridad Radiológica",
    ],
    "lab_oven_burns_chemistry": [
        "campana extractora",
        "NFPA 45",
        "fuente de ignición",
        "incendio relámpago",
    ],
    "lab_core_drilling_silica": [
        "corte húmedo",
        "sílice",
        "OSHA 1926.1153",
        "GFCI",
    ],
    "lab_solvent_handling_ppe": [
        "nitrilo",
        "campana extractora",
        "EPA TSCA",
        "auto-calentó",
    ],
}

# LMS / corporate / motivational drift bans — checked against both EN and ES.
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
    return LAB_EN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def es_text():
    return LAB_ES.read_text(encoding="utf-8")


def _extract_en_block(en_text: str, key: str) -> str:
    idx = en_text.find(f'key: "{key}"')
    end = en_text.find('key: "', idx + 20)
    return en_text[idx:end] if end != -1 else en_text[idx:]


def _extract_es_block(es_text: str, key: str) -> str:
    idx = es_text.find(f"{key}: {{")
    end = es_text.find("  },", idx)
    return es_text[idx:end] if end != -1 else es_text[idx:]


@pytest.mark.parametrize("key", LAB_KEYS)
def test_iter302_topic_present_with_canonical_fields(en_text, es_text, key):
    """Each lab topic has all 7 canonical fields in EN + same shape in ES."""
    en_block = _extract_en_block(en_text, key)
    assert "title:" in en_block, f"{key} missing title in EN"
    assert "severity:" in en_block, f"{key} missing severity in EN"
    assert "category:" in en_block, f"{key} missing category in EN"
    assert "incident_pattern:" in en_block, f"{key} missing incident_pattern in EN"
    assert "hazards_reviewed:" in en_block, f"{key} missing hazards_reviewed in EN"
    assert "discussion_notes:" in en_block, f"{key} missing discussion_notes in EN"
    assert "references_cited:" in en_block, f"{key} missing references_cited in EN"
    assert "action_items:" in en_block, f"{key} missing action_items in EN"

    es_block = _extract_es_block(es_text, key)
    assert "title:" in es_block, f"{key} missing title in ES"
    assert "incident_pattern:" in es_block, f"{key} missing incident_pattern in ES"
    assert "hazards_reviewed:" in es_block, f"{key} missing hazards_reviewed in ES"
    assert "discussion_notes:" in es_block, f"{key} missing discussion_notes in ES"
    assert "references_cited:" in es_block, f"{key} missing references_cited in ES"
    assert "action_items:" in es_block, f"{key} missing action_items in ES"


@pytest.mark.parametrize("key,expected_sev", sorted(EXPECTED_SEVERITY.items()))
def test_iter302_severity_classification(en_text, key, expected_sev):
    """Severity assignments lock per audit + operator approval."""
    block = _extract_en_block(en_text, key)
    m = re.search(r'severity:\s*"([^"]+)"', block)
    assert m and m.group(1) == expected_sev, (
        f"{key} severity drift: expected {expected_sev}, got {m.group(1) if m else None}"
    )


@pytest.mark.parametrize("key", LAB_KEYS)
def test_iter302_compressed_dn_envelope(en_text, key):
    """Operator-approved compressed envelope: 1150-1320 chars per topic
    (target was 1150-1250; +70 buffer for the benchmark topic which
    operator explicitly accepted as 'in range')."""
    block = _extract_en_block(en_text, key)
    m = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', block, re.DOTALL)
    assert m, f"{key} missing discussion_notes"
    n = len(m.group(1))
    assert DN_MIN <= n <= DN_MAX, (
        f"{key} discussion_notes {n} chars outside compressed envelope "
        f"[{DN_MIN}, {DN_MAX}] — operator approved compressed mobile-readability target"
    )


@pytest.mark.parametrize("key", LAB_KEYS)
def test_iter302_bullet_count_parity(en_text, es_text, key):
    """EN and ES discussion_notes carry the same number of • bullets (operational
    block-count parity discipline from iter297/iter300)."""
    en_block = _extract_en_block(en_text, key)
    es_block = _extract_es_block(es_text, key)
    en_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', en_block, re.DOTALL).group(1)
    es_dn = re.search(r'discussion_notes:\s*\n?\s*"([^"]*)"', es_block, re.DOTALL).group(1)
    assert en_dn.count("•") == es_dn.count("•"), (
        f"{key} bullet count drift: EN={en_dn.count('•')} ES={es_dn.count('•')}"
    )
    assert en_dn.count("•") == 10, (
        f"{key} should have exactly 10 discussion bullets (operator-approved compressed depth)"
    )


@pytest.mark.parametrize("key", LAB_KEYS)
def test_iter302_en_operational_anchors_present(en_text, key):
    """Custody-first / chemistry-first framing locks must survive any edit."""
    block_lower = _extract_en_block(en_text, key).lower()
    for anchor in EN_ANCHORS[key]:
        assert anchor.lower() in block_lower, (
            f"{key} EN missing operational anchor: {anchor!r}"
        )


@pytest.mark.parametrize("key", LAB_KEYS)
def test_iter302_es_field_spanish_anchors_present(es_text, key):
    """Field-Spanish discipline anchors (troca · campana extractora · etc.)."""
    block_lower = _extract_es_block(es_text, key).lower()
    for anchor in ES_ANCHORS[key]:
        assert anchor.lower() in block_lower, (
            f"{key} ES missing field-Spanish anchor: {anchor!r}"
        )


@pytest.mark.parametrize("key", LAB_KEYS)
def test_iter302_no_lms_drift_en(en_text, key):
    block_lower = _extract_en_block(en_text, key).lower()
    for banned in BANNED_LMS_EN:
        assert banned.lower() not in block_lower, (
            f"{key} EN contains banned LMS phrase: {banned!r}"
        )


@pytest.mark.parametrize("key", LAB_KEYS)
def test_iter302_no_lms_drift_es(es_text, key):
    block_lower = _extract_es_block(es_text, key).lower()
    for banned in BANNED_LMS_ES:
        assert banned.lower() not in block_lower, (
            f"{key} ES contains banned LMS phrase: {banned!r}"
        )


def test_iter302_en_aggregator_registered():
    text = INDEX_EN.read_text(encoding="utf-8")
    assert 'import { TOPICS_LAB } from "./lab.js"' in text, (
        "lab.js not imported in EN aggregator"
    )
    assert "...TOPICS_LAB," in text, (
        "TOPICS_LAB not spread into TOPIC_LIBRARY"
    )
    # Lab sits between plant and airport per audit-approved ordering.
    plant_idx = text.find("...TOPICS_PLANT,")
    lab_idx = text.find("...TOPICS_LAB,")
    airport_idx = text.find("...TOPICS_AIRPORT,")
    assert plant_idx < lab_idx < airport_idx, (
        "lab domain must be ordered between plant and airport in EN aggregator"
    )


def test_iter302_es_aggregator_registered():
    text = INDEX_ES.read_text(encoding="utf-8")
    assert 'import { TOPICS_LAB_ES } from "./lab.es.js"' in text, (
        "lab.es.js not imported in ES aggregator"
    )
    assert "...TOPICS_LAB_ES," in text
    plant_idx = text.find("...TOPICS_PLANT_ES,")
    lab_idx = text.find("...TOPICS_LAB_ES,")
    airport_idx = text.find("...TOPICS_AIRPORT_ES,")
    assert plant_idx < lab_idx < airport_idx, (
        "lab_es must be ordered between plant_es and airport_es in ES aggregator"
    )


def test_iter302_topic_picker_chip_added():
    text = TOPIC_PICKER.read_text(encoding="utf-8")
    assert '{ key: "lab", en: "Lab", es: "Laboratorio" }' in text, (
        "TopicPicker.jsx DOMAIN_CHIPS missing new lab chip"
    )
    # Plant chip renamed from "Plant / Lab" → "Plant"
    assert '{ key: "plant", en: "Plant", es: "Planta" }' in text, (
        "TopicPicker.jsx plant chip not renamed to clean 'Plant' label"
    )
    assert "Plant / Lab" not in text, (
        "Stale 'Plant / Lab' chip label survived in TopicPicker.jsx"
    )


def test_iter302_safety_topic_library_chip_added():
    text = LIBRARY_PAGE.read_text(encoding="utf-8")
    assert '{ key: "lab", en: "Lab", es: "Laboratorio" }' in text, (
        "SafetyTopicLibrary.jsx DOMAIN_CHIPS missing new lab chip"
    )
    assert '{ key: "plant", en: "Plant", es: "Planta" }' in text
    assert "Plant / Lab" not in text


def test_iter302_existing_topics_untouched():
    """Bounded-scope guard — the existing 136 topics in plant/paving/trucking
    domains must not have been edited. We sample-check anchor strings that
    define those domains' incident_pattern voices."""
    # plant_crusher_clearing_jams · trucking dump_bed_traveling_raised ·
    # paving_paver_blind_spots — three signature lines from iter audit.
    plant = (TOPICS_DIR / "plant.js").read_text()
    trucking = (TOPICS_DIR / "trucking.js").read_text()
    paving = (TOPICS_DIR / "paving.js").read_text()

    # These anchor strings from iter301 audit must survive.
    assert "plant_crusher_clearing_jams" in plant
    assert "I forgot the bed was up" in trucking  # canonical anecdotal punch
    assert "paving_paver_blind_spots" in paving
    # And plant_lab_solvents_ignition stays where it was (NOT moved to lab).
    assert "plant_lab_solvents_ignition" in plant, (
        "plant_lab_solvents_ignition must remain in plant domain — iter302 "
        "is purely ADDITIVE; no migration of existing topics"
    )


def test_iter302_lab_topic_count_locked():
    """Exactly 4 lab topics in the initial bounded set."""
    text = LAB_EN.read_text(encoding="utf-8")
    keys = re.findall(r'key:\s*"(lab_[^"]+)"', text)
    assert sorted(keys) == sorted(LAB_KEYS), (
        f"iter302 lab topic set drifted: expected {sorted(LAB_KEYS)}, got {sorted(keys)}"
    )
    assert len(keys) == 4, "iter302 bounded set is exactly 4 topics"


def test_iter302_es_topic_count_locked():
    text = LAB_ES.read_text(encoding="utf-8")
    keys = re.findall(r'^\s*(lab_[a-z_]+):\s*\{', text, re.MULTILINE)
    assert sorted(keys) == sorted(LAB_KEYS), (
        f"iter302 lab ES topic set drifted: expected {sorted(LAB_KEYS)}, got {sorted(keys)}"
    )


def test_iter302_total_library_size_grew_by_4():
    """The aggregator EN library now contains at least 140 topics (136 + 4 lab).
    Range-tolerant since later iterations (iter303 +1, etc.) legitimately grow
    the library further. iter302's contribution is the +4 lab topics — that
    delta is locked by `test_iter302_lab_topic_count_locked` above."""
    total = 0
    for jsfile in TOPICS_DIR.glob("*.js"):
        if jsfile.name.endswith(".es.js") or jsfile.name.startswith("index"):
            continue
        text = jsfile.read_text()
        total += len(re.findall(r'^\s*key:\s*"', text, re.MULTILINE))
    assert total >= 140, (
        f"Total topic count regressed below the iter302 floor: expected ≥ 140 "
        f"(136 pre-iter302 + 4 lab), got {total}"
    )

"""iter273 — Inspection + QA/QC coaching family parity tests.

Sequence #2 from PLATFORM_OPERATIONAL_MATURITY_MATRIX.md. Clones the
iter270 meeting test pattern exactly. Validates that both new families:

  * `inspection.*` (Site Safety Inspection)
  * `qaqc.*`       (QA/QC Inspection)

land at parity-density to the proven cousins (incident=18, meeting=22),
expose the canonical 4 kinds at the root, fall up through the
prefix-ladder, deliver EN+ES, stay concise, stay public, hold tone, and
cover the operator-priority coaching surfaces named in the iter273
direction.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

INSPECTION_KEYS = [
    "inspection",
    "inspection.context",
    "inspection.ppe",
    "inspection.findings",
    "inspection.signoff",
]
QAQC_KEYS = [
    "qaqc",
    "qaqc.context",
    "qaqc.checklist",
    "qaqc.corrective",
    "qaqc.photos",
    "qaqc.signoff",
]
ALL_KEYS = INSPECTION_KEYS + QAQC_KEYS

ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


def _family_tips(prefix: str):
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == prefix or t["form_key"].startswith(prefix + ".")
    ]


# ─── Density (parity benchmarks) ──────────────────────────────────────
def test_inspection_family_density():
    tips = _family_tips("inspection")
    # 4 root + 3 + 3 + 4 + 3 = 17
    assert len(tips) >= 17, (
        f"inspection family must hit ≥17 tips for parity; got {len(tips)}"
    )


def test_qaqc_family_density():
    tips = _family_tips("qaqc")
    # 4 root + 3 + 3 + 3 + 3 + 2 = 18
    assert len(tips) >= 15, (
        f"qaqc family must hit ≥15 tips for parity; got {len(tips)}"
    )


# ─── Canonical 4-kind root surface ────────────────────────────────────
@pytest.mark.parametrize("root", ["inspection", "qaqc"])
def test_root_exposes_canonical_four_kinds(root):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={root}", timeout=10.0)
    assert r.status_code == 200
    kinds = {t["kind"] for t in r.json()["tips"] if t["form_key"] == root}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, (
            f"{root} root missing canonical kind={required}; got {kinds}"
        )


# ─── Endpoint anon-readability + prefix-ladder ────────────────────────
@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_endpoint_anon_returns_tips(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    assert r.status_code == 200
    assert len(r.json()["tips"]) >= 1


@pytest.mark.parametrize("leaf,root", [
    ("inspection.findings", "inspection"),
    ("qaqc.checklist", "qaqc"),
])
def test_leaf_inherits_root_via_prefix_ladder(leaf, root):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={leaf}", timeout=10.0)
    keys = {t["form_key"] for t in r.json()["tips"]}
    assert root in keys, f"prefix-ladder broken: {leaf} did not surface {root}"
    assert leaf in keys


# ─── Bilingual contract ───────────────────────────────────────────────
@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_bilingual(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        if not (t["form_key"] == "inspection"
                or t["form_key"].startswith("inspection.")
                or t["form_key"] == "qaqc"
                or t["form_key"].startswith("qaqc.")):
            continue
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"), f"{t['form_key']}/{t['kind']}: missing body_es"


# ─── Concise (validator-mirrored) ─────────────────────────────────────
@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_concise(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        if not (t["form_key"] == "inspection"
                or t["form_key"].startswith("inspection.")
                or t["form_key"] == "qaqc"
                or t["form_key"].startswith("qaqc.")):
            continue
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN too long ({wc_en})"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES too long ({wc_es})"


@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_kinds_valid(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        assert t["kind"] in ALLOWED_KINDS, f"{t['form_key']}/{t['kind']}: invalid kind"


# ─── Public-scope contract ────────────────────────────────────────────
def test_families_use_public_scope_only():
    for prefix in ("inspection", "qaqc"):
        for t in _family_tips(prefix):
            scopes = set(t.get("scopes") or [])
            assert "public" in scopes, (
                f"{t['form_key']}/{t['kind']} must be public-scoped (got {scopes})"
            )


# ─── LMS / corporate / motivational tone guardrail ────────────────────
BANNED_TONE_PHRASES = [
    "training module",
    "course completion",
    "learning objective",
    "engage in active learning",
    "best practices",
    "stakeholders",
    "synergy",
    "leverage",
    "empower",
    "módulo de capacitación",
    "objetivos de aprendizaje",
    "mejores prácticas",
]


@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_tone_not_lms(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        if not (t["form_key"] == "inspection"
                or t["form_key"].startswith("inspection.")
                or t["form_key"] == "qaqc"
                or t["form_key"].startswith("qaqc.")):
            continue
        text = " ".join([
            (t.get("body") or "").lower(),
            (t.get("body_es") or "").lower(),
        ])
        for phrase in BANNED_TONE_PHRASES:
            assert phrase.lower() not in text, (
                f"{t['form_key']}/{t['kind']} drifts into LMS tone: '{phrase}'"
            )


# ─── Operator-priority surface coverage ───────────────────────────────
def test_inspection_covers_operator_priority_surfaces():
    """Operator-named themes for site safety inspection:
        • PPE shows yesterday's culture
        • stop-work is a tool, not a punishment
        • findings need owners + close-out
        • the inspection is read by the next investigator
        • photos prove findings
    """
    expected = {
        "inspection":           {"why", "escalate"},
        "inspection.context":   {"mistake", "when"},
        "inspection.ppe":       {"why", "mistake", "escalate"},
        "inspection.findings":  {"why", "mistake", "example", "next"},
        "inspection.signoff":   {"why", "next"},
    }
    by_key: dict[str, set[str]] = {}
    for t in _family_tips("inspection"):
        by_key.setdefault(t["form_key"], set()).add(t["kind"])
    for fk, kinds in expected.items():
        for k in kinds:
            assert k in by_key.get(fk, set()), (
                f"inspection missing operator-priority surface: {fk}/{k}"
            )


def test_qaqc_covers_operator_priority_surfaces():
    """Operator-named themes for QA/QC inspection:
        • catch it before it sets / cures / closes up
        • the punch list is hidden contract risk
        • plans are the truth — field shortcuts surface here
        • photos prove the location, not the effort
        • signature is the last act, not the first
    """
    expected = {
        "qaqc":              {"why", "escalate"},
        "qaqc.context":      {"mistake", "when"},
        "qaqc.checklist":    {"why", "mistake", "escalate"},
        "qaqc.corrective":   {"why", "mistake", "next"},
        "qaqc.photos":       {"why", "mistake", "example"},
        "qaqc.signoff":      {"why", "next"},
    }
    by_key: dict[str, set[str]] = {}
    for t in _family_tips("qaqc"):
        by_key.setdefault(t["form_key"], set()).add(t["kind"])
    for fk, kinds in expected.items():
        for k in kinds:
            assert k in by_key.get(fk, set()), (
                f"qaqc missing operator-priority surface: {fk}/{k}"
            )


# ─── Registry validator stays clean after append ──────────────────────
def test_registry_validator_clean_after_seed():
    from guidance.tips import validate_tips_registry
    issues = validate_tips_registry(strict=False)
    family_issues = [
        i for i in issues
        if "inspection" in i or "qaqc" in i
    ]
    assert not family_issues, (
        f"validate_tips_registry surfaced new-family issues: {family_issues}"
    )

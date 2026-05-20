"""iter275 — Bundled Sequences #5 + #6 coaching family parity.

Five surfaces, one closure pass. Same shape as iter270/iter273/iter274.

  • equipment-issuance   (PPE/gear issuance handshake)
  • equipment-training   (toolbox-talk-grade equipment training)
  • topic-library        (Admin/Safety topic library + PDF pack)
  • fire-extinguisher    (NFPA 10 cadence)
  • jha                  (Job Hazard Analysis + Poster)
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

ROOTS = ["equipment-issuance", "equipment-training", "topic-library",
         "fire-extinguisher", "jha"]
LEAVES = [
    "equipment-issuance.employee", "equipment-issuance.equipment",
    "equipment-issuance.photos", "equipment-issuance.acknowledgment",
    "equipment-training.context", "equipment-training.acknowledgment",
    "equipment-training.signatures",
    "topic-library.filter", "topic-library.pdf-pack",
    "fire-extinguisher.add", "fire-extinguisher.inspection",
    "jha.poster",
]
ALL_KEYS = ROOTS + LEAVES

ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


def _family_tips(prefix: str):
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == prefix or t["form_key"].startswith(prefix + ".")
    ]


@pytest.mark.parametrize("root,min_count", [
    ("equipment-issuance", 15),
    ("equipment-training", 13),
    ("topic-library", 10),
    ("fire-extinguisher", 10),
    ("jha", 8),
])
def test_family_density(root, min_count):
    tips = _family_tips(root)
    assert len(tips) >= min_count, (
        f"{root} must hit ≥{min_count} tips for parity; got {len(tips)}"
    )


@pytest.mark.parametrize("root", ROOTS)
def test_root_exposes_canonical_four_kinds(root):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={root}", timeout=10.0)
    assert r.status_code == 200
    kinds = {t["kind"] for t in r.json()["tips"] if t["form_key"] == root}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, (
            f"{root} root missing canonical kind={required}; got {kinds}"
        )


@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_endpoint_anon_returns_tips(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    assert r.status_code == 200
    assert len(r.json()["tips"]) >= 1


@pytest.mark.parametrize("leaf,root", [
    ("equipment-issuance.equipment", "equipment-issuance"),
    ("equipment-training.signatures", "equipment-training"),
    ("topic-library.pdf-pack", "topic-library"),
    ("fire-extinguisher.inspection", "fire-extinguisher"),
    ("jha.poster", "jha"),
])
def test_leaf_inherits_root(leaf, root):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={leaf}", timeout=10.0)
    keys = {t["form_key"] for t in r.json()["tips"]}
    assert root in keys, f"prefix-ladder broken: {leaf} did not surface {root}"
    assert leaf in keys


@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_bilingual(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        # only enforce ES presence on iter275 families
        root = t["form_key"].split(".")[0]
        if root not in ROOTS:
            continue
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"), f"{t['form_key']}/{t['kind']}: missing body_es"


@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_concise(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        root = t["form_key"].split(".")[0]
        if root not in ROOTS:
            continue
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN too long ({wc_en})"
        assert wc_es <= 95, f"{t['form_key']}/{t['kind']} ES too long ({wc_es})"


@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_kinds_valid(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        assert t["kind"] in ALLOWED_KINDS


def test_families_use_public_scope_only():
    for root in ROOTS:
        for t in _family_tips(root):
            assert "public" in (t.get("scopes") or []), (
                f"{t['form_key']}/{t['kind']} must be public-scoped"
            )


BANNED_TONE_PHRASES = [
    "training module", "course completion", "learning objective",
    "engage in active learning", "best practices", "stakeholders",
    "synergy", "leverage", "empower",
    "módulo de capacitación", "objetivos de aprendizaje", "mejores prácticas",
]


@pytest.mark.parametrize("form_key", ALL_KEYS)
def test_tips_tone_not_lms(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        root = t["form_key"].split(".")[0]
        if root not in ROOTS:
            continue
        text = " ".join([
            (t.get("body") or "").lower(),
            (t.get("body_es") or "").lower(),
        ])
        for phrase in BANNED_TONE_PHRASES:
            assert phrase.lower() not in text, (
                f"{t['form_key']}/{t['kind']} drifts into LMS tone: '{phrase}'"
            )


def test_registry_validator_clean_after_iter275_seed():
    from guidance.tips import validate_tips_registry
    issues = validate_tips_registry(strict=False)
    family_issues = [
        i for i in issues
        if any(root in i for root in ROOTS)
    ]
    assert not family_issues, (
        f"validate_tips_registry surfaced iter275 issues: {family_issues}"
    )


# ─── Regression — earlier closures still healthy ──────────────────────
@pytest.mark.parametrize("root", ["incident", "meeting", "writeup",
                                   "daily-report", "inspection", "qaqc",
                                   "corrective"])
def test_prior_families_still_have_canonical_four(root):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={root}", timeout=10.0)
    kinds = {t["kind"] for t in r.json()["tips"] if t["form_key"] == root}
    for k in ("why", "who", "next", "escalate"):
        assert k in kinds, (
            f"REGRESSION: {root} root lost canonical kind={k}; got {kinds}"
        )

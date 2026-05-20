"""iter274 — Safety Corrective Actions coaching family + canonical-4 fills.

Sequence #3 (corrective.* family) + Sequence #4 (fleet escalate + material-
calculator who) from PLATFORM_OPERATIONAL_MATURITY_MATRIX.md, bundled into
one closure pass because Sequence #4 is structurally adjacent and tiny.

Discipline mirrors iter270 (meeting) and iter273 (inspection + qaqc) exactly:
shape / kinds / bilingual / concise / public-scope / LMS-tone guard /
operator-priority surfaces / validator clean.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

CORRECTIVE_KEYS = ["corrective", "corrective.create", "corrective.close"]
ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


def _family_tips(prefix: str):
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == prefix or t["form_key"].startswith(prefix + ".")
    ]


# ─── corrective family (Sequence #3) ──────────────────────────────────
def test_corrective_family_density():
    tips = _family_tips("corrective")
    # 4 root + 4 create + 3 close = 11
    assert len(tips) >= 11, f"corrective family must hit ≥11 tips; got {len(tips)}"


def test_corrective_root_exposes_canonical_four_kinds():
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key=corrective", timeout=10.0)
    assert r.status_code == 200
    kinds = {t["kind"] for t in r.json()["tips"] if t["form_key"] == "corrective"}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, (
            f"corrective root missing canonical kind={required}; got {kinds}"
        )


@pytest.mark.parametrize("form_key", CORRECTIVE_KEYS)
def test_corrective_endpoint_anon_returns_tips(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    assert r.status_code == 200
    assert len(r.json()["tips"]) >= 1


def test_corrective_leaf_inherits_root():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=corrective.close",
        timeout=10.0,
    )
    keys = {t["form_key"] for t in r.json()["tips"]}
    assert "corrective" in keys, "prefix-ladder broken"
    assert "corrective.close" in keys


@pytest.mark.parametrize("form_key", CORRECTIVE_KEYS)
def test_corrective_tips_bilingual(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        if not (t["form_key"] == "corrective"
                or t["form_key"].startswith("corrective.")):
            continue
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"), f"{t['form_key']}/{t['kind']}: missing body_es"


@pytest.mark.parametrize("form_key", CORRECTIVE_KEYS)
def test_corrective_tips_concise(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        if not (t["form_key"] == "corrective"
                or t["form_key"].startswith("corrective.")):
            continue
        assert len((t.get("body") or "").split()) <= 80
        assert len((t.get("body_es") or "").split()) <= 90


@pytest.mark.parametrize("form_key", CORRECTIVE_KEYS)
def test_corrective_tips_kinds_valid(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        assert t["kind"] in ALLOWED_KINDS


def test_corrective_family_uses_public_scope_only():
    for t in _family_tips("corrective"):
        assert "public" in (t.get("scopes") or [])


BANNED_TONE_PHRASES = [
    "training module", "course completion", "learning objective",
    "engage in active learning", "best practices", "stakeholders",
    "synergy", "leverage", "empower",
    "módulo de capacitación", "objetivos de aprendizaje", "mejores prácticas",
]


@pytest.mark.parametrize("form_key", CORRECTIVE_KEYS)
def test_corrective_tone_not_lms(form_key):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0)
    for t in r.json()["tips"]:
        if not (t["form_key"] == "corrective"
                or t["form_key"].startswith("corrective.")):
            continue
        text = " ".join([
            (t.get("body") or "").lower(),
            (t.get("body_es") or "").lower(),
        ])
        for phrase in BANNED_TONE_PHRASES:
            assert phrase.lower() not in text, (
                f"{t['form_key']}/{t['kind']} drifts into LMS tone: '{phrase}'"
            )


def test_corrective_covers_operator_priority_surfaces():
    expected = {
        "corrective":         {"why", "who", "next", "escalate"},
        "corrective.create":  {"why", "mistake", "example", "escalate"},
        "corrective.close":   {"why", "mistake", "next"},
    }
    by_key: dict[str, set[str]] = {}
    for t in _family_tips("corrective"):
        by_key.setdefault(t["form_key"], set()).add(t["kind"])
    for fk, kinds in expected.items():
        for k in kinds:
            assert k in by_key.get(fk, set()), (
                f"corrective missing operator-priority surface: {fk}/{k}"
            )


# ─── Sequence #4 — canonical-4 hole fills ─────────────────────────────
def test_fleet_aggregate_now_covers_canonical_four():
    """`fleet` family aggregate (root + all sub-keys) must now include
    why · who · next · escalate after the iter274 fill."""
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    fleet_kinds = {
        t["kind"] for t in all_tips()
        if t["form_key"] == "fleet" or t["form_key"].startswith("fleet.")
    }
    for k in ("why", "who", "next", "escalate"):
        assert k in fleet_kinds, (
            f"fleet aggregate still missing canonical kind={k}; got {fleet_kinds}"
        )


def test_fleet_escalate_lives_under_dvir():
    """The new escalate tip should attach to fleet.dvir — the operational
    moment where escalation actually happens (defect → OOS)."""
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key=fleet.dvir", timeout=10.0)
    kinds = {
        t["kind"] for t in r.json()["tips"]
        if t["form_key"] == "fleet.dvir"
    }
    assert "escalate" in kinds, f"fleet.dvir missing escalate; got {kinds}"


def test_material_calculator_aggregate_now_covers_canonical_four_minus_escalate():
    """material-calculator aggregate must now include why · who · next.
    (escalate already existed pre-iter274 under material-calculator.field-verify.)"""
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    mc_kinds = {
        t["kind"] for t in all_tips()
        if t["form_key"] == "material-calculator"
        or t["form_key"].startswith("material-calculator.")
    }
    for k in ("why", "who", "next", "escalate"):
        assert k in mc_kinds, (
            f"material-calculator aggregate still missing canonical kind={k}; "
            f"got {mc_kinds}"
        )


def test_material_calculator_who_lives_at_root():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=material-calculator",
        timeout=10.0,
    )
    kinds = {
        t["kind"] for t in r.json()["tips"]
        if t["form_key"] == "material-calculator"
    }
    assert "who" in kinds, f"material-calculator root missing who; got {kinds}"


# ─── Validator clean ──────────────────────────────────────────────────
def test_registry_validator_clean_after_iter274_seed():
    from guidance.tips import validate_tips_registry
    issues = validate_tips_registry(strict=False)
    family_issues = [
        i for i in issues
        if "corrective" in i or "fleet.dvir" in i
        or "material-calculator" in i
    ]
    assert not family_issues, (
        f"validate_tips_registry surfaced iter274 issues: {family_issues}"
    )


# ─── Regression — older families still healthy ────────────────────────
@pytest.mark.parametrize("root", ["incident", "meeting", "writeup",
                                   "daily-report", "inspection", "qaqc"])
def test_prior_families_still_have_canonical_four(root):
    r = httpx.get(f"{API_URL}/api/guidance/tips?form_key={root}", timeout=10.0)
    kinds = {t["kind"] for t in r.json()["tips"] if t["form_key"] == root}
    for k in ("why", "who", "next", "escalate"):
        assert k in kinds, (
            f"REGRESSION: {root} root lost canonical kind={k}; got {kinds}"
        )

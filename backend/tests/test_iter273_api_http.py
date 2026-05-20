"""HTTP-level smoke tests against the public backend for iter273.

Verifies guidance registry endpoints work end-to-end and regression families
remain healthy.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")

ITER273_FAMILIES = [
    "inspection",
    "inspection.context",
    "inspection.ppe",
    "inspection.findings",
    "inspection.signoff",
    "qaqc",
    "qaqc.context",
    "qaqc.checklist",
    "qaqc.corrective",
    "qaqc.photos",
    "qaqc.signoff",
]

REGRESSION_FAMILIES = ["incident", "meeting", "writeup", "daily-report"]

CANONICAL_KINDS = {"why", "who", "next", "escalate"}

LMS_PHRASES = [
    "training module",
    "course completion",
    "learning objective",
    "best practices",
    "leverage",
    "empower",
    "stakeholders",
]


@pytest.fixture(scope="module")
def s():
    return requests.Session()


def _fetch(s, form_key):
    r = s.get(f"{BASE_URL}/api/guidance/tips", params={"form_key": form_key}, timeout=15)
    assert r.status_code == 200, f"{form_key} -> {r.status_code} {r.text[:200]}"
    body = r.json()
    # Endpoint may return list or {"tips":[...]}.
    if isinstance(body, dict):
        tips = body.get("tips") or body.get("data") or []
    else:
        tips = body
    assert isinstance(tips, list)
    return tips


# Iter273 new families: inspection + qaqc
@pytest.mark.parametrize("root", ["inspection", "qaqc"])
def test_root_family_has_canonical_four_kinds(s, root):
    tips = _fetch(s, root)
    assert len(tips) >= 4, f"{root}: got {len(tips)} tips"
    kinds = {t.get("kind") for t in tips}
    missing = CANONICAL_KINDS - kinds
    assert not missing, f"{root}: missing kinds {missing}"


@pytest.mark.parametrize("form_key", ITER273_FAMILIES)
def test_family_returns_at_least_one_tip(s, form_key):
    tips = _fetch(s, form_key)
    assert len(tips) >= 1, f"{form_key}: empty"


# Prefix-ladder: leaf returns leaf-tips + parent-root tips
@pytest.mark.parametrize("leaf,root", [
    ("inspection.context", "inspection"),
    ("inspection.ppe", "inspection"),
    ("inspection.findings", "inspection"),
    ("inspection.signoff", "inspection"),
    ("qaqc.context", "qaqc"),
    ("qaqc.checklist", "qaqc"),
    ("qaqc.corrective", "qaqc"),
    ("qaqc.photos", "qaqc"),
    ("qaqc.signoff", "qaqc"),
])
def test_prefix_ladder_includes_parent(s, leaf, root):
    leaf_tips = _fetch(s, leaf)
    root_tips = _fetch(s, root)
    leaf_keys = {(t.get("form_key"), t.get("kind"), t.get("title")) for t in leaf_tips}
    root_keys = {(t.get("form_key"), t.get("kind"), t.get("title")) for t in root_tips}
    # Leaf response must contain the parent's tips (prefix ladder)
    assert root_keys.issubset(leaf_keys), (
        f"{leaf}: missing parent {root} tips {root_keys - leaf_keys}"
    )


# Bilingual + concise + public-scope + tone — checked together to limit calls
@pytest.mark.parametrize("form_key", ITER273_FAMILIES)
def test_bilingual_concise_scope_and_tone(s, form_key):
    tips = _fetch(s, form_key)
    for t in tips:
        tid = f"{t.get('form_key')}::{t.get('kind')}"
        # Bilingual
        assert (t.get("title_es") or "").strip(), f"{tid}: empty title_es"
        assert (t.get("body_es") or "").strip(), f"{tid}: empty body_es"
        # Concise
        body_en = (t.get("body") or t.get("body_en") or "").split()
        body_es = (t.get("body_es") or "").split()
        assert len(body_en) <= 80, f"{tid}: EN body {len(body_en)} words"
        assert len(body_es) <= 90, f"{tid}: ES body {len(body_es)} words"
        # Public scope: HTTP endpoint strips internal fields; scope is enforced
        # by in-process pytest (test_iter273_inspection_qaqc_coaching.py).
        # Here we only verify the endpoint is publicly reachable (no auth needed).
        # LMS tone gate
        body_lc = (t.get("body") or "").lower() + " " + (t.get("body_es") or "").lower()
        for phrase in LMS_PHRASES:
            assert phrase not in body_lc, f"{tid}: LMS phrase '{phrase}'"


# Regression: existing families intact
@pytest.mark.parametrize("form_key", REGRESSION_FAMILIES)
def test_regression_families_intact(s, form_key):
    tips = _fetch(s, form_key)
    assert len(tips) >= 1, f"regression {form_key} empty"

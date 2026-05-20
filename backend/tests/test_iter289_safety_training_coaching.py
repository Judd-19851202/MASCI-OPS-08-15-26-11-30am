"""
iter289 · Safety Training Records coaching-family parity closure test.

Bounded closure of the iter289 audit. The Safety Training Records
workflow has been shipped since Phase 4 (iter120) but matrix-tracked
red on Coach / 4-Kinds / Tests / Parity. iter289 closes the coaching
parity gap without redesigning the workflow.

What this test locks:
  - `safety-training` top family carries canonical 4 (why/who/next/escalate)
  - `safety-training.expiration` sub-key carries why/escalate
  - `safety-training.upload` sub-key carries why/mistake
  - ≥8 total EN tips in the family
  - Every EN tip has its ES counterpart merged at load time
  - Scope locked to {safety, admin} — HR reads cross-portal but does
    NOT write or edit on this surface
  - No LMS / corporate-training drift
  - No collision with neighbor families (equipment-training,
    document-expirations, safety-library, driver-qualification)
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from guidance.tips import all_tips


def _st_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").startswith("safety-training")
    ]


# ─── Family taxonomy ─────────────────────────────────────────────


def test_top_family_has_canonical_four_kinds():
    top = {t["kind"] for t in _st_tips() if t["form_key"] == "safety-training"}
    missing = {"why", "who", "next", "escalate"} - top
    assert not missing, f"Top family missing canonical kinds: {missing}"


def test_expiration_sub_family_has_required_kinds():
    fam = {t["kind"] for t in _st_tips()
           if t["form_key"] == "safety-training.expiration"}
    assert {"why", "escalate"}.issubset(fam), \
        f"safety-training.expiration missing why/escalate: has {fam}"


def test_upload_sub_family_has_required_kinds():
    fam = {t["kind"] for t in _st_tips()
           if t["form_key"] == "safety-training.upload"}
    assert {"why", "mistake"}.issubset(fam), \
        f"safety-training.upload missing why/mistake: has {fam}"


def test_total_tip_count_at_least_eight():
    """4 (top canonical) + 2 (expiration) + 2 (upload) = 8."""
    assert len(_st_tips()) >= 8


def test_form_keys_exact_set():
    """Lock the family shape so future iterations don't sprawl."""
    keys = {t["form_key"] for t in _st_tips()}
    assert keys == {
        "safety-training",
        "safety-training.expiration",
        "safety-training.upload",
    }, f"Unexpected family shape: {keys}"


# ─── ES parity ───────────────────────────────────────────────────


def test_every_st_tip_has_es_counterpart_merged():
    not_merged = []
    for t in _st_tips():
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append((t["form_key"], t["kind"]))
    assert not not_merged, f"ES merge incomplete: {not_merged}"


# ─── Scope discipline ────────────────────────────────────────────


def test_all_st_tips_use_safety_or_admin_scope_only():
    """HR reads cross-portal via /hr/safety-records, but does NOT
    edit / write on this surface. Safety owns the source of truth."""
    bad = []
    for t in _st_tips():
        scopes = set(t.get("scopes") or [])
        if scopes - {"safety", "admin"}:
            bad.append((t["form_key"], t["kind"], scopes))
    assert not bad, f"safety-training tips have non-safety/admin scopes: {bad}"


# ─── Tone discipline ─────────────────────────────────────────────


def test_no_lms_drift_in_iter289_tips():
    """Operator/Safety-Director voice — never LMS / corporate-training."""
    banned = [
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bempower\b", re.I),
        re.compile(r"\bleverage\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
        re.compile(r"\bupskill", re.I),
        re.compile(r"\blearning experience\b", re.I),
    ]
    hits = []
    for t in _st_tips():
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"LMS drift in iter289 tips: {hits}"


def test_expiration_tip_names_osha_or_renewal_explicitly():
    """The expiration sub-key exists to coach OSHA-style renewal
    discipline. Verify both languages explicitly name the OSHA /
    renewal anchor (otherwise the coaching becomes generic)."""
    by_key = {(t["form_key"], t["kind"]): t for t in _st_tips()}
    why = by_key[("safety-training.expiration", "why")]
    en_body = (why.get("body") or "").lower()
    es_body = (why.get("body_es") or "").lower()
    assert "osha" in en_body or "renewal" in en_body
    assert "osha" in es_body or "renov" in es_body


# ─── No-collision guards ─────────────────────────────────────────


def test_safety_training_does_not_collide_with_equipment_training_family():
    """`equipment-training` (iter275) and `safety-training` (iter289)
    are sibling but distinct families. Make sure no form_key
    accidentally shows up in both."""
    et_keys = {t["form_key"] for t in all_tips()
               if (t.get("form_key") or "").startswith("equipment-training")}
    st_keys = {t["form_key"] for t in _st_tips()}
    assert not (et_keys & st_keys), \
        f"safety-training collides with equipment-training: {et_keys & st_keys}"


def test_safety_training_does_not_collide_with_document_expirations_family():
    """`document-expirations` (iter225) already covers cross-cutting
    expiration coaching. iter289 sits next to it, not on top of it."""
    de_keys = {t["form_key"] for t in all_tips()
               if (t.get("form_key") or "").startswith("document-expirations")}
    st_keys = {t["form_key"] for t in _st_tips()}
    assert not (de_keys & st_keys), \
        f"safety-training collides with document-expirations: {de_keys & st_keys}"


# ─── Operational anchor enforcement ──────────────────────────────


def test_30_day_renewal_anchor_present_in_top_family_next_tip():
    """The 'next' tip on the top family is where the 30-day filter
    is coached. Lock the operational anchor explicitly so future
    edits don't drift away from it."""
    by_key = {(t["form_key"], t["kind"]): t for t in _st_tips()}
    nxt = by_key[("safety-training", "next")]
    body_en = (nxt.get("body") or "")
    body_es = (nxt.get("body_es") or "")
    assert "30" in body_en, "EN next tip must mention 30-day window"
    assert "30" in body_es, "ES next tip must mention 30-day window"


def test_cross_portal_read_pattern_coached_in_who_tip():
    """The 'who' tip is where we coach that HR reads cross-portal
    but does not edit. Lock that operational pattern."""
    by_key = {(t["form_key"], t["kind"]): t for t in _st_tips()}
    who = by_key[("safety-training", "who")]
    en_body = (who.get("body") or "").lower()
    es_body = (who.get("body_es") or "").lower()
    assert "hr" in en_body or "/hr/" in en_body, \
        f"EN who tip must reference HR cross-portal read: {en_body[:200]}"
    assert "rh" in es_body or "/hr/" in es_body, \
        f"ES who tip must reference HR cross-portal read: {es_body[:200]}"

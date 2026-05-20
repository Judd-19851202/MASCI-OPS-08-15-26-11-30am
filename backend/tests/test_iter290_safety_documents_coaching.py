"""
iter290 · Safety Documents coaching-family parity closure test.

Bounded closure of the iter288-audit Safety-cluster (second of two —
iter289 closed Safety Training Records). The Safety Documents
workflow has been shipped since Phase 3 (iter120) with magic-byte
PDF validation and 15 MB inline cap, but matrix-tracked red on
Coach / 4-Kinds / Tests / Parity. iter290 closes the coaching parity
gap without redesigning the workflow.

What this test locks:
  - `safety-document` top family carries canonical 4 (why/who/next/escalate)
  - `safety-document.upload` sub-key carries why/mistake
  - `safety-document.classification` sub-key carries why/next
  - ≥8 total EN tips in the family
  - Every EN tip has its ES counterpart merged at load time
  - Scope locked to {safety, admin} — HR reads cross-portal, no edit
  - No LMS / corporate-training drift
  - No collision with neighbor families (safety-training,
    safety-library, document-expirations)
  - Operational anchors locked: 15 MB cap mentioned in upload.why,
    audit/inspector framing mentioned in top.why or .escalate
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from guidance.tips import all_tips


def _sd_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").startswith("safety-document")
    ]


# ─── Family taxonomy ─────────────────────────────────────────────


def test_top_family_has_canonical_four_kinds():
    top = {t["kind"] for t in _sd_tips() if t["form_key"] == "safety-document"}
    missing = {"why", "who", "next", "escalate"} - top
    assert not missing, f"Top family missing canonical kinds: {missing}"


def test_upload_sub_family_has_required_kinds():
    fam = {t["kind"] for t in _sd_tips()
           if t["form_key"] == "safety-document.upload"}
    assert {"why", "mistake"}.issubset(fam), \
        f"safety-document.upload missing why/mistake: has {fam}"


def test_classification_sub_family_has_required_kinds():
    fam = {t["kind"] for t in _sd_tips()
           if t["form_key"] == "safety-document.classification"}
    assert {"why", "next"}.issubset(fam), \
        f"safety-document.classification missing why/next: has {fam}"


def test_total_tip_count_at_least_eight():
    """4 (top canonical) + 2 (upload) + 2 (classification) = 8."""
    assert len(_sd_tips()) >= 8


def test_form_keys_exact_set():
    """Lock the family shape so future iterations don't sprawl."""
    keys = {t["form_key"] for t in _sd_tips()}
    assert keys == {
        "safety-document",
        "safety-document.upload",
        "safety-document.classification",
    }, f"Unexpected family shape: {keys}"


# ─── ES parity ───────────────────────────────────────────────────


def test_every_sd_tip_has_es_counterpart_merged():
    not_merged = []
    for t in _sd_tips():
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append((t["form_key"], t["kind"]))
    assert not not_merged, f"ES merge incomplete: {not_merged}"


# ─── Scope discipline ────────────────────────────────────────────


def test_all_sd_tips_use_safety_or_admin_scope_only():
    """HR reads cross-portal via /hr/safety-records, but does NOT
    edit / upload on this surface. Safety owns the source of truth."""
    bad = []
    for t in _sd_tips():
        scopes = set(t.get("scopes") or [])
        if scopes - {"safety", "admin"}:
            bad.append((t["form_key"], t["kind"], scopes))
    assert not bad, f"safety-document tips have non-safety/admin scopes: {bad}"


# ─── Tone discipline ─────────────────────────────────────────────


def test_no_lms_drift_in_iter290_tips():
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
        re.compile(r"\bcompliance training course\b", re.I),
    ]
    hits = []
    for t in _sd_tips():
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"LMS drift in iter290 tips: {hits}"


# ─── Operational-anchor locks ────────────────────────────────────


def test_15mb_cap_coached_in_upload_why_tip():
    """The 15 MB inline base64 cap is a real backend constraint
    (Phase 3 iter120). Make sure the why tip explicitly coaches it
    in BOTH languages so operators don't trip over it."""
    by_key = {(t["form_key"], t["kind"]): t for t in _sd_tips()}
    why = by_key[("safety-document.upload", "why")]
    en_body = (why.get("body") or "")
    es_body = (why.get("body_es") or "")
    assert "15 MB" in en_body, f"EN upload.why must mention 15 MB cap: {en_body[:200]}"
    assert "15 MB" in es_body, f"ES upload.why must mention 15 MB cap: {es_body[:200]}"


def test_audit_or_inspector_framing_in_top_family():
    """The top family must coach the operational anchor: this is the
    library OSHA / inspectors / lawyers ask from. Generic 'documents
    are important' tone fails this test."""
    en_body = " ".join((t.get("body") or "")
                       for t in _sd_tips() if t["form_key"] == "safety-document").lower()
    es_body = " ".join((t.get("body_es") or "")
                       for t in _sd_tips() if t["form_key"] == "safety-document").lower()
    en_anchors = ["osha", "inspector", "audit", "lawyer", "incident"]
    es_anchors = ["osha", "inspector", "auditor", "audit", "incidente"]
    assert any(a in en_body for a in en_anchors), \
        "EN top family must coach OSHA/inspector/audit/lawyer/incident anchor"
    assert any(a in es_body for a in es_anchors), \
        "ES top family must coach OSHA/inspector/audit/lawyer/incident anchor"


def test_cross_portal_read_pattern_coached_in_who_tip():
    """The 'who' tip is where we coach the HR cross-portal read
    boundary. Lock that operational pattern in both languages."""
    by_key = {(t["form_key"], t["kind"]): t for t in _sd_tips()}
    who = by_key[("safety-document", "who")]
    en_body = (who.get("body") or "").lower()
    es_body = (who.get("body_es") or "").lower()
    assert "hr" in en_body or "/hr/" in en_body
    assert "rh" in es_body or "/hr/" in es_body


# ─── No-collision guards ─────────────────────────────────────────


def test_safety_document_does_not_collide_with_safety_training_family():
    """`safety-training` (iter289) and `safety-document` (iter290) are
    sibling but distinct families. No form_key should appear in both."""
    st_keys = {t["form_key"] for t in all_tips()
               if (t.get("form_key") or "").startswith("safety-training")}
    sd_keys = {t["form_key"] for t in _sd_tips()}
    assert not (st_keys & sd_keys), \
        f"safety-document collides with safety-training: {st_keys & sd_keys}"


def test_safety_document_does_not_collide_with_safety_library_family():
    """`safety-library` (iter275) is a different surface (audit
    library of topics). iter290's `safety-document` is the document
    storage workflow. Names are close — verify no key overlap."""
    sl_keys = {t["form_key"] for t in all_tips()
               if (t.get("form_key") or "").startswith("safety-library")}
    sd_keys = {t["form_key"] for t in _sd_tips()}
    assert not (sl_keys & sd_keys), \
        f"safety-document collides with safety-library: {sl_keys & sd_keys}"


def test_safety_document_does_not_collide_with_document_expirations_family():
    """`document-expirations` (iter225) is the expiration-tracking
    workflow. iter290 sits adjacent, not on top."""
    de_keys = {t["form_key"] for t in all_tips()
               if (t.get("form_key") or "").startswith("document-expirations")}
    sd_keys = {t["form_key"] for t in _sd_tips()}
    assert not (de_keys & sd_keys), \
        f"safety-document collides with document-expirations: {de_keys & sd_keys}"

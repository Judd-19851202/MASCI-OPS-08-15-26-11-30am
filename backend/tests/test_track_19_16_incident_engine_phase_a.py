"""Track 19.16 · Phase A · Incident Intelligence Engine · LOCK TEST SUITE.

Six-Pillar certification for the Phase A backend.

Scope:
    * Constants shape & completeness
    * Pydantic models & validators
    * Permissions / role matrix
    * State machine legality + capability gates
    * Event spine (emit + read)
    * Evidence engine + chain-of-custody
    * Shared corrective-action engine (platform primitive)
    * Case service (create, patch, transition, cross-link, counters, exec review)
    * Legacy adapter (READ-ONLY, Zero-Drift)
    * Bilingual vocabulary
    * Zero-Drift assertions: legacy artifacts unmodified

Runs entirely offline against a compact in-memory async collection
stub so tests are hermetic and never touch the preview database.
"""
from __future__ import annotations

import asyncio
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from incident_engine import (
    ACTION_CLASSES,
    CASE_DEFAULT_STATE,
    CASE_STATES,
    CASE_TRANSITIONS,
    CROSS_LINK_KINDS,
    EVENT_TYPES,
    EVIDENCE_TYPES,
    IMMUTABLE_AFTER_STATES,
    INCIDENT_TYPES,
    ROLE_MATRIX,
)
from incident_engine import (
    case_service,
    corrective_actions as ca_engine,
    evidence as ev_engine,
)
from incident_engine.constants import (
    ACTION_CLASS_CODES,
    ACTION_DEFAULT_STATE,
    ACTION_STATES,
    COLLECTION_CASES,
    COLLECTION_CASE_EVENTS,
    COLLECTION_CASE_EVIDENCE,
    COLLECTION_CORRECTIVE_ACTIONS,
    COLLECTION_LEGACY_INCIDENTS,
    CROSS_LINK_KIND_CODES,
    EVENT_TYPES_SET,
    EVIDENCE_TYPE_CODES,
    INCIDENT_TYPE_CODES,
    TRANSITION_CAPABILITY,
)
from incident_engine.events import count_events, emit_event, list_events
from incident_engine.legacy_adapter import (
    _guess_incident_type,
    project_legacy,
)
from incident_engine.models import (
    CaseEvent,
    CorrectiveAction,
    CrossLink,
    EvidenceItem,
    FieldBlock,
    IncidentCase,
    SafetyBlock,
)
from incident_engine.permissions import (
    actor_can,
    capabilities_for,
    normalize_role,
    require_capability,
    role_can,
)
from incident_engine.state_machine import (
    coerce_state,
    field_block_immutable,
    is_legal,
    legal_next_states,
    validate_transition,
)
from incident_engine.vocabulary import build_vocabulary


# ═══════════════════════════════════════════════════════════════════
# In-memory async DB stub — minimum operations used by the engine
# ═══════════════════════════════════════════════════════════════════
class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, key, direction=1):
        self._docs.sort(key=lambda d: d.get(key, ""), reverse=(direction == -1))
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = deepcopy(self._docs[self._i])
        self._i += 1
        d.pop("_id", None)
        return d


def _match(doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
    for k, v in query.items():
        if k == "$or":
            if not any(_match(doc, sub) for sub in v):
                return False
            continue
        # Dotted path
        target = doc
        for part in k.split("."):
            if not isinstance(target, dict):
                target = None
                break
            target = target.get(part)
        if isinstance(v, dict):
            for op, op_v in v.items():
                if op == "$in":
                    if target not in op_v:
                        return False
                elif op == "$regex":
                    if not isinstance(target, str) or not re.search(op_v, target):
                        return False
                elif op == "$nin":
                    if target in op_v:
                        return False
                else:
                    return False
        else:
            if target != v:
                return False
    return True


class _FakeCollection:
    def __init__(self):
        self._docs: List[Dict[str, Any]] = []

    async def insert_one(self, doc):
        self._docs.append(deepcopy(doc))
        return type("R", (), {"inserted_id": doc.get("id")})()

    async def find_one(self, query, projection=None):
        for d in self._docs:
            if _match(d, query):
                out = deepcopy(d)
                out.pop("_id", None)
                return out
        return None

    def find(self, query, projection=None):
        matched = [d for d in self._docs if _match(d, query)]
        return _FakeCursor(matched)

    async def count_documents(self, query):
        return sum(1 for d in self._docs if _match(d, query))

    async def update_one(self, query, update):
        modified = 0
        for d in self._docs:
            if _match(d, query):
                for op, spec in update.items():
                    if op == "$set":
                        for k, v in spec.items():
                            # dotted path support
                            if "." in k:
                                parts = k.split(".")
                                cur = d
                                for p in parts[:-1]:
                                    cur = cur.setdefault(p, {})
                                cur[parts[-1]] = v
                            else:
                                d[k] = v
                    elif op == "$push":
                        for k, v in spec.items():
                            d.setdefault(k, []).append(deepcopy(v))
                    elif op == "$pull":
                        for k, sub in spec.items():
                            d[k] = [
                                item for item in d.get(k, [])
                                if not all(item.get(sk) == sv for sk, sv in sub.items())
                            ]
                modified += 1
                break
        return type("R", (), {"modified_count": modified, "matched_count": modified})()


class _FakeDB:
    def __init__(self):
        self._cols: Dict[str, _FakeCollection] = {}

    def __getitem__(self, name):
        return self._cols.setdefault(name, _FakeCollection())

    def __getattr__(self, name):
        return self._cols.setdefault(name, _FakeCollection())


@pytest.fixture
def db():
    return _FakeDB()


# Actor fixtures
FIELD  = {"role": "field",  "name": "Foreman F"}
SAFETY = {"role": "safety", "name": "Safety S"}
ADMIN  = {"role": "admin",  "name": "Admin A"}
PM     = {"role": "pm",     "name": "PM P"}
SHOP   = {"role": "shop",   "name": "Shop H"}
FLEET  = {"role": "fleet",  "name": "Fleet Q"}
OPS    = {"role": "ops",    "name": "Ops O"}
EXEC   = {"role": "exec",   "name": "Exec X"}
UNKNOWN = {"role": "stranger", "name": "?"}


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══════════════════════════════════════════════════════════════════
# 1 · CONSTANTS — shape + completeness
# ═══════════════════════════════════════════════════════════════════
def test_9_incident_types_present():
    # Track 19.16 baseline lock: the 9 original incident types must always
    # remain present in the canon (Track 19.17 additively expanded the set —
    # subset check preserves the original lock without blocking expansion).
    codes = {t[0] for t in INCIDENT_TYPES}
    baseline_9 = {
        "vehicle_accident", "equipment_accident", "utility_strike",
        "employee_injury", "near_miss", "property_damage",
        "environmental", "workplace_violence", "public_complaint",
    }
    assert baseline_9.issubset(codes), (
        f"Track 19.16 baseline incident types drifted; missing: {baseline_9 - codes}"
    )
    assert len(INCIDENT_TYPES) >= 9


def test_every_incident_type_is_bilingual():
    for code, en, es in INCIDENT_TYPES:
        assert code and en and es
        assert en != es
        assert code.islower()


def test_case_states_count_and_default():
    assert len(CASE_STATES) == 8
    assert CASE_DEFAULT_STATE == "DRAFT"
    assert CASE_DEFAULT_STATE in CASE_STATES


def test_case_transitions_form_graph():
    # Every source state (except CLOSED terminal-ish) has at least one edge.
    for state in CASE_STATES:
        edges = CASE_TRANSITIONS.get(state, ())
        for tgt in edges:
            assert tgt in CASE_STATES, f"target {tgt} not in states"


def test_field_block_immutability_starts_at_field_submitted():
    assert "DRAFT" not in IMMUTABLE_AFTER_STATES
    assert "FIELD_SUBMITTED" in IMMUTABLE_AFTER_STATES
    assert "CLOSED" in IMMUTABLE_AFTER_STATES
    assert "REOPENED" in IMMUTABLE_AFTER_STATES


def test_11_evidence_types_have_side_assignments():
    assert len(EVIDENCE_TYPES) == 11
    for code, en, es, side in EVIDENCE_TYPES:
        assert side in ("field", "safety", "either")
        assert code.islower()


def test_10_corrective_action_classes():
    assert len(ACTION_CLASSES) == 10
    for code, en, es in ACTION_CLASSES:
        assert code and en and es


def test_action_states_lifecycle():
    assert set(ACTION_STATES) == {"OPEN", "ASSIGNED", "IN_PROGRESS", "VERIFIED", "CANCELED"}
    assert ACTION_DEFAULT_STATE == "OPEN"


def test_event_types_all_dotted_and_unique():
    assert len(set(EVENT_TYPES)) == len(EVENT_TYPES)
    for et in EVENT_TYPES:
        assert "." in et and et == et.lower()


def test_10_cross_link_kinds():
    assert len(CROSS_LINK_KINDS) == 10
    codes = {k[0] for k in CROSS_LINK_KINDS}
    assert {"daily_report", "jhp", "employee", "equipment", "fleet_asset",
            "job", "customer", "organization", "photo", "document"} == codes


def test_transition_capability_map_covers_all_edges():
    for src, edges in CASE_TRANSITIONS.items():
        for tgt in edges:
            assert (src, tgt) in TRANSITION_CAPABILITY, f"no capability for {src}->{tgt}"


def test_collections_isolated_from_legacy():
    assert COLLECTION_CASES == "incident_cases"
    assert COLLECTION_CASE_EVENTS == "incident_case_events"
    assert COLLECTION_CASE_EVIDENCE == "incident_case_evidence"
    assert COLLECTION_CORRECTIVE_ACTIONS == "corrective_actions"
    assert COLLECTION_LEGACY_INCIDENTS == "incidents"
    # New collections must not collide with legacy.
    assert COLLECTION_CASES != COLLECTION_LEGACY_INCIDENTS


# ═══════════════════════════════════════════════════════════════════
# 2 · MODELS
# ═══════════════════════════════════════════════════════════════════
def test_field_block_rejects_unknown_incident_type():
    with pytest.raises(Exception):
        FieldBlock(incident_type="not_a_real_type")


def test_field_block_accepts_all_9_types():
    for code in INCIDENT_TYPE_CODES:
        fb = FieldBlock(incident_type=code)
        assert fb.incident_type == code


def test_incident_case_default_state_is_draft():
    case = IncidentCase(field_block=FieldBlock(incident_type="near_miss"))
    assert case.state == "DRAFT"
    assert case.id
    assert not case.field_block_locked
    assert case.evidence_count == 0
    assert case.corrective_action_count == 0


def test_incident_case_state_validator_rejects_bogus():
    with pytest.raises(Exception):
        IncidentCase(
            state="BOGUS",
            field_block=FieldBlock(incident_type="near_miss"),
        )


def test_evidence_item_rejects_unknown_type():
    with pytest.raises(Exception):
        EvidenceItem(case_id="x", evidence_type="bogus")


def test_evidence_item_accepts_all_types():
    for code in EVIDENCE_TYPE_CODES:
        item = EvidenceItem(case_id="c", evidence_type=code)
        assert item.evidence_type == code
        assert item.withdrawn is False
        assert item.custody_chain == []


def test_corrective_action_state_validator():
    ca = CorrectiveAction(
        consumer_id="c1", action_class="training", title="t",
    )
    assert ca.state == "OPEN"
    with pytest.raises(Exception):
        CorrectiveAction(
            consumer_id="c1", action_class="training", title="t", state="???",
        )


def test_corrective_action_rejects_unknown_class():
    with pytest.raises(Exception):
        CorrectiveAction(
            consumer_id="c1", action_class="unknown_class", title="t",
        )


def test_case_event_rejects_unknown_event_type():
    with pytest.raises(Exception):
        CaseEvent(case_id="c1", event_type="bogus.event")


def test_cross_link_rejects_unknown_kind():
    with pytest.raises(Exception):
        CrossLink(kind="not_a_kind", target_id="x")


# ═══════════════════════════════════════════════════════════════════
# 3 · PERMISSIONS
# ═══════════════════════════════════════════════════════════════════
def test_normalize_role_from_dict_variants():
    assert normalize_role({"role": "safety"}) == "safety"
    assert normalize_role({"_actor": "admin"}) == "admin"
    assert normalize_role({"kind": "field"}) == "field"
    assert normalize_role("field") == "field"
    assert normalize_role(None) == ""


def test_role_can_field_can_only_submit_and_add_field_evidence():
    assert role_can("field", "field_block.write")
    assert role_can("field", "transition.submit")
    assert role_can("field", "evidence.add_field")
    assert not role_can("field", "safety_block.write")
    assert not role_can("field", "transition.close")
    assert not role_can("field", "evidence.add_safety")


def test_role_can_safety_can_close_and_reopen():
    assert role_can("safety", "transition.close")
    assert role_can("safety", "transition.reopen")
    assert role_can("safety", "safety_block.write")
    assert role_can("safety", "corrective_action.assign")
    assert role_can("safety", "corrective_action.verify")


def test_role_can_pm_shop_fleet_ops_are_read_only():
    for r in ("pm", "shop", "fleet", "ops"):
        assert not role_can(r, "field_block.write")
        assert not role_can(r, "safety_block.write")
        assert not role_can(r, "transition.submit")
        assert not role_can(r, "transition.close")
    assert role_can("ops", "case.read_all")
    assert role_can("pm", "cross_link.write")


def test_role_can_exec_has_reopen_and_review():
    assert role_can("exec", "transition.reopen")
    assert role_can("exec", "executive_review.record")
    assert not role_can("exec", "field_block.write")


def test_role_can_admin_is_superset_of_safety_plus_exec():
    for cap in ROLE_MATRIX["safety"]:
        assert role_can("admin", cap), f"admin missing safety cap {cap}"
    assert role_can("admin", "executive_review.record")


def test_role_can_unknown_role_denied_everywhere():
    for cap in ("case.create", "case.read_all", "safety_block.write"):
        assert not role_can("stranger", cap)
        assert not role_can("", cap)


def test_require_capability_raises_permission_error():
    with pytest.raises(PermissionError):
        require_capability(FIELD, "safety_block.write")
    require_capability(SAFETY, "safety_block.write")  # no raise


def test_capabilities_for_returns_sorted_list():
    caps = list(capabilities_for("safety"))
    assert caps == sorted(caps)


def test_actor_can_actor_variants():
    assert actor_can(SAFETY, "safety_block.write")
    assert not actor_can(FIELD, "safety_block.write")
    assert not actor_can(None, "case.create")


# ═══════════════════════════════════════════════════════════════════
# 4 · STATE MACHINE
# ═══════════════════════════════════════════════════════════════════
def test_coerce_state_defaults_on_unknown():
    assert coerce_state("bogus") == "DRAFT"
    assert coerce_state(None) == "DRAFT"
    assert coerce_state("closed") == "CLOSED"


def test_is_legal_happy_path():
    assert is_legal("DRAFT", "FIELD_SUBMITTED")
    assert is_legal("SAFETY_INTAKE", "UNDER_INVESTIGATION")
    assert is_legal("VERIFICATION", "CLOSED")
    assert is_legal("CLOSED", "REOPENED")
    assert is_legal("REOPENED", "UNDER_INVESTIGATION")


def test_is_legal_rejects_illegal():
    assert not is_legal("DRAFT", "CLOSED")
    assert not is_legal("CLOSED", "DRAFT")
    assert not is_legal("SAFETY_INTAKE", "FIELD_SUBMITTED")


def test_legal_next_states_shape():
    assert legal_next_states("DRAFT") == ("FIELD_SUBMITTED",)
    assert legal_next_states("CLOSED") == ("REOPENED",)


def test_validate_transition_field_can_submit():
    ok, err = validate_transition(
        from_state="DRAFT", to_state="FIELD_SUBMITTED", actor=FIELD,
    )
    assert ok and err == ""


def test_validate_transition_field_cannot_close():
    ok, err = validate_transition(
        from_state="VERIFICATION", to_state="CLOSED", actor=FIELD,
    )
    assert not ok and err == "role_not_authorized"


def test_validate_transition_reopen_requires_reason():
    ok, err = validate_transition(
        from_state="CLOSED", to_state="REOPENED", actor=SAFETY, reason="",
    )
    assert not ok and err == "reason_required"
    ok, err = validate_transition(
        from_state="CLOSED", to_state="REOPENED", actor=SAFETY,
        reason="new evidence surfaced",
    )
    assert ok


def test_validate_transition_illegal_topology():
    ok, err = validate_transition(
        from_state="DRAFT", to_state="CLOSED", actor=SAFETY,
    )
    assert not ok and err == "illegal_transition"


def test_validate_transition_unknown_target():
    ok, err = validate_transition(
        from_state="DRAFT", to_state="NEVER_STATE", actor=SAFETY,
    )
    assert not ok and err == "unknown_transition"


def test_field_block_immutable_helper():
    assert not field_block_immutable("DRAFT")
    for s in IMMUTABLE_AFTER_STATES:
        assert field_block_immutable(s), s


# ═══════════════════════════════════════════════════════════════════
# 5 · EVENT SPINE
# ═══════════════════════════════════════════════════════════════════
def test_emit_event_writes_and_lists(db):
    async def _t():
        e = await emit_event(
            db, case_id="c1", event_type="case.created",
            actor=SAFETY, to_state="DRAFT",
        )
        assert e["event_type"] == "case.created"
        assert e["actor_role"] == "safety"
        events = await list_events(db, case_id="c1")
        assert len(events) == 1
        assert await count_events(db, case_id="c1") == 1
        assert await count_events(db, case_id="c2") == 0
    _run(_t())


def test_emit_event_rejects_unknown_type(db):
    async def _t():
        with pytest.raises(ValueError):
            await emit_event(db, case_id="c1", event_type="never.ever")
    _run(_t())


# ═══════════════════════════════════════════════════════════════════
# 6 · CASE SERVICE (integration)
# ═══════════════════════════════════════════════════════════════════
def _mk(db, actor=SAFETY, incident_type="near_miss"):
    return _run(case_service.create_case(
        db, actor=actor,
        field_block={
            "incident_type": incident_type,
            "location_label": "Zone A",
            "reporter_name": "Foreman",
        },
    ))


def test_create_case_field_can(db):
    c = _mk(db, actor=FIELD, incident_type="near_miss")
    assert c["state"] == "DRAFT"
    assert not c["field_block_locked"]
    events = _run(list_events(db, case_id=c["id"]))
    assert events[0]["event_type"] == "case.created"


def test_create_case_denied_for_pm(db):
    with pytest.raises(Exception):
        _run(case_service.create_case(
            db, actor=PM,
            field_block={"incident_type": "near_miss"},
        ))


def test_create_case_rejects_unknown_incident_type(db):
    with pytest.raises(Exception):
        _run(case_service.create_case(
            db, actor=SAFETY,
            field_block={"incident_type": "bogus"},
        ))


def test_full_lifecycle_walk(db):
    c = _mk(db, actor=FIELD)
    cid = c["id"]
    # DRAFT → FIELD_SUBMITTED (field)
    c = _run(case_service.transition_case(
        db, case_id=cid, to_state="FIELD_SUBMITTED", actor=FIELD,
    ))
    assert c["state"] == "FIELD_SUBMITTED"
    assert c["field_block_locked"] is True
    assert c["case_number"]
    # FIELD_SUBMITTED → SAFETY_INTAKE (safety)
    c = _run(case_service.transition_case(
        db, case_id=cid, to_state="SAFETY_INTAKE", actor=SAFETY,
    ))
    # → UNDER_INVESTIGATION
    c = _run(case_service.transition_case(
        db, case_id=cid, to_state="UNDER_INVESTIGATION", actor=SAFETY,
    ))
    # → CORRECTIVE_ACTIONS
    c = _run(case_service.transition_case(
        db, case_id=cid, to_state="CORRECTIVE_ACTIONS", actor=SAFETY,
    ))
    # → VERIFICATION
    c = _run(case_service.transition_case(
        db, case_id=cid, to_state="VERIFICATION", actor=SAFETY,
    ))
    # → CLOSED
    c = _run(case_service.transition_case(
        db, case_id=cid, to_state="CLOSED", actor=SAFETY,
    ))
    assert c["state"] == "CLOSED"
    assert c["closed_at"]
    # → REOPENED (with reason)
    c = _run(case_service.transition_case(
        db, case_id=cid, to_state="REOPENED", actor=SAFETY, reason="new evidence",
    ))
    assert c["state"] == "REOPENED"
    assert c["reopened_at"]
    assert not c["closed_at"]

    # Timeline captures every transition + special events.
    ev = _run(list_events(db, case_id=cid))
    types = [e["event_type"] for e in ev]
    assert "case.created" in types
    assert "case.field_submitted" in types
    assert types.count("case.state_changed") >= 7
    assert "case.closed" in types
    assert "case.reopened" in types


def test_transition_illegal_returns_permission_error(db):
    c = _mk(db)
    with pytest.raises(PermissionError) as ex:
        _run(case_service.transition_case(
            db, case_id=c["id"], to_state="CLOSED", actor=SAFETY,
        ))
    assert str(ex.value) == "illegal_transition"


def test_transition_role_gate(db):
    c = _mk(db)
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=FIELD,
    ))
    with pytest.raises(PermissionError) as ex:
        _run(case_service.transition_case(
            db, case_id=c["id"], to_state="SAFETY_INTAKE", actor=FIELD,
        ))
    assert str(ex.value) == "role_not_authorized"


def test_reopen_requires_reason(db):
    c = _mk(db)
    cid = c["id"]
    for tgt, actor in [
        ("FIELD_SUBMITTED", FIELD),
        ("SAFETY_INTAKE", SAFETY),
        ("UNDER_INVESTIGATION", SAFETY),
        ("CORRECTIVE_ACTIONS", SAFETY),
        ("VERIFICATION", SAFETY),
        ("CLOSED", SAFETY),
    ]:
        _run(case_service.transition_case(
            db, case_id=cid, to_state=tgt, actor=actor,
        ))
    with pytest.raises(PermissionError) as ex:
        _run(case_service.transition_case(
            db, case_id=cid, to_state="REOPENED", actor=SAFETY, reason="",
        ))
    assert str(ex.value) == "reason_required"


def test_field_block_immutability_after_submit(db):
    c = _mk(db, actor=FIELD)
    cid = c["id"]
    _run(case_service.update_field_block(
        db, case_id=cid, actor=FIELD, patch={"weather": "rain"},
    ))
    _run(case_service.transition_case(
        db, case_id=cid, to_state="FIELD_SUBMITTED", actor=FIELD,
    ))
    with pytest.raises(PermissionError) as ex:
        _run(case_service.update_field_block(
            db, case_id=cid, actor=FIELD, patch={"weather": "sunny"},
        ))
    assert str(ex.value) == "field_block_immutable"


def test_safety_block_editable_by_safety_only(db):
    c = _mk(db)
    cid = c["id"]
    _run(case_service.update_safety_block(
        db, case_id=cid, actor=SAFETY,
        patch={"osha_recordable": True, "root_cause_summary": "training gap"},
    ))
    # Recordability change emits a dedicated event
    ev = _run(list_events(db, case_id=cid))
    types = [e["event_type"] for e in ev]
    assert "safety_block.updated" in types
    assert "recordability.changed" in types
    assert "root_cause.updated" in types
    # Field can't edit safety block.
    with pytest.raises(PermissionError):
        _run(case_service.update_safety_block(
            db, case_id=cid, actor=FIELD, patch={"osha_recordable": False},
        ))


def test_field_cannot_write_safety_block(db):
    c = _mk(db)
    for role in (FIELD, PM, SHOP, FLEET, OPS):
        with pytest.raises(PermissionError):
            _run(case_service.update_safety_block(
                db, case_id=c["id"], actor=role,
                patch={"root_cause_summary": "x"},
            ))


def test_safety_cannot_edit_field_block_after_submit(db):
    c = _mk(db, actor=FIELD)
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=FIELD,
    ))
    with pytest.raises(PermissionError):
        _run(case_service.update_field_block(
            db, case_id=c["id"], actor=SAFETY, patch={"weather": "changed"},
        ))


def test_cross_link_add_and_remove(db):
    c = _mk(db)
    link = _run(case_service.add_cross_link(
        db, case_id=c["id"], actor=SAFETY,
        kind="equipment", target_id="EQ-100", target_label="CAT 320",
    ))
    assert link["kind"] == "equipment"
    _run(case_service.remove_cross_link(
        db, case_id=c["id"], actor=SAFETY, link_id=link["id"],
    ))
    # Read case back — cross_links empty again.
    stored = _run(case_service.get_case(db, c["id"]))
    assert stored["cross_links"] == []


def test_cross_link_service_rejects_unknown_kind(db):
    c = _mk(db)
    with pytest.raises(ValueError):
        _run(case_service.add_cross_link(
            db, case_id=c["id"], actor=SAFETY,
            kind="not_a_thing", target_id="x",
        ))


def test_pm_can_cross_link_but_not_write_blocks(db):
    c = _mk(db)
    _run(case_service.add_cross_link(
        db, case_id=c["id"], actor=PM,
        kind="daily_report", target_id="DR-1",
    ))
    with pytest.raises(PermissionError):
        _run(case_service.update_field_block(
            db, case_id=c["id"], actor=PM, patch={"weather": "storm"},
        ))


def test_executive_review_by_exec_role(db):
    c = _mk(db)
    _run(case_service.record_executive_review(
        db, case_id=c["id"], actor=EXEC, notes="reviewed",
    ))
    out = _run(case_service.get_case(db, c["id"]))
    assert out["safety_block"]["executive_reviewer"] == "Exec X"


def test_executive_review_denied_for_safety(db):
    c = _mk(db)
    with pytest.raises(PermissionError):
        _run(case_service.record_executive_review(
            db, case_id=c["id"], actor=SAFETY, notes="x",
        ))


def test_list_cases_role_gate(db):
    _mk(db)
    _mk(db, incident_type="vehicle_accident")
    cases = _run(case_service.list_cases(db, actor=SAFETY))
    assert len(cases) == 2
    with pytest.raises(PermissionError):
        _run(case_service.list_cases(db, actor=UNKNOWN))


def test_list_cases_filter_by_state_and_type(db):
    c1 = _mk(db, incident_type="near_miss")
    c2 = _mk(db, incident_type="vehicle_accident")
    _run(case_service.transition_case(
        db, case_id=c2["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    only_draft = _run(case_service.list_cases(db, actor=SAFETY, state="DRAFT"))
    assert {c["id"] for c in only_draft} == {c1["id"]}
    only_vehicle = _run(case_service.list_cases(
        db, actor=SAFETY, incident_type="vehicle_accident",
    ))
    assert {c["id"] for c in only_vehicle} == {c2["id"]}


# ═══════════════════════════════════════════════════════════════════
# 7 · EVIDENCE ENGINE
# ═══════════════════════════════════════════════════════════════════
def test_field_evidence_types_open_to_field(db):
    c = _mk(db)
    ev = _run(ev_engine.add_evidence(
        db, case_id=c["id"], evidence_type="photo",
        actor=FIELD, label="site photo",
    ))
    assert ev["evidence_type"] == "photo"
    assert ev["custody_chain"][0]["action"] == "added"


def test_field_cannot_add_safety_evidence(db):
    c = _mk(db)
    with pytest.raises(PermissionError):
        _run(ev_engine.add_evidence(
            db, case_id=c["id"], evidence_type="police_report",
            actor=FIELD,
        ))


def test_safety_can_add_all_evidence_types(db):
    c = _mk(db)
    for code in EVIDENCE_TYPE_CODES:
        _run(ev_engine.add_evidence(
            db, case_id=c["id"], evidence_type=code, actor=SAFETY,
        ))
    lst = _run(ev_engine.list_evidence(db, case_id=c["id"]))
    assert len(lst) == len(EVIDENCE_TYPE_CODES)


def test_withdraw_evidence_requires_reason_and_preserves_row(db):
    c = _mk(db)
    ev = _run(ev_engine.add_evidence(
        db, case_id=c["id"], evidence_type="photo", actor=FIELD,
    ))
    with pytest.raises(ValueError):
        _run(ev_engine.withdraw_evidence(
            db, evidence_id=ev["id"], actor=SAFETY, reason="",
        ))
    out = _run(ev_engine.withdraw_evidence(
        db, evidence_id=ev["id"], actor=SAFETY, reason="misfiled",
    ))
    assert out["withdrawn"] is True
    assert out["withdrawal_reason"] == "misfiled"
    assert len(out["custody_chain"]) == 2
    # Withdrawn row still LISTED (chain of custody preserved).
    lst = _run(ev_engine.list_evidence(db, case_id=c["id"]))
    assert len(lst) == 1
    lst2 = _run(ev_engine.list_evidence(
        db, case_id=c["id"], include_withdrawn=False,
    ))
    assert len(lst2) == 0


def test_withdraw_denied_for_field(db):
    c = _mk(db)
    ev = _run(ev_engine.add_evidence(
        db, case_id=c["id"], evidence_type="photo", actor=FIELD,
    ))
    with pytest.raises(PermissionError):
        _run(ev_engine.withdraw_evidence(
            db, evidence_id=ev["id"], actor=FIELD, reason="oops",
        ))


# ═══════════════════════════════════════════════════════════════════
# 8 · CORRECTIVE ACTION ENGINE (platform primitive)
# ═══════════════════════════════════════════════════════════════════
def test_create_action_bound_to_incident_case_emits_event(db):
    c = _mk(db)
    ca = _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="training", title="Retrain crew", actor=SAFETY,
        assigned_to_name="Jose", assigned_to_role="crew_lead",
    ))
    assert ca["state"] == "ASSIGNED"
    assert ca["assigned_at"]
    ev = _run(list_events(db, case_id=c["id"]))
    types = [e["event_type"] for e in ev]
    assert "corrective_action.assigned" in types


def test_create_action_for_non_incident_consumer_does_not_emit_case_event(db):
    ca = _run(ca_engine.create_action(
        db, consumer_kind="jhp", consumer_id="jhp-42",
        action_class="training", title="Retrain", actor=SAFETY,
    ))
    assert ca["consumer_kind"] == "jhp"
    # No incident case event emitted for jhp consumers.
    assert _run(count_events(db, case_id="jhp-42")) == 0


def test_verify_action_updates_state_and_emits_event(db):
    c = _mk(db)
    ca = _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="ppe", title="Issue vests", actor=SAFETY,
    ))
    v = _run(ca_engine.verify_action(
        db, action_id=ca["id"], actor=SAFETY, verification_notes="OK",
    ))
    assert v["state"] == "VERIFIED"
    ev = _run(list_events(db, case_id=c["id"]))
    types = [e["event_type"] for e in ev]
    assert "corrective_action.verified" in types


def test_cancel_action_requires_reason(db):
    c = _mk(db)
    ca = _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="policy_update", title="Update policy", actor=SAFETY,
    ))
    with pytest.raises(ValueError):
        _run(ca_engine.cancel_action(
            db, action_id=ca["id"], actor=SAFETY, reason="",
        ))
    cx = _run(ca_engine.cancel_action(
        db, action_id=ca["id"], actor=SAFETY, reason="duplicate",
    ))
    assert cx["state"] == "CANCELED"


def test_action_denied_for_field(db):
    c = _mk(db)
    with pytest.raises(PermissionError):
        _run(ca_engine.create_action(
            db, consumer_kind="incident_case", consumer_id=c["id"],
            action_class="training", title="x", actor=FIELD,
        ))


def test_summary_for_case_counts_open_and_total(db):
    c = _mk(db)
    a1 = _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="training", title="A1", actor=SAFETY,
    ))
    _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="ppe", title="A2", actor=SAFETY,
    ))
    _run(ca_engine.verify_action(db, action_id=a1["id"], actor=SAFETY))
    s = _run(ca_engine.summary_for_case(db, case_id=c["id"]))
    assert s == {"total": 2, "open": 1}


def test_refresh_counters_updates_case_cache(db):
    c = _mk(db)
    _run(ev_engine.add_evidence(
        db, case_id=c["id"], evidence_type="photo", actor=SAFETY,
    ))
    _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="training", title="x", actor=SAFETY,
    ))
    out = _run(case_service.refresh_counters(db, case_id=c["id"]))
    assert out["evidence_count"] == 1
    assert out["corrective_action_count"] == 1
    stored = _run(case_service.get_case(db, c["id"]))
    assert stored["evidence_count"] == 1
    assert stored["corrective_action_count"] == 1


# ═══════════════════════════════════════════════════════════════════
# 9 · LEGACY ADAPTER  (Zero-Drift, read-only)
# ═══════════════════════════════════════════════════════════════════
def test_legacy_projection_marks_flags():
    raw = {
        "id": "legacy-1",
        "doc_id": "INC-2024-001",
        "reporter_name": "Jose",
        "incident_type": "Utility Damage",
        "description": "hit a gas line",
        "project_number": "P100",
        "incident_date": "2025-05-01",
        "lifecycle_state": "CLOSED",
    }
    view = project_legacy(raw)
    assert view["__legacy__"] is True
    assert view["__raw_legacy__"] == raw
    assert view["field_block_locked"] is True
    assert view["field_block"]["incident_type"] == "utility_strike"
    assert view["state"] == "CLOSED"


def test_legacy_guessed_incident_types_cover_common_phrases():
    assert _guess_incident_type({"description": "Vehicle collision"}) == "vehicle_accident"
    assert _guess_incident_type({"description": "Employee hurt his back"}) == "employee_injury"
    assert _guess_incident_type({"description": "near miss report"}) == "near_miss"
    assert _guess_incident_type({"description": "fuel spill"}) == "environmental"
    assert _guess_incident_type({"description": "threat of assault"}) == "workplace_violence"
    assert _guess_incident_type({"description": "utility line struck"}) == "utility_strike"
    assert _guess_incident_type({"description": "damaged fence"}) == "property_damage"
    assert _guess_incident_type({"description": "excavator rolled"}) == "equipment_accident"
    assert _guess_incident_type({"description": "customer complaint"}) == "public_complaint"


def test_legacy_fallback_public_complaint_when_unknown():
    assert _guess_incident_type({"description": "asdfghjkl"}) == "public_complaint"


# ═══════════════════════════════════════════════════════════════════
# 10 · VOCABULARY (bilingual)
# ═══════════════════════════════════════════════════════════════════
def test_vocabulary_shape():
    v = build_vocabulary()
    for key in (
        "incident_types", "case_states", "evidence_types",
        "action_classes", "action_states", "cross_link_kinds",
        "roles", "event_types",
    ):
        assert key in v, key
    assert len(v["incident_types"]) >= 9  # Track 19.17 additively expanded
    assert len(v["case_states"]) == 8
    assert len(v["evidence_types"]) == 11
    assert len(v["action_classes"]) == 10
    assert len(v["cross_link_kinds"]) == 10


def test_vocabulary_every_entry_bilingual():
    v = build_vocabulary()
    for group in ("incident_types", "case_states", "evidence_types",
                  "action_classes", "action_states", "cross_link_kinds", "roles"):
        for entry in v[group]:
            assert entry["en"] and entry["es"], f"{group}:{entry.get('code')}"


def test_vocabulary_roles_carry_capabilities():
    v = build_vocabulary()
    roles = {r["code"]: r for r in v["roles"]}
    assert set(roles.keys()) == set(ROLE_MATRIX.keys())
    for code, spec in roles.items():
        assert set(spec["capabilities"]) == set(ROLE_MATRIX[code])


# ═══════════════════════════════════════════════════════════════════
# 11 · ZERO-DRIFT: legacy incident lifecycle routes untouched
# ═══════════════════════════════════════════════════════════════════
REPO_ROOT = Path("/app")
LEGACY_LIFECYCLE = REPO_ROOT / "backend/routes/incident_lifecycle.py"


def test_legacy_incident_lifecycle_module_still_exists():
    assert LEGACY_LIFECYCLE.is_file()


def test_legacy_incident_lifecycle_exports_unchanged():
    txt = LEGACY_LIFECYCLE.read_text(encoding="utf-8")
    assert "register_incident_lifecycle_routes" in txt
    # Legacy endpoints remain on /incidents/... namespace.
    assert '/incidents/{incident_id}/transition' in txt
    assert '/incidents/{incident_id}/state-events' in txt
    assert '/incidents/{incident_id}/lifecycle' in txt


def test_server_still_registers_legacy_lifecycle():
    server_txt = (REPO_ROOT / "backend/server.py").read_text(encoding="utf-8")
    assert "register_incident_lifecycle_routes" in server_txt
    assert "register_incident_engine_routes" in server_txt
    # NEW registration is documented under Track 19.16.
    assert "TRACK 19.16" in server_txt


def test_new_namespace_never_writes_to_legacy_collection():
    """No engine module may write to the legacy `incidents` collection."""
    engine_dir = REPO_ROOT / "backend/incident_engine"
    forbidden_writes = ("db.incidents.insert", "db.incidents.update",
                        "db.incidents.delete", "db.incidents.replace",
                        'db["incidents"].insert', 'db["incidents"].update',
                        'db["incidents"].delete', 'db["incidents"].replace')
    for path in engine_dir.glob("*.py"):
        src = path.read_text(encoding="utf-8")
        for needle in forbidden_writes:
            assert needle not in src, (
                f"{path} writes to legacy collection via {needle!r}"
            )


# ═══════════════════════════════════════════════════════════════════
# 12 · ROUTE ARTIFACT
# ═══════════════════════════════════════════════════════════════════
ENGINE_DIR = REPO_ROOT / "backend/incident_engine"


@pytest.mark.parametrize("module", [
    "__init__", "constants", "models", "permissions", "state_machine",
    "events", "evidence", "corrective_actions", "legacy_adapter",
    "vocabulary", "case_service", "routes",
])
def test_engine_module_exists(module):
    assert (ENGINE_DIR / f"{module}.py").is_file(), module


def test_routes_module_registers_expected_paths():
    src = (ENGINE_DIR / "routes.py").read_text(encoding="utf-8")
    expected = (
        "/incident-cases/vocabulary",
        "/incident-cases",
        "/incident-cases/{case_id}",
        "/incident-cases/{case_id}/field-block",
        "/incident-cases/{case_id}/safety-block",
        "/incident-cases/{case_id}/transitions",
        "/incident-cases/{case_id}/timeline",
        "/incident-cases/{case_id}/audit",
        "/incident-cases/{case_id}/evidence",
        "/incident-cases/{case_id}/cross-links",
        "/incident-cases/{case_id}/executive-review",
        "/incident-cases/legacy/{incident_id}",
        "/corrective-actions",
        "/corrective-actions/{action_id}/verify",
        "/corrective-actions/{action_id}/cancel",
    )
    for path in expected:
        assert path in src, path


# ═══════════════════════════════════════════════════════════════════
# 13 · SIX-PILLAR CERTIFICATION MANIFEST
# ═══════════════════════════════════════════════════════════════════
def test_pillar_powerful_domain_primitives_are_reusable():
    """Corrective Actions engine is consumer-agnostic (platform primitive)."""
    from incident_engine.corrective_actions import create_action
    import inspect
    sig = inspect.signature(create_action)
    assert "consumer_kind" in sig.parameters
    assert "consumer_id" in sig.parameters


def test_pillar_simple_field_block_only_has_facts():
    fb = FieldBlock(incident_type="near_miss")
    dumped = fb.model_dump()
    # These belong to Safety, not Field.
    for forbidden in ("osha_recordable", "root_cause_summary",
                      "root_cause_categories", "investigator_name"):
        assert forbidden not in dumped, forbidden


def test_pillar_beautiful_progressive_disclosure_ready():
    # Incident types are ordered; consumer picks type first → the UI
    # reveals only that type's block. Order is stable.
    codes = [t[0] for t in INCIDENT_TYPES]
    assert codes.index("vehicle_accident") < codes.index("public_complaint")


def test_pillar_trusted_immutable_after_submit():
    for s in ("FIELD_SUBMITTED", "SAFETY_INTAKE",
              "UNDER_INVESTIGATION", "CORRECTIVE_ACTIONS",
              "VERIFICATION", "CLOSED", "REOPENED"):
        assert field_block_immutable(s)


def test_pillar_proven_event_spine_records_every_mutation():
    # Every state-changing / mutation operation MUST emit at least one
    # event type from EVENT_TYPES.
    required = {
        "case.created", "case.field_submitted", "case.state_changed",
        "case.closed", "case.reopened",
        "field_block.updated", "safety_block.updated",
        "evidence.added", "evidence.withdrawn",
        "corrective_action.assigned", "corrective_action.verified",
        "corrective_action.canceled",
        "cross_link.attached", "cross_link.removed",
        "recordability.changed", "root_cause.updated",
        "executive_review.recorded",
    }
    assert required.issubset(EVENT_TYPES_SET)


def test_pillar_operational_role_matrix_covers_seven_roles():
    for r in ("field", "safety", "pm", "shop", "fleet", "ops", "exec"):
        assert r in ROLE_MATRIX, r
    assert "admin" in ROLE_MATRIX  # eighth: super-role

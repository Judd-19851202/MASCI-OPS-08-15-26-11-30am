from __future__ import annotations

from pathlib import Path


MEMORY = Path("/app/memory")

DOCS = {
    "definition_of_done": MEMORY / "MASCI_DEFINITION_OF_DONE.md",
    "constitution": MEMORY / "MASCI_OPERATIONAL_EXECUTION_CONSTITUTION.md",
    "register": MEMORY / "MASCI_OPERATIONAL_EXECUTION_REGISTER.md",
    "certification_plan": MEMORY / "MASCI_OPERATIONAL_EXECUTION_CERTIFICATION_PLAN.md",
    "appendix": MEMORY / "MASCI_OPERATIONAL_EXECUTION_CONSTITUTIONAL_APPENDIX.md",
    "traceability_report": MEMORY / "MASCI_FIVE_GATE_RELEASE_GOVERNANCE_TRACEABILITY.md",
    "traceability_matrix": MEMORY / "MASCI_OPERATIONAL_EXECUTION_REQUIREMENT_TRACEABILITY_MATRIX.md",
    "artifact_verification": MEMORY / "MASCI_OPERATIONAL_EXECUTION_ARTIFACT_VERIFICATION.md",
    "prd": MEMORY / "PRD.md",
}

FIVE_GATES = [
    "CONTRACT_LOCKED",
    "LOCAL_ENGINEERING_VERIFIED",
    "INDEPENDENT_ADVERSARIAL_CERTIFIED",
    "IMMUTABLE_RELEASE_CANDIDATE_VERIFIED",
    "DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED",
]

GOVERNING_DOC_KEYS = [
    "definition_of_done",
    "constitution",
    "register",
    "certification_plan",
    "appendix",
    "traceability_matrix",
]

BANNED_CASUAL_VOCAB = [
    "Looks Good",
]


def _read(path: Path) -> str:
    assert path.exists(), f"required artifact missing: {path}"
    return path.read_text(encoding="utf-8", errors="ignore")


def _all_docs_text() -> dict[str, str]:
    return {name: _read(path) for name, path in DOCS.items()}


def test_required_five_gate_artifacts_exist() -> None:
    for path in DOCS.values():
        assert path.exists(), f"required artifact missing: {path}"


def test_all_five_gate_tokens_exist_in_governing_set() -> None:
    texts = _all_docs_text()
    combined = "\n".join(texts[name] for name in GOVERNING_DOC_KEYS)
    for gate in FIVE_GATES:
        assert gate in combined, f"missing Five-Gate token: {gate}"


def test_definition_of_done_reserves_done_for_all_five_gates() -> None:
    body = _read(DOCS["definition_of_done"])
    assert "DONE means all five gates are VERIFIED." in body
    for gate in FIVE_GATES:
        assert gate in body, f"Definition of Done missing gate: {gate}"


def test_constitution_and_appendix_define_five_gate_law() -> None:
    constitution = _read(DOCS["constitution"])
    appendix = _read(DOCS["appendix"])
    assert "### 23.4 Five-Gate Release Governance Rule" in constitution
    assert "### 10.3 Five-Gate Release Governance Contract" in appendix
    for req_id in [f"FG-00{i}" for i in range(1, 10)] + ["FG-010"]:
        assert req_id in appendix, f"appendix missing requirement id {req_id}"


def test_traceability_artifacts_cover_fg_requirements() -> None:
    report = _read(DOCS["traceability_report"])
    matrix = _read(DOCS["traceability_matrix"])
    for req_id in [f"FG-00{i}" for i in range(1, 10)] + ["FG-010"]:
        assert req_id in report, f"traceability report missing {req_id}"
        assert f"| {req_id} |" in matrix, f"traceability matrix missing row {req_id}"


def test_register_milestone_set_contains_five_gates_and_done_rule() -> None:
    body = _read(DOCS["register"])
    for token in FIVE_GATES + ["DONE"]:
        assert f"- {token}" in body, f"register milestone set missing {token}"
    assert "all VERIFIED in order" in body


def test_builder_cannot_self_declare_done_or_independent_gate() -> None:
    combined = "\n".join(
        _read(DOCS[name])
        for name in ("definition_of_done", "constitution", "certification_plan", "appendix")
    )
    required_phrases = [
        "may not self-assert Gate 3",
        "may not self-assert Gate 5",
        "may not self-declare `DONE`",
    ]
    for phrase in required_phrases:
        assert phrase in combined, f"missing builder self-declaration prohibition: {phrase}"


def test_skipped_test_classification_is_mandatory_and_vocab_locked() -> None:
    body = _read(DOCS["certification_plan"])
    assert "skip_classification" in body
    assert "Permitted `skip_classification` values are:" in body
    assert "- `BLOCKING`" in body
    assert "- `NON_BLOCKING`" in body
    assert "No skipped required test may appear in evidence without" in body


def test_only_permitted_skip_classification_values_are_documented() -> None:
    body = _read(DOCS["certification_plan"])
    assert "`BLOCKING`" in body
    assert "`NON_BLOCKING`" in body
    for forbidden in ["OPTIONAL", "INFORMATIONAL", "SOFT_BLOCK", "N/A"]:
        assert f"`{forbidden}`" not in body, f"unexpected skip classification documented: {forbidden}"


def test_banned_casual_vocabulary_absent_from_amended_governing_artifacts() -> None:
    texts = _all_docs_text()
    scoped = "\n".join(
        texts[name]
        for name in [
            "definition_of_done",
            "constitution",
            "register",
            "certification_plan",
            "appendix",
            "traceability_report",
            "traceability_matrix",
        ]
    )
    assert "DONE-DONE" not in scoped
    for banned in BANNED_CASUAL_VOCAB:
        assert banned not in scoped, f"banned casual vocabulary still present: {banned}"


def test_artifact_verification_and_prd_reflect_amendment_without_broad_rewrite() -> None:
    artifact_verification = _read(DOCS["artifact_verification"])
    prd = _read(DOCS["prd"])
    assert "Deterministic backend governance regression tests added for Five-Gate law: yes" in artifact_verification
    assert "Application tests modified: yes" in artifact_verification
    assert prd.splitlines()[0].strip() == "## 2026-07-14 · TRACK DR-03 · LOCAL_ENGINEERING_VERIFIED"
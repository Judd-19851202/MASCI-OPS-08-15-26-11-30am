"""iter220 — Codify the walkthrough editorial cadence as a load-bearing
protocol document.

This test makes `walkthrough_pass.md` itself enforced: if a future
agent removes the strategic-holds section, replaces the persona order,
drops the anti-pattern guardrails, or breaks the cadence summary, the
test catches it.

The doc is not "documentation" in the marketing sense — it's the
load-bearing institutional memory that protects the editorial loop
from drift.
"""
from pathlib import Path

import pytest

DOC = Path("/app/walkthroughs/walkthrough_pass.md")


def test_walkthrough_pass_doc_exists():
    assert DOC.exists(), f"missing protocol doc: {DOC}"


def test_doc_has_all_required_sections():
    """Section ordering is operator-load-bearing — it encodes the
    editorial reasoning sequence (what IS this loop → priorities →
    execution → vocabulary → review → authoring → re-run → measure →
    realism → guardrails → strategic holds → summary)."""
    src = DOC.read_text()
    required_sections = [
        "## 0 · What this loop IS — and what it isn't",
        "## 1 · Persona execution order",
        "## 2 · Walkthrough execution expectations",
        "## 3 · Finding kinds — the load-bearing vocabulary",
        "## 4 · Finding review cadence",
        "## 5 · Coaching authoring standards",
        "## 6 · Re-run expectations after authoring coaching",
        "## 7 · Actionable-finding delta tracking",
        "## 8 · Operational realism requirements",
        "## 9 · Anti-pattern guardrails",
        "## 10 · Strategic holds",
        "## 11 · The cadence in one paragraph",
    ]
    for section in required_sections:
        assert section in src, f"protocol missing required section: {section!r}"


def test_doc_locks_operator_persona_order():
    """The persona priority order (foreman → super → operator →
    dispatcher → hr → safety → pm → laborer) is operator-stated and
    MUST stay aligned with aggregate_findings.PRIORITY_ORDER."""
    src = DOC.read_text()
    persona_order_lines = [
        "1. Foreman",
        "2. Superintendent",
        "3. Operator",
        "4. Dispatcher",
        "5. HR",
        "6. Safety",
        "7. PM",
        "8. Laborer",
    ]
    last_idx = -1
    for line in persona_order_lines:
        idx = src.find(line)
        assert idx != -1, f"persona order line missing: {line!r}"
        assert idx > last_idx, (
            f"persona order drifted — {line!r} appears out of sequence"
        )
        last_idx = idx


def test_doc_persona_order_matches_aggregator():
    """The doc's stated persona order must match what
    aggregate_findings.PRIORITY_ORDER actually uses at runtime."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "aggregate_findings",
        "/app/walkthroughs/aggregate_findings.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    expected = [
        "foreman", "superintendent", "operator", "dispatcher",
        "hr", "safety", "pm", "laborer",
    ]
    assert mod.PRIORITY_ORDER == expected, (
        "aggregate_findings.PRIORITY_ORDER drifted from doc-stated order"
    )


HARD_STOP_ANTI_PATTERNS = [
    "Mongo collection storing walkthrough runs",
    "dashboard rendering walkthrough trends",
    "score",
    "telemetry from the production app for any walkthrough purpose",
    "JIRA tickets",
    "CI pass/fail",
    "engagement metrics",
    "page object models",
    "LMS layer",
]


@pytest.mark.parametrize("phrase", HARD_STOP_ANTI_PATTERNS)
def test_doc_calls_out_all_anti_patterns(phrase):
    """Every hard-stop anti-pattern from the iter217 README must also
    appear explicitly in the protocol doc so future agents read both."""
    src = DOC.read_text()
    assert phrase.lower() in src.lower(), (
        f"protocol must explicitly ban anti-pattern: {phrase!r}"
    )


REQUIRED_STRATEGIC_HOLDS = [
    "Operator mid-day-defect",
    "HelpTip helpfulness-pulse",
]


@pytest.mark.parametrize("hold", REQUIRED_STRATEGIC_HOLDS)
def test_doc_preserves_operator_strategic_holds(hold):
    """Strategic holds are operator-stated deliberate deferrals. If a
    future agent removes them from the doc, the next agent will
    re-discover them and waste a cycle. Keep them visible."""
    src = DOC.read_text()
    assert hold in src, f"protocol must preserve strategic hold: {hold!r}"


REQUIRED_CULTURAL_ANCHORS = [
    "Checkout is the handshake",
    "Reviewing isn't auditing",
    "The paper is the evidence; the conversation is the work",
    "Calibration beats scoring",
    "Opportunity, not blame",
    "Dispatch is the operational referee",
    "The calculator is for planning; the Daily Report is for truth",
]


@pytest.mark.parametrize("anchor", REQUIRED_CULTURAL_ANCHORS)
def test_doc_lists_authored_cultural_anchors(anchor):
    """The cultural-anchor table preserves the operator-stated voice
    fingerprints. Future agents reference this table when authoring
    new families to match the established tone."""
    src = DOC.read_text()
    assert anchor in src, (
        f"protocol must preserve operator-stated cultural anchor: {anchor!r}"
    )


def test_doc_ends_with_cadence_summary_paragraph():
    """The cadence-in-one-paragraph closer is the protocol's executive
    summary. If a future agent skims and only reads one section, it
    should be this one. Must remain at the end as a single paragraph."""
    src = DOC.read_text()
    cadence_marker = "## 11 · The cadence in one paragraph"
    assert cadence_marker in src
    tail = src.split(cadence_marker, 1)[1]
    # The summary paragraph must contain the load-bearing verbs of the
    # editorial loop.
    for required_verb in (
        "Run", "Aggregate", "author", "Re-run", "Measure",
    ):
        assert required_verb in tail, (
            f"cadence summary missing required loop verb: {required_verb!r}"
        )
    # Closing protection — must explicitly tell the next agent that
    # analytics drift is the failure mode.
    assert "Never let the cadence become analytics" in tail, (
        "cadence summary must close with the analytics-drift hard stop"
    )


def test_doc_banned_taxonomy_vocabulary_called_out():
    """The doc must call out the banned-vocabulary list (warning,
    error, info, bug, etc.) so future agents don't try to 'translate'
    finding kinds into a JIRA-style triage taxonomy."""
    src = DOC.read_text()
    for banned in ("warning", "error", "info", "bug", "severity"):
        assert banned in src, (
            f"protocol must call out banned-taxonomy term: {banned!r}"
        )


def test_doc_references_load_bearing_tone_banlists():
    """The four tone-discipline banlists (introduced across
    iter211→iter218) are load-bearing. The protocol must reference all
    four by name so they don't quietly disappear."""
    src = DOC.read_text()
    for banlist in (
        "ROBOTIC_OSHA_PHRASES",
        "CORPORATE_DRIFT_PHRASES",
        "HR_LEGAL_DRIFT_PHRASES",
        "CORPORATE_HR_PHRASES",
    ):
        assert banlist in src, (
            f"protocol must reference banlist constant: {banlist!r}"
        )

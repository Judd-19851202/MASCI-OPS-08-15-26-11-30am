"""DR-ROI-001E · Invisible Intelligence Compliance Lock.

Scans the PM / Admin / Executive Operational Intelligence surface for AI
branding leaks (model names, provider names, agent names, token/cost
verbiage). Failing this test blocks any "AI branding creep" from landing
on the operator-facing dashboards, per the DR-ROI-001E user directive.
"""
from __future__ import annotations
import re
from pathlib import Path


ROOT = Path("/app/frontend/src")

INTELLIGENCE_SURFACE = [
    ROOT / "pages" / "PmOperationalIntelligence.jsx",
    ROOT / "pages" / "AdminOperationalIntelligence.jsx",
    ROOT / "pages" / "ExecutiveOperationalIntelligence.jsx",
    ROOT / "components" / "ods" / "HorizonPrimitives.jsx",
    ROOT / "lib" / "odsIntelligenceApi.js",
]

# Words that must NEVER surface on operator dashboards. Case-insensitive.
FORBIDDEN_UI_STRINGS = [
    "claude", "anthropic", "gpt-", "gpt5", "gpt 5",
    "openai", "gemini", "nano banana", "sonnet ", "opus ",
    "haiku", "llm", "model:", "provider:", "token cost",
    "tokens used", "cost per token", "ai agent",
    "prompt tokens", "completion tokens",
]

# Domain terms that ARE allowed — approve list to avoid false positives.
ALLOWED_TERMS = {
    "sourced from the operational data spine",
    "operational data spine",
    "operational_facts",
    "operational_kpi_snapshots",
}


def _scan(text: str, path: Path) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for word in FORBIDDEN_UI_STRINGS:
        if word in lower:
            # Skip if it's inside an ALLOWED_TERMS phrase.
            allowed = any(a in lower for a in ALLOWED_TERMS if word in a)
            if allowed:
                continue
            hits.append(f"{path.name}: forbidden UI string '{word}'")
    return hits


def test_invisible_intelligence_on_dashboards():
    hits: list[str] = []
    for p in INTELLIGENCE_SURFACE:
        assert p.exists(), f"missing intelligence surface file: {p}"
        hits.extend(_scan(p.read_text(encoding="utf-8"), p))
    assert not hits, "AI branding leaked into UI:\n" + "\n".join(hits)


def test_three_horizons_present_on_every_dashboard():
    """Every dashboard must expose the three canonical horizons."""
    files = [
        ROOT / "pages" / "PmOperationalIntelligence.jsx",
        ROOT / "pages" / "AdminOperationalIntelligence.jsx",
        ROOT / "pages" / "ExecutiveOperationalIntelligence.jsx",
    ]
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert '"What Happened"' in text, f"{f.name}: missing Horizon 1"
        assert '"What Is Happening"' in text, f"{f.name}: missing Horizon 2"
        assert '"What Needs Attention"' in text, f"{f.name}: missing Horizon 3"


def test_evidence_footer_present():
    """Every dashboard must cite the ODS as its data source."""
    files = [
        ROOT / "pages" / "PmOperationalIntelligence.jsx",
        ROOT / "pages" / "AdminOperationalIntelligence.jsx",
        ROOT / "pages" / "ExecutiveOperationalIntelligence.jsx",
    ]
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert "EvidenceFooter" in text, f"{f.name}: missing EvidenceFooter"


def test_no_placeholder_charts_or_fake_data():
    """No lorem ipsum / mock data / third-party decorative chart libraries."""
    # Import-level checks — dashboards must not depend on chart libs at all.
    banned_imports = ("from \"recharts\"", "from 'recharts'",
                       "from \"chart.js\"", "from 'chart.js'",
                       "from \"@nivo/", "from '@nivo/",
                       "from \"victory\"", "from 'victory'")
    banned_data = ("lorem ipsum", "MOCK_DATA", "SAMPLE_DATA", "DEMO_ROWS")
    for p in INTELLIGENCE_SURFACE:
        text = p.read_text(encoding="utf-8")
        for b in banned_imports:
            assert b not in text, f"{p.name}: chart lib import '{b}'"
        for b in banned_data:
            assert b not in text, f"{p.name}: fake data marker '{b}'"

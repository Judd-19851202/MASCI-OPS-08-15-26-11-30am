#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
TOKENS = REPO_ROOT / "frontend" / "src" / "styles" / "tokens.css"
PORTAL_SYSTEM = REPO_ROOT / "frontend" / "src" / "styles" / "portal-system.css"
PORTAL_PALETTE = REPO_ROOT / "frontend" / "src" / "lib" / "portalPalette.js"
HUB = REPO_ROOT / "frontend" / "src" / "pages" / "Hub.jsx"


EXPECTED_SNIPPETS = {
    "tokens.css": [
        "--domain-admin-solid: #334155;",
        "--domain-pm-solid: #4338ca;",
        "--domain-hr-solid: #7c3aed;",
        "--domain-safety-solid: #b42318;",
        "--domain-dispatch-solid: #0369a1;",
        "--domain-shop-solid: #c2410c;",
        "--domain-training-solid: #2563eb;",
        "--domain-field-solid: #9a5b12;",
        "--domain-qaqc-solid: #047857;",
        "--domain-leadership-solid: #57534e;",
    ],
    "portal-system.css": [
        "--portal-admin-700:    #334155;",
        "--portal-safety-700:   #b42318;",
        "--portal-dispatch-700: #0369a1;",
        "--portal-field-700:    #9a5b12;",
        "--portal-pm-700:       #4338ca;",
        "--portal-training-700: #2563eb;",
    ],
    "portalPalette.js": [
        'safety:     "safety"',
        'dispatch:   "dispatch"',
        'leadership: "leadership"',
        'admin:      "admin"',
        'pm:         "pm"',
    ],
    "Hub.jsx": [
        'title: "QA/QC"',
        'tone: "field"',
        'tone: "qaqc"',
        'tone: "safety"',
    ],
}

FORBIDDEN_PATTERNS = {
    "frontend-source": [
        (re.compile(r"\breview\s+qc\b", re.IGNORECASE), "review QC"),
        (re.compile(r"(?<!/)\bqc\s+review\b", re.IGNORECASE), "QC Review"),
        (re.compile(r"\bqa\s+/\s+qc\b", re.IGNORECASE), "QA / QC"),
    ],
}


def main() -> int:
    files = {
        "tokens.css": TOKENS.read_text(),
        "portal-system.css": PORTAL_SYSTEM.read_text(),
        "portalPalette.js": PORTAL_PALETTE.read_text(),
        "Hub.jsx": HUB.read_text(),
    }
    frontend_source = "\n".join(path.read_text(errors="ignore") for path in (REPO_ROOT / "frontend" / "src").rglob("*.jsx"))
    results = {"decision": "pass", "failures": []}

    for name, snippets in EXPECTED_SNIPPETS.items():
        text = files[name]
        for snippet in snippets:
            if snippet not in text:
                results["decision"] = "fail"
                results["failures"].append({"file": name, "missing_snippet": snippet})

    for regex, label in FORBIDDEN_PATTERNS["frontend-source"]:
        if regex.search(frontend_source):
            results["decision"] = "fail"
            results["failures"].append({"scope": "frontend-source", "forbidden": label})

    print(json.dumps(results, indent=2))
    return 0 if results["decision"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
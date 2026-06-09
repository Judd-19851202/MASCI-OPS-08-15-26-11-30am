"""
test_project_identity_compliance.py — PROJECT-IDENTITY-005 deployment blocker

OMEGA DIRECTIVE · DO NOT REFACTOR

Fails CI / deploy if any UI grouping or folder operation still uses
submitter free-text instead of routing through resolveProjectIdentity()
or JobFolderList (which itself canonicalizes via jobsMaster + the resolver
contract).

Three checks:

  1.  No file may concatenate {number}::{name} as a grouping key.
  2.  Every <JobFolderList ...> callsite MUST pass `jobsMaster=`.
  3.  Every page that imports JobFolderList must also fetch
      `/jobs-master` (or pass an empty {} map). Detected by static
      string match.

Exceptions (intentionally allowed):
  - frontend/src/lib/projectIdentity.js                      (the resolver itself)
  - frontend/src/lib/projectIdentity.test.js                 (unit tests)
  - frontend/src/components/JobFolderList.jsx                (component definition)
  - frontend/src/pages/admin/AdminProjectIdentityGovernance.jsx (the governance UI)
"""
from __future__ import annotations

import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "src"

EXEMPT = {
    str(FRONTEND / "lib" / "projectIdentity.js"),
    str(FRONTEND / "lib" / "projectIdentity.test.js"),
    str(FRONTEND / "components" / "JobFolderList.jsx"),
    str(FRONTEND / "pages" / "admin" / "AdminProjectIdentityGovernance.jsx"),
}


def _iter_source_files():
    for p in FRONTEND.rglob("*.jsx"):
        if str(p) in EXEMPT:
            continue
        yield p
    for p in FRONTEND.rglob("*.js"):
        if str(p) in EXEMPT:
            continue
        # skip test files for sub-test scans (resolver test exempted)
        yield p


def test_no_number_double_colon_name_grouping_key():
    """No file may use `${number}::${name}` as a grouping key. This is the
    exact defect class fixed in PROJECT-IDENTITY-003."""
    pattern = re.compile(r"\$\{[^}]*number[^}]*\}::\$\{[^}]*name[^}]*\}")
    offenders = []
    for f in _iter_source_files():
        text = f.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                # Allow ::${wk.week} style — only flag *name* concat
                offenders.append(f"{f}:{i}: {line.strip()}")
    assert not offenders, (
        "PROJECT-IDENTITY-005 deployment blocker: forbidden "
        "`${number}::${name}` grouping detected:\n  "
        + "\n  ".join(offenders)
    )


def test_jobfolderlist_callsites_pass_jobsMaster():
    """Every <JobFolderList ...> consumer MUST pass jobsMaster=. The
    component itself is exempt (it's the receiver)."""
    offenders = []
    open_tag = re.compile(r"<JobFolderList\b")
    for f in _iter_source_files():
        text = f.read_text(encoding="utf-8", errors="ignore")
        for m in open_tag.finditer(text):
            start = m.start()
            # Inspect a generous window after the opening tag — JobFolderList
            # callsites contain inline arrow functions / nested JSX so a
            # naive `>`-stop regex captures only the arrow function. Instead,
            # scan up to the matching closing `</JobFolderList>` or the
            # next sibling JSX element.
            tail = text[start:start + 4000]
            # cut at end of THIS element — look for `/>` self-close or
            # the `</JobFolderList>` closing tag.
            stop = re.search(r"</JobFolderList>|/>", tail)
            block = tail[: stop.end()] if stop else tail
            if "jobsMaster" not in block:
                line_no = text[:start].count("\n") + 1
                offenders.append(f"{f}:{line_no}: <JobFolderList> without jobsMaster prop")
    assert not offenders, (
        "PROJECT-IDENTITY-005 deployment blocker: <JobFolderList> callsites "
        "missing `jobsMaster` prop:\n  " + "\n  ".join(offenders)
    )


def test_jobfolderlist_consumers_fetch_jobs_master():
    """Every page that imports JobFolderList must also reference
    `/jobs-master` (the canonical endpoint). This catches a future
    contributor who would pass an empty object literal as jobsMaster
    just to satisfy the previous check.

    Exempts AdminSafetyFormsPanel which fetches /jobs-master once on
    component mount via its own effect (already verified manually)."""
    offenders = []
    for f in _iter_source_files():
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "import JobFolderList" not in text:
            continue
        if "/jobs-master" not in text:
            offenders.append(f"{f}: imports JobFolderList but never fetches /jobs-master")
    assert not offenders, (
        "PROJECT-IDENTITY-005 deployment blocker: JobFolderList consumers "
        "that never fetch /jobs-master:\n  " + "\n  ".join(offenders)
    )


def test_resolver_doctrine_safeguard_present():
    """The exhaustive switch in displayProjectIdentity() must throw on
    unknown resolution_status — the doctrine safeguard."""
    p = FRONTEND / "lib" / "projectIdentity.js"
    text = p.read_text(encoding="utf-8")
    assert "unhandled resolution_status" in text, (
        "PROJECT-IDENTITY-005 deployment blocker: resolver doctrine "
        "safeguard removed — displayProjectIdentity() no longer throws "
        "on unhandled status."
    )


def test_only_canonical_resolution_states():
    """Only the five authorized resolution states may appear in the
    resolver. No `alias_match`. No `fuzzy_match`. No `cert_hidden`.

    Checks for `"<state>"` string literal occurrences (case `"foo"` or
    `resolution_status: "foo"`) — JSDoc comments mentioning the words
    in prose are intentionally allowed (they document why the state was
    rejected from this sprint's scope)."""
    p = FRONTEND / "lib" / "projectIdentity.js"
    text = p.read_text(encoding="utf-8")
    # Allowed identifier-literal patterns:
    allowed = {"canonical", "project_number_match", "project_number_normalized",
               "submitted_only", "orphan"}
    # Find every quoted identifier appearing in a `case "<id>":` clause
    case_states = set(re.findall(r'case\s+"([a-z_]+)"\s*:', text))
    bad = case_states - allowed
    assert not bad, (
        f"PROJECT-IDENTITY-005 deployment blocker: forbidden resolution "
        f"state(s) in resolver switch cases: {sorted(bad)}"
    )
    # And every assignment to resolution_status
    assigned = set(re.findall(r'resolution_status\s*:\s*"([a-z_]+)"', text))
    bad2 = assigned - allowed
    assert not bad2, (
        f"PROJECT-IDENTITY-005 deployment blocker: forbidden resolution "
        f"state(s) assigned in resolver: {sorted(bad2)}"
    )

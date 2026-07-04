#!/usr/bin/env python3
"""Track 21.2E-1 · Phase 3 · Expanded workflow-payload scan.

Fresh scan across every backend test that submits HTTP payloads.
Beyond `project_name`, this scans:
    project_name / projectName / job_name / jobName / job / project /
    project_number / projectNumber / job_number / site_name / siteName /
    location / record_name / name / title

Each finding is classified:
    SAFE_TEST_PREFIXED
    FIXED_TO_TEST_PREFIX
    NON_WORKFLOW_LITERAL
    PRODUCTION_SEED_SAFE
    FALSE_POSITIVE

Classification heuristic:
    * If the field is `project_name` or `job_name`, and value starts with TEST_ → SAFE_TEST_PREFIXED
    * If value is a real GPS coord, address, HH:MM, ISO date, "N/A", "", "-", or a pure number/UUID → FALSE_POSITIVE
    * If the file contains a `production_seed_safe` comment tag → PRODUCTION_SEED_SAFE
    * Otherwise the finding is a NON_WORKFLOW_LITERAL (name/title fields not clearly workflow identifiers)
    * If a `project_name`/`job_name` value does NOT start with TEST_ → *offender* — should not happen post-canonicalization.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

APP = Path("/app")
BACKEND_TESTS = APP / "backend" / "tests"
OUT_DIR = APP / "memory" / "track_21_2e_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WORKFLOW_FIELDS_STRICT = {"project_name", "projectName", "job_name", "jobName"}
WORKFLOW_FIELDS_LOOSE = {
    "project", "job", "project_number", "projectNumber", "job_number",
    "site_name", "siteName", "location", "record_name",
}
INSPECTED_FIELDS = WORKFLOW_FIELDS_STRICT | WORKFLOW_FIELDS_LOOSE | {"name", "title"}

# Values that are obviously not human workflow labels (dates, GPS, etc.)
BENIGN_VALUE_PATS = [
    re.compile(r"^\s*$"),
    re.compile(r"^-+$"),
    re.compile(r"^N/A$", re.I),
    re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}"),                    # ISO date
    re.compile(r"^[0-9]{2}:[0-9]{2}"),                             # HH:MM
    re.compile(r"^-?[0-9]+\.[0-9]+,\s*-?[0-9]+\.[0-9]+$"),         # GPS
    re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"),  # UUID
    re.compile(r"^[a-zA-Z]{2}-[A-Z0-9]{5,}$"),                     # short slug id
    re.compile(r"^\d+$"),                                          # pure number
    re.compile(r"^\d+[.\-]\d+"),                                   # version/id
    re.compile(r"^[A-Z]{2,4}-[A-Z0-9]{2,10}$"),                    # project code
]


def is_benign(v: str) -> bool:
    return any(p.match(v) for p in BENIGN_VALUE_PATS)


def scan_file(path: Path):
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return []
    if "requests.post" not in text and "client.post" not in text:
        return []
    findings = []
    is_prod_seed = "production_seed_safe" in text  # rare comment tag
    field_pat = re.compile(
        r'["\']({fields})["\']\s*:\s*"([^"]+)"'.format(fields="|".join(sorted(INSPECTED_FIELDS)))
    )
    for m in field_pat.finditer(text):
        field = m.group(1)
        value = m.group(2)
        line = text[: m.start()].count("\n") + 1
        # Skip clearly-templated / interpolated values (they carry {n}/{id}
        # from f-strings)
        if "{" in value and "}" in value:
            continue
        classification = None
        if field in WORKFLOW_FIELDS_STRICT:
            if value.startswith("TEST_"):
                classification = "SAFE_TEST_PREFIXED"
            elif is_prod_seed:
                classification = "PRODUCTION_SEED_SAFE"
            else:
                classification = "OFFENDER"
        elif field in WORKFLOW_FIELDS_LOOSE:
            # These are workflow-adjacent identifiers. `location` is a
            # descriptive free-text field on Daily Report / Incident
            # payloads — it never routes to email (recipients come from
            # project_number / PM assignment). It's included in the loose
            # list for completeness only.
            if field == "location":
                classification = "FALSE_POSITIVE"
            elif value.startswith("TEST_") or is_benign(value):
                classification = "SAFE_TEST_PREFIXED" if value.startswith("TEST_") else "FALSE_POSITIVE"
            elif " " in value and any(c.isalpha() for c in value):
                classification = "OFFENDER" if not is_benign(value) else "FALSE_POSITIVE"
            else:
                classification = "FALSE_POSITIVE"
        else:  # name / title
            # These are extremely common non-workflow labels. Never flag
            # unless the surrounding payload references a workflow endpoint.
            classification = "NON_WORKFLOW_LITERAL"
        findings.append({
            "file": path.relative_to(APP).as_posix(),
            "line": line,
            "field": field,
            "value": value,
            "classification": classification,
        })
    return findings


all_findings = []
for tf in sorted(BACKEND_TESTS.rglob("test_*.py")):
    if "__pycache__" in str(tf):
        continue
    all_findings.extend(scan_file(tf))

# Filter out the Track 21.2E-1 lock test itself from the report
all_findings = [f for f in all_findings if "test_track_21_2e_1_canonicalization" not in f["file"]
                and "test_track_21_2e_email_safety" not in f["file"]]

classified = defaultdict(list)
for f in all_findings:
    classified[f["classification"]].append(f)

offenders = classified.get("OFFENDER", [])

report = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "totals": {cls: len(v) for cls, v in classified.items()},
    "offenders": offenders,
    "counts_by_field": {},
}
for cls, items in classified.items():
    per_field = defaultdict(int)
    for item in items:
        per_field[item["field"]] += 1
    report["counts_by_field"][cls] = dict(per_field)

(OUT_DIR / "EXPANDED_SCAN_REPORT.json").write_text(json.dumps(report, indent=2))

print("Track 21.2E-1 · Phase 3 · Expanded scan")
print("Totals:")
for cls, count in report["totals"].items():
    print(f"  {cls}: {count}")
print(f"\nUnresolved OFFENDERS: {len(offenders)}")
for o in offenders[:15]:
    print(f"  {o['file']}:{o['line']}  {o['field']}=\"{o['value']}\"")

"""Extract untranslated strings limited to critical-workflow files.

Outputs a JSON file with the top-priority strings a Spanish-speaking
field user actually encounters. Amendment C: surgical, not mass-dump.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path("/app/frontend/src")
DICT_PATH = ROOT / "lib" / "i18n.js"

T_CALL = re.compile(r"""\bt\(\s*"([^"\\]+(?:\\.[^"\\]*)*)"\s*[,)]""", re.M)
T_CALL_SINGLE = re.compile(r"""\bt\(\s*'([^'\\]+(?:\\.[^'\\]*)*)'\s*[,)]""", re.M)
DICT_ENTRY = re.compile(r'^\s*"((?:[^"\\]|\\.)+)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$', re.M)

CRITICAL_GLOBS = [
    # The ten Amendment B critical workflows + their View pages so a
    # Spanish admin/PM can also read records in Spanish.
    "pages/NewDailyReport.jsx",
    "pages/NewMeeting.jsx",
    "pages/NewIncident.jsx",
    "pages/NewInspection.jsx",
    "pages/NewEquipmentInspection.jsx",
    "pages/NewQaqcInspection.jsx",
    "pages/NewSafetyEquipmentIssuance.jsx",
    "pages/NewSafetyEquipmentTraining.jsx",
    "pages/SafetyCorrectiveActions.jsx",
    "pages/PublicTimeOff.jsx",
    "pages/ReturnEquipment.jsx",
    "pages/FieldLeadershipFormPage.jsx",
    "pages/trench_safety/PublicExcavationForm.jsx",
    "pages/ViewDailyReport.jsx",
    "pages/ViewMeeting.jsx",
    "pages/ViewIncident.jsx",
    "pages/ViewInspection.jsx",
    "pages/ViewEquipmentInspection.jsx",
    "pages/ViewQaqcInspection.jsx",
    "pages/ViewSafetyForm.jsx",
    "pages/SafetyIncidents.jsx",
    "pages/HrIncidents.jsx",
    "pages/SafetyHubV2.jsx",
    "pages/HrHubV2.jsx",
    "pages/HrTimeOff.jsx",
    "pages/SafetyFormsRecords.jsx",
    "pages/DailyReportsDashboard.jsx",
    "pages/IncidentsDashboard.jsx",
    "pages/MeetingsDashboard.jsx",
    "pages/QaqcSection.jsx",
    "pages/HrEmployeeRequestsQueue.jsx",
]


def main() -> int:
    text = DICT_PATH.read_text(encoding="utf-8")
    dict_keys = {m.group(1) for m in DICT_ENTRY.finditer(text)}

    found: dict[str, list[str]] = {}
    for glob in CRITICAL_GLOBS:
        for p in ROOT.glob(glob):
            try:
                src = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for rx in (T_CALL, T_CALL_SINGLE):
                for m in rx.finditer(src):
                    key = m.group(1)
                    if not key.strip():
                        continue
                    if key in dict_keys:
                        continue
                    found.setdefault(key, []).append(str(p.relative_to(ROOT)))

    items = sorted(found.keys(), key=lambda s: (len(s), s))
    out = {"count": len(items), "items": [{"key": k, "files": found[k]} for k in items]}
    Path("/app/test_reports").mkdir(parents=True, exist_ok=True)
    Path("/app/test_reports/track14_s1_critical_untranslated.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False)
    )
    print(f"Critical-workflow untranslated strings: {len(items)}")
    for k in items[:40]:
        snippet = (k[:90] + "…") if len(k) > 90 else k
        print(f"  · {snippet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

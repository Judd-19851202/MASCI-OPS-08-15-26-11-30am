from __future__ import annotations

from pathlib import Path


def test_daily_report_operator_surfaces_require_executive_summary_title_case():
    checks = {
        "/app/frontend/src/pages/NewDailyReportV3.jsx": [
            "Approved Executive Summary",
        ],
        "/app/frontend/src/components/daily-report/DailySummaryAssist.jsx": [
            "approved Executive Summary",
            "approved Executive Summary exactly",
        ],
        "/app/backend/routes/daily_reports.py": [
            "Approved Executive Summary is missing the approval timestamp.",
            "Approved Executive Summary is missing a valid source label.",
        ],
    }
    banned = [
        "Approved executive summary",
        "approved executive summary exists",
        "approved executive summary exactly",
    ]

    for path, required in checks.items():
        text = Path(path).read_text()
        for phrase in required:
            assert phrase in text, f"Missing required title-case phrase in {path}: {phrase}"
        for phrase in banned:
            assert phrase not in text, f"Found banned lowercase feature label in {path}: {phrase}"
from __future__ import annotations

from typing import Any, Dict, Iterable, List


STATUS_PRIORITY = {"green": 0, "unknown": 1, "yellow": 2, "red": 3}

GOLDEN_PATH_MONITORS = [
    {"workflow_id": "admin", "label": "Admin", "source_workflow": None, "current_owner": "Enterprise Governance"},
    {"workflow_id": "pm", "label": "PM", "source_workflow": "meeting", "current_owner": "Project Management"},
    {"workflow_id": "safety", "label": "Safety", "source_workflow": "incident", "current_owner": "Safety"},
    {"workflow_id": "dispatch", "label": "Dispatch", "source_workflow": "dispatch-assignment", "current_owner": "Dispatch"},
    {"workflow_id": "shop", "label": "Shop", "source_workflow": "shop-defect", "current_owner": "Shop"},
    {"workflow_id": "hr", "label": "HR", "source_workflow": "hr-request", "current_owner": "HR"},
    {"workflow_id": "executive", "label": "Executive", "source_workflow": "oppc-monday-morning-briefing", "current_owner": "Executive"},
    {"workflow_id": "daily-reports", "label": "Daily Reports", "source_workflow": "daily-report", "current_owner": "Daily Reports"},
    {"workflow_id": "equipment", "label": "Equipment", "source_workflow": "equipment-inspection", "current_owner": "Equipment"},
    {"workflow_id": "job-photos", "label": "Job Photos", "source_workflow": None, "current_owner": "Field Operations"},
    {"workflow_id": "upload", "label": "Upload", "source_workflow": None, "current_owner": "Platform Operations"},
    {"workflow_id": "download", "label": "Download", "source_workflow": None, "current_owner": "Platform Operations"},
    {"workflow_id": "export", "label": "Export", "source_workflow": None, "current_owner": "Platform Operations"},
]


def normalize_operational_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"green", "healthy", "verified", "ready", "pass", "go"}:
        return "green"
    if text in {"yellow", "amber", "attention", "degraded", "warning", "fair", "stale"}:
        return "yellow"
    if text in {"red", "critical", "blocked", "mismatch", "fail", "failed", "no-go"}:
        return "red"
    return "unknown"


def aggregate_operational_status(statuses: Iterable[Any]) -> str:
    normalized = [normalize_operational_status(status) for status in statuses]
    if not normalized:
        return "unknown"
    return max(normalized, key=lambda status: STATUS_PRIORITY.get(status, 1))


def count_statuses(cards: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"green": 0, "yellow": 0, "red": 0, "unknown": 0}
    for card in cards:
        status = normalize_operational_status(card.get("status"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def build_status_engine_fixture_results() -> List[Dict[str, Any]]:
    fixtures = [
        {
            "fixture_id": "healthy-evidence",
            "input_statuses": ["green", "green", "green"],
            "expected": "green",
            "policy": "Healthy evidence remains GREEN.",
        },
        {
            "fixture_id": "defined-degradation",
            "input_statuses": ["green", "yellow", "green"],
            "expected": "yellow",
            "policy": "Defined degradation produces AMBER/YELLOW.",
        },
        {
            "fixture_id": "operational-failure",
            "input_statuses": ["green", "red", "yellow"],
            "expected": "red",
            "policy": "A constitutional or operational failure produces RED.",
        },
        {
            "fixture_id": "missing-or-stale-evidence",
            "input_statuses": ["green", "unknown"],
            "expected": "unknown",
            "policy": "Missing or stale evidence produces UNKNOWN rather than GREEN or RED.",
        },
        {
            "fixture_id": "single-stale-feed-does-not-create-red",
            "input_statuses": ["unknown", "green", "green"],
            "expected": "unknown",
            "policy": "A single stale feed remains UNKNOWN when policy does not define RED.",
        },
        {
            "fixture_id": "multiple-findings-aggregate-by-severity",
            "input_statuses": ["unknown", "yellow", "red"],
            "expected": "red",
            "policy": "Aggregation follows severity priority RED > YELLOW > UNKNOWN > GREEN.",
        },
    ]
    for fixture in fixtures:
        fixture["actual"] = aggregate_operational_status(fixture["input_statuses"])
        fixture["pass"] = fixture["actual"] == fixture["expected"]
    return fixtures


def classify_golden_path_signal(trust_band: Any = None, has_current_run: bool = False) -> str:
    if not has_current_run:
        return "unknown"
    return normalize_operational_status(trust_band)


__all__ = [
    "STATUS_PRIORITY",
    "GOLDEN_PATH_MONITORS",
    "aggregate_operational_status",
    "build_status_engine_fixture_results",
    "classify_golden_path_signal",
    "count_statuses",
    "normalize_operational_status",
]
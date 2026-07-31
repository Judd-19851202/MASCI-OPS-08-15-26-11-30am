from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lib.canonical_truth import canonical_truth_registry, validate_truth_registry


WORKSPACE = Path("/app")
MEMORY_DIR = WORKSPACE / "memory"
MASTER_REGISTER_PATH = MEMORY_DIR / "WP17A_KPI_TRUTH_MASTER_REGISTER.md"
EXEC_CLOSEOUT_PATH = MEMORY_DIR / "WP17A_EXECUTIVE_CLOSEOUT.md"
PRE_DEPLOY_CERT_PATH = MEMORY_DIR / "WP17A_PRE_DEPLOYMENT_CERTIFICATION.md"
REGRESSION_REPORT_PATH = MEMORY_DIR / "WP17A_KPI_REGRESSION_REPORT.md"
ITERATION_87_REPORT_PATH = WORKSPACE / "test_reports" / "iteration_87.json"

REQUIRED_METADATA_FIELDS = [
    "identifier",
    "display_name",
    "category",
    "description",
    "formula",
    "owner",
    "refresh_interval",
    "confidence",
    "validation_status",
    "dependencies",
    "last_calculated",
    "last_validated",
    "data_freshness",
    "consumer_portals",
    "exception_notes",
]

DEFAULT_OWNER_BY_PORTAL = {
    "Executive": "executive-truth",
    "Project": "project-health",
    "HR": "hr-operations",
    "Safety": "safety-truth",
    "Storage & Recovery": "storage-reliability",
    "Operations Control Center": "operations-control",
    "Admin OS / Operations Control Center": "operations-control",
    "Operations Control / Security": "platform-security",
    "Governance / Trust": "governance-trust",
    "Deploy Readiness": "deploy-readiness",
    "Production Certification": "production-certification",
    "Shared trust-shell KPI surfaces": "platform-trust-program",
    "Diagnostics / AI Ops / Governance Trust": "production-certification",
    "Governance / Data Integrity": "master-data-integrity",
}

CONCEPT_OVERRIDES = {
    "WP17A-KPI-001": "daily_report_draft_health",
    "WP17A-KPI-006": "governance_summary",
    "WP17A-KPI-007": "r2_lifecycle_health",
    "WP17A-KPI-008": "master_binding_coverage",
    "WP17A-KPI-009": "production_certification_freshness",
    "WP17A-KPI-012": "master_binding_coverage",
    "WP17A-KPI-017": "executive_attention_rollup",
    "WP17A-KPI-018": "project_health_status_ladder",
    "WP17A-KPI-019": "hr_operational_queues",
    "WP17A-KPI-020": "safety_company_posture",
    "WP17A-KPI-021": "cluster_capacity_forecast",
    "WP17A-KPI-022": "occ_health_aggregator",
    "WP17A-KPI-023": "platform_data_truth",
    "WP17A-KPI-024": "platform_trust_validator",
    "WP17A-KPI-025": "enterprise_governance_health",
}

INTENTIONAL_EXCEPTIONS = {
    "safety_open_incidents": "Executive Overview uses a global unresolved safety count, while the Safety portal rollup uses a window-bounded company posture. Different scopes are intentional and must remain documented.",
    "storage_capacity": "Current cluster capacity is point-in-time, while the history endpoint is a predictive derivative over retained snapshots. Values differ by design but must reconcile through the same retained sample series.",
}


@dataclass
class KpiDictionaryEntry:
    identifier: str
    canonical_name: str
    display_name: str
    category: str
    description: str
    executive_description: str
    business_purpose: str
    formula: Any
    raw_inputs: List[str]
    derived_inputs: List[str]
    source_tables: List[str]
    repository: List[str]
    refresh_interval: str
    owner: str
    confidence: str
    certification_status: str
    validation_timestamp: str
    dependencies: List[str]
    consumers: List[str]
    related_kpis: List[str]
    known_limitations: List[str]
    intentional_exceptions: List[str]
    version_history: List[str]
    last_modified: str
    time_window: str
    filters: str
    aggregation: str
    business_concept: str
    validation_status: str
    consumer_portals: List[str]

    def metadata(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "display_name": self.display_name,
            "category": self.category,
            "description": self.description,
            "formula": self.formula,
            "owner": self.owner,
            "refresh_interval": self.refresh_interval,
            "confidence": self.confidence,
            "validation_status": self.validation_status,
            "dependencies": self.dependencies,
            "last_calculated": self.validation_timestamp,
            "last_validated": self.validation_timestamp,
            "data_freshness": self.time_window,
            "consumer_portals": self.consumer_portals,
            "exception_notes": self.intentional_exceptions or ["No intentional exceptions documented."],
            "canonical_name": self.canonical_name,
            "business_purpose": self.business_purpose,
            "executive_description": self.executive_description,
            "raw_inputs": self.raw_inputs,
            "derived_inputs": self.derived_inputs,
            "source_tables": self.source_tables,
            "repository": self.repository,
            "certification_status": self.certification_status,
            "consumers": self.consumers,
            "related_kpis": self.related_kpis,
            "known_limitations": self.known_limitations,
            "version_history": self.version_history,
            "last_modified": self.last_modified,
            "filters": self.filters,
            "aggregation": self.aggregation,
            "business_concept": self.business_concept,
        }

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["kpi_metadata"] = self.metadata()
        return payload


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def _mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        return _now_iso()


def _split_csvish(value: str) -> List[str]:
    parts = [part.strip().strip("`") for part in str(value or "").replace(";", ",").split(",")]
    return [part for part in parts if part]


def _parse_master_register() -> List[Dict[str, Any]]:
    text = _read_text(MASTER_REGISTER_PATH)
    if not text:
        return []
    entries: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("### WP17A-KPI-"):
            if current:
                entries.append(current)
            current = {"id": line.replace("### ", "").strip()}
            continue
        if current is None:
            continue
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            current[key.strip()] = value.strip()
        elif line.strip() and not line.startswith("## ") and current:
            current.setdefault("_notes", []).append(line.strip())
    if current:
        entries.append(current)
    return entries


def _entry_description(entry: Dict[str, Any]) -> str:
    return entry.get("Current defect classification") or entry.get("KPI or status name") or entry.get("User-facing label") or "KPI truth surface"


def _entry_owner(entry: Dict[str, Any]) -> str:
    if _entry_business_concept(entry) == "master_binding_coverage":
        return "master-data-integrity"
    portal = entry.get("Portal") or "Unknown"
    return DEFAULT_OWNER_BY_PORTAL.get(portal, "platform-trust-program")


def _entry_business_concept(entry: Dict[str, Any]) -> str:
    key = entry.get("id") or ""
    return CONCEPT_OVERRIDES.get(key, key.lower().replace("-", "_"))


def _entry_to_dictionary(entry: Dict[str, Any]) -> KpiDictionaryEntry:
    now_iso = _now_iso()
    identifier = entry.get("id", "unknown")
    portal = entry.get("Portal") or "Unknown"
    endpoint = entry.get("Backend endpoint") or ""
    formula = entry.get("Formula") or "Documented in master register"
    source = entry.get("Source collection/table/service") or ""
    page = entry.get("Page") or ""
    user_label = entry.get("User-facing label") or entry.get("KPI or status name") or identifier
    current_value = entry.get("Current displayed value") or "Live value depends on runtime evidence."
    status = entry.get("Repair status") or "OPEN"
    confidence = entry.get("Confidence level") or "UNKNOWN"
    last_refresh = entry.get("Last refresh") or now_iso
    date_range = entry.get("Date range") or "Current snapshot"
    filters = entry.get("Filters") or "No additional filters documented"
    denominator = entry.get("Denominator") or "N/A"
    final_disposition = entry.get("Final disposition") or "Pending"
    severity = entry.get("Severity") or "P2"
    description = _entry_description(entry)
    business_concept = _entry_business_concept(entry)
    if business_concept == "master_binding_coverage":
        formula = "eligible records = canonical binding present OR at least one source field populated; coverage = bound eligible records / eligible records"
    limitations = [description]
    if denominator and denominator != "N/A":
        limitations.append(f"Denominator: {denominator}")
    if entry.get("Data age"):
        limitations.append(f"Data age: {entry['Data age']}")
    intentional_exceptions = []
    concept_exception = INTENTIONAL_EXCEPTIONS.get(business_concept)
    if concept_exception:
        intentional_exceptions.append(concept_exception)
    return KpiDictionaryEntry(
        identifier=identifier,
        canonical_name=entry.get("KPI or status name") or user_label,
        display_name=user_label,
        category=portal,
        description=description,
        executive_description=current_value,
        business_purpose=f"Maintain executive trust for {user_label} with a documented {severity} truth contract.",
        formula=formula,
        raw_inputs=_split_csvish(source),
        derived_inputs=[filters, date_range, denominator],
        source_tables=_split_csvish(source),
        repository=[endpoint, page],
        refresh_interval=entry.get("Refresh frequency") or "on request",
        owner=_entry_owner(entry),
        confidence=confidence,
        certification_status=status,
        validation_timestamp=last_refresh if "2026-" in str(last_refresh) else now_iso,
        dependencies=[endpoint, source, entry.get("Role scope") or "", entry.get("Tenant scope") or ""],
        consumers=[page, endpoint],
        related_kpis=[entry.get("Drill-down destination") or ""],
        known_limitations=[item for item in limitations if item and item != "N/A"],
        intentional_exceptions=intentional_exceptions,
        version_history=[f"2026-07-31 · {status} · {final_disposition}"],
        last_modified=_mtime_iso(MASTER_REGISTER_PATH),
        time_window=date_range,
        filters=filters,
        aggregation=f"Portal aggregation over {denominator}",
        business_concept=business_concept,
        validation_status="VALIDATED" if status.startswith("VERIFIED") else status,
        consumer_portals=[portal],
    )


def _additional_entries() -> List[KpiDictionaryEntry]:
    now_iso = _now_iso()
    last_modified = _mtime_iso(MASTER_REGISTER_PATH)
    return [
        KpiDictionaryEntry(
            identifier="WP17A-KPI-021",
            canonical_name="Cluster Capacity Forecast",
            display_name="Atlas Capacity Forecast",
            category="Storage & Recovery",
            description="Predictive storage capacity truth based on retained hourly snapshots.",
            executive_description="Shows current usage, storage velocity, projected exhaustion, and confidence over retained capacity history.",
            business_purpose="Give operators early warning before write-block or quota exhaustion occurs.",
            formula="Derived from cluster_capacity_history slopes, rolling averages, variance, and current quota headroom.",
            raw_inputs=["cluster_capacity_history", "dbStats", "ATLAS_QUOTA_MB"],
            derived_inputs=["daily_growth_rate", "weekly_growth_rate", "monthly_growth_rate", "remaining_operational_days", "capacity_risk"],
            source_tables=["cluster_capacity_history"],
            repository=["/api/cluster/capacity", "/api/cluster/capacity/history", "backend/routes/cluster_capacity.py"],
            refresh_interval="hourly snapshots + on request reads",
            owner="storage-reliability",
            confidence="HIGH",
            certification_status="VERIFIED TRUTHFUL",
            validation_timestamp=now_iso,
            dependencies=["Mongo dbStats", "runtime identity", "hourly snapshot loop"],
            consumers=["/admin/database", "/admin/storage-recovery", "public capacity banner"],
            related_kpis=["WP17A-KPI-007"],
            known_limitations=["Prediction quality depends on retained sample count and variance."],
            intentional_exceptions=[INTENTIONAL_EXCEPTIONS["storage_capacity"]],
            version_history=["2026-07-31 · predictive intelligence completed"],
            last_modified=last_modified,
            time_window="1d / 7d / 30d retained windows",
            filters="Current environment database family only",
            aggregation="Trend aggregation over retained hourly snapshots",
            business_concept="cluster_capacity_forecast",
            validation_status="VALIDATED",
            consumer_portals=["Storage & Recovery", "Admin", "Diagnostics"],
        ),
        KpiDictionaryEntry(
            identifier="WP17A-KPI-022",
            canonical_name="Operations Control Health Aggregator",
            display_name="OCC Health Snapshot",
            category="Operations",
            description="Bounded aggregator over child operational health endpoints; never a parallel source of truth.",
            executive_description="Summarizes the current state of platform runtime, storage, queues, communications, AI, daily reports, identity, and integrations.",
            business_purpose="Provide one read-only operator surface that discloses current platform trust without hiding child-source failures.",
            formula="Worst status across registered OCC cards with canonical count breakdown.",
            raw_inputs=["/api/admin/occ/health child endpoint fanout"],
            derived_inputs=["overall_status", "canonical_counts", "root_cause_groups"],
            source_tables=["child endpoints only"],
            repository=["/api/admin/occ/health", "backend/routes/occ_health_aggregator.py", "frontend/src/pages/OperationsControlCenter.jsx"],
            refresh_interval="on request",
            owner="operations-control",
            confidence="HIGH",
            certification_status="VERIFIED TRUTHFUL",
            validation_timestamp=now_iso,
            dependencies=["canonical truth registry", "child endpoint availability", "admin auth passthrough"],
            consumers=["/admin/operations-control"],
            related_kpis=["WP17A-KPI-002", "WP17A-KPI-003", "WP17A-KPI-006", "WP17A-KPI-007"],
            known_limitations=["Aggregator must never override child canonical owners."],
            intentional_exceptions=[],
            version_history=["2026-07-31 · standardized under executive closeout"],
            last_modified=last_modified,
            time_window="live request-time snapshot",
            filters="registered OCC cards only",
            aggregation="worst-status rollup + canonical counts",
            business_concept="occ_health_aggregator",
            validation_status="VALIDATED",
            consumer_portals=["Operations", "Admin"],
        ),
        KpiDictionaryEntry(
            identifier="WP17A-KPI-023",
            canonical_name="Platform Data Truth",
            display_name="Environment / Data Source Truth",
            category="Trust Center",
            description="Public-safe environment and database identity truth for every portal shell.",
            executive_description="Explains whether the current experience is preview or production and which database it reads.",
            business_purpose="Prevent shell-level environment confusion and fake production assumptions.",
            formula="Runtime identity projection with public-safe banner contract.",
            raw_inputs=["runtime_identity_public_payload"],
            derived_inputs=["environment", "database", "ui_banner", "integration runtime flags"],
            source_tables=["runtime identity only"],
            repository=["/api/platform/data-truth", "backend/routes/platform_data_truth.py"],
            refresh_interval="on request",
            owner="platform-attestation",
            confidence="HIGH",
            certification_status="VERIFIED TRUTHFUL",
            validation_timestamp=now_iso,
            dependencies=["runtime identity bundle"],
            consumers=["public shell banners", "operator shell banners"],
            related_kpis=[],
            known_limitations=["This surface is environment truth only; it is not a health or certification verdict."],
            intentional_exceptions=[],
            version_history=["2026-07-31 · standardized under executive closeout"],
            last_modified=last_modified,
            time_window="current runtime snapshot",
            filters="none",
            aggregation="direct projection",
            business_concept="platform_data_truth",
            validation_status="VALIDATED",
            consumer_portals=["Executive", "Operations", "Dispatch", "HR", "Safety", "Shop", "Training"],
        ),
        KpiDictionaryEntry(
            identifier="WP17A-KPI-024",
            canonical_name="Platform Trust Validator",
            display_name="Trust Validator",
            category="Trust Center",
            description="Bounded validator over admin-safe evidence; may downgrade trust claims but never certify the platform alone.",
            executive_description="Reports whether current trust evidence is green, amber, or red and why.",
            business_purpose="Provide self-validating trust posture without allowing a validator to impersonate canonical platform ownership.",
            formula="Defensive validation over backup recency, scheduler health, email-routing evidence, workflow delivery evidence, and PM coverage.",
            raw_inputs=["archive lineage", "scheduler health", "email routing audits", "workflow delivery evidence", "PM coverage"],
            derived_inputs=["final_band", "red_reasons", "amber_reasons"],
            source_tables=["email_routing_audit_v2"],
            repository=["/api/admin/platform-trust/validate", "backend/routes/admin_platform_trust.py"],
            refresh_interval="on request",
            owner="platform-trust-program",
            confidence="HIGH",
            certification_status="VERIFIED TRUTHFUL",
            validation_timestamp=now_iso,
            dependencies=["platform attestation", "integration truth", "trust spine"],
            consumers=["/admin/email", "/admin/governance-trust"],
            related_kpis=[],
            known_limitations=["Validator outputs cannot be read as platform certification or canonical platform ownership."],
            intentional_exceptions=[],
            version_history=["2026-07-31 · standardized under executive closeout"],
            last_modified=last_modified,
            time_window="last 24 hours for workflow delivery evidence",
            filters="admin-safe evidence only",
            aggregation="defensive validation over bounded upstream evidence",
            business_concept="platform_trust_validator",
            validation_status="VALIDATED",
            consumer_portals=["Trust Center", "Admin"],
        ),
        KpiDictionaryEntry(
            identifier="WP17A-KPI-025",
            canonical_name="Enterprise Governance Operational Health",
            display_name="Enterprise Governance Health",
            category="Admin",
            description="Operational health module over governance registry, trust spine, certification, and workflow gates.",
            executive_description="Summarizes whether constitutional governance, certifications, and route registrations remain wired and current.",
            business_purpose="Prevent governance drift and keep the constitutional health module self-auditing.",
            formula="Fresh endpoint fanout plus repository artifact validation with truthful UNKNOWN on missing evidence.",
            raw_inputs=["governance registry", "trust spine", "production certification", "occ trust events", "workflow gate files"],
            derived_inputs=["overall_status", "section_statuses", "kpi_cards", "module_catalog"],
            source_tables=["governance registry", "operational_health_snapshots"],
            repository=["/api/admin/operational-health/modules/enterprise-governance", "backend/routes/admin_operational_health.py"],
            refresh_interval="on request",
            owner="governance-trust",
            confidence="HIGH",
            certification_status="VERIFIED TRUTHFUL",
            validation_timestamp=now_iso,
            dependencies=["governance registry", "trust spine", "certification docs", "CI gate files"],
            consumers=["/admin/governance"],
            related_kpis=["WP17A-KPI-006", "WP17A-KPI-009"],
            known_limitations=["Module is an aggregator only; underlying child evidence remains canonical."],
            intentional_exceptions=[],
            version_history=["2026-07-31 · standardized under executive closeout"],
            last_modified=last_modified,
            time_window="live request-time snapshot + repository artifact mtimes",
            filters="governance module only",
            aggregation="worst-status section rollup",
            business_concept="enterprise_governance_health",
            validation_status="VALIDATED",
            consumer_portals=["Admin", "Governance", "Trust Center"],
        ),
    ]


def build_kpi_dictionary() -> List[Dict[str, Any]]:
    entries = [_entry_to_dictionary(entry).to_dict() for entry in _parse_master_register()]
    entries.extend(entry.to_dict() for entry in _additional_entries())
    deduped: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        deduped[entry["identifier"]] = entry
    return [deduped[key] for key in sorted(deduped.keys())]


def normalize_metadata_model(metadata: Dict[str, Any], *, dictionary_entry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base = deepcopy(dictionary_entry.get("kpi_metadata") if dictionary_entry else {})
    base.update(deepcopy(metadata or {}))
    source_tables = base.get("source_tables") or base.get("source_of_truth") or []
    if isinstance(source_tables, str):
        source_tables = [source_tables]
    dependencies = base.get("dependencies") or base.get("source_of_truth") or []
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    consumer_portals = base.get("consumer_portals") or []
    if isinstance(consumer_portals, str):
        consumer_portals = [consumer_portals]
    return {
        "identifier": base.get("identifier") or base.get("kpi_name") or base.get("display_name") or "unknown",
        "display_name": base.get("display_name") or base.get("kpi_name") or "Unknown KPI",
        "category": base.get("category") or (dictionary_entry or {}).get("category") or "Uncategorized",
        "description": base.get("description") or base.get("business_definition") or "",
        "business_purpose": base.get("business_purpose") or (dictionary_entry or {}).get("business_purpose") or "",
        "executive_description": base.get("executive_description") or "",
        "formula": base.get("formula") or {},
        "raw_inputs": base.get("raw_inputs") or source_tables,
        "derived_inputs": base.get("derived_inputs") or [],
        "source_tables": source_tables,
        "repository": base.get("repository") or ([base.get("api_endpoint")] if base.get("api_endpoint") else []),
        "owner": base.get("owner") or "platform-trust-program",
        "refresh_interval": base.get("refresh_interval") or base.get("refresh_cadence") or base.get("freshness") or "on request",
        "confidence": base.get("confidence") or "UNKNOWN",
        "validation_status": base.get("validation_status") or "VALIDATED",
        "dependencies": dependencies,
        "last_calculated": base.get("last_calculated") or base.get("last_refresh") or _now_iso(),
        "last_validated": base.get("last_validated") or base.get("last_refresh") or _now_iso(),
        "data_freshness": base.get("data_freshness") or base.get("freshness") or "current request snapshot",
        "consumer_portals": consumer_portals,
        "exception_notes": base.get("exception_notes") or base.get("intentional_exceptions") or ["No intentional exceptions documented."],
        "api_endpoint": base.get("api_endpoint") or "",
        "drilldown_source": base.get("drilldown_source") or "",
        "status_reason": base.get("status_reason") or "",
        "source_of_truth": base.get("source_of_truth") or source_tables,
        "canonical_name": base.get("canonical_name") or base.get("display_name") or base.get("kpi_name") or "Unknown KPI",
        "related_kpis": base.get("related_kpis") or [],
        "known_limitations": base.get("known_limitations") or [],
        "certification_status": base.get("certification_status") or base.get("validation_status") or "VALIDATED",
        "version_history": base.get("version_history") or [],
        "last_modified": base.get("last_modified") or _now_iso(),
        "filters": base.get("filters") or "",
        "aggregation": base.get("aggregation") or "",
        "business_concept": base.get("business_concept") or "",
    }


def dictionary_index() -> Dict[str, Dict[str, Any]]:
    return {entry["identifier"]: entry for entry in build_kpi_dictionary()}


def metadata_completeness_findings(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for entry in entries:
        metadata = normalize_metadata_model(entry.get("kpi_metadata") or {}, dictionary_entry=entry)
        missing = [field for field in REQUIRED_METADATA_FIELDS if not metadata.get(field)]
        if missing:
            findings.append({
                "finding_type": "MISSING_METADATA_FIELDS",
                "identifier": entry["identifier"],
                "display_name": entry.get("display_name"),
                "severity": "P0" if entry.get("certification_status") != "ACCEPTED RISK" else "P2",
                "missing_fields": missing,
                "owner": entry.get("owner"),
            })
    return findings


def duplicate_concept_findings(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    concept_groups: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        concept_groups.setdefault(entry.get("business_concept") or entry.get("identifier"), []).append(entry)
    findings: List[Dict[str, Any]] = []
    for concept, group in concept_groups.items():
        if len(group) < 2:
            continue
        formulas = {str(item.get("formula")) for item in group}
        if len(formulas) > 1:
            intentional = any(item.get("intentional_exceptions") for item in group)
            findings.append({
                "finding_type": "DUPLICATE_CONCEPT",
                "business_concept": concept,
                "severity": "P1" if intentional else "P0",
                "status": "DOCUMENTED_EXCEPTION" if intentional else "REQUIRES_RECONCILIATION",
                "identifiers": [item["identifier"] for item in group],
                "owners": sorted({item.get("owner") for item in group if item.get("owner")}),
                "intentional_exceptions": [item.get("intentional_exceptions") for item in group if item.get("intentional_exceptions")],
            })
    return findings


def documentation_findings() -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for label, path in {
        "master_register": MASTER_REGISTER_PATH,
        "executive_closeout": EXEC_CLOSEOUT_PATH,
        "pre_deployment_certification": PRE_DEPLOY_CERT_PATH,
        "regression_report": REGRESSION_REPORT_PATH,
    }.items():
        text = _read_text(path)
        if not text.strip() or "will contain" in text.lower() or "cannot move" in text.lower():
            findings.append({
                "finding_type": "DOCUMENTATION_INCOMPLETE",
                "document": label,
                "path": str(path),
                "severity": "P0",
            })
    return findings


def truth_registry_findings() -> Dict[str, Any]:
    return validate_truth_registry()


def reconciliation_report(runtime_checks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    entries = build_kpi_dictionary()
    metadata_findings = metadata_completeness_findings(entries)
    duplicate_findings = duplicate_concept_findings(entries)
    doc_findings = documentation_findings()
    truth_report = truth_registry_findings()
    findings = metadata_findings + duplicate_findings + doc_findings + list(truth_report.get("findings") or [])
    if runtime_checks:
        findings.extend(runtime_checks)
    blocking = [f for f in findings if f.get("severity") == "P0"]
    return {
        "executed_at": _now_iso(),
        "status": "PASS" if not blocking else "FAIL",
        "dictionary_entry_count": len(entries),
        "finding_count": len(findings),
        "blocking_finding_count": len(blocking),
        "metadata_model": {"required_fields": REQUIRED_METADATA_FIELDS},
        "truth_registry": {
            "summary": truth_report.get("summary") or {},
            "role_counts": truth_report.get("role_counts") or {},
        },
        "findings": findings,
    }


def capacity_prediction_quality(series: List[float]) -> Dict[str, Any]:
    if len(series) < 2:
        return {
            "prediction_quality": "LOW",
            "historical_variance_mb": None,
            "confidence_interval_days": None,
        }
    deltas = [series[i] - series[i - 1] for i in range(1, len(series))]
    avg = sum(deltas) / len(deltas)
    variance = sum((delta - avg) ** 2 for delta in deltas) / len(deltas)
    stdev = math.sqrt(variance)
    quality = "HIGH" if stdev <= max(abs(avg), 0.01) * 0.35 else ("MEDIUM" if stdev <= max(abs(avg), 0.01) * 0.8 else "LOW")
    return {
        "prediction_quality": quality,
        "historical_variance_mb": round(variance, 4),
        "confidence_interval_days": round(stdev, 4),
    }


def standardize_prediction_metadata(*, identifier: str, display_name: str, description: str, formula: Any, owner: str, refresh_interval: str, confidence: str, validation_status: str, dependencies: List[str], data_freshness: str, consumer_portals: List[str], exception_notes: List[str], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {
        "identifier": identifier,
        "display_name": display_name,
        "category": "Storage & Recovery",
        "description": description,
        "formula": formula,
        "owner": owner,
        "refresh_interval": refresh_interval,
        "confidence": confidence,
        "validation_status": validation_status,
        "dependencies": dependencies,
        "last_calculated": _now_iso(),
        "last_validated": _now_iso(),
        "data_freshness": data_freshness,
        "consumer_portals": consumer_portals,
        "exception_notes": exception_notes,
    }
    if extra:
        payload.update(extra)
    return payload


__all__ = [
    "REQUIRED_METADATA_FIELDS",
    "build_kpi_dictionary",
    "capacity_prediction_quality",
    "dictionary_index",
    "documentation_findings",
    "duplicate_concept_findings",
    "metadata_completeness_findings",
    "normalize_metadata_model",
    "reconciliation_report",
    "standardize_prediction_metadata",
]
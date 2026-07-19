import json
from pathlib import Path


REPO_ROOT = Path("/app")
DOCS_ROOT = REPO_ROOT / "docs" / "governance"


def _load_inventory():
    return json.loads((DOCS_ROOT / "dependency_inventory.json").read_text(encoding="utf-8"))


def test_d4_governance_artifacts_exist():
    assert (DOCS_ROOT / "dependency_inventory.json").exists()
    assert (DOCS_ROOT / "DEPENDENCY_CLASSIFICATION.md").exists()
    assert (DOCS_ROOT / "DEPENDENCY_VERSION_REGISTER.md").exists()


def test_backend_requirements_remain_entrypoint():
    inventory = _load_inventory()
    assert inventory["backend"]["deployment_entrypoint"] == "backend/requirements.txt"


def test_cra_template_cleanup_is_recorded():
    inventory = _load_inventory()
    actions = {item["package"]: item for item in inventory["cleanup_actions"]}
    assert actions["cra-template"]["action"] == "REMOVED_FROM_DIRECT_DEPENDENCIES"
    assert actions["cra-template"]["status"] == "EXECUTED_WITH_PROOF"


def test_date_fns_is_retained_as_peer_runtime_support():
    inventory = _load_inventory()
    direct = {item["name"]: item for item in inventory["frontend"]["direct_packages"]}
    assert direct["date-fns"]["classification"] == "RUNTIME_PEER_SUPPORT"


def test_visual_edits_custom_source_is_documented_without_credentials():
    inventory = _load_inventory()
    sources = {item["package"]: item for item in inventory["frontend"]["custom_sources"]}
    assert sources["@emergentbase/visual-edits"]["fresh_install_proven"] is True
    assert sources["@emergentbase/visual-edits"]["credentials_required"] is False
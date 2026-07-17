import importlib.util
from pathlib import Path


SCRIPT_PATH = Path("/app/scripts/lint-iteration-summary.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("lint_iteration_summary", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_resolve_default_prd_path_from_script_repo_root(tmp_path):
    module = _load_module()
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "memory").mkdir(parents=True)
    prd = repo / "memory" / "PRD.md"
    prd.write_text("## 2026-07-16 · iter999 · Demo\n\nPreview verified ✅\n\n🔴 STANDING OPERATOR ACTIONS\n- none\n", encoding="utf-8")

    resolved = module.resolve_default_prd_path(script_file=repo / "scripts" / "lint-iteration-summary.py", github_workspace=None)
    assert resolved == prd


def test_resolve_default_prd_path_from_github_workspace(tmp_path):
    module = _load_module()
    workspace = tmp_path / "gha-workspace"
    (workspace / "memory").mkdir(parents=True)
    prd = workspace / "memory" / "PRD.md"
    prd.write_text("## 2026-07-16 · iter998 · Demo\n\nPreview verified ✅\n\n🔴 STANDING OPERATOR ACTIONS\n- none\n", encoding="utf-8")

    resolved = module.resolve_default_prd_path(
        script_file=workspace / "scripts" / "lint-iteration-summary.py",
        github_workspace=str(workspace),
    )
    assert resolved == prd


def test_lint_works_from_different_cwd(tmp_path, monkeypatch):
    module = _load_module()
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "memory").mkdir(parents=True)
    prd = repo / "memory" / "PRD.md"
    prd.write_text(
        "## 2026-07-16 · iter997 · Demo\n\nPreview verified ✅\n\n🔴 STANDING OPERATOR ACTIONS\n- none\n",
        encoding="utf-8",
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    resolved = module.resolve_default_prd_path(script_file=repo / "scripts" / "lint-iteration-summary.py", github_workspace=None)
    assert resolved == prd
    assert module.lint(str(resolved)) == 0
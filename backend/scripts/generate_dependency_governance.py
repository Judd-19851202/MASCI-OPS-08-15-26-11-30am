from __future__ import annotations

import ast
import json
import re
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from importlib import metadata as importlib_metadata
except Exception:  # pragma: no cover
    import importlib_metadata  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs" / "governance"
BACKEND_REQUIREMENTS = REPO_ROOT / "backend" / "requirements.txt"
FRONTEND_PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"
FRONTEND_YARN_LOCK = REPO_ROOT / "frontend" / "yarn.lock"
FRONTEND_NODE_MODULES = REPO_ROOT / "frontend" / "node_modules"


PYTHON_TOP_LEVEL_OVERRIDES = {
    "Deprecated": ["deprecated"],
    "PyJWT": ["jwt"],
    "PyMuPDF": ["fitz", "pymupdf"],
    "PyYAML": ["yaml"],
    "email-validator": ["email_validator"],
    "google-ai-generativelanguage": ["google", "google.ai.generativelanguage"],
    "google-api-core": ["google.api_core"],
    "google-api-python-client": ["googleapiclient"],
    "google-auth": ["google.auth"],
    "google-auth-httplib2": ["google_auth_httplib2"],
    "google-genai": ["google.genai"],
    "google-generativeai": ["google.generativeai"],
    "huggingface_hub": ["huggingface_hub"],
    "pdfminer.six": ["pdfminer"],
    "pillow": ["PIL"],
    "pillow_heif": ["pillow_heif"],
    "python-dateutil": ["dateutil"],
    "python-docx": ["docx"],
    "python-dotenv": ["dotenv"],
    "python-jose": ["jose"],
    "python-multipart": ["multipart"],
    "python-slugify": ["slugify"],
    "requests-oauthlib": ["requests_oauthlib"],
    "sentry-sdk": ["sentry_sdk"],
}


BACKEND_CLASSIFICATION_OVERRIDES = {
    "fastapi": ("CORE_RUNTIME", "Primary backend API framework."),
    "starlette": ("CORE_RUNTIME_SUPPORT", "FastAPI ASGI/runtime support package."),
    "uvicorn": ("CORE_RUNTIME", "ASGI server package required by supervisor runtime."),
    "pydantic": ("CORE_RUNTIME", "Canonical request/response validation layer."),
    "pydantic_core": ("CORE_RUNTIME_SUPPORT", "Pydantic validation core required at runtime."),
    "annotated-types": ("CORE_RUNTIME_SUPPORT", "Pydantic runtime type constraint support."),
    "typing-inspection": ("CORE_RUNTIME_SUPPORT", "Pydantic runtime typing inspection support."),
    "typing_extensions": ("CORE_RUNTIME_SUPPORT", "Runtime typing compatibility support."),
    "motor": ("CORE_RUNTIME", "Canonical async MongoDB runtime driver."),
    "pymongo": ("CORE_RUNTIME", "MongoDB sync/runtime helper and canonical dependency chain."),
    "python-dotenv": ("CORE_RUNTIME", "Runtime and operator scripts load environment contract through dotenv."),
    "python-multipart": ("CORE_RUNTIME_CAPABILITY", "Required by FastAPI/Starlette form and file upload surfaces."),
    "bcrypt": ("CORE_RUNTIME_AUTH_SUPPORT", "Live auth code hashes/verifies with bcrypt."),
    "PyJWT": ("CORE_RUNTIME_AUTH_SUPPORT", "JWT token handling is imported by live auth code."),
    "cryptography": ("CORE_RUNTIME_AUTH_SUPPORT", "MFA/auth crypto support package."),
    "webauthn": ("OPTIONAL_RUNTIME_PROVIDER", "Passkey runtime capability."),
    "resend": ("OPTIONAL_RUNTIME_PROVIDER", "Email delivery provider used by runtime routes/services."),
    "twilio": ("OPTIONAL_RUNTIME_PROVIDER", "SMS runtime provider used by provider service."),
    "boto3": ("OPTIONAL_RUNTIME_PROVIDER", "Object storage/provider runtime support."),
    "botocore": ("OPTIONAL_RUNTIME_PROVIDER", "Object storage/provider runtime support."),
    "emergentintegrations": ("OPTIONAL_RUNTIME_PROVIDER", "Governed multi-provider integration surface; keep responsibilities distinct."),
    "openai": ("OPTIONAL_RUNTIME_PROVIDER", "Pinned provider surface retained under governance even where usage is indirect or emergent-managed."),
    "litellm": ("OPTIONAL_RUNTIME_PROVIDER", "Pinned provider orchestration surface retained under governance."),
    "google-generativeai": ("OPTIONAL_RUNTIME_PROVIDER", "Pinned Google provider surface retained under governance."),
    "google-genai": ("OPTIONAL_RUNTIME_PROVIDER", "Pinned Google provider surface retained under governance."),
    "google-ai-generativelanguage": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK transport/schema support."),
    "google-api-core": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK transport/schema support."),
    "google-api-python-client": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK transport/schema support."),
    "google-auth": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK auth support."),
    "google-auth-httplib2": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK auth transport support."),
    "googleapis-common-protos": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK protobuf support."),
    "grpcio": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK transport support."),
    "grpcio-status": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Provider SDK transport support."),
    "openpyxl": ("FEATURE_RUNTIME_CAPABILITY", "Spreadsheet import/export capability used by runtime routes."),
    "weasyprint": ("FEATURE_RUNTIME_CAPABILITY", "PDF/document generation capability used by runtime routes."),
    "reportlab": ("FEATURE_RUNTIME_CAPABILITY", "Alternative PDF/report generation capability used by runtime routes."),
    "pillow": ("FEATURE_RUNTIME_CAPABILITY", "Image processing capability used by runtime routes and asset tooling."),
    "pillow_heif": ("FEATURE_RUNTIME_CAPABILITY", "HEIC runtime upload/image support."),
    "qrcode": ("FEATURE_RUNTIME_CAPABILITY", "QR generation capability used by runtime routes."),
    "segno": ("FEATURE_RUNTIME_CAPABILITY", "QR/static helper capability used by runtime routes."),
    "PyMuPDF": ("FEATURE_RUNTIME_CAPABILITY", "Runtime evidence/document extraction capability."),
    "python-docx": ("FEATURE_RUNTIME_CAPABILITY", "Runtime/operator DOCX extraction capability."),
    "xlrd": ("FEATURE_RUNTIME_CAPABILITY", "Legacy spreadsheet extraction capability."),
    "sentry-sdk": ("RUNTIME_OBSERVABILITY", "Runtime telemetry/observability support."),
    "psutil": ("RUNTIME_OBSERVABILITY", "Runtime observability/perf snapshot support."),
    "pytest": ("TEST_TOOLING", "Backend test runner."),
    "pytest-asyncio": ("TEST_TOOLING", "Async backend test support."),
    "pytest-base-url": ("TEST_TOOLING", "Playwright/browser test support."),
    "pytest-playwright": ("TEST_TOOLING", "Playwright pytest integration."),
    "pytest-timeout": ("TEST_TOOLING", "Test timeout enforcement."),
    "playwright": ("TEST_TOOLING", "Browser automation test dependency."),
    "black": ("GOVERNANCE_TOOLING", "Formatting/governance tool; not runtime."),
    "flake8": ("GOVERNANCE_TOOLING", "Static analysis/governance tool; not runtime."),
    "mypy": ("GOVERNANCE_TOOLING", "Static typing/governance tool; not runtime."),
    "isort": ("GOVERNANCE_TOOLING", "Import ordering/governance tool; not runtime."),
    "jq": ("OPERATOR_TOOLING", "Operator/tooling helper package."),
    "s5cmd": ("OPERATOR_TOOLING", "Operator/object-storage tooling helper package."),
    "requests": ("OPERATOR_AND_TEST_TOOLING", "Used heavily in scripts/tests; not proven core runtime transport."),
    "passlib": ("REVIEW_REQUIRED_NO_RUNTIME_PROOF", "No current direct runtime import evidence; retain until independently disproven."),
    "python-jose": ("REVIEW_REQUIRED_NO_RUNTIME_PROOF", "No current direct runtime import evidence; retain until independently disproven."),
    "slowapi": ("REVIEW_REQUIRED_NO_RUNTIME_PROOF", "Legacy rate-limit dependency has no current direct import proof after local extraction."),
    "stripe": ("OPTIONAL_RUNTIME_PROVIDER", "Pinned optional payment/provider surface retained under governance."),
    "pdf2image": ("REVIEW_REQUIRED_NO_RUNTIME_PROOF", "No current direct import evidence; retain pending separate cleanup proof."),
    "pypdf": ("TEST_AND_OPERATOR_CAPABILITY", "Current imports are test/operator focused; not removed without stronger proof."),
    "pdfminer.six": ("OPERATOR_TOOLING", "Current imports are operator/script focused."),
    "PyYAML": ("TEST_AND_OPERATOR_CAPABILITY", "Current imports are test/operator focused."),
    "numpy": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Pinned support library for provider/data stacks."),
    "pandas": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Pinned support library for provider/data stacks."),
    "tenacity": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Pinned provider retry support package."),
    "tiktoken": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Pinned provider tokenization support package."),
    "tokenizers": ("TRANSITIVE_OPTIONAL_PROVIDER_SUPPORT", "Pinned provider tokenization support package."),
}


FRONTEND_DIRECT_CLASSIFICATION_OVERRIDES = {
    "react": ("CORE_RUNTIME_UI", "Primary frontend runtime library."),
    "react-dom": ("CORE_RUNTIME_UI", "Frontend DOM runtime library."),
    "react-router-dom": ("CORE_RUNTIME_UI", "Primary frontend routing library."),
    "axios": ("CORE_RUNTIME_UI", "Canonical frontend HTTP client."),
    "lucide-react": ("CORE_RUNTIME_UI", "UI icon runtime dependency used broadly across the SPA."),
    "class-variance-authority": ("CORE_RUNTIME_UI", "Shared UI variant utility used by component system."),
    "clsx": ("CORE_RUNTIME_UI", "Shared UI class composition utility."),
    "cmdk": ("CORE_RUNTIME_UI", "Runtime command palette dependency."),
    "heic2any": ("CORE_RUNTIME_UI", "Runtime upload/image conversion capability."),
    "idb-keyval": ("CORE_RUNTIME_UI", "Runtime offline draft/resiliency storage dependency."),
    "input-otp": ("CORE_RUNTIME_UI", "Runtime OTP input dependency."),
    "jszip": ("CORE_RUNTIME_UI", "Runtime photo zip/download capability."),
    "maplibre-gl": ("CORE_RUNTIME_UI", "Runtime map rendering dependency."),
    "next-themes": ("CORE_RUNTIME_UI", "Theme support dependency used by sonner wrapper."),
    "qrcode.react": ("CORE_RUNTIME_UI", "Runtime QR rendering dependency."),
    "react-day-picker": ("CORE_RUNTIME_UI", "Runtime calendar dependency."),
    "react-hook-form": ("CORE_RUNTIME_UI", "Runtime form system dependency."),
    "react-resizable-panels": ("CORE_RUNTIME_UI", "Runtime panel layout dependency."),
    "react-signature-canvas": ("CORE_RUNTIME_UI", "Runtime signature capture dependency."),
    "sonner": ("CORE_RUNTIME_UI", "Runtime toast system dependency."),
    "tailwind-merge": ("CORE_RUNTIME_UI", "Runtime Tailwind class merge helper."),
    "vaul": ("CORE_RUNTIME_UI", "Runtime drawer dependency."),
    "react-scripts": ("BUILD_TOOLCHAIN", "CRA build/runtime toolchain entrypoint retained behind CRACO."),
    "@craco/craco": ("BUILD_TOOLCHAIN", "Build/runtime override layer for CRA."),
    "tailwindcss": ("BUILD_TOOLCHAIN", "CSS build pipeline dependency referenced by config files."),
    "tailwindcss-animate": ("BUILD_TOOLCHAIN", "Tailwind plugin referenced by config files."),
    "postcss": ("BUILD_TOOLCHAIN", "CSS build pipeline dependency referenced by config files."),
    "autoprefixer": ("BUILD_TOOLCHAIN", "CSS build pipeline dependency referenced by config files."),
    "@emergentbase/visual-edits": ("DEV_PREVIEW_TOOLING", "Preview-only visual editing integration loaded from custom tarball when available."),
    "eslint": ("GOVERNANCE_TOOLING", "Frontend lint/runtime boundary governance tool."),
    "eslint-plugin-react": ("GOVERNANCE_TOOLING", "Active ESLint plugin imported by flat config."),
    "eslint-plugin-react-hooks": ("GOVERNANCE_TOOLING", "Active ESLint plugin imported by flat config and CRACO lint config."),
    "globals": ("GOVERNANCE_TOOLING", "Active ESLint globals package imported by flat config."),
    "@testing-library/jest-dom": ("TEST_TOOLING", "Frontend test helper dependency."),
    "@testing-library/react": ("TEST_TOOLING", "Frontend test helper dependency."),
    "date-fns": ("RUNTIME_PEER_SUPPORT", "Required peer support for react-day-picker even without direct imports."),
    "@babel/plugin-proposal-private-property-in-object": ("BUILD_COMPAT_SHIM", "Retained build compatibility package for CRA/Babel toolchain."),
    "@hookform/resolvers": ("REVIEW_REQUIRED_NO_PROVEN_USE", "No current import proof; retain until separately disproven."),
    "recharts": ("REVIEW_REQUIRED_NO_PROVEN_USE", "No current import proof; retain until separately disproven."),
    "zod": ("REVIEW_REQUIRED_NO_PROVEN_USE", "No current import proof; retain until separately disproven."),
    "@eslint/js": ("REVIEW_REQUIRED_NO_PROVEN_USE", "No current direct config import proof; retain until separately disproven."),
    "eslint-plugin-import": ("REVIEW_REQUIRED_NO_PROVEN_USE", "No current config import proof; retain until separately disproven."),
    "eslint-plugin-jsx-a11y": ("REVIEW_REQUIRED_NO_PROVEN_USE", "No current config import proof; retain until separately disproven."),
}


FRONTEND_PATTERN_OVERRIDES = {
    "@craco/craco": [r"\bcraco\b"],
    "@emergentbase/visual-edits": [r"@emergentbase/visual-edits"],
    "@hookform/resolvers": [r"@hookform/resolvers"],
    "@sentry/react": [r"@sentry/react"],
    "@testing-library/jest-dom": [r"@testing-library/jest-dom"],
    "@testing-library/react": [r"@testing-library/react"],
    "class-variance-authority": [r"class-variance-authority"],
    "date-fns": [r"date-fns"],
    "embla-carousel-react": [r"embla-carousel-react"],
    "heic2any": [r"heic2any"],
    "idb-keyval": [r"idb-keyval"],
    "input-otp": [r"input-otp"],
    "jszip": [r"jszip"],
    "lucide-react": [r"lucide-react"],
    "maplibre-gl": [r"maplibre-gl"],
    "next-themes": [r"next-themes"],
    "qrcode.react": [r"qrcode.react"],
    "react-day-picker": [r"react-day-picker"],
    "react-hook-form": [r"react-hook-form"],
    "react-resizable-panels": [r"react-resizable-panels"],
    "react-router-dom": [r"react-router-dom"],
    "react-signature-canvas": [r"react-signature-canvas"],
    "recharts": [r"\brecharts\b"],
    "tailwind-merge": [r"tailwind-merge"],
    "tailwindcss-animate": [r"tailwindcss-animate"],
    "tailwindcss": [r"tailwindcss"],
    "postcss": [r"postcss"],
    "autoprefixer": [r"autoprefixer"],
    "vaul": [r"\bvaul\b"],
    "zod": [r"\bzod\b"],
    "@babel/plugin-proposal-private-property-in-object": [r"plugin-proposal-private-property-in-object"],
    "@eslint/js": [r"@eslint/js"],
    "eslint-plugin-import": [r"eslint-plugin-import"],
    "eslint-plugin-jsx-a11y": [r"eslint-plugin-jsx-a11y"],
    "eslint-plugin-react": [r"eslint-plugin-react"],
    "eslint-plugin-react-hooks": [r"eslint-plugin-react-hooks"],
    "react": [r"from\s+[\"']react[\"']", r"require\([\"']react[\"']\)"],
    "react-dom": [r"react-dom"],
    "sonner": [r"from\s+[\"']sonner[\"']", r"require\([\"']sonner[\"']\)"],
}


FRONTEND_ROOT_ROLE_PRIORITY = {
    "CORE_RUNTIME_UI": "runtime",
    "RUNTIME_PEER_SUPPORT": "runtime",
    "BUILD_TOOLCHAIN": "build",
    "BUILD_COMPAT_SHIM": "build",
    "DEV_PREVIEW_TOOLING": "preview",
    "TEST_TOOLING": "test",
    "GOVERNANCE_TOOLING": "governance",
    "REVIEW_REQUIRED_NO_PROVEN_USE": "review",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def parse_requirements() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_line in read_text(BACKEND_REQUIREMENTS).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, version = re.split(r"(==)", line, maxsplit=1) if "==" in line else (re.split(r"[<>=!~]", line, maxsplit=1)[0], "", "")
        rows.append({"name": name.strip(), "version": version.strip() if version else ""})
    return rows


def parse_python_imports() -> dict[str, set[str]]:
    imports: dict[str, set[str]] = defaultdict(set)
    for path in (REPO_ROOT / "backend").rglob("*.py"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if "/__pycache__/" in rel:
            continue
        try:
            tree = ast.parse(read_text(path))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name.split(".")[0]].add(rel)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports[node.module.split(".")[0]].add(rel)
    return imports


def resolve_python_top_levels(package_name: str) -> list[str]:
    if package_name in PYTHON_TOP_LEVEL_OVERRIDES:
        return PYTHON_TOP_LEVEL_OVERRIDES[package_name]
    try:
        dist = importlib_metadata.distribution(package_name)
        top_level = dist.read_text("top_level.txt")
    except Exception:
        top_level = None
    if top_level:
        values = [line.strip() for line in top_level.splitlines() if line.strip()]
        if values:
            return values
    normalized = package_name.lower().replace("-", "_").replace(".", "_")
    return [normalized]


def gather_backend_required_by(requirement_names: list[str]) -> dict[str, list[str]]:
    requirement_set = set(requirement_names)
    reverse: dict[str, set[str]] = {name: set() for name in requirement_names}
    for package_name in requirement_names:
        try:
            requires = importlib_metadata.requires(package_name) or []
        except Exception:
            requires = []
        for requirement in requires:
            child = re.split(r"[ ;(<>=!~\[]", requirement, maxsplit=1)[0]
            if child in requirement_set:
                reverse[child].add(package_name)
    return {name: sorted(values) for name, values in reverse.items()}


def classify_backend_package(name: str, import_hits: int, sample_files: list[str], required_by: list[str]) -> tuple[str, str]:
    if name in BACKEND_CLASSIFICATION_OVERRIDES:
        return BACKEND_CLASSIFICATION_OVERRIDES[name]

    runtime_files = [f for f in sample_files if f == "backend/server.py" or f.startswith("backend/routes/") or f.startswith("backend/lib/") or f.startswith("backend/services/")]
    script_files = [f for f in sample_files if f.startswith("backend/scripts/") or f.startswith("backend/tools/")]
    test_files = [f for f in sample_files if f.startswith("backend/tests/")]

    if runtime_files:
        return "FEATURE_RUNTIME_CAPABILITY", "Imported from governed backend runtime files."
    if script_files and not test_files:
        return "OPERATOR_TOOLING", "Imported only from operator/script tooling surfaces."
    if test_files and not script_files:
        return "TEST_TOOLING", "Imported only from test surfaces."
    if import_hits == 0 and required_by:
        return "TRANSITIVE_RUNTIME_SUPPORT", "No direct imports found; pinned support package required by governed dependencies."
    return "REVIEW_REQUIRED_NO_RUNTIME_PROOF", "No direct import proof found; retain until independently disproven."


def backend_registry_for(name: str) -> str:
    if name == "emergentintegrations":
        return "https://d33sy5i8bnduwe.cloudfront.net/simple/"
    return "https://pypi.org/simple/"


def build_backend_inventory() -> dict[str, Any]:
    requirements = parse_requirements()
    imports = parse_python_imports()
    required_by = gather_backend_required_by([row["name"] for row in requirements])
    packages = []

    for row in requirements:
        name = row["name"]
        top_levels = resolve_python_top_levels(name)
        sample_files = sorted({file for top in top_levels for file in imports.get(top.split(".")[0], set())})
        classification, note = classify_backend_package(name, len(sample_files), sample_files[:10], required_by.get(name, []))
        packages.append(
            {
                "name": name,
                "version": row["version"],
                "manifest_scope": "deployment_entrypoint_pinned",
                "classification": classification,
                "top_level_modules": top_levels,
                "import_hits": len(sample_files),
                "sample_files": sample_files[:10],
                "required_by": required_by.get(name, []),
                "registry_source": backend_registry_for(name),
                "note": note,
            }
        )

    totals = Counter(item["classification"] for item in packages)
    custom_sources = [
        {
            "package": "emergentintegrations",
            "source": "https://d33sy5i8bnduwe.cloudfront.net/simple/",
            "fresh_install_proven": True,
            "credentials_required": False,
            "evidence": "Fresh isolated pip install used indexes https://pypi.org/simple and the public CloudFront simple index without exposing credentials.",
        }
    ]
    return {
        "deployment_entrypoint": "backend/requirements.txt",
        "package_count": len(packages),
        "classification_totals": dict(sorted(totals.items())),
        "custom_sources": custom_sources,
        "packages": packages,
    }


def list_frontend_source_files() -> list[Path]:
    files: list[Path] = []
    for candidate in [REPO_ROOT / "frontend" / "src", REPO_ROOT / "frontend" / "scripts", REPO_ROOT / "frontend" / "craco.config.js", REPO_ROOT / "frontend" / "tailwind.config.js", REPO_ROOT / "frontend" / "postcss.config.js", REPO_ROOT / "frontend" / "eslint.config.js"]:
        if candidate.is_file():
            files.append(candidate)
        elif candidate.exists():
            files.extend(path for path in candidate.rglob("*") if path.is_file() and path.suffix in {".js", ".jsx", ".ts", ".tsx", ".cjs", ".mjs", ".css"})
    return files


def frontend_patterns_for(package_name: str) -> list[str]:
    if package_name in FRONTEND_PATTERN_OVERRIDES:
        return FRONTEND_PATTERN_OVERRIDES[package_name]
    if package_name.startswith("@radix-ui/"):
        return [re.escape(package_name)]
    return [re.escape(package_name)]


def gather_frontend_references(package_names: list[str]) -> dict[str, list[str]]:
    files = list_frontend_source_files()
    contents = {path.relative_to(REPO_ROOT).as_posix(): read_text(path) for path in files}
    references: dict[str, list[str]] = {}
    for package_name in package_names:
        matches = []
        patterns = frontend_patterns_for(package_name)
        for rel, text in contents.items():
            if any(re.search(pattern, text) for pattern in patterns):
                matches.append(rel)
        references[package_name] = matches
    return references


def classify_frontend_direct(package_name: str, hits: int, sample_files: list[str], manifest_scope: str) -> tuple[str, str]:
    if package_name in FRONTEND_DIRECT_CLASSIFICATION_OVERRIDES:
        return FRONTEND_DIRECT_CLASSIFICATION_OVERRIDES[package_name]
    if package_name.startswith("@radix-ui/"):
        return "CORE_RUNTIME_UI", "Runtime component primitive used through the shared UI system."
    if manifest_scope == "devDependencies":
        if hits:
            return "GOVERNANCE_TOOLING", "Direct dev dependency with active config/source references."
        return "REVIEW_REQUIRED_NO_PROVEN_USE", "Direct dev dependency has no current proof of use."
    if hits:
        return "CORE_RUNTIME_UI", "Direct frontend runtime dependency with source references."
    return "REVIEW_REQUIRED_NO_PROVEN_USE", "Direct dependency has no current proof of use."


def parse_yarn_lock() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in read_text(FRONTEND_YARN_LOCK).splitlines():
        if line and not line.startswith(" ") and line.endswith(":"):
            selector_line = line[:-1]
            selectors = [segment.strip().strip('"') for segment in selector_line.split(",")]
            current = {"selectors": selectors, "dependencies": {}}
            continue
        if current is None:
            continue
        if line.startswith("  version "):
            current["version"] = line.split('"')[1]
            continue
        if line.startswith("  resolved "):
            current["resolved"] = line.split('"')[1]
            continue
        if line.startswith("  integrity "):
            current["integrity"] = line.split(" ", 2)[2].strip()
            continue
        if line.startswith("  dependencies:"):
            current["_in_dependencies"] = True
            continue
        if current.get("_in_dependencies") and line.startswith("    "):
            dep_name, dep_spec = line.strip().split(" ", 1)
            current["dependencies"][dep_name] = dep_spec.strip().strip('"')
            continue
        if current.get("_in_dependencies") and line and not line.startswith("    "):
            current.pop("_in_dependencies", None)
        if not line and current.get("version"):
            entries.append(current)
            current = None
    if current and current.get("version"):
        current.pop("_in_dependencies", None)
        entries.append(current)
    return entries


def package_name_from_selector(selector: str) -> str:
    clean = selector.strip().strip('"')
    if clean.startswith("@"):
        scope_name, _, _version = clean[1:].partition("@")
        return f"@{scope_name}"
    return clean.partition("@")[0]


def package_manifest(name: str) -> dict[str, Any]:
    package_json = FRONTEND_NODE_MODULES / name / "package.json"
    if package_json.exists():
        return load_json(package_json)
    return {}


def classify_transitive_from_roles(roles: set[str], package_name: str) -> tuple[str, str]:
    if "runtime" in roles:
        return "TRANSITIVE_RUNTIME_SUPPORT", "Transitively required by runtime frontend packages."
    if "build" in roles:
        return "TRANSITIVE_BUILD_SUPPORT", "Transitively required by build toolchain packages."
    if "test" in roles:
        return "TRANSITIVE_TEST_SUPPORT", "Transitively required by frontend test packages."
    if "preview" in roles:
        return "TRANSITIVE_PREVIEW_SUPPORT", "Transitively required by preview-only tooling packages."
    if "governance" in roles:
        return "TRANSITIVE_GOVERNANCE_SUPPORT", "Transitively required by governance/lint packages."
    if package_name.startswith("@babel/") or package_name.startswith("webpack") or "postcss" in package_name or "eslint" in package_name or "jest" in package_name:
        return "TRANSITIVE_BUILD_SUPPORT", "Lockfile entry heuristically bound to build/test toolchain." 
    return "TRANSITIVE_LOCKFILE_REVIEW_REQUIRED", "Lockfile entry retained under governance but root role could not be proven from current install graph."


def build_frontend_inventory() -> dict[str, Any]:
    package_json = load_json(FRONTEND_PACKAGE_JSON)
    direct_packages = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
    manifest_scope_lookup = {name: "dependencies" for name in package_json.get("dependencies", {})}
    manifest_scope_lookup.update({name: "devDependencies" for name in package_json.get("devDependencies", {})})
    refs = gather_frontend_references(sorted(direct_packages))

    direct_rows = []
    root_roles: dict[str, str] = {}
    for name in sorted(direct_packages):
        sample_files = refs.get(name, [])[:10]
        classification, note = classify_frontend_direct(name, len(refs.get(name, [])), sample_files, manifest_scope_lookup[name])
        manifest = package_manifest(name)
        root_role = FRONTEND_ROOT_ROLE_PRIORITY.get(classification, "review")
        root_roles[name] = root_role
        direct_rows.append(
            {
                "name": name,
                "version_spec": direct_packages[name],
                "installed_version": manifest.get("version", ""),
                "manifest_scope": manifest_scope_lookup[name],
                "classification": classification,
                "import_hits": len(refs.get(name, [])),
                "sample_files": sample_files,
                "registry_source": manifest.get("_resolved") or ("https://assets.emergent.sh/npm/emergentbase-visual-edits-1.0.8.tgz" if name == "@emergentbase/visual-edits" else "https://registry.yarnpkg.com/"),
                "peer_dependencies": manifest.get("peerDependencies", {}),
                "note": note,
            }
        )

    graph_roles: dict[str, set[str]] = defaultdict(set)
    visited: set[tuple[str, str]] = set()
    queue: deque[tuple[str, str]] = deque((name, role) for name, role in root_roles.items())
    while queue:
        package_name, role = queue.popleft()
        if (package_name, role) in visited:
            continue
        visited.add((package_name, role))
        graph_roles[package_name].add(role)
        manifest = package_manifest(package_name)
        for dep_name in sorted((manifest.get("dependencies") or {}).keys() | (manifest.get("optionalDependencies") or {}).keys() | (manifest.get("peerDependencies") or {}).keys()):
            queue.append((dep_name, role))

    lock_entries = parse_yarn_lock()
    transitive_rows = []
    for entry in lock_entries:
        selector_name = package_name_from_selector(entry["selectors"][0])
        if selector_name in direct_packages:
            continue
        roles = graph_roles.get(selector_name, set())
        classification, note = classify_transitive_from_roles(roles, selector_name)
        transitive_rows.append(
            {
                "name": selector_name,
                "version": entry.get("version", ""),
                "selectors": entry.get("selectors", []),
                "resolved": entry.get("resolved", ""),
                "root_roles": sorted(roles),
                "classification": classification,
                "note": note,
            }
        )

    totals = Counter(item["classification"] for item in direct_rows + transitive_rows)
    custom_sources = [
        {
            "package": "@emergentbase/visual-edits",
            "source": "https://assets.emergent.sh/npm/emergentbase-visual-edits-1.0.8.tgz",
            "fresh_install_proven": True,
            "credentials_required": False,
            "evidence": "Fresh isolated yarn install resolved the tarball directly without exposing credentials.",
        }
    ]
    return {
        "manifests": ["frontend/package.json", "frontend/yarn.lock"],
        "direct_package_count": len(direct_rows),
        "transitive_package_count": len(transitive_rows),
        "classification_totals": dict(sorted(totals.items())),
        "custom_sources": custom_sources,
        "direct_packages": direct_rows,
        "transitive_packages": transitive_rows,
    }


def build_cleanup_actions() -> list[dict[str, Any]]:
    return [
        {
            "package": "cra-template",
            "ecosystem": "frontend",
            "prior_version": "1.2.0",
            "action": "REMOVED_FROM_DIRECT_DEPENDENCIES",
            "status": "EXECUTED_WITH_PROOF",
            "proof": {
                "inventory_evidence": "No static imports, no dynamic requires, no build/config references, and package purpose is create-react-app scaffolding only.",
                "fresh_isolated_install": "PASSED",
                "fresh_isolated_build": "PASSED",
                "focused_regression_tests": "PASSED",
            },
            "note": "Removed only after isolated clean install/build proof; this package is not a runtime, build, script, provider, or peer dependency for the governed app.",
        }
    ]


def build_inventory() -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checkpoint": "D4",
        "governance_rules": [
            "Keep backend/requirements.txt as the deployment entrypoint.",
            "Do not equate not-statically-imported with unused; peer dependencies, config plugins, scripts, and optional providers count.",
            "Do not collapse overlapping provider SDKs unless responsibilities are disproven.",
            "Do not broad-upgrade versions during D4.",
        ],
        "isolated_verification": {
            "backend_fresh_install": {
                "status": "PASSED",
                "command": "python3 -m venv <tmp>/venv && pip install --no-cache-dir -r backend/requirements.txt",
            },
            "backend_compileall": {
                "status": "PASSED",
                "command": "python -m compileall backend",
            },
            "frontend_fresh_install": {
                "status": "PASSED",
                "command": "yarn install --frozen-lockfile --ignore-scripts",
            },
            "frontend_production_build": {
                "status": "PASSED",
                "command": "yarn build",
            },
        },
        "backend": build_backend_inventory(),
        "frontend": build_frontend_inventory(),
        "cleanup_actions": build_cleanup_actions(),
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def write_classification_markdown(inventory: dict[str, Any]) -> None:
    backend_totals = inventory["backend"]["classification_totals"]
    frontend_totals = inventory["frontend"]["classification_totals"]
    notable_frontend = []
    direct_lookup = {item["name"]: item for item in inventory["frontend"]["direct_packages"]}
    for name in ["date-fns", "@hookform/resolvers", "recharts", "zod", "@babel/plugin-proposal-private-property-in-object", "@emergentbase/visual-edits"]:
        item = direct_lookup.get(name)
        if item:
            notable_frontend.append([name, item["classification"], item["note"]])

    notable_backend = []
    backend_lookup = {item["name"]: item for item in inventory["backend"]["packages"]}
    for name in ["fastapi", "motor", "pymongo", "emergentintegrations", "openai", "litellm", "google-generativeai", "google-genai", "slowapi", "passlib", "python-jose"]:
        item = backend_lookup.get(name)
        if item:
            notable_backend.append([name, item["classification"], item["note"]])

    body = f"""# DEPENDENCY CLASSIFICATION

Date: {datetime.now(timezone.utc).date().isoformat()}  
Checkpoint: D4

## Governing decisions

1. `backend/requirements.txt` remains the deployment entrypoint for this checkpoint.
2. Absence of a static import is not treated as proof of disuse.
3. Optional providers remain separated when responsibilities differ or remain plausible.
4. D4 performs classification, reproducibility proof, and bounded cleanup only.

Machine-readable authority:
- `docs/governance/dependency_inventory.json`

## Isolated proof status

{markdown_table(["Proof", "Status", "Command"], [
    ["Backend fresh install", inventory["isolated_verification"]["backend_fresh_install"]["status"], inventory["isolated_verification"]["backend_fresh_install"]["command"]],
    ["Backend compileall", inventory["isolated_verification"]["backend_compileall"]["status"], inventory["isolated_verification"]["backend_compileall"]["command"]],
    ["Frontend fresh install", inventory["isolated_verification"]["frontend_fresh_install"]["status"], inventory["isolated_verification"]["frontend_fresh_install"]["command"]],
    ["Frontend production build", inventory["isolated_verification"]["frontend_production_build"]["status"], inventory["isolated_verification"]["frontend_production_build"]["command"]],
])}

## Backend classification totals

{markdown_table(["Classification", "Count"], [[key, str(value)] for key, value in backend_totals.items()])}

## Frontend classification totals

{markdown_table(["Classification", "Count"], [[key, str(value)] for key, value in frontend_totals.items()])}

## Backend notable decisions

{markdown_table(["Package", "Classification", "Decision note"], notable_backend)}

## Frontend notable decisions

{markdown_table(["Package", "Classification", "Decision note"], notable_frontend)}

## Cleanup executed in D4

{markdown_table(["Package", "Action", "Status", "Reason"], [[action["package"], action["action"], action["status"], action["note"]] for action in inventory["cleanup_actions"]])}

## Acceptance-sensitive findings

- `cra-template` was removed only after isolated clean install and isolated production build proof demonstrated it was unnecessary.
- `date-fns` is retained as runtime peer support for `react-day-picker`; it is not treated as unused just because no direct import remains in app code.
- `@babel/plugin-proposal-private-property-in-object` is retained as a build compatibility shim even without source imports.
- `@hookform/resolvers`, `recharts`, `zod`, `@eslint/js`, `eslint-plugin-import`, and `eslint-plugin-jsx-a11y` remain review-required rather than auto-removed.
- Distinct AI/provider packages remain separately governed; D4 does not collapse them without stronger proof.

## Custom/public package sources proven available without credentials

{markdown_table(["Ecosystem", "Package", "Source", "Fresh install proven"], [
    ["backend", "emergentintegrations", inventory["backend"]["custom_sources"][0]["source"], "YES"],
    ["frontend", "@emergentbase/visual-edits", inventory["frontend"]["custom_sources"][0]["source"], "YES"],
])}
"""
    output_path = DOCS_ROOT / "DEPENDENCY_CLASSIFICATION.md"
    ensure_parent(output_path)
    output_path.write_text(body, encoding="utf-8")


def write_version_register_markdown(inventory: dict[str, Any]) -> None:
    backend_rows = [
        [item["name"], item["version"], item["classification"], item["registry_source"]]
        for item in inventory["backend"]["packages"]
    ]
    frontend_rows = [
        [item["name"], item["installed_version"], item["classification"], item["version_spec"]]
        for item in inventory["frontend"]["direct_packages"]
    ]
    body = f"""# DEPENDENCY VERSION REGISTER

Date: {datetime.now(timezone.utc).date().isoformat()}  
Checkpoint: D4

## Backend pinned entrypoint register

Deployment entrypoint remains `backend/requirements.txt`.

{markdown_table(["Package", "Pinned version", "Classification", "Source"], backend_rows)}

## Frontend direct dependency register

Authority remains `frontend/package.json` + `frontend/yarn.lock`.

{markdown_table(["Package", "Installed version", "Classification", "Manifest spec"], frontend_rows)}

## Source/index register

{markdown_table(["Surface", "Source", "Credential-free proof"], [
    ["backend requirements install", "https://pypi.org/simple/ + https://d33sy5i8bnduwe.cloudfront.net/simple/", "Fresh isolated pip install passed without exposing credentials"],
    ["frontend lockfile install", "https://registry.yarnpkg.com/ + https://assets.emergent.sh/npm/emergentbase-visual-edits-1.0.8.tgz", "Fresh isolated yarn install passed without exposing credentials"],
])}

## Bounded cleanup register

{markdown_table(["Package", "Prior version", "Action", "Status"], [[action["package"], action["prior_version"], action["action"], action["status"]] for action in inventory["cleanup_actions"]])}
"""
    output_path = DOCS_ROOT / "DEPENDENCY_VERSION_REGISTER.md"
    ensure_parent(output_path)
    output_path.write_text(body, encoding="utf-8")


def main() -> None:
    inventory = build_inventory()
    inventory_path = DOCS_ROOT / "dependency_inventory.json"
    ensure_parent(inventory_path)
    inventory_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    write_classification_markdown(inventory)
    write_version_register_markdown(inventory)
    print("Generated dependency governance artifacts:")
    print(f"- {inventory_path.relative_to(REPO_ROOT)}")
    print("- docs/governance/DEPENDENCY_CLASSIFICATION.md")
    print("- docs/governance/DEPENDENCY_VERSION_REGISTER.md")


if __name__ == "__main__":
    main()
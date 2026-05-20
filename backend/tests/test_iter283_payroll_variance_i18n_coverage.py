"""
iter283 · HR Payroll Variance i18n key coverage regression test.

Locks in that EVERY `t("...")` key called by HrPayrollVariance.jsx is
defined in `frontend/src/lib/i18n.js`. Prevents the silent
EN-fallback-in-ES-mode behavior that the iter277/iter282 audit
caught.

Mobile verification was performed live (see ship-log entry for
iter283 in PLATFORM_OPERATIONAL_MATURITY_MATRIX.md): 390x844 viewport
confirmed no horizontal page overflow · HelpTipBlock mounts render
correctly · `.overflow-x-auto` wraps the wide variance table per
existing platform convention.
"""
import re
import sys
import pathlib

# Compute absolute paths inside the /app workspace
APP_ROOT = pathlib.Path("/app")
JSX_PATH = APP_ROOT / "frontend/src/pages/HrPayrollVariance.jsx"
I18N_PATH = APP_ROOT / "frontend/src/lib/i18n.js"


def _extract_t_keys(jsx_src: str) -> list[str]:
    """Pull every t("...") literal from a JSX source.

    Lookbehind `(?<![\\w$])` prevents collisions with identifiers that
    happen to end in 't' (e.g. `get(` from `api.get("...")` or
    `Element(` from `document.createElement("...")`).
    """
    pat = re.compile(r'(?<![\w$])t\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
    return list(dict.fromkeys(pat.findall(jsx_src)))


def _i18n_has_key(i18n_src: str, key: str) -> bool:
    """True if `"<key>":` appears verbatim in the i18n.js source."""
    return ('"' + key + '":') in i18n_src


def test_all_payroll_variance_t_keys_resolve_in_i18n():
    jsx_src = JSX_PATH.read_text(encoding="utf-8")
    i18n_src = I18N_PATH.read_text(encoding="utf-8")

    keys = _extract_t_keys(jsx_src)
    assert keys, "Expected to extract at least one t() key — extractor regression?"

    missing = [k for k in keys if not _i18n_has_key(i18n_src, k)]
    # Truncate long keys for readability in failure output
    display = [k if len(k) <= 100 else k[:97] + "..." for k in missing]
    assert not missing, (
        f"HrPayrollVariance.jsx has {len(missing)} t() keys with no ES entry "
        f"in i18n.js. ES mode will fall back to English for these. Missing: {display}"
    )


def test_known_payroll_variance_ui_strings_have_es_entries():
    """Explicit anchor — these are the operationally critical UI strings
    that MUST stay translated. Beyond the regex sweep above, this is a
    second-line lock so a future i18n.js refactor (e.g. namespace split)
    can't silently drop the payroll-variance bundle."""
    i18n_src = I18N_PATH.read_text(encoding="utf-8")
    anchors = [
        "Paste your Exact payroll export",
        "Week Ending",
        "Threshold (minutes)",
        "Run Variance",
        "Recent Variance Batches",
        "Active Batch · Week Ending",
        "Download CSV",
        "Pending Review",
        "Exact Reg",
        "Exact OT",
        "Exact Total",
        "MASCI Total",
        "Diff",
        "Flag",
        "Decision",
        "Approve",
        "Dispute",
        "Could not load recent batches",
        "Variance batch created",
        "Upload failed",
        "CSV download failed",
    ]
    missing = [a for a in anchors if not _i18n_has_key(i18n_src, a)]
    assert not missing, f"Operational anchor strings missing from i18n.js: {missing}"

import json
import subprocess


def test_premerge_operator_language_check_passes_cleanly():
    completed = subprocess.run(
        ["python3", "/app/scripts/premerge_operator_language_check.py"],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "pass"
    assert int(payload.get("operator_facing_banned_findings") or 0) == 0
    assert int(payload.get("fail_rows") or 0) == 0
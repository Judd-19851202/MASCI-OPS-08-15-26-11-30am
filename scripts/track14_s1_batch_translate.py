"""TRACK 14.0-S1-B1 THROUGH B10 · Amendment C-compliant batched translation.

Reads critical-workflow untranslated strings, batches them through the
MASCI Heavy Civil-aware /api/translate endpoint, and emits a JSON file
of {english_key: spanish_value} pairs ready to be appended to
/app/frontend/src/lib/i18n.js.

Quality over percentage:
  • Uses the MASCI / US Heavy Civil glossary baked into /api/translate.
  • Translates ONLY critical-workflow strings — does not mass-dump.
  • Reviews are still required before merging into i18n.js.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

API_URL = "http://localhost:8001"
IN_PATH = Path("/app/test_reports/track14_s1_critical_untranslated.json")
OUT_PATH = Path("/app/test_reports/track14_s1_critical_translations.json")

BATCH_SIZE = 30  # small enough that Claude returns clean JSON
TIMEOUT = 90


def main() -> int:
    data = json.loads(IN_PATH.read_text())
    items = [it["key"] for it in data["items"]]
    print(f"To translate: {len(items)} strings")

    translations: dict[str, str] = {}

    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i : i + BATCH_SIZE]
        strings = {str(j): s for j, s in enumerate(batch)}
        r = requests.post(
            f"{API_URL}/api/translate",
            json={"from_lang": "en", "to_lang": "es", "strings": strings},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            print(f"  batch {i}: HTTP {r.status_code} — {r.text[:200]}", file=sys.stderr)
            continue
        out = r.json()["strings"]
        for j_str, en in strings.items():
            es = out.get(j_str, "").strip()
            if es and es != en:
                translations[en] = es
        print(f"  batch {i // BATCH_SIZE + 1}/{(len(items) + BATCH_SIZE - 1) // BATCH_SIZE}: "
              f"+{len(translations)} cumulative")
        time.sleep(0.5)

    OUT_PATH.write_text(
        json.dumps(translations, indent=2, ensure_ascii=False, sort_keys=True)
    )
    print(f"\nWrote {len(translations)} translations → {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""ITER20: validate /api/translate produces actual English output (not just same keys).

Spec from review_request: POST {from_lang:es, to_lang:en, strings:{k1: 'Hicimos
trabajo de pavimentación...', k2:'Llovió toda la mañana.', k3:'Operario Juan Pérez
instaló la malla de geotextil.'}} should return translated English values mapping
to same keys.
"""
import os
import re
import requests

def _read_url():
    u = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if u:
        return u.rstrip("/")
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = _read_url()
API = f"{BASE_URL}/api"


def _looks_english(s: str) -> bool:
    """Heuristic: contains common English words and lacks obvious Spanish-only
    diacritics-or-accented function words."""
    s_low = s.lower()
    english_markers = [
        " the ", " we ", " did ", " was ", " rained ", " main ", " street ",
        " all ", " morning ", " operator ", " installed ", "paving",
        " geotextile", " mesh ", " fabric ", " road ",
    ]
    spanish_giveaways = [
        "hicimos", "llovió", "mañana", "operario", "instaló",
        "pavimentación", "malla", "trabajo de",
    ]
    has_eng = any(m in f" {s_low} " for m in english_markers)
    has_es = any(g in s_low for g in spanish_giveaways)
    return has_eng and not has_es


class TestTranslateRealES2EN:
    def test_translates_spanish_paving_paragraph_to_english(self):
        body = {
            "from_lang": "es",
            "to_lang": "en",
            "strings": {
                "k1": "Hicimos trabajo de pavimentación en la calle principal.",
                "k2": "Llovió toda la mañana.",
                "k3": "Operario Juan Pérez instaló la malla de geotextil.",
            },
        }
        res = requests.post(f"{API}/translate", json=body, timeout=60)
        assert res.status_code == 200, res.text
        out = res.json()["strings"]
        assert set(out.keys()) == {"k1", "k2", "k3"}

        # k3 must preserve the proper noun "Juan Pérez" (or "Juan Perez")
        assert re.search(r"juan\s+p[eé]rez", out["k3"], re.I), (
            f"Proper noun lost: {out['k3']!r}"
        )

        # Each output must be different from its Spanish input (i.e. translation
        # actually happened) — otherwise the LLM/key isn't wired up.
        for k, original in body["strings"].items():
            translated = out[k]
            assert translated != original, (
                f"Key {k!r} was NOT translated — same as input. "
                f"This means EMERGENT_LLM_KEY isn't wired or the LLM call failed silently."
            )

        # And at least one of the three should look English
        assert any(_looks_english(v) for v in out.values()), (
            f"None of the outputs look English: {out!r}"
        )

    def test_short_circuit_empty(self):
        res = requests.post(
            f"{API}/translate",
            json={"from_lang": "es", "to_lang": "en", "strings": {}},
            timeout=10,
        )
        assert res.status_code == 200
        assert res.json() == {"strings": {}}

    def test_short_circuit_same_lang(self):
        payload = {
            "from_lang": "es",
            "to_lang": "es",
            "strings": {"a": "Llovió ligeramente"},
        }
        res = requests.post(f"{API}/translate", json=payload, timeout=10)
        assert res.status_code == 200
        # When src==dst, we expect the strings echoed back unchanged
        assert res.json()["strings"] == payload["strings"]

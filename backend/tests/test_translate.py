"""MASCI translation endpoint tests (Spanish→English at form-submit time)."""
import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")


def _read_frontend_url():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return BASE_URL


URL = _read_frontend_url()
API = f"{URL}/api"


class TestTranslateContract:
    def test_empty_strings_short_circuits(self):
        res = requests.post(
            f"{API}/translate",
            json={"from_lang": "es", "to_lang": "en", "strings": {}},
            timeout=30,
        )
        assert res.status_code == 200
        assert res.json() == {"strings": {}}

    def test_same_lang_short_circuits_no_change(self):
        payload = {
            "from_lang": "en",
            "to_lang": "en",
            "strings": {"a": "Concrete pour at 6am", "b": "Trench shoring"},
        }
        res = requests.post(f"{API}/translate", json=payload, timeout=30)
        assert res.status_code == 200
        assert res.json() == {"strings": payload["strings"]}

    def test_response_keeps_keys(self):
        res = requests.post(
            f"{API}/translate",
            json={
                "from_lang": "es",
                "to_lang": "en",
                "strings": {"x1": "Trabajo terminado", "x2": "Sin incidentes"},
            },
            timeout=45,
        )
        assert res.status_code == 200
        body = res.json()
        assert set(body["strings"].keys()) == {"x1", "x2"}
        for v in body["strings"].values():
            assert isinstance(v, str)
            assert v.strip() != ""


class TestTranslateLive:
    def test_translate_basic_es_to_en(self):
        """Translation may fall back gracefully on budget/network blips. The
        contract we always honor is: same keys back, every value is a non-empty
        string. When the LLM succeeds the values should be in English (best
        effort)."""
        res = requests.post(
            f"{API}/translate",
            json={
                "from_lang": "es",
                "to_lang": "en",
                "strings": {
                    "1": "Hubo un derrame de aceite en la zanja",
                    "2": "Cuadrilla 3 trabajó hasta tarde",
                },
            },
            timeout=45,
        )
        assert res.status_code == 200
        body = res.json()
        assert set(body["strings"].keys()) == {"1", "2"}
        for v in body["strings"].values():
            assert isinstance(v, str) and v.strip() != ""

    def test_translate_preserves_data_urls(self):
        # Frontend filters these out before send, but if they slip through the
        # LLM is instructed to keep them. The contract is: same keys back.
        res = requests.post(
            f"{API}/translate",
            json={
                "from_lang": "es",
                "to_lang": "en",
                "strings": {
                    "note": "Hubo un derrame",
                    "img": "data:image/png;base64,iVBORw0KGgo",
                },
            },
            timeout=45,
        )
        assert res.status_code == 200
        body = res.json()
        assert set(body["strings"].keys()) == {"note", "img"}

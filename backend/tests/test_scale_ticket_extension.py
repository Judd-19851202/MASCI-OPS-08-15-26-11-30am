"""Track 13.14 · scale-ticket 4-field extension backend test.

Exercises the upload endpoint against the live preview backend (because
the operational_attachments router requires the dispatch_portal_auth
runtime state that is harder to stand up inside the ASGI test client).

The seven cases below mirror the curl smoke executed in
TRACK_13_14_SCALE_TICKET_EXTENSION.md §11.

Set REACT_APP_BACKEND_URL to point at the live preview before running
this file. Tests skip cleanly if the URL or super-admin credentials
are not reachable.
"""
import io
import os
import sys
import pytest
import httpx

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PW = "Maddix123!"

PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _dispatch_token():
    """Mint a dispatch portal token via /api/auth/multi-login."""
    try:
        r = httpx.post(
            f"{API}/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PW},
            timeout=10,
        )
    except Exception as e:
        pytest.skip(f"preview backend unreachable: {e}")
    if r.status_code != 200:
        pytest.skip(f"multi-login failed: {r.status_code} {r.text[:150]}")
    body = r.json()
    tok = (body.get("portal_tokens") or {}).get("dispatch")
    if not tok:
        pytest.skip("no dispatch portal_token in multi-login response")
    return tok


def _live_assignment_id(tok):
    """Pull a real assignment id from the live dispatch list."""
    r = httpx.get(
        f"{API}/dispatch/assignments?limit=5",
        headers={"X-Dispatch-Token": tok},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"dispatch assignment fetch failed: {r.status_code}")
    j = r.json()
    items = j.get("assignments") if isinstance(j, dict) else j
    if not items:
        pytest.skip("no dispatch assignments available")
    return items[0]["id"]


def _upload(tok, asg_id, **fields):
    files = {"file": ("ticket.png", io.BytesIO(PNG_1PX), "image/png")}
    data = {
        "host_kind": "assignment",
        "host_id": asg_id,
    }
    data.update(fields)
    return httpx.post(
        f"{API}/operational-attachments/upload",
        headers={"X-Dispatch-Token": tok},
        data=data,
        files=files,
        timeout=15,
    )


def _delete(tok, oid):
    httpx.delete(
        f"{API}/operational-attachments/{oid}",
        headers={"X-Dispatch-Token": tok},
        timeout=10,
    )


@pytest.fixture(scope="module")
def session():
    tok = _dispatch_token()
    asg = _live_assignment_id(tok)
    created = []
    yield {"tok": tok, "asg": asg, "created": created}
    for oid in created:
        try:
            _delete(tok, oid)
        except Exception:
            pass


def test_scale_ticket_backward_compat(session):
    r = _upload(session["tok"], session["asg"], attachment_type="scale_ticket",
                operational_note="legacy ticket")
    assert r.status_code == 200, r.text
    body = r.json()
    session["created"].append(body["id"])
    assert body["type"] == "scale_ticket"
    assert "weight_gross_lbs" not in body
    assert "weight_tare_lbs" not in body
    assert "weight_net_lbs" not in body
    assert "material_code" not in body


def test_scale_ticket_all_four_fields(session):
    r = _upload(session["tok"], session["asg"], attachment_type="scale_ticket",
                weight_gross_lbs="78420", weight_tare_lbs="27300",
                weight_net_lbs="51120", material_code="SP-12.5")
    assert r.status_code == 200, r.text
    body = r.json()
    session["created"].append(body["id"])
    assert body["weight_gross_lbs"] == 78420.0
    assert body["weight_tare_lbs"] == 27300.0
    assert body["weight_net_lbs"] == 51120.0
    assert body["material_code"] == "SP-12.5"


def test_scale_ticket_auto_net_from_gross_minus_tare(session):
    r = _upload(session["tok"], session["asg"], attachment_type="scale_ticket",
                weight_gross_lbs="60000", weight_tare_lbs="20000")
    assert r.status_code == 200, r.text
    body = r.json()
    session["created"].append(body["id"])
    assert body["weight_net_lbs"] == 40000.0


def test_scale_ticket_explicit_net_not_overridden(session):
    r = _upload(session["tok"], session["asg"], attachment_type="scale_ticket",
                weight_gross_lbs="60000", weight_tare_lbs="20000",
                weight_net_lbs="39800")
    assert r.status_code == 200, r.text
    body = r.json()
    session["created"].append(body["id"])
    assert body["weight_net_lbs"] == 39800.0


def test_scale_ticket_invalid_numeric_rejected(session):
    r = _upload(session["tok"], session["asg"], attachment_type="scale_ticket",
                weight_gross_lbs="not a number")
    assert r.status_code == 400
    assert "Invalid numeric weight" in r.text


def test_scale_ticket_tare_exceeds_gross_rejected(session):
    r = _upload(session["tok"], session["asg"], attachment_type="scale_ticket",
                weight_gross_lbs="5000", weight_tare_lbs="9000")
    assert r.status_code == 400
    assert "Tare weight cannot exceed gross weight" in r.text


def test_unrelated_attachment_type_unaffected_by_scale_fields(session):
    r = _upload(session["tok"], session["asg"], attachment_type="load_photo",
                weight_gross_lbs="78420", material_code="SP-12.5")
    assert r.status_code == 200, r.text
    body = r.json()
    session["created"].append(body["id"])
    assert body["type"] == "load_photo"
    assert "weight_gross_lbs" not in body
    assert "material_code" not in body


def test_list_endpoint_returns_structured_fields(session):
    # Create a scale_ticket with fields then read it back via /list
    r = _upload(session["tok"], session["asg"], attachment_type="scale_ticket",
                weight_gross_lbs="55000", material_code="SP-9.5")
    assert r.status_code == 200
    new_id = r.json()["id"]
    session["created"].append(new_id)
    r2 = httpx.get(
        f"{API}/operational-attachments/list?host_kind=assignment&host_id={session['asg']}",
        headers={"X-Dispatch-Token": session["tok"]},
        timeout=10,
    )
    assert r2.status_code == 200, r2.text
    items = r2.json().get("attachments") or []
    found = next((a for a in items if a["id"] == new_id), None)
    assert found is not None
    assert found.get("weight_gross_lbs") == 55000.0
    assert found.get("material_code") == "SP-9.5"

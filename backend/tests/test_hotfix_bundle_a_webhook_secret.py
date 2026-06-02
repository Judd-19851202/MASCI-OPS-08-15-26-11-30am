"""HOTFIX BUNDLE A · Part A · Webhook secret enforcement verification.

Verifies that the existing _verify_signature() path in resend_webhook.py
ENFORCES correctly when RESEND_WEBHOOK_SECRET is set:
  * Missing headers → 401 signature_headers_missing
  * Bad signature → 401 signature_mismatch
  * Valid v1 HMAC → 200 ack

This is the in-code certification of MED-1. Production-side enforcement
depends on the operator setting the env var in the production env pane.
"""
import base64
import hashlib
import hmac
import importlib
import os
import sys


def _client(monkeypatch, secret: str):
    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", secret)
    sys.path.insert(0, "/app/backend")
    srv = sys.modules.get("server") or importlib.import_module("server")
    from fastapi.testclient import TestClient
    srv.app.state.ready = True
    return TestClient(srv.app)


def _sign(secret: str, msg_id: str, ts: str, body: bytes) -> str:
    raw = secret[len("whsec_"):] if secret.startswith("whsec_") else secret
    try:
        raw_bytes = base64.b64decode(raw)
    except Exception:
        raw_bytes = raw.encode("utf-8")
    sig = hmac.new(raw_bytes, f"{msg_id}.{ts}.".encode() + body, hashlib.sha256).digest()
    return f"v1,{base64.b64encode(sig).decode('ascii')}"


def test_webhook_rejects_when_secret_set_and_headers_missing(monkeypatch):
    client = _client(monkeypatch, "whsec_dGVzdHNlY3JldA==")  # "testsecret" b64'd
    r = client.post("/api/webhooks/resend", json={})
    assert r.status_code == 401, r.text
    body = r.json()
    detail = body.get("detail") or body
    assert detail.get("code") == "signature_headers_missing" if isinstance(detail, dict) else "signature_headers_missing" in r.text


def test_webhook_rejects_bad_signature(monkeypatch):
    client = _client(monkeypatch, "whsec_dGVzdHNlY3JldA==")
    r = client.post(
        "/api/webhooks/resend",
        json={"type": "email.bounced"},
        headers={
            "svix-id": "msg_test_bad",
            "svix-timestamp": "1700000000",
            "svix-signature": "v1,deadbeefdeadbeef",
        },
    )
    assert r.status_code == 401, r.text


def test_webhook_accepts_valid_signature(monkeypatch):
    secret = "whsec_dGVzdHNlY3JldA=="
    client = _client(monkeypatch, secret)
    msg_id = "msg_test_good_iter453_6"
    ts = "1700000123"
    body_bytes = b'{"type":"email.delivered","data":{"email_id":"VERIFY_PROBE_NO_OP"}}'
    sig = _sign(secret, msg_id, ts, body_bytes)
    r = client.post(
        "/api/webhooks/resend",
        content=body_bytes,
        headers={
            "Content-Type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": ts,
            "svix-signature": sig,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True


def test_webhook_no_secret_preview_mode_accepts_unsigned(monkeypatch):
    """Backward-compat: preview/dev environment with no secret still accepts."""
    monkeypatch.delenv("RESEND_WEBHOOK_SECRET", raising=False)
    sys.path.insert(0, "/app/backend")
    srv = sys.modules.get("server") or importlib.import_module("server")
    from fastapi.testclient import TestClient
    srv.app.state.ready = True
    client = TestClient(srv.app)
    r = client.post("/api/webhooks/resend", json={})
    assert r.status_code == 200, r.text

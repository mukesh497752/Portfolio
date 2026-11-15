from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "Portfolio <portfolio@example.com>")
    monkeypatch.setenv("CONTACT_TO_EMAIL", "owner@example.com")
    return TestClient(main.app)


def valid_message(**overrides):
    return {
        "name": "Alex Example",
        "email": "alex@example.com",
        "message": "Hello, I would like to connect.",
        "website": "",
        **overrides,
    }


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_origin_only(client):
    headers = {
        "Origin": "http://localhost:5500",
        "Access-Control-Request-Method": "POST",
    }
    allowed = client.options("/api/contact", headers=headers)
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5500"

    headers["Origin"] = "https://untrusted.example"
    rejected = client.options("/api/contact", headers=headers)
    assert rejected.status_code == 400
    assert "access-control-allow-origin" not in rejected.headers


def test_contact_sends_validated_message_to_resend(client):
    response_from_resend = MagicMock()
    response_from_resend.raise_for_status.return_value = None
    fake_client = AsyncMock()
    fake_client.__aenter__.return_value = fake_client
    fake_client.__aexit__.return_value = None
    fake_client.post.return_value = response_from_resend

    with patch.object(main.httpx, "AsyncClient", return_value=fake_client):
        response = client.post("/api/contact", json=valid_message())

    assert response.status_code == 202
    assert response.json() == {"message": "Message sent"}
    sent = fake_client.post.await_args.kwargs
    assert sent["headers"]["Authorization"] == "Bearer test-key"
    assert sent["json"]["reply_to"] == "alex@example.com"
    assert "Hello, I would like to connect." in sent["json"]["text"]


def test_invalid_email_is_rejected(client):
    response = client.post("/api/contact", json=valid_message(email="not-an-email"))
    assert response.status_code == 422


def test_honeypot_submission_is_discarded(client):
    with patch.object(main.httpx, "AsyncClient") as resend_client:
        response = client.post("/api/contact", json=valid_message(website="https://spam.example"))

    assert response.status_code == 202
    resend_client.assert_not_called()


def test_missing_resend_configuration_is_reported(client, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY")
    response = client.post("/api/contact", json=valid_message())
    assert response.status_code == 503
    assert response.json()["detail"] == "The contact form is temporarily unavailable."

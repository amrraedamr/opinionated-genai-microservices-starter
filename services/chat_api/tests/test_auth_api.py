"""Authentication behaviour chat_api must keep."""

from __future__ import annotations

import uuid

import pytest


def register_and_login(client, api_prefix: str) -> dict[str, str]:
    email = f"{uuid.uuid4().hex}@example.com"
    password = "Str0ng!Passw0rd"
    registered = client.post(
        f"{api_prefix}/auth/register",
        json={"email": email, "password": password, "firstName": "A", "lastName": "B"},
    )
    assert registered.status_code == 200, registered.text
    logged_in = client.post(
        f"{api_prefix}/auth/login", json={"email": email, "password": password}
    )
    assert logged_in.status_code == 200, logged_in.text
    return logged_in.json()["data"]


class TestHealth:
    def test_livez_does_not_touch_dependencies(self, client):
        body = client.get("/livez").json()
        assert body["status"] == "ok"
        assert body["checks"] == []

    def test_readyz_reports_capability_probes(self, client):
        body = client.get("/readyz").json()
        assert body["status"] == "ok"
        assert {check["name"] for check in body["checks"]} >= {"prompts"}


class TestAuthentication:
    def test_round_trip_issues_a_usable_token(self, client, api_prefix):
        tokens = register_and_login(client, api_prefix)
        response = client.get(
            f"{api_prefix}/users/me",
            headers={"Authorization": f"Bearer {tokens['accessToken']}"},
        )
        assert response.status_code == 200

    def test_refresh_returns_a_new_pair(self, client, api_prefix):
        tokens = register_and_login(client, api_prefix)
        response = client.post(
            f"{api_prefix}/auth/refresh",
            json={"refreshToken": tokens["refreshToken"]},
        )
        assert response.status_code == 200

    def test_unauthenticated_request_is_rejected(self, client, api_prefix):
        assert client.get(f"{api_prefix}/users/me").status_code in (401, 403)

    def test_access_token_is_not_a_refresh_token(self, client, api_prefix):
        tokens = register_and_login(client, api_prefix)
        response = client.post(
            f"{api_prefix}/auth/refresh", json={"refreshToken": tokens["accessToken"]}
        )
        assert response.status_code == 401

    def test_tampered_signature_is_rejected(self, client, api_prefix):
        tokens = register_and_login(client, api_prefix)
        tampered = tokens["accessToken"][:-3] + "xyz"
        response = client.get(
            f"{api_prefix}/users/me", headers={"Authorization": f"Bearer {tampered}"}
        )
        assert response.status_code == 401

    def test_duplicate_registration_is_rejected(self, client, api_prefix):
        email = f"{uuid.uuid4().hex}@example.com"
        payload = {
            "email": email,
            "password": "Str0ng!Passw0rd",
            "firstName": "A",
            "lastName": "B",
        }
        assert client.post(f"{api_prefix}/auth/register", json=payload).status_code == 200
        assert client.post(f"{api_prefix}/auth/register", json=payload).status_code >= 400


class TestOwnership:
    def test_a_user_cannot_read_another_users_conversation(self, client, api_prefix):
        owner = register_and_login(client, api_prefix)
        intruder = register_and_login(client, api_prefix)

        created = client.post(
            f"{api_prefix}/conversations",
            headers={"Authorization": f"Bearer {owner['accessToken']}"},
            json={"title": "private"},
        )
        if created.status_code >= 400:
            pytest.skip(f"conversation creation unavailable: {created.status_code}")

        conversation_id = created.json()["data"]["conversationId"]
        response = client.get(
            f"{api_prefix}/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {intruder['accessToken']}"},
        )
        assert response.status_code >= 400

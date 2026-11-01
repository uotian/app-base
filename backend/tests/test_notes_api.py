import pytest
from rest_framework.test import APIClient

from apps.notes.models import Note

pytestmark = pytest.mark.django_db


def test_public_read_and_create_with_csrf():
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/notes/")
    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]
    token = response.json()["csrfToken"]
    assert client.post("/api/notes/", {"text": "forged"}, format="json").status_code == 403
    assert (
        client.post(
            "/api/notes/",
            {"text": "forged"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_ORIGIN="https://evil.example",
        ).status_code
        == 403
    )
    response = client.post(
        "/api/notes/", {"text": " Shared note "}, format="json", HTTP_X_CSRFTOKEN=token
    )
    assert response.status_code == 201
    assert set(response.json()) == {"id", "text", "created_at"}
    assert Note.objects.get().text == "Shared note"
    assert APIClient().get("/api/notes/").json()["results"][0]["text"] == "Shared note"
    assert client.delete("/api/notes/", HTTP_X_CSRFTOKEN=token).status_code == 405
    assert client.get("/api/session/").status_code == 404


def test_notes_validate_and_paginate():
    Note.objects.bulk_create([Note(text=f"Note {i}") for i in range(21)])
    client = APIClient(enforce_csrf_checks=True)
    first = client.get("/api/notes/").json()
    assert first["count"] == 21
    assert len(first["results"]) == 20
    second = client.get("/api/notes/?page=2").json()
    assert len(second["results"]) == 1
    assert second["next"] is None
    assert client.get("/api/notes/?page=0").status_code == 404
    for text in ["", " ", "x" * 2001, None]:
        assert (
            client.post(
                "/api/notes/", {"text": text}, format="json", HTTP_X_CSRFTOKEN=first["csrfToken"]
            ).status_code
            == 400
        )
    assert Note.objects.count() == 21

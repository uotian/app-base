from django.test import override_settings
from rest_framework.test import APIClient


def test_greeting_contract():
    response = APIClient().get("/api/greeting/")
    assert response.status_code == 200
    assert response.json() == {"message": "Django + DRF が動いています"}


def test_only_get_is_supported():
    assert APIClient().post("/api/greeting/", {}).status_code == 405
    assert APIClient().get("/api/missing/").status_code == 404


@override_settings(DESKTOP_TOKEN="test-desktop-token")
def test_desktop_api_requires_its_private_token():
    client = APIClient()
    assert client.get("/api/greeting/").status_code == 403
    assert client.get("/api/greeting/", HTTP_AUTHORIZATION="Bearer wrong").status_code == 403
    assert client.get("/api/greeting/", HTTP_AUTHORIZATION="Bearer café").status_code == 403
    assert (
        client.get("/api/greeting/", HTTP_AUTHORIZATION="Bearer test-desktop-token").status_code
        == 200
    )


def test_dev_cors_does_not_allow_arbitrary_websites():
    client = APIClient()
    allowed = client.get("/api/greeting/", HTTP_ORIGIN="http://127.0.0.1:3100")
    assert allowed["Access-Control-Allow-Origin"] == "http://127.0.0.1:3100"
    denied = client.get("/api/greeting/", HTTP_ORIGIN="https://untrusted.example")
    assert "Access-Control-Allow-Origin" not in denied

import os
import subprocess
import sys

import pytest
from rest_framework.test import APIClient


def test_schema_documents_existing_contract():
    client = APIClient()
    response = client.get("/api/schema/?format=json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert set(schema["paths"]) == {"/api/greeting/", "/api/notes/"}
    notes = schema["paths"]["/api/notes/"]
    assert set(notes) == {"get", "post"}
    assert notes["get"]["parameters"][0]["name"] == "page"
    assert notes["post"]["parameters"][0]["name"] == "X-CSRFToken"
    request = schema["components"]["schemas"]["NoteInputRequest"]
    assert request["required"] == ["text"]
    assert request["properties"]["text"]["maxLength"] == 2000
    assert request["properties"]["text"]["minLength"] == 1
    assert client.get("/api/schema/")["Content-Type"].startswith("application/vnd.oai.openapi")


@pytest.mark.django_db
def test_schema_matches_real_responses():
    client = APIClient(enforce_csrf_checks=True)
    schema = client.get("/api/schema/?format=json").json()
    page = client.get("/api/notes/").json()
    created = client.post(
        "/api/notes/",
        {"text": "Schema contract"},
        format="json",
        HTTP_X_CSRFTOKEN=page["csrfToken"],
    )
    assert created.status_code == 201
    # Resolve component references using the actual generated document.
    for path, method, status, data in [
        ("/api/greeting/", "get", "200", client.get("/api/greeting/").json()),
        ("/api/notes/", "get", "200", client.get("/api/notes/").json()),
        ("/api/notes/", "post", "201", created.json()),
    ]:
        content = schema["paths"][path][method]["responses"][status]["content"]
        name = content["application/json"]["schema"]["$ref"].split("/")[-1]
        component = schema["components"]["schemas"][name]
        assert set(data) == set(component["properties"])
        assert set(component["required"]) <= set(data)
    assert schema["components"]["schemas"]["NotePage"]["properties"]["next"]["nullable"]
    assert schema["components"]["schemas"]["NotePage"]["properties"]["results"]["items"] == {
        "$ref": "#/components/schemas/Note"
    }


@pytest.mark.parametrize(
    ("path", "marker"), [("/api/docs/", b"SwaggerUIBundle"), ("/api/redoc/", b"redoc")]
)
def test_api_documentation_uses_schema(path, marker):
    response = APIClient().get(path)
    assert response.status_code == 200
    assert marker in response.content
    assert b"/api/schema/" in response.content


def test_desktop_does_not_publish_web_schema_or_docs():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import django
django.setup()
from django.urls import resolve, Resolver404
for path in ['/api/schema/', '/api/docs/', '/api/redoc/', '/api/notes/']:
    try:
        resolve(path)
    except Resolver404:
        continue
    raise AssertionError(path)
""",
        ],
        env={
            **os.environ,
            "DESKTOP_TOKEN": "test-token",
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "PYTHONPATH": "backend/src",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

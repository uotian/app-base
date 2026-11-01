import asyncio
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from mcp import Client

from server import create_server


@contextmanager
def running_server(command, log_path, env):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    root = Path(__file__).resolve().parents[2]
    with log_path.open("w+") as log:
        process = subprocess.Popen(
            [sys.executable, *command(port)],
            cwd=root,
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(log.read())
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                pytest.fail("Test server did not start")
            yield f"http://127.0.0.1:{port}"
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.fixture
def server_env():
    env = os.environ.copy()
    for name in ("PYTHONPATH", "DJANGO_SETTINGS_MODULE", "DESKTOP_TOKEN"):
        env.pop(name, None)
    env["PYTHONPYCACHEPREFIX"] = str(Path(__file__).resolve().parents[2] / ".cache/python")
    return env


@pytest.fixture
def api_url(tmp_path, server_env):
    env = {**server_env, "DJANGO_DB_PATH": str(tmp_path / "test.sqlite3")}
    root = Path(__file__).resolve().parents[2]
    subprocess.run(
        [sys.executable, "backend/manage.py", "migrate", "--noinput"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        timeout=30,
    )
    with running_server(
        lambda port: ["backend/manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        tmp_path / "django.log",
        env,
    ) as url:
        yield url


@pytest.fixture
def mcp_url(api_url, tmp_path, server_env):
    with running_server(
        lambda port: ["mcp/src/server.py", "--api-url", api_url, "--port", str(port)],
        tmp_path / "mcp.log",
        server_env,
    ) as url:
        yield f"{url}/mcp"


def test_mcp_http_to_django(mcp_url, api_url):
    with httpx.Client(base_url=api_url, timeout=10) as client:
        token = client.get("/api/notes/").json()["csrfToken"]
        for i in range(21):
            response = client.post(
                "/api/notes/", json={"text": f"Note {i}"}, headers={"X-CSRFToken": token}
            )
            assert response.status_code == 201

    async def exercise():
        async with Client(mcp_url) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {"list_notes", "add_note"}
            first = await client.call_tool("list_notes", {})
            assert not first.is_error
            assert first.structured_content["count"] == 21
            assert first.structured_content["has_next"] is True
            assert len(first.structured_content["results"]) == 20
            assert "csrf" not in str(first.structured_content).lower()
            second = await client.call_tool("list_notes", {"page": 2})
            assert len(second.structured_content["results"]) == 1
            assert second.structured_content["has_next"] is False
            for arguments in [{"page": 0}, {"page": 999}]:
                assert (await client.call_tool("list_notes", arguments)).is_error
            for text in ["", "  ", "x" * 2001]:
                assert (await client.call_tool("add_note", {"text": text})).is_error
            added = await client.call_tool("add_note", {"text": " From MCP "})
            assert not added.is_error
            assert added.structured_content["text"] == "From MCP"
            return added.structured_content["id"]

    note_id = asyncio.run(exercise())
    page = httpx.get(f"{api_url}/api/notes/").json()
    assert page["count"] == 22
    assert page["results"][0]["id"] == note_id
    assert page["results"][0]["text"] == "From MCP"
    assert httpx.post(f"{api_url}/api/notes/", json={"text": "forged"}).status_code == 403
    response = httpx.post(
        mcp_url, headers={"Origin": "https://evil.example"}, json={"jsonrpc": "2.0"}
    )
    assert response.status_code == 403


@pytest.mark.parametrize("failure", ["timeout", "status", "invalid"])
@pytest.mark.parametrize(
    ("tool_name", "stage"), [("add_note", "GET"), ("add_note", "POST"), ("list_notes", "GET")]
)
def test_api_errors_are_tool_errors_without_leaking_response(
    monkeypatch, failure, tool_name, stage
):
    calls = []

    async def request(self, method, url, **kwargs):
        calls.append(method)
        if method != stage:
            return httpx.Response(
                200,
                json={
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "results": [],
                    "csrfToken": "test-token",
                },
                request=httpx.Request(method, url),
            )
        if failure == "timeout":
            raise httpx.ReadTimeout("private connection details")
        return httpx.Response(
            503 if failure == "status" else 200,
            text="private response details",
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", request)

    async def exercise():
        async with Client(create_server("http://127.0.0.1:8100")) as client:
            arguments = {"text": "test"} if tool_name == "add_note" else {}
            result = await client.call_tool(tool_name, arguments)
            assert result.is_error
            assert "private" not in str(result)
            if stage == "POST":
                assert "may already have been saved" in str(result)
            elif failure == "invalid":
                assert "may already have been saved" not in str(result)

    asyncio.run(exercise())
    assert calls == (["GET"] if stage == "GET" else ["GET", "POST"])


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/db",
        "https://user:pass@example.test",
        "http://a/x",
        "http://example.test:abc",
        "http://[invalid]",
    ],
)
def test_api_origin_validation(url):
    with pytest.raises(ValueError):
        create_server(url)


def test_mcp_imports_are_isolated():
    root = Path(__file__).resolve().parents[2]
    assert Path(sys.modules["server"].__file__).resolve() == root / "mcp/src/server.py"
    assert root / "backend/src" not in {Path(path).resolve() for path in sys.path}
    assert "django" not in sys.modules

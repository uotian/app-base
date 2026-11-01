import ast
from pathlib import Path

import pytest

ALLOWED = {
    "server.py": {"argparse", "mcp", "registry"},
    "registry.py": {"collections.abc", "mcp", "notes.tools", "notes.notes_api_url"},
    "notes/tools/list_notes.py": {
        "typing",
        "mcp",
        "pydantic",
        "httpx",
        "notes.django",
        "notes.schemas",
    },
    "notes/tools/add_note.py": {
        "typing",
        "mcp",
        "pydantic",
        "httpx",
        "notes.django",
        "notes.schemas",
    },
    "notes/django/request.py": {"httpx", "notes.django.error"},
    "notes/django/error.py": set(),
    "notes/notes_api_url.py": {"httpx"},
    "notes/schemas.py": {"datetime", "typing", "pydantic"},
}


def forbidden_imports(source, area):
    forbidden = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = (
                [f"{node.module}.{alias.name}" for alias in node.names]
                if not node.level
                else ["relative import"]
            )
        else:
            continue
        forbidden.extend(
            name
            for name in modules
            if not any(
                name == allowed or name.startswith(allowed + ".") for allowed in ALLOWED[area]
            )
        )
    return forbidden


def forbidden_http_sends(source, area):
    if Path(area).parts[-2:] == ("django", "request.py"):
        return []
    tree = ast.parse(source)
    scope_types = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

    def local_nodes(scope):
        for child in ast.iter_child_nodes(scope):
            if not isinstance(child, scope_types):
                yield child
                yield from local_nodes(child)

    module_imports = [
        node for node in local_nodes(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    scopes = [tree, *(node for node in ast.walk(tree) if isinstance(node, scope_types))]
    return sorted(
        line
        for scope in scopes
        for line in http_sends_in_scope([*module_imports, *local_nodes(scope)])
    )


def http_sends_in_scope(nodes):
    aliases = {}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "httpx":
                    aliases[alias.asname or alias.name] = "httpx"
        elif isinstance(node, ast.ImportFrom) and node.module == "httpx":
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"httpx.{alias.name}"

    def reference(node):
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return f"{reference(node.value)}.{node.attr}"
        return ""

    client_types = {"httpx.Client", "httpx.AsyncClient"}
    clients = set()
    for node in nodes:
        if isinstance(node, ast.arg) and reference(node.annotation) in client_types:
            clients.add(node.arg)
        if isinstance(node, ast.withitem):
            value, targets = node.context_expr, [node.optional_vars]
        elif isinstance(node, ast.Assign):
            value, targets = node.value, node.targets
        elif isinstance(node, ast.AnnAssign):
            value, targets = node.value, [node.target]
        else:
            continue
        if isinstance(value, ast.Call) and reference(value.func) in client_types:
            clients.update(target.id for target in targets if isinstance(target, ast.Name))

    methods = {
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "request",
        "send",
        "stream",
    }
    violations = []
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        if reference(node.func) in {f"httpx.{method}" for method in methods}:
            violations.append(node.lineno)
        elif isinstance(node.func, ast.Attribute) and node.func.attr in methods:
            receiver = node.func.value
            if (isinstance(receiver, ast.Name) and receiver.id in clients) or (
                isinstance(receiver, ast.Call) and reference(receiver.func) in client_types
            ):
                violations.append(node.lineno)
    return sorted(violations)


def test_mcp_dependency_direction():
    root = Path(__file__).resolve().parents[1] / "src"
    for path in root.rglob("*.py"):
        area = path.relative_to(root).as_posix()
        assert area in ALLOWED, f"Unexpected source location: {area}"
        source = path.read_text()
        assert not forbidden_imports(source, area), area
        assert not forbidden_http_sends(source, area), area


@pytest.mark.parametrize(
    ("area", "source", "expected"),
    [
        ("notes/tools/list_notes.py", "from notes import django", []),
        ("notes/tools/list_notes.py", "from notes.django.request import request", []),
        ("notes/tools/list_notes.py", "from notes.schemas import Note", []),
        ("notes/schemas.py", "from pydantic import BaseModel", []),
        ("notes/tools/list_notes.py", "import httpx", []),
        ("notes/tools/add_note.py", "from notes import django", []),
        ("notes/tools/add_note.py", "import httpx", []),
        (
            "notes/tools/list_notes.py",
            "from mcp.server import MCPServer",
            [],
        ),
        (
            "notes/schemas.py",
            "from notes.tools.add_note import register_add_note",
            ["notes.tools.add_note.register_add_note"],
        ),
        ("notes/schemas.py", "from notes import django", ["notes.django"]),
        ("notes/tools/list_notes.py", "import notes.tools", ["notes.tools"]),
        (
            "notes/tools/list_notes.py",
            "from apps.notes.models import Note",
            ["apps.notes.models.Note"],
        ),
        ("notes/tools/list_notes.py", "import sqlite3", ["sqlite3"]),
        ("notes/tools/list_notes.py", "import django", ["django"]),
        ("notes/tools/add_note.py", "from notes.django.request import request", []),
        ("notes/django/request.py", "from notes.django.error import NoteAPIError", []),
        (
            "notes/django/request.py",
            "from notes.tools.add_note import register_add_note",
            ["notes.tools.add_note.register_add_note"],
        ),
        ("notes/django/error.py", "import httpx", ["httpx"]),
        (
            "notes/django/error.py",
            "from notes.django.request import request",
            ["notes.django.request.request"],
        ),
        ("notes/notes_api_url.py", "import httpx", []),
        ("notes/notes_api_url.py", "import notes.tools", ["notes.tools"]),
        ("registry.py", "import httpx", ["httpx"]),
        ("registry.py", "import server", ["server"]),
        ("notes/tools/add_note.py", "import registry", ["registry"]),
        ("server.py", "from registry import TOOL_REGISTRARS", []),
        ("server.py", "import notes.tools", ["notes.tools"]),
        ("server.py", "import notes.notes_api_url", ["notes.notes_api_url"]),
        ("registry.py", "from notes.notes_api_url import notes_api_url", []),
        ("server.py", "import httpx", ["httpx"]),
        ("registry.py", "from notes.tools.list_notes import register_list_notes", []),
        ("notes/tools/list_notes.py", "from . import django", ["relative import"]),
        ("notes/tools/list_notes.py", "import notes.django_extra", ["notes.django_extra"]),
    ],
)
def test_import_check_rejects_crossing_responsibilities(area, source, expected):
    assert forbidden_imports(source, area) == expected


@pytest.mark.parametrize(
    ("source", "area", "expected"),
    [
        ("import httpx\nhttpx.get(url)", "notes/tools/list_notes.py", [2]),
        ("import httpx as h\nh.post(url)", "notes/tools/add_note.py", [2]),
        ("from httpx import get as fetch\nfetch(url)", "notes/notes_api_url.py", [2]),
        (
            "import httpx\nasync with httpx.AsyncClient() as api:\n    await api.get(url)",
            "notes/tools/list_notes.py",
            [3],
        ),
        (
            "from httpx import Client as HTTPClient\napi = HTTPClient()\napi.send(req)",
            "notes/tools/add_note.py",
            [3],
        ),
        (
            "import httpx\nasync def f(api: httpx.AsyncClient):\n    await api.stream('GET', url)",
            "notes/tools/list_notes.py",
            [3],
        ),
        (
            "import httpx\nasync with httpx.AsyncClient(timeout=10) as api:\n"
            "    await request(api, 'GET', url)",
            "notes/tools/list_notes.py",
            [],
        ),
        ("import httpx\nhttpx.URL(url).join('/api/notes/')", "notes/notes_api_url.py", []),
        ("data.get('text')", "notes/tools/list_notes.py", []),
        (
            "import httpx\nasync def fetch(client: httpx.AsyncClient):\n"
            "    return await request(client, 'GET', url)\n"
            "def setting(client: dict):\n    return client.get('name')",
            "notes/tools/list_notes.py",
            [],
        ),
        (
            "import httpx\ndef outer(client: httpx.AsyncClient):\n"
            "    def inner(client: dict):\n        return client.get('name')\n"
            "    return client.get(url)",
            "notes/tools/list_notes.py",
            [5],
        ),
        (
            "import httpx\nasync def f(client: httpx.AsyncClient):\n"
            "    return await client.request('GET', url)",
            "notes/django/request.py",
            [],
        ),
    ],
)
def test_http_send_check(source, area, expected):
    assert forbidden_http_sends(source, area) == expected

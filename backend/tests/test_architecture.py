"""Mechanical boundaries only; business responsibilities still require review."""

import ast
import sys
from pathlib import Path

import pytest
from django.apps import apps as django_apps

from config import settings

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DEPENDENCIES = {
    "api": {"api", "apps", "utils"},
    "apps": {"apps", "lib", "utils"},
    "lib": {"lib", "utils"},
    "utils": {"utils"},
    "config": {"config", "api", "apps", "lib", "utils"},
}
IO_MODULES = {"os", "sys", "subprocess", "platform", "socket", "requests", "httpx", "urllib", "io"}
APP_DIRECTORIES = {
    "models",
    "admins",
    "actions",
    "services",
    "bridges",
    "migrations",
    "utils",
    "management",
    "templates",
    "static",
}
FILE_IO_METHODS = {"read_text", "read_bytes", "write_text", "write_bytes"}


def violations(source: str, filename: str) -> list[str]:
    errors = []
    path = Path(filename)
    layer = path.parts[0]
    is_common = path.parts[:2] == ("apps", "_common")
    is_app_utils = layer == "apps" and path.parts[2:3] == ("utils",)
    is_pure = layer == "utils" or is_app_utils
    no_direct_io = (
        layer == "api"
        or is_pure
        or (
            layer == "apps"
            and path.parts[2:3]
            in {("models",), ("admins",), ("actions",), ("services",), ("bridges",)}
        )
    )
    if filename != "server.py" and (len(path.parts) < 2 or layer not in DEPENDENCIES):
        errors.append("PY03: ソースはsrcのconfig/apps/api/lib/utils以下へ置く")
    if layer == "apps" and any(
        part in {"views", "serializers", "urls"} for part in path.with_suffix("").parts[2:]
    ):
        errors.append("PY03: HTTP入口はappsではなくapiへ置く")
    if (
        layer == "apps"
        and len(path.parts) == 3
        and path.name in {"models.py", "services.py", "admins.py", "actions.py", "bridges.py"}
    ):
        errors.append("PY03: models・admins・actions・services・bridgesはディレクトリに分ける")
    if filename in {"api/views.py", "api/serializers.py"}:
        errors.append("PY03: viewとserializerはapi/views・api/serializers以下に内容別で置く")
    if layer == "apps" and len(path.parts) >= 4:
        allowed = {"models"} if is_common else APP_DIRECTORIES
        if path.parts[2] not in allowed:
            errors.append("PY03: app内は規約で定めた分類に揃える")
        if path.parts[2] == "services" and len(path.parts) == 4:
            errors.append("PY03: servicesはサービスの種類ごとに分け、組み立てはactionsへ置く")
    if layer == "lib" and path.parts[1:2] not in {("files",), ("clients",)}:
        errors.append("PY03: 外部I/Oはlib/files・lib/clients、純粋な共通処理はutilsへ置く")
    if layer == "api" and any(
        part in {"models", "migrations"} for part in path.with_suffix("").parts[1:]
    ):
        errors.append("PY03: モデルとmigrationはappsへ置く")
    for node in ast.walk(ast.parse(source)):
        if no_direct_io and isinstance(node, ast.Call):
            function = node.func
            if (
                isinstance(function, ast.Name)
                and function.id == "open"
                or isinstance(function, ast.Attribute)
                and (function.attr in FILE_IO_METHODS or function.attr == "open")
            ):
                errors.append("PY02: ファイル操作はlib/filesへ置く")
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            prefix = path.parts[: -node.level] if node.level else ()
            base = ".".join((*prefix, node.module or "")).rstrip(".")
            modules = [f"{base}.{alias.name}" for alias in node.names]
        else:
            continue
        for module in modules:
            target = module.split(".")[0]
            if target in {"frontend", "native"}:
                errors.append("PY01: Pythonからfrontend/nativeの実装を参照しない")
            if no_direct_io and target in IO_MODULES:
                errors.append("PY02: 外部I/Oはlib/files・lib/clientsへ置く")
            if (
                layer in DEPENDENCIES
                and target in DEPENDENCIES
                and target not in DEPENDENCIES[layer]
            ):
                errors.append("PY04: apiからapps、appsからlib、libからutilsの依存方向を守る")
            if layer in {"apps", "lib", "utils"} and target == "rest_framework":
                errors.append("PY04: DRFのHTTP処理はapiに置く")
            if is_common and target == "apps" and not module.startswith("apps._common."):
                errors.append("PY04: _commonから個別の機能appに依存しない")
            if layer == "apps" and len(path.parts) >= 3 and target == "apps":
                target_parts = module.split(".")
                own_app = path.parts[1]
                source_kind = path.parts[2]
                target_app = target_parts[1] if len(target_parts) > 1 else ""
                target_kind = target_parts[2] if len(target_parts) > 2 else ""
                if (
                    target_app
                    and target_app not in {own_app, "_common"}
                    and (source_kind != "bridges" or target_kind != "actions")
                ):
                    errors.append("PY04: 他appは自appのbridgesから相手のactionsだけを呼ぶ")
                if target_app == own_app and (
                    source_kind == "services"
                    and target_kind in {"actions", "bridges"}
                    or source_kind == "bridges"
                    and target_kind in {"actions", "services"}
                ):
                    errors.append("PY04: actionsがservices・bridgesを組み立て、逆依存しない")
            if is_pure and target in {"django", *IO_MODULES}:
                errors.append("PY04: utilsはDjango・外部I/Oに依存しない")
            if is_app_utils and target in DEPENDENCIES and target != "utils":
                own_utils = ".".join(path.parts[:3]) + "."
                if not module.startswith(own_utils):
                    errors.append("PY04: app内utilsは同じutilsと共通utilsだけを利用する")
    return errors


def test_backend_boundaries():
    for path in SRC.rglob("*.py"):
        assert not violations(path.read_text(), path.relative_to(SRC).as_posix()), path


def test_python_bytecode_cache_is_centralized():
    cache_root = ROOT.parent / ".cache" / "python"
    assert sys.pycache_prefix is not None
    assert Path(sys.pycache_prefix).resolve() == cache_root
    cached_module = Path(settings.__cached__).resolve()
    assert cached_module.is_relative_to(cache_root)
    assert cached_module.is_file()


def test_backend_source_layout():
    assert {path.name for path in ROOT.glob("*.py")} == {"manage.py"}
    for directory in ROOT.iterdir():
        assert directory.name == "tests" or not (directory / "__init__.py").is_file(), directory
    for config in django_apps.get_app_configs():
        path = Path(config.path).resolve()
        if path.is_relative_to(SRC):
            assert path.parent == SRC / "apps", config.name
            assert config.name == f"apps.{path.name}", config.name
    for directory in (SRC / "apps").iterdir():
        if (directory / "apps.py").is_file():
            assert django_apps.is_installed(f"apps.{directory.name}"), directory


@pytest.mark.parametrize("source", ["import subprocess", "from httpx import get", "import native"])
@pytest.mark.parametrize("path", ["api/views/greeting.py", "api/serializers/greeting.py"])
def test_rule_rejects_intentional_violations(source, path):
    assert violations(source, path)


def test_rule_allows_normal_api_imports():
    assert not violations(
        "from api.serializers.greeting import GreetingSerializer", "api/views/greeting.py"
    )


@pytest.mark.parametrize(
    ("source", "path", "rule"),
    [
        ("", "hello/views.py", "PY03"),
        ("", "apps/hello/views.py", "PY03"),
        ("", "apps/hello/serializers.py", "PY03"),
        ("", "apps/hello/views/greeting.py", "PY03"),
        ("", "apps/hello/serializers/greeting.py", "PY03"),
        ("", "api/views.py", "PY03"),
        ("", "api/serializers.py", "PY03"),
        ("", "api/models.py", "PY03"),
        ("", "api/models/greeting.py", "PY03"),
        ("", "apps/hello/models.py", "PY03"),
        ("", "apps/hello/services.py", "PY03"),
        ("", "apps/hello/admins.py", "PY03"),
        ("from api import views", "apps/hello/services/greeters/greeting.py", "PY04"),
        ("from .....api import views", "apps/hello/services/greeters/greeting.py", "PY04"),
        ("from lib.clients.example import send", "api/views/greeting.py", "PY04"),
        ("from apps.hello import services", "lib/clients/example.py", "PY04"),
        ("from ...apps.hello import services", "lib/clients/example.py", "PY04"),
        (
            "from rest_framework.request import Request",
            "apps/hello/services/greeters/greeting.py",
            "PY04",
        ),
        ("from django.conf import settings", "utils/text.py", "PY04"),
        ("import requests", "utils/text.py", "PY04"),
        ("", "apps/notes/repositories/note.py", "PY03"),
        ("", "apps/_common/lib/files/json.py", "PY03"),
        ("", "lib/utils/text.py", "PY03"),
        ("from apps.notes.models import Note", "apps/_common/models/base.py", "PY04"),
        ("from apps import notes", "apps/_common/models/base.py", "PY04"),
        ("from ...notes.models import Note", "apps/_common/models/base.py", "PY04"),
        ("import httpx", "apps/notes/services/importers/note.py", "PY02"),
        ("path.read_text()", "apps/notes/services/importers/note.py", "PY02"),
        ("open(path)", "apps/notes/services/importers/note.py", "PY02"),
        ("from io import open", "apps/notes/services/importers/note.py", "PY02"),
        ("path.write_text(text)", "utils/text.py", "PY02"),
        ("from lib.files.json import read_json", "apps/notes/utils/text.py", "PY04"),
    ],
)
def test_layout_and_dependency_rules_reject_violations(source, path, rule):
    assert any(error.startswith(rule) for error in violations(source, path))


@pytest.mark.parametrize(
    ("source", "path"),
    [
        ("from apps.hello import services", "api/views/greeting.py"),
        ("from ..serializers.greeting import GreetingSerializer", "api/views/greeting.py"),
        ("from rest_framework import serializers", "api/serializers/greeting.py"),
        ("from lib.clients.example import send", "apps/hello/services/greeters/greeting.py"),
        ("from django.db import models", "apps/hello/models/greeting.py"),
        ("from .greeting import Greeting", "apps/hello/models/__init__.py"),
        ("from django.contrib import admin", "apps/hello/admins/greeting.py"),
        ("from .admins.greeting import GreetingAdmin", "apps/hello/admin.py"),
        ("from utils.text import normalize", "lib/clients/example.py"),
        ("from math import ceil", "utils/numbers.py"),
        ("from django.db import models", "apps/_common/models/base.py"),
        ("from apps._common.models.base import BaseModel", "apps/notes/models/note.py"),
        ("from django.db.models import QuerySet", "apps/notes/models/querysets/note.py"),
        ("from django.db.models import Manager", "apps/notes/models/managers/note_import.py"),
        ("from lib.files.json import read_json", "apps/notes/services/importers/note.py"),
        ("from pathlib import Path", "apps/notes/actions/importer.py"),
        ("path.read_text()", "lib/files/json.py"),
        ("import httpx", "lib/clients/example.py"),
        ("from utils.text import normalize", "apps/notes/utils/text.py"),
    ],
)
def test_layout_and_dependency_rules_allow_normal_imports(source, path):
    assert not violations(source, path)


@pytest.mark.parametrize(
    ("source", "path", "rule"),
    [
        ("", "apps/notes/actions.py", "PY03"),
        ("", "apps/notes/bridges.py", "PY03"),
        ("", "apps/notes/services/importer.py", "PY03"),
        ("path.read_text()", "apps/notes/actions/importer.py", "PY02"),
        ("import httpx", "apps/notes/bridges/notify.py", "PY02"),
        ("from apps.hello.models import Greeting", "apps/notes/actions/importer.py", "PY04"),
        ("from apps.hello.actions.notify import Notify", "apps/notes/actions/importer.py", "PY04"),
        (
            "from apps.hello.actions.notify import Notify",
            "apps/notes/services/importers/note.py",
            "PY04",
        ),
        ("from apps.hello.models import Greeting", "apps/notes/bridges/notify.py", "PY04"),
        ("import apps.hello.services.greeters.greeting", "apps/notes/bridges/notify.py", "PY04"),
        (
            "from ...hello.services.greeters.greeting import Greeting",
            "apps/notes/bridges/notify.py",
            "PY04",
        ),
        ("from apps import hello", "apps/notes/bridges/notify.py", "PY04"),
        (
            "from apps.notes.actions.importer import Importer",
            "apps/notes/services/importers/note.py",
            "PY04",
        ),
        ("from ...bridges.notify import Notify", "apps/notes/services/importers/note.py", "PY04"),
        ("from ..actions.importer import Importer", "apps/notes/bridges/notify.py", "PY04"),
        (
            "from ..services.importers.note import NoteImporter",
            "apps/notes/bridges/notify.py",
            "PY04",
        ),
    ],
)
def test_app_boundaries_reject_violations(source, path, rule):
    assert any(error.startswith(rule) for error in violations(source, path))


@pytest.mark.parametrize(
    ("source", "path"),
    [
        ("from apps.notes.actions.importer import Importer", "api/views/notes.py"),
        ("from ..services.importers.note import NoteImporter", "apps/notes/actions/importer.py"),
        ("from ..models import Note", "apps/notes/actions/importer.py"),
        ("from ..bridges.notify import Notify", "apps/notes/actions/importer.py"),
        ("from apps.hello.actions.notify import Notify", "apps/notes/bridges/notify.py"),
        ("from ...hello.actions.notify import Notify", "apps/notes/bridges/notify.py"),
        ("import apps.hello.actions.notify", "apps/notes/bridges/notify.py"),
        ("from apps.notes.models import Note", "apps/notes/services/importers/note.py"),
        ("from apps._common.models.base import BaseModel", "apps/notes/models/note.py"),
        ("from .base import BaseModel", "apps/_common/models/example.py"),
    ],
)
def test_app_boundaries_allow_normal_imports(source, path):
    assert not violations(source, path)

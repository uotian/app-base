from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

root = Path(SPEC).resolve().parent
a = Analysis(
    [str(root / "src/server.py")],
    pathex=[str(root / "src")],
    datas=[(str(root / "build/static"), "static"),
           (str(root / "src/apps/notes/templates"), "apps/notes/templates")] + collect_data_files("drf_spectacular"),
    hiddenimports=[
        "config.settings", "config.urls", "api.permissions", "api.urls",
        "api.views.greeting", "api.serializers.greeting",
        "api.views.notes", "api.serializers.notes",
        "apps.hello.apps", "apps.notes.apps", "apps.notes.models",
        "django.db.backends.sqlite3", "whitenoise.middleware",
        "drf_spectacular", "drf_spectacular.openapi",
        "unfold", "unfold.contrib.import_export", "unfold.contrib.simple_history",
        "import_export", "simple_history", "simple_history.middleware",
        "adminsortable2", "django_filters", "django_filters.rest_framework",
        "rest_framework", "rest_framework.renderers", "rest_framework.parsers",
        "rest_framework.authentication", "rest_framework.permissions",
        "django.middleware.security", "django.middleware.common", "corsheaders.middleware",
    ] + collect_submodules("apps.notes") + collect_submodules("tablib.formats"),
    excludes=["pytest", "mypy", "ruff"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="backend", console=True)
coll = COLLECT(exe, a.binaries, a.datas, name="backend")

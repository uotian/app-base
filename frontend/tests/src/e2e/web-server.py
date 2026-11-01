"""Run the real Web server against a disposable database."""

import os
import secrets
import signal
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "backend/src"))


def stop_server(_signum, _frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop_server)
    with tempfile.TemporaryDirectory(prefix="app-base-e2e-") as directory:
        os.environ["DJANGO_DB_PATH"] = str(Path(directory) / "test.sqlite3")
        os.environ["DJANGO_SECRET_KEY"] = secrets.token_urlsafe(48)
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
        os.environ.pop("DESKTOP_TOKEN", None)

        import django

        django.setup()

        from django.core.management import call_command

        call_command("migrate", interactive=False, verbosity=0)

        from django.contrib.auth.models import User

        User.objects.create_superuser("e2e-admin", password="test-only-admin-password")

        from server import main

        main()

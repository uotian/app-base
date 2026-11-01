import os
import subprocess
import sys

import pytest
from django.contrib.auth.models import Permission, User
from django.test import Client
from django.urls import reverse

from apps.notes.models import Note

pytestmark = pytest.mark.django_db


def staff(username):
    user = User.objects.create_user(username=username, is_staff=True)
    user.user_permissions.set(Permission.objects.filter(content_type__app_label="notes"))
    return user


def test_admin_requires_login_and_model_permission():
    url = reverse("admin:notes_note_changelist")
    client = Client()
    assert client.get(url).status_code == 302
    user = User.objects.create_user(username="no-permissions", is_staff=True)
    client.force_login(user)
    assert client.get(url).status_code == 403


def test_admin_add_validates():
    user = staff("writer")
    client = Client()
    client.force_login(user)
    url = reverse("admin:notes_note_add")
    assert client.post(url, {"text": "   ", "_save": "Save"}).status_code == 200
    assert not Note.objects.exists()
    assert client.post(url, {"text": "x" * 2001, "_save": "Save"}).status_code == 200
    assert not Note.objects.exists()
    response = client.post(url, {"text": "A saved note", "_save": "Save"})
    assert response.status_code == 302
    note = Note.objects.get()
    assert note.text == "A saved note"
    assert note.created_at is not None


def test_staff_with_permission_can_manage_shared_notes():
    user = staff("editor")
    note = Note.objects.create(text="Shared note")
    client = Client()
    client.force_login(user)
    response = client.get(reverse("admin:notes_note_changelist"))
    assert note.text in response.content.decode()
    url = reverse("admin:notes_note_change", args=[note.pk])
    assert client.post(url, {"text": "Updated", "_save": "Save"}).status_code == 302
    note.refresh_from_db()
    assert note.text == "Updated"


def test_admin_post_requires_csrf():
    client = Client(enforce_csrf_checks=True)
    client.force_login(staff("csrf"))
    assert client.post(reverse("admin:notes_note_add"), {"text": "forged"}).status_code == 403
    assert not Note.objects.exists()


def test_sqlite_survives_separate_processes(tmp_path):
    env = {**os.environ, "DJANGO_DB_PATH": str(tmp_path / "notes.sqlite3")}
    command = [sys.executable, "backend/manage.py"]
    subprocess.run([*command, "migrate", "--noinput"], env=env, check=True, capture_output=True)
    subprocess.run(
        [
            *command,
            "shell",
            "-c",
            "from django.contrib.auth.models import User; from apps.notes.models import Note; "
            "Note.objects.create(text='Persistent')",
        ],
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            *command,
            "shell",
            "-c",
            "from apps.notes.models import Note; assert Note.objects.get().text == 'Persistent'",
        ],
        env=env,
        check=True,
        capture_output=True,
    )


def test_admin_login_uses_django_authentication():
    user = staff("login")
    user.set_password("test-only-admin-password")
    user.save()
    client = Client()
    url = reverse("admin:login")
    assert client.post(url, {"username": "login", "password": "wrong"}).status_code == 200
    assert "_auth_user_id" not in client.session
    assert (
        client.post(
            url,
            {
                "username": "login",
                "password": "test-only-admin-password",
                "next": "/admin/",
            },
        ).status_code
        == 302
    )
    assert client.session["_auth_user_id"] == str(user.pk)
    assert client.get(reverse("admin:notes_note_changelist")).status_code == 200


@pytest.mark.django_db(transaction=True)
def test_public_note_migration_preserves_existing_content():
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    previous = [("notes", "0001_initial")]
    latest = executor.loader.graph.leaf_nodes("notes")
    executor.migrate(previous)
    try:
        old_note = executor.loader.project_state(previous).apps.get_model("notes", "Note")
        user = User.objects.create_user(username="previous-owner")
        saved = old_note.objects.create(owner_id=user.pk, text="Keep this note")
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        actual = Note.objects.get(pk=saved.pk)
        assert actual.text == saved.text
        assert actual.created_at == saved.created_at
        assert actual.position > 0
        assert actual.history.get().text == saved.text
        assert actual.history.get().history_change_reason == "Initial snapshot at history adoption"
    finally:
        MigrationExecutor(connection).migrate(latest)

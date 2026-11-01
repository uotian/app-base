import json

import pytest
from django.contrib.auth.models import Permission, User
from django.test import Client
from django.urls import reverse
from import_export.formats.base_formats import CSV, XLSX
from tablib import Dataset

from apps.notes.admins.note import NoteResource
from apps.notes.models import Note
from apps.notes.services.importers.note import NoteImporter

pytestmark = pytest.mark.django_db


def admin_client(*permissions):
    user = User.objects.create_user(username="manager", is_staff=True)
    user.user_permissions.set(
        Permission.objects.filter(content_type__app_label="notes", codename__in=permissions)
    )
    client = Client()
    client.force_login(user)
    return client, user


def test_extension_pages_and_permissions():
    client, _ = admin_client("view_note")
    note = Note.objects.create(text="Read only")
    assert client.get(reverse("admin:notes_note_export")).status_code == 200
    assert client.get(reverse("admin:notes_note_import")).status_code == 403
    assert client.get(reverse("admin:notes_note_history", args=[note.pk])).status_code == 200
    assert (
        client.post(
            reverse("admin:notes_note_sortable_update"),
            data=json.dumps({"updatedItems": [[note.pk, 2]]}),
            content_type="application/json",
        ).status_code
        == 403
    )
    historical = note.history.get()
    history_form = reverse("admin:notes_note_simple_history", args=[note.pk, historical.history_id])
    assert client.post(history_form, {"text": "Forged restore", "_save": "Save"}).status_code == 403
    note.refresh_from_db()
    assert note.text == "Read only"
    no_permissions = User.objects.create_user(username="no-permissions", is_staff=True)
    client.force_login(no_permissions)
    for name in ["import", "export"]:
        assert client.get(reverse(f"admin:notes_note_{name}")).status_code == 403
    assert client.get(reverse("admin:notes_note_history", args=[note.pk])).status_code == 403


def test_reordering_updates_admin_order_and_history_atomically():
    client, user = admin_client("view_note", "add_note", "change_note")
    first = Note.objects.create(text="First")
    second = Note.objects.create(text="Second")
    url = reverse("admin:notes_note_sortable_update")
    response = client.post(
        url,
        data=json.dumps(
            {"updatedItems": [[first.pk, second.position], [second.pk, first.position]]}
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    listing = client.get(reverse("admin:notes_note_changelist"))
    assert b"admin_sortable2_config" in listing.content
    assert list(listing.context["cl"].result_list) == [first, second]
    assert list(Note.objects.all()) == [second, first]
    first.refresh_from_db()
    assert first.history.first().position == first.position
    assert first.history.first().history_user_id == user.pk
    before = list(Note.objects.values_list("id", "position"))
    history_count = Note.history.count()
    assert (
        client.post(
            url,
            data=json.dumps({"updatedItems": [[first.pk, 99], [999999, 1]]}),
            content_type="application/json",
        ).status_code
        == 400
    )
    assert list(Note.objects.values_list("id", "position")) == before
    assert Note.history.count() == history_count
    newest = Note.objects.create(text="Newest")
    assert Note.objects.first() == newest
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(user)
    assert csrf_client.post(url, data="{}", content_type="application/json").status_code == 403


@pytest.mark.parametrize("file_format", [CSV, XLSX])
def test_import_export_round_trip_and_dry_run(file_format):
    note = Note.objects.create(text="Original")
    resource = NoteResource()
    exported = file_format().export_data(resource.export())
    dataset = file_format().create_dataset(exported)
    assert dataset.headers == ["id", "text", "created_at"]
    dataset[0] = [note.pk, " Updated ", dataset[0][2]]
    assert not resource.import_data(dataset, dry_run=True).has_errors()
    note.refresh_from_db()
    assert note.text == "Original"
    assert note.history.count() == 1
    result = resource.import_data(dataset, rollback_on_validation_errors=True)
    assert not result.has_errors() and not result.has_validation_errors()
    note.refresh_from_db()
    assert note.text == "Updated"
    assert note.history.first().text == "Updated"


def test_import_validation_rolls_back_all_rows():
    dataset = Dataset(["", "Valid"], ["", "   "], headers=["id", "text"])
    result = NoteResource().import_data(dataset, rollback_on_validation_errors=True)
    assert result.has_errors() or result.has_validation_errors()
    assert not Note.objects.exists()
    assert Note.history.count() == 0
    dataset = Dataset(["", "x" * 2001], headers=["id", "text"])
    assert NoteResource().import_data(dataset).has_validation_errors()


@pytest.mark.parametrize("text", ["=1+1", "+1+1", "-1+1", "@SUM(A1)", "\t=1+1", "  =1+1"])
def test_spreadsheet_export_keeps_untrusted_text_inert(text):
    note = Note.objects.create(text=text)
    for file_format in [CSV, XLSX]:
        exported = file_format().export_data(NoteResource().export())
        row = file_format().create_dataset(exported).dict[0]
        assert row["text"] == "'" + text
    note.refresh_from_db()
    assert note.text == text


def test_admin_and_json_import_record_history(tmp_path):
    client, user = admin_client("view_note", "add_note", "change_note", "delete_note")
    assert (
        client.post(reverse("admin:notes_note_add"), {"text": "Admin", "_save": "Save"}).status_code
        == 302
    )
    note = Note.objects.get()
    assert note.history.first().history_user_id == user.pk
    assert (
        client.post(
            reverse("admin:notes_note_change", args=[note.pk]), {"text": "Edited", "_save": "Save"}
        ).status_code
        == 302
    )
    assert list(note.history.values_list("text", flat=True)) == ["Edited", "Admin"]
    assert (
        client.post(reverse("admin:notes_note_delete", args=[note.pk]), {"post": "yes"}).status_code
        == 302
    )
    assert Note.history.filter(id=note.pk).first().history_type == "-"
    (tmp_path / "notes.json").write_text('[{"text":"JSON"}]')
    NoteImporter(tmp_path).run()
    assert Note.objects.get().history.get().text == "JSON"

import json
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError

from apps.notes.actions.importer import Importer
from apps.notes.models import Note
from apps.notes.services.importers.note import NoteImporter

pytestmark = pytest.mark.django_db


def test_import_notes_adds_to_existing_notes(tmp_path):
    existing = Note.objects.create(text="Existing")
    path = tmp_path / "notes.json"
    path.write_text(json.dumps([{"text": " First "}, {"text": "日本語"}]), encoding="utf-8")

    assert NoteImporter(tmp_path).run() == 2
    assert Note.objects.count() == 3
    assert set(Note.objects.exclude(pk=existing.pk).values_list("text", flat=True)) == {
        "First",
        "日本語",
    }
    assert all(note.created_at is not None for note in Note.objects.all())


@pytest.mark.parametrize(
    "data",
    [
        {},
        [None],
        [{"text": 123}],
        [{"text": "ok", "id": 1}],
        [{"text": " "}],
        [{"text": "x" * 2001}],
    ],
)
def test_import_rejects_invalid_data_without_partial_writes(tmp_path, data):
    existing = Note.objects.create(text="Keep")
    path = tmp_path / "notes.json"
    payload = [{"text": "Valid first row"}, *data] if isinstance(data, list) else data
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises((ValueError, ValidationError)):
        NoteImporter(tmp_path).run()
    assert list(Note.objects.values_list("pk", "text")) == [(existing.pk, "Keep")]


def test_import_sample_file():
    directory = Path(__file__).resolve().parents[1] / "var/data"
    assert Importer(directory).run() == 2
    assert Note.objects.count() == 2


def test_import_reports_unreadable_or_malformed_json(tmp_path):
    path = tmp_path / "notes.json"
    with pytest.raises(FileNotFoundError):
        NoteImporter(tmp_path).run()
    path.write_text("[", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        NoteImporter(tmp_path).run()
    assert not Note.objects.exists()


@pytest.mark.parametrize("importer_class", [NoteImporter, Importer])
def test_results_are_reset_before_each_run(tmp_path, importer_class):
    importer = importer_class(tmp_path)
    assert importer.results == []
    path = tmp_path / "notes.json"
    path.write_text('[{"text": "First"}]', encoding="utf-8")
    assert importer.run() == 1
    previous_results = importer.results
    assert previous_results[0].text == "First"

    path.write_text('[{"text": "Second"}]', encoding="utf-8")
    assert importer.run() == 1
    assert [note.text for note in importer.results] == ["Second"]
    assert importer.results[0].pk != previous_results[0].pk

    path.write_text("[", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        importer.run()
    assert importer.results == []
    assert Note.objects.count() == 2
    assert previous_results[0].text == "First"

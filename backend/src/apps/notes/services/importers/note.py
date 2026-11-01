from pathlib import Path

from django.db import transaction

from apps.notes.models import Note
from lib.files.json import read_json


class NoteImporter:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.results: list[Note] = []

    def run(self) -> int:
        """notes.jsonを全件追加する。失敗時は追加せず、再実行時は同じ内容も追加する。"""
        self.results = []
        path = self.directory / "notes.json"
        data = read_json(path)
        if not isinstance(data, list):
            raise ValueError("Notes must be a JSON array")

        notes = []
        for item in data:
            if not isinstance(item, dict) or set(item) != {"text"}:
                raise ValueError("Each note must contain only text")
            if not isinstance(item["text"], str):
                raise ValueError("Note text must be a string")
            note = Note(text=item["text"].strip())
            note.full_clean()
            notes.append(note)

        with transaction.atomic():
            for note in notes:
                note.save()
        self.results = notes
        return len(self.results)

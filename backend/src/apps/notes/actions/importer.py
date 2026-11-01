from pathlib import Path

from django.db import transaction

from apps.notes.models import Note
from apps.notes.services.importers.note import NoteImporter


class Importer:
    """Noteの一括取込を組み立てる公開アクション。"""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.results: list[Note] = []

    def run(self) -> int:
        """順に実行して合計登録件数を返す。失敗時は全件取消し、再実行時も追加する。"""
        self.results = []
        importer = NoteImporter(self.directory)
        with transaction.atomic():
            importer.run()
        self.results = importer.results
        return len(self.results)

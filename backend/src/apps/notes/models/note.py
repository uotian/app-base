from typing import Any

from django.db import models, transaction
from django.db.models import Max
from simple_history.models import HistoricalRecords


class Note(models.Model):
    text = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(default=0, db_index=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        with transaction.atomic():
            # shortcut: SQLite write locking protects allocation; revisit before adding PostgreSQL.
            if self._state.adding and self.position == 0:
                self.position = (Note.objects.aggregate(last=Max("position"))["last"] or 0) + 1
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.text[:80]

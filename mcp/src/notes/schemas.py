from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class Note(BaseModel):
    id: Annotated[int, Field(strict=True, gt=0)]
    text: str
    created_at: datetime


class NotesPage(BaseModel):
    count: Annotated[int, Field(strict=True, ge=0)]
    next: str | None
    previous: str | None
    results: list[Note]
    csrf_token: Annotated[str, Field(alias="csrfToken", min_length=1, exclude=True)]


class NoteList(BaseModel):
    count: int
    page: int
    has_next: bool
    results: list[Note]

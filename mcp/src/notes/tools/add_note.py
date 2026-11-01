from typing import Annotated

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field, ValidationError

from notes.django.error import NoteAPIError
from notes.django.request import request
from notes.schemas import Note, NotesPage


def register_add_note(server: MCPServer, notes_url: str) -> None:
    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=False,
            open_world_hint=True,
        )
    )
    async def add_note(text: Annotated[str, Field(min_length=1, max_length=2000)]) -> Note:
        """Add a public note. Do not include secrets. Repeated calls create duplicates."""
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                response = await request(client, "GET", notes_url)
                try:
                    page = NotesPage.model_validate_json(response.content)
                except ValidationError:
                    raise ToolError("Note API returned an invalid response.") from None
                response = await request(
                    client,
                    "POST",
                    notes_url,
                    json={"text": text},
                    headers={"X-CSRFToken": page.csrf_token, "Referer": str(notes_url)},
                )
        except NoteAPIError as error:
            raise ToolError(str(error)) from None
        try:
            return Note.model_validate_json(response.content)
        except ValidationError:
            raise ToolError(
                "Note API returned an invalid response. Check the list before retrying; "
                "the note may already have been saved."
            ) from None

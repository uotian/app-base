from typing import Annotated

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field, ValidationError

from notes.django.error import NoteAPIError
from notes.django.request import request
from notes.schemas import NoteList, NotesPage


def register_list_notes(server: MCPServer, notes_url: str) -> None:
    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True))
    async def list_notes(page: Annotated[int, Field(ge=1)] = 1) -> NoteList:
        """List public notes, newest first, 20 per page. Everyone can read these notes."""
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                response = await request(client, "GET", notes_url, params={"page": page})
            result = NotesPage.model_validate_json(response.content)
        except ValidationError:
            raise ToolError("Note API returned an invalid response.") from None
        except NoteAPIError as error:
            raise ToolError(str(error)) from None
        return NoteList(
            count=result.count, page=page, has_next=result.next is not None, results=result.results
        )

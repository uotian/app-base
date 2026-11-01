from collections.abc import Callable

from mcp.server import MCPServer

from notes.notes_api_url import notes_api_url
from notes.tools.add_note import register_add_note
from notes.tools.list_notes import register_list_notes

TOOL_REGISTRARS: tuple[tuple[Callable[[MCPServer, str], None], Callable[[str], str]], ...] = (
    (register_list_notes, notes_api_url),
    (register_add_note, notes_api_url),
)

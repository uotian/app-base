import httpx

from notes.django.error import NoteAPIError


async def request(
    client: httpx.AsyncClient,
    method: str,
    notes_url: str,
    *,
    params: dict[str, int] | None = None,
    json: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    try:
        response = await client.request(
            method, notes_url, params=params, json=json, headers=headers
        )
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as error:
        message = f"Note API returned HTTP {error.response.status_code}."
        if method == "POST":
            message += " Check the list before retrying; the note may already have been saved."
        raise NoteAPIError(message) from None
    except httpx.RequestError:
        raise NoteAPIError(
            "Note API could not be reached. If adding, check the list before retrying; "
            "the note may already have been saved."
        ) from None

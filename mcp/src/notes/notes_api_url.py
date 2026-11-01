import httpx


def notes_api_url(api_url: str) -> str:
    try:
        url = httpx.URL(api_url)
    except httpx.InvalidURL:
        raise ValueError("API URL is invalid.") from None
    if (
        url.scheme not in {"http", "https"}
        or not url.host
        or url.userinfo
        or url.query
        or url.fragment
    ):
        raise ValueError("API URL must be an HTTP(S) origin without credentials, query or fragment")
    if url.path not in {"", "/"}:
        raise ValueError("API URL must be an origin without a path")
    return str(url.join("/api/notes/"))

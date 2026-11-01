import httpx
import pytest
from hypothesis import given
from hypothesis import strategies as st

from notes.notes_api_url import notes_api_url


@given(
    scheme=st.sampled_from(["http", "https"]),
    label=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=63),
    port=st.integers(min_value=1, max_value=65535),
    slash=st.sampled_from(["", "/"]),
)
def test_generated_origins_preserve_destination(scheme, label, port, slash):
    origin = httpx.URL(f"{scheme}://{label}.example:{port}{slash}")
    result = httpx.URL(notes_api_url(str(origin)))
    assert (result.scheme, result.host, result.port) == (origin.scheme, origin.host, origin.port)
    assert result.path == "/api/notes/"
    assert not result.userinfo and not result.query and not result.fragment


@given(
    component=st.sampled_from(["credentials", "path", "query", "fragment"]),
    value=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=80),
)
def test_generated_non_origins_are_rejected_without_echoing_input(component, value):
    urls = {
        "credentials": f"https://user:{value}@example.test/",
        "path": f"https://example.test/{value}",
        "query": f"https://example.test/?key={value}",
        "fragment": f"https://example.test/#{value}",
    }
    with pytest.raises(ValueError) as error:
        notes_api_url(urls[component])
    assert urls[component] not in str(error.value)

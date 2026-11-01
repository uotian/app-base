from wsgiref.headers import Headers

from server import static_headers


def test_exported_html_uses_hashed_scripts_instead_of_unsafe_inline(tmp_path):
    html = tmp_path / "index.html"
    html.write_text('<script>console.log("hello")</script>', encoding="utf-8")
    headers = Headers()
    static_headers(headers, str(html), "/")
    policy = headers["Content-Security-Policy"]
    script_policy = policy.split("script-src ")[1].split(";")[0]
    assert "'sha256-" in script_policy
    assert "unsafe-inline" not in script_policy
    assert headers["Cache-Control"] == "no-cache"

"""Serve the same static Next.js output and Django API on Web and desktop."""

import argparse
import base64
import hashlib
import json
import logging
import os
import re
import sys
import threading
from pathlib import Path
from wsgiref.headers import Headers

from django.core.wsgi import get_wsgi_application
from waitress.server import TcpWSGIServer, create_server
from whitenoise import WhiteNoise


def static_headers(headers: Headers, path: str, url: str) -> None:
    if path.endswith(".html"):
        html = Path(path).read_text(encoding="utf-8")
        hashes = [
            "'sha256-" + base64.b64encode(hashlib.sha256(script.encode()).digest()).decode() + "'"
            for script in re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.DOTALL)
        ]
        headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' "
            + " ".join(hashes)
            + "; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        headers["Cache-Control"] = "no-cache"
    headers["X-Content-Type-Options"] = "nosniff"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--frontend", type=Path, default=Path(__file__).resolve().parents[2] / "frontend/out"
    )
    parser.add_argument("--desktop", action="store_true")
    args = parser.parse_args()
    if not (args.frontend / "index.html").is_file():
        parser.error("Build the frontend first: pnpm build")
    if args.desktop and (not os.environ.get("DESKTOP_TOKEN") or args.host != "127.0.0.1"):
        parser.error("Desktop requires a token and loopback host")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    application = WhiteNoise(
        get_wsgi_application(),
        root=str(args.frontend),
        index_file=True,
        add_headers_function=static_headers,
    )
    server = create_server(application, host=args.host, port=args.port)
    if not isinstance(server, TcpWSGIServer):
        server.close()
        raise RuntimeError("Specify a single IPv4 listen address")
    port = int(server.getsockname()[1])
    logger = logging.getLogger("app_base.server")
    print(json.dumps({"port": port}), flush=True)
    try:
        logger.info("server_started", extra={"port": port, "desktop": args.desktop})
        if args.desktop:
            # stdin closes even if Electron crashes; stop the child server in that case too.
            threading.Thread(target=server.run, daemon=True).start()
            sys.stdin.buffer.read()
        else:
            server.run()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        server.task_dispatcher.shutdown(timeout=5)
        logger.info("server_stopped")


if __name__ == "__main__":
    main()

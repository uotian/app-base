import argparse

from mcp.server import MCPServer

from registry import TOOL_REGISTRARS


def create_server(api_url: str) -> MCPServer:
    server = MCPServer("App Base", log_level="WARNING")
    for register_tool, resolve_api_url in TOOL_REGISTRARS:
        register_tool(server, resolve_api_url(api_url))
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="App Base MCP server (Django HTTP API client)")
    parser.add_argument("--api-url", default="http://127.0.0.1:8100")
    parser.add_argument("--port", type=int, default=8200)
    args = parser.parse_args()
    create_server(args.api_url).run(
        transport="streamable-http", host="127.0.0.1", port=args.port, stateless_http=True
    )

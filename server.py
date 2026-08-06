"""FastMCP server exposing authenticated, read-only Kalvium Livebook tools."""

import logging

from fastmcp import FastMCP

from tools import (
    get_lesson,
    hello,
    list_lessons,
    list_livebooks,
)

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("Kalvium Livebooks")

# Register MCP tools
mcp.tool()(list_livebooks)
mcp.tool()(list_lessons)
mcp.tool()(get_lesson)
mcp.tool()(hello)


def main() -> None:
    """Run the server over the standard MCP stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
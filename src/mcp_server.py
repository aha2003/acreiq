"""
src/mcp_server.py

Model Context Protocol server exposing AcreIQ's `get_area_metrics` tool.

Written against MCP Python SDK v2 (mcp.server.mcpserver.MCPServer), which is
what `pip install mcp` installs as of 2026. If you're pinned to the old v1
SDK (mcp.server.lowlevel.Server), this file will not import correctly --
run `pip show mcp` to check your installed version.

This lets any MCP-compatible client (Claude Desktop, a claude.ai connector,
ChatGPT with MCP support, etc.) call directly into the DLD transaction
database -- the same shape of integration described as "Majlis" in the
job posting.

Local usage (stdio transport, for Claude Desktop):
    python -m src.mcp_server

Claude Desktop config (~/Library/Application Support/Claude/claude_desktop_config.json
on macOS, or the equivalent path on your OS):

    {
      "mcpServers": {
        "acreiq": {
          "command": "python",
          "args": ["-m", "src.mcp_server"],
          "cwd": "/absolute/path/to/acreiq"
        }
      }
    }

Requires: pip install mcp
"""

import logging

from mcp.server.mcpserver import MCPServer

from src.tools import get_area_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("acreiq.mcp")

mcp = MCPServer("acreiq")


@mcp.tool()
def get_area_metrics_tool(area_name: str, trans_group: str = "Sales") -> dict:
    """
    Retrieves official DLD (Dubai Land Department) sales volume, average
    price, median price, and transaction traces for a Dubai area. Every
    number returned is sourced directly from registered transaction
    records -- never estimated.

    Args:
        area_name: Dubai area name, e.g. 'Dubai Marina', 'Business Bay', 'JVC'.
            Common investor names and abbreviations are resolved to their
            official cadastral name automatically.
        trans_group: Transaction group -- one of 'Sales', 'Mortgages', 'Gifts'.
            Defaults to 'Sales'.
    """
    logger.info(f"tool_call get_area_metrics area={area_name!r} trans_group={trans_group!r}")

    # Reuses the exact same grounded-data function the internal agent
    # pipeline calls -- an external MCP client gets identical, database-
    # verified numbers, never a separate/looser code path.
    return get_area_metrics(area_name=area_name, trans_group=trans_group)


if __name__ == "__main__":
    # Defaults to stdio transport, which is what Claude Desktop expects.
    mcp.run()
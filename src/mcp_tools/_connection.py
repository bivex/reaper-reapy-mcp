"""MCP tools for connection to REAPER."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
from ._helpers import _create_success_response, _create_error_response, _handle_controller_operation, logger

def _setup_connection_tools(mcp: FastMCP, controller) -> None:
    """Setup connection-related MCP tools."""

    @mcp.tool("test_connection")
    def test_connection(ctx: Context) -> Dict[str, Any]:
        """Test connection to Reaper."""
        return _handle_controller_operation(
            "Connection test", controller.verify_connection
        )



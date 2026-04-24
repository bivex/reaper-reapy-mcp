"""Project and connection MCP tools."""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context
from .tool_helpers import (
    _create_success_response,
    _create_error_response,
    _handle_controller_operation,
)

logger = logging.getLogger(__name__)


def _setup_connection_tools(mcp: FastMCP, controller) -> None:
    """Setup connection-related MCP tools."""

    @mcp.tool("test_connection")
    def test_connection(ctx: Context) -> Dict[str, Any]:
        """Test connection to Reaper."""
        return _handle_controller_operation(
            "Connection test", controller.verify_connection
        )


def _setup_project_tools(mcp: FastMCP, controller) -> None:
    """Setup project-related MCP tools."""

    @mcp.tool("set_tempo")
    def set_tempo(ctx: Context, bpm: float) -> Dict[str, Any]:
        """Set the project tempo."""
        return _handle_controller_operation(
            f"Set tempo to {bpm} BPM", controller.project.set_tempo, bpm
        )

    @mcp.tool("get_tempo")
    def get_tempo(ctx: Context) -> Dict[str, Any]:
        """Get the current project tempo."""
        try:
            tempo = controller.project.get_tempo()
            return _create_success_response(f"Current tempo: {tempo} BPM")
        except Exception as e:
            logger.error(f"Failed to get tempo: {str(e)}")
            return _create_error_response(f"Failed to get tempo: {str(e)}")

    @mcp.tool("clear_project")
    def clear_project(ctx: Context) -> Dict[str, Any]:
        """Clear all items from all tracks in the project."""
        return _handle_controller_operation(
            "Clear all items from project", controller.project.clear_project
        )

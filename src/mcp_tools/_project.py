"""MCP tools for project and marker management."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
from ._helpers import _create_success_response, _create_error_response, _handle_controller_operation, logger

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


def _setup_marker_tools(mcp: FastMCP, controller) -> None:
    """Setup marker and region-related MCP tools."""

    @mcp.tool("create_region")
    def create_region(
        ctx: Context, start_time: float, end_time: float, name: str
    ) -> Dict[str, Any]:
        """
        Create a region in the project.

        Args:
            start_time (float): Start time in seconds (use number, not string)
            end_time (float): End time in seconds (use number, not string)
            name (str): Name of the region
        """
        operation_name = f"Create region '{name}' from {start_time} to {end_time}"
        return _handle_controller_operation(
            operation_name, controller.marker.create_region, start_time, end_time, name
        )

    @mcp.tool("delete_region")
    def delete_region(ctx: Context, region_index: int) -> Dict[str, Any]:
        """Delete a region from the project."""
        return _handle_controller_operation(
            f"Delete region {region_index}",
            controller.marker.delete_region,
            region_index,
        )

    @mcp.tool("create_marker")
    def create_marker(ctx: Context, time: float, name: str) -> Dict[str, Any]:
        """
        Create a marker at the specified time.

        Args:
            time (float): Time in seconds (use number, not string)
            name (str): Name of the marker
        """
        return _handle_controller_operation(
            f"Create marker '{name}' at {time}",
            controller.marker.create_marker,
            time,
            name,
        )

    @mcp.tool("delete_marker")
    def delete_marker(ctx: Context, marker_index: int) -> Dict[str, Any]:
        """Delete a marker from the project."""
        return _handle_controller_operation(
            f"Delete marker {marker_index}",
            controller.marker.delete_marker,
            marker_index,
        )



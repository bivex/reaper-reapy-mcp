"""MCP tools for master track control."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
from ._helpers import _create_success_response, _create_error_response, _handle_controller_operation, logger

def _setup_master_tools(mcp: FastMCP, controller) -> None:
    """Setup master track-related MCP tools."""

    @mcp.tool("get_master_track")
    def get_master_track(ctx: Context) -> Dict[str, Any]:
        """Get master track information."""
        try:
            master_info = controller.master.get_master_track()
            return _create_success_response(f"Master track info: {master_info}")
        except Exception as e:
            logger.error(f"Failed to get master track: {str(e)}")
            return _create_error_response(f"Failed to get master track: {str(e)}")

    @mcp.tool("set_master_volume")
    def set_master_volume(ctx: Context, volume: float) -> Dict[str, Any]:
        """
        Set master track volume.

        Args:
            volume (float): Volume in dB (use number, not string, e.g., -6.0, 0.0, 3.0)
        """
        return _handle_controller_operation(
            f"Set master volume to {volume}",
            controller.master.set_master_volume,
            volume,
        )

    @mcp.tool("set_master_pan")
    def set_master_pan(ctx: Context, pan: float) -> Dict[str, Any]:
        """
        Set master track pan.

        Args:
            pan (float): Pan position (-1.0 to 1.0, use number, not string)
        """
        return _handle_controller_operation(
            f"Set master pan to {pan}", controller.master.set_master_pan, pan
        )

    @mcp.tool("toggle_master_mute")
    def toggle_master_mute(ctx: Context, mute: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle master track mute."""
        action = "mute" if mute else "toggle mute"
        return _handle_controller_operation(
            f"{action.capitalize()} master track",
            controller.master.toggle_master_mute,
            mute,
        )

    @mcp.tool("toggle_master_solo")
    def toggle_master_solo(ctx: Context, solo: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle master track solo."""
        action = "solo" if solo else "toggle solo"
        return _handle_controller_operation(
            f"{action.capitalize()} master track",
            controller.master.toggle_master_solo,
            solo,
        )



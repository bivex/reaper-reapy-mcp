"""MCP tools for automation envelopes."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
from ._helpers import _create_success_response, _create_error_response, _handle_controller_operation, logger

def _setup_automation_tools(mcp: FastMCP, controller) -> None:
    """Setup automation and modulation MCP tools."""

    @mcp.tool("create_automation_envelope")
    def create_automation_envelope(
        ctx: Context, track_index: int, envelope_name: str
    ) -> Dict[str, Any]:
        """
        Create an automation envelope on a track.

        Args:
            track_index (int): Index of the track to create envelope on
            envelope_name (str): Name of the automation envelope
        """
        return _handle_controller_operation(
            f"Create automation envelope '{envelope_name}' on track {track_index}",
            controller.automation.create_automation_envelope,
            track_index,
            envelope_name,
        )

    @mcp.tool("add_automation_point")
    def add_automation_point(
        ctx: Context,
        track_index: int,
        envelope_name: str,
        time: float,
        value: float,
        shape: int = 0,
    ) -> Dict[str, Any]:
        """
        Add an automation point to an envelope.

        Args:
            track_index (int): Index of the track containing the envelope
            envelope_name (str): Name of the automation envelope
            time (float): Time position in seconds (use number, not string)
            value (float): Value of the automation point (use number, not string)
            shape (int): Shape of the automation curve (0: linear, 1: slow, 2: fast, 3: bezier, 4: square)
        """
        return _handle_controller_operation(
            f"Add automation point at {time}s with value {value} on track {track_index}",
            controller.automation.add_automation_point,
            track_index,
            envelope_name,
            time,
            value,
            shape,
        )

    @mcp.tool("get_automation_points")
    def get_automation_points(
        ctx: Context, track_index: int, envelope_name: str
    ) -> Dict[str, Any]:
        """
        Get all automation points from an envelope.

        Args:
            track_index (int): Index of the track containing the envelope
            envelope_name (str): Name of the automation envelope
        """
        try:
            points = controller.automation.get_automation_points(
                track_index, envelope_name
            )
            return _create_success_response(
                f"Automation points for '{envelope_name}' on track {track_index}: {points}"
            )
        except Exception as e:
            logger.error(f"Failed to get automation points: {str(e)}")
            return _create_error_response(f"Failed to get automation points: {str(e)}")

    @mcp.tool("set_automation_mode")
    def set_automation_mode(
        ctx: Context, track_index: int, mode: str
    ) -> Dict[str, Any]:
        """
        Set the automation mode for a track.

        Args:
            track_index (int): Index of the track to set automation mode for
            mode (str): Automation mode (e.g., "read", "write", "touch", "latch", "trim")
        """
        return _handle_controller_operation(
            f"Set automation mode to '{mode}' on track {track_index}",
            controller.automation.set_automation_mode,
            track_index,
            mode,
        )

    @mcp.tool("get_automation_mode")
    def get_automation_mode(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Get the current automation mode for a track.

        Args:
            track_index (int): Index of the track to get automation mode for
        """
        try:
            mode = controller.automation.get_automation_mode(track_index)
            return _create_success_response(
                f"Track {track_index} automation mode: {mode}"
            )
        except Exception as e:
            logger.error(f"Failed to get automation mode: {str(e)}")
            return _create_error_response(f"Failed to get automation mode: {str(e)}")

    @mcp.tool("delete_automation_point")
    def delete_automation_point(
        ctx: Context, track_index: int, envelope_name: str, point_index: int
    ) -> Dict[str, Any]:
        """
        Delete an automation point from an envelope.

        Args:
            track_index (int): Index of the track containing the envelope
            envelope_name (str): Name of the automation envelope
            point_index (int): Index of the automation point to delete
        """
        return _handle_controller_operation(
            f"Delete automation point {point_index} from '{envelope_name}' on track {track_index}",
            controller.automation.delete_automation_point,
            track_index,
            envelope_name,
            point_index,
        )


